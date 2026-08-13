import json

import pytest

from qs_everesteer.selection.champion import select_champion


def _run(root, name, profile, score):
    folder = root / "runs" / "experiments" / name
    folder.mkdir(parents=True)
    (folder / "run.json").write_text(json.dumps({
        "run_id": name, "status": "COMPLETED", "config": {"profile": profile}
    }))
    (folder / "metrics.json").write_text(json.dumps({"score": score}))


def test_champion_requires_promotion_grade_oof(tmp_path):
    _run(tmp_path, "synthetic-r1", "R1", 99.0)
    _run(tmp_path, "synthetic-r3-a", "R3", 0.2)
    _run(tmp_path, "synthetic-r3-b", "R3", 0.4)
    result = select_champion(tmp_path)
    assert result["champion"]["id"] == "synthetic-r3-b"
    assert result["reserves"][0]["id"] == "synthetic-r3-a"


def test_champion_blocks_without_r3_evidence(tmp_path):
    _run(tmp_path, "synthetic-r1", "R1", 1.0)
    with pytest.raises(RuntimeError, match="no completed R3"):
        select_champion(tmp_path)
