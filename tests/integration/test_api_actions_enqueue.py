from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from dashboard.backend.app.main import create_app
from qs_everesteer.jobs.queue import list_jobs


def test_race_start_enqueues_without_running_training(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))

    response = client.post("/api/actions/race/start?profile=fast")

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["code"].startswith("JOB_QUEUED:")
    jobs = list_jobs(tmp_path)
    assert len(jobs) == 1
    assert jobs[0].status.value == "QUEUED"
    assert jobs[0].payload == {"profile": "fast"}
    assert jobs[0].started_at is None
