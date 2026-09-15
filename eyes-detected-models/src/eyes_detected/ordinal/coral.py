import torch
from torch import nn
import torch.nn.functional as F


def encode(grades):
    if grades.dtype not in [torch.int32, torch.int64] or torch.any((grades < 0) | (grades > 4)):
        raise ValueError("DR grades must be integer 0..4")
    return (grades.unsqueeze(-1) > torch.arange(4, device=grades.device)).float()


class CoralHead(nn.Module):
    """Shared projection with ordered cutpoints gives monotone cumulative logits."""

    def __init__(self, dim):
        super().__init__()
        self.score = nn.Linear(dim, 1, bias=False)
        self.first = nn.Parameter(torch.tensor(-1.5))
        self.gaps = nn.Parameter(torch.zeros(3))

    def forward(self, x):
        cuts = torch.cat([self.first.view(1), self.first + torch.cumsum(F.softplus(self.gaps), 0)])
        return self.score(x) - cuts


def loss(logits, grades):
    return F.binary_cross_entropy_with_logits(logits, encode(grades))


def predict(logits):
    p = logits.sigmoid()
    if torch.any(p[..., 1:] > p[..., :-1]):
        raise ValueError("Threshold probabilities are not monotone")
    return (p > 0.5).sum(-1), p


def class_probabilities(p):
    return torch.cat([1 - p[..., :1], p[..., :-1] - p[..., 1:], p[..., -1:]], -1)
