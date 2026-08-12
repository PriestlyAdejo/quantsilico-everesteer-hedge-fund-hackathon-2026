"""Read-only git helpers for repository metadata (allowlisted args only)."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def _run_git(root: Path, args: list[str], timeout: float = 8.0) -> str | None:
    try:
        out = subprocess.run(  # noqa: S603
            ["git", *args],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    return (out.stdout or "").strip()


def git_head_sha(root: Path) -> str | None:
    text = _run_git(root, ["rev-parse", "HEAD"])
    return text or None


def git_branch(root: Path) -> str | None:
    text = _run_git(root, ["rev-parse", "--abbrev-ref", "HEAD"])
    return text or None


def git_is_dirty(root: Path) -> bool:
    text = _run_git(root, ["status", "--porcelain"])
    if text is None:
        return False
    return bool(text.strip())


def git_latest_commits(root: Path, limit: int = 8) -> list[dict[str, Any]]:
    fmt = "%H%x09%s%x09%an%x09%cI"
    text = _run_git(root, ["log", f"-{limit}", f"--pretty=format:{fmt}"])
    if not text:
        return []
    commits: list[dict[str, Any]] = []
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        sha, msg, author, ts = parts[0], parts[1], parts[2], parts[3]
        commits.append(
            {
                "sha": sha[:12] if len(sha) > 12 else sha,
                "msg": msg,
                "author": author,
                "ts": ts,
            }
        )
    return commits
