from typing import Protocol


class GradabilityPredictor(Protocol):
    """QC head is trained on synthetic targets only in smoke; calibration remains external."""

    def predict_gradability(self, features) -> float: ...
