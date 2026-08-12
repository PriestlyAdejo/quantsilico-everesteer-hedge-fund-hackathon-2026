"""Submission pipeline: SELECT→INFER→VALIDATE→PACKAGE→DRY_RUN→SUBMIT→RECORD."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from qs_everesteer.fsutil import atomic_write_json, read_json, research_state_lock
from qs_everesteer.paths import ensure_dir, find_repo_root, state_dir
from qs_everesteer.state.research import SubmissionMode, load_research_state, update_research_state
from qs_everesteer.submission.guard import GuardResult, SubmissionContext, SubmissionGuard
from qs_everesteer.submission.mode import get_mode

STAGES: tuple[str, ...] = (
    "SELECT",
    "INFER",
    "VALIDATE",
    "PACKAGE",
    "DRY_RUN",
    "SUBMIT",
    "RECORD",
)


class StageStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SKIPPED = "SKIPPED"
    PASSED = "PASSED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


@dataclass
class StageResult:
    name: str
    status: StageStatus
    detail: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "detail": self.detail,
            "data": self.data,
        }


@dataclass
class PipelineResult:
    ok: bool
    mode: str
    idempotency_key: str
    stages: list[StageResult] = field(default_factory=list)
    guard: dict[str, Any] | None = None
    upload: dict[str, Any] | None = None
    blocked_reason: str | None = None
    reused_prior: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "mode": self.mode,
            "idempotency_key": self.idempotency_key,
            "stages": [s.to_dict() for s in self.stages],
            "guard": self.guard,
            "upload": self.upload,
            "blocked_reason": self.blocked_reason,
            "reused_prior": self.reused_prior,
        }


def make_idempotency_key(
    *,
    event_id: str | None,
    round_id: str | None,
    split_fingerprint: str | None,
    candidate_id: str | None,
    action: str,
) -> str:
    """
    Idempotency key ≈ event + round + split fingerprint + candidate + action.

    Stable SHA-256 hex (truncated) over the canonical joined material.
    """
    material = "|".join(
        [
            str(event_id or "UNKNOWN_EVENT"),
            str(round_id or "UNKNOWN_ROUND"),
            str(split_fingerprint or "UNKNOWN_SPLIT"),
            str(candidate_id or "UNKNOWN_CANDIDATE"),
            str(action or "UNKNOWN_ACTION"),
        ]
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def idempotency_path(repo_root: str | Path | None = None) -> Path:
    root = Path(repo_root) if repo_root is not None else find_repo_root()
    return state_dir(root) / "idempotency.json"


class IdempotencyLedger:
    """Filesystem ledger at ``runs/state/idempotency.json``."""

    def __init__(self, repo_root: str | Path | None = None) -> None:
        self.repo_root = Path(repo_root) if repo_root is not None else find_repo_root()
        self.path = idempotency_path(self.repo_root)

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema_version": 1, "entries": {}}
        data = read_json(self.path)
        if not isinstance(data, dict):
            return {"schema_version": 1, "entries": {}}
        data.setdefault("entries", {})
        return data

    def get(self, key: str) -> dict[str, Any] | None:
        with research_state_lock(self.repo_root):
            data = self._load()
            entry = data.get("entries", {}).get(key)
            return dict(entry) if isinstance(entry, dict) else None

    def record(self, key: str, entry: dict[str, Any]) -> dict[str, Any]:
        with research_state_lock(self.repo_root):
            data = self._load()
            payload = {
                **entry,
                "key": key,
                "recorded_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
            }
            data.setdefault("entries", {})[key] = payload
            ensure_dir(self.path.parent)
            atomic_write_json(self.path, data)
            return payload


class QuotaController:
    """
    Runtime upload budget from capabilities / research state.

    Never hardcodes 12/20 as truth. Unknown → null (not zero).
    Synthetic tests may set an explicit budget.
    """

    def __init__(
        self,
        *,
        repo_root: str | Path | None = None,
        explicit_cap: int | None = None,
        explicit_remaining: int | None = None,
        capabilities: dict[str, Any] | None = None,
    ) -> None:
        self.repo_root = Path(repo_root) if repo_root is not None else find_repo_root()
        self.explicit_cap = explicit_cap
        self.explicit_remaining = explicit_remaining
        self.capabilities = capabilities or {}

    def snapshot(self) -> dict[str, Any]:
        state = load_research_state(self.repo_root)
        budget = dict(state.get("upload_budget") or {})
        cap = self.explicit_cap
        if cap is None:
            cap = self.capabilities.get("submission_cap")
        if cap is None:
            cap = budget.get("cap")

        remaining = self.explicit_remaining
        if remaining is None:
            # Prefer live_remaining; fall back to practice; never invent.
            remaining = budget.get("live_remaining")
            if remaining is None:
                remaining = budget.get("practice_remaining")

        known = remaining is not None
        return {
            "cap": cap if cap is not None else None,
            "remaining": remaining if remaining is not None else None,
            "known": known,
            "source": (
                "explicit"
                if self.explicit_remaining is not None or self.explicit_cap is not None
                else ("capabilities" if self.capabilities.get("submission_cap") is not None else "research_state")
            ),
        }

    def permit(self, *, mode: SubmissionMode) -> tuple[bool, str | None]:
        snap = self.snapshot()
        if not snap["known"] or snap["remaining"] is None:
            if mode is SubmissionMode.DRY_RUN:
                return True, "quota UNKNOWN (DRY_RUN permitted)"
            if mode is SubmissionMode.DISABLED:
                return False, "submission DISABLED"
            return False, "quota UNKNOWN — refusing ARMED submit"
        if int(snap["remaining"]) <= 0:
            return False, f"no quota remaining ({snap['remaining']})"
        return True, None

    def consume(self, n: int = 1, *, lane: str = "live") -> dict[str, Any]:
        """Decrement remaining budget when known; no-op when UNKNOWN."""

        def _mutate(state: dict[str, Any]) -> None:
            budget = state.setdefault("upload_budget", {})
            key = (
                "practice_remaining"
                if lane.lower() in {"practice", "validation", "diagnostics"}
                else "live_remaining"
            )
            cur = budget.get(key)
            if cur is None:
                return
            budget[key] = max(0, int(cur) - int(n))

        return update_research_state(_mutate, repo_root=self.repo_root).get("upload_budget", {})


InferFn = Callable[[dict[str, Any]], Path | dict[str, Any]]
SelectFn = Callable[[dict[str, Any]], dict[str, Any]]
PackageFn = Callable[[dict[str, Any]], dict[str, Any]]
SubmitFn = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass
class PipelineRequest:
    event_id: str
    round_id: str
    lane: str
    candidate_id: str
    split_fingerprint: str
    action: str = "submit"
    event_snapshot_id: str | None = None
    expected_split_fingerprint: str | None = None
    expected_ids: list[str] | None = None
    predictions_path: str | Path | None = None
    artefact_path: str | Path | None = None
    capabilities: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class SubmissionPipeline:
    """Orchestrate guarded submission stages with idempotency + quota."""

    def __init__(
        self,
        *,
        repo_root: str | Path | None = None,
        adapter: Any | None = None,
        guard: SubmissionGuard | None = None,
        quota: QuotaController | None = None,
        ledger: IdempotencyLedger | None = None,
        select_fn: SelectFn | None = None,
        infer_fn: InferFn | None = None,
        package_fn: PackageFn | None = None,
        submit_fn: SubmitFn | None = None,
    ) -> None:
        self.repo_root = Path(repo_root) if repo_root is not None else find_repo_root()
        self.adapter = adapter
        self.guard = guard or SubmissionGuard()
        self.quota = quota or QuotaController(repo_root=self.repo_root)
        self.ledger = ledger or IdempotencyLedger(repo_root=self.repo_root)
        self.select_fn = select_fn
        self.infer_fn = infer_fn
        self.package_fn = package_fn
        self.submit_fn = submit_fn

    def run(self, request: PipelineRequest) -> PipelineResult:
        mode = get_mode(self.repo_root)
        key = make_idempotency_key(
            event_id=request.event_id,
            round_id=request.round_id,
            split_fingerprint=request.split_fingerprint,
            candidate_id=request.candidate_id,
            action=request.action,
        )
        prior = self.ledger.get(key)
        if prior and prior.get("status") in {"DRY_RUN_OK", "SUBMITTED", "RECORDED"}:
            return PipelineResult(
                ok=True,
                mode=mode.value,
                idempotency_key=key,
                stages=[
                    StageResult(
                        name="RECORD",
                        status=StageStatus.SKIPPED,
                        detail="idempotent reuse of prior result",
                        data={"prior": prior},
                    )
                ],
                upload=prior.get("upload"),
                reused_prior=True,
            )

        stages: list[StageResult] = []
        ctx_data: dict[str, Any] = {
            "event_id": request.event_id,
            "round_id": request.round_id,
            "lane": request.lane,
            "candidate_id": request.candidate_id,
            "split_fingerprint": request.split_fingerprint,
            "event_snapshot_id": request.event_snapshot_id,
            "predictions_path": request.predictions_path,
            "artefact_path": request.artefact_path,
            "metadata": dict(request.metadata),
        }

        if mode is SubmissionMode.DISABLED:
            stages.append(
                StageResult(
                    name="SELECT",
                    status=StageStatus.BLOCKED,
                    detail="submission mode DISABLED",
                )
            )
            return PipelineResult(
                ok=False,
                mode=mode.value,
                idempotency_key=key,
                stages=stages,
                blocked_reason="submission mode DISABLED",
            )

        # SELECT
        stages.append(self._run_stage("SELECT", lambda: self._select(ctx_data)))
        if stages[-1].status is StageStatus.FAILED:
            return self._fail(mode, key, stages)

        # INFER
        stages.append(self._run_stage("INFER", lambda: self._infer(ctx_data)))
        if stages[-1].status is StageStatus.FAILED:
            return self._fail(mode, key, stages)

        # VALIDATE (guard)
        quota_snap = self.quota.snapshot()
        if request.capabilities:
            self.quota.capabilities = request.capabilities
            quota_snap = self.quota.snapshot()

        guard_ctx = SubmissionContext(
            event_id=request.event_id,
            event_snapshot_id=request.event_snapshot_id,
            round_id=request.round_id,
            lane=request.lane,
            split_fingerprint=request.split_fingerprint,
            expected_split_fingerprint=request.expected_split_fingerprint
            or request.split_fingerprint,
            candidate_id=request.candidate_id,
            predictions_path=ctx_data.get("predictions_path"),
            expected_ids=request.expected_ids,
            artefact_path=ctx_data.get("artefact_path"),
            quota_remaining=quota_snap.get("remaining"),
            quota_known=bool(quota_snap.get("known")),
            capabilities=request.capabilities,
            mode=mode,
        )
        guard_result = self.guard.validate(guard_ctx)
        stages.append(
            StageResult(
                name="VALIDATE",
                status=StageStatus.PASSED if guard_result.ok else StageStatus.FAILED,
                detail="guard " + guard_result.verdict.value,
                data=guard_result.to_dict(),
            )
        )
        if not guard_result.ok:
            return PipelineResult(
                ok=False,
                mode=mode.value,
                idempotency_key=key,
                stages=stages,
                guard=guard_result.to_dict(),
                blocked_reason="; ".join(guard_result.blocking_reasons),
            )

        # PACKAGE
        stages.append(self._run_stage("PACKAGE", lambda: self._package(ctx_data)))
        if stages[-1].status is StageStatus.FAILED:
            return self._fail(mode, key, stages, guard=guard_result)

        # DRY_RUN stage always records packaging success without external upload
        stages.append(
            StageResult(
                name="DRY_RUN",
                status=StageStatus.PASSED,
                detail="full local path without external upload",
                data={
                    "predictions_path": str(ctx_data.get("predictions_path")),
                    "package": ctx_data.get("package"),
                },
            )
        )

        upload: dict[str, Any] | None = None
        if mode is SubmissionMode.DRY_RUN:
            stages.append(
                StageResult(
                    name="SUBMIT",
                    status=StageStatus.SKIPPED,
                    detail="DRY_RUN — external upload skipped",
                )
            )
            status = "DRY_RUN_OK"
        else:
            # ARMED — real submit if quota permits
            permitted, reason = self.quota.permit(mode=mode)
            if not permitted:
                stages.append(
                    StageResult(
                        name="SUBMIT",
                        status=StageStatus.BLOCKED,
                        detail=reason,
                    )
                )
                return PipelineResult(
                    ok=False,
                    mode=mode.value,
                    idempotency_key=key,
                    stages=stages,
                    guard=guard_result.to_dict(),
                    blocked_reason=reason,
                )
            try:
                upload = self._submit(ctx_data, request)
                stages.append(
                    StageResult(
                        name="SUBMIT",
                        status=StageStatus.PASSED,
                        detail="external upload completed",
                        data=upload if isinstance(upload, dict) else {"result": upload},
                    )
                )
                self.quota.consume(1, lane=request.lane)
                status = "SUBMITTED"
            except Exception as exc:  # noqa: BLE001
                stages.append(
                    StageResult(
                        name="SUBMIT",
                        status=StageStatus.FAILED,
                        detail=f"{type(exc).__name__}: {exc}",
                    )
                )
                return PipelineResult(
                    ok=False,
                    mode=mode.value,
                    idempotency_key=key,
                    stages=stages,
                    guard=guard_result.to_dict(),
                    blocked_reason=str(exc),
                )

        # RECORD
        record = {
            "status": status,
            "mode": mode.value,
            "event_id": request.event_id,
            "round_id": request.round_id,
            "lane": request.lane,
            "candidate_id": request.candidate_id,
            "split_fingerprint": request.split_fingerprint,
            "event_snapshot_id": request.event_snapshot_id,
            "predictions_path": str(ctx_data.get("predictions_path")),
            "upload": upload,
            "guard": guard_result.to_dict(),
        }
        self.ledger.record(key, record)
        evidence_dir = ensure_dir(
            self.repo_root / "runs" / "submissions" / request.round_id
        )
        evidence_path = evidence_dir / f"{key[:16]}_{status.lower()}.json"
        atomic_write_json(evidence_path, {**record, "idempotency_key": key, "stages": [s.to_dict() for s in stages]})
        stages.append(
            StageResult(
                name="RECORD",
                status=StageStatus.PASSED,
                detail=str(evidence_path),
                data={"path": str(evidence_path)},
            )
        )
        return PipelineResult(
            ok=True,
            mode=mode.value,
            idempotency_key=key,
            stages=stages,
            guard=guard_result.to_dict(),
            upload=upload,
        )

    def _fail(
        self,
        mode: SubmissionMode,
        key: str,
        stages: list[StageResult],
        guard: GuardResult | None = None,
    ) -> PipelineResult:
        detail = stages[-1].detail if stages else "pipeline failed"
        return PipelineResult(
            ok=False,
            mode=mode.value,
            idempotency_key=key,
            stages=stages,
            guard=guard.to_dict() if guard else None,
            blocked_reason=detail,
        )

    def _run_stage(self, name: str, fn: Callable[[], dict[str, Any]]) -> StageResult:
        try:
            data = fn() or {}
            return StageResult(name=name, status=StageStatus.PASSED, data=data)
        except Exception as exc:  # noqa: BLE001
            return StageResult(
                name=name,
                status=StageStatus.FAILED,
                detail=f"{type(exc).__name__}: {exc}",
            )

    def _select(self, ctx: dict[str, Any]) -> dict[str, Any]:
        if self.select_fn:
            selected = self.select_fn(ctx)
            ctx.update(selected)
            return selected
        return {
            "candidate_id": ctx["candidate_id"],
            "lane": ctx["lane"],
        }

    def _infer(self, ctx: dict[str, Any]) -> dict[str, Any]:
        if self.infer_fn:
            result = self.infer_fn(ctx)
            if isinstance(result, Path):
                ctx["predictions_path"] = result
                return {"predictions_path": str(result)}
            ctx.update(result)
            return result
        if ctx.get("predictions_path"):
            return {"predictions_path": str(ctx["predictions_path"])}
        raise RuntimeError("INFER requires infer_fn or precomputed predictions_path")

    def _package(self, ctx: dict[str, Any]) -> dict[str, Any]:
        if self.package_fn:
            packaged = self.package_fn(ctx)
            ctx["package"] = packaged
            return packaged
        path = ctx.get("predictions_path")
        package = {
            "predictions_path": str(path) if path else None,
            "artefact_path": str(ctx["artefact_path"]) if ctx.get("artefact_path") else None,
            "candidate_id": ctx.get("candidate_id"),
        }
        ctx["package"] = package
        return package

    def _submit(self, ctx: dict[str, Any], request: PipelineRequest) -> dict[str, Any]:
        if self.submit_fn:
            return self.submit_fn(ctx)
        if self.adapter is None:
            raise RuntimeError("ARMED submit requires adapter or submit_fn")
        result = self.adapter.submit_predictions(
            model_id=str(request.candidate_id),
            predictions_path=ctx["predictions_path"],
            lane=request.lane,
            model_pkl=ctx.get("artefact_path"),
        )
        return result if isinstance(result, dict) else {"result": result}
