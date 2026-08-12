"""Generate visibly-synthetic Everesteer-like Parquet fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from qs_everesteer.paths import ensure_dir, find_repo_root, synthetic_data_dir

TARGET_COL = "target_everest_20"
ID_COL = "id"
EXPED_COL = "exped"
DEFAULT_N_FEATURES = 32


def feature_columns(n_features: int = DEFAULT_N_FEATURES) -> list[str]:
    return [f"feature_{i:04d}" for i in range(1, n_features + 1)]


def generate_synthetic_event_data(
    output_dir: str | Path | None = None,
    *,
    seed: int = 7,
    n_features: int = DEFAULT_N_FEATURES,
    n_practice_ids: int = 120,
    n_live_ids: int = 40,
    rows_per_exped: int = 4,
    n_expeds: int = 24,
    missingness: float = 0.03,
) -> dict[str, Path]:
    """
    Write train / validation / live Parquet under *output_dir*.

    - train: practice IDs with targets
    - validation: practice IDs with blank targets
    - live: disjoint live IDs with blank targets
    """
    out = Path(output_dir) if output_dir is not None else synthetic_data_dir(find_repo_root())
    ensure_dir(out)
    rng = np.random.default_rng(seed)

    practice_ids = [f"SYN-P-{i:05d}" for i in range(n_practice_ids)]
    live_ids = [f"SYN-L-{i:05d}" for i in range(n_live_ids)]
    assert not set(practice_ids) & set(live_ids)

    expeds = np.arange(n_expeds, dtype=np.int32)
    feats = feature_columns(n_features)

    train = _build_split(
        ids=practice_ids,
        expeds=expeds,
        rows_per_exped=rows_per_exped,
        feature_names=feats,
        rng=rng,
        with_target=True,
        missingness=missingness,
        lane="practice",
    )
    # Validation reuses practice IDs but blanks targets (prediction lane shape).
    validation = train.drop(columns=[TARGET_COL]).copy()
    validation[TARGET_COL] = np.nan
    # Resample a subset for a distinct validation file while keeping ID universe.
    val_ids = practice_ids[::2] or practice_ids
    validation = validation[validation[ID_COL].isin(val_ids)].reset_index(drop=True)

    live = _build_split(
        ids=live_ids,
        expeds=expeds,
        rows_per_exped=max(1, rows_per_exped // 2),
        feature_names=feats,
        rng=rng,
        with_target=False,
        missingness=missingness,
        lane="live",
    )

    paths = {
        "train": out / "train.parquet",
        "validation": out / "validation.parquet",
        "live": out / "live.parquet",
    }
    train.to_parquet(paths["train"], index=False)
    validation.to_parquet(paths["validation"], index=False)
    live.to_parquet(paths["live"], index=False)

    meta = {
        "synthetic": True,
        "seed": seed,
        "n_features": n_features,
        "practice_ids": n_practice_ids,
        "live_ids": n_live_ids,
        "target_column": TARGET_COL,
        "note": "SYNTHETIC_FIXTURE — not official Everesteer data",
    }
    (out / "manifest.json").write_text(
        json.dumps(meta, indent=2) + "\n",
        encoding="utf-8",
    )
    return paths


def write_failure_fixtures(out_dir: str | Path, *, seed: int = 11) -> dict[str, Path]:
    """
    Write small Parquet/CSV fixtures that should fail integrity / submission checks.

    Cases: leakage, duplicate IDs, wrong lane, missing/extra prediction IDs,
    schema mismatch.
    """
    out = ensure_dir(out_dir)
    rng = np.random.default_rng(seed)
    feats = feature_columns(8)
    base_ids = [f"SYN-P-{i:05d}" for i in range(20)]
    expeds = np.arange(4, dtype=np.int32)

    clean = _build_split(
        ids=base_ids,
        expeds=expeds,
        rows_per_exped=2,
        feature_names=feats,
        rng=rng,
        with_target=True,
        missingness=0.0,
        lane="practice",
    )

    paths: dict[str, Path] = {}

    # 1) Leakage: validation targets filled from train (should warn/fail).
    leakage = clean.copy()
    paths["leakage_validation"] = out / "leakage_validation.parquet"
    leakage.to_parquet(paths["leakage_validation"], index=False)

    # 2) Duplicate IDs within a prediction file.
    dup = clean[[ID_COL]].drop_duplicates().head(10).copy()
    dup["prediction"] = rng.normal(size=len(dup))
    dup = pd.concat([dup, dup.iloc[:3]], ignore_index=True)
    paths["duplicate_ids"] = out / "duplicate_ids.parquet"
    dup.to_parquet(paths["duplicate_ids"], index=False)

    # 3) Wrong lane: live IDs submitted into practice template.
    wrong = pd.DataFrame(
        {
            ID_COL: [f"SYN-L-{i:05d}" for i in range(10)],
            "prediction": rng.normal(size=10),
        }
    )
    paths["wrong_lane"] = out / "wrong_lane_predictions.parquet"
    wrong.to_parquet(paths["wrong_lane"], index=False)

    # 4) Missing / extra prediction IDs vs expected practice set.
    expected = set(base_ids)
    pred_ids = list(base_ids[2:]) + [f"SYN-EXTRA-{i:03d}" for i in range(3)]
    missing_extra = pd.DataFrame(
        {
            ID_COL: pred_ids,
            "prediction": rng.normal(size=len(pred_ids)),
        }
    )
    paths["missing_extra_ids"] = out / "missing_extra_prediction_ids.parquet"
    missing_extra.to_parquet(paths["missing_extra_ids"], index=False)
    (out / "expected_practice_ids.json").write_text(
        json.dumps(sorted(expected), indent=2) + "\n",
        encoding="utf-8",
    )

    # 5) Schema mismatch: renamed target / missing feature columns.
    bad_schema = clean.rename(columns={TARGET_COL: "target_wrong"}).drop(
        columns=feats[:3], errors="ignore"
    )
    paths["schema_mismatch"] = out / "schema_mismatch.parquet"
    bad_schema.to_parquet(paths["schema_mismatch"], index=False)

    return paths


def _build_split(
    *,
    ids: list[str],
    expeds: np.ndarray,
    rows_per_exped: int,
    feature_names: list[str],
    rng: np.random.Generator,
    with_target: bool,
    missingness: float,
    lane: str,
) -> pd.DataFrame:
    n_features = len(feature_names)
    rows: list[dict[str, Any]] = []
    # Weak linear weights + a few nonlinear interactions; time drift via exped.
    weights = rng.normal(0.0, 1.0, size=n_features)
    weights[n_features // 2 :] *= 0.05  # trailing features nearly redundant
    # Exact copies of early features later → redundancy.
    for id_ in ids:
        for exped in expeds:
            for _rep in range(rows_per_exped):
                x = rng.normal(0.0, 1.0, size=n_features).astype(np.float64)
                # Redundant features: copy + tiny noise.
                if n_features >= 8:
                    x[n_features - 1] = x[0] + rng.normal(0.0, 0.01)
                    x[n_features - 2] = x[1] + rng.normal(0.0, 0.01)
                # Time drift: shift mean with exped index.
                x += 0.02 * float(exped)
                row: dict[str, Any] = {ID_COL: id_, EXPED_COL: int(exped)}
                for j, name in enumerate(feature_names):
                    row[name] = float(x[j])
                if with_target:
                    linear = float(x @ weights)
                    nonlinear = 0.35 * float(x[0] * x[1]) + 0.2 * float(np.tanh(x[2]))
                    noise = float(rng.normal(0.0, 0.75))
                    drift = 0.05 * float(exped)
                    row[TARGET_COL] = linear + nonlinear + noise + drift
                else:
                    row[TARGET_COL] = np.nan
                rows.append(row)

    df = pd.DataFrame(rows)
    # Column order: id, exped, features..., target
    ordered = [ID_COL, EXPED_COL, *feature_names, TARGET_COL]
    df = df[ordered]

    if missingness > 0:
        feat_block = df[feature_names].to_numpy(copy=True)
        mask = rng.random(feat_block.shape) < missingness
        feat_block[mask] = np.nan
        df[feature_names] = feat_block

    # Marker column kept out of schema — synthetic provenance via ID prefix + manifest.
    df.attrs["synthetic_lane"] = lane
    return df
