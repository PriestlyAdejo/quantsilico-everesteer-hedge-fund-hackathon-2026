"""QuantSilico Everesteer Research Console API.

The process launcher owns networking; the intended development bind is
``127.0.0.1:8766``. This module only constructs the ASGI application.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from dashboard.backend.app.routes import actions, events, reads
from dashboard.backend.app.services.console import ConsoleService
from qs_everesteer.paths import find_repo_root


def create_app(repo_root: str | Path | None = None) -> FastAPI:
    root = Path(repo_root).resolve() if repo_root is not None else find_repo_root()
    application = FastAPI(
        title="QuantSilico × Everesteer 2026 Research Console",
        version="2",
        docs_url="/api/dev/docs",
        openapi_url="/api/openapi.json",
        redoc_url=None,
    )
    application.state.repo_root = root
    application.state.console = ConsoleService(root)

    # API routes must precede the SPA fallback.
    application.include_router(reads.router)
    application.include_router(actions.router)
    application.include_router(events.router)

    dist = root / "dashboard" / "frontend" / "dist"
    assets = dist / "assets"
    if assets.is_dir():
        application.mount("/assets", StaticFiles(directory=assets), name="assets")

    @application.get("/{spa_path:path}", include_in_schema=False)
    async def spa_fallback(spa_path: str) -> FileResponse:
        if spa_path == "api" or spa_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API route not found")
        if not dist.is_dir():
            raise HTTPException(status_code=404, detail="Frontend build not found")

        requested = (dist / spa_path).resolve()
        try:
            requested.relative_to(dist.resolve())
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="Asset not found") from exc

        if spa_path and requested.is_file():
            return FileResponse(requested)
        if Path(spa_path).suffix:
            raise HTTPException(status_code=404, detail="Asset not found")

        index = dist / "index.html"
        if index.is_file():
            return FileResponse(index)
        raise HTTPException(status_code=404, detail="Frontend index not found")

    return application


app = create_app()
