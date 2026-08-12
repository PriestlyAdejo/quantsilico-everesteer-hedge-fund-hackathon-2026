"""Filesystem-backed job queue under ``runs/jobs/``."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from filelock import FileLock

from qs_everesteer.fsutil import atomic_write_json, read_json
from qs_everesteer.jobs.model import Job, JobKind, JobStatus
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
        except Exception:  # noqa: BLE001
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
    return int(round(sum(durations) / len(durations)))


def enqueue(
    kind: str | JobKind,
    payload: dict[str, Any] | None = None,
    *,
    repo_root: str | Path | None = None,
    name: str | None = None,
    candidate: str | None = None,
    device: str = "CPU",
    job_id: str | None = None,
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
        )
        save_job(job, root)
        return job.id


def recompute_queue_positions(repo_root: str | Path | None = None) -> None:
    root = Path(repo_root) if repo_root is not None else find_repo_root()
    with _queue_lock(root):
        queued = sorted(
            list_jobs(root, status=JobStatus.QUEUED),
            key=lambda j: j.id,
        )
        for idx, job in enumerate(queued, start=1):
            job.queue_position = idx
            save_job(job, root)
