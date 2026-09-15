from pathlib import Path
import hashlib
import torch
from torch import nn


class DINOv3Adapter(nn.Module):
    """Local official torch.hub checkout + approved local weights; no downloads."""

    encoder_id = "dinov3_vitb16"

    def __init__(self, repo_path, weight_path, expected_sha256, license_reviewed=False):
        super().__init__()
        if not license_reviewed:
            raise RuntimeError("Review DINOv3 license and access terms; see docs/DINO_SETUP.md")
        repo = Path(repo_path)
        weights = Path(weight_path)
        if not (repo / "hubconf.py").is_file() or not weights.is_file():
            raise RuntimeError(
                "DINOv3 unavailable: provide official local checkout and approved weights. See docs/DINO_SETUP.md; no TinyTestEncoder fallback."
            )
        h = hashlib.sha256()
        with weights.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        self.weight_hash = h.hexdigest()
        if self.weight_hash != expected_sha256:
            raise RuntimeError("DINOv3 weight SHA256 mismatch")
        self.model = torch.hub.load(str(repo), self.encoder_id, source="local", weights=str(weights))
        self.model.eval().requires_grad_(False)

    def forward(self, x):
        if x.ndim != 4 or x.shape[1] != 3 or x.shape[-1] % 16 or x.shape[-2] % 16:
            raise ValueError("DINO expects normalized NCHW RGB, dimensions divisible by 16")
        with torch.no_grad():
            return self.model(x)
