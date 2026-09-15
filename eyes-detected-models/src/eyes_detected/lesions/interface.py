from typing import Protocol
from eyes_contracts.models import Candidate


class LesionPrelabeler(Protocol):
    """REQUIRES_MODEL_WEIGHTS and localized supervision; MIL attention is excluded."""

    def predict(self, image) -> list[Candidate]: ...
