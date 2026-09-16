# Public GPU and local runtime boundary

**Status:** ACTIVE SUPPORTING RUNTIME GUIDE
**Authority:** [`POC_MASTER_PLAN.md`](POC_MASTER_PLAN.md)

The current gate is `R0_V3=READY_TO_EXECUTE / NOT_YET_PASSED`; R1 C0/C1/C2 is `READY_NOT_EXECUTED`. This document
does not authorize R0/R1 execution, dataset download, training, or provider provisioning.

## Allowed zones

- **Public GPU (RunPod/Vast or equivalent):** temporary training, feature extraction, and experiments using reviewed
  public/synthetic data and eligible public model assets only.
- **Local/on-premise:** authoritative inference, model archive, clinical integration, hospital/private data, and every
  private derived artifact.
- **Vercel:** public/synthetic demo frontend or measured light inference only; never clinical authority or PHI storage.
- **GitHub:** code, safe configs/manifests, metadata, hashes, reports, and synthetic fixtures only.

Use provider-neutral roots: `OCUFORGE_DATA_ROOT`, `OCUFORGE_MODEL_ROOT`, `OCUFORGE_CACHE_ROOT`, and
`OCUFORGE_ARTIFACT_ROOT`. A provider volume is a workspace/cache, not production storage or deployment authority.

## R1 execution discipline

After R0 passes, run one candidate at a time from the registry: C0, stop/review; C1, stop/review; C2, stop/review.
Compare CE first. Only a measured winner/finalist may enter the CE versus CORN ablation. Record exact asset revision,
license decision, hashes, preprocessing, runtime image, git SHA, data manifest, split, and operational measurements.

No automatic promotion, fixed champion, or “DINO required to pass” rule exists. Missing FLAIR/DINOv3 assets are explicit
blocked/asset-not-present conditions, not silent substitutions.
