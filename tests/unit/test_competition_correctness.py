from __future__ import annotations

import numpy as np
import pandas as pd

from qs_everesteer.autopilot.orchestrator import CompetitionAutopilot
from qs_everesteer.cli_app.common import wants_synthetic
from qs_everesteer.event.mechanics import classify_optional_mechanics
from qs_everesteer.models.baseline import ORGANISER_BASELINE_PROVENANCE
from qs_everesteer.state.research import update_research_state
from qs_everesteer.submission.guard import SubmissionContext, SubmissionGuard
from qs_everesteer.validation import scoring
from qs_everesteer.validation.temporal import TemporalSplitter, profile_for_target


def test_synthetic_mode_requires_explicit_opt_in(monkeypatch):
    monkeypatch.delenv("QSEH_SYNTHETIC", raising=False)
    monkeypatch.delenv("EIQ_API_KEY", raising=False)
    monkeypatch.delenv("EVEREST_API_KEY", raising=False)
    assert wants_synthetic() is False
    monkeypatch.setenv("QSEH_SYNTHETIC", "1")
    assert wants_synthetic() is True


def test_target_horizon_is_minimum_embargo_and_fold_count_reduces():
    profile = profile_for_target("R3", "target_everest_20")
    assert profile.embargo == 20
    groups = np.repeat(np.arange(28), 2)
    folds = list(TemporalSplitter(profile).split(groups))
    assert 0 < len(folds) < profile.n_splits
    for train, valid in folds:
        assert groups[valid].min() - groups[train].max() >= 21


def test_official_scoring_maps_named_prediction_and_target(monkeypatch):
    observed = {}

    def fake(*, y_true, y_pred):
        observed.update(y_true=list(y_true), y_pred=list(y_pred))
        return 0.25

    monkeypatch.setattr(scoring, "official_scorers", lambda: {"CORR20": fake})
    result = scoring.score(
        "CORR20", predictions=[0.1, 0.2], target=[1.0, 2.0]
    )
    assert result.official and result.value == 0.25
    assert observed == {"y_true": [1.0, 2.0], "y_pred": [0.1, 0.2]}


def test_submission_guard_accepts_unbounded_finite_predictions(tmp_path):
    path = tmp_path / "predictions.parquet"
    pd.DataFrame({"id": ["a", "b"], "prediction": [-3.0, 4.0]}).to_parquet(path)
    result = SubmissionGuard().validate(
        SubmissionContext(
            event_id="event",
            round_id="round",
            lane="practice",
            split_fingerprint="fingerprint",
            candidate_id="candidate",
            predictions_path=path,
            expected_ids=["a", "b"],
            quota_known=True,
            quota_remaining=1,
            mode="DRY_RUN",
        )
    )
    assert result.ok


def test_submission_guard_rejects_nonfinite_predictions(tmp_path):
    path = tmp_path / "predictions.parquet"
    pd.DataFrame({"id": ["a"], "prediction": [np.inf]}).to_parquet(path)
    result = SubmissionGuard().validate(
        SubmissionContext(
            event_id="event", round_id="round", lane="practice",
            split_fingerprint="fingerprint", candidate_id="candidate",
            predictions_path=path, expected_ids=["a"], quota_known=True,
            quota_remaining=1, mode="DRY_RUN",
        )
    )
    assert not result.ok
    assert any("non-finite" in reason for reason in result.blocking_reasons)


def test_missing_autopilot_handler_blocks_without_advancing(tmp_path):
    update_research_state(
        lambda state: state.update(autopilot_stage="DISCOVER"), repo_root=tmp_path
    )
    state = CompetitionAutopilot(tmp_path).run(max_steps=5)
    assert state["autopilot_stage"] == "DISCOVER"
    assert state["autopilot_blocked"] is True
    assert "mandatory handler missing" in state["autopilot_block_reason"]
    assert len(state["autopilot_history"]) == 1


def test_optional_event_mechanics_are_capability_classified():
    result = classify_optional_mechanics(
        {"final_selection_available": False, "staking_available": None}
    )
    assert result["final_selection"]["status"] == "SKIPPED_NOT_APPLICABLE"
    assert result["staking"]["status"] == "BLOCKED_CAPABILITY_UNKNOWN"


def test_official_starter_provenance_is_attributable():
    assert ORGANISER_BASELINE_PROVENANCE["organiser_parity_status"] == "SOURCE_RETRIEVED"
    assert ORGANISER_BASELINE_PROVENANCE["embargo_expeds"] == 20
    assert ORGANISER_BASELINE_PROVENANCE["holdout_expeds"] == 100
    assert len(ORGANISER_BASELINE_PROVENANCE["hash"]) == 64
