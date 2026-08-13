import json

from qs_everesteer.api_schemas.pages import RaceDecision
from qs_everesteer.experiments.racing import RacingScheduler


def test_racing_integrity_is_hard_and_quality_is_soft():
    records = [
        {"candidate_id": "bad", "score": 99, "integrity_ok": False},
        {"candidate_id": "best", "score": 0.4},
        {"candidate_id": "low", "score": 0.1},
    ]
    outcomes = {x.candidate_id: x for x in RacingScheduler().evaluate(records, "R0")}
    assert outcomes["bad"].decision is RaceDecision.INVALID_INTEGRITY
    assert outcomes["best"].next_stage == "R1"
    assert outcomes["low"].decision is RaceDecision.RETIRE_DOMINATED


def test_promotions_create_retraining_child_configs(tmp_path):
    folder = tmp_path / "runs" / "experiments" / "synthetic-parent"
    folder.mkdir(parents=True)
    (folder / "run.json").write_text(json.dumps({
        "config": {"model": "ridge", "profile": "R0", "data_path": "synthetic.parquet"}
    }))
    outcomes = RacingScheduler().evaluate(
        [{"candidate_id": "synthetic-parent", "score": 0.2}], "R0"
    )
    configs = RacingScheduler.child_configs(outcomes, repo_root=tmp_path, target_stage="R1")
    assert configs[0]["parent_run_id"] == "synthetic-parent"
    assert configs[0]["profile"] == "R1"
    assert configs[0]["run_id"].endswith("-r1")
