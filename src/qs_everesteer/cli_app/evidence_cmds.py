"""Lineage and artifact verification commands."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import typer

from qs_everesteer.cli_app.common import print_json, repo_root
from qs_everesteer.fsutil import read_json

evidence_app = typer.Typer(no_args_is_help=True, help="Verify persisted research evidence.")


def verify_evidence(root: Path) -> dict[str, Any]:
    checked = 0
    failures: list[dict[str, str]] = []
    experiments = root / "runs" / "experiments"
    if experiments.is_dir():
        for run_path in sorted(experiments.glob("*/run.json")):
            run = read_json(run_path)
            checked += 1
            run_dir = run_path.parent
            for required in ("metrics.json", "decision.json", "resource.json"):
                if not (run_dir / required).exists():
                    failures.append({"run": run_dir.name, "reason": f"missing {required}"})
            if run.get("status") != "COMPLETED":
                continue
            if not (run_dir / "oof.parquet").exists():
                failures.append({"run": run_dir.name, "reason": "completed run missing OOF"})
            metadata = run.get("model_metadata") or {}
            artefact_path = metadata.get("artefact_path")
            expected = metadata.get("artefact_hash")
            if artefact_path and expected:
                artefact = Path(artefact_path)
                if not artefact.exists():
                    failures.append({"run": run_dir.name, "reason": "model artefact missing"})
                elif hashlib.sha256(artefact.read_bytes()).hexdigest() != expected:
                    failures.append({"run": run_dir.name, "reason": "model hash mismatch"})
    return {"ok": not failures, "checked_runs": checked, "failures": failures}


@evidence_app.command("verify")
def evidence_verify_cmd() -> None:
    """Verify run completeness and model hashes without loading pickle/joblib."""
    result = verify_evidence(repo_root())
    print_json(result)
    if not result["ok"]:
        raise typer.Exit(code=1)
