"""Independent reference baseline, not an organiser starter reproduction."""
from qs_everesteer.models.lgbm import lgbm_model

ORGANISER_BASELINE_PROVENANCE = {
    "organiser_parity_status": "UNAVAILABLE",
    "reason": "Exact organiser starter was not retrieved; parameters cannot be verified.",
    "source_url": None,
    "version": "UNAVAILABLE",
    "date": None,
    "hash": None,
}


def reference_lgbm(**kwargs):
    model = lgbm_model(**kwargs)
    model.metadata.private_name = "reference_lgbm"
    model.metadata.extra.update(ORGANISER_BASELINE_PROVENANCE)
    return model
