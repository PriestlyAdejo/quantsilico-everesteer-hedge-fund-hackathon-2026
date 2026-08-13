from qs_everesteer.automl.search import RESEARCH_SEQUENCE, AutoMLSearch


def test_search_is_bounded_deterministic_and_ordered(tmp_path):
    search = AutoMLSearch(tmp_path)
    first = search.family_trials(profile="R0", max_trials=3)
    second = search.family_trials(profile="R0", max_trials=3)
    assert [trial.run_id for trial in first] == [trial.run_id for trial in second]
    assert len(first) == 3
    assert RESEARCH_SEQUENCE.index("PROMOTE_R1") < RESEARCH_SEQUENCE.index("TUNE_R2")
    assert RESEARCH_SEQUENCE.index("DIVERSITY_R1") < RESEARCH_SEQUENCE.index("PROMOTE_R2_R3")


def test_tuning_preserves_parent_lineage_and_trial_cap(tmp_path):
    trials = AutoMLSearch(tmp_path).tune_trials(
        [{"run_id": "synthetic-parent-a", "family": "ridge"},
         {"run_id": "synthetic-parent-b", "family": "lgbm"}],
        max_trials=2,
    )
    assert len(trials) == 2
    assert all(trial.parent_run_id == "synthetic-parent-a" for trial in trials)
    assert all(trial.profile == "R2" for trial in trials)


def test_ridge_sweep_is_real_evidence_namespaced_and_regularised(tmp_path):
    trials = AutoMLSearch(tmp_path).ridge_trials(profile="R1", max_trials=4)
    assert len(trials) == 4
    assert all(trial.run_id.startswith("ridge-real-ridge-") for trial in trials)
    assert [trial.params["alpha"] for trial in trials] == [1.0, 30.0, 300.0, 3_000.0]


def test_final_round_trials_are_shardable_and_seed_diverse(tmp_path):
    search = AutoMLSearch(tmp_path)
    first = search.final_trials(offset=0, max_trials=2)
    second = search.final_trials(offset=2, max_trials=2)
    assert len(first + second) == 4
    assert {trial.family for trial in first + second} == {"xgboost", "lgbm"}
    assert len({trial.run_id for trial in first + second}) == 4
