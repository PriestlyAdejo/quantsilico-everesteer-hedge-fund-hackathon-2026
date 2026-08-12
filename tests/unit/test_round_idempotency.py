"""RoundController restart / idempotency (synthetic feed, no real Everesteer)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from qs_everesteer.data.fingerprint import file_sha256
from qs_everesteer.data.synthetic import generate_synthetic_event_data
from qs_everesteer.event.adapter import EveresteerAdapter, SimulatedEventFeed
from qs_everesteer.live.rounds import RoundController
from qs_everesteer.state.research import load_research_state
from qs_everesteer.submission.mode import disarm_submissions
from qs_everesteer.submission.pipeline import QuotaController, SubmissionPipeline


def _prep_preds_from_live(live_path: Path, out: Path) -> Path:
    df = pd.read_parquet(live_path)
    ids = sorted(df["id"].astype(str).unique())
    pred = pd.DataFrame({"id": ids, "prediction": [0.5] * len(ids)})
    pred.to_parquet(out, index=False)
    return out


def test_simulated_feed_disconnect_reconnect(tmp_path):
    feed = SimulatedEventFeed(event_id="SYN-E", round_id="SYN-R1")
    assert feed.status.value == "LIVE"
    feed.disconnect()
    assert feed.current_round()["round"] is None
    feed.reconnect()
    assert feed.status.value == "LIVE"
    assert feed.current_round()["round"] == "SYN-R1"


def test_round_tick_idempotent_across_restart(tmp_path):
    feed = SimulatedEventFeed(event_id="SYN-E", round_id="SYN-R2")
    adapter = EveresteerAdapter(synthetic=True, feed=feed)
    # Generate synthetic live under the temp repo root.
    paths = generate_synthetic_event_data(tmp_path / "data" / "synthetic", n_live_ids=8, n_practice_ids=16)

    # First pull so we can build matching predictions.
    live_copy = tmp_path / "seed_live.parquet"
    live_copy.write_bytes(paths["live"].read_bytes())
    preds = _prep_preds_from_live(live_copy, tmp_path / "preds.parquet")
    expected_ids = pd.read_parquet(preds)["id"].astype(str).tolist()

    pipe = SubmissionPipeline(
        repo_root=tmp_path,
        adapter=adapter,
        quota=QuotaController(repo_root=tmp_path, explicit_cap=10, explicit_remaining=10),
    )
    ctrl = RoundController(
        repo_root=tmp_path,
        adapter=adapter,
        feed=feed,
        pipeline=pipe,
    )
    disarm_submissions(tmp_path)  # ensure DRY_RUN

    first = ctrl.tick(
        predictions_path=preds,
        expected_ids=expected_ids,
        candidate_id="champ-1",
        lane="practice",  # dry-run practice path; live lane would require ARMED
        force=True,
    )
    assert first.ok
    assert first.skipped is False or first.submission is not None
    key1 = (first.submission or {}).get("idempotency_key")
    assert key1

    # Simulate process restart: new controller, same ledger on disk.
    ctrl2 = RoundController(
        repo_root=tmp_path,
        adapter=EveresteerAdapter(synthetic=True, feed=feed),
        feed=feed,
        pipeline=SubmissionPipeline(
            repo_root=tmp_path,
            quota=QuotaController(repo_root=tmp_path, explicit_cap=10, explicit_remaining=10),
        ),
    )
    second = ctrl2.tick(
        predictions_path=preds,
        expected_ids=expected_ids,
        candidate_id="champ-1",
        lane="practice",
        force=True,
    )
    assert second.ok
    assert second.skipped is True
    assert "idempotent" in (second.skip_reason or "").lower() or second.submission is not None
    key2 = (second.submission or {}).get("idempotency_key") or (
        (second.submission or {}).get("prior") or {}
    ).get("key")
    # Same fingerprint + candidate + action ⇒ same key
    assert key2 == key1 or (second.submission or {}).get("idempotency_key") == key1

    state = load_research_state(tmp_path)
    assert state["round"] == "SYN-R2"


def test_disconnect_skips_without_fabricating(tmp_path):
    feed = SimulatedEventFeed(round_id="SYN-R3")
    feed.disconnect()
    ctrl = RoundController(
        repo_root=tmp_path,
        adapter=EveresteerAdapter(synthetic=True, feed=feed),
        feed=feed,
    )
    result = ctrl.tick()
    assert result.ok
    assert result.skipped
    assert result.skip_reason == "feed disconnected"
    assert result.submission is None


def test_fingerprint_change_allows_new_key(tmp_path):
    feed = SimulatedEventFeed(round_id="SYN-R4")
    adapter = EveresteerAdapter(synthetic=True, feed=feed)
    generate_synthetic_event_data(tmp_path / "data" / "synthetic", seed=1, n_live_ids=6)
    preds_a = tmp_path / "a.parquet"
    pd.DataFrame({"id": ["SYN-L-00000"], "prediction": [0.1]}).to_parquet(preds_a, index=False)

    # Bypass full ID coverage by not passing expected_ids; still need artefact present.
    pipe = SubmissionPipeline(
        repo_root=tmp_path,
        quota=QuotaController(repo_root=tmp_path, explicit_remaining=9, explicit_cap=9),
    )
    ctrl = RoundController(repo_root=tmp_path, adapter=adapter, feed=feed, pipeline=pipe)
    r1 = ctrl.tick(predictions_path=preds_a, candidate_id="c", lane="practice", force=True)
    assert r1.ok
    fp1 = ((r1.detail.get("fingerprint") or {}).get("content_sha256"))
    assert fp1

    # Mutate synthetic live source so next pull fingerprints differently.
    live_src = tmp_path / "data" / "synthetic" / "live.parquet"
    df = pd.read_parquet(live_src)
    df.loc[0, "feature_0001"] = float(df.loc[0, "feature_0001"]) + 99.0
    df.to_parquet(live_src, index=False)
    assert file_sha256(live_src) != fp1

    ctrl._last_fingerprint = None  # allow re-pull path past in-memory short-circuit
    r2 = ctrl.tick(predictions_path=preds_a, candidate_id="c", lane="practice", force=True)
    assert r2.ok
    fp2 = ((r2.detail.get("fingerprint") or {}).get("content_sha256"))
    assert fp2 != fp1
    assert (r2.submission or {}).get("idempotency_key") != (r1.submission or {}).get(
        "idempotency_key"
    )
