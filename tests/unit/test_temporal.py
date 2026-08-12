import numpy as np

from qs_everesteer.validation.temporal import FoldProfile, TemporalSplitter


def test_temporal_expanding_split_respects_embargo():
    groups = np.repeat(np.arange(8), 2)
    splitter = TemporalSplitter(FoldProfile("test", 3, 2, 1, embargo=1))
    folds = list(splitter.split(groups))
    assert folds
    for train, valid in folds:
        assert groups[train].max() < groups[valid].min() - 0
        assert groups[valid].min() - groups[train].max() >= 2
