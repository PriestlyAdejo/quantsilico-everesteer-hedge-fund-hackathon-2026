"""Event inspect / watch / snapshot / submission-mode commands."""

from __future__ import annotations

import time
from pathlib import Path

import typer

from qs_everesteer.cli_app.common import (
    console,
    print_json,
    print_kv,
    print_mutation_context,
    repo_root,
    wants_synthetic,
)
from qs_everesteer.event.adapter import EveresteerAdapter
from qs_everesteer.event.timebase import countdown, extract_deadline, extract_server_observed_at
from qs_everesteer.fsutil import read_json
from qs_everesteer.live.rounds import RoundController
from qs_everesteer.paths import runs_dir
from qs_everesteer.state.research import SubmissionMode, load_research_state, update_research_state
from qs_everesteer.submission.mode import (
    arm_submissions,
    disarm_submissions,
    get_mode,
    set_mode,
)

event_app = typer.Typer(help="Event control and submission arming.", no_args_is_help=True)


def _adapter() -> EveresteerAdapter:
    return EveresteerAdapter(synthetic=wants_synthetic())


def _latest_snapshot_id(root: Path) -> str | None:
    event_dir = runs_dir(root) / "event"
    if not event_dir.is_dir():
        return None
    files = sorted(event_dir.glob("event_snapshot_*.json"), reverse=True)
    if not files:
        return None
    try:
        data = read_json(files[0])
        if isinstance(data, dict) and data.get("snapshot_id"):
            return str(data["snapshot_id"])
    except Exception:  # noqa: BLE001
        pass
    return files[0].stem


@event_app.command("inspect")
def event_inspect() -> None:
    """Capability-detecting event inspection (never invents quotas/standings)."""
    inspected = _adapter().inspect()
    summary = {
        k: inspected.get(k)
        for k in (
            "sdk_version",
            "connection",
            "event_id",
            "current_round",
            "tournament",
            "submission_cap",
            "validation_available",
            "live_available",
            "standings_available",
            "staking_available",
            "server_compute_available",
            "key_fingerprint",
            "synthetic",
            "error",
            "provenance",
        )
    }
    print_json(summary)


@event_app.command("watch")
def event_watch(
    interval: float = typer.Option(5.0, "--interval", "-i", help="Seconds between polls."),
    once: bool = typer.Option(False, "--once", help="Single poll then exit."),
    tick_round: bool = typer.Option(
        False,
        "--tick-round",
        help="Advance one RoundController cycle (detect→pull→guard→submit path).",
    ),
) -> None:
    """Poll current round / deadline using server-observed time when available."""
    adapter = _adapter()
    controller: RoundController | None = None
    if tick_round:
        controller = RoundController(repo_root=repo_root(), adapter=adapter)
    while True:
        inspected = adapter.inspect()
        raw = inspected.get("raw") or {}
        deadline = extract_deadline(raw.get("current_round") if isinstance(raw, dict) else None)
        observed = extract_server_observed_at(
            raw.get("current_round") if isinstance(raw, dict) else None
        )
        cd = countdown(deadline, now=observed) if deadline else None
        print_kv(
            [
                ("connection", inspected.get("connection")),
                ("event_id", inspected.get("event_id")),
                ("round", inspected.get("current_round")),
                ("deadline", deadline.isoformat() if deadline else None),
                ("server_observed_at", observed.isoformat() if observed else None),
                ("seconds_remaining", cd.get("seconds_remaining") if cd else None),
                ("synthetic", inspected.get("synthetic")),
            ],
            title="event watch",
        )
        if controller is not None:
            print_mutation_context(lane="live", run_id=None)
            result = controller.tick()
            print_json(result.to_dict())
        if once or tick_round:
            break
        time.sleep(max(0.5, interval))


@event_app.command("snapshot")
def event_snapshot() -> None:
    """Write an event capability snapshot under runs/event/."""
    print_mutation_context(lane=None)
    record = _adapter().snapshot(repo_root())
    root = repo_root()

    def _mutate(state: dict) -> None:
        state["event_snapshot_id"] = record.get("snapshot_id")
        state["round"] = record.get("current_round")
        state["connection"] = record.get("connection")
        meta = state.setdefault("meta", {})
        meta["event_id"] = record.get("event_id")
        meta["source"] = "event_snapshot"

    update_research_state(_mutate, repo_root=root)
    print_json(
        {
            "snapshot_id": record.get("snapshot_id"),
            "path": record.get("path"),
            "event_id": record.get("event_id"),
            "current_round": record.get("current_round"),
            "connection": record.get("connection"),
            "submission_cap": record.get("submission_cap"),
            "key_fingerprint": record.get("key_fingerprint"),
            "provenance": record.get("provenance"),
        }
    )


@event_app.command("arm-submissions")
def event_arm(
    snapshot_id: str | None = typer.Option(
        None,
        "--snapshot-id",
        help="Event snapshot id required to arm (defaults to latest / state).",
    ),
) -> None:
    """Explicitly arm real uploads (requires a current event snapshot id)."""
    root = repo_root()
    snap = snapshot_id
    if not snap:
        snap = load_research_state(root).get("event_snapshot_id") or _latest_snapshot_id(root)
    if not snap:
        # Create a fresh snapshot so arming has a real id to bind to.
        record = _adapter().snapshot(root)
        snap = str(record.get("snapshot_id"))
    print_mutation_context(extra={"arming_snapshot": snap})
    mode = arm_submissions(str(snap), repo_root=root)
    console.print(f"[green]submission mode[/green] → {mode.value} (snapshot={snap})")


@event_app.command("disarm-submissions")
def event_disarm() -> None:
    """Return to DRY_RUN (safe default)."""
    print_mutation_context()
    mode = disarm_submissions(repo_root())
    console.print(f"[yellow]submission mode[/yellow] → {mode.value}")


@event_app.command("submission-mode")
def event_submission_mode(
    mode: str | None = typer.Argument(
        None,
        help="Optional mode to set: DISABLED | DRY_RUN | ARMED. Omit to print current.",
    ),
    snapshot_id: str | None = typer.Option(
        None, "--snapshot-id", help="Required when setting ARMED."
    ),
) -> None:
    """Show or set submission operating mode."""
    root = repo_root()
    if mode is None:
        current = get_mode(root)
        print_kv([("submission_mode", current.value)], title="submission mode")
        return
    target = mode.strip().upper()
    snap = snapshot_id
    if target == SubmissionMode.ARMED.value and not snap:
        snap = load_research_state(root).get("event_snapshot_id") or _latest_snapshot_id(root)
    print_mutation_context(extra={"requested_mode": target})
    try:
        result = set_mode(target, repo_root=root, event_snapshot_id=snap)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    console.print(f"submission mode → {result.value}")
