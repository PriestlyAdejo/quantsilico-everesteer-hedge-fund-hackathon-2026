"""Matched public-synthetic backend benchmarks and geometry evidence."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import numpy as np
import psutil
from scipy.stats import spearmanr

from qs_everesteer.fsutil import atomic_write_json, read_json
from qs_everesteer.hardware.probe import probe_hardware
from qs_everesteer.paths import ensure_dir, find_repo_root


def run_matched_benchmark(
    profile: str = "matched", repo_root: str | Path | None = None
) -> dict[str, Any]:
    """Benchmark identical synthetic XGBoost work on CPU and CUDA when usable."""
    root = Path(repo_root) if repo_root is not None else find_repo_root()
    rows = 1024 if profile == "tiny" else 4096
    features = 24 if profile == "tiny" else 48
    rng = np.random.default_rng(20260813)
    x = rng.normal(size=(rows, features)).astype(np.float32)
    weights = rng.normal(size=features).astype(np.float32)
    y = (x @ weights + rng.normal(scale=0.5, size=rows)).astype(np.float32)
    split = max(64, int(rows * 0.8))
    x_train, x_valid = x[:split], x[split:]
    y_train, y_valid = y[:split], y[split:]
    hardware = probe_hardware()

    records = [
        _xgboost_trial("LOCAL_CPU", x_train, y_train, x_valid, y_valid, device="cpu")
    ]
    if hardware.gpu_available:
        records.append(
            _xgboost_trial("LOCAL_NATIVE_GPU", x_train, y_train, x_valid, y_valid, device="cuda")
        )
    payload = {
        "profile": profile,
        "synthetic": True,
        "public_safe": True,
        "rows": rows,
        "features": features,
        "family": "xgboost",
        "records": records,
        "note": "Matched synthetic canary; not competition-score evidence",
    }
    out = ensure_dir(root / "runs" / "benchmarks") / "latest.json"
    atomic_write_json(out, payload)
    return {**payload, "path": str(out)}


def _xgboost_trial(
    lane: str,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_valid: np.ndarray,
    y_valid: np.ndarray,
    *,
    device: str,
) -> dict[str, Any]:
    from xgboost import XGBRegressor
    from xgboost.core import XGBoostError

    params = {
        "n_estimators": 40,
        "max_depth": 4,
        "learning_rate": 0.05,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "random_state": 42,
        "n_jobs": 2,
        "device": device,
        "tree_method": "hist",
    }
    process = psutil.Process()
    rss_before = process.memory_info().rss
    try:
        warm = XGBRegressor(**{**params, "n_estimators": 2})
        warm_start = time.perf_counter()
        warm.fit(x_train[:256], y_train[:256])
        warmup = time.perf_counter() - warm_start

        model = XGBRegressor(**params)
        start = time.perf_counter()
        model.fit(x_train, y_train)
        prediction = np.asarray(model.predict(x_valid), dtype=float)
        elapsed = time.perf_counter() - start
        rho = float(spearmanr(prediction, y_valid).statistic)
        if not np.isfinite(prediction).all() or not np.isfinite(rho):
            raise ValueError("benchmark produced non-finite output")
        return {
            "lane": lane,
            "status": "PASSED",
            "warmup_seconds": warmup,
            "steady_state_seconds": elapsed,
            "rows_per_second": len(x_train) / elapsed,
            "peak_rss_bytes_lower_bound": max(rss_before, process.memory_info().rss),
            "valid_spearman": rho,
        }
    except (ImportError, RuntimeError, ValueError, XGBoostError) as exc:
        return {
            "lane": lane,
            "status": "FAILED",
            "error": f"{type(exc).__name__}: {exc}",
        }


def autotune_from_latest(repo_root: str | Path | None = None) -> dict[str, Any]:
    """Persist the fastest passing lane; refuse when matched evidence is absent."""
    root = Path(repo_root) if repo_root is not None else find_repo_root()
    source = root / "runs" / "benchmarks" / "latest.json"
    if not source.exists():
        return {"status": "BLOCKED", "reason": "matched benchmark evidence is missing"}
    payload = read_json(source)
    passing = [row for row in payload.get("records", []) if row.get("status") == "PASSED"]
    if not passing:
        return {"status": "BLOCKED", "reason": "no benchmark lane passed"}
    winner = min(passing, key=lambda row: float(row["steady_state_seconds"]))
    result = {
        "status": "SELECTED",
        "family": payload.get("family"),
        "profile": payload.get("profile"),
        "lane": winner["lane"],
        "steady_state_seconds": winner["steady_state_seconds"],
        "source": str(source),
        "synthetic": True,
    }
    atomic_write_json(source.with_name("autotune.json"), result)
    return result


def latest_lane_passed(lane: str, repo_root: str | Path | None = None) -> bool:
    root = Path(repo_root) if repo_root is not None else find_repo_root()
    source = root / "runs" / "benchmarks" / "latest.json"
    if not source.exists():
        return False
    try:
        payload = read_json(source)
    except (OSError, ValueError, TypeError):
        return False
    return any(
        row.get("lane") == lane and row.get("status") == "PASSED"
        for row in payload.get("records", [])
    )
