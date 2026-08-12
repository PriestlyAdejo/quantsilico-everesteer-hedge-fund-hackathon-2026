"""Idempotency keys and ledger behaviour."""

from __future__ import annotations

import pandas as pd

from qs_everesteer.state.research import SubmissionMode, update_research_state
from qs_everesteer.submission.mode import arm_submissions, get_mode
from qs_everesteer.submission.pipeline import (
    IdempotencyLedger,
    PipelineRequest,
    QuotaController,
    SubmissionPipeline,
    make_idempotency_key,
)


def test_idempotency_key_stable_and_distinct():
    a = make_idempotency_key(
        event_id="e1",
        round_id="r1",
        split_fingerprint="fp1",
        candidate_id="c1",
        action="submit",
    )
    b = make_idempotency_key(
        event_id="e1",
        round_id="r1",
        split_fingerprint="fp1",
        candidate_id="c1",
        action="submit",
    )
    c = make_idempotency_key(
        event_id="e1",
        round_id="r1",
        split_fingerprint="fp2",
        candidate_id="c1",
        action="submit",
    )
    assert a == b
    assert a != c
    assert len(a) == 64


def test_ledger_record_and_get(tmp_path):
    ledger = IdempotencyLedger(tmp_path)
    key = make_idempotency_key(
        event_id="e",
        round_id="r",
        split_fingerprint="fp",
        candidate_id="c",
        action="submit",
    )
    assert ledger.get(key) is None
    ledger.record(key, {"status": "DRY_RUN_OK", "candidate_id": "c"})
    got = ledger.get(key)
    assert got is not None
    assert got["status"] == "DRY_RUN_OK"
    assert (tmp_path / "runs" / "state" / "idempotency.json").exists()


def test_pipeline_dry_run_is_idempotent(tmp_path):
    ids = [f"id-{i}" for i in range(3)]
    pred = tmp_path / "preds.parquet"
    pd.DataFrame({"id": ids, "prediction": [0.2, 0.4, 0.6]}).to_parquet(pred, index=False)

    # Default DRY_RUN; give explicit synthetic quota for clarity (not required for dry-run).
    update_research_state(
        lambda s: s["upload_budget"].update({"cap": 5, "live_remaining": 5, "practice_remaining": 5}),
        repo_root=tmp_path,
    )
    assert get_mode(tmp_path) is SubmissionMode.DRY_RUN

    pipe = SubmissionPipeline(
        repo_root=tmp_path,
        quota=QuotaController(repo_root=tmp_path, explicit_cap=5, explicit_remaining=5),
    )
    req = PipelineRequest(
        event_id="evt",
        round_id="R0",
        lane="practice",
        candidate_id="cand",
        split_fingerprint="fp-stable",
        event_snapshot_id="snap-1",
        expected_ids=ids,
        predictions_path=pred,
        capabilities={"validation_available": True},
    )
    first = pipe.run(req)
    assert first.ok
    assert first.reused_prior is False
    assert any(s.name == "SUBMIT" and s.status.value == "SKIPPED" for s in first.stages)

    second = pipe.run(req)
    assert second.ok
    assert second.reused_prior is True
    assert second.idempotency_key == first.idempotency_key


def test_pipeline_disabled_blocks(tmp_path):
    update_research_state(
        lambda s: s.__setitem__("submission_mode", "DISABLED"),
        repo_root=tmp_path,
    )
    pipe = SubmissionPipeline(repo_root=tmp_path)
    result = pipe.run(
        PipelineRequest(
            event_id="e",
            round_id="r",
            lane="practice",
            candidate_id="c",
            split_fingerprint="fp",
            predictions_path=tmp_path / "missing.parquet",
        )
    )
    assert not result.ok
    assert result.blocked_reason and "DISABLED" in result.blocked_reason


def test_armed_requires_quota_known(tmp_path):
    ids = ["a"]
    pred = tmp_path / "p.parquet"
    pd.DataFrame({"id": ids, "prediction": [0.5]}).to_parquet(pred, index=False)
    arm_submissions("snap-x", repo_root=tmp_path)

    calls: list[dict] = []

    def fake_submit(ctx):
        calls.append(ctx)
        return {"ok": True}

    pipe = SubmissionPipeline(
        repo_root=tmp_path,
        quota=QuotaController(repo_root=tmp_path),  # UNKNOWN
        submit_fn=fake_submit,
    )
    result = pipe.run(
        PipelineRequest(
            event_id="e",
            round_id="r",
            lane="practice",
            candidate_id="c",
            split_fingerprint="fp",
            event_snapshot_id="snap-x",
            expected_ids=ids,
            predictions_path=pred,
            capabilities={"validation_available": True},
        )
    )
    assert not result.ok
    assert not calls
    assert result.blocked_reason and "UNKNOWN" in result.blocked_reason
