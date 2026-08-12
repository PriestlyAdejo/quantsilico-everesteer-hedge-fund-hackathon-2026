"""Typer CLI application package for `qseh`."""

from __future__ import annotations

import typer

from qs_everesteer.cli_app.autopilot_cmds import autopilot_app
from qs_everesteer.cli_app.baseline import baseline_app
from qs_everesteer.cli_app.dashboard_cmds import dashboard_app
from qs_everesteer.cli_app.data_cmds import data_app
from qs_everesteer.cli_app.docs_cmds import docs_app
from qs_everesteer.cli_app.doctor import run_doctor
from qs_everesteer.cli_app.emergency import run_emergency
from qs_everesteer.cli_app.ensemble_cmds import ensemble_app
from qs_everesteer.cli_app.event import event_app
from qs_everesteer.cli_app.rehearsal import run_rehearsal
from qs_everesteer.cli_app.research import register_research_commands
from qs_everesteer.cli_app.sdk import sdk_app
from qs_everesteer.cli_app.stake_cmds import stake_app
from qs_everesteer.cli_app.submit_cmds import register_listing_commands, submit_app

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="QuantSilico × Everesteer 2026 CLI",
)


@app.command("doctor")
def doctor_cmd() -> None:
    """Check Python, everestapi, disk, optional GPU, and repo paths."""
    run_doctor()


@app.command("rehearsal")
def rehearsal_cmd() -> None:
    """Synthetic end-to-end rehearsal (works without dashboard/LLM)."""
    result = run_rehearsal()
    if result.get("run_status") == "FAILED" or result.get("audit_integrity") == "fail":
        raise typer.Exit(code=1)


@app.command("emergency")
def emergency_cmd(
    send: bool = typer.Option(False, "--send", help="Queue a local alert marker (no secrets)."),
) -> None:
    """Disarm submissions, stop autopilot, snapshot event."""
    run_emergency(send=send)


app.add_typer(sdk_app, name="sdk")
app.add_typer(event_app, name="event")
app.add_typer(data_app, name="data")
app.add_typer(baseline_app, name="baseline")
register_research_commands(app)
app.add_typer(ensemble_app, name="ensemble")
app.add_typer(submit_app, name="submit")
register_listing_commands(app)
app.add_typer(stake_app, name="stake")
app.add_typer(autopilot_app, name="autopilot")
app.add_typer(dashboard_app, name="dashboard")
app.add_typer(docs_app, name="docs")

__all__ = ["app"]
