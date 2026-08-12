"""Job worker: in-process sync runner and subprocess entrypoint."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable

from qs_everesteer.jobs.model import Job, JobKind, JobStatus, utc_now_iso
from qs_everesteer.jobs.queue import load_job, recompute_queue_positions, save_job
from qs_everesteer.paths import find_repo_root

Handler = Callable[[Job, Path], dict[str, Any] | None]


def _default_handlers() -> dict[str, Handler]:
    """Allowlisted handlers. Production will swap these for real pipelines."""

    def _noop(job: Job, repo_root: Path) -> dict[str, Any]:
        # Tiny sleep so monotonic elapsed is measurable in tests when requested.
        delay = float((job.payload or {}).get("sleep_seconds", 0.0))
        if delay > 0:
            time.sleep(delay)
        return {"ok": True, "kind": job.type, "repo_root": str(repo_root)}

    return {kind.value: _noop for kind in JobKind}


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
        job.total_seconds = max(0, int(round(elapsed)))
        # Soft ETA becomes observed duration once finished.
        if job.status == JobStatus.DONE and job.eta_seconds is None:
            job.eta_seconds = job.total_seconds
        job._mono_start = None
        save_job(job, root)
        recompute_queue_positions(root)

    return load_job(job_id, root)


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
    return subprocess.Popen(
        [exe, "-m", "qs_everesteer.jobs.worker", "--job-id", job_id, "--repo-root", str(root)],
        cwd=str(root),
        env=env,
    )


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
