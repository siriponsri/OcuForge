# R1-P0 RunPod Revalidation Receipt

**Recorded:** 2026-09-19 03:06 Asia/Bangkok  
**Campaign:** `ocuforge-r1-p0-20260919`  
**Scope:** bounded runtime, storage-root, compact-export, and hash revalidation on the owner-authorized public RunPod Pod. The accepted lifecycle smoke was reused; it was not repeated.

## Gate outcome

```text
R0_V3=PASS
R1_P0_EXECUTION_READY=YES
R1_P0_ACQUISITION_PREFLIGHT=BLOCKED
R1_TRAINING_READY=NO
RUNPOD_AUTOMATION_SMOKE=PASS_WITH_WARNINGS (reused)
```

The blocking finding remains unchanged: exact duplicate-content groups `tr003656.jpg`/`ts002433.jpg` and
`tr007667.jpg`/`ts002038.jpg` cross the released MMRDR `tr`/train and `ts`/test boundary. The released split was
not reshuffled and no rows were excluded. R1 training and C0/C1/C2 benchmark execution were not started.

The prior P0 evidence remains the source for the already completed acquisition checks: official MMRDR archive and
inventory, ordinal schema, exact C0/C1/C2 asset hashes, preprocessing, gated access, and model load/forward-pass.
This revalidation did not reacquire data or model bytes.

## Current Pod validation

| Check | Result | Evidence |
| --- | --- | --- |
| Pod | PASS | RunPod Pod `i2m2mxxx687n02`, secure RTX 4090, `$0.74/hour` reported by provider |
| SSH path | PASS | Direct TCP endpoint used with no PTY allocation |
| Runtime command | PASS | CUDA-visible PyTorch runtime and GPU query completed |
| Provider-neutral roots | PASS | `OCUFORGE_DATA_ROOT`, `OCUFORGE_MODEL_ROOT`, `OCUFORGE_CACHE_ROOT`, and `OCUFORGE_ARTIFACT_ROOT` created and writable |
| Network Volume | PASS | None attached; Pod-local `/workspace` only |
| Compact export | PASS | `local-state/campaigns/ocuforge-r1-p0-20260919/r1-p0/remote_compact_export.json` |
| Remote/local SHA-256 | PASS | `5b6ba1fe5560aafd8b7d6f97389a31da6208342007a7657d03af69fa8c66eebb` on both sides |
| Training/benchmark | PASS | Not executed |

The remote export contains runtime metadata, root status, scope, and warnings only. It contains no image bytes, PHI,
credentials, tokens, private data, checkpoints, or model outputs.

## Warnings and next action

- Reused `RUNPOD_AUTOMATION_SMOKE=PASS_WITH_WARNINGS`; the recovery-path stop/start probe remains a warning only.
- DagsHub/MLflow connectivity remains unresolved and non-blocking; local evidence is authoritative.
- Review and resolve the released-split duplicate leakage under the governing protocol before any R1 training.

## Teardown

Export verification completed before teardown. The official RunPod REST API returned `HTTP 204 No Content` with a
zero-byte response body for `POST /v2/pods/i2m2mxxx687n02/action` with action `terminate`. The first post-action
lookup returned `HTTP 404 Not Found`, the active-Pod list contained zero matches, and termination was confirmed.
