from __future__ import annotations

from pathlib import Path

import pandas as pd

from qs_everesteer.data.audit import IntegrityLevel, audit_dataset, compare_train_val_schema
from qs_everesteer.data.fingerprint import file_sha256, fingerprint_dataset, schema_fingerprint
from qs_everesteer.data.synthetic import (
    EXPED_COL,
    ID_COL,
    TARGET_COL,
    generate_synthetic_event_data,
    write_failure_fixtures,
)


def test_generate_synthetic_splits_and_audit(tmp_path: Path):
    paths = generate_synthetic_event_data(
        tmp_path,
        seed=7,
        n_features=16,
        n_practice_ids=40,
        n_live_ids=12,
        rows_per_exped=2,
        n_expeds=6,
    )
    assert set(paths) == {"train", "validation", "live"}
    train = pd.read_parquet(paths["train"])
    val = pd.read_parquet(paths["validation"])
    live = pd.read_parquet(paths["live"])

    assert ID_COL in train.columns and EXPED_COL in train.columns
    assert TARGET_COL in train.columns
    assert train[TARGET_COL].notna().all()
    assert val[TARGET_COL].isna().all()
    assert live[TARGET_COL].isna().all()

    practice_ids = set(train[ID_COL].unique())
    live_ids = set(live[ID_COL].unique())
    assert practice_ids.isdisjoint(live_ids)
    assert all(str(i).startswith("SYN-") for i in practice_ids | live_ids)

    # Multiple rows per id.
    assert train.groupby(ID_COL).size().max() > 1

    audit = audit_dataset(paths["train"])
    assert audit.rows == len(train)
    assert audit.integrity in {IntegrityLevel.PASS, IntegrityLevel.WARN}
    assert audit.target_available is True
    assert audit.exped_count == 6
    assert len(audit.feature_columns) == 16
    assert not audit.hard_failures

    val_audit = audit_dataset(paths["validation"])
    assert val_audit.target_available is False

    cmp = compare_train_val_schema(paths["train"], paths["validation"])
    assert cmp["integrity"] in {"pass", "warn"}
    assert not cmp["missing_in_validation"]
    assert not cmp["extra_in_validation"]


def test_fingerprint_stable(tmp_path: Path):
    paths = generate_synthetic_event_data(tmp_path, seed=3, n_features=8, n_practice_ids=10, n_live_ids=4)
    fp1 = fingerprint_dataset(paths["train"])
    fp2 = fingerprint_dataset(paths["train"])
    assert fp1["content_sha256"] == fp2["content_sha256"] == file_sha256(paths["train"])
    df = pd.read_parquet(paths["train"])
    assert fp1["schema_sha256"] == schema_fingerprint(df)


def test_failure_fixtures_written(tmp_path: Path):
    paths = write_failure_fixtures(tmp_path / "failures")
    assert "leakage_validation" in paths
    assert "duplicate_ids" in paths
    assert "wrong_lane" in paths
    assert "missing_extra_ids" in paths
    assert "schema_mismatch" in paths
    for p in paths.values():
        assert p.is_file()

    bad = audit_dataset(paths["schema_mismatch"])
    # Missing feature columns / wrong target name → not a clean Everesteer schema.
    assert bad.integrity in {IntegrityLevel.WARN, IntegrityLevel.FAIL}
    assert TARGET_COL not in pd.read_parquet(paths["schema_mismatch"]).columns
