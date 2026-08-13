import numpy as np
import pandas as pd
import pytest

from qs_everesteer.ensemble.blend import ridge_oof_stack


def test_ridge_stack_is_temporally_cross_fitted():
    groups = np.repeat(np.arange(5), 4)
    target = np.linspace(-1, 1, len(groups))
    predictions = pd.DataFrame({"synthetic_a": target + 0.02, "synthetic_b": -target})
    result = ridge_oof_stack(predictions, target, groups)
    assert result["member_ids"] == ["synthetic_a", "synthetic_b"]
    assert result["scored_rows"] == 12
    assert np.isnan(result["prediction"][:8]).all()
    assert np.isfinite(result["prediction"][8:]).all()


def test_stack_rejects_positional_or_too_small_inputs():
    with pytest.raises(ValueError, match="equal row counts"):
        ridge_oof_stack(np.ones((5, 2)), np.ones(4), np.arange(5))
    with pytest.raises(ValueError, match="at least two"):
        ridge_oof_stack(np.ones((6, 1)), np.ones(6), np.repeat(range(3), 2))
