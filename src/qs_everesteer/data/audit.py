"""Dataset integrity audit for Everesteer-like tabular files."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

import pandas as pd

from qs_everesteer.data.fingerprint import schema_fingerprint
from qs_everesteer.data.synthetic import EXPED_COL, ID_COL, TARGET_COL, feature_columns


class IntegrityLevel(StrEnum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass
class DatasetAudit:
    path: Path
    rows: int
    columns: int
    id_column: str | None
    time_group: str | None
    target_columns: list[str]
    feature_columns: list[str]
    exped_count: int
    duplicate_ids: int
    missingness: dict[str, float]
    memory_bytes_estimate: int
    target_available: bool
    integrity: IntegrityLevel
    schema_sha256: str
    warnings: list[str] = field(default_factory=list)
    hard_failures: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "rows": self.rows,
            "columns": self.columns,
            "id_column": self.id_column,
            "time_group": self.time_group,
            "target_columns": list(self.target_columns),
            "feature_columns": list(self.feature_columns),
            "exped_count": self.exped_count,
            "duplicate_ids": self.duplicate_ids,
            "missingness": dict(self.missingness),
            "memory_bytes_estimate": self.memory_bytes_estimate,
            "target_available": self.target_available,
            "integrity": self.integrity.value,
            "schema_sha256": self.schema_sha256,
            "warnings": list(self.warnings),
            "hard_failures": list(self.hard_failures),
        }


def audit_dataset(path: str | Path) -> DatasetAudit:
    """Run structural integrity checks on a Parquet/CSV dataset."""
    p = Path(path)
    warnings: list[str] = []
    hard_failures: list[str] = []

    if not p.exists():
        return DatasetAudit(
            path=p,
            rows=0,
            columns=0,
            id_column=None,
            time_group=None,
            target_columns=[],
            feature_columns=[],
            exped_count=0,
            duplicate_ids=0,
            missingness={},
            memory_bytes_estimate=0,
            target_available=False,
            integrity=IntegrityLevel.FAIL,
            schema_sha256="",
            warnings=[],
            hard_failures=[f"file does not exist: {p}"],
        )

    try:
        df = _read_frame(p)
    except Exception as exc:  # noqa: BLE001 — surface as audit failure
        return DatasetAudit(
            path=p.resolve(),
            rows=0,
            columns=0,
            id_column=None,
            time_group=None,
            target_columns=[],
            feature_columns=[],
            exped_count=0,
            duplicate_ids=0,
            missingness={},
            memory_bytes_estimate=0,
            target_available=False,
            integrity=IntegrityLevel.FAIL,
            schema_sha256="",
            warnings=[],
            hard_failures=[f"failed to read dataset: {exc}"],
        )

    cols = [str(c) for c in df.columns]
    id_column = ID_COL if ID_COL in df.columns else None
    time_group = EXPED_COL if EXPED_COL in df.columns else None
    target_cols = [c for c in cols if c.startswith("target_")]
    feat_cols = [c for c in cols if c.startswith("feature_")]

    if id_column is None:
        hard_failures.append(f"missing required id column '{ID_COL}'")
    if time_group is None:
        warnings.append(f"missing exped/time-group column '{EXPED_COL}'")
    if not feat_cols:
        hard_failures.append("no feature_* columns found")

    expected_feats = feature_columns(len(feat_cols)) if feat_cols else []
    if feat_cols and feat_cols != expected_feats[: len(feat_cols)]:
        # Allow non-contiguous only as warning; exact Everesteer pads are 0001..N.
        if feat_cols != sorted(feat_cols):
            warnings.append("feature_* columns are not sorted")

    duplicate_ids = 0
    if id_column is not None:
        duplicate_ids = int(df[id_column].duplicated().sum())
        # Multiple rows per id/exped is expected; duplicate exact (id, exped) is worse.
        if time_group is not None and {id_column, time_group}.issubset(df.columns):
            dup_keys = int(df.duplicated(subset=[id_column, time_group]).sum())
            if dup_keys:
                warnings.append(f"duplicate (id, exped) rows: {dup_keys}")
        elif duplicate_ids:
            warnings.append(f"duplicate id values: {duplicate_ids}")

    missingness: dict[str, float] = {}
    for c in feat_cols + target_cols:
        rate = float(df[c].isna().mean()) if len(df) else 0.0
        missingness[c] = rate
    feat_miss = [missingness[c] for c in feat_cols]
    if feat_miss and max(feat_miss) > 0.25:
        warnings.append(f"high feature missingness (max={max(feat_miss):.2%})")
    if feat_miss and max(feat_miss) > 0.75:
        hard_failures.append(f"extreme feature missingness (max={max(feat_miss):.2%})")

    target_available = False
    if TARGET_COL in df.columns:
        target_available = bool(df[TARGET_COL].notna().any())
        if df[TARGET_COL].isna().all():
            warnings.append(f"'{TARGET_COL}' present but entirely blank")
    elif not target_cols:
        warnings.append("no target_* columns present")

    exped_count = 0
    if time_group is not None:
        exped_count = int(df[time_group].nunique(dropna=True))

    if len(df) == 0:
        hard_failures.append("dataset has zero rows")

    mem = int(df.memory_usage(deep=True).sum())
    integrity = _integrity(warnings, hard_failures)

    return DatasetAudit(
        path=p.resolve(),
        rows=int(len(df)),
        columns=int(df.shape[1]),
        id_column=id_column,
        time_group=time_group,
        target_columns=target_cols,
        feature_columns=feat_cols,
        exped_count=exped_count,
        duplicate_ids=duplicate_ids,
        missingness=missingness,
        memory_bytes_estimate=mem,
        target_available=target_available,
        integrity=integrity,
        schema_sha256=schema_fingerprint(df),
        warnings=warnings,
        hard_failures=hard_failures,
    )


def compare_train_val_schema(
    train_path: str | Path,
    val_path: str | Path,
) -> dict[str, Any]:
    """Compare train vs validation column names/dtypes (ignoring target nullability)."""
    train = audit_dataset(train_path)
    val = audit_dataset(val_path)
    train_df = _read_frame(train_path)
    val_df = _read_frame(val_path)

    train_cols = [(str(c), str(train_df[c].dtype)) for c in train_df.columns]
    val_cols = [(str(c), str(val_df[c].dtype)) for c in val_df.columns]
    train_names = [c for c, _ in train_cols]
    val_names = [c for c, _ in val_cols]

    missing_in_val = [c for c in train_names if c not in val_names]
    extra_in_val = [c for c in val_names if c not in train_names]
    dtype_mismatches: list[dict[str, str]] = []
    for name in set(train_names) & set(val_names):
        td = str(train_df[name].dtype)
        vd = str(val_df[name].dtype)
        if td != vd:
            # float64 vs float32 for blank targets is a soft warning, not hard fail.
            dtype_mismatches.append({"column": name, "train": td, "validation": vd})

    hard = bool(missing_in_val or extra_in_val)
    warn = bool(dtype_mismatches)
    level = IntegrityLevel.FAIL if hard else (IntegrityLevel.WARN if warn else IntegrityLevel.PASS)

    return {
        "train": train.to_dict(),
        "validation": val.to_dict(),
        "missing_in_validation": missing_in_val,
        "extra_in_validation": extra_in_val,
        "dtype_mismatches": dtype_mismatches,
        "schema_match": train.schema_sha256 == val.schema_sha256,
        "integrity": level.value,
    }


def _integrity(warnings: list[str], hard_failures: list[str]) -> IntegrityLevel:
    if hard_failures:
        return IntegrityLevel.FAIL
    if warnings:
        return IntegrityLevel.WARN
    return IntegrityLevel.PASS


def _read_frame(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".parquet":
        return pd.read_parquet(p)
    if suffix in {".csv", ".tsv"}:
        sep = "\t" if suffix == ".tsv" else ","
        return pd.read_csv(p, sep=sep)
    raise ValueError(f"unsupported dataset format: {p}")
