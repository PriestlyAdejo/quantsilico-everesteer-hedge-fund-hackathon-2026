"""Official-score-driven, quota-aware live competition controller."""

from __future__ import annotations

import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psutil

from qs_everesteer.event.adapter import EveresteerAdapter
from qs_everesteer.fsutil import atomic_write_json, read_json
from qs_everesteer.models.registry import ModelRegistry
from qs_everesteer.paths import ensure_dir, find_repo_root
from qs_everesteer.selection.candidate import infer_candidate
from qs_everesteer.state.research import update_research_state


@dataclass(frozen=True)
class AdaptivePolicy:
    """Hard bounds for one controller process."""

    max_live_models_per_round: int = 6
    max_validation_models_per_cycle: int = 4
    upload_reserve: int = 20
    poll_seconds: float = 15.0
    allow_live_submit: bool = False
    allow_auto_stake: bool = False
    max_stake_usdc_per_round: float | None = None
    stake_bankroll_fraction: float = 0.5
    stake_slots: int = 3

    def validate(self) -> None:
        if not 1 <= self.max_live_models_per_round <= 150:
            raise ValueError("max_live_models_per_round must be in [1, 150]")
        if not 0 <= self.max_validation_models_per_cycle <= 12:
            raise ValueError("max_validation_models_per_cycle must be in [0, 12]")
        if self.upload_reserve < 1:
            raise ValueError("upload_reserve must be positive")
        if not 0 < self.stake_bankroll_fraction <= 1:
            raise ValueError("stake_bankroll_fraction must be in (0, 1]")
        if not 1 <= self.stake_slots <= 5:
            raise ValueError("stake_slots must be in [1, 5]")
        if self.max_stake_usdc_per_round is not None and self.max_stake_usdc_per_round < 1:
            raise ValueError("stake cap is below the platform minimum of 1 USDC")


class AdaptiveCompetitionController:
    """Reconcile platform truth, select a frontier, and take bounded actions."""

    def __init__(
        self,
        repo_root: str | Path | None = None,
        *,
        policy: AdaptivePolicy | None = None,
        client: Any | None = None,
    ) -> None:
        self.root = Path(repo_root) if repo_root else find_repo_root()
        self.policy = policy or AdaptivePolicy()
        self.policy.validate()
        self.client = client or EveresteerAdapter(synthetic=False)._get_client()
        if self.client is None:
            raise RuntimeError("authenticated Everesteer client is unavailable")
        self.registry = ModelRegistry(self.root)
        self.state_path = self.root / "runs" / "state" / "adaptive_controller.json"

    def reconcile(self) -> dict[str, Any]:
        previous = read_json(self.state_path) if self.state_path.exists() else {}
        status = self.client.get_status()
        models_payload = self.client.get_models()
        submissions = self.client.get_submission_status().get("submissions", [])
        staking = self.client.get_event_staking()
        fixed = self.client.get_diagnostics_leaderboard(
            view="agents", tournament="futures", limit=500,
            window="leaderboard", scoring_window="leaderboard",
        )
        self_scores = {
            str(row.get("model_name")): row
            for row in fixed.get("entries", [])
            if row.get("is_self")
        }
        cadence = status.get("cadence") or {}
        phase = str(cadence.get("phase") or "UNKNOWN")
        round_name = str(cadence.get("open_window") or phase)
        paid_scores = self._revealed_round_scores(round_name)
        latest_paid = paid_scores.get(self._previous_round(round_name) or "", {})
        remote_models = {
            str(row.get("name")): row for row in models_payload.get("models", [])
        }
        candidates = self._candidate_inventory(self_scores, latest_paid, remote_models)
        frontier = self._diverse_frontier(candidates)
        payload = {
            "schema_version": 1,
            "updated_at": datetime.now(UTC).isoformat(),
            "phase": phase,
            "round": round_name,
            "event_status": status.get("event_status"),
            "seconds_until_next_phase": cadence.get("seconds_until_next_phase"),
            "live_data_available": bool(cadence.get("live_data_available")),
            "intake_fenced": bool(cadence.get("intake_fenced")),
            "uploads_remaining": status.get("uploads_remaining"),
            "remote_models": remote_models,
            "submissions": submissions,
            "official_validation_scores": self_scores,
            "official_paid_round_scores": paid_scores,
            "candidates": candidates,
            "frontier": frontier,
            "champion": frontier[0] if frontier else None,
            "staking": staking,
            "policy": asdict(self.policy),
            "validation_attempts": previous.get("validation_attempts", {}),
        }
        atomic_write_json(self.state_path, payload)

        def mutate(state: dict[str, Any]) -> None:
            remaining = status.get("uploads_remaining")
            state["connection"] = "LIVE"
            state["round"] = round_name
            state["time_remaining_seconds"] = cadence.get("seconds_until_next_phase")
            state["frontier"] = frontier
            state["champion"] = frontier[0] if frontier else None
            state["race_outcomes"] = [
                {
                    "candidate_id": row["id"],
                    "decision": "PROMOTE_OFFICIAL_SCORE",
                    "stage": "OFFICIAL",
                    "next_stage": "R2",
                    "rationale": "revealed paid-round score"
                    if row.get("latest_paid_round_score") is not None
                    else "fixed validation score",
                }
                for row in frontier[:4]
                if row.get("official_round_score") is not None
            ]
            state["official_scores"] = self_scores
            state["official_paid_round_scores"] = paid_scores
            state["remote_submissions"] = submissions
            state["upload_budget"] = {
                "cap": 150,
                "live_remaining": remaining,
                "practice_remaining": remaining,
                "source": "get_status.uploads_remaining",
            }
            state["autopilot_active"] = True
            state["autopilot_stage"] = "ADAPT"
            state.setdefault("meta", {})["source"] = "adaptive_controller"
            state["meta"]["updated_at"] = payload["updated_at"]

        update_research_state(mutate, self.root)
        return payload

    def tick(self) -> dict[str, Any]:
        before = self.reconcile()
        actions: list[dict[str, Any]] = []
        remaining = before.get("uploads_remaining")
        can_spend_upload = remaining is not None and remaining > self.policy.upload_reserve
        if can_spend_upload:
            actions.extend(self._submit_unscored_validation(before))
        if (
            can_spend_upload
            and self.policy.allow_live_submit
            and before.get("live_data_available")
            and not before.get("intake_fenced")
        ):
            actions.extend(self._submit_open_round(before))
        actions.extend(self._maybe_launch_research(before))
        actions.extend(self._maybe_stake(before))
        after = self.reconcile()
        result = {"before": before, "actions": actions, "after": after}
        atomic_write_json(
            ensure_dir(self.root / "runs" / "autopilot") / "latest_tick.json", result
        )
        return result

    def run(self, *, max_ticks: int | None = None) -> dict[str, Any]:
        ticks = 0
        latest: dict[str, Any] = {}
        while max_ticks is None or ticks < max_ticks:
            latest = self.tick()
            ticks += 1
            if latest["after"].get("event_status") not in {"running", "RUNNING"}:
                break
            time.sleep(self.policy.poll_seconds)
        return {"ticks": ticks, "latest": latest}

    def _candidate_inventory(
        self,
        scores: dict[str, dict[str, Any]],
        latest_paid: dict[str, dict[str, Any]],
        remote: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        result = []
        seen_aliases: set[str] = set()
        authoritative_train = (self.root / "data" / "train.parquet").resolve()
        for metadata in self.registry.list():
            candidate_id = str(metadata.get("model_id"))
            run_path = self.root / "runs" / "experiments" / candidate_id / "run.json"
            if not run_path.exists():
                continue
            run = read_json(run_path)
            if run.get("status") != "COMPLETED":
                continue
            configured_data = Path(str((run.get("config") or {}).get("data_path") or ""))
            if not configured_data.is_absolute():
                configured_data = self.root / configured_data
            if not configured_data.exists() or configured_data.resolve() != authoritative_train:
                continue
            alias = str(metadata.get("public_alias") or "")
            if not alias or alias in seen_aliases:
                continue
            seen_aliases.add(alias)
            official = scores.get(alias) or {}
            paid = latest_paid.get(alias) or {}
            result.append({
                "id": candidate_id,
                "public_alias": alias,
                "family": metadata.get("private_name") or metadata.get("family"),
                "official_round_score": official.get("round_score"),
                "official_corr20": official.get("corr20"),
                "latest_paid_round_score": paid.get("round_score"),
                "latest_paid_corr20": paid.get("corr20"),
                "latest_paid_rank": paid.get("rank"),
                "remote_model_id": (remote.get(alias) or {}).get("id"),
                "artefact_path": metadata.get("artefact_path"),
            })
        return sorted(
            result,
            key=lambda row: (
                row.get("latest_paid_round_score") is not None,
                row.get("latest_paid_round_score") or -999.0,
                row.get("official_round_score") is not None,
                row.get("official_round_score") or -999.0,
            ),
            reverse=True,
        )

    def _revealed_round_scores(
        self, current_round: str
    ) -> dict[str, dict[str, dict[str, Any]]]:
        try:
            current = int(current_round.split("_", 1)[1])
        except (IndexError, ValueError):
            return {}
        result: dict[str, dict[str, dict[str, Any]]] = {}
        for number in range(1, current):
            name = f"round_{number}"
            board = self.client.get_diagnostics_leaderboard(
                view="agents", tournament="futures", limit=500,
                window="leaderboard", scoring_window=name,
            )
            if board.get("results_withheld_until"):
                continue
            result[name] = {
                str(row.get("model_name")): row
                for row in board.get("entries", [])
                if row.get("is_self")
            }
        return result

    @staticmethod
    def _diverse_frontier(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        chosen, seen = [], set()
        for row in candidates:
            family = row.get("family")
            if family in seen:
                continue
            chosen.append(row)
            seen.add(family)
        return chosen + [row for row in candidates if row not in chosen]

    def _ensure_remote(self, row: dict[str, Any]) -> str:
        if row.get("remote_model_id"):
            return str(row["remote_model_id"])
        created = self.client.create_model(
            name=row["public_alias"], description="adaptive bounded challenger"
        )
        return str(created.get("id") or created.get("model_id"))

    def _model_pkl(self, candidate_id: str) -> Path:
        folder = self.root / "artifacts" / "models" / candidate_id
        source, output = folder / "model.joblib", folder / "model.pkl"
        if not source.exists():
            raise FileNotFoundError(source)
        if not output.exists() or output.stat().st_mtime_ns < source.stat().st_mtime_ns:
            shutil.copy2(source, output)
        return output

    def _submit_unscored_validation(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        actions = []
        scored = snapshot["official_validation_scores"]
        attempted = snapshot.get("validation_attempts", {})
        data_path = self.root / "data" / "validation.parquet"
        if not data_path.exists():
            return actions
        for row in snapshot["candidates"]:
            if len(actions) >= self.policy.max_validation_models_per_cycle:
                break
            if row["public_alias"] in scored or row["public_alias"] in attempted:
                continue
            remote_id = self._ensure_remote(row)
            out = self.root / "artifacts" / "predictions" / f"{row['id']}.parquet"
            inferred = infer_candidate(
                self.root, candidate_id=row["id"], data_path=data_path, output_path=out
            )
            response = self.client.submit_validation_diagnostics(
                remote_id, str(out), tournament="futures", target="target_everest_20",
                model_pkl=str(self._model_pkl(row["id"])),
                model_pkl_python_version=f"{sys.version_info.major}.{sys.version_info.minor}",
                client_label=row["public_alias"], wait=False,
            )
            self._record_validation_attempt(row["public_alias"], row["id"], response)
            actions.append({"type": "VALIDATION_SUBMIT", "candidate": row["id"],
                            "inference": inferred, "response": response})
        return actions

    def _record_validation_attempt(
        self, alias: str, candidate_id: str, response: dict[str, Any]
    ) -> None:
        state = read_json(self.state_path) if self.state_path.exists() else {}
        attempts = state.setdefault("validation_attempts", {})
        attempts[alias] = {
            "candidate_id": candidate_id,
            "upload_id": response.get("upload_id"),
            "status": response.get("status"),
            "submitted_at": datetime.now(UTC).isoformat(),
        }
        atomic_write_json(self.state_path, state)

    def _submit_open_round(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        if snapshot.get("uploads_remaining", 0) <= self.policy.upload_reserve:
            return []
        submitted = {
            str(row.get("model_id")) for row in snapshot["submissions"]
            if str(row.get("round")) == snapshot["round"] and row.get("accepted")
        }
        slots_left = max(0, self.policy.max_live_models_per_round - len(submitted))
        if slots_left == 0:
            return []
        live_path = Path(self.client.download_dataset(
            universe="futures", split="live", output_path=str(self.root / "data" / "live.parquet")
        ))
        actions = []
        for row in snapshot["frontier"]:
            if len(actions) >= slots_left:
                break
            if row.get("official_round_score") is None or row["public_alias"] in submitted:
                continue
            remote_id = self._ensure_remote(row)
            out = self.root / "artifacts" / "predictions" / f"{row['id']}-{snapshot['round']}.parquet"
            inferred = infer_candidate(
                self.root, candidate_id=row["id"], data_path=live_path, output_path=out
            )
            response = self.client.submit_event_predictions(
                remote_id, str(out), tournament="futures", target="target_everest_20",
                model_pkl=str(self._model_pkl(row["id"])),
                model_pkl_python_version=f"{sys.version_info.major}.{sys.version_info.minor}",
                client_label=row["public_alias"], wait=False,
            )
            actions.append({"type": "LIVE_SUBMIT", "round": snapshot["round"],
                            "candidate": row["id"], "inference": inferred,
                            "response": response})
        return actions

    def _maybe_launch_research(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        if self._search_process_running():
            return []
        completed_ridge = list(
            (self.root / "runs" / "experiments").glob("ridge-real-*/run.json")
        )
        if not completed_ridge:
            command = "ridge"
            args = [str(self._qseh()), "--verbose", "search", command]
            args += ["--profile", "R1", "--max-trials", "4"]
            args += ["--data", str(self.root / "data" / "train.parquet")]
            return self._spawn_research(args, command)
        completed_tunes = list((self.root / "runs" / "experiments").glob("tune-*/run.json"))
        if completed_tunes:
            return []
        command = "tune"
        args = [str(self._qseh()), "--verbose", "search", command]
        args += ["--survivors", "--profile", "R2", "--max-trials", "4"]
        args += ["--data", str(self.root / "data" / "train.parquet")]
        return self._spawn_research(args, command)

    def _spawn_research(self, args: list[str], command: str) -> list[dict[str, Any]]:
        log_dir = ensure_dir(self.root / "runs" / "autopilot" / "logs")
        log_path = log_dir / f"research-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.log"
        log = log_path.open("ab")
        process = subprocess.Popen(args, cwd=self.root, stdout=log, stderr=subprocess.STDOUT)
        log.close()
        return [{"type": "RESEARCH_LAUNCH", "kind": command,
                 "pid": process.pid, "log": str(log_path)}]

    def _maybe_stake(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        if not self.policy.allow_auto_stake:
            return []
        staking = snapshot["staking"]
        if not staking.get("stake_window_open"):
            return []
        current_window = str(staking.get("draft_window") or snapshot["round"])
        current_allocations: list[dict[str, Any]] = []
        for window in staking.get("windows", []):
            if window.get("window") == current_window:
                current_allocations = list(window.get("allocations") or [])
                if any(row.get("locked") for row in current_allocations):
                    return []
        previous = self._previous_round(snapshot["round"])
        if previous is None:
            return []
        board = self.client.get_diagnostics_leaderboard(
            view="agents", tournament="futures", limit=500,
            window="leaderboard", scoring_window=previous,
        )
        own = [row for row in board.get("entries", []) if row.get("is_self")]
        own = [row for row in own if row.get("round_score") is not None]
        if not own:
            return []
        submitted = {
            str(row.get("model_id")) for row in snapshot["submissions"]
            if str(row.get("round")) == current_window and row.get("accepted")
        }
        own = [row for row in own if str(row.get("model_name")) in submitted]
        own.sort(key=lambda row: float(row["round_score"]), reverse=True)
        own = own[: self.policy.stake_slots]
        if not own:
            return []
        spendable = float(staking.get("max_stakeable_micro") or 0) / 1_000_000
        total = spendable * self.policy.stake_bankroll_fraction
        if self.policy.max_stake_usdc_per_round is not None:
            total = min(total, self.policy.max_stake_usdc_per_round)
        total = round(total, 2)
        if total < len(own):
            return []
        weights = [max(float(row["round_score"]), 0.0) for row in own]
        weight_sum = sum(weights)
        if weight_sum <= 0:
            return []
        amounts = [round(total * weight / weight_sum, 2) for weight in weights]
        amounts[-1] = round(total - sum(amounts[:-1]), 2)
        desired = {
            str(row["model_name"]): amount
            for row, amount in zip(own, amounts, strict=True)
            if amount >= 1
        }
        existing = {
            str(row.get("model_name")): int(row.get("amount_micro") or 0)
            for row in current_allocations
        }
        actions: list[dict[str, Any]] = []
        for model_name in sorted(set(existing) - set(desired)):
            response = self.client.withdraw_stake_allocation(
                model_name, window=current_window
            )
            actions.append({
                "type": "STAKE_WITHDRAW", "round": current_window,
                "model": model_name, "response": response,
            })
        for row, amount in zip(own, amounts, strict=True):
            if amount < 1:
                continue
            model_name = str(row["model_name"])
            desired_micro = round(amount * 1_000_000)
            if existing.get(model_name) == desired_micro:
                continue
            response = self.client.set_stake_allocation(
                model_name, amount_micro=desired_micro, window=current_window
            )
            actions.append({
                "type": "STAKE_ALLOCATION", "evidence_round": previous,
                "round": current_window, "model": model_name,
                "amount_usdc": amount, "evidence_score": row["round_score"],
                "response": response,
            })
        return actions

    @staticmethod
    def _previous_round(round_name: str) -> str | None:
        if not round_name.startswith("round_"):
            return None
        try:
            number = int(round_name.split("_", 1)[1])
        except ValueError:
            return None
        return f"round_{number - 1}" if number > 1 else None

    @staticmethod
    def _search_process_running() -> bool:
        for process in psutil.process_iter(["cmdline"]):
            try:
                command = " ".join(process.info.get("cmdline") or []).lower()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue
            if "qseh" in command and "search" in command:
                return True
        return False

    def _qseh(self) -> Path:
        local = self.root / ".venv" / ("Scripts" if sys.platform == "win32" else "bin") / (
            "qseh.exe" if sys.platform == "win32" else "qseh"
        )
        if local.exists():
            return local
        found = shutil.which("qseh")
        if not found:
            raise FileNotFoundError("qseh executable is unavailable")
        return Path(found)
