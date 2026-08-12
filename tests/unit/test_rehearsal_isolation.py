"""Rehearsal must not contaminate production research_state."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from qs_everesteer.cli_app.rehearsal import run_rehearsal
from qs_everesteer.state.research import load_research_state, save_research_state


def _hash_state(root: Path) -> str:
    path = root / "runs" / "state" / "research_state.json"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_rehearsal_isolates_from_production_state(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='t'\n", encoding="utf-8")
    save_research_state(
        {
            "connection": "LIVE",
            "champion": "keep-me",
            "meta": {"source": "live_event", "updated_at": "2026-01-01T00:00:00+00:00"},
        },
        tmp_path,
    )
    before = _hash_state(tmp_path)

    monkeypatch.setattr("qs_everesteer.cli_app.rehearsal.repo_root", lambda: tmp_path)

    # Keep synthetic/tiny experiment cheap and deterministic.
    result = run_rehearsal()
    assert result["isolated"] is True
    after = _hash_state(tmp_path)
    assert after == before

    state = load_research_state(tmp_path)
    assert state["champion"] == "keep-me"
    assert state["meta"]["source"] == "live_event"

    rehearsal_root = Path(result["rehearsal_root"])
    assert rehearsal_root.is_dir()
    assert (rehearsal_root / "runs" / "state" / "research_state.json").is_file()
    isolated = json.loads(
        (rehearsal_root / "runs" / "state" / "research_state.json").read_text(encoding="utf-8")
    )
    assert isolated["meta"]["source"] == "rehearsal"
    assert (tmp_path / "runs" / "state" / "last_rehearsal.json").is_file()


def test_rehearsal_clears_stale_production_stamp(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='t'\n", encoding="utf-8")
    save_research_state(
        {
            "connection": "SYNTHETIC",
            "champion": "was-contaminated",
            "meta": {"source": "rehearsal", "updated_at": "2026-01-01T00:00:00+00:00"},
        },
        tmp_path,
    )
    monkeypatch.setattr("qs_everesteer.cli_app.rehearsal.repo_root", lambda: tmp_path)
    result = run_rehearsal()
    assert result["cleared_production_rehearsal_stamp"] is True
    state = load_research_state(tmp_path)
    assert state["meta"]["source"] == "default"
    assert state["champion"] == "was-contaminated"
