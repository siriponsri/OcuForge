# DINOv3 setup for candidate C2

Status: **R1 C2 READY / NOT EXECUTED / REQUIRES APPROVED MODEL ASSETS**. DINOv3 ViT-B/16 is the high-resolution
local-detail hypothesis, not a predetermined champion. No successful external-model inference is claimed.

1. Review the [official repository](https://github.com/facebookresearch/dinov3) and [official model
   card](https://huggingface.co/facebook/dinov3-vitb16-pretrain-lvd1689m). Accept access and license terms yourself.
2. Obtain an official checkout at an immutable commit and approved local weights. Store them below
   `OCUFORGE_MODEL_ROOT` or another configured model root. Do not bundle or redistribute them with this repository.
3. Inspect the upstream Python/PyTorch requirements in a separate research environment. The repository CPU pin is
   tested for TinyTestEncoder, not certified for every upstream DINOv3 revision.
4. Record commit, weight SHA-256, preprocessing hash, patch geometry, and runtime. R0 must audit foundation-model
   pretraining overlap before C2 evidence can support an external-generalization claim.

The checked-in candidate config must resolve local paths and review flags from the execution environment. The loader
uses local source only and never initiates a model download. Missing access, missing files, or hash mismatch must fail
clearly; there is no automatic TinyTestEncoder fallback for C2.

C2 uses high-resolution patches and learned Attention MIL with a 5-class CE objective. Attention is aggregation
evidence only and is not a validated lesion-localization map. C0 ConvNeXt V2-Tiny and C1 FLAIR are separate R1
candidates and must be compared with CE under the same evidence rules.
