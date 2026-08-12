from qs_everesteer.selection.frontier import pareto_frontier


def test_mixed_objective_frontier():
    records = [
        {"id": "fast", "score": 0.5, "diversity": 0.2, "runtime": 1},
        {"id": "slow", "score": 0.5, "diversity": 0.2, "runtime": 2},
        {"id": "diverse", "score": 0.4, "diversity": 0.9, "runtime": 1},
    ]
    result = pareto_frontier(
        records, [("score", "max"), ("diversity", "max"), ("runtime", "min")]
    )
    assert {row["id"] for row in result} == {"fast", "diverse"}
