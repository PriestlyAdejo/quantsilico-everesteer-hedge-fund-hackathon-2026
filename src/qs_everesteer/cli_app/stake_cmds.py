"""Staking status / recommend (never executes real-money transfers)."""

from __future__ import annotations

import typer

from qs_everesteer.cli_app.common import console, print_json, print_mutation_context, repo_root, wants_synthetic
from qs_everesteer.event.adapter import EveresteerAdapter
from qs_everesteer.state.research import load_research_state
from qs_everesteer.staking.classify import classify_staking, recommend_allocations

stake_app = typer.Typer(help="Stake classification (no real transfers).", no_args_is_help=True)


def _staking_payload() -> dict:
    adapter = EveresteerAdapter(synthetic=wants_synthetic())
    inspected = adapter.inspect()
    raw = inspected.get("raw") or {}
    staking = raw.get("staking") if isinstance(raw, dict) else None
    return {
        "staking": staking if isinstance(staking, dict) else {},
        "connection": inspected.get("connection"),
        "staking_available": inspected.get("staking_available"),
        "synthetic": inspected.get("synthetic"),
        "provenance": inspected.get("provenance"),
    }


@stake_app.command("status")
def stake_status() -> None:
    """Classify current stake mode from event capabilities (never invent balances)."""
    print_mutation_context(lane="stake")
    payload = _staking_payload()
    classification = classify_staking(payload)
    print_json({"payload_summary": {k: payload.get(k) for k in ("connection", "staking_available", "synthetic", "provenance")}, "classification": classification.to_dict()})


@stake_app.command("recommend")
def stake_recommend(
    risk_profile: str = typer.Option("aggressive", "--profile"),
) -> None:
    """Recommend allocations. Real-money modes always require human action."""
    print_mutation_context(lane="stake")
    state = load_research_state(repo_root())
    champion = state.get("champion")
    model_ids: list[str] = []
    if isinstance(champion, dict) and champion.get("id"):
        model_ids.append(str(champion["id"]))
    elif isinstance(champion, str) and champion:
        model_ids.append(champion)
    for member in (state.get("ensemble") or {}).get("members") or []:
        mid = str(member)
        if mid not in model_ids:
            model_ids.append(mid)

    payload = _staking_payload()
    classification = classify_staking(payload)
    rec = recommend_allocations(
        classification,
        model_ids=model_ids,
        risk_profile=risk_profile,
    )
    print_json({"classification": classification.to_dict(), "recommendation": rec.to_dict()})
    if rec.requires_human:
        console.print("[yellow]human action required — no wallet tx will be constructed[/yellow]")
