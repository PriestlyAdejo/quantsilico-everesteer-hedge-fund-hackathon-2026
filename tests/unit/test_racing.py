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
