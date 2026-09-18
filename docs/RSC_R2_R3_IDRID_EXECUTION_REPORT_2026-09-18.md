# R2/R3 IDRiD Execution Report

**Date:** 2026-09-18
**Branch:** `agent/r2-r3-idrid-execution`
**Base SHA:** `5f9187d`
**Lane:** IDRiD research-only; DDR/OIA-DDR excluded
**Outcome:** `BLOCKED`

## Blocker

The worker could not reach an authorized RunPod control plane. `runpodctl` is not installed, no RunPod MCP
control tool is connected, the local RunPod config has an empty `apikey`, and `RUNPOD_API_KEY` is absent from the
environment. The official REST v2 Pod inventory probe therefore could not authenticate.

The task requires stopping when the required control plane or current external credential is unavailable. No
tooling was installed, no secret was requested or printed, and no Pod was created.

## Source-only checks

The official source pages were reachable on 2026-09-18:

- [IDRiD Grand Challenge data page](https://idrid.grand-challenge.org/Data/) returned HTTP 200 and displayed the
  CC BY 4.0 statement and the four lesion mask families.
- [IEEE DataPort IDRiD record](https://ieee-dataport.org/open-access/indian-diabetic-retinopathy-image-dataset-idrid) returned
  HTTP 200 and described 516 images, a 413/103 train/test release split, JPG images, and TIF lesion groundtruths.
  The page directs users through an IEEE DataPort login/account route for downloads.

These are source metadata observations only. They do not establish authenticated access, archive integrity,
file hashes, extracted inventory, or usable local bytes.

## Required checks not executed

IDRiD archive/file SHA-256, archive integrity, extracted inventory, image/mask identity, class-specific coverage,
released split inventory, duplicate/near-duplicate leakage review, R2 spatial construction, geometry/provenance QA,
and R3 train/evaluation were not executed because no authorized data bytes were acquired.

The frozen conservative policy remains active: unannotated regions are `UNKNOWN` or `WEAK_NEGATIVE`; they are not
hard negatives without exhaustive annotation evidence and a verified geometry rule. The supported classes remain
`MICROANEURYSM`, `INTRARETINAL_HEMORRHAGE`, `HARD_EXUDATE`, and `SOFT_EXUDATE`, with
`NO_SUPPORTED_LESION_IN_ROI` retaining its scoped ROI meaning.

## Resource and governance state

No Pod, Network Volume, dataset bytes, model weights, private data, PHI, or credential value was used. No R1-P0
state was changed or awaited. The account-wide Pod inventory is unverified because the control plane was
unauthenticated; the worker-created Pod list is empty and lane cost is USD 0.

The machine-readable receipt is
[`RSC_R2_R3_IDRID_EXECUTION_RECEIPT_2026-09-18.json`](RSC_R2_R3_IDRID_EXECUTION_RECEIPT_2026-09-18.json).

## Validation

- `python scripts/validate_r0_r1.py`: PASS.
- `python -m pytest`: not run; `pytest` is unavailable in the active Python environment.
- `python -m ruff check .`: not run; `ruff` is unavailable in the active Python environment.
- `git diff --check`: PASS before this evidence-only change.

## Next action

Restore an authorized non-logging RunPod control path and authorized external IDRiD access, then rerun only the
IDRiD acquisition/preflight. Do not construct ROIs or train/evaluate R3 until that preflight is `PASS` or
`PASS_WITH_WARNINGS` with no blocker. Do not install tooling or request secrets through this worker.
