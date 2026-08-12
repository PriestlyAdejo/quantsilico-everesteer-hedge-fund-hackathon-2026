"""CPU-safe random-forest variants."""
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline

from qs_everesteer.models.base import SklearnResearchModel


def forest_model(
    *,
    kind: str = "extra_trees",
    n_estimators: int = 100,
    max_depth: int | None = 8,
    max_features: float | str = 0.7,
    seed: int = 7,
    n_jobs: int = -1,
    **kwargs,
) -> SklearnResearchModel:
    params = {
        "kind": kind,
        "n_estimators": n_estimators,
        "max_depth": max_depth,
        "max_features": max_features,
        "seed": seed,
        **kwargs,
    }
    cls = ExtraTreesRegressor if kind in {"extra", "extra_trees"} else RandomForestRegressor
    estimator = make_pipeline(
        SimpleImputer(strategy="median"),
        cls(
            n_estimators=n_estimators,
            max_depth=max_depth,
            max_features=max_features,
            random_state=seed,
            n_jobs=n_jobs,
            **kwargs,
        ),
    )
    return SklearnResearchModel(
        estimator, private_name=kind, family="forest", params=params
    )


def random_forest(**kwargs) -> SklearnResearchModel:
    return forest_model(kind="random_forest", **kwargs)


def extra_trees(**kwargs) -> SklearnResearchModel:
    return forest_model(kind="extra_trees", **kwargs)
