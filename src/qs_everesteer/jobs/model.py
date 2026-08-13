"""Job dataclass aligned with the Figma Research Console Job fields."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import IntEnum, StrEnum
from typing import Any
from uuid import uuid4


class JobStatus(StrEnum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    BLOCKED = "BLOCKED"


class JobPriority(IntEnum):
    """Lower values run first; names reflect the event operating lanes."""

    LIVE_INTEGRITY = 0
    ROUND_RECOVERY = 1
    CHAMPION_PROMOTION = 2
    PRACTICE = 3
    AUTOML = 4
    RESEARCH = 5


class JobKind(StrEnum):
    TRAIN = "TRAIN"
    INFER = "INFER"
    VALIDATE = "VALIDATE"
    DATA_PULL = "DATA_PULL"
    ENSEMBLE = "ENSEMBLE"
    SCORER_PARITY = "SCORER_PARITY"
    SUBMIT = "SUBMIT"
    DOCS = "DOCS"


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class Job:
    id: str
    name: str
    type: str
    status: JobStatus
    device: str = "CPU"
    candidate: str | None = None
    started_at: str | None = None
    eta_seconds: int | None = None
    total_seconds: int | None = None
    progress: float | None = None
    queue_position: int | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    priority: int = int(JobPriority.AUTOML)
    deadline: str | None = None
    created_at: str = field(default_factory=utc_now_iso)
    dependencies: list[str] = field(default_factory=list)
    attempt: int = 0
    maximum_attempts: int = 2
    lease_owner: str | None = None
    lease_expires_at: str | None = None
    heartbeat_at: str | None = None
    process_id: int | None = None
    # Monotonic clock snapshot (perf_counter) when RUNNING began; not serialized to UI.
    _mono_start: float | None = field(default=None, repr=False, compare=False)

    @classmethod
    def create(
        cls,
        *,
        kind: str | JobKind,
        name: str | None = None,
        candidate: str | None = None,
        device: str = "CPU",
        payload: dict[str, Any] | None = None,
        eta_seconds: int | None = None,
        queue_position: int | None = None,
        job_id: str | None = None,
        priority: int | JobPriority = JobPriority.AUTOML,
        deadline: str | None = None,
        dependencies: list[str] | None = None,
        maximum_attempts: int = 2,
    ) -> Job:
        kind_s = kind.value if isinstance(kind, JobKind) else str(kind)
        return cls(
            id=job_id or f"job-{uuid4().hex[:12]}",
            name=name or kind_s.lower(),
            type=kind_s,
            status=JobStatus.QUEUED,
            device=device,
            candidate=candidate,
            started_at=None,
            eta_seconds=eta_seconds,
            total_seconds=None,
            progress=0.0,
            queue_position=queue_position,
            payload=dict(payload or {}),
            error=None,
            priority=int(priority),
            deadline=deadline,
            dependencies=list(dependencies or []),
            maximum_attempts=max(1, int(maximum_attempts)),
        )

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("_mono_start", None)
        d["status"] = self.status.value if isinstance(self.status, JobStatus) else str(self.status)
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Job:
        payload = dict(data.get("payload") or {})
        status_raw = data.get("status", JobStatus.PENDING)
        status = JobStatus(status_raw) if not isinstance(status_raw, JobStatus) else status_raw
        return cls(
            id=str(data["id"]),
            name=str(data.get("name") or data.get("type") or "job"),
            type=str(data.get("type") or "TRAIN"),
            status=status,
            device=str(data.get("device") or "CPU"),
            candidate=data.get("candidate"),
            started_at=data.get("started_at"),
            eta_seconds=data.get("eta_seconds"),
            total_seconds=data.get("total_seconds"),
            progress=data.get("progress"),
            queue_position=data.get("queue_position"),
            payload=payload,
            error=data.get("error"),
            priority=int(data.get("priority", JobPriority.AUTOML)),
            deadline=data.get("deadline"),
            created_at=str(data.get("created_at") or utc_now_iso()),
            dependencies=list(data.get("dependencies") or []),
            attempt=int(data.get("attempt", 0)),
            maximum_attempts=max(1, int(data.get("maximum_attempts", 2))),
            lease_owner=data.get("lease_owner"),
            lease_expires_at=data.get("lease_expires_at"),
            heartbeat_at=data.get("heartbeat_at"),
            process_id=data.get("process_id"),
            _mono_start=data.get("_mono_start"),
        )
