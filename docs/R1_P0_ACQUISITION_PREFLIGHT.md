# R1-P0 Acquisition Preflight

**Status:** `R1_P0_ACQUISITION_PREFLIGHT=READY_NOT_EXECUTED`
**Authority:** [`POC_MASTER_PLAN.md`](POC_MASTER_PLAN.md)
**Machine-readable contract:** [`R1_P0_ACQUISITION_PREFLIGHT.json`](R1_P0_ACQUISITION_PREFLIGHT.json)

R1-P0 is the post-R0 acquisition and runtime gate. It exists because archive/file hashes, extracted inventories,
schema smoke tests, model weight hashes, gated access, and model loading cannot be verified before the authorized bytes
are acquired. It is not an R1 training run.

## Gate state

```text
R0_V3=PASS
R0_DATASET_TAXONOMY=PASS
R1_P0_ACQUISITION_PREFLIGHT=READY_NOT_EXECUTED
R1_GLOBAL_BENCHMARK=READY_NOT_EXECUTED
CURRENT_R1_CHAMPION=NONE
TRAINING_UNLOCK=FORBIDDEN_UNTIL_R1_P0_PASS
```

## Required sequence

1. `git pull` and inspect `HANDOFF.md`.
2. Resolve the four provider-neutral storage roots without placing secrets in Git.
3. Acquire only the frozen MMRDR-UWF and IDRiD records through their official access paths.
4. Compute and record archive/file SHA-256 values, integrity results, and extracted inventories locally.
5. Run schema, split, identity, duplicate, mask-coverage, and preprocessing smoke checks.
6. Acquire only the exact C0/C1/C2 assets and record local SHA-256, terms, gated-access status, and loading results.
7. Update the P0 record only with safe metadata; every check must become `PASS` before training is permitted.

## Non-negotiable controls

- Preserve the MMRDR released UWF train/test split; its missing row-level patient IDs remain a limitation.
- Preserve IDRiD's image-level split and never claim patient-level independence without evidence.
- Treat unannotated IDRiD regions as `UNKNOWN` or `WEAK_NEGATIVE` unless a verified source rule supports clean negatives.
- Do not convert MMRDR image-level lesion presence into ROI geometry.
- Do not silently substitute model assets or use a TinyTestEncoder fallback.
- Do not upload private data or derived artifacts; no cloud provisioning occurs in P0.
- Do not execute R1 during P0.
