"""Docs build produces authoritative artefacts from live code."""

from __future__ import annotations

import json
from pathlib import Path

from qs_everesteer.docs_build import build_docs
from qs_everesteer.paths import find_repo_root


def test_build_docs_writes_sha_and_real_openapi(tmp_path: Path, monkeypatch) -> None:
    root = find_repo_root()
    # Build into a temp overlay by pointing generated dirs via chdir? build_docs uses repo_root.
    # Use the real repo root but assert key invariants; artefacts are meant to be regenerated.
    result = build_docs(root)
    manifest = json.loads(result["docs_manifest"].read_text(encoding="utf-8"))
    assert manifest.get("generated_from_sha")
    assert manifest.get("generated_at")
    assert "CLI Reference" in {a["title"] for a in manifest["articles"]}
    assert "Backend API" in {a["title"] for a in manifest["articles"]}
    assert not any("stub" in str(a.get("title", "")).lower() for a in manifest["articles"])
    assert not any("openapi-stub" in str(a.get("id", "")) for a in manifest["articles"])

    openapi = json.loads(result["openapi"].read_text(encoding="utf-8"))
    paths = openapi.get("paths") or {}
    assert "/api/health" in paths
    assert len(paths) > 5
    assert "/api/overview" in paths or any("overview" in p for p in paths)

    commands = {c["command"] for c in json.loads(result["commands_json"].read_text(encoding="utf-8"))["commands"]}
    assert "qseh doctor" in commands
    assert "qseh dashboard diagnose" in commands
    assert "qseh docs build" in commands
    assert "qseh event inspect" in commands

    curated_ids = {a["id"] for a in manifest["articles"] if a.get("source") == "curated"}
    assert "dashboard" in curated_ids or "start-here" in curated_ids
