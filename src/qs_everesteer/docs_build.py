"""Documentation generator: live Typer/FastAPI/Python/config + curated MDX."""

from __future__ import annotations

import dataclasses
import inspect
import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from qs_everesteer.paths import ensure_dir, find_repo_root

GENERATOR_VERSION = "3"
MIN_CLI_COMMANDS = 20
MIN_API_PATHS = 10
MIN_CONFIG_FIELD_ROWS = 8
MIN_PYTHON_SIGNATURES = 8
MIN_GENERATED_BLOCKS = 8

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
_COMPONENT_RE = re.compile(
    r"<(PageIntro|FlowDiagram|Callout|Command|MetricDefinition|RelatedPage)"
    r"((?:\s+[^>]*)?)(?:/>|>(.*?)</\1>)",
    re.DOTALL,
)
_HEADING_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
_MOJIBAKE_RE = re.compile(r"[â�]|â€”|â†’|â€œ|â€\x9d")
_TABLE_SEP_RE = re.compile(r"^\|[\s:|-]+\|\s*$")
_MD_HEADING_RE = re.compile(r"^(#{2,3})\s+(.+)$")

PYTHON_API_TARGETS: list[tuple[str, str]] = [
    ("qs_everesteer.event.adapter", "EveresteerAdapter"),
    ("qs_everesteer.event.adapter", "sdk_version"),
    ("qs_everesteer.data.audit", "audit_dataset"),
    ("qs_everesteer.data.fingerprint", "fingerprint_dataset"),
    ("qs_everesteer.validation.scoring", "official_scorers"),
    ("qs_everesteer.validation.temporal", "temporal_cv"),
    ("qs_everesteer.validation.temporal", "TemporalSplitter"),
    ("qs_everesteer.experiments.runner", "ExperimentRunner"),
    ("qs_everesteer.experiments.racing", "RacingScheduler"),
    ("qs_everesteer.selection.frontier", "pareto_frontier"),
    ("qs_everesteer.ensemble.blend", "rank_average"),
    ("qs_everesteer.ensemble.blend", "weighted"),
    ("qs_everesteer.ensemble.blend", "greedy_forward"),
    ("qs_everesteer.ensemble.blend", "diversity_aware"),
    ("qs_everesteer.submission.guard", "SubmissionGuard"),
    ("qs_everesteer.submission.mode", "get_mode"),
    ("qs_everesteer.submission.mode", "arm_submissions"),
    ("qs_everesteer.live.rounds", "RoundController"),
    ("qs_everesteer.jobs.queue", "enqueue"),
    ("qs_everesteer.jobs.worker", "run_job_sync"),
    ("qs_everesteer.autopilot.orchestrator", "CompetitionAutopilot"),
    ("qs_everesteer.dashboard.process", "DashboardProcessManager"),
]


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _git_sha(root: Path) -> str | None:
    try:
        out = subprocess.run(
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


def _yaml_frontmatter(
    *,
    title: str,
    description: str,
    sha: str | None,
    generated_at: str,
) -> str:
    return "\n".join(
        [
            "---",
            f"title: {title}",
            f"description: {description}",
            "source: generated",
            f"generatedFromSha: {sha or 'unavailable'}",
            f"generatedAt: {generated_at}",
            "---",
            "",
        ]
    )


def _esc_cell(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _md_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        padded = list(row) + [""] * (len(headers) - len(row))
        lines.append("| " + " | ".join(_esc_cell(c) for c in padded[: len(headers)]) + " |")
    return lines


# ─── CLI from live Typer / Click tree ───────────────────────────


def _click_params(command: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        import click
    except ImportError:
        click = None  # type: ignore[assignment]
    for param in getattr(command, "params", []) or []:
        name = getattr(param, "name", None)
        if not name or name in {"self", "ctx", "context"}:
            continue
        if getattr(param, "hidden", False):
            continue
        is_argument = click is not None and isinstance(param, click.Argument)
        opts = [str(o) for o in (getattr(param, "opts", None) or []) if o]
        if not opts:
            opts = [str(name) if is_argument else f"--{str(name).replace('_', '-')}"]
        default = getattr(param, "default", None)
        if default is inspect.Parameter.empty:
            default = None
        required = bool(getattr(param, "required", False))
        if default is None and is_argument and getattr(param, "required", True):
            required = True
        help_text = str(getattr(param, "help", None) or "").strip()
        rows.append(
            {
                "name": str(name),
                "cli": " / ".join(opts),
                "help": help_text,
                "default": default,
                "required": required,
                "kind": "argument" if is_argument else "option",
            }
        )
    return rows


def _usage_line(path: str, params: list[dict[str, Any]]) -> str:
    parts = [path]
    for param in params:
        token = param.get("cli") or param.get("name") or ""
        if param.get("kind") == "argument":
            name = str(token).upper().replace("-", "_")
            parts.append(name if param.get("required") else f"[{name}]")
        elif "[OPTIONS]" not in parts:
            parts.append("[OPTIONS]")
    if "[OPTIONS]" not in parts and any(p.get("kind") == "option" for p in params):
        parts.append("[OPTIONS]")
    if len(parts) == 1:
        parts.append("[OPTIONS]")
    return "Usage: " + " ".join(parts)


def _walk_click(command: Any, prefix: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    children = getattr(command, "commands", None) or {}
    for name, sub in sorted(children.items()):
        path = f"{prefix} {name}".strip()
        help_text = (getattr(sub, "help", None) or "").strip()
        help_text = help_text.splitlines()[0] if help_text else ""
        params = _click_params(sub)
        is_group = bool(getattr(sub, "commands", None))
        sub_names = sorted((getattr(sub, "commands", None) or {}).keys())
        rows.append(
            {
                "command": path,
                "help": help_text,
                "params": params,
                "usage": _usage_line(path, params),
                "is_group": is_group,
                "subcommands": sub_names,
            }
        )
        if is_group:
            rows.extend(_walk_click(sub, path))
    return rows


def _walk_typer(app: Any, prefix: str = "qseh") -> list[dict[str, Any]]:
    """Extract a flat command list from a Typer app (live tree is authoritative)."""
    try:
        from typer.main import get_command

        click_cmd = get_command(app)
        rows = _walk_click(click_cmd, prefix)
        if rows:
            return rows
    except Exception:  # noqa: BLE001
        rows = []

    rows: list[dict[str, Any]] = []

    def visit(typer_app: Any, path: str) -> None:
        for cmd in getattr(typer_app, "registered_commands", []) or []:
            name = cmd.name or getattr(cmd.callback, "__name__", "command")
            help_text = (cmd.help or getattr(cmd.callback, "__doc__", None) or "").strip()
            help_text = help_text.splitlines()[0] if help_text else ""
            params = _command_params_fallback(cmd.callback) if cmd.callback else []
            rows.append(
                {
                    "command": f"{path} {name}".strip(),
                    "help": help_text,
                    "params": params,
                    "usage": _usage_line(f"{path} {name}".strip(), params),
                    "is_group": False,
                    "subcommands": [],
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
                    "usage": f"Usage: {path} {gname} [OPTIONS] COMMAND [ARGS]...",
                    "is_group": True,
                    "subcommands": [],
                }
            )
            visit(gapp, f"{path} {gname}".strip())

    visit(app, prefix)
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for row in rows:
        key = row["command"]
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


def _command_params_fallback(callback: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
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
            required = True
        else:
            default_value = getattr(default, "default", default)
            help_text = str(getattr(default, "help", "") or "")
            param_decls = getattr(default, "param_decls", None) or ()
            option_names = [str(d) for d in param_decls if d]
            cls_name = type(default).__name__
            if "Argument" in cls_name:
                is_option = False
            if default_value is Ellipsis or repr(default_value) == "Ellipsis":
                default_value = None
                required = True
            else:
                required = False
        if not option_names:
            option_names = [f"--{name.replace('_', '-')}" if is_option else name]
        rows.append(
            {
                "name": name,
                "cli": " / ".join(option_names),
                "help": help_text.strip(),
                "default": None if default_value is Ellipsis else default_value,
                "required": bool(required),
                "kind": "option" if is_option else "argument",
            }
        )
    return rows


def _cli_markdown(commands: list[dict[str, Any]], *, generated_at: str, sha: str | None) -> str:
    lines = [
        _yaml_frontmatter(
            title="CLI Reference",
            description="Generated from the current qseh Typer command tree.",
            sha=sha,
            generated_at=generated_at,
        ).rstrip(),
        "",
        "# CLI Reference",
        "",
        f"Generated from commit `{sha or 'unavailable'}`.",
        "",
        "Authoritative source: the live Typer command tree (`qseh docs build`).",
        "",
        "Do not maintain a handwritten second command inventory.",
        "",
    ]
    for row in commands:
        cmd = row["command"]
        lines.append(f"## `{cmd}`")
        lines.append("")
        help_text = (row.get("help") or "").strip()
        if help_text:
            lines.append(help_text)
            lines.append("")
        usage = row.get("usage") or f"Usage: {cmd} [OPTIONS]"
        lines.append("```text")
        lines.append(usage)
        lines.append("```")
        lines.append("")
        subcommands = row.get("subcommands") or []
        if subcommands:
            lines.append("Subcommands: " + ", ".join(f"`{s}`" for s in subcommands) + ".")
            lines.append("")
        params = row.get("params") or []
        args = [p for p in params if p.get("kind") == "argument"]
        opts = [p for p in params if p.get("kind") != "argument"]
        if args:
            lines.append("### Arguments")
            lines.append("")
            lines.extend(
                _md_table(
                    ["Argument", "Required", "Default", "Meaning"],
                    [
                        [
                            p.get("cli") or p.get("name"),
                            "yes" if p.get("required") else "no",
                            "" if p.get("default") is None else p.get("default"),
                            p.get("help") or "",
                        ]
                        for p in args
                    ],
                )
            )
            lines.append("")
        if opts:
            lines.append("### Options")
            lines.append("")
            lines.extend(
                _md_table(
                    ["Option", "Required", "Default", "Meaning"],
                    [
                        [
                            p.get("cli") or p.get("name"),
                            "yes" if p.get("required") else "no",
                            "" if p.get("default") is None else p.get("default"),
                            p.get("help") or "",
                        ]
                        for p in opts
                    ],
                )
            )
            lines.append("")
    return "\n".join(lines) + "\n"


# ─── Backend API from OpenAPI ───────────────────────────────────


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


def _ref_name(ref: str) -> str:
    return ref.rsplit("/", 1)[-1]


def _schema_label(schema: Any, components: dict[str, Any], *, depth: int = 0) -> str:
    if not isinstance(schema, dict):
        return ""
    if "$ref" in schema:
        name = _ref_name(str(schema["$ref"]))
        if depth >= 2:
            return name
        resolved = (components.get("schemas") or {}).get(name) or {}
        inner = _schema_label(resolved, components, depth=depth + 1)
        return f"{name} ({inner})" if inner and inner != name else name
    if "anyOf" in schema or "oneOf" in schema:
        alts = schema.get("anyOf") or schema.get("oneOf") or []
        return " | ".join(_schema_label(item, components, depth=depth + 1) for item in alts[:4])
    typ = schema.get("type")
    if typ == "array":
        return f"array[{_schema_label(schema.get('items') or {}, components, depth=depth + 1)}]"
    if typ == "object":
        props = schema.get("properties") or {}
        if not props:
            return "object"
        bits = []
        for key, value in list(props.items())[:16]:
            bits.append(f"{key}: {_schema_label(value, components, depth=depth + 1) or value.get('type', 'any')}")
        extra = "" if len(props) <= 16 else f", … +{len(props) - 16}"
        return "{" + ", ".join(bits) + extra + "}"
    if typ:
        return str(typ)
    if schema.get("title"):
        return str(schema["title"])
    return ""


def _backend_api_markdown(schema: dict[str, Any], *, generated_at: str, sha: str | None) -> str:
    paths = schema.get("paths") or {}
    components = schema.get("components") or {}
    lines = [
        _yaml_frontmatter(
            title="Backend API",
            description="Generated from create_app().openapi() for the Research Console.",
            sha=sha,
            generated_at=generated_at,
        ).rstrip(),
        "",
        "# Backend API",
        "",
        f"Generated from commit `{sha or 'unavailable'}`.",
        "",
        f"OpenAPI `{schema.get('openapi', '')}` — {len(paths)} paths from the live FastAPI application.",
        "",
        "Swagger UI is isolated at `/api/dev/docs` so it does not collide with the SPA `/docs` page.",
        "",
    ]
    for path in sorted(paths):
        methods = paths[path] or {}
        for method in ("get", "post", "put", "patch", "delete"):
            op = methods.get(method)
            if not isinstance(op, dict):
                continue
            summary = (op.get("summary") or op.get("operationId") or "").strip()
            description = (op.get("description") or "").strip()
            lines.append(f"## `{method.upper()} {path}`")
            lines.append("")
            if summary:
                lines.append(summary)
                lines.append("")
            if description and description != summary:
                lines.append(description)
                lines.append("")
            params = op.get("parameters") or []
            if params:
                rows = []
                for param in params:
                    if not isinstance(param, dict):
                        continue
                    schema_obj = param.get("schema") or {}
                    rows.append(
                        [
                            param.get("name"),
                            param.get("in"),
                            "yes" if param.get("required") else "no",
                            _schema_label(schema_obj, components) or schema_obj.get("type", ""),
                            param.get("description") or "",
                        ]
                    )
                lines.append("### Parameters")
                lines.append("")
                lines.extend(
                    _md_table(["Name", "In", "Required", "Type", "Meaning"], rows)
                )
                lines.append("")
            body = (op.get("requestBody") or {}).get("content") or {}
            json_body = body.get("application/json") or next(iter(body.values()), None)
            if isinstance(json_body, dict) and json_body.get("schema"):
                lines.append("### Request body")
                lines.append("")
                lines.append(_schema_label(json_body["schema"], components) or "object")
                lines.append("")
            responses = op.get("responses") or {}
            if responses:
                rows = []
                for code, resp in responses.items():
                    if not isinstance(resp, dict):
                        continue
                    content = (resp.get("content") or {}).get("application/json") or {}
                    schema_obj = content.get("schema") or {}
                    rows.append(
                        [
                            str(code),
                            resp.get("description") or "",
                            _schema_label(schema_obj, components),
                        ]
                    )
                lines.append("### Responses")
                lines.append("")
                lines.extend(_md_table(["Status", "Description", "Schema"], rows))
                lines.append("")
    return "\n".join(lines) + "\n"


# ─── Python API from signatures ─────────────────────────────────


def _format_default(value: Any) -> str:
    if value is inspect.Parameter.empty:
        return ""
    try:
        text = repr(value)
    except Exception:  # noqa: BLE001
        text = str(value)
    if len(text) > 80:
        return text[:77] + "..."
    return text


def _document_callable(qualname: str, obj: Any, missing: list[str]) -> list[str]:
    lines: list[str] = [f"## `{qualname}`", ""]
    try:
        if inspect.isclass(obj):
            init = getattr(obj, "__init__", None)
            sig = f"{obj.__name__}{inspect.signature(init)}" if init else f"{obj.__name__}(...)"
        elif callable(obj):
            sig = f"{getattr(obj, '__name__', qualname.split('.')[-1])}{inspect.signature(obj)}"
        else:
            sig = qualname.split(".")[-1]
    except (TypeError, ValueError):
        sig = qualname.split(".")[-1]
    lines.append(f"`{sig}`")
    lines.append("")
    doc = inspect.getdoc(obj)
    if doc:
        lines.append(doc)
        lines.append("")
    else:
        missing.append(qualname)
        lines.append("MISSING DOCSTRING")
        lines.append("")
    try:
        target = obj.__init__ if inspect.isclass(obj) else obj
        signature = inspect.signature(target)
    except (TypeError, ValueError):
        signature = None
    if signature is not None:
        rows = []
        for name, param in signature.parameters.items():
            if name in {"self", "cls"}:
                continue
            ann = "" if param.annotation is inspect.Parameter.empty else str(param.annotation)
            rows.append(
                [
                    name,
                    "yes" if param.default is inspect.Parameter.empty else "no",
                    _format_default(param.default),
                    ann,
                ]
            )
        if rows:
            lines.append("### Parameters")
            lines.append("")
            lines.extend(_md_table(["Name", "Required", "Default", "Type"], rows))
            lines.append("")
        ret = signature.return_annotation
        if ret is not inspect.Parameter.empty:
            lines.append(f"Returns: `{ret}`")
            lines.append("")
    raises = []
    if doc:
        for raw in doc.splitlines():
            stripped = raw.strip()
            if stripped.startswith((":raises", "Raises")):
                raises.append(stripped)
    if raises:
        lines.append("### Exceptions")
        lines.append("")
        for item in raises:
            lines.append(f"- {item}")
        lines.append("")
    if inspect.isclass(obj):
        methods = []
        for name, member in inspect.getmembers(obj, predicate=inspect.isfunction):
            if name.startswith("_"):
                continue
            methods.append((name, member))
        for name, member in methods:
            lines.extend(_document_callable(f"{qualname}.{name}", member, missing))
    return lines


def _python_api_reference() -> tuple[str, list[str], int]:
    missing: list[str] = []
    generated_at = _utc_now()
    sha = _git_sha(find_repo_root())
    lines = [
        _yaml_frontmatter(
            title="Python API",
            description="Generated from public project signatures and docstrings.",
            sha=sha,
            generated_at=generated_at,
        ).rstrip(),
        "",
        "# Python API",
        "",
        f"Generated from commit `{sha or 'unavailable'}`.",
        "",
        "Intended public interfaces only. Private helpers (`_name`) are omitted.",
        "",
        "Missing docstrings are reported as `MISSING DOCSTRING` rather than invented.",
        "",
    ]
    signatures = 0
    for module_name, attr in PYTHON_API_TARGETS:
        try:
            mod = __import__(module_name, fromlist=[attr])
            obj = getattr(mod, attr)
        except Exception as exc:  # noqa: BLE001
            lines.append(f"## `{module_name}.{attr}`")
            lines.append("")
            lines.append(f"_Unavailable: {type(exc).__name__}: {exc}_")
            lines.append("")
            continue
        signatures += 1
        lines.extend(_document_callable(f"{module_name}.{attr}", obj, missing))
    return "\n".join(lines) + "\n", missing, signatures


# ─── Configuration from real schemas / YAML ─────────────────────


def _config_reference(repo_root: Path, *, generated_at: str, sha: str | None) -> str:
    from qs_everesteer.models import MODEL_FACTORIES
    from qs_everesteer.state.research import SubmissionMode
    from qs_everesteer.validation.temporal import FOLD_PROFILES, FoldProfile

    lines = [
        _yaml_frontmatter(
            title="Configuration",
            description="Generated from experiment YAML keys, fold profiles, and project configs.",
            sha=sha,
            generated_at=generated_at,
        ).rstrip(),
        "",
        "# Configuration",
        "",
        f"Generated from commit `{sha or 'unavailable'}`.",
        "",
        "Fields below are taken from code that actually reads them, dataclasses, enums, and checked-in YAML. Undocumented keys are not inferred.",
        "",
        "## Race / experiment configuration",
        "",
        "Consumed by `ExperimentRunner.run` from a YAML mapping or dict.",
        "",
    ]
    lines.extend(
        _md_table(
            ["Field", "Type", "Required", "Default", "Meaning"],
            [
                ["data_path", "path", "yes", "", "Training parquet path read by ExperimentRunner"],
                ["model", "str | {name, params}", "no", "ridge", "Model factory name or mapping with name/params"],
                ["params", "dict", "no", "{}", "Hyperparameters when model is a string"],
                ["profile", "R0/R1/R2/R3", "no", "R1", "Temporal fold profile passed to temporal_cv"],
                ["target", "str", "no", "target_everest_20", "Target column"],
                ["exped_col", "str", "no", "exped", "Time-group / exped column"],
                ["features", "list[str]", "no", "feature_* columns", "Feature list; otherwise columns starting with feature_"],
                ["run_id", "str", "no", "run-<uuid12>", "Persisted experiment id"],
                ["data_hash", "str", "no", "", "Optional training data fingerprint stored on the model artefact"],
            ],
        )
    )
    lines += ["", "## Fold profiles", "", "From `FoldProfile` / `FOLD_PROFILES` in `qs_everesteer.validation.temporal`.", ""]
    fold_fields = [f.name for f in dataclasses.fields(FoldProfile)]
    fold_rows = []
    for name, profile in FOLD_PROFILES.items():
        fold_rows.append([name] + [getattr(profile, field) for field in fold_fields])
    lines.extend(_md_table(["Key", *fold_fields], fold_rows))
    lines += [
        "",
        "## Model factories",
        "",
        "Names accepted by `qs_everesteer.models.create_model`.",
        "",
    ]
    lines.extend(
        _md_table(
            ["Name", "Factory"],
            [[key, f"{fn.__module__}.{fn.__name__}"] for key, fn in sorted(MODEL_FACTORIES.items())],
        )
    )

    model_dir = repo_root / "configs" / "models"
    if model_dir.is_dir():
        lines += ["", "## Model YAML examples", "", "Checked-in files under `configs/models/`.", ""]
        try:
            import yaml
        except ImportError:
            yaml = None  # type: ignore[assignment]
        for path in sorted(model_dir.glob("*.yaml")):
            lines.append(f"### `{path.as_posix()}`")
            lines.append("")
            if yaml is None:
                lines.append("_PyYAML unavailable_")
                lines.append("")
                continue
            loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            rows = []
            if isinstance(loaded, dict):
                for key, value in loaded.items():
                    if isinstance(value, dict):
                        for inner_k, inner_v in value.items():
                            rows.append([f"{key}.{inner_k}", type(inner_v).__name__, inner_v])
                    else:
                        rows.append([key, type(value).__name__, value])
            if rows:
                lines.extend(_md_table(["Field", "Type", "Example"], rows))
                lines.append("")

    event_path = repo_root / "configs" / "event" / "everesteer_london_2026.yaml"
    if event_path.is_file():
        lines += ["", "## Event configuration", "", f"From `{event_path.as_posix()}`.", ""]
        try:
            import yaml

            loaded = yaml.safe_load(event_path.read_text(encoding="utf-8")) or {}
        except Exception:  # noqa: BLE001
            loaded = {}
        rows = []

        def walk(prefix: str, node: Any) -> None:
            if isinstance(node, dict):
                for key, value in node.items():
                    walk(f"{prefix}.{key}" if prefix else str(key), value)
            else:
                rows.append([prefix, type(node).__name__, node])

        walk("", loaded)
        if rows:
            lines.extend(_md_table(["Field", "Type", "Example"], rows))
            lines.append("")

    lines += [
        "",
        "## Submission configuration",
        "",
        "Persisted as `submission_mode` in research state. `ARMED` requires an explicit snapshot id.",
        "",
    ]
    lines.extend(
        _md_table(
            ["Value", "Type", "Default", "Meaning"],
            [
                [SubmissionMode.DISABLED.value, "enum", "no", "External uploads cannot be performed"],
                [SubmissionMode.DRY_RUN.value, "enum", "yes", "Validate/package/record without uploading"],
                [SubmissionMode.ARMED.value, "enum", "no", "Real uploads permitted after explicit arm"],
            ],
        )
    )
    from qs_everesteer.autopilot.orchestrator import STAGE_ORDER, CompetitionAutopilot

    step_sig = inspect.signature(CompetitionAutopilot.step)
    profile_default = step_sig.parameters["profile"].default
    lines += [
        "",
        "## Autopilot configuration",
        "",
        f"`CompetitionAutopilot.step` / `run` take `profile` (default `{profile_default}`).",
        "",
        "Autopilot never transitions submission mode to ARMED.",
        "",
    ]
    lines.extend(
        _md_table(
            ["Stage", "Order"],
            [[stage.value, i] for i, stage in enumerate(STAGE_ORDER)],
        )
    )
    lines.append("")
    return "\n".join(lines) + "\n"


# ─── Markdown → DocBlock ────────────────────────────────────────


def markdown_to_blocks(body: str) -> list[dict[str, Any]]:
    """Convert generated markdown (minus frontmatter) into Documentation blocks."""
    blocks: list[dict[str, Any]] = []
    lines = body.splitlines()
    i = 0
    saw_intro = False
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        if not stripped:
            i += 1
            continue
        if stripped.startswith("# ") and not stripped.startswith("## "):
            i += 1
            continue
        heading = _MD_HEADING_RE.match(stripped)
        if heading:
            blocks.append({"kind": "heading", "text": heading.group(2).strip().strip("`")})
            i += 1
            continue
        if stripped.startswith("```"):
            fence: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                fence.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            text = "\n".join(fence).strip()
            if text.lower().startswith("usage:") or text.startswith(("qseh ", ".\\", "./")):
                blocks.append({"kind": "command", "command": text})
            elif text:
                blocks.append({"kind": "paragraph", "text": text})
            continue
        if stripped.startswith("|") and i + 1 < len(lines) and _TABLE_SEP_RE.match(lines[i + 1].strip()):
            headers = [c.strip().strip("`") for c in stripped.strip("|").split("|")]
            i += 2
            rows: list[list[str]] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip().strip("`") for c in lines[i].strip().strip("|").split("|")])
                i += 1
            blocks.append({"kind": "table", "headers": headers, "rows": rows})
            continue
        para = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if not nxt or nxt.startswith(("#", "|", "```")):
                break
            para.append(nxt)
            i += 1
        text = " ".join(para)
        if not saw_intro:
            blocks.append({"kind": "intro", "text": text})
            saw_intro = True
        else:
            blocks.append({"kind": "paragraph", "text": text})
    return blocks


def article_search_haystack(article: dict[str, Any]) -> str:
    """Index title, description, headings, body, commands, tables, metrics."""
    parts = [str(article.get("title") or ""), str(article.get("description") or "")]
    for block in article.get("blocks") or []:
        if not isinstance(block, dict):
            continue
        kind = block.get("kind")
        if kind in {"intro", "heading", "paragraph", "callout"}:
            parts.append(str(block.get("text") or ""))
        elif kind == "command":
            parts.append(str(block.get("command") or ""))
        elif kind == "metric":
            parts.append(str(block.get("name") or ""))
            parts.append(str(block.get("text") or ""))
        elif kind == "related":
            parts.append(str(block.get("href") or ""))
            parts.append(str(block.get("label") or ""))
        elif kind == "flow":
            for node in block.get("nodes") or []:
                if isinstance(node, dict):
                    parts.append(str(node.get("label") or ""))
        elif kind == "table":
            parts.extend(str(h) for h in (block.get("headers") or []))
            for row in block.get("rows") or []:
                if isinstance(row, list):
                    parts.extend(str(cell) for cell in row)
    return " ".join(parts).lower()


def article_matches_query(article: dict[str, Any], query: str) -> bool:
    if not query:
        return True
    return query.lower() in article_search_haystack(article)


# ─── Curated MDX ────────────────────────────────────────────────


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
    leftover = _HEADING_RE.sub("", suffix).strip()
    if leftover:
        for para in re.split(r"\n\s*\n", leftover):
            cleaned = para.strip()
            if cleaned:
                blocks.append({"kind": "paragraph", "text": cleaned})
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


def _count_table_rows(blocks: list[dict[str, Any]]) -> int:
    total = 0
    for block in blocks:
        if block.get("kind") == "table":
            total += len(block.get("rows") or [])
    return total


def _is_stub_article(article: dict[str, Any]) -> bool:
    blocks = article.get("blocks") or []
    if len(blocks) < MIN_GENERATED_BLOCKS:
        return True
    kinds = {b.get("kind") for b in blocks if isinstance(b, dict)}
    if kinds <= {"intro"}:
        return True
    texts = [
        str(b.get("text") or "")
        for b in blocks
        if isinstance(b, dict) and b.get("kind") in {"intro", "paragraph"}
    ]
    return bool(
        texts
        and all("generated" in t.lower() and len(t) < 120 for t in texts)
        and "table" not in kinds
    )


class DocsBuildError(RuntimeError):
    """Generated documentation failed the quality gate."""


def verify_docs_manifest(repo_root: str | Path | None = None) -> dict[str, Any]:
    """Fail if generated docs are missing, stubby, or lack a git sha."""
    root = Path(repo_root) if repo_root is not None else find_repo_root()
    manifest_path = root / "dashboard" / "frontend" / "src" / "generated" / "docs-manifest.json"
    if not manifest_path.is_file():
        raise DocsBuildError(f"missing docs manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sha = manifest.get("generated_from_sha") or manifest.get("generatedFromSha")
    generated_at = manifest.get("generated_at") or manifest.get("generatedAt")
    if not sha or sha == "unavailable":
        raise DocsBuildError("generatedFromSha is null/unavailable")
    if not generated_at:
        raise DocsBuildError("generatedAt is missing")
    articles = {a["id"]: a for a in manifest.get("articles") or [] if isinstance(a, dict)}
    for article_id in ("cli-reference", "backend-api", "python-api", "configuration"):
        article = articles.get(article_id)
        if not article:
            raise DocsBuildError(f"missing generated article {article_id}")
        if _is_stub_article(article):
            raise DocsBuildError(f"{article_id} is a stub (too few blocks / intro-only)")
    hay = " ".join(article_search_haystack(a) for a in articles.values())
    if "qseh event arm-submissions" not in hay and "arm-submissions" not in hay:
        raise DocsBuildError("CLI reference does not contain arm-submissions")
    if "/api/overview" not in hay and "/api/health" not in hay:
        raise DocsBuildError("Backend API is missing real routes")
    config = articles["configuration"]
    if _count_table_rows(config.get("blocks") or []) < MIN_CONFIG_FIELD_ROWS:
        raise DocsBuildError("Configuration is missing real field tables")
    return {
        "ok": True,
        "generated_from_sha": sha,
        "generated_at": generated_at,
        "articles": len(manifest.get("articles") or []),
    }


def _assert_generated_quality(
    *,
    commands: list[dict[str, Any]],
    openapi: dict[str, Any],
    python_signatures: int,
    articles: list[dict[str, Any]],
) -> None:
    leaf_commands = [c for c in commands if not c.get("is_group")]
    if len(leaf_commands) < MIN_CLI_COMMANDS:
        raise DocsBuildError(
            f"CLI reference too small: {len(leaf_commands)} leaf commands (min {MIN_CLI_COMMANDS})"
        )
    names = {c["command"] for c in commands}
    if "qseh doctor" not in names or "qseh docs build" not in names:
        raise DocsBuildError("CLI reference missing required live commands")
    if "qseh event arm-submissions" not in names:
        raise DocsBuildError("CLI reference missing qseh event arm-submissions")
    paths = openapi.get("paths") or {}
    if "/api/health" not in paths or len(paths) < MIN_API_PATHS:
        raise DocsBuildError(f"Backend API too small: {len(paths)} paths")
    if "/api/overview" not in paths:
        raise DocsBuildError("Backend API missing /api/overview")
    if python_signatures < MIN_PYTHON_SIGNATURES:
        raise DocsBuildError(f"Python API too small: {python_signatures} signatures")
    by_id = {a["id"]: a for a in articles}
    for article_id in ("cli-reference", "backend-api", "python-api", "configuration"):
        article = by_id.get(article_id)
        if article is None or _is_stub_article(article):
            raise DocsBuildError(f"generated article {article_id} is a stub")
    if _count_table_rows(by_id["configuration"]["blocks"]) < MIN_CONFIG_FIELD_ROWS:
        raise DocsBuildError("Configuration page has no real field tables")
    if _count_table_rows(by_id["cli-reference"]["blocks"]) < MIN_CLI_COMMANDS:
        raise DocsBuildError("CLI reference has no option/argument tables")


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
        raise DocsBuildError("Typer command walk returned empty — refusing to write stale CLI docs")

    cli_md = generated / "cli-reference.md"
    cli_text = _cli_markdown(commands, generated_at=generated_at, sha=sha)
    cli_md.write_text(cli_text, encoding="utf-8")

    openapi = research_console_openapi()
    openapi_path = generated / "openapi.json"
    openapi_path.write_text(json.dumps(openapi, indent=2) + "\n", encoding="utf-8")
    backend_md = generated / "backend-api.md"
    backend_text = _backend_api_markdown(openapi, generated_at=generated_at, sha=sha)
    backend_md.write_text(backend_text, encoding="utf-8")
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

    python_text, missing_docs, python_signatures = _python_api_reference()
    python_api_path = generated / "python-api.md"
    python_api_path.write_text(python_text, encoding="utf-8")

    config_path = generated / "configuration.md"
    config_text = _config_reference(root, generated_at=generated_at, sha=sha)
    config_path.write_text(config_text, encoding="utf-8")

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

    def _generated_article(
        *,
        article_id: str,
        title: str,
        path: str,
        order: int,
        description: str,
        markdown: str,
        tags: list[str],
    ) -> dict[str, Any]:
        _meta, body = _parse_frontmatter(markdown)
        blocks = markdown_to_blocks(body)
        return {
            "id": article_id,
            "title": title,
            "path": path,
            "tags": tags,
            "source": "generated",
            "section": "generated",
            "order": order,
            "description": description,
            "blocks": blocks,
        }

    path_count = len(openapi.get("paths") or {})
    generated_articles = [
        _generated_article(
            article_id="cli-reference",
            title="CLI Reference",
            path="docs/generated/cli-reference.md",
            order=1000,
            description="Generated from the current qseh Typer command tree.",
            markdown=cli_text,
            tags=["cli", "generated"],
        ),
        _generated_article(
            article_id="backend-api",
            title="Backend API",
            path="docs/generated/backend-api.md",
            order=1010,
            description=f"Research Console OpenAPI ({path_count} paths) from create_app().openapi()",
            markdown=backend_text,
            tags=["api", "generated", "openapi"],
        ),
        _generated_article(
            article_id="python-api",
            title="Python API",
            path="docs/generated/python-api.md",
            order=1020,
            description="Public project Python signatures and docstrings",
            markdown=python_text,
            tags=["python", "generated"],
        ),
        _generated_article(
            article_id="configuration",
            title="Configuration",
            path="docs/generated/configuration.md",
            order=1030,
            description="Experiment YAML, fold profiles, submission modes, autopilot stages",
            markdown=config_text,
            tags=["config", "generated"],
        ),
    ]

    manifest_articles: list[dict[str, Any]] = list(generated_articles)
    for article in curated:
        manifest_articles.append(
            {
                "id": article["id"],
                "title": article["title"],
                "path": article.get("path") or f"docs/{article['section']}/{article['id']}.mdx",
                "tags": ["curated", article["section"]],
                "source": "curated",
                "section": article["section"],
                "order": article["order"],
                "description": article["description"],
                "blocks": article["blocks"],
            }
        )

    _assert_generated_quality(
        commands=commands,
        openapi=openapi,
        python_signatures=python_signatures,
        articles=generated_articles,
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
        "missing_docstrings": missing_docs,
    }
    manifest_path = frontend_gen / "docs-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    index_path = generated / "README.md"
    missing_line = ", ".join(missing_docs) if missing_docs else "(none)"
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
                f"- CLI reference: `{cli_md.name}` ({len(commands)} commands)",
                f"- Commands JSON: `{commands_json.name}`",
                f"- Backend API: `{backend_md.name}` ({path_count} paths)",
                f"- Backend OpenAPI: `{openapi_path.name}`",
                f"- Python API: `{python_api_path.name}` ({python_signatures} entry points)",
                f"- Configuration: `{config_path.name}`",
                f"- Curated articles: `{curated_path.name}` ({len(curated)} MDX)",
                f"- Frontend manifest: `{manifest_path.relative_to(root).as_posix()}`",
                f"- MISSING DOCSTRING: {missing_line}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    for path in (
        cli_md,
        commands_json,
        openapi_path,
        backend_md,
        python_api_path,
        config_path,
        curated_path,
        manifest_path,
        index_path,
    ):
        _assert_utf8_clean(path)

    verify_docs_manifest(root)
    return {
        "cli_reference": cli_md,
        "commands_json": commands_json,
        "openapi": openapi_path,
        "backend_api": backend_md,
        "python_api": python_api_path,
        "configuration": config_path,
        "curated_articles": curated_path,
        "docs_manifest": manifest_path,
        "index": index_path,
    }
