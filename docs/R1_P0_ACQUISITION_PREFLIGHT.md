# R1-P0 Acquisition Preflight

**Status:** `R1_P0_ACQUISITION_PREFLIGHT=READY_NOT_EXECUTED` · states: `READY_NOT_EXECUTED`, `RUNNING`,
`PASS_WITH_WARNINGS`, `PASS`, `BLOCKED`
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
TRAINING_UNLOCK=FORBIDDEN_UNTIL_PASS_OR_PASS_WITH_WARNINGS
```

`PASS` requires every required check to pass. `PASS_WITH_WARNINGS` permits only `PASS` or
`PASS_WITH_WARNINGS` checks, requires no blocker, and requires every warning to be recorded and copied into R1
artifacts. `BLOCKED` is reserved for an invalidating, unauthorized, corrupt, leaking, incompatible, or impossible
R1 execution condition. `RUNNING` is not an unlock state.

## Required sequence

1. `git pull` and inspect `HANDOFF.md`.
2. Resolve the four provider-neutral storage roots without placing secrets in Git.
3. Acquire only the frozen MMRDR-UWF record and the exact C0/C1/C2 assets through their official access paths.
4. Compute and record archive/file SHA-256 values, integrity results, and extracted inventories locally.
5. Run MMRDR schema, split, identity, duplicate, and preprocessing smoke checks. IDRiD acquisition and mask-coverage
   checks are deferred to R2/R3 preparation and do not block R1.
6. Acquire only the exact C0/C1/C2 assets and record local SHA-256, terms, gated-access status, and loading results.
7. Update the P0 record only with safe metadata; training is permitted after `PASS` or `PASS_WITH_WARNINGS` when no
   blocking finding remains.

## R1 critical path

R1-P0 Global requires only:

- MMRDR-UWF;
- C0 ConvNeXt V2-Tiny, C1 FLAIR, and C2 DINOv3;
- provider-neutral storage and runtime readiness;
- preprocessing and model-load/forward-pass checks.

IDRiD remains recorded as the R2/R3 spatial candidate. Its source, split, mask coverage, and conservative
`UNKNOWN`/`WEAK_NEGATIVE` policy remain preserved, but its acquisition is not an R1 training dependency.

## Eligibility and claim limits

Each candidate records `research_execution_eligible` separately from `deployment_license_status`. A restricted or
review-required deployment license may be a warning for a research-eligible candidate; it is not by itself an R1
blocker. Scientific and deployment champions may therefore differ. Unknown foundation-model overlap remains a warning
and caps external-generalization claims; it does not invalidate a controlled R1 benchmark.

## Blocking versus warnings

Block R1 only for unauthorized required access, corrupt or incomplete required R1 data, an incorrect or ambiguous
ordinal target, split leakage, incompatible preprocessing, or a candidate that cannot load and forward-pass. Record
unknown overlap, unavailable row-level patient IDs with the official split preserved, deployment-license restriction,
and claim ceilings as non-blocking warnings.

## Non-negotiable controls

- Preserve the MMRDR released UWF train/test split; its missing row-level patient IDs remain a limitation.
- Preserve IDRiD's image-level split for its later R2/R3 track and never claim patient-level independence without
  evidence.
- Treat unannotated IDRiD regions as `UNKNOWN` or `WEAK_NEGATIVE` unless a verified source rule supports clean negatives.
- Do not convert MMRDR image-level lesion presence into ROI geometry.
- Do not silently substitute model assets or use a TinyTestEncoder fallback.
- Do not upload private data or derived artifacts; no cloud provisioning occurs in P0.
- Do not execute R1 during P0; P0 only determines whether R1 may unlock.
