"""Shared CLI helpers: Rich console, safe context banners, JSON printing."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from qs_everesteer.paths import find_repo_root
from qs_everesteer.state.research import load_research_state
from qs_everesteer.submission.mode import get_mode
from qs_everesteer.submission.pipeline import QuotaController

console = Console()


def repo_root() -> Path:
    return find_repo_root()


def wants_synthetic() -> bool:
    """Return whether the operator explicitly enabled synthetic fixtures."""
    raw = os.environ.get("QSEH_SYNTHETIC", "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def print_json(payload: Any) -> None:
    console.print_json(json.dumps(payload, default=str, indent=2))


def print_kv(rows: list[tuple[str, Any]], *, title: str | None = None) -> None:
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("key", style="cyan")
    table.add_column("value")
    for key, value in rows:
        table.add_row(key, "null" if value is None else str(value))
    if title:
        console.print(Panel(table, title=title, border_style="dim"))
    else:
        console.print(table)


def mutation_context(
    *,
    lane: str | None = None,
    candidate: str | None = None,
    run_id: str | None = None,
    hashes: dict[str, str] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Safe operator context for mutating commands.

    Never includes API keys, wallet secrets, or raw credentials.
    """
    root = repo_root()
    state = load_research_state(root)
    mode = get_mode(root)
    budget = QuotaController(repo_root=root).snapshot()
    champion = state.get("champion")
    if candidate is not None:
        candidate_id = candidate
    elif isinstance(champion, dict):
        candidate_id = champion.get("id")
    else:
        candidate_id = champion
    ctx: dict[str, Any] = {
        "event": state.get("event_snapshot_id") or state.get("meta", {}).get("event_id"),
        "round": state.get("round"),
        "lane": lane,
        "candidate": candidate_id,
        "run_id": run_id,
        "hashes": hashes or {},
        "quota": {
            "cap": budget.get("cap"),
            "remaining": budget.get("remaining"),
            "known": budget.get("known"),
        },
        "submission_mode": mode.value,
        "connection": state.get("connection"),
        "autopilot_active": state.get("autopilot_active"),
    }
    if extra:
        ctx.update(extra)
    return ctx


def print_mutation_context(**kwargs: Any) -> dict[str, Any]:
    ctx = mutation_context(**kwargs)
    rows = [
        ("event", ctx.get("event")),
        ("round", ctx.get("round")),
        ("lane", ctx.get("lane")),
        ("candidate", ctx.get("candidate")),
        ("run_id", ctx.get("run_id")),
        ("submission_mode", ctx.get("submission_mode")),
        ("quota.cap", (ctx.get("quota") or {}).get("cap")),
        ("quota.remaining", (ctx.get("quota") or {}).get("remaining")),
        ("connection", ctx.get("connection")),
    ]
    hashes = ctx.get("hashes") or {}
    for name, digest in hashes.items():
        rows.append((f"hash.{name}", digest))
    print_kv(rows, title="mutation context")
    return ctx
