from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from dashboard.backend.app.main import create_app


def test_core_reads_and_docs_do_not_collide(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))

    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["schemaVersion"] == 2

    for path in ("/api/overview", "/api/event-control", "/api/submission", "/api/docs"):
        response = client.get(path)
        assert response.status_code == 200, response.text
        assert response.json()["schemaVersion"] == 2

    assert client.get("/api/submission").json()["data"]["submissionMode"] == "DRY_RUN"
    assert client.get("/api/event-control").json()["data"]["serverObservedAt"]
    assert client.get("/docs").status_code == 404
    assert client.get("/api/dev/docs").status_code == 200
    assert client.get("/api/docs").headers["content-type"].startswith("application/json")


def test_every_figma_read_route_returns_camel_case_envelope(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))
    paths = (
        "event-status",
        "overview",
        "event-control",
        "round-room",
        "data-lab",
        "experiments",
        "validation",
        "models",
        "feature-lab",
        "ensembles",
        "leaderboard",
        "submission",
        "staking",
        "compute",
        "repository",
        "docs",
    )
    for name in paths:
        response = client.get(f"/api/{name}")
        assert response.status_code == 200, f"{name}: {response.text}"
        body = response.json()
        assert body["schemaVersion"] == 2
        assert "generatedAt" in body
        assert "schema_version" not in body


def test_spa_history_fallback_never_catches_api(tmp_path: Path) -> None:
    dist = tmp_path / "dashboard" / "frontend" / "dist"
    dist.mkdir(parents=True)
    (dist / "index.html").write_text("<main>console</main>", encoding="utf-8")
    client = TestClient(create_app(tmp_path))

    assert client.get("/research/models").text == "<main>console</main>"
    assert client.get("/api/not-a-route").status_code == 404
    assert client.get("/missing.js").status_code == 404
