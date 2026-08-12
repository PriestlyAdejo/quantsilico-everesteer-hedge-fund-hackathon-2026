"""Load/save ``runs/state/research_state.json`` under an exclusive lock."""

from __future__ import annotations

from copy import deepcopy
from enum import StrEnum
from pathlib import Path
from typing import Any, Callable

from qs_everesteer.fsutil import atomic_write_json, read_json, research_state_lock
from qs_everesteer.paths import ensure_dir, find_repo_root, state_dir


class SubmissionMode(StrEnum):
    DISABLED = "DISABLED"
    DRY_RUN = "DRY_RUN"
    ARMED = "ARMED"


def default_research_state() -> dict[str, Any]:
    """Compact default state for a fresh research console."""
    return {
        "schema_version": 1,
        "event_snapshot_id": None,
        "round": None,
        "time_remaining_seconds": None,
        "submission_mode": SubmissionMode.DRY_RUN.value,
        "upload_budget": {
            "practice_remaining": None,
            "live_remaining": None,
            "cap": None,
        },
        "champion": None,
        "frontier": [],
        "ensemble": {
            "members": [],
            "blend_id": None,
        },
        "active_jobs": [],
        "recommendation": None,
        "autopilot_active": False,
        "connection": "NOT_CONNECTED",
        "correlations": {},
        "live_evidence": {},
        "saturated_branches": [],
        "pending_operators": [],
        "meta": {
            "updated_at": None,
            "source": "default",
        },
    }


def research_state_path(repo_root: str | Path | None = None) -> Path:
    root = Path(repo_root) if repo_root is not None else find_repo_root()
    return state_dir(root) / "research_state.json"


def load_research_state(repo_root: str | Path | None = None) -> dict[str, Any]:
    """Load state under lock; create defaults if the file is missing."""
    root = Path(repo_root) if repo_root is not None else find_repo_root()
    path = research_state_path(root)
    with research_state_lock(root):
        if not path.exists():
            state = default_research_state()
            ensure_dir(path.parent)
            atomic_write_json(path, state)
            return deepcopy(state)
        loaded = read_json(path)
        if not isinstance(loaded, dict):
            raise ValueError(f"research_state must be a JSON object: {path}")
        return _merge_defaults(loaded)


def save_research_state(
    state: dict[str, Any],
    repo_root: str | Path | None = None,
) -> Path:
    """Persist *state* atomically under the research-state lock."""
    root = Path(repo_root) if repo_root is not None else find_repo_root()
    path = research_state_path(root)
    merged = _merge_defaults(state)
    mode = merged.get("submission_mode", SubmissionMode.DRY_RUN.value)
    if mode not in {m.value for m in SubmissionMode}:
        raise ValueError(f"invalid submission_mode: {mode!r}")
    with research_state_lock(root):
        ensure_dir(path.parent)
        atomic_write_json(path, merged)
    return path.resolve()


def update_research_state(
    mutator: Callable[[dict[str, Any]], None],
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    """Load-modify-save under a single lock hold."""
    root = Path(repo_root) if repo_root is not None else find_repo_root()
    path = research_state_path(root)
    with research_state_lock(root):
        if path.exists():
            state = _merge_defaults(read_json(path))
        else:
            state = default_research_state()
        mutator(state)
        mode = state.get("submission_mode", SubmissionMode.DRY_RUN.value)
        if mode not in {m.value for m in SubmissionMode}:
            raise ValueError(f"invalid submission_mode: {mode!r}")
        ensure_dir(path.parent)
        atomic_write_json(path, state)
        return deepcopy(state)


def _merge_defaults(state: dict[str, Any]) -> dict[str, Any]:
    base = default_research_state()
    out = deepcopy(base)
    for key, value in state.items():
        if key in out and isinstance(out[key], dict) and isinstance(value, dict):
            merged = deepcopy(out[key])
            merged.update(value)
            out[key] = merged
        else:
            out[key] = value
    return out
