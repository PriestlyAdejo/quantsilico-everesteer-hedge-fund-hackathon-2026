"""SubmissionGuard structured pass/fail checks."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from qs_everesteer.state.research import SubmissionMode
from qs_everesteer.submission.guard import SubmissionContext, SubmissionGuard


def _write_preds(path: Path, ids: list[str], values: list[float] | None = None) -> Path:
    vals = values if values is not None else [0.5] * len(ids)
    pd.DataFrame({"id": ids, "prediction": vals}).to_parquet(path, index=False)
    return path


def test_guard_passes_happy_path(tmp_path):
    ids = [f"SYN-P-{i:05d}" for i in range(5)]
    pred = _write_preds(tmp_path / "preds.parquet", ids)
    result = SubmissionGuard().validate(
        SubmissionContext(
            event_id="evt-1",
            event_snapshot_id="snap-1",
            round_id="R1",
            lane="practice",
            split_fingerprint="abc123",
            expected_split_fingerprint="abc123",
            candidate_id="cand-1",
            predictions_path=pred,
            expected_ids=ids,
            quota_remaining=3,
            quota_known=True,
            capabilities={"validation_available": True},
            mode=SubmissionMode.DRY_RUN,
        )
    )
    assert result.ok
    assert result.verdict.value == "PASS"
    assert not result.blocking_reasons


def test_guard_blocks_disabled_mode(tmp_path):
    ids = ["a", "b"]
    pred = _write_preds(tmp_path / "p.parquet", ids)
    result = SubmissionGuard().validate(
        SubmissionContext(
            event_id="e",
            round_id="r",
            lane="practice",
            split_fingerprint="fp",
            candidate_id="c",
            predictions_path=pred,
            expected_ids=ids,
            quota_remaining=1,
            quota_known=True,
            mode=SubmissionMode.DISABLED,
        )
    )
    assert not result.ok
    assert any("DISABLED" in r for r in result.blocking_reasons)


def test_guard_blocks_fingerprint_mismatch(tmp_path):
    ids = ["a"]
    pred = _write_preds(tmp_path / "p.parquet", ids)
    result = SubmissionGuard().validate(
        SubmissionContext(
            event_id="e",
            round_id="r",
            lane="practice",
            split_fingerprint="fp-a",
            expected_split_fingerprint="fp-b",
            candidate_id="c",
            predictions_path=pred,
            expected_ids=ids,
            quota_remaining=1,
            quota_known=True,
            mode=SubmissionMode.DRY_RUN,
        )
    )
    assert not result.ok
    assert any("fingerprint" in r.lower() for r in result.blocking_reasons)


def test_guard_blocks_id_coverage_and_bounds(tmp_path):
    pred = _write_preds(tmp_path / "p.parquet", ["a", "b"], [0.1, 1.5])
    result = SubmissionGuard().validate(
        SubmissionContext(
            event_id="e",
            round_id="r",
            lane="practice",
            split_fingerprint="fp",
            candidate_id="c",
            predictions_path=pred,
            expected_ids=["a", "b", "c"],
            quota_remaining=1,
            quota_known=True,
            mode=SubmissionMode.DRY_RUN,
        )
    )
    assert not result.ok
    joined = " ".join(result.blocking_reasons).lower()
    assert "coverage" in joined
    assert "bounds" in joined


def test_guard_unknown_quota_blocks_armed_allows_dry_run(tmp_path):
    ids = ["a"]
    pred = _write_preds(tmp_path / "p.parquet", ids)
    dry = SubmissionGuard().validate(
        SubmissionContext(
            event_id="e",
            round_id="r",
            lane="practice",
            split_fingerprint="fp",
            candidate_id="c",
            predictions_path=pred,
            expected_ids=ids,
            quota_known=False,
            quota_remaining=None,
            mode=SubmissionMode.DRY_RUN,
        )
    )
    assert dry.ok

    armed = SubmissionGuard().validate(
        SubmissionContext(
            event_id="e",
            round_id="r",
            lane="practice",
            split_fingerprint="fp",
            candidate_id="c",
            predictions_path=pred,
            expected_ids=ids,
            quota_known=False,
            quota_remaining=None,
            mode=SubmissionMode.ARMED,
            require_armed_for_live=False,
        )
    )
    assert not armed.ok
    assert any("UNKNOWN" in r for r in armed.blocking_reasons)


def test_live_lane_requires_armed(tmp_path):
    ids = ["a"]
    pred = _write_preds(tmp_path / "p.parquet", ids)
    result = SubmissionGuard().validate(
        SubmissionContext(
            event_id="e",
            round_id="r",
            lane="live",
            split_fingerprint="fp",
            candidate_id="c",
            predictions_path=pred,
            expected_ids=ids,
            quota_remaining=2,
            quota_known=True,
            capabilities={"live_available": True},
            mode=SubmissionMode.DRY_RUN,
        )
    )
    assert not result.ok
    assert any("ARMED" in r for r in result.blocking_reasons)
