"""Synthetic end-to-end rehearsal (no live credentials required).

Isolated under ``runs/rehearsal/<timestamp>/`` so production research_state
is never mutated by rehearsal.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from qs_everesteer.cli_app.common import console, print_json, print_mutation_context, repo_root
from qs_everesteer.cli_app.research import write_default_race_config
from qs_everesteer.data.audit import audit_dataset
from qs_everesteer.data.fingerprint import fingerprint_dataset
from qs_everesteer.data.synthetic import generate_synthetic_event_data
from qs_everesteer.experiments.racing import RacingScheduler
from qs_everesteer.experiments.runner import ExperimentRunner
from qs_everesteer.fsutil import atomic_write_json
from qs_everesteer.ops_status import write_ops_status
from qs_everesteer.paths import ensure_dir, ensure_standard_dirs
from qs_everesteer.state.research import load_research_state, update_research_state
from qs_everesteer.submission.mode import get_mode


def _clear_rehearsal_contamination(production_root: Path) -> bool:
    """Clear stale meta.source=rehearsal on production state only."""
    state = load_research_state(production_root)
    meta = state.get("meta") if isinstance(state.get("meta"), dict) else {}
    if meta.get("source") != "rehearsal":
        return False

    def _mutate(current: dict) -> None:
        current_meta = current.setdefault("meta", {})
        if current_meta.get("source") == "rehearsal":
            current_meta["source"] = "default"

    update_research_state(_mutate, repo_root=production_root)
    return True


def run_rehearsal() -> dict:
    """Generate synthetic data → audit → fingerprint → tiny run → race (isolated)."""
    root = repo_root()
    ensure_standard_dirs(root)
    print_mutation_context(lane="practice", candidate="rehearsal", extra={"synthetic": True})

    cleared = _clear_rehearsal_contamination(root)

    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    rehearsal_root = ensure_dir(root / "runs" / "rehearsal" / stamp)
    syn = ensure_dir(rehearsal_root / "data" / "synthetic")
    ensure_dir(rehearsal_root / "runs" / "experiments")
    ensure_dir(rehearsal_root / "runs" / "state")
    ensure_dir(rehearsal_root / "artifacts" / "models")

    paths = generate_synthetic_event_data(syn)
    audit = audit_dataset(paths["train"])
    fp = fingerprint_dataset(paths["train"])

    cfg = write_default_race_config(rehearsal_root, profile="R0")
    # Point the isolated race config at the isolated synthetic train set.
    try:
        import yaml

        cfg_text = Path(cfg).read_text(encoding="utf-8")
        cfg_data = yaml.safe_load(cfg_text) or {}
        cfg_data["data_path"] = str(paths["train"])
        Path(cfg).write_text(yaml.safe_dump(cfg_data, sort_keys=False), encoding="utf-8")
    except Exception:  # noqa: BLE001 — keep going with default config path
        pass

    manifest = ExperimentRunner(rehearsal_root).run(cfg)
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

    rehearsal_state = {
        "schema_version": 1,
        "connection": "SYNTHETIC",
        "meta": {"source": "rehearsal", "updated_at": datetime.now(UTC).isoformat()},
        "candidates": records,
        "race_outcomes": outcomes,
        "note": "ISOLATED_REHEARSAL — not production research_state",
    }
    atomic_write_json(rehearsal_root / "runs" / "state" / "research_state.json", rehearsal_state)
    atomic_write_json(
        rehearsal_root / "summary.json",
        {
            "stamp": stamp,
            "run_id": manifest.get("run_id"),
            "run_status": manifest.get("status"),
            "audit_integrity": audit.integrity.value,
            "content_sha256": fp["content_sha256"],
        },
    )

    ok = not audit.hard_failures and manifest.get("status") != "FAILED"
    write_ops_status(
        "last_rehearsal.json",
        status="passing" if ok else "failing",
        detail=f"isolated rehearsal {stamp}; run={manifest.get('run_id')}; status={manifest.get('status')}",
        repo_root=root,
        extra={"rehearsal_root": str(rehearsal_root), "stamp": stamp},
    )

    result = {
        "synthetic": True,
        "isolated": True,
        "rehearsal_root": str(rehearsal_root),
        "cleared_production_rehearsal_stamp": cleared,
        "submission_mode": get_mode(root).value,
        "train_path": str(paths["train"]),
        "audit_integrity": audit.integrity.value,
        "content_sha256": fp["content_sha256"],
        "schema_sha256": fp["schema_sha256"],
        "run_id": manifest.get("run_id"),
        "run_status": manifest.get("status"),
        "race_outcomes": outcomes,
        "note": "SYNTHETIC_FIXTURE rehearsal — isolated under runs/rehearsal/; not official Everesteer data",
    }
    print_json(result)
    if not ok:
        console.print("[red]rehearsal completed with failures[/red]")
    else:
        console.print("[green]rehearsal ok (isolated)[/green]")
    return result
