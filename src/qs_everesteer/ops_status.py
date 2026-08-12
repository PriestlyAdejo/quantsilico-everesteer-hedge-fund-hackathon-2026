"""Persist operational status for project-owned CLI commands only.

Raw external pytest invocations are never inferred into last_tests.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from qs_everesteer.fsutil import atomic_write_json, read_json
from qs_everesteer.paths import ensure_dir, find_repo_root, state_dir

StatusLiteral = Literal["passing", "failing", "unknown"]


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def status_path(name: str, repo_root: str | Path | None = None) -> Path:
    root = Path(repo_root) if repo_root is not None else find_repo_root()
    return state_dir(root) / name


def write_ops_status(
    filename: str,
    *,
    status: StatusLiteral,
    detail: str,
    repo_root: str | Path | None = None,
    extra: dict[str, Any] | None = None,
) -> Path:
    """Write a small JSON status file under runs/state/."""
    root = Path(repo_root) if repo_root is not None else find_repo_root()
    path = status_path(filename, root)
    payload: dict[str, Any] = {
        "status": status,
        "at": _utc_now(),
        "detail": detail,
    }
    if extra:
        payload.update(extra)
    ensure_dir(path.parent)
    atomic_write_json(path, payload)
    return path


def read_ops_status(
    filename: str,
    repo_root: str | Path | None = None,
) -> dict[str, Any] | None:
    root = Path(repo_root) if repo_root is not None else find_repo_root()
    path = status_path(filename, root)
    if not path.is_file():
        return None
    try:
        data = read_json(path)
    except (OSError, ValueError, TypeError):
        return None
    return data if isinstance(data, dict) else None


def as_check_result(payload: dict[str, Any] | None) -> dict[str, Any]:
    """Normalise a persisted payload into RepoCheckResult-shaped fields."""
    if not payload:
        return {"status": "unknown", "at": None, "detail": "No persisted result"}
    status = str(payload.get("status") or "unknown")
    if status not in {"passing", "failing", "unknown"}:
        status = "unknown"
    return {
        "status": status,
        "at": payload.get("at"),
        "detail": str(payload.get("detail") or ""),
    }
