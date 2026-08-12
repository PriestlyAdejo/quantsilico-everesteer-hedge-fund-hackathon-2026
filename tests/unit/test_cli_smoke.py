"""Smoke tests for the Typer CLI entry point."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from qs_everesteer.cli import app
from qs_everesteer.data.synthetic import generate_synthetic_event_data


runner = CliRunner()


def test_doctor_smoke() -> None:
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0, result.output
    assert "python" in result.output.lower() or "everestapi" in result.output.lower()
    assert "qseh doctor" in result.output or "repo_root" in result.output


def test_event_submission_mode_smoke() -> None:
    result = runner.invoke(app, ["event", "submission-mode"])
    assert result.exit_code == 0, result.output
    assert "DRY_RUN" in result.output or "DISABLED" in result.output or "ARMED" in result.output
    assert "submission" in result.output.lower()


def test_data_audit_synthetic(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("QSEH_SYNTHETIC", "1")
    # Point synthetic generation at a temp dir by patching find_repo_root consumers
    # via generating fixtures and auditing that path explicitly.
    paths = generate_synthetic_event_data(
        tmp_path,
        seed=3,
        n_features=8,
        n_practice_ids=20,
        n_live_ids=8,
        rows_per_exped=2,
        n_expeds=4,
    )
    result = runner.invoke(app, ["data", "audit", str(paths["train"])])
    assert result.exit_code == 0, result.output
    assert "integrity" in result.output
    assert "schema_sha256" in result.output
