"""Local research dashboard lifecycle (optional FastAPI dependency)."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

import typer

from qs_everesteer.cli_app.common import console, print_json, print_kv, repo_root

dashboard_app = typer.Typer(help="Local dashboard on 127.0.0.1:8766.", no_args_is_help=True)

HOST = "127.0.0.1"
PORT = 8766
HEALTH_URL = f"http://{HOST}:{PORT}/api/health"
PID_NAME = "dashboard.pid"


def _pid_path(root: Path) -> Path:
    return root / "runs" / "state" / PID_NAME


def _backend_dir(root: Path) -> Path:
    return root / "dashboard" / "backend"


def _script(root: Path, name: str) -> Path:
    return root / "scripts" / "dashboard" / name


def _health() -> dict | None:
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=2) as resp:
            import json

            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError):
        return None


def _read_pid(root: Path) -> int | None:
    path = _pid_path(root)
    if not path.exists():
        return None
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except ValueError:
        return None


@dashboard_app.command("start")
def dashboard_start(
    use_script: bool = typer.Option(
        False,
        "--script",
        help="Prefer scripts/dashboard/start.cmd when present.",
    ),
) -> None:
    """Start FastAPI backend via uvicorn on 127.0.0.1:8766."""
    root = repo_root()
    if _health() is not None:
        console.print(f"[green]dashboard already healthy[/green] {HEALTH_URL}")
        return

    script = _script(root, "start.cmd")
    if use_script and script.exists() and sys.platform.startswith("win"):
        subprocess.Popen(["cmd", "/c", str(script)], cwd=str(root))  # noqa: S603
        console.print(f"[dim]launched[/dim] {script}")
        return

    backend = _backend_dir(root)
    if not (backend / "app" / "main.py").exists():
        console.print(f"[red]dashboard backend missing:[/red] {backend / 'app' / 'main.py'}")
        raise typer.Exit(code=1)

    # Optional dependency — fail clearly if uvicorn/fastapi not installed.
    try:
        import uvicorn  # noqa: F401
    except ImportError as exc:
        console.print(
            "[red]dashboard extras missing[/red] — pip install '.[dashboard]' "
            "(fastapi/uvicorn)"
        )
        raise typer.Exit(code=1) from exc

    log_dir = root / "runs" / "state"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "dashboard.log"
    pid_path = _pid_path(root)

    env = os.environ.copy()
    creationflags = 0
    if sys.platform.startswith("win"):
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

    with log_path.open("ab") as log_fh:
        proc = subprocess.Popen(  # noqa: S603
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                HOST,
                "--port",
                str(PORT),
                "--app-dir",
                str(backend),
            ],
            cwd=str(backend),
            env=env,
            stdout=log_fh,
            stderr=subprocess.STDOUT,
            creationflags=creationflags,
        )
    pid_path.write_text(str(proc.pid), encoding="utf-8")
    # Brief wait for health.
    healthy = None
    for _ in range(20):
        time.sleep(0.25)
        healthy = _health()
        if healthy is not None:
            break
    print_kv(
        [
            ("url", f"http://{HOST}:{PORT}"),
            ("pid", proc.pid),
            ("log", str(log_path)),
            ("healthy", healthy is not None),
        ],
        title="dashboard start",
    )
    if healthy is None:
        console.print("[yellow]started but health not yet ready — try qseh dashboard status[/yellow]")


@dashboard_app.command("status")
def dashboard_status() -> None:
    """Health / PID status for the local dashboard."""
    root = repo_root()
    health = _health()
    print_json(
        {
            "url": f"http://{HOST}:{PORT}",
            "health": health,
            "pid": _read_pid(root),
            "script": str(_script(root, "status.cmd")),
        }
    )
    script = _script(root, "status.cmd")
    if script.exists() and sys.platform.startswith("win"):
        subprocess.run(["cmd", "/c", str(script)], cwd=str(root), check=False)  # noqa: S603


@dashboard_app.command("open")
def dashboard_open() -> None:
    """Open the dashboard URL in the default browser."""
    root = repo_root()
    script = _script(root, "open.cmd")
    if script.exists() and sys.platform.startswith("win"):
        subprocess.run(["cmd", "/c", str(script)], cwd=str(root), check=False)  # noqa: S603
    else:
        webbrowser.open(f"http://{HOST}:{PORT}")
    console.print(f"opened http://{HOST}:{PORT}")


@dashboard_app.command("stop")
def dashboard_stop() -> None:
    """Stop the dashboard process recorded in runs/state/dashboard.pid."""
    root = repo_root()
    pid = _read_pid(root)
    if pid is None:
        console.print("[dim]no dashboard pid file[/dim]")
        script = _script(root, "stop.cmd")
        if script.exists() and sys.platform.startswith("win"):
            subprocess.run(["cmd", "/c", str(script)], cwd=str(root), check=False)  # noqa: S603
        return
    try:
        if sys.platform.startswith("win"):
            subprocess.run(  # noqa: S603
                ["taskkill", "/PID", str(pid), "/F"],
                check=False,
                capture_output=True,
            )
        else:
            os.kill(pid, signal.SIGTERM)
        console.print(f"[yellow]stopped pid[/yellow] {pid}")
    except OSError as exc:
        console.print(f"[yellow]stop failed:[/yellow] {exc}")
    pid_path = _pid_path(root)
    if pid_path.exists():
        pid_path.unlink()
