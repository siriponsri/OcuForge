# R3 IDRiD ROI Execution Report

**Date:** 2026-09-19
**Branch:** `agent/r3-roi-execution`
**Lane:** IDRiD research-only; DDR/OIA-DDR excluded
**Preflight:** `PASS_WITH_WARNINGS`
**Outcome:** `PASS_WITH_WARNINGS` for engineering execution only

## Bounded outcome

One R3 checkpoint was executed from the accepted R2 IDRiD evidence using the
separate `R3_MASKED_LINEAR_RGB_BASELINE` NumPy path. The checkpoint used local
CPU execution, created no Pod, uploaded no data, and had an estimated cost of
USD 0.

The source provenance remains `OWNER_ACQUIRED_OFFICIAL_IDRID`. The released
split and R2 ROI identity set were preserved: 81 source images, 54 TRAIN and
27 TEST images, and 282 input/target rows. The derived checkpoint contained
187 TRAIN rows and 95 TEST rows across the four supported lesion classes.

## Integrity and semantics

- R2 archive, copy, image, mask, geometry, split, and cross-split hash checks
  were reused from the accepted recovery evidence.
- All 282 rows are positive mask-derived ROI rows; no negative rows were
  invented.
- Missing or unannotated mask evidence remains `UNKNOWN` and is excluded from
  supervision. `WEAK_NEGATIVE` remains reserved for present-empty masks.
- The four supported classes are `MICROANEURYSM`,
  `INTRARETINAL_HEMORRHAGE`, `HARD_EXUDATE`, and `SOFT_EXUDATE`.

## Execution evidence

The complete ignored local output is under
`local-state/campaigns/r2-r3-idrid-20260919/r3-execution-20260919-final/`.
It includes the manifest build, JSONL inputs/targets, local-only model, train
receipt, TEST evaluation receipt, and artifact manifest. No raw dataset,
checkpoint, or private artifact is tracked by Git.

The TEST receipt reports 27 observed rows for each of the first three classes
and 14 observed rows for `SOFT_EXUDATE`; each observed subset is positive-only
and therefore reports thresholded accuracy of 1.0. These values are not a
scientific performance result and must not be used for model selection,
generalization, lesion-localization, or clinical claims.

DagsHub/MLflow reused the prior read-only probe for `ocuforge-r3-roi`, which
returned HTTP 404; no write was attempted. Local evidence is authoritative.

## Validation and remaining gates

- Focused R3 tests: `5 passed`.
- Ruff check for the checkpoint script: passed.
- Python compilation for the checkpoint script: passed.
- `git diff --check`: passed.
- R1-P0 remains blocked by the accepted MMRDR released-split duplicate groups;
  R1 training and the R1 benchmark remain forbidden.
- R3 remains `scientific_result_eligible=false` until a contract-complete
  evaluation with appropriate negative/unknown coverage is available.
