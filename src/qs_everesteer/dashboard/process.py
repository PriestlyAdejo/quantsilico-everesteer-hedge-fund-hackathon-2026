"""Authoritative local Research Console process lifecycle."""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any

from qs_everesteer.fsutil import atomic_write_json, read_json
from qs_everesteer.paths import ensure_dir, find_repo_root, state_dir

HOST = "127.0.0.1"
PORT = 8766
HEALTH_PATH = "/api/health"
APP_MODULE = "dashboard.backend.app.main:app"
STATE_NAME = "dashboard.json"
LOG_NAME = "dashboard.log"
LEGACY_PID_NAME = "dashboard.pid"
SCHEMA_VERSION = 1
STARTUP_TIMEOUT_S = 12.0
POLL_INTERVAL_S = 0.25


class DashboardState(StrEnum):
    RUNNING = "RUNNING"
    STARTING = "STARTING"
    STOPPED = "STOPPED"
    CRASHED = "CRASHED"
    STALE_STATE = "STALE_STATE"
    PORT_CONFLICT = "PORT_CONFLICT"
    UNHEALTHY = "UNHEALTHY"


@dataclass
class DashboardRuntime:
    schema_version: int
    pid: int | None
    started_at: str | None
    host: str
    port: int
    url: str
    log_path: str
    command: list[str]
    repo_sha: str | None
    frontend_build_sha: str | None
    last_exit_code: int | None = None
    last_error: str | None = None


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _python_executable(root: Path) -> Path:
    venv_py = root / ".venv" / "Scripts" / "python.exe"
    if venv_py.is_file():
        return venv_py
    venv_py_unix = root / ".venv" / "bin" / "python"
    if venv_py_unix.is_file():
        return venv_py_unix
    return Path(sys.executable)


def _pnpm_executable() -> str:
    """Resolve pnpm for subprocess (Windows needs pnpm.cmd, not the .ps1 shim)."""
    import shutil

    if sys.platform.startswith("win"):
        for name in ("pnpm.cmd", "pnpm.exe"):
            found = shutil.which(name)
            if found:
                return found
    found = shutil.which("pnpm")
    if found:
        return found
    return "pnpm"


def _git_sha(root: Path) -> str | None:
    try:
        out = subprocess.check_output(  # noqa: S603
            ["git", "rev-parse", "HEAD"],
            cwd=str(root),
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip() or None
    except (OSError, subprocess.CalledProcessError):
        return None


def _frontend_build_sha(root: Path) -> str | None:
    index = root / "dashboard" / "frontend" / "dist" / "index.html"
    if not index.is_file():
        return None
    import hashlib

    return hashlib.sha256(index.read_bytes()).hexdigest()[:16]


def _port_listening(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _health_payload(host: str = HOST, port: int = PORT, timeout: float = 2.0) -> dict[str, Any] | None:
    url = f"http://{host}:{port}{HEALTH_PATH}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310
            data = json.loads(resp.read().decode("utf-8"))
            if not isinstance(data, dict):
                return None
            if data.get("status") != "ok":
                return None
            return data
    except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
        return None


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform.startswith("win"):
        try:
            out = subprocess.check_output(  # noqa: S603
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            return str(pid) in out and "No tasks" not in out
        except (OSError, subprocess.CalledProcessError):
            return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _creationflags() -> int:
    if not sys.platform.startswith("win"):
        return 0
    # Minimal flag set: keep child alive after CLI exit; preserve redirected logs.
    return int(getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))


def _tail_file(path: Path, n: int = 50) -> list[str]:
    if not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    return lines[-n:]


class DashboardProcessManager:
    """Single authority for Research Console start/status/stop/open/diagnose."""

    def __init__(self, repo_root: str | Path | None = None) -> None:
        self.root = Path(repo_root).resolve() if repo_root is not None else find_repo_root()
        self.state_path = state_dir(self.root) / STATE_NAME
        self.log_path = state_dir(self.root) / LOG_NAME
        self.legacy_pid_path = state_dir(self.root) / LEGACY_PID_NAME
        self.host = HOST
        self.port = PORT

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def health_url(self) -> str:
        return f"{self.url}{HEALTH_PATH}"

    @property
    def frontend_dist(self) -> Path:
        return self.root / "dashboard" / "frontend" / "dist"

    @property
    def frontend_index(self) -> Path:
        return self.frontend_dist / "index.html"

    def _load_state(self) -> DashboardRuntime | None:
        if not self.state_path.exists():
            if self.legacy_pid_path.exists():
                try:
                    pid = int(self.legacy_pid_path.read_text(encoding="utf-8").strip())
                except ValueError:
                    return None
                return DashboardRuntime(
                    schema_version=SCHEMA_VERSION,
                    pid=pid,
                    started_at=None,
                    host=self.host,
                    port=self.port,
                    url=self.url,
                    log_path=str(self.log_path),
                    command=[],
                    repo_sha=None,
                    frontend_build_sha=None,
                )
            return None
        raw = read_json(self.state_path)
        if not isinstance(raw, dict):
            return None
        try:
            return DashboardRuntime(
                schema_version=int(raw.get("schema_version", SCHEMA_VERSION)),
                pid=raw.get("pid"),
                started_at=raw.get("started_at"),
                host=str(raw.get("host", self.host)),
                port=int(raw.get("port", self.port)),
                url=str(raw.get("url", self.url)),
                log_path=str(raw.get("log_path", self.log_path)),
                command=list(raw.get("command") or []),
                repo_sha=raw.get("repo_sha"),
                frontend_build_sha=raw.get("frontend_build_sha"),
                last_exit_code=raw.get("last_exit_code"),
                last_error=raw.get("last_error"),
            )
        except (TypeError, ValueError):
            return None

    def _save_state(self, runtime: DashboardRuntime) -> None:
        ensure_dir(self.state_path.parent)
        atomic_write_json(self.state_path, asdict(runtime))
        if runtime.pid is not None:
            self.legacy_pid_path.write_text(str(runtime.pid), encoding="utf-8")
        elif self.legacy_pid_path.exists():
            self.legacy_pid_path.unlink()

    def _clear_state(self, *, last_exit_code: int | None = None, last_error: str | None = None) -> None:
        ensure_dir(self.state_path.parent)
        cleared = DashboardRuntime(
            schema_version=SCHEMA_VERSION,
            pid=None,
            started_at=None,
            host=self.host,
            port=self.port,
            url=self.url,
            log_path=str(self.log_path),
            command=[],
            repo_sha=_git_sha(self.root),
            frontend_build_sha=_frontend_build_sha(self.root),
            last_exit_code=last_exit_code,
            last_error=last_error,
        )
        atomic_write_json(self.state_path, asdict(cleared))
        if self.legacy_pid_path.exists():
            self.legacy_pid_path.unlink()

    def build_command(self) -> list[str]:
        py = str(_python_executable(self.root))
        return [
            py,
            "-m",
            "uvicorn",
            APP_MODULE,
            "--host",
            self.host,
            "--port",
            str(self.port),
        ]

    def classify(self) -> dict[str, Any]:
        runtime = self._load_state()
        health = _health_payload(self.host, self.port)
        listening = _port_listening(self.host, self.port)
        pid = runtime.pid if runtime else None
        alive = _pid_alive(pid) if pid is not None else False

        if health is not None and alive:
            state = DashboardState.RUNNING
        elif health is not None and not alive:
            state = DashboardState.STALE_STATE
        elif pid is not None and alive and listening and health is None:
            state = DashboardState.UNHEALTHY
        elif pid is not None and alive and not listening:
            state = DashboardState.STARTING
        elif pid is not None and not alive:
            state = DashboardState.CRASHED
        elif listening and (pid is None or not alive):
            state = DashboardState.PORT_CONFLICT
        else:
            state = DashboardState.STOPPED

        return {
            "state": state.value,
            "pid": pid,
            "process_alive": alive,
            "port_listening": listening,
            "health": health,
            "url": self.url,
            "log_path": str(self.log_path),
            "state_path": str(self.state_path),
            "last_exit_code": runtime.last_exit_code if runtime else None,
            "last_error": runtime.last_error if runtime else None,
            "command": runtime.command if runtime else [],
            "frontend_dist": str(self.frontend_index),
            "frontend_present": self.frontend_index.is_file(),
        }

    def start(self) -> dict[str, Any]:
        current = self.classify()
        if current["state"] == DashboardState.RUNNING.value:
            return {**current, "ok": True, "message": "Dashboard already running"}

        if current["state"] == DashboardState.PORT_CONFLICT.value:
            return {
                **current,
                "ok": False,
                "message": (
                    f"PORT CONFLICT on {self.host}:{self.port} — "
                    "listener is not owned by qseh; refusing to start"
                ),
            }

        if not self.frontend_index.is_file():
            return {
                **current,
                "ok": False,
                "message": "FRONTEND BUILD MISSING\nRun: qseh dashboard build",
                "code": "FRONTEND_BUILD_MISSING",
            }

        if current["state"] in {
            DashboardState.CRASHED.value,
            DashboardState.STALE_STATE.value,
            DashboardState.STOPPED.value,
            DashboardState.UNHEALTHY.value,
        }:
            self._clear_state()

        try:
            import uvicorn  # noqa: F401
        except ImportError as exc:
            return {
                "ok": False,
                "message": "dashboard extras missing — pip install '.[dashboard]'",
                "error": str(exc),
            }

        cmd = self.build_command()
        ensure_dir(self.log_path.parent)
        self.log_path.write_text("", encoding="utf-8")

        with self.log_path.open("ab") as log_fh:
            proc = subprocess.Popen(  # noqa: S603
                cmd,
                cwd=str(self.root),
                env=os.environ.copy(),
                stdout=log_fh,
                stderr=subprocess.STDOUT,
                creationflags=_creationflags(),
            )

        runtime = DashboardRuntime(
            schema_version=SCHEMA_VERSION,
            pid=proc.pid,
            started_at=_utc_now(),
            host=self.host,
            port=self.port,
            url=self.url,
            log_path=str(self.log_path),
            command=cmd,
            repo_sha=_git_sha(self.root),
            frontend_build_sha=_frontend_build_sha(self.root),
        )
        self._save_state(runtime)

        deadline = time.monotonic() + STARTUP_TIMEOUT_S
        health: dict[str, Any] | None = None
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                exit_code = proc.returncode
                self._clear_state(
                    last_exit_code=exit_code,
                    last_error="child exited during startup",
                )
                return {
                    "ok": False,
                    "message": "Dashboard failed to start",
                    "exit_code": exit_code,
                    "log_path": str(self.log_path),
                    "log_tail": _tail_file(self.log_path, 50),
                    "port_listening": _port_listening(self.host, self.port),
                    "suggested": "qseh dashboard diagnose",
                }
            health = _health_payload(self.host, self.port)
            if health is not None and _pid_alive(proc.pid):
                break
            time.sleep(POLL_INTERVAL_S)

        if health is None or not _pid_alive(proc.pid):
            if proc.poll() is None:
                self._terminate_pid(proc.pid, force=True)
            exit_code = proc.poll()
            self._clear_state(
                last_exit_code=exit_code,
                last_error="health timeout",
            )
            return {
                "ok": False,
                "message": "Dashboard failed to start",
                "exit_code": exit_code,
                "log_path": str(self.log_path),
                "log_tail": _tail_file(self.log_path, 50),
                "port_listening": _port_listening(self.host, self.port),
                "suggested": "qseh dashboard diagnose",
            }

        return {
            "ok": True,
            "message": "Dashboard running",
            "url": self.url,
            "pid": proc.pid,
            "health": health,
            "frontend_present": True,
            "log_path": str(self.log_path),
            "repo_sha": runtime.repo_sha,
            "frontend_build_sha": runtime.frontend_build_sha,
            "state": DashboardState.RUNNING.value,
        }

    def stop(self) -> dict[str, Any]:
        runtime = self._load_state()
        pid = runtime.pid if runtime else None
        if pid is None:
            if _port_listening(self.host, self.port):
                return {
                    "ok": False,
                    "state": DashboardState.PORT_CONFLICT.value,
                    "message": (
                        f"PORT CONFLICT — {self.host}:{self.port} is listening "
                        "but not owned by qseh; not terminating foreign process"
                    ),
                }
            return {
                "ok": True,
                "state": DashboardState.STOPPED.value,
                "message": "Dashboard already stopped.",
            }

        if not _pid_alive(pid):
            self._clear_state(last_error="stale pid cleared on stop")
            return {
                "ok": True,
                "state": DashboardState.STOPPED.value,
                "message": "Dashboard already stopped.",
                "cleared_stale_pid": pid,
            }

        self._terminate_pid(pid, force=False)
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline and _pid_alive(pid):
            time.sleep(0.2)
        if _pid_alive(pid):
            self._terminate_pid(pid, force=True)
            time.sleep(0.3)

        still_alive = _pid_alive(pid)
        listening = _port_listening(self.host, self.port)
        self._clear_state(last_exit_code=0 if not still_alive else 1)

        if still_alive:
            return {
                "ok": False,
                "state": DashboardState.UNHEALTHY.value,
                "pid": pid,
                "process_alive": True,
                "port_listening": listening,
                "message": f"Failed to stop pid {pid}",
            }

        if listening:
            return {
                "ok": False,
                "state": DashboardState.PORT_CONFLICT.value,
                "message": (
                    f"Process {pid} stopped but {self.host}:{self.port} still listening "
                    "(foreign owner); not killing foreign process"
                ),
            }

        return {
            "ok": True,
            "state": DashboardState.STOPPED.value,
            "message": f"stopped pid {pid}",
            "pid": pid,
            "port_listening": False,
        }

    def open_browser(self, *, start_if_needed: bool = False) -> dict[str, Any]:
        status = self.classify()
        if status["state"] != DashboardState.RUNNING.value:
            if start_if_needed:
                started = self.start()
                if not started.get("ok"):
                    return {
                        "ok": False,
                        "opened": False,
                        "message": started.get("message", "Dashboard is not running."),
                        "detail": started,
                    }
            else:
                return {
                    "ok": False,
                    "opened": False,
                    "message": "Dashboard is not running.\nRun `qseh dashboard start`.",
                    "state": status["state"],
                }
        webbrowser.open(self.url)
        return {"ok": True, "opened": True, "url": self.url, "message": f"opened {self.url}"}

    def diagnose(self) -> dict[str, Any]:
        py = _python_executable(self.root)
        fastapi_ok = False
        uvicorn_ok = False
        app_import_ok = False
        app_import_error = None
        try:
            import fastapi  # noqa: F401

            fastapi_ok = True
        except ImportError as exc:
            app_import_error = str(exc)
        try:
            import uvicorn  # noqa: F401

            uvicorn_ok = True
        except ImportError as exc:
            app_import_error = str(exc)

        # Import the app the same way uvicorn does: subprocess from repo root.
        try:
            probe = subprocess.run(  # noqa: S603
                [
                    str(py),
                    "-c",
                    "import dashboard.backend.app.main as m; assert m.app is not None",
                ],
                cwd=str(self.root),
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if probe.returncode == 0:
                app_import_ok = True
                app_import_error = None
            else:
                err = (probe.stderr or probe.stdout or "").strip()
                app_import_error = err[-2000:] if err else f"exit {probe.returncode}"
        except (OSError, subprocess.TimeoutExpired) as exc:
            app_import_error = f"{type(exc).__name__}: {exc}"

        status = self.classify()
        return {
            "repo_root": str(self.root),
            "python_executable": str(py),
            "python_version": sys.version.split()[0],
            "fastapi_import": fastapi_ok,
            "uvicorn_import": uvicorn_ok,
            "app_import": app_import_ok,
            "app_import_error": app_import_error,
            "frontend_dir": str(self.root / "dashboard" / "frontend"),
            "frontend_dist_exists": self.frontend_index.is_file(),
            "frontend_build_sha": _frontend_build_sha(self.root),
            "host": self.host,
            "port": self.port,
            "port_available": not _port_listening(self.host, self.port)
            or status["state"] == DashboardState.RUNNING.value,
            "runtime_state_file": str(self.state_path),
            "stored_pid": status["pid"],
            "pid_alive": status["process_alive"],
            "health_url": self.health_url,
            "health_response": status["health"],
            "state": status["state"],
            "log_path": str(self.log_path),
            "log_tail": _tail_file(self.log_path, 50),
            "launch_command": self.build_command(),
        }

    def build_frontend(self, *, clean: bool = False) -> dict[str, Any]:
        frontend = self.root / "dashboard" / "frontend"
        if not (frontend / "package.json").is_file():
            return {"ok": False, "message": f"frontend missing: {frontend}"}

        node_modules = frontend / "node_modules"
        need_install = clean or not node_modules.is_dir()
        steps: list[str] = []
        pnpm = _pnpm_executable()

        def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
            return subprocess.run(  # noqa: S603
                args,
                cwd=str(frontend),
                check=False,
                capture_output=True,
                text=True,
            )

        if need_install:
            steps.append(f"{pnpm} install --frozen-lockfile")
            install = _run([pnpm, "install", "--frozen-lockfile"])
            if install.returncode != 0:
                return {
                    "ok": False,
                    "message": "pnpm install failed",
                    "steps": steps,
                    "stdout": (install.stdout or "")[-4000:],
                    "stderr": (install.stderr or "")[-4000:],
                    "exit_code": install.returncode,
                }

        steps.append(f"{pnpm} run build")
        build = _run([pnpm, "run", "build"])
        if build.returncode != 0:
            return {
                "ok": False,
                "message": "pnpm run build failed",
                "steps": steps,
                "stdout": (build.stdout or "")[-4000:],
                "stderr": (build.stderr or "")[-4000:],
                "exit_code": build.returncode,
            }

        return {
            "ok": True,
            "message": "frontend build complete",
            "steps": steps,
            "dist": str(self.frontend_index),
            "frontend_build_sha": _frontend_build_sha(self.root),
        }

    def _terminate_pid(self, pid: int, *, force: bool) -> None:
        if sys.platform.startswith("win"):
            args = ["taskkill", "/PID", str(pid)]
            if force:
                args.extend(["/T", "/F"])
            else:
                args.append("/T")
            subprocess.run(args, check=False, capture_output=True)  # noqa: S603
            return
        try:
            os.kill(pid, signal.SIGKILL if force else signal.SIGTERM)
        except OSError:
            pass
