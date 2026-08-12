import numpy as np
import pandas as pd

from qs_everesteer.models.forest import extra_trees
from qs_everesteer.models.registry import ModelRegistry
from qs_everesteer.models.ridge import ridge_model


def test_models_fit_predict_and_registry(tmp_path):
    X = pd.DataFrame({"feature_0001": [0.0, 1.0, np.nan, 3.0], "feature_0002": [1, 0, 2, 3]})
    y = np.array([0.0, 1.0, 1.5, 3.0])
    for model in (ridge_model(), extra_trees(n_estimators=5, max_depth=2)):
        model.fit(X, y)
        assert model.predict(X).shape == (4,)
        assert model.metadata.public_alias.startswith("candidate-")
    registry = ModelRegistry(tmp_path)
    saved = registry.save(model, model_id="tiny")
    assert saved["artefact_hash"]
    assert registry.load("tiny").predict(X).shape == (4,)
