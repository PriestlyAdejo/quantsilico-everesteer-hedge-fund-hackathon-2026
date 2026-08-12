"""Failure drills: dashboard kill, idempotent restart, reconnect provenance."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from dashboard.backend.app.main import create_app
from dashboard.backend.app.services.console import ConsoleService
from qs_everesteer.data.synthetic import generate_synthetic_event_data
from qs_everesteer.event.adapter import ConnectionStatus, EveresteerAdapter, SimulatedEventFeed
from qs_everesteer.jobs.model import JobStatus
from qs_everesteer.jobs.queue import enqueue, load_job
from qs_everesteer.jobs.worker import run_job_sync
from qs_everesteer.live.rounds import RoundController
from qs_everesteer.state.research import load_research_state, update_research_state
from qs_everesteer.submission.mode import disarm_submissions
from qs_everesteer.submission.pipeline import QuotaController, SubmissionPipeline


def test_dashboard_context_kill_job_continues_and_state_survives(tmp_path: Path) -> None:
    update_research_state(
        lambda state: state.update(
            connection="LIVE",
            champion="survives-kill",
            event_id="SYN-KILL",
            meta={"source": "failure_drill", "updated_at": None},
        ),
        tmp_path,
    )
    client = TestClient(create_app(tmp_path))
    assert client.get("/api/event-status").json()["data"]["champion"] == "survives-kill"

    job_id = enqueue(
        "TRAIN",
        {"sleep_seconds": 0.05, "note": "continues after dashboard close"},
        repo_root=tmp_path,
        name="post-dashboard-train",
    )

    # Kill / stop dashboard HTTP context while the job continues via run_job_sync.
    client.close()
    del client

    done = run_job_sync(job_id, tmp_path)
    assert done.status == JobStatus.DONE
    assert done.payload.get("result", {}).get("ok") is True

    state = load_research_state(tmp_path)
    assert state["champion"] == "survives-kill"
    assert state["connection"] == "LIVE"
    assert load_job(job_id, tmp_path).status == JobStatus.DONE

    # Fresh console still reads surviving research state.
    revived = TestClient(create_app(tmp_path))
    assert revived.get("/api/event-status").json()["data"]["champion"] == "survives-kill"


def test_autopilot_round_restart_does_not_duplicate_submissions(tmp_path: Path) -> None:
    feed = SimulatedEventFeed(event_id="SYN-IDEM", round_id="SYN-R-IDEM")
    adapter = EveresteerAdapter(synthetic=True, feed=feed)
    paths = generate_synthetic_event_data(
        tmp_path / "data" / "synthetic",
        n_live_ids=6,
        n_practice_ids=10,
        n_features=3,
        rows_per_exped=1,
        n_expeds=3,
        missingness=0,
    )
    live_ids = pd.read_parquet(paths["live"])["id"].astype(str).drop_duplicates().tolist()
    preds = tmp_path / "preds.parquet"
    pd.DataFrame({"id": live_ids, "prediction": [0.4] * len(live_ids)}).to_parquet(
        preds, index=False
    )

    pipe = SubmissionPipeline(
        repo_root=tmp_path,
        adapter=adapter,
        quota=QuotaController(repo_root=tmp_path, explicit_cap=8, explicit_remaining=8),
    )
    ctrl = RoundController(
        repo_root=tmp_path,
        adapter=adapter,
        feed=feed,
        pipeline=pipe,
    )
    disarm_submissions(tmp_path)
    update_research_state(lambda state: state.update(autopilot_active=True), tmp_path)

    first = ctrl.tick(
        predictions_path=preds,
        expected_ids=live_ids,
        candidate_id="champ-idem",
        lane="practice",
        force=True,
    )
    assert first.ok
    key1 = (first.submission or {}).get("idempotency_key")
    assert key1

    # Autopilot / process restart: new controller, same ledger.
    ctrl2 = RoundController(
        repo_root=tmp_path,
        adapter=EveresteerAdapter(synthetic=True, feed=feed),
        feed=feed,
        pipeline=SubmissionPipeline(
            repo_root=tmp_path,
            quota=QuotaController(repo_root=tmp_path, explicit_cap=8, explicit_remaining=8),
        ),
    )
    second = ctrl2.tick(
        predictions_path=preds,
        expected_ids=live_ids,
        candidate_id="champ-idem",
        lane="practice",
        force=True,
    )
    assert second.ok
    assert second.skipped is True
    key2 = (second.submission or {}).get("idempotency_key") or (
        (second.submission or {}).get("prior") or {}
    ).get("key")
    assert key2 == key1 or (second.submission or {}).get("idempotency_key") == key1


def test_simulated_feed_reconnect_keeps_live_provenance(tmp_path: Path) -> None:
    feed = SimulatedEventFeed(event_id="SYN-RECONN", round_id="SYN-R-RECONN")
    assert feed.status is ConnectionStatus.LIVE

    feed.disconnect()
    assert feed.status is ConnectionStatus.DISCONNECTED
    assert feed.current_round()["connection"] == "DISCONNECTED"

    # Hold on RECONNECTING so the intermediate state is observable.
    assert feed.reconnect(settle=False) is ConnectionStatus.RECONNECTING
    assert feed.current_round()["connection"] == "RECONNECTING"
    assert feed.settle() is ConnectionStatus.LIVE
    assert feed.current_round()["connection"] == "LIVE"

    service = ConsoleService(tmp_path)
    seen: list[str] = []
    for connection in ("DISCONNECTED", "RECONNECTING", "LIVE"):
        update_research_state(
            lambda state, conn=connection: state.update(
                connection=conn,
                event_id="SYN-RECONN",
                round="SYN-R-RECONN",
                meta={"source": "live_adapter", "updated_at": None},
            ),
            tmp_path,
        )
        envelope = service.event_status()
        seen.append(envelope.data.connection.value)
        # Live ConsoleService path — never DemoDataSource SYNTHETIC_FIXTURE fixtures.
        assert envelope.provenance.value != "SYNTHETIC_FIXTURE"
        assert "preview" not in envelope.source.lower()
        assert "Local research store" not in envelope.source

    assert seen == ["DISCONNECTED", "RECONNECTING", "LIVE"]
    room = service.round_room()
    assert room.provenance.value == "OFFICIAL_EVENT_STATE"
    assert room.data.live_feed.value == "LIVE"
