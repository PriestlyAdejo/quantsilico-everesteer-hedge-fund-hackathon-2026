"""Local research dashboard lifecycle — thin Typer surface over DashboardProcessManager."""

from __future__ import annotations

import typer

from qs_everesteer.cli_app.common import console, print_json, print_kv
from qs_everesteer.dashboard.process import DashboardProcessManager

dashboard_app = typer.Typer(help="Local dashboard on 127.0.0.1:8766.", no_args_is_help=True)


@dashboard_app.command("start")
def dashboard_start() -> None:
    """Start FastAPI/Uvicorn; success requires live process + /api/health."""
    mgr = DashboardProcessManager()
    result = mgr.start()
    if result.get("ok"):
        print_kv(
            [
                ("state", result.get("state", "RUNNING")),
                ("url", result.get("url")),
                ("pid", result.get("pid")),
                ("health", "PASS" if result.get("health") else "FAIL"),
                ("frontend", "PASS" if result.get("frontend_present") else "MISSING"),
                ("repo_sha", result.get("repo_sha")),
                ("frontend_build_sha", result.get("frontend_build_sha")),
                ("log", result.get("log_path")),
            ],
            title="Dashboard running",
        )
        return

    console.print(f"[red]{result.get('message', 'Dashboard failed to start')}[/red]")
    for line in result.get("log_tail") or []:
        console.print(f"[dim]{line}[/dim]")
    if result.get("suggested"):
        console.print(f"[yellow]Suggested next command:[/yellow] {result['suggested']}")
    raise typer.Exit(code=1)


@dashboard_app.command("status")
def dashboard_status() -> None:
    """Authoritative dashboard lifecycle status (single source of truth)."""
    mgr = DashboardProcessManager()
    status = mgr.classify()
    print_kv(
        [
            ("state", status["state"]),
            ("pid", status["pid"]),
            ("process_alive", status["process_alive"]),
            ("port_listening", status["port_listening"]),
            ("health", "PASS" if status["health"] else "unavailable"),
            ("url", status["url"]),
            ("log", status["log_path"]),
            ("last_exit_code", status.get("last_exit_code")),
            ("last_error", status.get("last_error")),
        ],
        title="dashboard status",
    )
    if status["health"] is not None:
        print_json(status["health"])


@dashboard_app.command("stop")
def dashboard_stop() -> None:
    """Stop the qseh-owned dashboard process; never kill foreign :8766 owners."""
    mgr = DashboardProcessManager()
    result = mgr.stop()
    if result.get("ok"):
        console.print(f"[green]{result.get('message')}[/green]")
        return
    console.print(f"[red]{result.get('message')}[/red]")
    raise typer.Exit(code=1)


@dashboard_app.command("open")
def dashboard_open(
    start: bool = typer.Option(
        False,
        "--start",
        help="Start the dashboard first if it is not healthy.",
    ),
) -> None:
    """Open the dashboard URL only when healthy."""
    mgr = DashboardProcessManager()
    result = mgr.open_browser(start_if_needed=start)
    if result.get("ok"):
        console.print(f"[green]{result.get('message')}[/green]")
        return
    console.print(f"[yellow]{result.get('message')}[/yellow]")
    raise typer.Exit(code=1)


@dashboard_app.command("diagnose")
def dashboard_diagnose() -> None:
    """Print venue-ready dashboard diagnostics (no secrets)."""
    mgr = DashboardProcessManager()
    print_json(mgr.diagnose())


@dashboard_app.command("build")
def dashboard_build(
    clean: bool = typer.Option(
        False,
        "--clean",
        help="Force pnpm install --frozen-lockfile before build.",
    ),
) -> None:
    """Build the Figma frontend production bundle."""
    mgr = DashboardProcessManager()
    result = mgr.build_frontend(clean=clean)
    if result.get("ok"):
        print_kv(
            [
                ("message", result.get("message")),
                ("steps", ", ".join(result.get("steps") or [])),
                ("dist", result.get("dist")),
                ("frontend_build_sha", result.get("frontend_build_sha")),
            ],
            title="dashboard build",
        )
        return
    console.print(f"[red]{result.get('message')}[/red]")
    if result.get("stderr"):
        console.print(result["stderr"])
    raise typer.Exit(code=1)
