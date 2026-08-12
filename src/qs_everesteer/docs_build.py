"""Documentation generator: live Typer/FastAPI + curated MDX flows/runbooks."""

from __future__ import annotations

import inspect
import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from qs_everesteer.paths import ensure_dir, find_repo_root

GENERATOR_VERSION = "2"
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
_COMPONENT_RE = re.compile(
    r"<(PageIntro|FlowDiagram|Callout|Command|MetricDefinition|RelatedPage)"
    r"((?:\s+[^>]*)?)(?:/>|>(.*?)</\1>)",
    re.DOTALL,
)
_HEADING_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
_MOJIBAKE_RE = re.compile(r"[â�]|â€”|â†’|â€œ|â€\x9d")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _git_sha(root: Path) -> str | None:
    try:
        out = subprocess.run(  # noqa: S603
            ["git", "rev-parse", "HEAD"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    sha = (out.stdout or "").strip()
    return sha or None


def _command_params(callback: Any) -> list[dict[str, Any]]:
    """Extract Typer/Click parameters from a command callback."""
    rows: list[dict[str, Any]] = []
    try:
        import typer

        # Prefer Click params attached by Typer.
        click_cmd = getattr(callback, "__click_params__", None)
        if click_cmd is None and hasattr(callback, "params"):
            click_cmd = callback.params
    except Exception:  # noqa: BLE001
        click_cmd = None

    # Typer stores ParameterInfo via annotations / function defaults.
    try:
        sig = inspect.signature(callback)
    except (TypeError, ValueError):
        return rows

    for name, param in sig.parameters.items():
        if name in {"self", "ctx", "context"}:
            continue
        default = param.default
        option_names: list[str] = []
        help_text = ""
        is_option = True
        default_value: Any = None
        if default is inspect.Parameter.empty:
            is_option = False
            default_value = None
        else:
            # typer.Option / Argument infos
            default_value = getattr(default, "default", default)
            if default_value is inspect.Parameter.empty or str(type(default_value)).endswith(
                "OptionInfo'>"
            ):
                # typer.models.OptionInfo
                default_value = getattr(default, "default", None)
            help_text = str(getattr(default, "help", "") or "")
            param_decls = getattr(default, "param_decls", None) or ()
            option_names = [str(d) for d in param_decls if d]
            # ArgumentInfo has no leading dashes typically
            cls_name = type(default).__name__
            if "Argument" in cls_name:
                is_option = False
        if not option_names:
            option_names = [f"--{name.replace('_', '-')}" if is_option else name]
        # Normalise Ellipsis / missing defaults
        if default_value is Ellipsis or repr(default_value) == "Ellipsis":
            default_value = None
            required = True
        else:
            required = default is inspect.Parameter.empty or (
                getattr(default, "default", None) is Ellipsis
            )
        rows.append(
            {
                "name": name,
                "cli": " / ".join(option_names),
                "help": help_text.strip(),
                "default": None if default_value is Ellipsis else default_value,
                "required": bool(required) and default_value is None and not is_option,
                "kind": "option" if is_option else "argument",
            }
        )
    return rows


def _walk_typer(app: Any, prefix: str = "qseh") -> list[dict[str, Any]]:
    """Extract a flat command list from a Typer app (live tree is authoritative)."""
    rows: list[dict[str, Any]] = []

    def visit(typer_app: Any, path: str) -> None:
        for cmd in getattr(typer_app, "registered_commands", []) or []:
            name = cmd.name or getattr(cmd.callback, "__name__", "command")
            help_text = (cmd.help or getattr(cmd.callback, "__doc__", None) or "").strip()
            help_text = help_text.splitlines()[0] if help_text else ""
            callback = cmd.callback
            params = _command_params(callback) if callback else []
            rows.append(
                {
                    "command": f"{path} {name}".strip(),
                    "help": help_text,
                    "params": params,
                }
            )
        for group in getattr(typer_app, "registered_groups", []) or []:
            gname = group.name or "group"
            gapp = group.typer_instance
            ghelp = (getattr(gapp, "info", None) and getattr(gapp.info, "help", None)) or ""
            rows.append(
                {
                    "command": f"{path} {gname}".strip(),
                    "help": str(ghelp).strip() or "(group)",
                    "params": [],
                }
            )
            visit(gapp, f"{path} {gname}".strip())

    try:
        visit(app, prefix)
    except Exception:  # noqa: BLE001
        return []

    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for row in rows:
        key = row["command"]
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


def research_console_openapi() -> dict[str, Any]:
    """OpenAPI schema from the real FastAPI Research Console application."""
    import sys

    root = find_repo_root()
    root_s = str(root)
    if root_s not in sys.path:
        sys.path.insert(0, root_s)
    from dashboard.backend.app.main import create_app

    application = create_app(root)
    schema = application.openapi()
    if not isinstance(schema, dict):
        raise TypeError("create_app().openapi() did not return a dict")
    return schema


def openapi_stub() -> dict[str, Any]:
    """Backward-compatible alias — returns the real Research Console OpenAPI."""
    return research_console_openapi()


def _python_api_reference() -> str:
    """Document intended public project APIs (not every private helper)."""
    targets: list[tuple[str, str]] = [
        ("qs_everesteer.hardware.probe", "probe_hardware"),
        ("qs_everesteer.state.research", "load_research_state"),
        ("qs_everesteer.state.research", "update_research_state"),
        ("qs_everesteer.event.adapter", "EveresteerAdapter"),
        ("qs_everesteer.experiments.runner", "ExperimentRunner"),
        ("qs_everesteer.experiments.racing", "RacingScheduler"),
        ("qs_everesteer.docs_build", "build_docs"),
        ("qs_everesteer.dashboard.process", "DashboardProcessManager"),
        ("qs_everesteer.ops_status", "write_ops_status"),
        ("qs_everesteer.gitmeta", "git_head_sha"),
    ]
    lines = [
        "# Python API reference (generated)",
        "",
        f"Generated at `{_utc_now()}`.",
        "",
        "Public entry points intended for event-day tooling. Private helpers are omitted.",
        "",
    ]
    for module_name, attr in targets:
        try:
            mod = __import__(module_name, fromlist=[attr])
            obj = getattr(mod, attr)
        except Exception as exc:  # noqa: BLE001
            lines.append(f"## `{module_name}.{attr}`")
            lines.append("")
            lines.append(f"_Unavailable: {type(exc).__name__}: {exc}_")
            lines.append("")
            continue
        doc = inspect.getdoc(obj) or ""
        first = doc.splitlines()[0] if doc else ""
        try:
            if inspect.isclass(obj):
                sig = f"{attr}(...)"
                init = getattr(obj, "__init__", None)
                if init:
                    sig = f"{attr}{inspect.signature(init)}"
            elif callable(obj):
                sig = f"{attr}{inspect.signature(obj)}"
            else:
                sig = attr
        except (TypeError, ValueError):
            sig = attr
        lines.append(f"## `{module_name}.{attr}`")
        lines.append("")
        lines.append(f"`{sig}`")
        lines.append("")
        if first:
            lines.append(first)
            lines.append("")
    return "\n".join(lines) + "\n"


def _config_reference() -> str:
    """Document supported experiment YAML / known config fields."""
    return "\n".join(
        [
            "# Configuration reference (generated)",
            "",
            f"Generated at `{_utc_now()}`.",
            "",
            "Experiment YAML fields consumed by `ExperimentRunner` / `qseh` research commands:",
            "",
            "| Field | Default / notes |",
            "|---|---|",
            "| `model` | string model name (e.g. `ridge`, `reference_lgbm`) or `{name, params}` |",
            "| `params` | model hyperparameters (dict) |",
            "| `data_path` | path to training parquet |",
            "| `profile` | temporal profile `R0`–`R3` |",
            "| `target` | default `target_everest_20` |",
            "| `exped_col` | default `exped` |",
            "| `features` | optional list; otherwise `feature_*` columns |",
            "| `run_id` | optional; auto-generated when omitted |",
            "| `data_hash` | optional training data fingerprint |",
            "",
            "Submission modes: `DISABLED`, `DRY_RUN`, `ARMED` (persisted in research state).",
            "",
            "Hardware probe is live host detection — not YAML-configured.",
            "",
        ]
    )


def _cli_markdown(commands: list[dict[str, Any]], *, generated_at: str, sha: str | None) -> str:
    lines = [
        "# qseh CLI reference (generated)",
        "",
        f"Generated at `{generated_at}`.",
        f"generatedFromSha: `{sha or 'unavailable'}`.",
        "",
        "Authoritative source: live Typer command tree (`qseh docs build`).",
        "",
        "| Command | Help |",
        "|---|---|",
    ]
    for row in commands:
        help_text = (row.get("help") or "").replace("|", "\\|")
        lines.append(f"| `{row['command']}` | {help_text} |")
    lines.append("")
    lines.append("## Options and arguments")
    lines.append("")
    for row in commands:
        params = row.get("params") or []
        if not params:
            continue
        lines.append(f"### `{row['command']}`")
        lines.append("")
        lines.append("| Name | Kind | Default | Help |")
        lines.append("|---|---|---|---|")
        for p in params:
            default = p.get("default")
            default_s = "" if default is None else str(default).replace("|", "\\|")
            help_text = (p.get("help") or "").replace("|", "\\|")
            lines.append(
                f"| `{p.get('cli') or p.get('name')}` | {p.get('kind')} | `{default_s}` | {help_text} |"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    match = _FRONTMATTER_RE.match(text.strip() + ("\n" if not text.endswith("\n") else ""))
    if not match:
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


def _assert_utf8_clean(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if _MOJIBAKE_RE.search(text):
        raise ValueError(f"mojibake detected in generated docs: {path}")


def build_docs(repo_root: str | Path | None = None, *, app: Any | None = None) -> dict[str, Path]:
    """
    Write docs/generated/ artefacts and dashboard frontend docs-manifest.json.

    Derives CLI/API/config reference from live code. Curated MDX under
    docs/flows and docs/runbooks is preserved and indexed, never overwritten.
    """
    root = Path(repo_root) if repo_root is not None else find_repo_root()
    generated = ensure_dir(root / "docs" / "generated")
    frontend_gen = ensure_dir(root / "dashboard" / "frontend" / "src" / "generated")
    generated_at = _utc_now()
    sha = _git_sha(root)

    if app is None:
        from qs_everesteer.cli import app as cli_app

        app = cli_app

    commands = _walk_typer(app)
    if not commands:
        raise RuntimeError("Typer command walk returned empty — refusing to write stale CLI docs")

    cli_md = generated / "cli-reference.md"
    cli_md.write_text(
        _cli_markdown(commands, generated_at=generated_at, sha=sha),
        encoding="utf-8",
    )

    openapi = research_console_openapi()
    openapi_path = generated / "openapi.json"
    openapi_path.write_text(json.dumps(openapi, indent=2) + "\n", encoding="utf-8")
    # Remove legacy stub filename if present so searches do not find stale copy.
    legacy_stub = generated / "openapi-stub.json"
    if legacy_stub.is_file():
        legacy_stub.unlink()

    commands_json = generated / "cli-commands.json"
    commands_json.write_text(
        json.dumps(
            {
                "generated_at": generated_at,
                "generated_from_sha": sha,
                "generator_version": GENERATOR_VERSION,
                "commands": commands,
            },
            indent=2,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    python_api_path = generated / "python-api.md"
    python_api_path.write_text(_python_api_reference(), encoding="utf-8")

    config_path = generated / "configuration.md"
    config_path.write_text(_config_reference(), encoding="utf-8")

    curated = collect_curated_articles(root)
    curated_path = generated / "curated-articles.json"
    curated_payload = {
        "generated_at": generated_at,
        "generated_from_sha": sha,
        "generator_version": GENERATOR_VERSION,
        "sections": curated_sections(curated),
        "articles": [{k: v for k, v in article.items() if k != "path"} for article in curated],
    }
    curated_path.write_text(json.dumps(curated_payload, indent=2) + "\n", encoding="utf-8")

    def _gen_article(
        *,
        article_id: str,
        title: str,
        path: str,
        order: int,
        description: str,
        intro: str,
        tags: list[str],
    ) -> dict[str, Any]:
        return {
            "id": article_id,
            "title": title,
            "path": path,
            "tags": tags,
            "source": "generated",
            "section": "generated",
            "order": order,
            "description": description,
            "blocks": [{"kind": "intro", "text": intro}],
        }

    path_count = len((openapi.get("paths") or {}))
    manifest_articles: list[dict[str, Any]] = [
        _gen_article(
            article_id="cli-reference",
            title="CLI Reference",
            path="docs/generated/cli-reference.md",
            order=1000,
            description="Generated Typer command reference from the live CLI",
            intro="Generated CLI reference from the live Typer command tree.",
            tags=["cli", "generated"],
        ),
        _gen_article(
            article_id="backend-api",
            title="Backend API",
            path="docs/generated/openapi.json",
            order=1010,
            description=f"Research Console OpenAPI ({path_count} paths) from create_app().openapi()",
            intro=(
                f"Generated from the live FastAPI Research Console application "
                f"({path_count} paths). Swagger UI is at /api/dev/docs."
            ),
            tags=["api", "generated", "openapi"],
        ),
        _gen_article(
            article_id="python-api",
            title="Python API",
            path="docs/generated/python-api.md",
            order=1020,
            description="Public project Python entry points",
            intro="Generated public Python API reference (selected entry points).",
            tags=["python", "generated"],
        ),
        _gen_article(
            article_id="configuration",
            title="Configuration",
            path="docs/generated/configuration.md",
            order=1030,
            description="Experiment YAML and supported configuration fields",
            intro="Generated configuration reference derived from runner/config schemas.",
            tags=["config", "generated"],
        ),
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

    sections = curated_sections(curated) + [{"id": "generated", "label": "Generated reference"}]

    manifest = {
        "generated_at": generated_at,
        "generated_from_sha": sha,
        "generator_version": GENERATOR_VERSION,
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
                f"- generatedFromSha: `{sha or 'unavailable'}`",
                f"- generatedAt: `{generated_at}`",
                f"- generatorVersion: `{GENERATOR_VERSION}`",
                f"- CLI reference: `{cli_md.name}`",
                f"- Commands JSON: `{commands_json.name}`",
                f"- Backend OpenAPI: `{openapi_path.name}` ({path_count} paths)",
                f"- Python API: `{python_api_path.name}`",
                f"- Configuration: `{config_path.name}`",
                f"- Curated articles: `{curated_path.name}` ({len(curated)} MDX)",
                f"- Frontend manifest: `{manifest_path.relative_to(root).as_posix()}`",
                "",
            ]
        ),
        encoding="utf-8",
    )

    for path in (
        cli_md,
        commands_json,
        openapi_path,
        python_api_path,
        config_path,
        curated_path,
        manifest_path,
        index_path,
    ):
        _assert_utf8_clean(path)

    return {
        "cli_reference": cli_md,
        "commands_json": commands_json,
        "openapi": openapi_path,
        "python_api": python_api_path,
        "configuration": config_path,
        "curated_articles": curated_path,
        "docs_manifest": manifest_path,
        "index": index_path,
    }
