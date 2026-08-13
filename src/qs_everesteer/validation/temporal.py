"""Exped-aware temporal splits and out-of-fold evaluation."""
from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from qs_everesteer.validation.scoring import local_grouped_corr


@dataclass(frozen=True)
class FoldProfile:
    name: str
    n_splits: int
    min_train_expeds: int
    test_expeds: int
    embargo: int = 0
    rolling_window: int | None = None


FOLD_PROFILES = {
    "R0": FoldProfile("R0", 1, 2, 1),
    "R1": FoldProfile("R1", 2, 3, 1),
    "R2": FoldProfile("R2", 3, 4, 2, embargo=1),
    "R3": FoldProfile("R3", 4, 5, 2, embargo=1),
}


def target_horizon(target: str) -> int:
    """Extract the forward horizon encoded by targets such as ``*_20``."""
    match = re.search(r"(?:^|_)(\d+)$", str(target))
    return int(match.group(1)) if match else 0


def profile_for_target(profile: str | FoldProfile, target: str) -> FoldProfile:
    """Apply the target horizon as the minimum temporal embargo.

    ``TemporalSplitter`` naturally emits fewer folds when the dataset cannot
    support the requested fold count; it never weakens this embargo to make a
    profile fit.
    """
    base = FOLD_PROFILES[profile.upper()] if isinstance(profile, str) else profile
    horizon = target_horizon(target)
    if horizon <= base.embargo:
        return base
    return FoldProfile(
        name=base.name,
        n_splits=base.n_splits,
        min_train_expeds=base.min_train_expeds,
        test_expeds=base.test_expeds,
        embargo=horizon,
        rolling_window=base.rolling_window,
    )


class TemporalSplitter:
    def __init__(self, profile: str | FoldProfile = "R1") -> None:
        self.profile = FOLD_PROFILES[profile.upper()] if isinstance(profile, str) else profile

    def split(self, data, groups=None) -> Iterator[tuple[np.ndarray, np.ndarray]]:
        exped = np.asarray(groups if groups is not None else data)
        unique = np.sort(pd.unique(exped))
        p = self.profile
        starts = list(range(p.min_train_expeds + p.embargo, len(unique), p.test_expeds))
        starts = starts[-p.n_splits :]
        for start in starts:
            test_values = unique[start : start + p.test_expeds]
            train_end = start - p.embargo
            train_values = unique[:train_end]
            if p.rolling_window is not None:
                train_values = train_values[-p.rolling_window :]
            train_idx = np.flatnonzero(np.isin(exped, train_values))
            test_idx = np.flatnonzero(np.isin(exped, test_values))
            if len(train_idx) and len(test_idx):
                yield train_idx, test_idx

    def get_n_splits(self, data=None, groups=None) -> int:
        if data is None and groups is None:
            return self.profile.n_splits
        return sum(1 for _ in self.split(data, groups))


def temporal_cv(
    frame: pd.DataFrame,
    model_factory: Callable[[], Any],
    *,
    features: list[str],
    target: str,
    exped_col: str = "exped",
    profile: str | FoldProfile = "R1",
    sample_weight_fn: Callable[[Any], Any] | None = None,
    enforce_target_horizon: bool = True,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    effective_profile = (
        profile_for_target(profile, target)
        if enforce_target_horizon
        else FOLD_PROFILES[profile.upper()]
        if isinstance(profile, str)
        else profile
    )
    splitter = TemporalSplitter(effective_profile)
    oof_parts, fold_metrics = [], []
    for fold, (train_idx, valid_idx) in enumerate(splitter.split(frame[exped_col])):
        train, valid = frame.iloc[train_idx], frame.iloc[valid_idx]
        model = model_factory()
        weights = sample_weight_fn(train[exped_col]) if sample_weight_fn else None
        model.fit(train[features], train[target], sample_weight=weights)
        pred = model.predict(valid[features])
        scored = local_grouped_corr(valid[target], pred, valid[exped_col])
        part = valid[[exped_col]].copy()
        if "id" in valid:
            part["id"] = valid["id"].values
        part["row_index"] = valid.index
        part["target"] = valid[target].values
        part["prediction"] = pred
        part["fold"] = fold
        oof_parts.append(part)
        fold_metrics.append({"fold": fold, "score": scored.value, "rows": len(valid)})
    oof = pd.concat(oof_parts, ignore_index=True) if oof_parts else pd.DataFrame()
    overall = (
        local_grouped_corr(oof["target"], oof["prediction"], oof[exped_col]).value
        if not oof.empty else 0.0
    )
    per_exped = (
        local_grouped_corr(oof["target"], oof["prediction"], oof[exped_col]).per_exped
        if not oof.empty else {}
    )
    return oof, {
        "score": overall, "folds": fold_metrics, "per_exped": per_exped,
        "requested_folds": effective_profile.n_splits,
        "effective_folds": len(fold_metrics),
        "embargo": effective_profile.embargo,
        "target_horizon": target_horizon(target),
        "target_horizon_enforced": enforce_target_horizon,
        "provenance": "LOCAL_EXPERIMENT / not official",
    }
