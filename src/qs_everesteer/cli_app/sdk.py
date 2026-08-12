"""SDK inspection commands."""

from __future__ import annotations

import typer

from qs_everesteer.cli_app.common import console, print_json, print_kv, wants_synthetic
from qs_everesteer.event.adapter import EveresteerAdapter, sdk_version

sdk_app = typer.Typer(help="everestapi SDK inspection.", no_args_is_help=True)


@sdk_app.command("info")
def sdk_info() -> None:
    """Show installed everestapi version and adapter fingerprint (never the key)."""
    adapter = EveresteerAdapter(synthetic=wants_synthetic())
    print_kv(
        [
            ("everestapi", sdk_version()),
            ("key_fingerprint", adapter.safe_key_fingerprint()),
            ("synthetic", adapter.synthetic),
            ("tournament", adapter.tournament),
        ],
        title="sdk info",
    )


@sdk_app.command("check")
def sdk_check() -> None:
    """Probe SDK client connectivity / capability discovery."""
    adapter = EveresteerAdapter(synthetic=wants_synthetic())
    inspected = adapter.inspect()
    # Strip large raw payloads for readability; keep probe summaries.
    summary = {
        "sdk_version": inspected.get("sdk_version"),
        "connection": inspected.get("connection"),
        "event_id": inspected.get("event_id"),
        "current_round": inspected.get("current_round"),
        "key_fingerprint": inspected.get("key_fingerprint"),
        "synthetic": inspected.get("synthetic"),
        "submission_cap": inspected.get("submission_cap"),
        "validation_available": inspected.get("validation_available"),
        "live_available": inspected.get("live_available"),
        "methods_present": inspected.get("methods_present"),
        "probes": inspected.get("probes"),
        "error": inspected.get("error"),
        "provenance": inspected.get("provenance"),
    }
    print_json(summary)
    if inspected.get("error"):
        console.print(f"[yellow]check reported:[/yellow] {inspected['error']}")
        raise typer.Exit(code=1)
