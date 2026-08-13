"""Reproducible blending strategies and blend manifests."""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, Ridge

from qs_everesteer.fsutil import atomic_write_json


def _matrix(predictions) -> tuple[np.ndarray, list[str]]:
    if isinstance(predictions, pd.DataFrame):
        return predictions.to_numpy(dtype=float), [str(c) for c in predictions.columns]
    if isinstance(predictions, dict):
        names = list(predictions)
        return np.column_stack([predictions[name] for name in names]), names
    array = np.asarray(predictions, dtype=float)
    if array.ndim == 1:
        array = array[:, None]
    return array, [str(i) for i in range(array.shape[1])]


def rank_average(predictions):
    matrix, _ = _matrix(predictions)
    ranks = np.column_stack(
        [pd.Series(matrix[:, i]).rank(pct=True, method="average") for i in range(matrix.shape[1])]
    )
    return np.nanmean(ranks, axis=1)


def weighted(predictions, weights=None):
    matrix, _ = _matrix(predictions)
    weights = np.ones(matrix.shape[1]) if weights is None else np.asarray(weights, dtype=float)
    if len(weights) != matrix.shape[1] or np.sum(np.abs(weights)) == 0:
        raise ValueError("weights must match prediction columns and have non-zero sum")
    weights = weights / weights.sum()
    return np.average(matrix, axis=1, weights=weights)


def greedy_forward(
    predictions, y_true, scorer: Callable[[Any, Any], Any], *, max_members: int | None = None
) -> dict[str, Any]:
    matrix, names = _matrix(predictions)
    remaining, selected, history = list(range(matrix.shape[1])), [], []
    limit = max_members or matrix.shape[1]
    best_score = float("-inf")
    while remaining and len(selected) < limit:
        trials = []
        for index in remaining:
            candidate = np.mean(matrix[:, selected + [index]], axis=1)
            raw = scorer(y_true, candidate)
            value = float(raw.value if hasattr(raw, "value") else raw)
            trials.append((value, index))
        score_value, winner = max(trials)
        if selected and score_value <= best_score:
            break
        selected.append(winner)
        remaining.remove(winner)
        history.append({"member_id": names[winner], "score": score_value, "marginal_contribution": score_value - best_score if np.isfinite(best_score) else None})
        best_score = score_value
    weights = [1 / len(selected) if i in selected else 0.0 for i in range(matrix.shape[1])]
    return {"prediction": weighted(matrix, weights), "member_ids": [names[i] for i in selected], "weights": weights, "score": best_score, "history": history}


def diversity_aware(
    predictions, y_true, scorer: Callable[[Any, Any], Any], *, diversity_weight: float = 0.05,
    max_members: int | None = None,
) -> dict[str, Any]:
    matrix, names = _matrix(predictions)
    selected, remaining = [], list(range(matrix.shape[1]))
    history = []
    while remaining and len(selected) < (max_members or matrix.shape[1]):
        trials = []
        for index in remaining:
            raw = scorer(y_true, np.mean(matrix[:, selected + [index]], axis=1))
            score_value = float(raw.value if hasattr(raw, "value") else raw)
            corr = max(
                [abs(float(np.corrcoef(matrix[:, index], matrix[:, j])[0, 1])) for j in selected]
                or [0.0]
            )
            trials.append((score_value + diversity_weight * (1 - corr), score_value, corr, index))
        utility, score_value, corr, winner = max(trials)
        if selected and utility <= history[-1]["utility"]:
            break
        selected.append(winner)
        remaining.remove(winner)
        history.append({"member_id": names[winner], "score": score_value, "correlation": corr, "utility": utility})
    weights = [1 / len(selected) if i in selected else 0.0 for i in range(matrix.shape[1])]
    return {"prediction": weighted(matrix, weights), "member_ids": [names[i] for i in selected], "weights": weights, "history": history}


def ridge_oof_stack(
    predictions, y_true, groups, *, alpha: float = 1.0, non_negative: bool = False,
) -> dict[str, Any]:
    """Fit a temporal cross-fitted stacker using only base-model OOF predictions."""
    matrix, names = _matrix(predictions)
    target = np.asarray(y_true, dtype=float)
    exped = np.asarray(groups)
    if len(matrix) != len(target) or len(target) != len(exped):
        raise ValueError("predictions, target, and groups must have equal row counts")
    if matrix.shape[1] < 2:
        raise ValueError("stacking requires at least two OOF candidates")
    if not np.isfinite(matrix).all() or not np.isfinite(target).all():
        raise ValueError("stacking inputs must be finite")
    unique = np.sort(pd.unique(exped))
    if len(unique) < 3:
        raise ValueError("temporal stacking requires at least three exped groups")
    meta_oof = np.full(len(target), np.nan)
    # Expanding splits: every meta prediction is from strictly earlier expeds.
    for split in range(2, len(unique)):
        train = np.isin(exped, unique[:split])
        valid = exped == unique[split]
        estimator = LinearRegression(positive=True) if non_negative else Ridge(alpha=alpha)
        estimator.fit(matrix[train], target[train])
        meta_oof[valid] = estimator.predict(matrix[valid])
    scored = np.isfinite(meta_oof)
    if not scored.any():
        raise ValueError("temporal stacker produced no cross-fitted rows")
    final = LinearRegression(positive=True) if non_negative else Ridge(alpha=alpha)
    final.fit(matrix, target)
    return {
        "prediction": meta_oof,
        "member_ids": names,
        "weights": np.asarray(final.coef_, dtype=float).tolist(),
        "intercept": float(final.intercept_),
        "scored_rows": int(scored.sum()),
        "total_rows": len(target),
        "method": "non_negative_oof" if non_negative else "ridge_oof",
    }


def greedy_diverse_blend(oof_predictions, scorer, y_true=None):
    if y_true is None and isinstance(oof_predictions, pd.DataFrame) and "target" in oof_predictions:
        y_true = oof_predictions["target"]
        oof_predictions = oof_predictions.drop(columns=["target"])
    if y_true is None:
        raise ValueError("y_true is required")
    return diversity_aware(oof_predictions, y_true, scorer)


def persist_blend(path: str | Path, result: dict[str, Any], predictions=None) -> Path:
    payload = {key: value for key, value in result.items() if key != "prediction"}
    if predictions is not None:
        matrix, names = _matrix(predictions)
        payload["correlation"] = pd.DataFrame(matrix, columns=names).corr().to_dict()
    atomic_write_json(path, payload)
    return Path(path)
