# OcuForge Operational Handoff

**Updated:** 2026-09-17
**Authority:** Operational state only. Contracts and the active master plan remain authoritative.

## Current gate/status

```text
R0_V3=PASS
R0_DATASET_TAXONOMY=PASS
R1_P0_ACQUISITION_PREFLIGHT=READY_NOT_EXECUTED
R1_GLOBAL_BENCHMARK=READY_NOT_EXECUTED
CURRENT_R1_CHAMPION=NONE
```

R0 scientific evidence review passed. R1-P0 is the next and only permitted execution gate. It must pass before any
candidate training; it does not authorize R1 training or cloud provisioning.

## What was completed

- Audited official MMRDR Figshare metadata and the Scientific Data descriptor for the UWF role, labels, split wording,
  file IDs, file sizes, license record, and image-level lesion semantics.
- Audited official IDRiD Grand Challenge and IEEE DataPort pages for modality, image counts, grading split, lesion-mask
  families, mask coverage, and the displayed CC BY 4.0 statement.
- Audited the official DDR/OIA-DDR repository and did not admit it because dataset terms, checksums, split files, and
  exact annotation inventory were not verified.
- Audited exact candidate asset sources: ConvNeXt V2-Tiny 22K/384, FLAIR Hub revision, and DINOv3 ViT-B/16 LVD-1689M.
- Recorded licenses, preprocessing, corpus/overlap status, deferred byte checks, taxonomy, negative ROI policy, and a
  provider-neutral future download manifest in `docs/RSC_R0_DATASET_TAXONOMY_FREEZE_v0.1.json`.
- Reclassified byte-dependent findings into `docs/R1_P0_ACQUISITION_PREFLIGHT.json` without deleting warnings.
- Updated active status documents, the R1 registry, and the offline validator for separate R0 and R1-P0 gates.

## R1-P0 checks not yet executed

See the machine-readable P0 contract. The short form is:

- Dataset/archive SHA-256, integrity, extracted inventory, schema/split smoke, and duplicate checks.
- C0/C1/C2 local weight SHA-256, gated access, preprocessing smoke, and model loading.
- Storage capacity, permissions, runtime readiness, and public/synthetic-only boundary.
- IDRiD examples remain UNKNOWN/WEAK_NEGATIVE unless acquisition evidence supports clean negatives.

## Important artifacts/files

- `docs/RSC_R0_DATASET_TAXONOMY_FREEZE_v0.1.json` - authoritative R0 evidence record and future manifest.
- `docs/POC_MASTER_PLAN.md` - authoritative project direction.
- `docs/R0_DATASET_SUPERVISION_FREEZE.md` - R0 protocol and PASS outcome.
- `docs/R1_P0_ACQUISITION_PREFLIGHT.md` - next gate and operator checklist.
- `docs/R1_P0_ACQUISITION_PREFLIGHT.json` - machine-readable P0 contract.
- `eyes-detected-models/configs/research/r1-global-benchmark.json` - R1 C0/C1/C2 readiness registry; no measured result.
- `R0_DATASET_COMPARISON_AND_SOURCE_GUIDE.md` - research companion, not authority.
- `validation/FINAL_DELIVERY_REPORT.md` - repository validation report.

## Exact next action

`git pull` -> execute R1-P0 acquisition preflight.

From a clean machine/session:

```powershell
git pull
```

Then follow `docs/R1_P0_ACQUISITION_PREFLIGHT.md`. Do not execute R1-P0 and R1 in the same phase; after P0, stop for
review and update this handoff with the evidence and final P0 status.

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

Inspect `git status --short --branch` before editing. Do not train or execute R1 as part of R1-P0.

## External dependencies/assets

- MMRDR: `https://figshare.com/articles/dataset/MMRDR/29423747`, DOI `10.6084/m9.figshare.29423747.v2`.
- IDRiD: `https://idrid.grand-challenge.org/Data/`, IEEE DOI `10.21227/H25W98`.
- DDR/OIA-DDR: `https://github.com/nkicsl/DDR-dataset` (not admitted).
- C0: official ConvNeXt V2 Tiny ImageNet-22K 384px checkpoint URL in the freeze record.
- C1: `jusiro2/FLAIR`, revision `5f6bdd0a068353dc41a896ba3abdd7c0f6d35938`.
- C2: `facebook/dinov3-vitb16-pretrain-lvd1689m`, revision `5931719e67bbdb9737e363e781fb0c67687896bc`, gated.

## Do-not-do / governance reminders

- Do not train models, execute R1, or provision cloud GPU during R1-P0.
- Acquire only the frozen public records/assets through official paths; do not use mirrors or silently substitute.
- Do not put hospital images, PHI, credentials, secrets, private data, model weights, or machine-local secrets in Git or
  this handoff.
- Do not convert MMRDR image-level lesion presence into ROI supervision.
- Do not infer ordinal grades from binary `DR`/`no-DR` labels, or treat `no-DR` as adjudicated grade 0.
- Do not treat unannotated IDRiD regions as verified negatives.
- Do not call foundation-model evaluation clean external evidence while overlap is unknown or contaminated.
- Do not treat MIL attention as lesion localization or fundus/UWF evidence as OCT-confirmed DME.
