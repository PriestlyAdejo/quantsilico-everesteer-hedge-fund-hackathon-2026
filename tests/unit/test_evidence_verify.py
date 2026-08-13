from __future__ import annotations

from pathlib import Path

from qs_everesteer.cli_app.evidence_cmds import verify_evidence
from qs_everesteer.fsutil import atomic_write_json


def test_evidence_verifier_flags_incomplete_completed_run(tmp_path: Path):
    run = tmp_path / "runs" / "experiments" / "synthetic-run"
    atomic_write_json(run / "run.json", {"run_id": "synthetic-run", "status": "COMPLETED"})
    result = verify_evidence(tmp_path)
    assert not result["ok"]
    assert result["checked_runs"] == 1
    assert {failure["reason"] for failure in result["failures"]} >= {
        "missing metrics.json",
        "completed run missing OOF",
    }
