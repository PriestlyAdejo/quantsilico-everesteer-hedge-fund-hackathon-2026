"""Champion selection and local candidate inference/package commands."""
from __future__ import annotations

from pathlib import Path

import typer

from qs_everesteer.cli_app.common import print_json, print_mutation_context, repo_root
from qs_everesteer.selection.candidate import infer_candidate, package_candidate
from qs_everesteer.selection.champion import select_champion
from qs_everesteer.state.research import load_research_state, update_research_state

candidate_app = typer.Typer(help="Local candidate inference and packaging.", no_args_is_help=True)


def _candidate_id(value: str, root: Path) -> str:
    if value != "champion":
        return value
    champion = load_research_state(root).get("champion") or {}
    candidate_id = champion.get("id") if isinstance(champion, dict) else None
    if not candidate_id:
        raise typer.BadParameter("no champion has been selected")
    return str(candidate_id)


@candidate_app.command("infer")
def infer(candidate: str = typer.Option("champion", "--candidate"), data: Path = typer.Option(..., "--data"), out: Path | None = typer.Option(None, "--out")) -> None:  # noqa: B008
    """Generate local predictions; never uploads them."""
    root = repo_root()
    candidate_id = _candidate_id(candidate, root)
    print_mutation_context(candidate=candidate_id, lane="practice")
    print_json(infer_candidate(root, candidate_id=candidate_id, data_path=data, output_path=out))


@candidate_app.command("package")
def package(candidate: str = typer.Option("champion", "--candidate"), predictions: Path = typer.Option(..., "--predictions")) -> None:  # noqa: B008
    """Create a lineage manifest without external upload."""
    root = repo_root()
    candidate_id = _candidate_id(candidate, root)
    print_mutation_context(candidate=candidate_id, lane="practice")
    print_json(package_candidate(root, candidate_id=candidate_id, predictions_path=predictions))


def champion_select_command() -> None:
    """Select the best integrity-valid promotion-grade R3 candidate."""
    root = repo_root()
    selected = select_champion(root)
    def _mutate(state: dict) -> None:
        state["champion"] = selected["champion"]
        state["reserves"] = selected["reserves"]
        state["meta"]["source"] = "champion_select"
    update_research_state(_mutate, repo_root=root)
    print_json(selected)
