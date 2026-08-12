"""Synthetic end-to-end rehearsal (no live credentials required)."""

from __future__ import annotations

from qs_everesteer.cli_app.common import console, print_json, print_mutation_context, repo_root
from qs_everesteer.cli_app.research import write_default_race_config
from qs_everesteer.data.audit import audit_dataset
from qs_everesteer.data.fingerprint import fingerprint_dataset
from qs_everesteer.data.synthetic import generate_synthetic_event_data
from qs_everesteer.experiments.racing import RacingScheduler
from qs_everesteer.experiments.runner import ExperimentRunner
from qs_everesteer.paths import ensure_standard_dirs, synthetic_data_dir
from qs_everesteer.state.research import update_research_state
from qs_everesteer.submission.mode import get_mode


def run_rehearsal() -> dict:
    """Generate synthetic data → audit → fingerprint → tiny run → race."""
    root = repo_root()
    ensure_standard_dirs(root)
    print_mutation_context(lane="practice", candidate="rehearsal", extra={"synthetic": True})

    syn = synthetic_data_dir(root)
    paths = generate_synthetic_event_data(syn)
    audit = audit_dataset(paths["train"])
    fp = fingerprint_dataset(paths["train"])

    cfg = write_default_race_config(root, profile="R0")
    manifest = ExperimentRunner(root).run(cfg)
    records = [
        {
            "candidate_id": manifest.get("run_id"),
            "run_id": manifest.get("run_id"),
            "status": manifest.get("status"),
            "score": 0.0,
            "diversity": 0.0,
            "integrity_ok": manifest.get("status") != "FAILED",
            "runtime_seconds": manifest.get("runtime_seconds"),
        }
    ]
    outcomes = [o.to_dict() for o in RacingScheduler().evaluate(records, "R0")]

    def _mutate(state: dict) -> None:
        state["connection"] = "SYNTHETIC"
        state["meta"]["source"] = "rehearsal"
        state["candidates"] = records
        state["race_outcomes"] = outcomes

    update_research_state(_mutate, repo_root=root)

    result = {
        "synthetic": True,
        "submission_mode": get_mode(root).value,
        "train_path": str(paths["train"]),
        "audit_integrity": audit.integrity.value,
        "content_sha256": fp["content_sha256"],
        "schema_sha256": fp["schema_sha256"],
        "run_id": manifest.get("run_id"),
        "run_status": manifest.get("status"),
        "race_outcomes": outcomes,
        "note": "SYNTHETIC_FIXTURE rehearsal — not official Everesteer data",
    }
    print_json(result)
    if audit.hard_failures or manifest.get("status") == "FAILED":
        console.print("[red]rehearsal completed with failures[/red]")
    else:
        console.print("[green]rehearsal ok[/green]")
    return result
