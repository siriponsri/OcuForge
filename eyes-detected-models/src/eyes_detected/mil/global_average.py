import torch
from torch import nn
from eyes_detected.ordinal.coral import CoralHead


class GlobalAveragePooling(nn.Module):
    """Pool valid patch features uniformly for the frozen-encoder B1 baseline."""

    def __init__(self, dim=16):
        super().__init__()
        self.dr = CoralHead(dim)
        self.lesions = nn.Linear(dim, 7)
        self.qc = nn.Linear(dim, 1)

    def forward(self, x, mask=None):
        if x.ndim != 3 or not torch.isfinite(x).all():
            raise ValueError("Expected finite batch,patch,embedding tensor")
        if mask is None:
            mask = torch.ones(x.shape[:2], dtype=torch.bool, device=x.device)
        if mask.shape != x.shape[:2] or mask.dtype != torch.bool or not mask.any(1).all():
            raise ValueError("Each bag needs valid patches and boolean mask")
        weights = mask.to(x.dtype)
        weights = weights / weights.sum(1, keepdim=True)
        bag = (weights.unsqueeze(-1) * x).sum(1)
        return {
            "dr_logits": self.dr(bag),
            "lesion_logits": self.lesions(bag),
            "qc_logits": self.qc(bag).squeeze(-1),
            "embedding": bag,
        }
