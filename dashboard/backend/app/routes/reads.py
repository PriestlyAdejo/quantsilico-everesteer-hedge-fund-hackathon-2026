"""Read-only JSON routes for every Figma DataSource page."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from dashboard.backend.app.services.console import ConsoleService, utc_now
from qs_everesteer.api_schemas import ApiModel

router = APIRouter()


class HealthResponse(ApiModel):
    status: str
    service: str
    schema_version: int
    server_observed_at: str
    submission_mode: str


def _service(request: Request) -> ConsoleService:
    return request.app.state.console


def _json(value: Any) -> JSONResponse:
    return JSONResponse(value.model_dump(mode="json", by_alias=True))


@router.get("/api/health")
def health(request: Request) -> JSONResponse:
    state = _service(request).state()
    return _json(
        HealthResponse(
            status="ok",
            service="QuantSilico Everesteer 2026 Research Console",
            schema_version=2,
            server_observed_at=utc_now(),
            submission_mode=str(state.get("submission_mode", "DRY_RUN")),
        )
    )


def _register(path: str, method_name: str) -> None:
    def endpoint(request: Request) -> JSONResponse:
        service = _service(request)
        method: Callable[[], Any] = getattr(service, method_name)
        return _json(method())

    endpoint.__name__ = f"get_{method_name}"
    router.add_api_route(path, endpoint, methods=["GET"])


for _path, _method in (
    ("/api/event-status", "event_status"),
    ("/api/overview", "overview"),
    ("/api/event-control", "event_control"),
    ("/api/round-room", "round_room"),
    ("/api/data-lab", "data_lab"),
    ("/api/experiments", "experiments"),
    ("/api/validation", "validation"),
    ("/api/models", "models"),
    ("/api/feature-lab", "feature_lab"),
    ("/api/ensembles", "ensembles"),
    ("/api/leaderboard", "leaderboard"),
    ("/api/submission", "submission"),
    ("/api/staking", "staking"),
    ("/api/compute", "compute"),
    ("/api/repository", "repository"),
    ("/api/docs", "documentation"),
):
    _register(_path, _method)
