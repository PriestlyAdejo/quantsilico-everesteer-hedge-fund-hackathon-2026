"""Emergency operator path — disarm + snapshot + stop autopilot."""

from __future__ import annotations

from qs_everesteer.cli_app.common import console, print_json, print_mutation_context, repo_root, wants_synthetic
from qs_everesteer.event.adapter import EveresteerAdapter
from qs_everesteer.state.research import update_research_state
from qs_everesteer.submission.mode import disarm_submissions, get_mode


def run_emergency(*, send: bool = False) -> dict:
    """
    Safe emergency stop: disarm submissions, stop autopilot, snapshot event.

    ``--send`` is reserved for an explicit human-approved alert path and never
    transmits secrets.
    """
    root = repo_root()
    print_mutation_context(lane="emergency", extra={"send": send})
    mode_before = get_mode(root)
    mode_after = disarm_submissions(root)

    def _mutate(state: dict) -> None:
        state["autopilot_active"] = False
        meta = state.setdefault("meta", {})
        meta["emergency"] = True
        meta["source"] = "emergency"

    update_research_state(_mutate, repo_root=root)
    snap = EveresteerAdapter(synthetic=wants_synthetic()).snapshot(root)
    result = {
        "submission_mode_before": mode_before.value,
        "submission_mode_after": mode_after.value,
        "autopilot_active": False,
        "snapshot_id": snap.get("snapshot_id"),
        "send": send,
        "alert": (
            "ALERT QUEUED (local only — no external send implemented)"
            if send
            else "no alert sent"
        ),
    }
    print_json(result)
    if send:
        console.print("[yellow]--send noted; no secrets transmitted[/yellow]")
    console.print("[green]emergency path complete — submissions disarmed[/green]")
    return result
