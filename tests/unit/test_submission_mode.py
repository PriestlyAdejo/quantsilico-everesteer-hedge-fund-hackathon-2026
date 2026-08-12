"""Submission mode DISABLED | DRY_RUN | ARMED."""

from __future__ import annotations

import pytest

from qs_everesteer.state.research import SubmissionMode, load_research_state
from qs_everesteer.submission.mode import (
    arm_submissions,
    disarm_submissions,
    get_mode,
    set_mode,
)


def test_default_mode_is_dry_run(tmp_path):
    assert get_mode(tmp_path) is SubmissionMode.DRY_RUN
    state = load_research_state(tmp_path)
    assert state["submission_mode"] == "DRY_RUN"


def test_disarm_returns_to_dry_run(tmp_path):
    arm_submissions("event_snapshot_test_001", repo_root=tmp_path)
    assert get_mode(tmp_path) is SubmissionMode.ARMED
    assert disarm_submissions(tmp_path) is SubmissionMode.DRY_RUN
    assert get_mode(tmp_path) is SubmissionMode.DRY_RUN


def test_arm_requires_snapshot_id(tmp_path):
    with pytest.raises(ValueError, match="event_snapshot_id"):
        arm_submissions("", repo_root=tmp_path)
    with pytest.raises(ValueError, match="event_snapshot_id"):
        set_mode(SubmissionMode.ARMED, repo_root=tmp_path)


def test_arm_records_snapshot_id(tmp_path):
    arm_submissions("snap-abc", repo_root=tmp_path)
    state = load_research_state(tmp_path)
    assert state["submission_mode"] == "ARMED"
    assert state["event_snapshot_id"] == "snap-abc"


def test_set_mode_disabled(tmp_path):
    set_mode("DISABLED", repo_root=tmp_path)
    assert get_mode(tmp_path) is SubmissionMode.DISABLED
