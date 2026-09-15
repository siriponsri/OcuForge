from typing import Protocol
import torch


class Encoder(Protocol):
    encoder_id: str

    def __call__(self, patches: torch.Tensor) -> torch.Tensor: ...
