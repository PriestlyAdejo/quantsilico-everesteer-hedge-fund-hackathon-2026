"""Bounded, dependency-light diversity challengers.

These are deliberately modest tabular challengers rather than claims to exact
published TabM/RealMLP implementations. Optional accelerator implementations can
be added only after parity and crossover measurements.
"""
from __future__ import annotations

from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import KBinsDiscretizer, StandardScaler

from qs_everesteer.models.base import SklearnResearchModel


def realmlp_style(
    *, hidden_layer_sizes: tuple[int, ...] = (64, 32), alpha: float = 0.01,
    max_iter: int = 160, seed: int = 7, **kwargs,
) -> SklearnResearchModel:
    params = {
        "hidden_layer_sizes": hidden_layer_sizes, "alpha": alpha,
        "max_iter": max_iter, "seed": seed, **kwargs,
    }
    estimator = make_pipeline(
        SimpleImputer(strategy="median"), StandardScaler(),
        MLPRegressor(
            hidden_layer_sizes=hidden_layer_sizes, alpha=alpha, max_iter=max_iter,
            early_stopping=True, random_state=seed, **kwargs,
        ),
    )
    return SklearnResearchModel(
        estimator, private_name="realmlp_style", family="neural", params=params,
        metadata_extra={"accelerator": "optional_not_required"},
    )


def feature_bin_model(
    *, n_bins: int = 16, alpha: float = 0.02, max_iter: int = 140,
    seed: int = 7, **kwargs,
) -> SklearnResearchModel:
    params = {"n_bins": n_bins, "alpha": alpha, "max_iter": max_iter, "seed": seed, **kwargs}
    estimator = make_pipeline(
        SimpleImputer(strategy="median"),
        KBinsDiscretizer(n_bins=n_bins, encode="ordinal", strategy="quantile"),
        StandardScaler(),
        MLPRegressor(
            hidden_layer_sizes=(48,), alpha=alpha, max_iter=max_iter,
            early_stopping=True, random_state=seed, **kwargs,
        ),
    )
    return SklearnResearchModel(
        estimator, private_name="feature_bin_mlp", family="neural", params=params,
    )


def tabular_hist_challenger(
    *, max_iter: int = 160, max_leaf_nodes: int = 31, learning_rate: float = 0.05,
    l2_regularization: float = 1.0, seed: int = 7, **kwargs,
) -> SklearnResearchModel:
    params = {
        "max_iter": max_iter, "max_leaf_nodes": max_leaf_nodes,
        "learning_rate": learning_rate, "l2_regularization": l2_regularization,
        "seed": seed, **kwargs,
    }
    estimator = make_pipeline(
        SimpleImputer(strategy="median"),
        HistGradientBoostingRegressor(
            max_iter=max_iter, max_leaf_nodes=max_leaf_nodes,
            learning_rate=learning_rate, l2_regularization=l2_regularization,
            random_state=seed, **kwargs,
        ),
    )
    return SklearnResearchModel(
        estimator, private_name="tabular_hist_challenger", family="boosting",
        params=params,
    )
