import numpy as np


class PrototypeOOD:
    """Uncalibrated Euclidean reference-distance interface; no clinical threshold."""

    def __init__(self, prototypes, threshold):
        self.prototypes = np.asarray(prototypes, dtype=float)
        self.threshold = float(threshold)
        if (
            self.prototypes.ndim != 2
            or not np.isfinite(self.prototypes).all()
            or not np.isfinite(threshold)
            or threshold < 0
        ):
            raise ValueError("Invalid prototypes/threshold")

    def score(self, x):
        x = np.asarray(x, dtype=float)
        if x.ndim != 2 or x.shape[1] != self.prototypes.shape[1] or not np.isfinite(x).all():
            raise ValueError("Invalid features")
        d = np.linalg.norm(x[:, None, :] - self.prototypes[None, :, :], axis=-1).min(1)
        return [
            {
                "method": "prototype_distance_uncalibrated",
                "score": float(v),
                "abstain_recommended": bool(v > self.threshold),
            }
            for v in d
        ]
