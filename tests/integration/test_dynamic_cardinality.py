"""ConsoleService heatmap/matrix/table lengths track model×round cardinality."""

from __future__ import annotations

from pathlib import Path

import pytest

from dashboard.backend.app.services.console import ConsoleService
from qs_everesteer.state.research import save_research_state, update_research_state


def _seed_cardinality(repo: Path, *, n_models: int, n_rounds: int) -> None:
    models = [f"m{i:02d}" for i in range(n_models)]
    rounds = [f"R{i + 1}" for i in range(n_rounds)]
    save_research_state(
        {
            "connection": "LIVE",
            "models": models,
            "rounds": rounds,
            "frontier": [{"id": mid, "score": 0.5} for mid in models],
            "champion": models[0] if models else None,
            "meta": {"source": "cardinality_fixture", "updated_at": None},
        },
        repo,
    )


@pytest.mark.parametrize("n_models,n_rounds", [(1, 1), (4, 5), (50, 20)])
def test_console_heatmap_and_matrix_match_cardinality(
    tmp_path: Path, n_models: int, n_rounds: int
) -> None:
    _seed_cardinality(tmp_path, n_models=n_models, n_rounds=n_rounds)
    service = ConsoleService(tmp_path)

    models_env = service.models()
    assert len(models_env.data) == n_models

    room = service.round_room()
    assert len(room.data.heatmap_data) == n_models * n_rounds
    assert {cell.model for cell in room.data.heatmap_data} == {
        f"m{i:02d}" for i in range(n_models)
    }
    assert {cell.round for cell in room.data.heatmap_data} == {
        f"R{i + 1}" for i in range(n_rounds)
    }

    board = service.leaderboard()
    assert len(board.data.round_model_matrix) == n_models * n_rounds
    assert len(board.data.round_model_matrix) == len(room.data.heatmap_data)


def test_empty_cardinality_does_not_crash(tmp_path: Path) -> None:
    update_research_state(lambda state: state.update(models=[], rounds=[]), tmp_path)
    service = ConsoleService(tmp_path)
    assert service.models().data == []
    assert service.round_room().data.heatmap_data == []
    assert service.leaderboard().data.round_model_matrix == []
