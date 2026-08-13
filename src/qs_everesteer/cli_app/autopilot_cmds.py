"""Competition autopilot status / run / stop."""

from __future__ import annotations

import typer

from qs_everesteer.autopilot.adaptive import AdaptiveCompetitionController, AdaptivePolicy
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


def _policy(
    *,
    allow_live_submit: bool,
    max_live: int,
    max_validation: int,
    reserve: int,
    poll_seconds: float,
    allow_auto_stake: bool,
    stake_cap_usdc: float | None,
    stake_bankroll_fraction: float,
    stake_slots: int,
) -> AdaptivePolicy:
    return AdaptivePolicy(
        max_live_models_per_round=max_live,
        max_validation_models_per_cycle=max_validation,
        upload_reserve=reserve,
        poll_seconds=poll_seconds,
        allow_live_submit=allow_live_submit,
        allow_auto_stake=allow_auto_stake,
        max_stake_usdc_per_round=stake_cap_usdc,
        stake_bankroll_fraction=stake_bankroll_fraction,
        stake_slots=stake_slots,
    )


@autopilot_app.command("reconcile")
def adaptive_reconcile() -> None:
    """Synchronise SDK truth into the research state without external writes."""
    print_json(AdaptiveCompetitionController(repo_root()).reconcile())


@autopilot_app.command("tick")
def adaptive_tick(
    allow_live_submit: bool = typer.Option(False, "--allow-live-submit"),
    max_live: int = typer.Option(6, "--max-live", min=1, max=150),
    max_validation: int = typer.Option(4, "--max-validation", min=0, max=12),
    reserve: int = typer.Option(20, "--upload-reserve", min=1),
    allow_auto_stake: bool = typer.Option(False, "--allow-auto-stake"),
    stake_cap_usdc: float | None = typer.Option(None, "--stake-cap-usdc", min=1.0),
    stake_bankroll_fraction: float = typer.Option(0.5, "--stake-bankroll-fraction", min=0.01, max=1.0),
    stake_slots: int = typer.Option(3, "--stake-slots", min=1, max=5),
) -> None:
    """Perform one bounded reconcile/train/score/submit/adapt cycle."""
    print_mutation_context(lane="adaptive-autopilot")
    policy = _policy(
        allow_live_submit=allow_live_submit, max_live=max_live,
        max_validation=max_validation, reserve=reserve, poll_seconds=15.0,
        allow_auto_stake=allow_auto_stake, stake_cap_usdc=stake_cap_usdc,
        stake_bankroll_fraction=stake_bankroll_fraction, stake_slots=stake_slots,
    )
    print_json(AdaptiveCompetitionController(repo_root(), policy=policy).tick())


@autopilot_app.command("live")
def adaptive_live(
    allow_live_submit: bool = typer.Option(False, "--allow-live-submit"),
    max_live: int = typer.Option(6, "--max-live", min=1, max=150),
    max_validation: int = typer.Option(4, "--max-validation", min=0, max=12),
    reserve: int = typer.Option(20, "--upload-reserve", min=1),
    poll_seconds: float = typer.Option(15.0, "--poll-seconds", min=5.0, max=300.0),
    max_ticks: int | None = typer.Option(None, "--max-ticks", min=1),
    allow_auto_stake: bool = typer.Option(False, "--allow-auto-stake"),
    stake_cap_usdc: float | None = typer.Option(None, "--stake-cap-usdc", min=1.0),
    stake_bankroll_fraction: float = typer.Option(0.5, "--stake-bankroll-fraction", min=0.01, max=1.0),
    stake_slots: int = typer.Option(3, "--stake-slots", min=1, max=5),
) -> None:
    """Run the adaptive controller until stopped, bounded, or the event ends."""
    print_mutation_context(lane="adaptive-autopilot")
    policy = _policy(
        allow_live_submit=allow_live_submit, max_live=max_live,
        max_validation=max_validation, reserve=reserve, poll_seconds=poll_seconds,
        allow_auto_stake=allow_auto_stake, stake_cap_usdc=stake_cap_usdc,
        stake_bankroll_fraction=stake_bankroll_fraction, stake_slots=stake_slots,
    )
    print_json(
        AdaptiveCompetitionController(repo_root(), policy=policy).run(max_ticks=max_ticks)
    )
