from __future__ import annotations

import json
from pathlib import Path

from qs_everesteer.fsutil import atomic_write_bytes, atomic_write_json, read_json
from qs_everesteer.paths import ensure_dir, find_repo_root


def test_find_repo_root_discovers_pyproject():
    root = find_repo_root(Path(__file__))
    assert (root / "pyproject.toml").is_file()


def test_atomic_write_json_roundtrip(tmp_path: Path):
    path = tmp_path / "nested" / "state.json"
    payload = {"b": 2, "a": 1, "nested": {"ok": True}}
    atomic_write_json(path, payload)
    assert path.is_file()
    loaded = read_json(path)
    assert loaded == payload
    # No leftover temp files in the destination directory.
    leftovers = list(path.parent.glob("*.tmp"))
    assert leftovers == []


def test_atomic_write_bytes_replaces_existing(tmp_path: Path):
    path = tmp_path / "blob.bin"
    atomic_write_bytes(path, b"first")
    atomic_write_bytes(path, b"second")
    assert path.read_bytes() == b"second"


def test_atomic_write_json_creates_parents(tmp_path: Path):
    path = tmp_path / "a" / "b" / "c.json"
    atomic_write_json(path, {"x": 1})
    assert json.loads(path.read_text(encoding="utf-8"))["x"] == 1
    ensure_dir(tmp_path / "a" / "b")  # idempotent
