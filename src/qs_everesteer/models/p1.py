"""Priority-one candidate utilities."""
from __future__ import annotations

import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from qs_everesteer.models.base import SklearnResearchModel


def recency_weights(expeds, *, half_life: float = 8.0) -> np.ndarray:
    values = np.asarray(expeds, dtype=float)
    age = np.nanmax(values) - values
    return np.power(0.5, age / max(float(half_life), 1e-9))


def feature_subspace(features: list[str], *, fraction: float = 0.8, seed: int = 7) -> list[str]:
    if not 0 < fraction <= 1:
        raise ValueError("fraction must be in (0, 1]")
    rng = np.random.default_rng(seed)
    n = max(1, int(np.ceil(len(features) * fraction)))
    return sorted(rng.choice(features, size=n, replace=False).tolist())


def shallow_mlp(
    *, hidden_layer_sizes: tuple[int, ...] = (32,), alpha: float = 0.01,
    max_iter: int = 200, seed: int = 7, **kwargs,
) -> SklearnResearchModel:
    params = {
        "hidden_layer_sizes": hidden_layer_sizes, "alpha": alpha,
        "max_iter": max_iter, "seed": seed, **kwargs,
    }
    estimator = make_pipeline(
        SimpleImputer(strategy="median"), StandardScaler(),
        MLPRegressor(
            hidden_layer_sizes=hidden_layer_sizes, alpha=alpha, max_iter=max_iter,
            random_state=seed, early_stopping=True, **kwargs,
        ),
    )
    return SklearnResearchModel(
        estimator, private_name="shallow_mlp", family="neural", params=params
    )


class SeedBaggingModel:
    def __init__(self, factory, seeds=(7, 17, 29)):
        self.models = [factory(seed=seed) for seed in seeds]
        self.metadata = self.models[0].metadata
        self.metadata.private_name = "seed_bag"
        self.metadata.extra["seeds"] = list(seeds)

    def fit(self, X, y, sample_weight=None):
        for model in self.models:
            model.fit(X, y, sample_weight=sample_weight)
        return self

    def predict(self, X):
        return np.mean([model.predict(X) for model in self.models], axis=0)
