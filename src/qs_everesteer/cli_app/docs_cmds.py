"""Documentation generation commands."""

from __future__ import annotations

import typer

from qs_everesteer.cli_app.common import print_json, repo_root
from qs_everesteer.docs_build import build_docs

docs_app = typer.Typer(help="Generate documentation from live code.", no_args_is_help=True)


@docs_app.command("build")
def docs_build() -> None:
    """Write docs/generated/ and dashboard frontend docs-manifest.json."""
    from qs_everesteer.cli import app as cli_app

    paths = build_docs(repo_root(), app=cli_app)
    print_json({key: str(path) for key, path in paths.items()})
