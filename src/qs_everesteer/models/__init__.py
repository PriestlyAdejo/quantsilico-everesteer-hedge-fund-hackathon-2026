"""Research model factories."""
from qs_everesteer.models.advanced import feature_bin_model, realmlp_style, tabular_hist_challenger
from qs_everesteer.models.baseline import organiser_lgbm, reference_lgbm
from qs_everesteer.models.catboost_model import catboost_model
from qs_everesteer.models.forest import extra_trees, forest_model, random_forest
from qs_everesteer.models.lgbm import lgbm_model
from qs_everesteer.models.p1 import SeedBaggingModel, feature_subspace, recency_weights, shallow_mlp
from qs_everesteer.models.ridge import ridge_model
from qs_everesteer.models.xgboost_model import xgboost_model

MODEL_FACTORIES = {
    "ridge": ridge_model,
    "random_forest": random_forest,
    "extra_trees": extra_trees,
    "xgboost": xgboost_model,
    "lgbm": lgbm_model,
    "reference_lgbm": reference_lgbm,
    "organiser_lgbm": organiser_lgbm,
    "shallow_mlp": shallow_mlp,
    "catboost": catboost_model,
    "realmlp_style": realmlp_style,
    "feature_bin": feature_bin_model,
    "tabular_hist": tabular_hist_challenger,
}


def create_model(name: str, **params):
    try:
        return MODEL_FACTORIES[name](**params)
    except KeyError as exc:
        raise ValueError(f"unknown model {name!r}; choose from {sorted(MODEL_FACTORIES)}") from exc


__all__ = [
    "MODEL_FACTORIES",
    "SeedBaggingModel",
    "catboost_model",
    "create_model",
    "extra_trees",
    "feature_bin_model",
    "feature_subspace",
    "forest_model",
    "lgbm_model",
    "organiser_lgbm",
    "random_forest",
    "realmlp_style",
    "recency_weights",
    "reference_lgbm",
    "ridge_model",
    "shallow_mlp",
    "tabular_hist_challenger",
    "xgboost_model",
]
