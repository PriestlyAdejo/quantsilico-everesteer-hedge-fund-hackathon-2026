"""Durable worker and legacy job-control CLI surfaces."""

from __future__ import annotations

import socket

import typer

from qs_everesteer.cli_app.common import print_json
from qs_everesteer.jobs.queue import cancel_job, list_jobs, load_job, recover_stale_jobs, save_job
from qs_everesteer.jobs.worker import run_next_job

worker_app = typer.Typer(no_args_is_help=True, help="Run the local durable worker.")
jobs_app = typer.Typer(no_args_is_help=True, help="Inspect and control persisted jobs.")


@worker_app.command("start")
def worker_start_cmd(
    once: bool = typer.Option(True, "--once/--loop", help="Run once or continue until idle."),
) -> None:
    """Recover expired leases, then execute queued jobs in scheduler order."""
    worker_id = f"{socket.gethostname()}-cli"
    recovered = recover_stale_jobs()
    completed: list[str] = []
    while True:
        job = run_next_job(worker_id)
        if job is None:
            break
        completed.append(job.id)
        if once:
            break
    print_json({"worker_id": worker_id, "recovered": recovered, "completed": completed, "status": "IDLE"})


@worker_app.command("status")
def worker_status_cmd() -> None:
    """Show queued/running jobs without starting work."""
    jobs = list_jobs()
    print_json({"queued": sum(j.status.value == "QUEUED" for j in jobs), "running": sum(j.status.value == "RUNNING" for j in jobs)})


@jobs_app.command("list")
def jobs_list_cmd() -> None:
    print_json([job.to_dict() for job in list_jobs()])


@jobs_app.command("cancel")
def jobs_cancel_cmd(job_id: str) -> None:
    print_json(cancel_job(job_id).to_dict())


@jobs_app.command("retry")
def jobs_retry_cmd(job_id: str) -> None:
    job = load_job(job_id)
    if job.status.value not in {"FAILED", "CANCELLED", "BLOCKED"}:
        raise typer.BadParameter("only failed, cancelled, or blocked jobs can be retried")
    if job.attempt >= job.maximum_attempts:
        raise typer.BadParameter("maximum attempts exhausted")
    job.status = type(job.status).QUEUED
    job.error = None
    job.lease_owner = None
    job.lease_expires_at = None
    save_job(job)
    print_json(job.to_dict())
