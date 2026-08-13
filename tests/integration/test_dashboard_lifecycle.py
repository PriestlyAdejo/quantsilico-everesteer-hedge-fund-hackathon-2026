"""Real start→health→stop integration for the Research Console (Windows-friendly)."""

from __future__ import annotations

import json
import urllib.request

import pytest

from qs_everesteer.dashboard.process import DashboardProcessManager, DashboardState
from qs_everesteer.paths import find_repo_root


@pytest.mark.integration
def test_dashboard_start_health_stop_roundtrip() -> None:
    root = find_repo_root()
    mgr = DashboardProcessManager(root)
    if not mgr.frontend_index.is_file():
        pytest.skip("frontend dist missing — run qseh dashboard build")

    # Ensure clean slate.
    mgr.stop()

    started = mgr.start()
    assert started.get("ok") is True, started
    assert started.get("pid")
    assert started.get("health", {}).get("status") == "ok"

    status = mgr.classify()
    assert status["state"] == DashboardState.RUNNING.value
    assert status["pid"] == started["pid"]
    assert status["process_alive"] is True
    assert status["port_listening"] is True

    with urllib.request.urlopen(mgr.health_url, timeout=3) as resp:  # noqa: S310
        payload = json.loads(resp.read().decode("utf-8"))
    assert payload["status"] == "ok"
    assert payload.get("schemaVersion") == 2

    for path in (
        "/api/overview",
        "/api/event-control",
        "/api/compute",
        "/api/repository",
        "/api/docs",
    ):
        with urllib.request.urlopen(f"{mgr.url}{path}", timeout=20) as resp:  # noqa: S310
            body = json.loads(resp.read().decode("utf-8"))
        assert body.get("schemaVersion") == 2
        assert "data" in body

    stopped = mgr.stop()
    assert stopped.get("ok") is True, stopped
    assert stopped.get("port_listening") is False

    after = mgr.classify()
    assert after["state"] == DashboardState.STOPPED.value
    assert after["port_listening"] is False
