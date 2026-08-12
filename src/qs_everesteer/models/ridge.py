"""Regularised linear reference models."""
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from qs_everesteer.models.base import SklearnResearchModel


def ridge_model(*, alpha: float = 10.0, seed: int = 7, **kwargs) -> SklearnResearchModel:
    params = {"alpha": alpha, "seed": seed, **kwargs}
    estimator = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        Ridge(alpha=alpha, **kwargs),
    )
    return SklearnResearchModel(
        estimator, private_name="ridge", family="linear", params=params
    )


RidgeModel = ridge_model
