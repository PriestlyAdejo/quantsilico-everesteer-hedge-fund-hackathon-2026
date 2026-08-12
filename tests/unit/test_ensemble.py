import numpy as np
import pandas as pd

from qs_everesteer.ensemble.blend import greedy_forward, rank_average, weighted


def test_blend_shapes_and_greedy_selection():
    frame = pd.DataFrame({"good": [0, 1, 2, 3], "bad": [3, 0, 2, 1]})
    target = np.arange(4)
    scorer = lambda y, p: np.corrcoef(y, p)[0, 1]
    assert rank_average(frame).shape == (4,)
    assert np.allclose(weighted(frame, [1, 0]), frame["good"])
    result = greedy_forward(frame, target, scorer)
    assert result["member_ids"][0] == "good"
