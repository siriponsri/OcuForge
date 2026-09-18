# R2/R3 IDRiD Recovery Report

**Date:** 2026-09-19
**Branch:** `agent/r2-r3-idrid-recovery`
**Lane:** IDRiD research-only; DDR/OIA-DDR excluded
**Preflight:** `PASS_WITH_WARNINGS`
**R2:** `PASS_WITH_WARNINGS`
**R3:** `BLOCKED`

## Bounded outcome

The official OWNER Drive folder was inspected read-only and the source-derived `A. Segmentation.zip` was verified
locally. Only the 81 segmentation images, four supported lesion-mask families, and the two source license files were
copied into ignored local campaign state; Disease Grading, Localization, and Optic Disc content was not copied.

R2 spatial derivation and geometry/provenance QA completed on CPU with one class-level foreground bounding-box ROI per
non-empty lesion mask. R3 training/evaluation did not start because this worker has no installed Torch runtime, no
authenticated RunPod control path, and no authenticated MLflow/DagsHub credentials; no Pod or paid resource was
created (`USD 0`).

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

R3 remains locked. The installed Python environment has Pillow but not Torch; `runpodctl` is absent, the local RunPod
config has no non-empty key, and no `MLFLOW_TRACKING_USERNAME` or `MLFLOW_TRACKING_PASSWORD` is available for the
required one-time in-memory authenticated probe. No model, checkpoint, DagsHub run, Pod, Network Volume, or raw-data
upload was created.

The next safe gate is to provide an already-authorized non-logging compute/runtime path and perform the required
in-memory MLflow probe, then run only the supported-lesion R3 baseline/evaluation from the verified local manifests.
Do not infer R3 metrics from the R2 ROI inventory or start a paid Pod before that gate passes.
