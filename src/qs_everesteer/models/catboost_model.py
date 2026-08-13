"""Optional CatBoost candidate using CatBoost's native CPU/GPU implementation."""
from __future__ import annotations

from qs_everesteer.models.base import SklearnResearchModel


def catboost_model(
    *, iterations: int = 200, depth: int = 6, learning_rate: float = 0.03,
    l2_leaf_reg: float = 3.0, seed: int = 7, use_gpu: bool = False, **kwargs,
) -> SklearnResearchModel:
    try:
        from catboost import CatBoostRegressor
    except ImportError as exc:
        raise RuntimeError(
            "catboost is unavailable; install the optional catboost package to run this family"
        ) from exc
    params = {
        "iterations": iterations, "depth": depth, "learning_rate": learning_rate,
        "l2_leaf_reg": l2_leaf_reg, "seed": seed, "use_gpu": use_gpu, **kwargs,
    }
    estimator = CatBoostRegressor(
        iterations=iterations, depth=depth, learning_rate=learning_rate,
        l2_leaf_reg=l2_leaf_reg, random_seed=seed,
        task_type="GPU" if use_gpu else "CPU", verbose=False, allow_writing_files=False,
        **kwargs,
    )
    return SklearnResearchModel(
        estimator, private_name="catboost", family="boosting", params=params,
        metadata_extra={"device": "gpu_requested" if use_gpu else "cpu"},
    )
