"""Synthetic end-to-end live-event rehearsal via filesystem + API + domain modules."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from dashboard.backend.app.main import create_app
from qs_everesteer.data.audit import audit_dataset
from qs_everesteer.data.synthetic import generate_synthetic_event_data
from qs_everesteer.ensemble.blend import weighted
from qs_everesteer.event.adapter import EveresteerAdapter, SimulatedEventFeed
from qs_everesteer.experiments.racing import RacingScheduler
from qs_everesteer.experiments.runner import ExperimentRunner
from qs_everesteer.jobs.queue import enqueue, list_jobs
from qs_everesteer.live.rounds import RoundController
from qs_everesteer.selection.frontier import pareto_frontier
from qs_everesteer.state.research import load_research_state, update_research_state
from qs_everesteer.submission.pipeline import PipelineRequest, QuotaController, SubmissionPipeline


def test_live_event_rehearsal_happy_path(tmp_path: Path) -> None:
    # 1) Event disconnected
    feed = SimulatedEventFeed(event_id="SYN-REHEARSE", round_id="SYN-R1")
    feed.disconnect()
    assert feed.status.value == "DISCONNECTED"

    client = TestClient(create_app(tmp_path))
    update_research_state(
        lambda state: state.update(connection="DISCONNECTED", event_id="SYN-REHEARSE"),
        tmp_path,
    )
    status = client.get("/api/event-status").json()
    assert status["data"]["connection"] == "DISCONNECTED"

    # 2) Connect (synthetic)
    feed.reconnect()
    assert feed.status.value == "LIVE"
    update_research_state(
        lambda state: state.update(
            connection="LIVE",
            event_id="SYN-REHEARSE",
            event_phase="QUALIFYING",
            round="SYN-R1",
            round_status="open",
            scope="research:synthetic",
            meta={"source": "synthetic_rehearsal", "updated_at": "2026-01-01T00:00:00+00:00"},
        ),
        tmp_path,
    )
    assert client.get("/api/event-status").json()["data"]["connection"] == "LIVE"

    # 3) Data release + audit
    paths = generate_synthetic_event_data(
        tmp_path / "data" / "synthetic",
        n_features=4,
        n_practice_ids=6,
        n_live_ids=3,
        rows_per_exped=1,
        n_expeds=4,
        missingness=0,
    )
    audit = audit_dataset(paths["train"])
    assert audit.hard_failures == []
    audit_path = tmp_path / "data" / "synthetic" / "train_audit.json"
    audit_path.write_text(json.dumps(audit.to_dict()), encoding="utf-8")
    update_research_state(
        lambda state: state.update(data_fingerprint=audit.schema_sha256 or "synthetic"),
        tmp_path,
    )
    data_lab = client.get("/api/data-lab").json()
    assert data_lab["schemaVersion"] == 2
    assert data_lab["provenance"] == "SYNTHETIC_FIXTURE"
    assert len(data_lab["data"]["datasets"]) >= 1

    # 4) Baseline / race enqueue (API does not run work)
    race = client.post("/api/actions/race/start?profile=R0")
    assert race.status_code == 200
    assert race.json()["code"].startswith("JOB_QUEUED:")
    assert len(list_jobs(tmp_path)) == 1

    # 5) Tiny baseline train + race decision + frontier/champion
    run = ExperimentRunner(tmp_path).run(
        {
            "run_id": "rehearse-baseline",
            "data_path": str(paths["train"]),
            "model": {"name": "reference_lgbm", "params": {"n_estimators": 5}},
            "profile": "R0",
        }
    )
    assert run["status"] == "COMPLETED"
    metrics = json.loads((tmp_path / "runs/experiments/rehearse-baseline/metrics.json").read_text())
    outcomes = RacingScheduler().evaluate(
        [{"candidate_id": "rehearse-baseline", "score": metrics["score"]}],
        "R0",
    )
    frontier = pareto_frontier(
        [
            {
                "id": "rehearse-baseline",
                "score": metrics["score"],
                "runtime": run["runtime_seconds"],
            }
        ],
        [("score", "max"), ("runtime", "min")],
    )
    assert outcomes[0].next_stage == "R1"
    assert frontier
    update_research_state(
        lambda state: state.update(
            frontier=frontier,
            champion="rehearse-baseline",
            models=["rehearse-baseline", "challenger-a"],
            rounds=["SYN-R0", "SYN-R1"],
        ),
        tmp_path,
    )
    overview = client.get("/api/overview").json()
    assert overview["data"]["currentStage"] in {"ensemble", "submit", "research"}

    # 6) Ensemble preview
    blend = weighted(np.array([[0.25], [0.75]]))
    assert blend.shape == (2,)
    ens = client.post("/api/actions/build-ensemble?strategy=rank_average")
    assert ens.status_code == 200
    update_research_state(
        lambda state: state.update(ensemble={"members": ["rehearse-baseline"], "blend_id": "blend-reh"}),
        tmp_path,
    )
    assert client.get("/api/ensembles").json()["data"]["currentBlend"] == "blend-reh"

    # 7) Practice dry-run
    validation = pd.read_parquet(paths["validation"])
    ids = validation["id"].drop_duplicates().tolist()
    practice_pred = tmp_path / "practice.parquet"
    pd.DataFrame({"id": ids, "prediction": np.linspace(0.1, 0.9, len(ids))}).to_parquet(
        practice_pred, index=False
    )
    practice = SubmissionPipeline(repo_root=tmp_path).run(
        PipelineRequest(
            event_id="SYN-REHEARSE",
            round_id="SYN-R1",
            lane="practice",
            candidate_id="rehearse-baseline",
            split_fingerprint="synthetic-fingerprint",
            expected_ids=ids,
            predictions_path=practice_pred,
        )
    )
    assert practice.ok and practice.mode == "DRY_RUN"
    assert practice.upload is None

    # 8) Round open → live infer path → dry-run live submit
    update_research_state(
        lambda state: state.update(round_status="open", connection="LIVE", round="SYN-R1"),
        tmp_path,
    )
    live_ids = pd.read_parquet(paths["live"])["id"].drop_duplicates().astype(str).tolist()
    live_pred = tmp_path / "live_preds.parquet"
    pd.DataFrame({"id": live_ids, "prediction": [0.5] * len(live_ids)}).to_parquet(
        live_pred, index=False
    )
    adapter = EveresteerAdapter(synthetic=True, feed=feed)
    ctrl = RoundController(
        repo_root=tmp_path,
        adapter=adapter,
        feed=feed,
        pipeline=SubmissionPipeline(
            repo_root=tmp_path,
            adapter=adapter,
            quota=QuotaController(repo_root=tmp_path, explicit_cap=10, explicit_remaining=10),
        ),
    )
    tick = ctrl.tick(
        predictions_path=live_pred,
        expected_ids=live_ids,
        candidate_id="rehearse-baseline",
        lane="practice",
        force=True,
    )
    assert tick.ok
    assert tick.connection == "LIVE"
    assert "submit" in tick.stages

    # 9) Leaderboard / standings update (local evidence; no invented official ranks)
    update_research_state(
        lambda state: state.update(
            external_rank=None,
            live_evidence={
                "SYN-R1": {
                    "split_fingerprint": tick.detail.get("fingerprint", {}).get("content_sha256"),
                    "standing_note": "SYNTHETIC — no official leaderboard numbers",
                }
            },
        ),
        tmp_path,
    )
    board = client.get("/api/leaderboard").json()
    assert board["schemaVersion"] == 2
    assert len(board["data"]["roundModelMatrix"]) == 4  # 2 models × 2 rounds

    # 10) Round close
    update_research_state(
        lambda state: state.update(round_status="closed", time_remaining_seconds=0),
        tmp_path,
    )
    room = client.get("/api/round-room").json()
    assert room["data"]["roundStatus"] == "closed"
    assert room["data"]["submissionMode"] == "DRY_RUN"
    assert room["data"]["emergency"]["champion"] == "rehearse-baseline"

    state = load_research_state(tmp_path)
    assert state["connection"] == "LIVE"
    assert state["champion"] == "rehearse-baseline"
    assert enqueue("INFER", {"note": "post-close"}, repo_root=tmp_path, name="noop")
