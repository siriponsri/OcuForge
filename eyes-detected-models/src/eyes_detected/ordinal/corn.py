"""Conditional ordinal regression utilities for the post-selection R1 ablation."""

import torch
import torch.nn.functional as F
from torch import nn


NUM_THRESHOLDS = 4


def _validate_grades(grades):
    if grades.dtype not in [torch.int32, torch.int64] or torch.any((grades < 0) | (grades > 4)):
        raise ValueError("DR grades must be integer 0..4")
    if grades.ndim != 1:
        raise ValueError("CORN grades must be a one-dimensional batch")


def encode(grades, num_thresholds=NUM_THRESHOLDS):
    """Return conditional targets and eligibility masks for CORN thresholds."""

    if num_thresholds != NUM_THRESHOLDS:
        raise ValueError("The starter CORN contract supports exactly five grades")
    _validate_grades(grades)
    levels = torch.arange(num_thresholds, device=grades.device)
    targets = (grades.unsqueeze(-1) > levels).float()
    eligible = torch.ones_like(targets, dtype=torch.bool)
    eligible[:, 1:] = grades.unsqueeze(-1) > levels[:-1]
    return targets, eligible


class CORNHead(nn.Module):
    """Unconstrained conditional logits decoded through a cumulative probability product."""

    def __init__(self, dim, num_thresholds=NUM_THRESHOLDS):
        super().__init__()
        if num_thresholds != NUM_THRESHOLDS:
            raise ValueError("The starter CORN contract supports exactly five grades")
        self.score = nn.Linear(dim, num_thresholds)

    def forward(self, x):
        if x.ndim < 2 or not torch.isfinite(x).all():
            raise ValueError("Expected finite feature tensor")
        if x.shape[-1] != self.score.in_features:
            raise ValueError("Feature dimension does not match CORN head")
        return self.score(x)


def loss(logits, grades):
    """Train each conditional threshold only on samples eligible for that threshold."""

    if logits.shape[-1] != NUM_THRESHOLDS:
        raise ValueError("CORN logits must have four thresholds")
    targets, eligible = encode(grades)
    if logits.shape != targets.shape:
        raise ValueError("CORN logits and targets must have the same shape")
    return F.binary_cross_entropy_with_logits(logits[eligible], targets[eligible])


def cumulative_probabilities(logits):
    if logits.shape[-1] != NUM_THRESHOLDS:
        raise ValueError("CORN logits must have four thresholds")
    conditional = logits.sigmoid()
    return torch.cumprod(conditional, dim=-1)


def predict(logits):
    """Decode monotone P(grade > threshold) probabilities and a grade 0..4."""

    probabilities = cumulative_probabilities(logits)
    return (probabilities > 0.5).sum(-1), probabilities


def class_probabilities(probabilities):
    if probabilities.shape[-1] != NUM_THRESHOLDS:
        raise ValueError("CORN probabilities must have four thresholds")
    cumulative = torch.cat(
        [1 - probabilities[..., :1], probabilities[..., :-1] - probabilities[..., 1:]],
        dim=-1,
    )
    # Derive the final class as a residual so rounding is concentrated in one bin.
    final = 1 - cumulative.sum(dim=-1, keepdim=True)
    return torch.cat([cumulative, final], dim=-1)
