"""Explicit local-asset adapters for the V3 C0/C1 candidates.

These adapters validate asset provenance and wrap an already-loaded upstream model. They never
download weights or silently substitute a synthetic encoder.
"""

from pathlib import Path
import hashlib

import torch
from torch import nn


class AssetNotPresentError(RuntimeError):
    """Raised when a candidate's approved local model asset is unavailable."""


class LocalModelAdapter(nn.Module):
    """Common provenance boundary for externally supplied candidate models."""

    def __init__(self, encoder_id, asset_path, expected_sha256, license_reviewed, model=None):
        super().__init__()
        self.encoder_id = encoder_id
        if not license_reviewed:
            raise RuntimeError(f"Review {encoder_id} license and access terms before loading the asset")
        path = Path(asset_path)
        if not path.is_file():
            raise AssetNotPresentError(
                f"{encoder_id} ASSET_NOT_PRESENT: provide an approved local asset; no download or fallback"
            )
        if not isinstance(expected_sha256, str) or len(expected_sha256) != 64:
            raise ValueError("A verified 64-character SHA-256 is required for candidate assets")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != expected_sha256:
            raise RuntimeError(f"{encoder_id} asset SHA256 mismatch")
        if model is None:
            raise AssetNotPresentError(
                f"{encoder_id} loader is not configured for this asset format; no inference claimed"
            )
        self.model = model
        self.asset_sha256 = digest

    def forward(self, x):
        if x.ndim != 4 or x.shape[1] != 3 or not torch.isfinite(x).all():
            raise ValueError("Candidate image encoder expects finite NCHW RGB input")
        return self.model(x)


class ConvNeXtV2TinyAdapter(LocalModelAdapter):
    encoder_id = "convnextv2_tiny"

    def __init__(self, asset_path, expected_sha256, license_reviewed, model=None):
        super().__init__(self.encoder_id, asset_path, expected_sha256, license_reviewed, model)


class FLAIRAdapter(LocalModelAdapter):
    encoder_id = "flair_image_encoder"

    def __init__(self, asset_path, expected_sha256, license_reviewed, model=None):
        super().__init__(self.encoder_id, asset_path, expected_sha256, license_reviewed, model)
