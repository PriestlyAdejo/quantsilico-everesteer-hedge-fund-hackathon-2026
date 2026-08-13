"""Independent and attributable organiser LightGBM baseline recipes."""
from qs_everesteer.models.lgbm import lgbm_model

ORGANISER_BASELINE_PROVENANCE = {
    "organiser_parity_status": "SOURCE_RETRIEVED",
    "reason": "Official public futures starter retrieved and hashed; numeric parity is data-dependent.",
    "source_url": "https://raw.githubusercontent.com/everestquant/example-scripts/main/himalayas/futures_starter.py",
    "version": "main@2026-08-13",
    "date": "2026-08-13",
    "hash_algorithm": "sha256",
    "hash": "e3d35ca62db8e72ae29a0aa8861a92a323cb3854edf6bb1c4d3e94d96d041396",
    "target": "target_everest_20",
    "embargo_expeds": 20,
    "holdout_expeds": 100,
    "missing_sentinel": -1,
}


def reference_lgbm(**kwargs):
    model = lgbm_model(**kwargs)
    model.metadata.private_name = "reference_lgbm"
    model.metadata.extra.update(ORGANISER_BASELINE_PROVENANCE)
    return model


def organiser_lgbm(**kwargs):
    """Estimator parameters from the attributable public futures starter."""
    params = {
        "n_estimators": 2000,
        "learning_rate": 0.01,
        "max_depth": 6,
        "num_leaves": 64,
        "colsample_bytree": 0.10,
        "subsample": 0.80,
        "min_child_samples": 500,
        "reg_alpha": 0.1,
        "reg_lambda": 1.0,
        "seed": 42,
        **kwargs,
    }
    model = lgbm_model(**params)
    model.metadata.private_name = "organiser_lgbm"
    model.metadata.extra.update(ORGANISER_BASELINE_PROVENANCE)
    return model
