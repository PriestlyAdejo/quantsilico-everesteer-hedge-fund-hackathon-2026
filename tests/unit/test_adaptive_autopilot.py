from pathlib import Path

import joblib

from qs_everesteer.autopilot.adaptive import AdaptiveCompetitionController, AdaptivePolicy
from qs_everesteer.fsutil import atomic_write_json


class FakeClient:
    def get_status(self):
        return {
            "event_status": "running", "uploads_remaining": 42,
            "cadence": {"phase": "round_2", "open_window": "round_2",
                        "seconds_until_next_phase": 100, "live_data_available": False,
                        "intake_fenced": False},
        }

    def get_models(self):
        return {"models": [{"id": "remote-1", "name": "candidate-one"}]}

    def get_submission_status(self):
        return {"submissions": []}

    def get_event_staking(self):
        return {"stake_window_open": False, "windows": []}

    def get_diagnostics_leaderboard(self, **kwargs):
        if kwargs.get("scoring_window") == "round_1":
            return {"entries": [{"is_self": True, "model_name": "candidate-one",
                                  "round_score": 0.7, "corr20": 0.08}]}
        return {"entries": [{"is_self": True, "model_name": "candidate-one",
                              "round_score": 0.4, "corr20": 0.05}]}


def _candidate(root: Path):
    run = root / "runs" / "experiments" / "run-one"
    model = root / "artifacts" / "models" / "run-one"
    run.mkdir(parents=True)
    model.mkdir(parents=True)
    data = root / "data" / "train.parquet"
    data.parent.mkdir(parents=True)
    data.touch()
    atomic_write_json(run / "run.json", {
        "status": "COMPLETED", "config": {"data_path": str(data)}
    })
    joblib.dump({"model": "synthetic-test"}, model / "model.joblib")
    atomic_write_json(model / "metadata.json", {
        "model_id": "run-one", "public_alias": "candidate-one",
        "private_name": "lgbm", "artefact_path": str(model / "model.joblib"),
    })


def test_reconcile_uses_official_scores_and_true_quota(tmp_path: Path):
    _candidate(tmp_path)
    controller = AdaptiveCompetitionController(tmp_path, client=FakeClient())
    state = controller.reconcile()
    assert state["uploads_remaining"] == 42
    assert state["champion"]["id"] == "run-one"
    assert state["champion"]["official_round_score"] == 0.4
    assert state["champion"]["latest_paid_round_score"] == 0.7


def test_auto_stake_requires_valid_bankroll_fraction():
    try:
        AdaptivePolicy(allow_auto_stake=True, stake_bankroll_fraction=1.1).validate()
    except ValueError as exc:
        assert "stake_bankroll_fraction" in str(exc)
    else:
        raise AssertionError("invalid bankroll fraction was accepted")


def test_auto_stake_weights_three_submitted_models_by_paid_score(tmp_path: Path):
    class StakingClient(FakeClient):
        def __init__(self):
            self.allocations = []

        def set_stake_allocation(self, model_name, *, amount_usdc, window):
            self.allocations.append((model_name, amount_usdc, window))
            return {"ok": True}

    client = StakingClient()
    client.get_diagnostics_leaderboard = lambda **kwargs: {
        "entries": [
            {"is_self": True, "model_name": "model-a", "round_score": 0.6},
            {"is_self": True, "model_name": "model-b", "round_score": 0.3},
            {"is_self": True, "model_name": "model-c", "round_score": 0.1},
        ]
    }
    controller = AdaptiveCompetitionController(
        tmp_path, client=client,
        policy=AdaptivePolicy(allow_auto_stake=True, stake_bankroll_fraction=0.5),
    )
    snapshot = {
        "round": "round_2",
        "staking": {"stake_window_open": True, "draft_window": "round_2",
                    "max_stakeable_micro": 50_000_000, "windows": []},
        "submissions": [
            {"model_id": name, "round": "round_2", "accepted": True}
            for name in ("model-a", "model-b", "model-c")
        ],
    }
    actions = controller._maybe_stake(snapshot)
    assert [row[0] for row in client.allocations] == ["model-a", "model-b", "model-c"]
    assert sum(float(row[1]) for row in client.allocations) == 25.0
    assert len(actions) == 3


def test_validation_attempt_ledger_survives_reconcile(tmp_path: Path):
    _candidate(tmp_path)
    controller = AdaptiveCompetitionController(tmp_path, client=FakeClient())
    controller.reconcile()
    controller._record_validation_attempt(
        "candidate-one", "run-one", {"upload_id": "u1", "status": "pending"}
    )
    state = controller.reconcile()
    assert state["validation_attempts"]["candidate-one"]["upload_id"] == "u1"


def test_live_round_limit_counts_already_accepted_submissions(tmp_path: Path):
    _candidate(tmp_path)
    client = FakeClient()
    client.get_submission_status = lambda: {
        "submissions": [
            {"model_id": f"candidate-{index}", "round": "round_2", "accepted": True}
            for index in range(4)
        ]
    }
    controller = AdaptiveCompetitionController(
        tmp_path,
        client=client,
        policy=AdaptivePolicy(allow_live_submit=True, max_live_models_per_round=4),
    )
    snapshot = controller.reconcile()
    assert controller._submit_open_round(snapshot) == []
