import json

import numpy as np
import pandas as pd

from qs_everesteer.data.audit import audit_dataset
from qs_everesteer.data.synthetic import generate_synthetic_event_data
from qs_everesteer.ensemble.blend import weighted
from qs_everesteer.experiments.racing import RacingScheduler
from qs_everesteer.experiments.runner import ExperimentRunner
from qs_everesteer.selection.frontier import pareto_frontier
from qs_everesteer.submission.pipeline import PipelineRequest, SubmissionPipeline


def test_synthetic_research_loop_to_practice_dry_run(tmp_path):
    paths = generate_synthetic_event_data(
        tmp_path / "data", n_features=5, n_practice_ids=8, n_live_ids=3,
        rows_per_exped=1, n_expeds=6, missingness=0,
    )
    assert audit_dataset(paths["train"]).hard_failures == []
    run = ExperimentRunner(tmp_path).run({
        "run_id": "baseline", "data_path": str(paths["train"]),
        "model": {"name": "reference_lgbm", "params": {"n_estimators": 5}},
        "profile": "R0",
    })
    assert run["status"] == "COMPLETED"
    metrics = json.loads((tmp_path / "runs/experiments/baseline/metrics.json").read_text())
    outcomes = RacingScheduler().evaluate(
        [{"candidate_id": "baseline", "score": metrics["score"]}], "R0"
    )
    frontier = pareto_frontier(
        [{"id": "baseline", "score": metrics["score"], "runtime": run["runtime_seconds"]}],
        [("score", "max"), ("runtime", "min")],
    )
    assert outcomes[0].next_stage == "R1" and frontier
    assert weighted(np.array([[0.2], [0.8]])).shape == (2,)

    validation = pd.read_parquet(paths["validation"])
    ids = validation["id"].drop_duplicates().tolist()
    pred_path = tmp_path / "practice.parquet"
    pd.DataFrame({"id": ids, "prediction": np.linspace(0.1, 0.9, len(ids))}).to_parquet(
        pred_path, index=False
    )
    result = SubmissionPipeline(repo_root=tmp_path).run(PipelineRequest(
        event_id="SYNTHETIC_EVENT", round_id="SYNTHETIC_ROUND", lane="practice",
        candidate_id="baseline", split_fingerprint="synthetic-fingerprint",
        expected_ids=ids, predictions_path=pred_path,
    ))
    assert result.ok and result.mode == "DRY_RUN"
    assert result.upload is None
