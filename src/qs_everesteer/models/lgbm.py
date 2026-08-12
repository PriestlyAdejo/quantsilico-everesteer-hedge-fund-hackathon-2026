"""LightGBM candidates; CPU is always the safe default."""
from __future__ import annotations

import os

from qs_everesteer.models.base import SklearnResearchModel


def lgbm_model(
    *, n_estimators: int = 200, learning_rate: float = 0.03,
    num_leaves: int = 31, reg_lambda: float = 1.0, reg_alpha: float = 0.1,
    feature_fraction: float = 0.8, seed: int = 7, use_gpu: bool | None = None,
    **kwargs,
) -> SklearnResearchModel:
    try:
        from lightgbm import LGBMRegressor
    except ImportError as exc:
        raise RuntimeError("lightgbm is optional and is not installed") from exc
    gpu = (
        os.getenv("QS_EVERESTEER_USE_GPU", "").lower() in {"1", "true", "yes"}
        if use_gpu is None else use_gpu
    )
    params = {
        "n_estimators": n_estimators, "learning_rate": learning_rate,
        "num_leaves": num_leaves, "reg_lambda": reg_lambda, "reg_alpha": reg_alpha,
        "feature_fraction": feature_fraction, "seed": seed, "use_gpu": gpu, **kwargs,
    }
    estimator = LGBMRegressor(
        n_estimators=n_estimators, learning_rate=learning_rate, num_leaves=num_leaves,
        reg_lambda=reg_lambda, reg_alpha=reg_alpha, feature_fraction=feature_fraction,
        random_state=seed, verbosity=-1, device_type="gpu" if gpu else "cpu", **kwargs,
    )
    return SklearnResearchModel(
        estimator, private_name="regularised_lgbm", family="boosting", params=params,
        metadata_extra={"device": "gpu_requested" if gpu else "cpu"},
    )


LGBMModel = lgbm_model
