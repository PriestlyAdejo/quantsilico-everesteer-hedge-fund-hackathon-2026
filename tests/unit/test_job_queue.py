from __future__ import annotations

from pathlib import Path

from qs_everesteer.jobs.model import JobKind, JobStatus
from qs_everesteer.jobs.queue import enqueue, estimate_eta, list_jobs, load_job, save_job
from qs_everesteer.jobs.worker import run_job_sync


def test_enqueue_persists_queued_job(tmp_path: Path):
    job_id = enqueue(
        JobKind.TRAIN,
        {"model": "ridge"},
        repo_root=tmp_path,
        name="ridge-smoke",
        candidate="ridge-01",
        device="CPU",
    )
    job = load_job(job_id, tmp_path)
    assert job.id == job_id
    assert job.type == "TRAIN"
    assert job.status == JobStatus.QUEUED
    assert job.name == "ridge-smoke"
    assert job.candidate == "ridge-01"
    assert job.queue_position == 1
    assert job.eta_seconds is not None
    assert (tmp_path / "runs" / "jobs" / f"{job_id}.json").is_file()


def test_run_job_sync_completes_with_monotonic_timing(tmp_path: Path):
    job_id = enqueue(
        JobKind.INFER,
        {"sleep_seconds": 0.05},
        repo_root=tmp_path,
        name="infer-demo",
    )
    done = run_job_sync(job_id, tmp_path)
    assert done.status == JobStatus.DONE
    assert done.started_at is not None
    assert done.progress == 1.0
    assert done.total_seconds is not None
    assert done.total_seconds >= 0
    assert done.queue_position is None
    assert done.payload.get("result", {}).get("ok") is True


def test_soft_eta_uses_prior_same_family_jobs(tmp_path: Path):
    first = enqueue(JobKind.VALIDATE, {}, repo_root=tmp_path, name="v1")
    j = load_job(first, tmp_path)
    j.status = JobStatus.DONE
    j.total_seconds = 120
    save_job(j, tmp_path)

    eta = estimate_eta(JobKind.VALIDATE, tmp_path)
    assert eta == 120

    second = enqueue(JobKind.VALIDATE, {}, repo_root=tmp_path, name="v2")
    queued = load_job(second, tmp_path)
    assert queued.eta_seconds == 120


def test_failed_handler_marks_job_failed(tmp_path: Path):
    job_id = enqueue(JobKind.TRAIN, {}, repo_root=tmp_path, name="boom")

    def boom(job, repo_root):  # noqa: ANN001
        raise RuntimeError("synthetic failure")

    failed = run_job_sync(job_id, tmp_path, handlers={"TRAIN": boom})
    assert failed.status == JobStatus.FAILED
    assert "RuntimeError" in (failed.error or "")
    assert failed.total_seconds is not None


def test_list_jobs_filters(tmp_path: Path):
    enqueue(JobKind.TRAIN, {}, repo_root=tmp_path, name="t")
    enqueue(JobKind.INFER, {}, repo_root=tmp_path, name="i")
    assert len(list_jobs(tmp_path)) == 2
    assert len(list_jobs(tmp_path, kind=JobKind.TRAIN)) == 1
    assert len(list_jobs(tmp_path, status=JobStatus.QUEUED)) == 2
