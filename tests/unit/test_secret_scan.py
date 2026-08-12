"""Scan tracked-ish text files for accidental secret material."""

from __future__ import annotations

import re
from pathlib import Path

from qs_everesteer.paths import find_repo_root

_SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".cursor",
    ".figma",
    "pnpm-store",
}

_SKIP_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".ico",
    ".pdf",
    ".parquet",
    ".pkl",
    ".pickle",
    ".bin",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".zip",
    ".gz",
    ".7z",
    ".lock",
}

_ALLOWLIST_NAMES = {
    ".env.example",
    "test_secret_scan.py",
}

_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("ek_live_", re.compile(r"ek_live_[A-Za-z0-9_\-]{8,}")),
    ("BEGIN PRIVATE KEY", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    (
        "generic API key assignment",
        re.compile(
            r"(?i)(?:api[_-]?key|eiq_api_key|everest_api_key)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]"
        ),
    ),
    (
        "AWS-style access key",
        re.compile(r"AKIA[0-9A-Z]{16}"),
    ),
]


def _iter_text_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in _SKIP_DIR_NAMES for part in path.parts):
            continue
        if path.name in _ALLOWLIST_NAMES:
            continue
        if path.suffix.lower() in _SKIP_SUFFIXES:
            continue
        # Skip large blobs / generated lockfiles by size.
        try:
            if path.stat().st_size > 1_500_000:
                continue
        except OSError:
            continue
        files.append(path)
    return files


def test_repo_has_no_obvious_secrets() -> None:
    root = find_repo_root()
    hits: list[str] = []
    for path in _iter_text_files(root):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for label, pattern in _PATTERNS:
            if pattern.search(text):
                rel = path.relative_to(root).as_posix()
                hits.append(f"{rel}: {label}")
    assert hits == [], "potential secrets found:\n" + "\n".join(hits)


def test_env_example_is_allowlisted_placeholder() -> None:
    root = find_repo_root()
    example = root / ".env.example"
    assert example.is_file()
    text = example.read_text(encoding="utf-8")
    # Placeholders / empty assignments are fine; live key material is not.
    assert "ek_live_" not in text
    assert "BEGIN PRIVATE KEY" not in text
