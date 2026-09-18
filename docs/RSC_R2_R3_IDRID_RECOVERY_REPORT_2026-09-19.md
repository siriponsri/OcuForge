# R2/R3 IDRiD Recovery Report

**Date:** 2026-09-19
**Branch:** `agent/r2-r3-idrid-recovery`
**Lane:** IDRiD research-only; DDR/OIA-DDR excluded
**Preflight:** `PASS_WITH_WARNINGS`
**R2:** `PASS_WITH_WARNINGS`
**R3:** `BLOCKED_IMPLEMENTATION`

## Bounded outcome

The official OWNER Drive folder was inspected read-only and the source-derived `A. Segmentation.zip` was verified
locally. Only the 81 segmentation images, four supported lesion-mask families, and the two source license files were
copied into ignored local campaign state; Disease Grading, Localization, and Optic Disc content was not copied.

R2 spatial derivation and geometry/provenance QA completed on CPU with one class-level foreground bounding-box ROI per
non-empty lesion mask. R3 training/evaluation did not start. The coordinator's official RunPod REST read-only
preflight returned HTTP 200 with zero active Pods, and the required one-time credentialed MLflow read-only probe for
`ocuforge-r3-roi` returned HTTP 404 without any write. The committed models package still has no R3 supported-lesion
classifier train/eval entrypoint or R3 input contract: its only lesion-related model path is the global DR MIL
pipeline, which requires feature-indexed `ImageManifest` records and `dr_grade`/`binary_dr` targets rather than the
R2 spatial ROI manifest. The local environment also lacks Torch, but that is secondary because no executable R3 path
exists to run in an approved PyTorch Pod; no Pod or paid resource was created (`USD 0`).

## Source and recursive inventory

- Official source: OWNER Drive folder ID `1JYKhcSf9IWjIItbGtq3mN4hTEl5Of_jp`; the folder URL returned HTTP 200.
- Top-level source entries observed: `A. Segmentation` (included), `B. Disease Grading` (excluded), `C. Localization`
  (excluded), and `Instruction.txt` (metadata only).
- The extra same-name directory level was observed as `A. Segmentation/A. Segmentation` (Drive item ID
  `12RBkYtxMTLmig83078YIjkgwPiYGw7Ul`); its required children were `1. Original Images`, `2. All Segmentation
  Groundtruths`, `CC-BY-4.0.txt`, and `LICENSE.txt`.
- The recursively enumerated extracted source contained 81 JPG images and 363 TIF files, including 81 Optic Disc
  masks. The acquired campaign subset contains 81 JPG, 282 supported-lesion TIF, and 2 license files (365 files;
  460,390,075 bytes), with zero Disease Grading, Localization, or Optic Disc files.
- Source archive integrity: 463 ZIP members (446 files, 17 directories), CRC test passed, archive SHA-256
  `f9a7fc0f7d228e326ca8ba61cfc99d54de689c52e44f52bde9917c78b07a1eaf`.
- Authenticated OWNER identity was not independently verified by this worker; this is a warning, not a claim of
  authenticated access. The local archive is recorded as `OWNER_ACQUIRED_OFFICIAL_IDRID` based on the owner-specified
  folder and source-derived local copy. No mirror, DDR, or OIA-DDR content was used.

The complete relative inventory, byte sizes, and SHA-256 values are in ignored local evidence at
`local-state/campaigns/r2-r3-idrid-20260919/idrid_acquisition_manifest.json`.

## Preflight checks

- Copy integrity: all 365 acquired files matched their source-derived counterparts by byte size and SHA-256.
- Images: 54 released train IDs (`IDRiD_01`-`IDRiD_54`) and 27 released test IDs (`IDRiD_55`-`IDRiD_81`); all are
  4288x2848 JPG files, with 81 unique image SHA-256 values and zero exact cross-split duplicates.
- Masks: all present supported-lesion masks are 4288x2848 and map to an image by ID stem; no mask/image dimension or
  geometry-bound violations were found. Supported-mask counts are MA 81, hemorrhage 80, hard exudate 81, and soft
  exudate 40.
- Missing mask files remain `UNKNOWN`: hemorrhage `IDRiD_43`, soft-exudate 28 train IDs, and soft-exudate 13 test IDs.
  No unannotated region was converted to a verified negative. `WEAK_NEGATIVE` remains reserved for an explicitly
  present but empty mask, and `NO_SUPPORTED_LESION_IN_ROI` remains ROI-scoped rather than a global negative.
- R2 produced 282 positive class ROIs (MA 81, hemorrhage 80, hard exudate 81, soft exudate 40), preserving the
  released split before derivation. Geometry is recorded with pixel and normalized coordinates, source image/mask
  hashes, and source-relative paths in `local-state/campaigns/r2-r3-idrid-20260919/r2_roi_manifest.json`.

## R3 gate and next safe action

R3 is `BLOCKED_IMPLEMENTATION`, not `BLOCKED_RUNTIME_AUTH`. The exact entrypoint audit found only
`eyes-detected-models/src/eyes_detected/lesions/interface.py` (a protocol) and the generic global DR
`eyes-detected-models/src/eyes_detected/pipeline/{train,evaluate}.py` path; no R3 classifier module, train/eval CLI,
R3 config, ROI crop/image manifest, or supported-lesion target manifest is committed. The generic path cannot be
repurposed without inventing a scientific pipeline: it trains global `dr_grade`/`binary_dr` targets over feature
bags, while R2 records 282 class-level positive bounding-box ROIs and preserves missing masks as `UNKNOWN` rather
than supplying the required five-class ROI training/evaluation contract.

The local runtime probe found `torch_present=False`, `mlflow_present=False`, and `runpodctl_present=False`; Torch is
not itself the blocker because official RunPod REST control is restored and no executable R3 workload exists to send
to a PyTorch Pod. The single credentialed MLflow GET probe used the configured URI and experiment name
`ocuforge-r3-roi`, returned HTTP 404, and performed no write. No model, metric, checkpoint, DagsHub run, Pod, Network
Volume, raw-data upload, or export was created; runtime and estimated cost remain zero, and Pod termination is not
applicable because no Pod was created.

Follow-up validation passed for JSON parsing of the receipt and both ignored R2 manifests,
`python scripts/validate_r0_r1.py`, and `git diff --check`. The focused pytest command was not run because the
approved launcher environment has no
`pytest` module; no dependency was installed.

Do not infer R3 metrics from the R2 ROI inventory or create a paid Pod. The next safe gate is an owner-approved,
contracted R3 classifier train/eval entrypoint and its compatible ROI inputs; implementing that scientific path is
outside this bounded recovery checkpoint.
