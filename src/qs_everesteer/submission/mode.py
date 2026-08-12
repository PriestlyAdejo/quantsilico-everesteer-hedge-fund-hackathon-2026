"""Submission operating mode: DISABLED | DRY_RUN | ARMED (default DRY_RUN)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qs_everesteer.state.research import (
    SubmissionMode,
    load_research_state,
    update_research_state,
)

__all__ = [
    "SubmissionMode",
    "arm_submissions",
    "disarm_submissions",
    "get_mode",
    "set_mode",
]


def get_mode(repo_root: str | Path | None = None) -> SubmissionMode:
    """Return the current submission mode (default DRY_RUN)."""
    state = load_research_state(repo_root)
    raw = state.get("submission_mode", SubmissionMode.DRY_RUN.value)
    try:
        return SubmissionMode(raw)
    except ValueError:
        return SubmissionMode.DRY_RUN


def set_mode(
    mode: SubmissionMode | str,
    repo_root: str | Path | None = None,
    *,
    event_snapshot_id: str | None = None,
) -> SubmissionMode:
    """
    Set submission mode in research state.

    Transitioning to ARMED requires a non-empty ``event_snapshot_id``
    (current event snapshot). No caller may silently auto-arm.
    """
    target = SubmissionMode(mode) if not isinstance(mode, SubmissionMode) else mode
    if target is SubmissionMode.ARMED:
        if not event_snapshot_id:
            raise ValueError("arming submissions requires a current event_snapshot_id")
        return arm_submissions(event_snapshot_id, repo_root=repo_root)

    def _mutate(state: dict[str, Any]) -> None:
        state["submission_mode"] = target.value
        if target is SubmissionMode.DISABLED:
            # Keep last snapshot id for audit; mode alone disables uploads.
            pass

    update_research_state(_mutate, repo_root=repo_root)
    return target


def arm_submissions(
    event_snapshot_id: str,
    repo_root: str | Path | None = None,
) -> SubmissionMode:
    """Explicitly enable real uploads. Requires a current event snapshot id."""
    snap = (event_snapshot_id or "").strip()
    if not snap:
        raise ValueError("arm_submissions requires a non-empty event_snapshot_id")

    def _mutate(state: dict[str, Any]) -> None:
        state["submission_mode"] = SubmissionMode.ARMED.value
        state["event_snapshot_id"] = snap
        meta = state.setdefault("meta", {})
        meta["armed_with_snapshot"] = snap
        meta["source"] = meta.get("source") or "submission_mode"

    update_research_state(_mutate, repo_root=repo_root)
    return SubmissionMode.ARMED


def disarm_submissions(repo_root: str | Path | None = None) -> SubmissionMode:
    """Return to DRY_RUN (safe default). Does not erase the last snapshot id."""

    def _mutate(state: dict[str, Any]) -> None:
        state["submission_mode"] = SubmissionMode.DRY_RUN.value
        meta = state.setdefault("meta", {})
        meta["disarmed"] = True

    update_research_state(_mutate, repo_root=repo_root)
    return SubmissionMode.DRY_RUN
