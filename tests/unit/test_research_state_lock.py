from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from qs_everesteer.fsutil import research_state_lock
from qs_everesteer.state.research import (
    SubmissionMode,
    default_research_state,
    load_research_state,
    save_research_state,
    update_research_state,
)


def test_default_submission_mode_is_dry_run():
    state = default_research_state()
    assert state["submission_mode"] == SubmissionMode.DRY_RUN.value
    assert SubmissionMode.DISABLED.value == "DISABLED"
    assert SubmissionMode.ARMED.value == "ARMED"


def test_load_creates_and_save_roundtrips(tmp_path: Path):
    state = load_research_state(tmp_path)
    assert state["submission_mode"] == "DRY_RUN"
    assert (tmp_path / "runs" / "state" / "research_state.json").is_file()

    state["champion"] = "synth-lgbm-01"
    state["autopilot_active"] = True
    state["active_jobs"] = ["job-abc"]
    save_research_state(state, tmp_path)

    again = load_research_state(tmp_path)
    assert again["champion"] == "synth-lgbm-01"
    assert again["autopilot_active"] is True
    assert again["active_jobs"] == ["job-abc"]


def test_update_research_state_under_lock(tmp_path: Path):
    load_research_state(tmp_path)

    def bump(s: dict) -> None:
        s["round"] = "R2"
        s["submission_mode"] = SubmissionMode.DISABLED.value

    out = update_research_state(bump, tmp_path)
    assert out["round"] == "R2"
    assert out["submission_mode"] == "DISABLED"


def test_research_state_lock_serializes_writers(tmp_path: Path):
    counter_path = tmp_path / "runs" / "state" / "counter.txt"
    counter_path.parent.mkdir(parents=True)
    counter_path.write_text("0", encoding="utf-8")

    def increment(_: int) -> None:
        with research_state_lock(tmp_path):
            n = int(counter_path.read_text(encoding="utf-8"))
            counter_path.write_text(str(n + 1), encoding="utf-8")

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(increment, range(40)))

    assert counter_path.read_text(encoding="utf-8") == "40"
