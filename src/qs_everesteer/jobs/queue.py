"""Filesystem-backed job queue under ``runs/jobs/``."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from filelock import FileLock

from qs_everesteer.fsutil import atomic_write_json, read_json
from qs_everesteer.jobs.model import Job, JobKind, JobPriority, JobStatus
from qs_everesteer.paths import ensure_dir, find_repo_root, jobs_dir


def _jobs_root(repo_root: str | Path | None = None) -> Path:
    root = Path(repo_root) if repo_root is not None else find_repo_root()
    return ensure_dir(jobs_dir(root))


def _job_path(job_id: str, repo_root: str | Path | None = None) -> Path:
    return _jobs_root(repo_root) / f"{job_id}.json"


def _queue_lock(repo_root: str | Path | None = None) -> FileLock:
    root = _jobs_root(repo_root)
    return FileLock(str(root / ".queue.lock"), timeout=30.0)


def save_job(job: Job, repo_root: str | Path | None = None) -> Path:
    path = _job_path(job.id, repo_root)
    atomic_write_json(path, job.to_dict())
    return path.resolve()


def load_job(job_id: str, repo_root: str | Path | None = None) -> Job:
    path = _job_path(job_id, repo_root)
    if not path.exists():
        raise FileNotFoundError(f"job not found: {job_id} ({path})")
    return Job.from_dict(read_json(path))


def list_jobs(
    repo_root: str | Path | None = None,
    *,
    status: JobStatus | str | None = None,
    kind: JobKind | str | None = None,
) -> list[Job]:
    root = _jobs_root(repo_root)
    jobs: list[Job] = []
    for path in sorted(root.glob("job-*.json")):
        try:
            job = Job.from_dict(read_json(path))
        except Exception:  # noqa: BLE001, S112
            continue
        if status is not None:
            want = status.value if isinstance(status, JobStatus) else str(status)
            if job.status.value != want:
                continue
        if kind is not None:
            want_k = kind.value if isinstance(kind, JobKind) else str(kind)
            if job.type != want_k:
                continue
        jobs.append(job)
    return jobs


def estimate_eta(
    kind: str | JobKind,
    repo_root: str | Path | None = None,
    *,
    default_seconds: int = 60,
) -> int:
    """Soft ETA from mean ``total_seconds`` of prior DONE jobs of the same type."""
    kind_s = kind.value if isinstance(kind, JobKind) else str(kind)
    durations = [
        j.total_seconds
        for j in list_jobs(repo_root, status=JobStatus.DONE, kind=kind_s)
        if j.total_seconds is not None and j.total_seconds >= 0
    ]
    if not durations:
        return default_seconds
    return round(sum(durations) / len(durations))


def enqueue(
    kind: str | JobKind,
    payload: dict[str, Any] | None = None,
    *,
    repo_root: str | Path | None = None,
    name: str | None = None,
    candidate: str | None = None,
    device: str = "CPU",
    job_id: str | None = None,
    priority: int | JobPriority = JobPriority.AUTOML,
    deadline: str | None = None,
    dependencies: list[str] | None = None,
    maximum_attempts: int = 2,
) -> str:
    """Write a QUEUED job JSON under ``runs/jobs/`` and return its id."""
    root = Path(repo_root) if repo_root is not None else find_repo_root()
    with _queue_lock(root):
        queued = list_jobs(root, status=JobStatus.QUEUED)
        position = len(queued) + 1
        eta = estimate_eta(kind, root)
        job = Job.create(
            kind=kind,
            name=name,
            candidate=candidate,
            device=device,
            payload=payload,
            eta_seconds=eta,
            queue_position=position,
            job_id=job_id,
            priority=priority,
            deadline=deadline,
            dependencies=dependencies,
            maximum_attempts=maximum_attempts,
        )
        save_job(job, root)
    recompute_queue_positions(root)
    return job.id


def recompute_queue_positions(repo_root: str | Path | None = None) -> None:
    root = Path(repo_root) if repo_root is not None else find_repo_root()
    with _queue_lock(root):
        queued = sorted(list_jobs(root, status=JobStatus.QUEUED), key=_queue_key)
        for idx, job in enumerate(queued, start=1):
            job.queue_position = idx
            save_job(job, root)


def _queue_key(job: Job) -> tuple[int, str, str, str, str]:
    # Missing deadlines sort after real deadlines; created_at preserves FIFO among peers.
    return (job.priority, "0" if job.deadline else "1", job.deadline or "", job.created_at, job.id)


def _dependencies_done(job: Job, root: Path) -> bool:
    for dep_id in job.dependencies:
        try:
            if load_job(dep_id, root).status != JobStatus.DONE:
                return False
        except FileNotFoundError:
            return False
    return True


def claim_next_job(
    worker_id: str,
    repo_root: str | Path | None = None,
    *,
    lease_seconds: int = 60,
) -> Job | None:
    """Atomically lease the highest-priority runnable job."""
    root = Path(repo_root) if repo_root is not None else find_repo_root()
    with _queue_lock(root):
        queued = sorted(list_jobs(root, status=JobStatus.QUEUED), key=_queue_key)
        job = next((item for item in queued if _dependencies_done(item, root)), None)
        if job is None:
            return None
        now = datetime.now(UTC)
        job.status = JobStatus.RUNNING
        job.lease_owner = worker_id
        job.heartbeat_at = now.isoformat()
        job.lease_expires_at = (now + timedelta(seconds=max(1, lease_seconds))).isoformat()
        job.attempt += 1
        job.queue_position = None
        save_job(job, root)
    recompute_queue_positions(root)
    return job


def heartbeat_job(
    job_id: str,
    worker_id: str,
    repo_root: str | Path | None = None,
    *,
    lease_seconds: int = 60,
) -> Job:
    root = Path(repo_root) if repo_root is not None else find_repo_root()
    with _queue_lock(root):
        job = load_job(job_id, root)
        if job.status != JobStatus.RUNNING or job.lease_owner != worker_id:
            raise RuntimeError("job is not leased by this worker")
        now = datetime.now(UTC)
        job.heartbeat_at = now.isoformat()
        job.lease_expires_at = (now + timedelta(seconds=max(1, lease_seconds))).isoformat()
        save_job(job, root)
        return job


def recover_stale_jobs(repo_root: str | Path | None = None, *, now: datetime | None = None) -> list[str]:
    """Requeue expired attempts, preserving attempt/failure evidence."""
    root = Path(repo_root) if repo_root is not None else find_repo_root()
    now = now or datetime.now(UTC)
    recovered: list[str] = []
    with _queue_lock(root):
        for job in list_jobs(root, status=JobStatus.RUNNING):
            if not job.lease_expires_at:
                continue
            expiry = datetime.fromisoformat(job.lease_expires_at)
            if expiry > now:
                continue
            job.error = f"lease expired for worker {job.lease_owner or 'UNKNOWN'}"
            job.lease_owner = None
            job.lease_expires_at = None
            job.heartbeat_at = None
            job.status = JobStatus.QUEUED if job.attempt < job.maximum_attempts else JobStatus.FAILED
            save_job(job, root)
            recovered.append(job.id)
    recompute_queue_positions(root)
    return recovered


def cancel_job(job_id: str, repo_root: str | Path | None = None) -> Job:
    """Persist cancellation. A process owner may additionally terminate process_id."""
    root = Path(repo_root) if repo_root is not None else find_repo_root()
    with _queue_lock(root):
        job = load_job(job_id, root)
        if job.status in {JobStatus.DONE, JobStatus.FAILED, JobStatus.CANCELLED}:
            return job
        job.status = JobStatus.CANCELLED
        job.error = "cancelled by operator"
        job.lease_owner = None
        job.lease_expires_at = None
        save_job(job, root)
    recompute_queue_positions(root)
    return job
