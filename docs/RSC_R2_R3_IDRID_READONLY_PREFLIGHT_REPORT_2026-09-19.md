# R2/R3 IDRiD Read-Only Preflight Report

**Date:** 2026-09-19
**Branch:** agent/r2-r3-idrid-execution
**Lane:** IDRiD research-only; DDR/OIA-DDR excluded
**Outcome:** BLOCKED

## Bounded result

The rerun stopped at the access gate. The OWNER Drive URL is reachable as an unauthenticated public HTML shell,
but no authenticated OWNER Drive/Colab path was available to this worker. The public shell is not treated as
authorized dataset access, so recursive inventory, acquisition, hashing, split checks, image/mask checks, and all
R2/R3 stages remain unexecuted.

## Read-only access evidence

- OWNER folder URL:
  https://drive.google.com/drive/folders/1JYKhcSf9IWjIItbGtq3mN4hTEl5Of_jp?usp=sharing
- The URL returned HTTP 200 with text/html; this proves URL reachability only.
- The public shell showed the top-level names A. Segmentation, B. Disease Grading, C. Localization, and
  Instruction.txt. This is not an authenticated recursive inventory, and the extra same-name directory level
  check was not run.
- The MaxPlus-launched read-only probe found no Drive, Google, Colab, or browser-backed authenticated capability.
- The Colab browser connection attempt returned false.
- Official IDRiD Grand Challenge and IEEE DataPort pages returned HTTP 200, but remain source metadata only.

## RunPod and resource state

- MaxPlus launcher: C:\Users\Siripon Sri\bin\maxplus-codex.cmd (invoked successfully).
- runpodctl was absent; RUNPOD_API_KEY was absent; the local RunPod config existed with no non-empty key.
- Unauthenticated read-only GET https://rest.runpod.io/v1/pods returned HTTP 401.
- RunPod MCP authentication was rejected or unavailable; account-wide inventory is
  NOT_VERIFIED_UNAUTHENTICATED.
- No Pod, Network Volume, experiment, R2 construction, R3 training, or R3 evaluation was started.
- IDRiD bytes downloaded: 0; archive/file hashes: unavailable; estimated lane cost: USD 0.

## Scientific checks

Image/mask identity, class coverage, released split verification, duplicate/leakage checks, and archive integrity
remain NOT_EXECUTED_NO_IDRID_BYTES. Supported classes remain MICROANEURYSM, INTRARETINAL_HEMORRHAGE,
HARD_EXUDATE, and SOFT_EXUDATE; unannotated regions remain UNKNOWN or WEAK_NEGATIVE, and
NO_SUPPORTED_LESION_IN_ROI remains a scoped ROI semantic rather than a global negative.

R2 spatial construction, geometry/provenance QA, R3 supported-lesion training/evaluation, and the evidence freeze
are locked. DDR/OIA-DDR was not admitted.

## Validation

- Existing blocked receipt docs/RSC_R2_R3_IDRID_EXECUTION_RECEIPT_2026-09-18.json: JSON parse PASS.
- New read-only receipt: JSON parse PASS.
- python scripts/validate_r0_r1.py: PASS.
- No code or runtime configuration was changed.

## Next action

Obtain an already-authorized non-logging OWNER Drive path and rerun only the IDRiD read-only inventory/preflight.
Do not proceed to R2/R3 until authenticated access and byte integrity checks pass or pass with warnings and no
blocking finding.
