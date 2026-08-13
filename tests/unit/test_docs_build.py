"""Docs build produces authoritative artefacts from live code."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from qs_everesteer.docs_build import (
    DocsBuildError,
    _is_stub_article,
    article_matches_query,
    build_docs,
    markdown_to_blocks,
    verify_docs_manifest,
)
from qs_everesteer.paths import find_repo_root


def test_build_docs_writes_sha_and_real_openapi(tmp_path: Path, monkeypatch) -> None:
    root = find_repo_root()
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

    commands = {
        c["command"]
        for c in json.loads(result["commands_json"].read_text(encoding="utf-8"))["commands"]
    }
    assert "qseh doctor" in commands
    assert "qseh dashboard diagnose" in commands
    assert "qseh docs build" in commands
    assert "qseh event inspect" in commands
    assert "qseh event arm-submissions" in commands

    curated_ids = {a["id"] for a in manifest["articles"] if a.get("source") == "curated"}
    assert "start-here" in curated_ids
    assert "event-day" in curated_ids
    assert "developer-guide" in curated_ids
    assert "dashboard-operations" in curated_ids
    assert "research-loop" in curated_ids

    by_id = {a["id"]: a for a in manifest["articles"]}
    for article_id in ("cli-reference", "backend-api", "python-api", "configuration"):
        article = by_id[article_id]
        assert len(article["blocks"]) >= 8
        kinds = {b["kind"] for b in article["blocks"]}
        assert "table" in kinds
        assert not _is_stub_article(article)

    cli_text = result["cli_reference"].read_text(encoding="utf-8")
    assert cli_text.startswith("---")
    assert "generatedFromSha:" in cli_text
    assert "qseh event arm-submissions" in cli_text
    assert "Usage:" in cli_text

    backend_text = result["backend_api"].read_text(encoding="utf-8")
    assert "/api/overview" in backend_text
    assert "/api/health" in backend_text
    assert "GET" in backend_text

    python_text = result["python_api"].read_text(encoding="utf-8")
    assert "EveresteerAdapter" in python_text
    assert "SubmissionGuard" in python_text
    assert "`" in python_text

    config_text = result["configuration"].read_text(encoding="utf-8")
    assert "data_path" in config_text
    assert "DRY_RUN" in config_text
    assert "R0" in config_text

    assert article_matches_query(by_id["cli-reference"], "arm-submissions")
    assert article_matches_query(by_id["submission-path"], "arm-submissions")
    assert article_matches_query(by_id["dashboard-operations"], "8766")
    assert article_matches_query(by_id["research-loop"], "ICIR")

    verify_docs_manifest(root)


def test_stub_intro_is_rejected() -> None:
    stub = {
        "id": "configuration",
        "title": "Configuration",
        "description": "Generated configuration reference derived from runner/config schemas.",
        "blocks": [
            {
                "kind": "intro",
                "text": "Generated configuration reference derived from runner/config schemas.",
            }
        ],
    }
    assert _is_stub_article(stub)


def test_markdown_tables_become_blocks() -> None:
    body = """# CLI Reference

Generated from commit `abc`.

## qseh doctor

Check Python.

```text
Usage: qseh doctor [OPTIONS]
```

### Options

| Option | Required | Default | Meaning |
| --- | --- | --- | --- |
| --help | no |  | Show help |
"""
    blocks = markdown_to_blocks(body)
    kinds = [b["kind"] for b in blocks]
    assert "heading" in kinds
    assert "command" in kinds
    assert "table" in kinds
    table = next(b for b in blocks if b["kind"] == "table")
    assert "Option" in table["headers"]
    assert any("--help" in row for row in table["rows"])


def test_verify_docs_manifest_requires_sha(tmp_path: Path, monkeypatch) -> None:
    manifest_dir = tmp_path / "dashboard" / "frontend" / "src" / "generated"
    manifest_dir.mkdir(parents=True)
    (manifest_dir / "docs-manifest.json").write_text(
        json.dumps({"generated_from_sha": None, "generated_at": "x", "articles": []}),
        encoding="utf-8",
    )
    monkeypatch.setattr("qs_everesteer.docs_build.find_repo_root", lambda: tmp_path)
    with pytest.raises(DocsBuildError):
        verify_docs_manifest(tmp_path)


def test_preflight_cmd_uses_crlf() -> None:
    """cmd.exe misparses LF-only batch files (setlocal -> 'tlocal')."""
    data = (find_repo_root() / "scripts" / "preflight.cmd").read_bytes()
    assert not data.startswith(b"\xef\xbb\xbf")
    assert b"\r\n" in data
    assert b"setlocal" in data
    assert b".venv\\Scripts\\python.exe" in data
