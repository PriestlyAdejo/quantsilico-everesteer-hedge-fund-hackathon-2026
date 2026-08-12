"""Documentation generator: Typer CLI stubs + curated MDX flows/runbooks."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from qs_everesteer.paths import ensure_dir, find_repo_root

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
_COMPONENT_RE = re.compile(
    r"<(PageIntro|FlowDiagram|Callout|Command|MetricDefinition|RelatedPage)"
    r"((?:\s+[^>]*)?)(?:/>|>(.*?)</\1>)",
    re.DOTALL,
)
_HEADING_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _walk_typer(app: Any, prefix: str = "qseh") -> list[dict[str, str]]:
    """Extract a flat command list from a Typer app (best-effort)."""
    rows: list[dict[str, str]] = []

    def visit(typer_app: Any, path: str) -> None:
        for cmd in getattr(typer_app, "registered_commands", []) or []:
            name = cmd.name or getattr(cmd.callback, "__name__", "command")
            help_text = (cmd.help or getattr(cmd.callback, "__doc__", None) or "").strip()
            help_text = help_text.splitlines()[0] if help_text else ""
            rows.append({"command": f"{path} {name}".strip(), "help": help_text})
        for group in getattr(typer_app, "registered_groups", []) or []:
            gname = group.name or "group"
            gapp = group.typer_instance
            ghelp = (getattr(gapp, "info", None) and getattr(gapp.info, "help", None)) or ""
            rows.append({"command": f"{path} {gname}".strip(), "help": str(ghelp).strip() or "(group)"})
            visit(gapp, f"{path} {gname}".strip())

    try:
        visit(app, prefix)
    except Exception:  # noqa: BLE001
        return []

    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for row in rows:
        key = row["command"]
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


def openapi_stub() -> dict[str, Any]:
    """Minimal OpenAPI-shaped stub mirroring the local dashboard health surface."""
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "QuantSilico Everesteer 2026 Research Console",
            "version": "0.1.0",
            "description": "Generated stub — not a live platform contract.",
        },
        "paths": {
            "/api/health": {
                "get": {
                    "summary": "Health",
                    "operationId": "health",
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string"},
                                            "service": {"type": "string"},
                                            "schema_version": {"type": "integer"},
                                        },
                                    }
                                }
                            },
                        }
                    },
                }
            }
        },
    }


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    match = _FRONTMATTER_RE.match(text.strip() + ("\n" if not text.endswith("\n") else ""))
    if not match:
        # Allow files that already strip trailing newline inconsistently.
        match = _FRONTMATTER_RE.match(text.strip())
    if not match:
        return {}, text
    meta: dict[str, Any] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta, match.group(2)


def _parse_flow_nodes(attr_blob: str) -> list[dict[str, str]]:
    nodes: list[dict[str, str]] = []
    for node_match in re.finditer(
        r"\{\s*id:\s*[\"']([^\"']+)[\"']\s*,\s*label:\s*[\"']([^\"']+)[\"']\s*\}",
        attr_blob,
    ):
        nodes.append({"id": node_match.group(1), "label": node_match.group(2)})
    return nodes


def _component_attrs(attr_text: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for match in re.finditer(r'(\w+)="([^"]*)"', attr_text or ""):
        attrs[match.group(1)] = match.group(2)
    return attrs


def mdx_to_blocks(body: str) -> list[dict[str, Any]]:
    """Map curated MDX-ish components into DocumentationData block dicts."""
    blocks: list[dict[str, Any]] = []
    cursor = 0
    for match in _COMPONENT_RE.finditer(body):
        prefix = body[cursor : match.start()]
        for heading in _HEADING_RE.finditer(prefix):
            blocks.append({"kind": "heading", "text": heading.group(1).strip()})
        leftover = _HEADING_RE.sub("", prefix).strip()
        if leftover:
            # Keep plain prose between components as paragraphs when present.
            for para in re.split(r"\n\s*\n", leftover):
                cleaned = para.strip()
                if cleaned:
                    blocks.append({"kind": "paragraph", "text": cleaned})

        name = match.group(1)
        attrs_raw = match.group(2) or ""
        inner = (match.group(3) or "").strip()
        attrs = _component_attrs(attrs_raw)

        if name == "PageIntro":
            blocks.append({"kind": "intro", "text": " ".join(inner.split())})
        elif name == "FlowDiagram":
            blocks.append({"kind": "flow", "nodes": _parse_flow_nodes(attrs_raw)})
        elif name == "Callout":
            tone = attrs.get("tone", "info")
            if tone not in {"info", "warning", "danger"}:
                tone = "info"
            blocks.append({"kind": "callout", "tone": tone, "text": " ".join(inner.split())})
        elif name == "Command":
            blocks.append({"kind": "command", "command": " ".join(inner.split())})
        elif name == "MetricDefinition":
            blocks.append(
                {
                    "kind": "metric",
                    "name": attrs.get("name", "metric"),
                    "text": " ".join(inner.split()),
                }
            )
        elif name == "RelatedPage":
            blocks.append(
                {
                    "kind": "related",
                    "href": attrs.get("href", "/"),
                    "label": " ".join(inner.split()) or attrs.get("href", "/"),
                }
            )
        cursor = match.end()

    suffix = body[cursor:]
    for heading in _HEADING_RE.finditer(suffix):
        blocks.append({"kind": "heading", "text": heading.group(1).strip()})
    return blocks


def parse_curated_mdx(path: Path) -> dict[str, Any] | None:
    """Parse one curated MDX file into a DocArticle-shaped dict."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    meta, body = _parse_frontmatter(text)
    if not meta.get("title"):
        return None
    section = str(meta.get("section") or path.parent.name)
    try:
        order = int(meta.get("order") or 100)
    except (TypeError, ValueError):
        order = 100
    article_id = path.stem
    return {
        "id": article_id,
        "title": str(meta["title"]),
        "description": str(meta.get("description") or ""),
        "section": section,
        "order": order,
        "source": "curated",
        "blocks": mdx_to_blocks(body),
        "path": path.as_posix(),
    }


def collect_curated_articles(repo_root: Path) -> list[dict[str, Any]]:
    """Load docs/flows/*.mdx and docs/runbooks/*.mdx."""
    articles: list[dict[str, Any]] = []
    for folder in ("flows", "runbooks"):
        root = repo_root / "docs" / folder
        if not root.is_dir():
            continue
        for path in sorted(root.glob("*.mdx")):
            article = parse_curated_mdx(path)
            if article:
                articles.append(article)
    articles.sort(key=lambda item: (item.get("section") or "", int(item.get("order") or 0), item["id"]))
    return articles


def curated_sections(articles: list[dict[str, Any]]) -> list[dict[str, str]]:
    labels = {
        "flows": "Flows",
        "runbooks": "Runbooks",
        "generated": "Generated reference",
        "start": "Start Here",
    }
    seen: list[str] = []
    for article in articles:
        section = str(article.get("section") or "flows")
        if section not in seen:
            seen.append(section)
    return [{"id": section, "label": labels.get(section, section.title())} for section in seen]


def build_docs(repo_root: str | Path | None = None, *, app: Any | None = None) -> dict[str, Path]:
    """
    Write docs/generated/ artefacts and dashboard frontend docs-manifest.json.

    Creates directories as needed. Curated MDX under docs/flows and docs/runbooks
    is parsed into DocumentationData-shaped articles for the console.
    """
    root = Path(repo_root) if repo_root is not None else find_repo_root()
    generated = ensure_dir(root / "docs" / "generated")
    frontend_gen = ensure_dir(root / "dashboard" / "frontend" / "src" / "generated")

    if app is None:
        from qs_everesteer.cli import app as cli_app

        app = cli_app

    commands = _walk_typer(app)
    if not commands:
        commands = [
            {"command": "qseh doctor", "help": "Environment readiness checks"},
            {"command": "qseh rehearsal", "help": "Synthetic end-to-end rehearsal"},
            {"command": "qseh sdk info", "help": "SDK version / fingerprint"},
            {"command": "qseh event inspect", "help": "Event capability inspect"},
            {"command": "qseh data audit", "help": "Dataset integrity audit"},
            {"command": "qseh docs build", "help": "Generate docs stubs"},
        ]

    cli_md_lines = [
        "# qseh CLI reference (generated)",
        "",
        f"Generated at `{_utc_now()}`.",
        "",
        "| Command | Help |",
        "|---|---|",
    ]
    for row in commands:
        help_text = (row.get("help") or "").replace("|", "\\|")
        cli_md_lines.append(f"| `{row['command']}` | {help_text} |")
    cli_md_lines.append("")

    cli_md = generated / "cli-reference.md"
    cli_md.write_text("\n".join(cli_md_lines), encoding="utf-8")

    openapi_path = generated / "openapi-stub.json"
    openapi_path.write_text(json.dumps(openapi_stub(), indent=2) + "\n", encoding="utf-8")

    commands_json = generated / "cli-commands.json"
    commands_json.write_text(
        json.dumps({"generated_at": _utc_now(), "commands": commands}, indent=2) + "\n",
        encoding="utf-8",
    )

    curated = collect_curated_articles(root)
    curated_path = generated / "curated-articles.json"
    curated_payload = {
        "generated_at": _utc_now(),
        "sections": curated_sections(curated),
        "articles": [
            {k: v for k, v in article.items() if k != "path"} for article in curated
        ],
    }
    curated_path.write_text(json.dumps(curated_payload, indent=2) + "\n", encoding="utf-8")

    manifest_articles: list[dict[str, Any]] = [
        {
            "id": "cli-reference",
            "title": "CLI reference",
            "path": "docs/generated/cli-reference.md",
            "tags": ["cli", "generated"],
            "source": "generated",
            "section": "generated",
            "order": 1000,
            "description": "Generated Typer command reference",
            "blocks": [
                {
                    "kind": "intro",
                    "text": "Generated CLI reference from the Typer command tree.",
                }
            ],
        },
        {
            "id": "openapi-stub",
            "title": "Dashboard OpenAPI stub",
            "path": "docs/generated/openapi-stub.json",
            "tags": ["api", "generated"],
            "source": "generated",
            "section": "generated",
            "order": 1010,
            "description": "Minimal OpenAPI stub for local dashboard health",
            "blocks": [
                {
                    "kind": "intro",
                    "text": "Generated OpenAPI stub — not a live platform contract.",
                }
            ],
        },
    ]
    for article in curated:
        manifest_articles.append(
            {
                "id": article["id"],
                "title": article["title"],
                "path": article.get("path")
                or f"docs/{article['section']}/{article['id']}.mdx",
                "tags": ["curated", article["section"]],
                "source": "curated",
                "section": article["section"],
                "order": article["order"],
                "description": article["description"],
                "blocks": article["blocks"],
            }
        )

    sections = curated_sections(curated) + (
        [{"id": "generated", "label": "Generated reference"}] if curated else []
    )
    if not curated:
        sections = [{"id": "generated", "label": "Generated reference"}]

    manifest = {
        "generated_at": _utc_now(),
        "schema_version": 1,
        "title": "QuantSilico Everesteer Docs Manifest",
        "sections": sections,
        "articles": manifest_articles,
        "commands": [c["command"] for c in commands],
    }
    manifest_path = frontend_gen / "docs-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    index_path = generated / "README.md"
    index_path.write_text(
        "\n".join(
            [
                "# Generated docs",
                "",
                "Produced by `qseh docs build` / `qs_everesteer.docs_build.build_docs`.",
                "",
                f"- CLI reference: `{cli_md.name}`",
                f"- Commands JSON: `{commands_json.name}`",
                f"- OpenAPI stub: `{openapi_path.name}`",
                f"- Curated articles: `{curated_path.name}` ({len(curated)} MDX)",
                f"- Frontend manifest: `{manifest_path.relative_to(root).as_posix()}`",
                "",
            ]
        ),
        encoding="utf-8",
    )

    return {
        "cli_reference": cli_md,
        "commands_json": commands_json,
        "openapi_stub": openapi_path,
        "curated_articles": curated_path,
        "docs_manifest": manifest_path,
        "index": index_path,
    }
