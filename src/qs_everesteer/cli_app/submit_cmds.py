"""Submission check / practice / live / listings / leaderboard / standings."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import typer

from qs_everesteer.cli_app.common import (
    console,
    print_json,
    print_mutation_context,
    repo_root,
    wants_synthetic,
)
from qs_everesteer.event.adapter import EveresteerAdapter
from qs_everesteer.fsutil import read_json
from qs_everesteer.paths import artifacts_dir
from qs_everesteer.state.research import SubmissionMode, load_research_state
from qs_everesteer.submission.guard import SubmissionContext, SubmissionGuard
from qs_everesteer.submission.mode import get_mode
from qs_everesteer.submission.pipeline import (
    PipelineRequest,
    QuotaController,
    SubmissionPipeline,
)

submit_app = typer.Typer(help="Submission guard and upload pipeline.", no_args_is_help=True)


def _safe_client_call(adapter: EveresteerAdapter, method: str, **kwargs: Any) -> dict[str, Any]:
    client = adapter._get_client()  # noqa: SLF001 — intentional thin CLI bridge
    if client is None or not hasattr(client, method):
        return {
            "available": False,
            "method": method,
            "reason": "SDK client/method unavailable",
            "synthetic": adapter.synthetic,
        }
    try:
        value = getattr(client, method)(**kwargs) if kwargs else getattr(client, method)()
        return {"available": True, "method": method, "value": value}
    except Exception as exc:  # noqa: BLE001
        return {
            "available": False,
            "method": method,
            "error": f"{type(exc).__name__}: {exc}",
        }


@submit_app.command("check")
def submit_check(
    predictions: Optional[Path] = typer.Option(None, "--predictions"),
    lane: str = typer.Option("practice", "--lane"),
    candidate: str = typer.Option("champion", "--candidate"),
    round_id: Optional[str] = typer.Option(None, "--round"),
) -> None:
    """Run SubmissionGuard without uploading."""
    root = repo_root()
    state = load_research_state(root)
    mode = get_mode(root)
    quota = QuotaController(repo_root=root).snapshot()
    print_mutation_context(lane=lane, candidate=candidate, run_id=None)
    ctx = SubmissionContext(
        event_id=state.get("meta", {}).get("event_id"),
        event_snapshot_id=state.get("event_snapshot_id"),
        round_id=round_id or state.get("round") or "UNKNOWN",
        lane=lane,
        candidate_id=candidate,
        predictions_path=predictions,
        quota_remaining=quota.get("remaining"),
        quota_known=bool(quota.get("known")),
        mode=mode,
    )
    result = SubmissionGuard().validate(ctx)
    print_json(result.to_dict())
    if not result.ok:
        raise typer.Exit(code=1)


def _run_submit(lane: str, predictions: Path | None, candidate: str, round_id: str | None) -> None:
    root = repo_root()
    state = load_research_state(root)
    mode = get_mode(root)
    print_mutation_context(lane=lane, candidate=candidate)

    if mode is SubmissionMode.DISABLED:
        console.print("[red]submission mode DISABLED — refusing[/red]")
        raise typer.Exit(code=1)

    adapter = EveresteerAdapter(synthetic=wants_synthetic())
    inspected = adapter.inspect()
    event_id = state.get("meta", {}).get("event_id") or inspected.get("event_id") or "UNKNOWN_EVENT"
    rid = round_id or state.get("round") or inspected.get("current_round") or "UNKNOWN_ROUND"
    snap = state.get("event_snapshot_id")
    split_fp = (state.get("live_evidence") or {}).get("split_fingerprint") or "UNKNOWN_SPLIT"

    request = PipelineRequest(
        event_id=str(event_id),
        round_id=str(rid),
        lane=lane,
        candidate_id=candidate,
        split_fingerprint=str(split_fp),
        action=f"submit_{lane}",
        event_snapshot_id=str(snap) if snap else None,
        predictions_path=predictions,
        capabilities={
            "validation_available": inspected.get("validation_available"),
            "live_available": inspected.get("live_available"),
            "submission_cap": inspected.get("submission_cap"),
        },
    )
    pipeline = SubmissionPipeline(repo_root=root, adapter=adapter)
    result = pipeline.run(request)
    print_json(result.to_dict())

    if mode is SubmissionMode.DRY_RUN:
        console.print("[yellow]DRY_RUN — no real upload performed[/yellow]")
    if not result.ok:
        raise typer.Exit(code=1)
    if mode is SubmissionMode.ARMED and lane in {"live", "event"} and result.upload:
        console.print("[green]ARMED live submit completed (see upload record)[/green]")


@submit_app.command("practice")
def submit_practice(
    predictions: Optional[Path] = typer.Option(None, "--predictions"),
    candidate: str = typer.Option("champion", "--candidate"),
    round_id: Optional[str] = typer.Option(None, "--round"),
) -> None:
    """Practice/diagnostics submit respecting DISABLED/DRY_RUN/ARMED."""
    _run_submit("practice", predictions, candidate, round_id)


@submit_app.command("live")
def submit_live(
    predictions: Optional[Path] = typer.Option(None, "--predictions"),
    candidate: str = typer.Option("champion", "--candidate"),
    round_id: Optional[str] = typer.Option(None, "--round"),
) -> None:
    """Live event submit respecting DISABLED/DRY_RUN/ARMED (+ guard)."""
    mode = get_mode(repo_root())
    if mode is SubmissionMode.ARMED:
        console.print("[bold yellow]ARMED live path — guard + quota enforced[/bold yellow]")
    _run_submit("live", predictions, candidate, round_id)


def register_listing_commands(app: typer.Typer) -> None:
    """Top-level submissions / leaderboard / standings."""

    @app.command("submissions")
    def submissions() -> None:
        """List local submission artefacts / idempotency ledger entries."""
        root = repo_root()
        sub_dir = artifacts_dir(root) / "submissions"
        local = []
        if sub_dir.is_dir():
            local = [str(p) for p in sorted(sub_dir.glob("*"))[:50]]
        ledger_path = root / "runs" / "state" / "idempotency.json"
        ledger = read_json(ledger_path) if ledger_path.exists() else {"entries": {}}
        entries = ledger.get("entries") if isinstance(ledger, dict) else {}
        print_json({"local_artefacts": local, "idempotency_entries": len(entries or {}), "entries": entries})

    @app.command("leaderboard")
    def leaderboard() -> None:
        """Fetch official leaderboard when available (never invent ranks)."""
        adapter = EveresteerAdapter(synthetic=wants_synthetic())
        result = _safe_client_call(adapter, "get_leaderboard")
        if not result.get("available"):
            diag = _safe_client_call(adapter, "get_diagnostics_leaderboard")
            print_json({"leaderboard": result, "diagnostics_leaderboard": diag})
            return
        print_json(result)

    @app.command("standings")
    def standings() -> None:
        """Fetch diagnostics standings when available."""
        adapter = EveresteerAdapter(synthetic=wants_synthetic())
        print_json(_safe_client_call(adapter, "get_diagnostics_standings"))
