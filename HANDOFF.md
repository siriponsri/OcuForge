# OcuForge Operational Handoff

**Updated:** 2026-09-16
**Authority:** Operational state only. Contracts and the active master plan remain authoritative.

## Current gate/status

```text
R0_V3=COMPLETE
R0_DATASET_TAXONOMY=BLOCKED
R1_GLOBAL_BENCHMARK=READY_NOT_EXECUTED
CURRENT_R1_CHAMPION=NONE
```

R0 evidence review ended as BLOCKED. This is a deliberate evidence outcome, not a permission to substitute a dataset,
asset, split, or assumption.

## What was completed

- Audited official MMRDR Figshare metadata and the Scientific Data descriptor for the UWF role, labels, split wording,
  file IDs, file sizes, license record, and image-level lesion semantics.
- Audited official IDRiD Grand Challenge and IEEE DataPort pages for modality, image counts, grading split, lesion-mask
  families, mask coverage, and the displayed CC BY 4.0 statement.
- Audited the official DDR/OIA-DDR repository and did not admit it because dataset terms, checksums, split files, and
  exact annotation inventory were not verified.
- Audited exact candidate asset sources: ConvNeXt V2-Tiny 22K/384, FLAIR Hub revision, and DINOv3 ViT-B/16 LVD-1689M.
- Recorded licenses, preprocessing, corpus/overlap status, missing local hashes, taxonomy, negative ROI policy, and a
  provider-neutral future download manifest in `docs/RSC_R0_DATASET_TAXONOMY_FREEZE_v0.1.json`.
- Updated active status documents and the offline R0/R1 validator to preserve a valid BLOCKED R0 result.

## Active blockers/unverified evidence

See the six exact blockers in the machine-readable freeze record. The short form is:

- MMRDR current file metadata exposes IDs and sizes but not hashes; its data-license scope also needs reconciliation
  with the associated article copyright notice.
- MMRDR published UWF split wording does not expose row-level patient IDs for the required identity audit.
- IDRiD archive terms, complete file inventory, checksums, and exhaustive-negative semantics remain unverified.
- C0 has no local weight hash; C1 has documented overlap with IDRiD/OIA-DDR/EyePACS and no local hash; C2 is gated,
  has no local hash, and has unknown source-image overlap.

## Important artifacts/files

- `docs/RSC_R0_DATASET_TAXONOMY_FREEZE_v0.1.json` - authoritative R0 evidence record and future manifest.
- `docs/POC_MASTER_PLAN.md` - authoritative project direction.
- `docs/R0_DATASET_SUPERVISION_FREEZE.md` - R0 protocol and blocked outcome.
- `eyes-detected-models/configs/research/r1-global-benchmark.json` - R1 C0/C1/C2 readiness registry; no measured result.
- `R0_DATASET_COMPARISON_AND_SOURCE_GUIDE.md` - research companion, not authority.
- `validation/FINAL_DELIVERY_REPORT.md` - repository validation report.

## Exact next action

Resolve the frozen blockers in this order: reconcile MMRDR data-license scope; obtain authorized MMRDR/IDRiD metadata or
archives and compute local SHA-256 manifests; verify MMRDR identity/split metadata; define evidence-backed IDRiD negative
ROI policy; obtain and hash the approved C0/C1/C2 assets and record exact preprocessing and overlap evidence. Then rerun
the R0 audit and update this handoff before any R1 execution decision.

## Resume commands/checks

From the repository root after any authorized evidence update:

```powershell
python -m pytest
python -m ruff check .
python scripts/validate_configs.py
python scripts/validate_r0_r1.py
python scripts/package_check.py
git diff --check
```

Inspect `git status --short --branch` before editing. Do not run R1 as part of resuming R0.

## External dependencies/assets

- MMRDR: `https://figshare.com/articles/dataset/MMRDR/29423747`, DOI `10.6084/m9.figshare.29423747.v2`.
- IDRiD: `https://idrid.grand-challenge.org/Data/`, IEEE DOI `10.21227/H25W98`.
- DDR/OIA-DDR: `https://github.com/nkicsl/DDR-dataset` (not admitted).
- C0: official ConvNeXt V2 Tiny ImageNet-22K 384px checkpoint URL in the freeze record.
- C1: `jusiro2/FLAIR`, revision `5f6bdd0a068353dc41a896ba3abdd7c0f6d35938`.
- C2: `facebook/dinov3-vitb16-pretrain-lvd1689m`, revision `5931719e67bbdb9737e363e781fb0c67687896bc`, gated.

## Do-not-do / governance reminders

- Do not train models, execute R1, provision cloud GPU, or download large archives to make R0 appear active.
- Do not put hospital images, PHI, credentials, secrets, private data, model weights, or machine-local secrets in Git or
  this handoff.
- Do not convert MMRDR image-level lesion presence into ROI supervision.
- Do not infer ordinal grades from binary `DR`/`no-DR` labels, or treat `no-DR` as adjudicated grade 0.
- Do not treat unannotated IDRiD regions as verified negatives.
- Do not call foundation-model evaluation clean external evidence while overlap is unknown or contaminated.
- Do not treat MIL attention as lesion localization or fundus/UWF evidence as OCT-confirmed DME.
