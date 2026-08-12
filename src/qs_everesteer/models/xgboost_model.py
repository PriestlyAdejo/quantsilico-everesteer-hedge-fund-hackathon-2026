"""Optional XGBoost model with conservative hardware detection."""
from __future__ import annotations

import os

from qs_everesteer.models.base import SklearnResearchModel


def gpu_requested() -> bool:
    return os.getenv("QS_EVERESTEER_USE_GPU", "").lower() in {"1", "true", "yes"}


def xgboost_model(
    *, n_estimators: int = 200, max_depth: int = 5, learning_rate: float = 0.03,
    seed: int = 7, use_gpu: bool | None = None, **kwargs
) -> SklearnResearchModel:
    try:
        from xgboost import XGBRegressor
    except ImportError as exc:
        raise RuntimeError("xgboost is optional and is not installed") from exc
    gpu = gpu_requested() if use_gpu is None else use_gpu
    params = {
        "n_estimators": n_estimators, "max_depth": max_depth,
        "learning_rate": learning_rate, "seed": seed, "use_gpu": gpu, **kwargs,
    }
    estimator = XGBRegressor(
        n_estimators=n_estimators, max_depth=max_depth, learning_rate=learning_rate,
        random_state=seed, tree_method="hist", device="cuda" if gpu else "cpu",
        n_jobs=-1, **kwargs,
    )
    return SklearnResearchModel(
        estimator, private_name="xgboost", family="boosting", params=params,
        metadata_extra={"device": "gpu_requested" if gpu else "cpu"},
    )


XGBoostModel = xgboost_model
