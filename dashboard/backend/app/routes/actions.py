"""Mutation routes enqueue filesystem jobs; request handlers never run work."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from dashboard.backend.app.routes.events import hub
from qs_everesteer.api_schemas import ActionResult
from qs_everesteer.jobs.model import JobStatus
from qs_everesteer.jobs.queue import enqueue, load_job, save_job
from qs_everesteer.state.research import update_research_state

router = APIRouter(prefix="/api/actions")


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _root(request: Request):
    return request.app.state.repo_root


def _result(message: str, code: str) -> JSONResponse:
    value = ActionResult(ok=True, message=message, code=code, timestamp=_now())
    return JSONResponse(value.model_dump(mode="json", by_alias=True))


async def _enqueue(
    request: Request,
    kind: str,
    *,
    name: str,
    payload: dict[str, Any] | None = None,
    candidate: str | None = None,
) -> JSONResponse:
    job_id = enqueue(
        kind,
        payload or {},
        repo_root=_root(request),
        name=name,
        candidate=candidate,
    )
    await hub.publish("job_queued", jobId=job_id, jobType=kind)
    return _result(f"Queued {name} as {job_id}", f"JOB_QUEUED:{job_id}")


@router.post("/refresh-event")
async def refresh_event(request: Request) -> JSONResponse:
    return await _enqueue(request, "EVENT_REFRESH", name="refresh event")


@router.post("/snapshot-event")
async def snapshot_event(request: Request) -> JSONResponse:
    return await _enqueue(request, "EVENT_SNAPSHOT", name="snapshot event")


@router.post("/pull-datasets")
async def pull_datasets(request: Request) -> JSONResponse:
    return await _enqueue(request, "DATA_PULL", name="pull datasets")


@router.post("/scorer-parity")
async def scorer_parity(request: Request) -> JSONResponse:
    return await _enqueue(request, "SCORER_PARITY", name="official scorer parity")


@router.post("/official-baseline")
async def official_baseline(request: Request) -> JSONResponse:
    return await _enqueue(request, "TRAIN", name="official baseline")


@router.post("/autopilot/start")
async def start_autopilot(request: Request) -> JSONResponse:
    root = _root(request)
    update_research_state(lambda state: state.update(autopilot_active=True), root)
    response = await _enqueue(
        request,
        "AUTOPILOT",
        name="autopilot",
        payload={"max_steps": None},
    )
    await hub.publish("autopilot_started")
    return response


@router.post("/autopilot/stop")
async def stop_autopilot(request: Request) -> JSONResponse:
    update_research_state(
        lambda state: state.update(autopilot_active=False),
        _root(request),
    )
    await hub.publish("autopilot_stopped")
    return _result("Autopilot stop requested", "AUTOPILOT_STOPPED")


@router.post("/race/start")
async def start_race(
    request: Request,
    profile: str = Query(default="standard", min_length=1, max_length=80),
) -> JSONResponse:
    return await _enqueue(
        request,
        "TRAIN",
        name=f"research race ({profile})",
        payload={"profile": profile},
    )


@router.post("/build-ensemble")
async def build_ensemble(
    request: Request,
    strategy: str = Query(default="rank_average", min_length=1, max_length=80),
) -> JSONResponse:
    return await _enqueue(
        request,
        "ENSEMBLE",
        name=f"build ensemble ({strategy})",
        payload={"strategy": strategy},
    )


@router.post("/save-ensemble")
async def save_ensemble(
    request: Request,
    strategy: str = Query(default="rank_average", min_length=1, max_length=80),
) -> JSONResponse:
    return await _enqueue(
        request,
        "ENSEMBLE",
        name=f"save ensemble ({strategy})",
        payload={"strategy": strategy, "save_candidate": True},
    )


@router.post("/promote-ensemble")
async def promote_ensemble(request: Request) -> JSONResponse:
    return await _enqueue(request, "ENSEMBLE", name="promote ensemble")


@router.post("/validate/{candidate_id}")
async def validate_submission(request: Request, candidate_id: str) -> JSONResponse:
    return await _enqueue(
        request,
        "VALIDATE",
        name=f"validate {candidate_id}",
        candidate=candidate_id,
    )


@router.post("/submit-practice/{candidate_id}")
async def submit_practice(request: Request, candidate_id: str) -> JSONResponse:
    return await _enqueue(
        request,
        "SUBMIT",
        name=f"practice submission {candidate_id}",
        payload={"lane": "practice"},
        candidate=candidate_id,
    )


@router.post("/submit-live/{candidate_id}")
async def submit_live(request: Request, candidate_id: str) -> JSONResponse:
    mode = request.app.state.console.state().get("submission_mode", "DRY_RUN")
    return await _enqueue(
        request,
        "SUBMIT",
        name=f"live submission {candidate_id} ({mode})",
        payload={"lane": "live", "submission_mode": mode},
        candidate=candidate_id,
    )


@router.post("/jobs/{job_id}/stop")
async def stop_job(request: Request, job_id: str) -> JSONResponse:
    try:
        job = load_job(job_id, _root(request))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc
    if job.status not in {JobStatus.DONE, JobStatus.FAILED}:
        job.status = JobStatus.FAILED
        job.error = "Stopped by console operator"
        job.queue_position = None
        save_job(job, _root(request))
    await hub.publish("job_stopped", jobId=job_id)
    return _result(f"Stopped {job_id}", "JOB_STOPPED")
