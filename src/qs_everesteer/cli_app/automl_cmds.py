"""Bounded family, survivor-tuning, and diversity search commands."""
from __future__ import annotations

from pathlib import Path

import typer

from qs_everesteer.automl.search import AutoMLSearch
from qs_everesteer.cli_app.common import print_json, print_mutation_context, repo_root

search_app = typer.Typer(help="Bounded AutoML search.", no_args_is_help=True)


def _run(kind: str, data: Path, profile: str, max_trials: int) -> None:
    root = repo_root()
    print_mutation_context(lane="practice", extra={"search_kind": kind, "profile": profile})
    search = AutoMLSearch(root)
    if kind == "family":
        trials = search.family_trials(profile=profile, max_trials=max_trials)
    elif kind == "advanced":
        trials = search.advanced_trials(profile=profile, max_trials=max_trials)
    else:
        trials = search.tune_trials(search.survivor_records(), profile=profile, max_trials=max_trials)
    result = search.execute(trials, data_path=data)
    print_json(result)
    if not trials:
        raise typer.Exit(code=1)


@search_app.command("family")
def family(data: Path = typer.Option(..., "--data"), profile: str = typer.Option("R0", "--profile"), max_trials: int = typer.Option(7, "--max-trials", min=1, max=32)) -> None:  # noqa: B008
    """Run the broad, cheap family tournament."""
    _run("family", data, profile.upper(), max_trials)


@search_app.command("tune")
def tune(data: Path = typer.Option(..., "--data"), profile: str = typer.Option("R2", "--profile"), max_trials: int = typer.Option(8, "--max-trials", min=1, max=32), survivors: bool = typer.Option(True, "--survivors/--all")) -> None:  # noqa: B008
    """Tune only candidates promoted by the latest race."""
    del survivors  # retained as an explicit, backward-stable semantic flag
    _run("tune", data, profile.upper(), max_trials)


@search_app.command("advanced")
def advanced(data: Path = typer.Option(..., "--data"), profile: str = typer.Option("R1", "--profile"), max_trials: int = typer.Option(3, "--max-trials", min=1, max=12), bounded: bool = typer.Option(True, "--bounded/--unbounded")) -> None:  # noqa: B008
    """Run diversity challengers at bounded budgets."""
    if not bounded:
        raise typer.BadParameter("unbounded advanced search is intentionally unsupported")
    _run("advanced", data, profile.upper(), max_trials)
