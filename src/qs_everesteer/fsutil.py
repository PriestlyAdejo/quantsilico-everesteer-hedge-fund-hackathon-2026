"""Atomic writes, JSON IO, and cross-platform research-state locking."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from filelock import FileLock

from qs_everesteer.paths import ensure_dir, find_repo_root, state_dir


def atomic_write_bytes(path: str | Path, data: bytes) -> Path:
    """Write *data* via a same-directory temp file then ``os.replace``."""
    dest = Path(path)
    ensure_dir(dest.parent)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{dest.name}.", suffix=".tmp", dir=dest.parent)
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, dest)
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    return dest.resolve()


def atomic_write_json(
    path: str | Path,
    obj: Any,
    *,
    indent: int | None = 2,
    sort_keys: bool = True,
) -> Path:
    """Serialize *obj* as UTF-8 JSON and write atomically."""
    text = json.dumps(obj, indent=indent, sort_keys=sort_keys, default=str)
    if indent is not None:
        text += "\n"
    return atomic_write_bytes(path, text.encode("utf-8"))


def read_json(path: str | Path) -> Any:
    """Load a JSON file."""
    with Path(path).open("r", encoding="utf-8") as fh:
        return json.load(fh)


def research_lock_path(repo_root: str | Path | None = None) -> Path:
    root = Path(repo_root) if repo_root is not None else find_repo_root()
    return state_dir(root) / ".lock"


@contextmanager
def research_state_lock(
    repo_root: str | Path | None = None,
    *,
    timeout: float = 30.0,
) -> Iterator[Path]:
    """Exclusive lock on ``runs/state/.lock`` (Windows-safe via filelock)."""
    root = Path(repo_root) if repo_root is not None else find_repo_root()
    ensure_dir(state_dir(root))
    lock_path = research_lock_path(root)
    lock = FileLock(str(lock_path), timeout=timeout)
    with lock:
        yield lock_path
