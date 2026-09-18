# R1-P0 Acquisition Preflight

**Status:** `R1_P0_ACQUISITION_PREFLIGHT=BLOCKED` · states: `READY_NOT_EXECUTED`, `RUNNING`,
`PASS_WITH_WARNINGS`, `PASS`, `BLOCKED`
**Authority:** [`POC_MASTER_PLAN.md`](POC_MASTER_PLAN.md)
**Machine-readable contract:** [`R1_P0_ACQUISITION_PREFLIGHT.json`](R1_P0_ACQUISITION_PREFLIGHT.json)

R1-P0 is the post-R0 acquisition and runtime gate. It may execute on the owner-authorized public RunPod runtime. It
exists because archive/file hashes, extracted inventories,
schema smoke tests, model weight hashes, gated access, and model loading cannot be verified before the authorized bytes
are acquired. It is not an R1 training run.

## Gate state

```text
R0_V3=PASS
R0_DATASET_TAXONOMY=PASS
R1_P0_ACQUISITION_PREFLIGHT=BLOCKED
R1_GLOBAL_BENCHMARK=READY_NOT_EXECUTED
CURRENT_R1_CHAMPION=NONE
TRAINING_UNLOCK=FORBIDDEN_UNTIL_PASS_OR_PASS_WITH_WARNINGS
```

`PASS` requires every required check to pass. `PASS_WITH_WARNINGS` permits only `PASS` or
`PASS_WITH_WARNINGS` checks, requires no blocker, and requires every warning to be recorded and copied into R1
artifacts. `BLOCKED` is reserved for an invalidating, unauthorized, corrupt, leaking, incompatible, or impossible
R1 execution condition. `RUNNING` is not an unlock state. The 2026-09-18 receipt records the infrastructure smoke as
`PASS_WITH_WARNINGS`; `MODEL_ASSET`, `DATASET_ARCHIVE`, `DATASET_SCHEMA_SPLIT`, `PREPROCESSING`, and
`MODEL_LOADING` remain blocked or `NOT_EXECUTED` because no data or model bytes were acquired.

## Current decision

R1 training cannot proceed because R1-P0 is `BLOCKED`; P0 execution itself is authorized. Authenticated access to the exact C2 revision was verified inside one
short-lived RunPod, all four Pod-side OcuForge roots were writable, and no model or data bytes were downloaded. The
normal smoke path passed; the prior stop/start probe failed only because RunPod reported insufficient free GPUs and
the retry's sentinel persistence was not verified. Under the revised runbook this is a non-blocking recovery-path
warning, so `RUNPOD_AUTOMATION_SMOKE=PASS_WITH_WARNINGS`. The rotated credential was propagated only after
connection through a non-logging stdin path and was not placed in Pod metadata/environment. The structured,
redacted execution receipt contains no secret values, PHI, image bytes, or private artifacts.

Owner governance now authorizes IDRiD research-only RunPod execution under the public-data boundary. This does not
add IDRiD as an R1-P0 blocker; IDRiD remains deferred to the R2/R3 preflight.

## Latest lifecycle smoke retry

The prior uncommitted smoke evidence remains preserved. The 2026-09-18 retry used one short-lived secure RTX 4090
Pod with no HF token in Pod metadata or environment. Post-connect C2 metadata access passed for the exact DINOv3
revision; the token traveled only through an SSH stdin-fed curl config, was not written to a temporary file, and was
not logged. Remote command, writable roots, sentinel export, matching SHA-256, stop, termination, and confirmation
that no Pod remained all passed. The one restart attempt returned provider success, but the sentinel was not verifiable
after a bounded readiness wait; this is recorded as the allowed recovery-path warning. Therefore
`RUNPOD_AUTOMATION_SMOKE=PASS_WITH_WARNINGS` with no smoke blocker.

R1 training remains forbidden. Do not start long-run training until R1-P0 acquisition, integrity, schema/split,
preprocessing, model-load, and forward-pass checks reach `PASS` or `PASS_WITH_WARNINGS` with no blocker. The accepted
infrastructure smoke is already `PASS_WITH_WARNINGS` and does not need to be repeated unless materially invalidated.

## Required sequence

1. `git pull` and inspect `HANDOFF.md`.
2. Resolve the four provider-neutral storage roots without placing secrets in Git.
3. Authenticate and accept the exact gated C2 asset through the official Hugging Face path, without placing credentials
   or tokens in Git.
4. Configure the provider-neutral roots and runtime on the authorized RunPod target; local Windows torch/disk capacity
   is not a P0 prerequisite.
5. Preserve the owner decision authorizing IDRiD research-only RunPod execution under the public-data boundary.
6. Acquire only the frozen MMRDR-UWF record and the exact C0/C1/C2 assets through their official access paths.
7. Compute and record archive/file SHA-256 values, integrity results, and extracted inventories locally.
8. Run MMRDR schema, split, identity, duplicate, and preprocessing smoke checks. IDRiD acquisition and mask-coverage
   checks are deferred to R2/R3 preparation and do not block R1.
9. Acquire only the exact C0/C1/C2 assets and record local SHA-256, terms, gated-access status, and loading results.
10. Update the P0 record only with safe metadata; training is permitted after `PASS` or `PASS_WITH_WARNINGS` when no
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
- Do not upload private data or derived artifacts. P0 may provision only its authorized short-lived public-data
  validation runtime; it does not authorize a long-run training Pod.
- Do not execute R1 during P0; P0 execution determines whether R1 may unlock.
