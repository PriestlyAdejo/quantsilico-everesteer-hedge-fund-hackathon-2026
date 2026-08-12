"""Unit coverage for DashboardProcessManager lifecycle classification and guards."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from qs_everesteer.dashboard.process import (
    DashboardProcessManager,
    DashboardRuntime,
    DashboardState,
    SCHEMA_VERSION,
)


@pytest.fixture()
def mgr(tmp_path: Path) -> DashboardProcessManager:
    # Minimal package layout markers for find helpers if needed.
    (tmp_path / "pyproject.toml").write_text("[project]\nname='t'\n", encoding="utf-8")
    (tmp_path / "runs" / "state").mkdir(parents=True)
    (tmp_path / "dashboard" / "frontend" / "dist").mkdir(parents=True)
    return DashboardProcessManager(tmp_path)


def test_missing_frontend_build_blocks_start(mgr: DashboardProcessManager) -> None:
    # No index.html
    result = mgr.start()
    assert result["ok"] is False
    assert result.get("code") == "FRONTEND_BUILD_MISSING"
    assert "qseh dashboard build" in result["message"]


def test_open_while_stopped_refuses(mgr: DashboardProcessManager) -> None:
    result = mgr.open_browser(start_if_needed=False)
    assert result["ok"] is False
    assert result["opened"] is False
    assert "not running" in result["message"].lower()


def test_stop_idempotent_when_already_stopped(mgr: DashboardProcessManager) -> None:
    result = mgr.stop()
    assert result["ok"] is True
    assert result["state"] == DashboardState.STOPPED.value


def test_stale_pid_classified_as_crashed(mgr: DashboardProcessManager) -> None:
    runtime = DashboardRuntime(
        schema_version=SCHEMA_VERSION,
        pid=999_999_991,
        started_at="2026-01-01T00:00:00+00:00",
        host="127.0.0.1",
        port=8766,
        url="http://127.0.0.1:8766",
        log_path=str(mgr.log_path),
        command=["python", "-m", "uvicorn"],
        repo_sha=None,
        frontend_build_sha=None,
    )
    mgr._save_state(runtime)
    with (
        patch("qs_everesteer.dashboard.process._pid_alive", return_value=False),
        patch("qs_everesteer.dashboard.process._port_listening", return_value=False),
        patch("qs_everesteer.dashboard.process._health_payload", return_value=None),
    ):
        status = mgr.classify()
    assert status["state"] == DashboardState.CRASHED.value


def test_port_conflict_when_listener_not_ours(mgr: DashboardProcessManager) -> None:
    with (
        patch("qs_everesteer.dashboard.process._pid_alive", return_value=False),
        patch("qs_everesteer.dashboard.process._port_listening", return_value=True),
        patch("qs_everesteer.dashboard.process._health_payload", return_value=None),
    ):
        status = mgr.classify()
    assert status["state"] == DashboardState.PORT_CONFLICT.value


def test_port_conflict_refuses_start(mgr: DashboardProcessManager) -> None:
    (mgr.frontend_index).write_text("<html></html>", encoding="utf-8")
    with patch.object(
        mgr,
        "classify",
        return_value={
            "state": DashboardState.PORT_CONFLICT.value,
            "pid": None,
            "process_alive": False,
            "port_listening": True,
            "health": None,
        },
    ):
        result = mgr.start()
    assert result["ok"] is False
    assert "PORT CONFLICT" in result["message"]


def test_stop_does_not_kill_foreign_port(mgr: DashboardProcessManager) -> None:
    with patch("qs_everesteer.dashboard.process._port_listening", return_value=True):
        result = mgr.stop()
    assert result["ok"] is False
    assert result["state"] == DashboardState.PORT_CONFLICT.value


def test_build_command_uses_repo_root_module(mgr: DashboardProcessManager) -> None:
    cmd = mgr.build_command()
    assert "-m" in cmd
    assert "uvicorn" in cmd
    assert "dashboard.backend.app.main:app" in cmd
    assert "--host" in cmd
    assert "127.0.0.1" in cmd
    assert "--port" in cmd
    assert "8766" in cmd


def test_start_child_crash_clears_state(mgr: DashboardProcessManager, tmp_path: Path) -> None:
    mgr.frontend_index.write_text("<html></html>", encoding="utf-8")
    fake = MagicMock()
    fake.pid = 4242
    fake.poll.side_effect = [1]  # exited immediately
    fake.returncode = 1

    with (
        patch("qs_everesteer.dashboard.process.subprocess.Popen", return_value=fake),
        patch("qs_everesteer.dashboard.process._git_sha", return_value="deadbeef"),
        patch("qs_everesteer.dashboard.process._frontend_build_sha", return_value="abc"),
        patch("qs_everesteer.dashboard.process._health_payload", return_value=None),
        patch("qs_everesteer.dashboard.process._pid_alive", return_value=False),
    ):
        result = mgr.start()

    assert result["ok"] is False
    assert result["message"] == "Dashboard failed to start"
    assert result.get("exit_code") == 1
    loaded = mgr._load_state()
    assert loaded is not None
    assert loaded.pid is None
