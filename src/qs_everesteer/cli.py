"""CLI entry point. ``qseh = qs_everesteer.cli:app`` in pyproject.toml."""

from __future__ import annotations

from qs_everesteer.cli_app import app

__all__ = ["app"]


if __name__ == "__main__":
    app()
