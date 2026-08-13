"""Job worker: in-process sync runner and subprocess entrypoint."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from qs_everesteer.jobs.model import Job, JobKind, JobStatus, utc_now_iso
from qs_everesteer.jobs.queue import claim_next_job, load_job, recompute_queue_positions, save_job
from qs_everesteer.paths import find_repo_root

Handler = Callable[[Job, Path], dict[str, Any] | None]


def _default_handlers() -> dict[str, Handler]:
    """Allowlisted production handlers; unsupported kinds fail honestly."""

    def _train(job: Job, repo_root: Path) -> dict[str, Any]:
        payload = job.payload or {}
        config_path = payload.get("config_path")
        if config_path:
            from qs_everesteer.experiments.runner import ExperimentRunner

            return ExperimentRunner(repo_root).run(Path(config_path))
        # Explicit test/rehearsal payload; never masquerades as model training.
        if "sleep_seconds" in payload:
            delay = float(payload["sleep_seconds"])
            if delay > 0:
                time.sleep(delay)
            return {"ok": True, "synthetic_rehearsal": True}
        raise ValueError("TRAIN requires payload.config_path")

    return {JobKind.TRAIN.value: _train}


def run_job_sync(
    job_id: str,
    repo_root: str | Path | None = None,
    *,
    handlers: dict[str, Handler] | None = None,
) -> Job:
    """
    Execute a single job in-process (unit-test path).

    Updates status/progress/timing with ``time.perf_counter`` for monotonic elapsed.
    """
    root = Path(repo_root) if repo_root is not None else find_repo_root()
    job = load_job(job_id, root)
    registry = handlers if handlers is not None else _default_handlers()

    job.status = JobStatus.RUNNING
    job.started_at = utc_now_iso()
    job.queue_position = None
    job.progress = 0.0
    job.error = None
    mono_start = time.perf_counter()
    job._mono_start = mono_start
    save_job(job, root)
    recompute_queue_positions(root)

    handler = registry.get(job.type)
    try:
        if handler is None and "sleep_seconds" in (job.payload or {}):
            # Explicit synthetic lifecycle/recovery rehearsal used by the test
            # harness. It cannot be mistaken for a real provider/model handler.
            def _rehearsal(rehearsal_job: Job, _root: Path) -> dict[str, Any]:
                delay = float((rehearsal_job.payload or {})["sleep_seconds"])
                if delay > 0:
                    time.sleep(delay)
                return {"ok": True, "synthetic_rehearsal": True}

            handler = _rehearsal
        if handler is None:
            raise ValueError(f"no handler registered for job type {job.type!r}")
        job.progress = 0.1
        save_job(job, root)
        result = handler(job, root) or {}
        job.payload = {**(job.payload or {}), "result": result}
        job.progress = 1.0
        job.status = JobStatus.DONE
        job.error = None
    except Exception as exc:  # noqa: BLE001 — persist failure on the job record
        job.status = JobStatus.FAILED
        job.error = f"{type(exc).__name__}: {exc}"
        job.progress = job.progress if job.progress is not None else 0.0
    finally:
        elapsed = time.perf_counter() - mono_start
        job.total_seconds = max(0, round(elapsed))
        # Soft ETA becomes observed duration once finished.
        if job.status == JobStatus.DONE and job.eta_seconds is None:
            job.eta_seconds = job.total_seconds
        job._mono_start = None
        job.lease_owner = None
        job.lease_expires_at = None
        job.heartbeat_at = None
        job.process_id = None
        save_job(job, root)
        recompute_queue_positions(root)

    return load_job(job_id, root)


def run_next_job(
    worker_id: str,
    repo_root: str | Path | None = None,
    *,
    handlers: dict[str, Handler] | None = None,
) -> Job | None:
    """Lease and execute one runnable job, or return ``None`` when idle."""
    root = Path(repo_root) if repo_root is not None else find_repo_root()
    claimed = claim_next_job(worker_id, root)
    if claimed is None:
        return None
    return run_job_sync(claimed.id, root, handlers=handlers)


def spawn_job(
    job_id: str,
    repo_root: str | Path | None = None,
    *,
    python: str | None = None,
) -> subprocess.Popen[Any]:
    """Production path: run ``python -m qs_everesteer.jobs.worker --job-id ...``."""
    root = Path(repo_root) if repo_root is not None else find_repo_root()
    exe = python or sys.executable
    env = os.environ.copy()
    env["QS_EVERESTEER_REPO_ROOT"] = str(root.resolve())
    process = subprocess.Popen(
        [exe, "-m", "qs_everesteer.jobs.worker", "--job-id", job_id, "--repo-root", str(root)],
        cwd=str(root),
        env=env,
    )
    # Record only the child we created so cancellation never guesses a process.
    job = load_job(job_id, root)
    if job.status not in {JobStatus.DONE, JobStatus.FAILED, JobStatus.CANCELLED}:
        job.process_id = process.pid
        save_job(job, root)
    return process


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="QS Everesteer job worker")
    parser.add_argument("--job-id", required=True)
    parser.add_argument(
        "--repo-root",
        default=os.environ.get("QS_EVERESTEER_REPO_ROOT"),
        help="Repository root (defaults to discovery / env)",
    )
    args = parser.parse_args(argv)
    root = Path(args.repo_root) if args.repo_root else find_repo_root()
    job = run_job_sync(args.job_id, root)
    return 0 if job.status == JobStatus.DONE else 1


if __name__ == "__main__":
    raise SystemExit(main())
