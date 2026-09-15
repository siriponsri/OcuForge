import numpy as np


def qwk(truth, prediction):
    a = np.asarray(truth)
    b = np.asarray(prediction)
    if (
        a.shape != b.shape
        or a.ndim != 1
        or not len(a)
        or not np.isin(a, range(5)).all()
        or not np.isin(b, range(5)).all()
    ):
        raise ValueError("Aligned grades 0..4 required")
    observed = np.zeros((5, 5))
    np.add.at(observed, (a.astype(int), b.astype(int)), 1)
    expected = np.outer(observed.sum(1), observed.sum(0)) / len(a)
    weights = (np.arange(5)[:, None] - np.arange(5)[None, :]) ** 2 / 16
    denom = (weights * expected).sum()
    return None if denom == 0 else float(1 - (weights * observed).sum() / denom)
