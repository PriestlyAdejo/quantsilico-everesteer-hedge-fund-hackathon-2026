"""Official scoring adapters and explicitly-labelled local diagnostics."""
from __future__ import annotations

import importlib
import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ScoreResult:
    value: float
    metric: str
    provenance: str
    official: bool
    per_exped: dict[str, float] | None = None


def official_scorers() -> dict[str, Callable[..., Any]]:
    try:
        module = importlib.import_module("everestapi.scoring")
    except ImportError:
        return {}
    aliases = {
        "CORR20": ("CORR20", "corr20", "score_corr20"),
        "AIMC": ("AIMC", "aimc", "score_aimc"),
        "NCORR": ("NCORR", "ncorr", "score_ncorr"),
    }
    found = {}
    for metric, names in aliases.items():
        for name in names:
            candidate = getattr(module, name, None)
            if callable(candidate):
                found[metric] = candidate
                break
    return found


def score_with_official_engine(
    metric: str,
    *,
    predictions: Any,
    target: Any,
    features: Any | None = None,
    expeds: Any | None = None,
) -> ScoreResult:
    """Call an organiser scorer using explicit, name-matched semantics.

    Signatures differ between SDK releases. We map only recognised parameter
    names and refuse an ambiguous scorer instead of guessing positional order.
    """
    name = metric.upper()
    scorer = official_scorers().get(name)
    if scorer is None:
        raise RuntimeError(f"official {name} scorer unavailable")
    values = {
        "predictions": predictions,
        "prediction": predictions,
        "y_pred": predictions,
        "preds": predictions,
        "target": target,
        "targets": target,
        "y_true": target,
        "features": features,
        "neutralizers": features,
        "expeds": expeds,
        "exped": expeds,
        "groups": expeds,
    }
    signature = inspect.signature(scorer)
    kwargs = {
        name: values[name]
        for name, parameter in signature.parameters.items()
        if name in values
        and values[name] is not None
        and parameter.kind
        in {inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY}
    }
    prediction_names = {"predictions", "prediction", "y_pred", "preds"}
    target_names = {"target", "targets", "y_true"}
    if not prediction_names.intersection(kwargs) or not target_names.intersection(kwargs):
        raise RuntimeError(
            f"official {name} scorer has unsupported/ambiguous signature {signature}"
        )
    raw = scorer(**kwargs)
    value = raw.get("score", raw.get(name)) if isinstance(raw, dict) else raw
    return ScoreResult(float(value), name, "everestapi.scoring", True)


def local_grouped_corr(
    y_true, y_pred, expeds=None, *, metric: str = "LOCAL_IC"
) -> ScoreResult:
    """Mean Pearson correlation by exped for synthetic/local research only."""
    frame = pd.DataFrame(
        {"y": np.asarray(y_true), "p": np.asarray(y_pred),
         "exped": 0 if expeds is None else np.asarray(expeds)}
    )
    values: dict[str, float] = {}
    for exped, group in frame.groupby("exped", sort=True):
        valid = group[["y", "p"]].dropna()
        corr = (
            float(valid["y"].corr(valid["p"]))
            if len(valid) >= 2 and valid["y"].nunique() > 1 and valid["p"].nunique() > 1
            else 0.0
        )
        values[str(exped)] = 0.0 if not np.isfinite(corr) else corr
    return ScoreResult(
        float(np.mean(list(values.values()))) if values else 0.0,
        metric, "LOCAL_EXPERIMENT / not official", False, values,
    )


def score(
    metric: str,
    *,
    predictions: Any,
    target: Any,
    features: Any | None = None,
    expeds: Any | None = None,
) -> ScoreResult:
    """Score explicit prediction/target inputs without positional ambiguity."""
    if metric.upper() in official_scorers():
        return score_with_official_engine(
            metric,
            predictions=predictions,
            target=target,
            features=features,
            expeds=expeds,
        )
    return local_grouped_corr(
        target, predictions, expeds, metric=f"LOCAL_{metric.upper()}"
    )


def scorer_parity(
    expected, observed, *, expected_ids=None, observed_ids=None, tolerance: float = 1e-8
) -> dict[str, Any]:
    a, b = np.asarray(expected, dtype=float), np.asarray(observed, dtype=float)
    id_aligned = True
    if expected_ids is not None and observed_ids is not None:
        id_aligned = list(expected_ids) == list(observed_ids)
    same = len(a) == len(b) and bool(np.allclose(a, b, atol=tolerance, equal_nan=True))
    inverted = len(a) == len(b) and bool(np.allclose(a, -b, atol=tolerance, equal_nan=True))
    return {
        "ok": same and id_aligned,
        "sign_inversion": inverted and not same,
        "id_alignment": id_aligned,
        "length_match": len(a) == len(b),
        "max_abs_error": (
            float(np.nanmax(np.abs(a - b))) if len(a) == len(b) and len(a) else None
        ),
    }
