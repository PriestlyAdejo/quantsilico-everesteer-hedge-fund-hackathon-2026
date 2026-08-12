"""Competition autopilot status / run / stop."""

from __future__ import annotations

import typer

from qs_everesteer.autopilot.orchestrator import CompetitionAutopilot
from qs_everesteer.cli_app.common import console, print_json, print_mutation_context, repo_root
from qs_everesteer.state.research import load_research_state, update_research_state

autopilot_app = typer.Typer(help="Deterministic competition autopilot (no LLM).", no_args_is_help=True)


@autopilot_app.command("status")
def autopilot_status() -> None:
    """Show autopilot stage / history from research state."""
    state = load_research_state(repo_root())
    print_json(
        {
            "autopilot_active": state.get("autopilot_active"),
            "autopilot_stage": state.get("autopilot_stage", "DISCOVER"),
            "submission_mode": state.get("submission_mode"),
            "history_len": len(state.get("autopilot_history") or []),
            "last": (state.get("autopilot_history") or [None])[-1],
        }
    )


@autopilot_app.command("run")
def autopilot_run(
    profile: str = typer.Option(
        "competition-aggressive",
        "--profile",
        help="Autopilot profile name.",
    ),
    max_steps: int | None = typer.Option(
        None,
        "--max-steps",
        help="Optional step cap (default: run until COMPLETE).",
    ),
) -> None:
    """Advance the persisted autopilot workflow (never auto-arms submissions)."""
    profile_norm = profile.strip().replace("-", "_")
    print_mutation_context(lane="autopilot", extra={"profile": profile_norm})
    root = repo_root()

    def _mutate(state: dict) -> None:
        state["autopilot_active"] = True
        state.setdefault("autopilot_stage", "DISCOVER")

    update_research_state(_mutate, repo_root=root)
    state = CompetitionAutopilot(root).run(profile=profile_norm, max_steps=max_steps)
    print_json(
        {
            "autopilot_active": state.get("autopilot_active"),
            "autopilot_stage": state.get("autopilot_stage"),
            "submission_mode": state.get("submission_mode"),
            "steps": len(state.get("autopilot_history") or []),
        }
    )


@autopilot_app.command("stop")
def autopilot_stop() -> None:
    """Deactivate autopilot without erasing history."""
    print_mutation_context(lane="autopilot")

    def _mutate(state: dict) -> None:
        state["autopilot_active"] = False
        meta = state.setdefault("meta", {})
        meta["autopilot_stopped"] = True

    update_research_state(_mutate, repo_root=repo_root())
    console.print("[yellow]autopilot stopped[/yellow]")
