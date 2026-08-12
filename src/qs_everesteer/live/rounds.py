"""Restartable open-round controller: detect → pull → infer → guard → submit → observe."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from qs_everesteer.data.fingerprint import fingerprint_dataset
from qs_everesteer.event.adapter import ConnectionStatus, EveresteerAdapter, SimulatedEventFeed
from qs_everesteer.event.timebase import countdown
from qs_everesteer.fsutil import atomic_write_json
from qs_everesteer.paths import ensure_dir, find_repo_root, runs_dir
from qs_everesteer.state.research import update_research_state
from qs_everesteer.submission.pipeline import (
    IdempotencyLedger,
    PipelineRequest,
    QuotaController,
    SubmissionPipeline,
    make_idempotency_key,
)


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


@dataclass
class RoundTickResult:
    ok: bool
    round_id: str | None
    connection: str
    stages: list[str] = field(default_factory=list)
    skipped: bool = False
    skip_reason: str | None = None
    submission: dict[str, Any] | None = None
    state_path: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "round_id": self.round_id,
            "connection": self.connection,
            "stages": list(self.stages),
            "skipped": self.skipped,
            "skip_reason": self.skip_reason,
            "submission": self.submission,
            "state_path": self.state_path,
            "detail": self.detail,
        }


InferChampionFn = Callable[[dict[str, Any]], dict[str, Any]]
EnsembleFn = Callable[[dict[str, Any]], dict[str, Any]]


class RoundController:
    """
    Restartable / idempotent live-round loop.

    detect round → snapshot → pull live → fingerprint → audit →
    infer champion/challengers → ensemble → guard → submit (mode+idempotency) →
    observe → update state.
    """

    def __init__(
        self,
        *,
        repo_root: str | Path | None = None,
        adapter: EveresteerAdapter | None = None,
        feed: SimulatedEventFeed | None = None,
        pipeline: SubmissionPipeline | None = None,
        infer_fn: InferChampionFn | None = None,
        ensemble_fn: EnsembleFn | None = None,
        audit_fn: Callable[[Path], dict[str, Any]] | None = None,
    ) -> None:
        self.repo_root = Path(repo_root) if repo_root is not None else find_repo_root()
        self.feed = feed
        self.adapter = adapter or EveresteerAdapter(feed=feed, synthetic=True)
        if feed is not None and self.adapter.feed is None:
            self.adapter.feed = feed
        self.pipeline = pipeline or SubmissionPipeline(
            repo_root=self.repo_root,
            adapter=self.adapter,
        )
        self.infer_fn = infer_fn
        self.ensemble_fn = ensemble_fn
        self.audit_fn = audit_fn
        self.ledger = IdempotencyLedger(repo_root=self.repo_root)
        self._last_fingerprint: str | None = None
        self._last_round: str | None = None

    def tick(self, **kwargs: Any) -> RoundTickResult:
        """Run one restartable cycle. Extra kwargs override detect/submit fields."""
        stages: list[str] = []
        detail: dict[str, Any] = {}

        # 1) Detect round / connection
        stages.append("detect_round")
        detected = self._detect_round()
        detail["detect"] = detected
        connection = str(detected.get("connection") or ConnectionStatus.UNAVAILABLE.value)

        if connection == ConnectionStatus.DISCONNECTED.value:
            return RoundTickResult(
                ok=True,
                round_id=detected.get("round"),
                connection=connection,
                stages=stages,
                skipped=True,
                skip_reason="feed disconnected",
                detail=detail,
            )

        round_id = kwargs.get("round_id") or detected.get("round")
        event_id = kwargs.get("event_id") or detected.get("event_id") or "UNKNOWN_EVENT"
        if not round_id:
            return RoundTickResult(
                ok=False,
                round_id=None,
                connection=connection,
                stages=stages,
                skipped=True,
                skip_reason="no open round detected",
                detail=detail,
            )

        # 2) Snapshot
        stages.append("snapshot")
        snap = self.adapter.snapshot(self.repo_root)
        detail["snapshot_id"] = snap.get("snapshot_id")
        event_id = snap.get("event_id") or event_id

        # 3) Pull live
        stages.append("pull_live")
        live_dir = ensure_dir(runs_dir(self.repo_root) / "live" / str(round_id))
        live_path = self.adapter.pull_split(
            "live",
            live_dir / "live.parquet",
            repo_root=self.repo_root,
        )
        detail["live_path"] = str(live_path)

        # 4) Fingerprint
        stages.append("fingerprint")
        fp = fingerprint_dataset(live_path)
        split_fp = fp["content_sha256"]
        detail["fingerprint"] = {"content_sha256": split_fp, "schema_sha256": fp["schema_sha256"]}

        # Idempotent short-circuit: same round + fingerprint already submitted
        candidate_id = kwargs.get("candidate_id") or self._champion_id() or "champion"
        action = str(kwargs.get("action") or "submit_live")
        key = make_idempotency_key(
            event_id=str(event_id),
            round_id=str(round_id),
            split_fingerprint=split_fp,
            candidate_id=str(candidate_id),
            action=action,
        )
        prior = self.ledger.get(key)
        if prior and prior.get("status") in {"DRY_RUN_OK", "SUBMITTED", "RECORDED"}:
            stages.append("idempotent_skip")
            self._update_state(round_id=str(round_id), snap=snap, connection=connection, fp=split_fp)
            return RoundTickResult(
                ok=True,
                round_id=str(round_id),
                connection=connection,
                stages=stages,
                skipped=True,
                skip_reason="idempotent — prior submission exists for this key",
                submission={"idempotency_key": key, "prior": prior},
                detail=detail,
            )

        if (
            self._last_round == str(round_id)
            and self._last_fingerprint == split_fp
            and not kwargs.get("force")
        ):
            stages.append("fingerprint_unchanged")
            return RoundTickResult(
                ok=True,
                round_id=str(round_id),
                connection=connection,
                stages=stages,
                skipped=True,
                skip_reason="split fingerprint unchanged since last tick",
                detail=detail,
            )

        # 5) Audit
        stages.append("audit")
        if self.audit_fn:
            detail["audit"] = self.audit_fn(live_path)
        else:
            try:
                from qs_everesteer.data.audit import audit_dataset

                detail["audit"] = audit_dataset(live_path).to_dict()
            except Exception as exc:  # noqa: BLE001
                detail["audit"] = {"error": f"{type(exc).__name__}: {exc}"}

        # 6) Infer champion / challengers
        stages.append("infer")
        infer_ctx = {
            "round_id": round_id,
            "event_id": event_id,
            "live_path": live_path,
            "split_fingerprint": split_fp,
            "candidate_id": candidate_id,
            **kwargs,
        }
        if self.infer_fn:
            inferred = self.infer_fn(infer_ctx)
        else:
            # Require explicit predictions for standalone use / tests.
            pred = kwargs.get("predictions_path")
            if not pred:
                return RoundTickResult(
                    ok=False,
                    round_id=str(round_id),
                    connection=connection,
                    stages=stages,
                    skipped=True,
                    skip_reason="no infer_fn and no predictions_path provided",
                    detail=detail,
                )
            inferred = {"predictions_path": pred, "candidate_id": candidate_id}
        detail["infer"] = {k: (str(v) if isinstance(v, Path) else v) for k, v in inferred.items()}
        candidate_id = str(inferred.get("candidate_id") or candidate_id)
        predictions_path = inferred.get("predictions_path") or kwargs.get("predictions_path")

        # 7) Ensemble (optional)
        stages.append("ensemble")
        if self.ensemble_fn:
            ens = self.ensemble_fn({**infer_ctx, **inferred})
            detail["ensemble"] = ens
            predictions_path = ens.get("predictions_path", predictions_path)
            candidate_id = str(ens.get("candidate_id") or candidate_id)
        else:
            detail["ensemble"] = {"skipped": True}

        # 8) Guard + submit via pipeline (respects mode + idempotency)
        stages.append("submit")
        caps = self.adapter.inspect()
        req = PipelineRequest(
            event_id=str(event_id),
            round_id=str(round_id),
            lane=str(kwargs.get("lane") or "live"),
            candidate_id=str(candidate_id),
            split_fingerprint=split_fp,
            action=action,
            event_snapshot_id=snap.get("snapshot_id"),
            expected_split_fingerprint=split_fp,
            expected_ids=kwargs.get("expected_ids"),
            predictions_path=predictions_path,
            artefact_path=kwargs.get("artefact_path") or inferred.get("artefact_path"),
            capabilities=caps,
            metadata={"source": "RoundController"},
        )
        # Ensure quota controller sees capabilities
        if self.pipeline.quota is None:
            self.pipeline.quota = QuotaController(
                repo_root=self.repo_root, capabilities=caps
            )
        else:
            self.pipeline.quota.capabilities = caps

        result = self.pipeline.run(req)
        detail["pipeline"] = result.to_dict()

        # 9) Observe
        stages.append("observe")
        clock = countdown(payload=detected)
        detail["countdown"] = clock

        # 10) Update state
        stages.append("update_state")
        state_path = self._update_state(
            round_id=str(round_id),
            snap=snap,
            connection=connection,
            fp=split_fp,
            submission=result.to_dict(),
            countdown=clock,
        )

        self._last_round = str(round_id)
        self._last_fingerprint = split_fp

        evidence = ensure_dir(runs_dir(self.repo_root) / "live" / str(round_id))
        tick_path = evidence / f"tick_{_utc_now_iso().replace(':', '')}.json"
        atomic_write_json(
            tick_path,
            {
                "round_id": round_id,
                "connection": connection,
                "stages": stages,
                "detail": detail,
                "submission_ok": result.ok,
                "idempotency_key": result.idempotency_key,
            },
        )

        return RoundTickResult(
            ok=result.ok,
            round_id=str(round_id),
            connection=connection,
            stages=stages,
            skipped=result.reused_prior,
            skip_reason="idempotent reuse" if result.reused_prior else None,
            submission=result.to_dict(),
            state_path=str(state_path),
            detail=detail,
        )

    def _detect_round(self) -> dict[str, Any]:
        if self.feed is not None:
            return self.feed.current_round()
        inspected = self.adapter.inspect()
        return {
            "connection": inspected.get("connection"),
            "round": inspected.get("current_round"),
            "event_id": inspected.get("event_id"),
            "observed_at": None,
            "deadline": None,
            "raw": inspected,
        }

    def _champion_id(self) -> str | None:
        try:
            from qs_everesteer.state.research import load_research_state

            state = load_research_state(self.repo_root)
            champ = state.get("champion")
            if isinstance(champ, dict):
                return champ.get("id") or champ.get("candidate_id")
            if isinstance(champ, str):
                return champ
        except Exception:  # noqa: BLE001
            return None
        return None

    def _update_state(
        self,
        *,
        round_id: str,
        snap: dict[str, Any],
        connection: str,
        fp: str,
        submission: dict[str, Any] | None = None,
        countdown: dict[str, Any] | None = None,
    ) -> Path:
        def _mutate(state: dict[str, Any]) -> None:
            state["round"] = round_id
            state["event_snapshot_id"] = snap.get("snapshot_id")
            state["connection"] = connection
            if countdown is not None:
                state["time_remaining_seconds"] = countdown.get("remaining_seconds")
            live = state.setdefault("live_evidence", {})
            live[round_id] = {
                "split_fingerprint": fp,
                "snapshot_id": snap.get("snapshot_id"),
                "updated_at": _utc_now_iso(),
                "submission": submission,
                "countdown": countdown,
            }
            meta = state.setdefault("meta", {})
            meta["updated_at"] = _utc_now_iso()
            meta["source"] = "RoundController"

        update_research_state(_mutate, repo_root=self.repo_root)
        return (self.repo_root / "runs" / "state" / "research_state.json").resolve()
