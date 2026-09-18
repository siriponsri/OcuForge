# Public GPU and local runtime boundary

**Status:** ACTIVE SUPPORTING RUNTIME GUIDE
**Authority:** [`POC_MASTER_PLAN.md`](POC_MASTER_PLAN.md)

The current gates are `R0_V3=PASS`, `R1_P0_ACQUISITION_PREFLIGHT=BLOCKED` on a released-split duplicate leakage
finding, and R1 C0/C1/C2 is `READY_NOT_EXECUTED`. This document authorizes the owner-approved public RunPod runtime for R1-P0
acquisition and validation only; it does not authorize training or R1 execution before P0 unlock. R1-P0 Global may
acquire only MMRDR-UWF and the approved C0/C1/C2 assets under its contract; IDRiD is deferred to R2/R3.

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

After R0 and R1-P0 reaches `PASS` or `PASS_WITH_WARNINGS` with no blocker, and `RUNPOD_AUTOMATION_SMOKE` reaches
`PASS` or `PASS_WITH_WARNINGS`, the authorized unattended overnight run may execute one candidate at a time from the
registry: C0 -> validated checkpoint -> C1
-> validated checkpoint -> C2. No candidate may train before those unlock conditions. Validate each checkpoint before
continuing, carrying all warnings into the next artifact; stop on a blocker. After C2, stop at the evidence freeze for
the mandatory OWNER/morning architecture-selection gate. Compare CE first; the overnight run does not authorize
CE-vs-CORN. Record exact asset revision, license decision, hashes, preprocessing, runtime image, git SHA, data
manifest, split, and operational measurements.

No automatic promotion, fixed champion, or “DINO required to pass” rule exists. Missing FLAIR/DINOv3 assets are explicit
blocked/asset-not-present conditions, not silent substitutions.
