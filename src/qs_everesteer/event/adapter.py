"""Thin capability-detecting wrapper around the pinned everestapi SDK."""

from __future__ import annotations

import hashlib
import os
import shutil
from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

from qs_everesteer.contracts import EventCapabilities, Provenance
from qs_everesteer.fsutil import atomic_write_json
from qs_everesteer.paths import ensure_dir, find_repo_root, runs_dir

# Methods probed during capability discovery (presence ≠ availability).
_CAPABILITY_PROBES: tuple[tuple[str, str], ...] = (
    ("get_capabilities", "platform_capabilities"),
    ("get_started", "get_started"),
    ("get_profile", "profile"),
    ("get_status", "status"),
    ("health", "health"),
    ("explain_scoring", "scoring"),
    ("get_dataset_info", "dataset_info"),
    ("get_current_round", "current_round"),
    ("get_rounds", "rounds"),
    ("get_leaderboard", "leaderboard"),
    ("get_diagnostics_leaderboard", "diagnostics_leaderboard"),
    ("get_diagnostics_standings", "standings"),
    ("get_event_staking", "staking"),
    ("get_final_selection", "final_selection"),
    ("set_final_selection", "set_final_selection"),
    ("get_stake_balance", "stake_balance"),
    ("get_compute_credits", "server_compute"),
    ("list_compute_jobs", "server_compute_jobs"),
    ("submit_validation_diagnostics", "practice_submit"),
    ("submit_event_predictions", "live_submit"),
    ("submit_predictions", "equities_submit"),
    ("validate_submission", "validate_submission"),
    ("download_dataset", "download_dataset"),
    ("download_futures_data", "download_futures_data"),
)


class ConnectionStatus(StrEnum):
    LIVE = "LIVE"
    DISCONNECTED = "DISCONNECTED"
    RECONNECTING = "RECONNECTING"
    NOT_CONNECTED = "NOT_CONNECTED"
    UNAVAILABLE = "UNAVAILABLE"
    SYNTHETIC = "SYNTHETIC"


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _safe_call(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> tuple[Any | None, str | None]:
    try:
        return fn(*args, **kwargs), None
    except Exception as exc:  # noqa: BLE001 — structured unavailable, never crash inspect
        return None, f"{type(exc).__name__}: {exc}"


def _has_method(obj: Any, name: str) -> bool:
    return callable(getattr(obj, name, None))


def sdk_version() -> str:
    """Return installed everestapi version string, or UNKNOWN."""
    try:
        import importlib.metadata as md

        return md.version("everestapi")
    except Exception:  # noqa: BLE001
        try:
            import everestapi

            return str(getattr(everestapi, "__version__", "UNKNOWN") or "UNKNOWN")
        except Exception:  # noqa: BLE001
            return "UNKNOWN"


def safe_key_fingerprint(api_key: str | None) -> str | None:
    """SHA-256 fingerprint of an API key. Never returns or logs the raw key."""
    if not api_key:
        return None
    digest = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
    return digest[:16]


def synthetic_mode_enabled(flag: bool | None = None) -> bool:
    if flag is not None:
        return bool(flag)
    raw = os.environ.get("QSEH_SYNTHETIC", "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


class SimulatedEventFeed:
    """
    In-process mock/sim feed for tests and rehearsals.

    Can disconnect / reconnect without inventing official leaderboard numbers.
    """

    def __init__(
        self,
        *,
        event_id: str = "SYNTHETIC_EVENT",
        round_id: str = "SYN-R0",
        deadline: str | None = None,
    ) -> None:
        self.event_id = event_id
        self.round_id = round_id
        self.deadline = deadline
        self._status = ConnectionStatus.LIVE
        self._observed_at = _utc_now_iso()

    @property
    def status(self) -> ConnectionStatus:
        return self._status

    def disconnect(self) -> ConnectionStatus:
        self._status = ConnectionStatus.DISCONNECTED
        return self._status

    def reconnect(self, *, settle: bool = True) -> ConnectionStatus:
        """
        Transition DISCONNECTED → RECONNECTING → LIVE.

        When settle=False, remain on RECONNECTING so callers can assert the
        intermediate state before completing the handshake.
        """
        self._status = ConnectionStatus.RECONNECTING
        self._observed_at = _utc_now_iso()
        if settle:
            self._status = ConnectionStatus.LIVE
        return self._status

    def settle(self) -> ConnectionStatus:
        """Complete a held reconnect (RECONNECTING → LIVE)."""
        if self._status == ConnectionStatus.RECONNECTING:
            self._status = ConnectionStatus.LIVE
            self._observed_at = _utc_now_iso()
        return self._status

    def tick_observation(self) -> str:
        self._observed_at = _utc_now_iso()
        return self._observed_at

    def current_round(self) -> dict[str, Any]:
        if self._status == ConnectionStatus.DISCONNECTED:
            return {
                "connection": ConnectionStatus.DISCONNECTED.value,
                "round": None,
                "event_id": self.event_id,
                "observed_at": None,
                "provenance": Provenance.SYNTHETIC_FIXTURE.value,
                "note": "feed disconnected — no fabricated round state",
            }
        if self._status == ConnectionStatus.RECONNECTING:
            return {
                "connection": ConnectionStatus.RECONNECTING.value,
                "event_id": self.event_id,
                "round": self.round_id,
                "deadline": self.deadline,
                "observed_at": self._observed_at,
                "provenance": Provenance.SYNTHETIC_FIXTURE.value,
                "note": "SYNTHETIC_FIXTURE — reconnecting; not swapping to demo fixtures",
            }
        return {
            "connection": self._status.value,
            "event_id": self.event_id,
            "round": self.round_id,
            "deadline": self.deadline,
            "observed_at": self._observed_at,
            "provenance": Provenance.SYNTHETIC_FIXTURE.value,
            "note": "SYNTHETIC_FIXTURE — not official Everesteer state",
        }


class EveresteerAdapter:
    """Capability-discovering Everesteer / everestapi adapter."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        tournament: str = "futures",
        synthetic: bool | None = None,
        client: Any | None = None,
        feed: SimulatedEventFeed | None = None,
    ) -> None:
        self._explicit_key = api_key
        self.api_key = api_key or os.getenv("EIQ_API_KEY") or os.getenv("EVEREST_API_KEY") or ""
        self.base_url = base_url
        self.tournament = tournament
        self.synthetic = synthetic_mode_enabled(synthetic)
        self._client = client
        self.feed = feed
        self._last_error: str | None = None

    # ------------------------------------------------------------------ SDK
    def sdk_version(self) -> str:
        return sdk_version()

    def safe_key_fingerprint(self) -> str | None:
        return safe_key_fingerprint(self.api_key or None)

    def _get_client(self) -> Any | None:
        if self._client is not None:
            return self._client
        if self.synthetic and not self.api_key:
            return None
        try:
            from everestapi.client import EverestAPI
        except Exception as exc:  # noqa: BLE001
            self._last_error = f"{type(exc).__name__}: {exc}"
            return None
        kwargs: dict[str, Any] = {"tournament": self.tournament}
        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.base_url:
            kwargs["base_url"] = self.base_url
        try:
            self._client = EverestAPI(**kwargs)
        except Exception as exc:  # noqa: BLE001
            self._last_error = f"{type(exc).__name__}: {exc}"
            return None
        return self._client

    def _discover_methods(self, client: Any | None) -> dict[str, bool]:
        out: dict[str, bool] = {}
        for method_name, _label in _CAPABILITY_PROBES:
            out[method_name] = _has_method(client, method_name) if client is not None else False
        return out

    def inspect(self) -> dict[str, Any]:
        """
        Return EventCapabilities-like dict plus connection status.

        Missing methods / failed probes become structured UNAVAILABLE / null —
        never fabricated zeros for quotas or standings.
        """
        version = self.sdk_version()
        key_fp = self.safe_key_fingerprint()
        methods_present: dict[str, bool] = {}
        probes: dict[str, Any] = {}
        connection = ConnectionStatus.NOT_CONNECTED.value
        api_scope: str | None = None
        tournament: str | None = self.tournament
        validation_available: bool | None = None
        live_available: bool | None = None
        standings_available: bool | None = None
        staking_available: bool | None = None
        final_selection_available: bool | None = None
        server_compute_available: bool | None = None
        submission_cap: int | None = None
        current_round: str | None = None
        event_id: str | None = None
        raw: dict[str, Any] = {}

        if self.feed is not None:
            feed_round = self.feed.current_round()
            connection = str(feed_round.get("connection") or ConnectionStatus.SYNTHETIC.value)
            current_round = feed_round.get("round")
            event_id = feed_round.get("event_id")
            raw["feed"] = feed_round
            caps = EventCapabilities(
                sdk_version=version,
                api_scope=api_scope,
                tournament=tournament,
                validation_available=True,
                live_available=True,
                standings_available=None,
                staking_available=None,
                final_selection_available=None,
                server_compute_available=None,
                submission_cap=None,
                current_round=current_round,
                raw=raw,
            )
            return {
                **asdict(caps),
                "connection": connection,
                "event_id": event_id,
                "key_fingerprint": key_fp,
                "methods_present": methods_present,
                "probes": probes,
                "synthetic": True,
                "error": None,
                "provenance": Provenance.SYNTHETIC_FIXTURE.value,
            }

        client = self._get_client()
        methods_present = self._discover_methods(client)

        if client is None:
            if self.synthetic:
                connection = ConnectionStatus.SYNTHETIC.value
                err = None
            else:
                connection = ConnectionStatus.UNAVAILABLE.value
                err = self._last_error or "no SDK client (missing credentials or import failure)"
            caps = EventCapabilities(
                sdk_version=version,
                submission_cap=None,
                current_round=None,
                raw={"note": err},
            )
            return {
                **asdict(caps),
                "connection": connection,
                "event_id": None,
                "key_fingerprint": key_fp,
                "methods_present": methods_present,
                "probes": {},
                "synthetic": self.synthetic,
                "error": err,
                "provenance": (
                    Provenance.SYNTHETIC_FIXTURE.value
                    if self.synthetic
                    else Provenance.OFFICIAL_PLATFORM_OBSERVATION.value
                ),
            }

        # Lightweight connectivity probe — prefer health, else get_started.
        connected = False
        for probe_name in ("health", "get_started", "get_status"):
            if not methods_present.get(probe_name):
                continue
            value, err = _safe_call(getattr(client, probe_name))
            probes[probe_name] = {"ok": err is None, "error": err, "value": value if err is None else None}
            if err is None:
                connected = True
                if isinstance(value, dict):
                    raw[probe_name] = value
                    api_scope = api_scope or value.get("scope") or value.get("api_scope")
                    event_id = event_id or value.get("event_id") or value.get("event")
                    if probe_name == "get_started":
                        validation_available = _truthy_or_none(
                            value.get("validation_available", value.get("practice_available"))
                        )
                        live_available = _truthy_or_none(
                            value.get("live_available", value.get("event_available"))
                        )
                break

        connection = (
            ConnectionStatus.LIVE.value if connected else ConnectionStatus.UNAVAILABLE.value
        )

        # Optional capability probes — getattr only; failures → UNAVAILABLE.
        optional_calls: list[tuple[str, str]] = [
            ("get_current_round", "current_round"),
            ("get_diagnostics_standings", "standings"),
            ("get_event_staking", "staking"),
            ("get_final_selection", "final_selection"),
            ("get_compute_credits", "server_compute"),
            ("explain_scoring", "scoring"),
            ("get_dataset_info", "dataset_info"),
            ("get_capabilities", "platform_capabilities"),
        ]
        for method_name, label in optional_calls:
            if not methods_present.get(method_name):
                probes[label] = {"ok": False, "error": "method_absent", "value": None}
                continue
            fn = getattr(client, method_name)
            kwargs: dict[str, Any] = {}
            if method_name == "get_current_round":
                kwargs = {"tournament": self.tournament}
            value, err = _safe_call(fn, **kwargs) if kwargs else _safe_call(fn)
            probes[label] = {"ok": err is None, "error": err, "value": value if err is None else None}
            if err is not None or not isinstance(value, dict):
                continue
            raw[label] = value
            if label == "current_round":
                current_round = (
                    value.get("round")
                    or value.get("round_id")
                    or value.get("id")
                    or value.get("name")
                )
                if current_round is not None:
                    current_round = str(current_round)
            elif label == "standings":
                standings_available = True
            elif label == "staking":
                staking_available = True
            elif label == "final_selection":
                final_selection_available = True
            elif label == "server_compute":
                server_compute_available = True

        # Method presence as soft availability when live probes were not attempted.
        if validation_available is None:
            validation_available = methods_present.get("submit_validation_diagnostics")
        if live_available is None:
            live_available = methods_present.get("submit_event_predictions")
        if standings_available is None and methods_present.get("get_diagnostics_standings"):
            standings_available = None  # present but not confirmed
        if staking_available is None and methods_present.get("get_event_staking"):
            staking_available = None
        if final_selection_available is None:
            final_selection_available = (
                None if methods_present.get("get_final_selection") else False
            )
        if server_compute_available is None and methods_present.get("get_compute_credits"):
            server_compute_available = None

        # Submission cap: only from explicit fields — never invent 12/20.
        submission_cap = _extract_submission_cap(raw)

        caps = EventCapabilities(
            sdk_version=version,
            api_scope=str(api_scope) if api_scope is not None else None,
            tournament=tournament,
            validation_available=validation_available,
            live_available=live_available,
            standings_available=standings_available,
            staking_available=staking_available,
            final_selection_available=final_selection_available,
            server_compute_available=server_compute_available,
            submission_cap=submission_cap,
            current_round=current_round,
            raw=raw,
        )
        return {
            **asdict(caps),
            "connection": connection,
            "event_id": str(event_id) if event_id is not None else None,
            "key_fingerprint": key_fp,
            "methods_present": methods_present,
            "probes": {
                k: {"ok": v.get("ok"), "error": v.get("error")} for k, v in probes.items()
            },
            "synthetic": False,
            "error": None if connected else (self._last_error or "connection_failed"),
            "provenance": Provenance.OFFICIAL_PLATFORM_OBSERVATION.value,
        }

    def snapshot(self, repo_root: str | Path | None = None) -> dict[str, Any]:
        """Inspect capabilities and write ``runs/event/event_snapshot_<ts>.json``."""
        root = Path(repo_root) if repo_root is not None else find_repo_root()
        inspected = self.inspect()
        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        snapshot_id = f"event_snapshot_{ts}_{uuid4().hex[:8]}"
        event_dir = ensure_dir(runs_dir(root) / "event")
        path = event_dir / f"event_snapshot_{ts}.json"
        record = {
            "snapshot_id": snapshot_id,
            "observed_at": _utc_now_iso(),
            "sdk_version": inspected.get("sdk_version"),
            "api_scope": inspected.get("api_scope"),
            "key_fingerprint": inspected.get("key_fingerprint"),
            "event_id": inspected.get("event_id"),
            "tournament": inspected.get("tournament"),
            "connection": inspected.get("connection"),
            "started": inspected.get("raw", {}).get("get_started") or {},
            "dataset_info": inspected.get("raw", {}).get("dataset_info") or {},
            "scoring": inspected.get("raw", {}).get("scoring") or {},
            "staking": inspected.get("raw", {}).get("staking") or {},
            "submission_cap": inspected.get("submission_cap"),
            "server_compute": inspected.get("raw", {}).get("server_compute") or {},
            "current_round": inspected.get("current_round"),
            "methods_present": inspected.get("methods_present") or {},
            "capabilities": {
                k: inspected.get(k)
                for k in (
                    "validation_available",
                    "live_available",
                    "standings_available",
                    "staking_available",
                    "final_selection_available",
                    "server_compute_available",
                )
            },
            "provenance": inspected.get("provenance"),
            "synthetic": inspected.get("synthetic"),
            "error": inspected.get("error"),
            "path": str(path),
        }
        atomic_write_json(path, record)
        return record

    def pull_split(
        self,
        split: str,
        dest: str | Path,
        *,
        repo_root: str | Path | None = None,
    ) -> Path:
        """
        Download a dataset split to *dest*.

        When credentials / SDK are unavailable and ``QSEH_SYNTHETIC=1`` (or
        ``synthetic=True``), copies/generates a synthetic fixture instead.
        """
        dest_path = Path(dest)
        ensure_dir(dest_path.parent if dest_path.suffix else dest_path)

        client = self._get_client()
        if client is not None and not self.synthetic:
            out_file = dest_path if dest_path.suffix else dest_path / f"{split}.parquet"
            ensure_dir(out_file.parent)
            if _has_method(client, "download_dataset"):
                result, err = _safe_call(
                    client.download_dataset,
                    universe=self.tournament,
                    split=split,
                    output_path=str(out_file),
                )
                if err is None:
                    return Path(result or out_file).resolve()
                self._last_error = err
            if _has_method(client, "download_futures_data"):
                result, err = _safe_call(
                    client.download_futures_data,
                    split=split,
                    output_path=str(out_file),
                )
                if err is None:
                    return Path(result or out_file).resolve()
                self._last_error = err
            raise RuntimeError(
                f"pull_split failed for split={split!r}: {self._last_error or 'no download method'}"
            )

        if not self.synthetic and not self.api_key:
            raise RuntimeError(
                "pull_split: no credentials; set EIQ_API_KEY or QSEH_SYNTHETIC=1 for fixtures"
            )

        return self._pull_synthetic(split, dest_path, repo_root=repo_root)

    def submit_predictions(
        self,
        *,
        model_id: str,
        predictions_path: str | Path,
        lane: str = "practice",
        model_pkl: str | Path | None = None,
        target: str = "target_everest_20",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Real upload path (practice diagnostics or live event).

        Callers must gate this behind ARMED mode + SubmissionGuard. This method
        never auto-arms and never runs in synthetic mode.
        """
        if self.synthetic:
            raise RuntimeError("submit_predictions refused: adapter is in synthetic mode")
        client = self._get_client()
        if client is None:
            raise RuntimeError("submit_predictions: SDK client unavailable")

        lane_norm = lane.strip().lower()
        if lane_norm in {"practice", "validation", "diagnostics"}:
            if not _has_method(client, "submit_validation_diagnostics"):
                raise RuntimeError("submit_validation_diagnostics method absent on SDK")
            return client.submit_validation_diagnostics(
                model_id,
                str(predictions_path),
                tournament=self.tournament,
                target=target,
                model_pkl=str(model_pkl) if model_pkl else None,
                **kwargs,
            )
        if lane_norm in {"live", "event"}:
            if not _has_method(client, "submit_event_predictions"):
                raise RuntimeError("submit_event_predictions method absent on SDK")
            return client.submit_event_predictions(
                model_id,
                str(predictions_path),
                tournament=self.tournament,
                target=target,
                model_pkl=str(model_pkl) if model_pkl else None,
                **kwargs,
            )
        raise ValueError(f"unknown submission lane: {lane!r}")

    def _pull_synthetic(
        self,
        split: str,
        dest: Path,
        *,
        repo_root: str | Path | None = None,
    ) -> Path:
        from qs_everesteer.data.synthetic import generate_synthetic_event_data
        from qs_everesteer.paths import synthetic_data_dir

        root = Path(repo_root) if repo_root is not None else find_repo_root()
        syn_dir = synthetic_data_dir(root)
        split_key = split.strip().lower()
        if split_key in {"val", "valid"}:
            split_key = "validation"
        expected = syn_dir / f"{split_key}.parquet"
        if not expected.exists():
            generate_synthetic_event_data(syn_dir)
        if not expected.exists():
            raise FileNotFoundError(f"synthetic split not found after generation: {expected}")

        out_file = dest if dest.suffix else dest / f"{split_key}.parquet"
        ensure_dir(out_file.parent)
        shutil.copy2(expected, out_file)
        # Sidecar marker so audits can see synthetic provenance.
        marker = out_file.with_suffix(out_file.suffix + ".synthetic.json")
        atomic_write_json(
            marker,
            {
                "synthetic": True,
                "split": split_key,
                "source": str(expected),
                "note": "SYNTHETIC_FIXTURE — not official Everesteer data",
                "provenance": Provenance.SYNTHETIC_FIXTURE.value,
            },
        )
        return out_file.resolve()


def _truthy_or_none(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"", "unknown", "null", "none"}:
            return None
        if lowered in {"1", "true", "yes", "available"}:
            return True
        if lowered in {"0", "false", "no", "unavailable"}:
            return False
    return bool(value)


def _extract_submission_cap(raw: dict[str, Any]) -> int | None:
    """Pull a numeric upload/submission cap when explicitly present; else None."""
    candidates: list[Any] = []
    for blob in raw.values():
        if not isinstance(blob, dict):
            continue
        for key in (
            "submission_cap",
            "upload_cap",
            "uploads_remaining",
            "account_upload_cap",
            "max_submissions",
            "quota_total",
        ):
            if key in blob:
                candidates.append(blob.get(key))
        budget = blob.get("upload_budget") or blob.get("quota")
        if isinstance(budget, dict):
            for key in ("cap", "total", "limit"):
                if key in budget:
                    candidates.append(budget.get(key))
    for value in candidates:
        if value is None:
            continue
        if isinstance(value, bool):
            continue
        if isinstance(value, int):
            return value
        if isinstance(value, float) and value.is_integer():
            return int(value)
        if isinstance(value, str) and value.strip().isdigit():
            return int(value.strip())
    return None


# Back-compat alias for the scaffold name.
EveresteerEventAdapter = EveresteerAdapter
