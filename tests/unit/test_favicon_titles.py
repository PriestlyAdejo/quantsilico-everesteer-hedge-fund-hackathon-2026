"""Favicon / document title static checks."""

from __future__ import annotations

from pathlib import Path

from qs_everesteer.paths import find_repo_root


def test_index_html_brand_and_favicon() -> None:
    root = find_repo_root()
    index = (root / "dashboard" / "frontend" / "index.html").read_text(encoding="utf-8")
    assert "QuantSilico // Everesteer 2026" in index
    assert 'href="/favicon.svg"' in index
    assert "figma:title" not in index
    favicon = root / "dashboard" / "frontend" / "public" / "favicon.svg"
    assert favicon.is_file()
    svg = favicon.read_text(encoding="utf-8")
    assert "#090D11" in svg
    assert "#FFB000" in svg


def test_document_title_component_exists() -> None:
    root = find_repo_root()
    path = root / "dashboard" / "frontend" / "src" / "components" / "DocumentTitle.tsx"
    text = path.read_text(encoding="utf-8")
    assert "PAGE_META" in text
    assert "document.title" in text
