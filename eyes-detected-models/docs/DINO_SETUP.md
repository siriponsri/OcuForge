# DINOv3 setup

Status: **R1 G0-G5 READY / NOT EXECUTED / REQUIRES_MODEL_WEIGHTS**. `dinov3_vitb16`, ViT-B/16, is a leading
candidate for G1-G5, not a predetermined champion. No successful external-model inference is claimed.

1. Review [official repository](https://github.com/facebookresearch/dinov3) and [official model card](https://huggingface.co/facebook/dinov3-vitb16-pretrain-lvd1689m). Accept applicable access/license terms yourself.
2. Obtain an official checkout at an immutable commit and approved local weights. Store them below
   `OCUFORGE_MODEL_ROOT` (for example `dinov3/`) or another configured model root. Do not bundle or
   redistribute them with this repository.
3. Install the upstream requirements in a separate research environment after inspecting its pinned Python/PyTorch requirements. The starter's CPU torch pin is tested for TinyTestEncoder, not certified for every upstream DINOv3 revision.
4. Record commit, weight SHA-256, preprocessing hash and runtime. For the R1 benchmark, set `DINOV3_REPO`,
   `DINOV3_WEIGHTS`, `DINOV3_SHA256`, `DINOV3_LICENSE_REVIEWED=true`, and `EYES_DOCKER_IMAGE` in the
   execution environment. The checked-in R1 benchmark extraction config resolves these values from environment variables:

```python
from eyes_detected.encoders.dinov3_adapter import DINOv3Adapter
encoder = DINOv3Adapter(repo_path='/approved/dinov3', weight_path='/approved/weights.pth', expected_sha256='YOUR_ACTUAL_SHA256', license_reviewed=True)
```

Input is normalized RGB NCHW with dimensions divisible by 16, using the explicit patch normalization config. The loader uses `torch.hub.load(..., source='local')` and never initiates a model download. Only trusted reviewed local source code may be supplied.

Missing access, missing files or hash mismatch fail clearly; no automatic TinyTestEncoder fallback. RETFound/EyeCLIP/RetiZero integrations are planned challengers, not implemented model loaders.
