# OcuForge Operational Handoff

**Updated:** 2026-09-18
**Authority:** Operational state only. Contracts and the active master plan remain authoritative.

## Current gate/status

```text
R0_V3=PASS
R0_DATASET_TAXONOMY=PASS
R1_P0_ACQUISITION_PREFLIGHT=BLOCKED
R1_GLOBAL_BENCHMARK=READY_NOT_EXECUTED
CURRENT_R1_CHAMPION=NONE
```

R0 scientific evidence review passed. R1-P0 Global is the next and only permitted execution gate. Its allowed terminal
outcomes are `PASS`, `PASS_WITH_WARNINGS`, and `BLOCKED`; `PASS` or `PASS_WITH_WARNINGS` unlocks candidate training only
when no blocking finding remains. It does not authorize cloud provisioning or execute R1 itself.

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
- Decoupled IDRiD acquisition from the R1 critical path while preserving its source evidence and conservative negative
  policy for R2/R3.
- Added explicit P0 state/outcome rules, research/deployment license eligibility fields, artifact warning propagation,
  and separate evidence-audit/gate-decision dates.
- Updated active status documents, the R1 registry, report generator, tests, and offline validator for the simplified
  R1-P0 Global gate.

## R1-P0 decision and checks

The campaign cannot proceed: R1 remains locked by R1-P0 `BLOCKED`. The owner-authorized RunPod lifecycle smoke
verified creation/readiness, remote execution, exact C2 metadata access, Pod roots, local sentinel export/hash, stop,
termination, and confirmation that no Pod remained. The prior stop/start probe failed only because the provider had
insufficient GPU capacity; under the revised runbook this is recovery-path evidence and the infrastructure result is
`RUNPOD_AUTOMATION_SMOKE=PASS_WITH_WARNINGS`. The rotated HF credential was not placed in Pod metadata/environment
or exposed by the retry path. Owner governance authorizes IDRiD research-only RunPod execution under the public-data
boundary; IDRiD remains deferred to R2/R3 and is not an R1-P0 blocker.

See the machine-readable P0 contract and its redacted execution receipt. The short form is:

- `PASS`: exact C2 gated metadata access inside the Pod at revision
  `5931719e67bbdb9737e363e781fb0c67687896bc`; no model or data bytes were downloaded.
- `PASS`: Pod-side provider-neutral roots, remote command execution, sentinel export, and matching SHA-256.
- `PASS_WITH_WARNINGS`: `RUNPOD_AUTOMATION_SMOKE`; normal-path controls passed and the recovery-only stop/start probe
  was not a mandatory success condition. The Pod was terminated and confirmed gone.
- `PASS`: credential safety; the rotated HF credential was propagated only after SSH connection through a non-logging
  stdin path and was not placed in Pod metadata/environment or recorded in repository evidence.
- `NOT_EXECUTED`: MMRDR dataset/archive integrity, extracted inventory, schema/split smoke, and duplicate checks.
- `NOT_EXECUTED`: preprocessing and model loading because no bytes were acquired.
- IDRiD acquisition, mask coverage, and image-level split checks are deferred to R2/R3; unannotated regions remain
  `UNKNOWN`/`WEAK_NEGATIVE` unless acquisition evidence supports clean negatives.

The prior uncommitted smoke evidence remains preserved as historical evidence. The 2026-09-18 retry used Pod
`jinjh504k0b9gm` without an HF token in Pod metadata or environment. It passed create/readiness, remote command,
exact C2 metadata access at revision `5931719e67bbdb9737e363e781fb0c67687896bc`, writable Pod roots, local export,
remote/local hash match (`8ea23673cc8a936b490a8b8c7c1c88de721959ab92833b0a64acbbe0319438a1`), stop, termination, and
confirmation that no Pod remained. The rotated HF credential was propagated only after SSH connection through a
stdin-fed curl config, with no temporary file or logged value. The single restart attempt returned provider success,
but the post-restart sentinel was not verifiable after a bounded readiness wait; this is recorded as a non-blocking
recovery-path warning under the revised runbook. `RUNPOD_AUTOMATION_SMOKE=PASS_WITH_WARNINGS`; long-run execution
remains locked by R1-P0, not by the smoke result.

## Important artifacts/files

- `docs/RSC_R0_DATASET_TAXONOMY_FREEZE_v0.1.json` - authoritative R0 evidence record and future manifest.
- `docs/POC_MASTER_PLAN.md` - authoritative project direction.
- `docs/R0_DATASET_SUPERVISION_FREEZE.md` - R0 protocol and PASS outcome.
- `docs/R1_P0_ACQUISITION_PREFLIGHT.md` - next gate and operator checklist.
- `docs/R1_P0_ACQUISITION_PREFLIGHT.json` - machine-readable P0 contract.
- `eyes-detected-models/configs/research/r1-global-benchmark.json` - R1 C0/C1/C2 readiness registry; no measured result.
- `R0_DATASET_COMPARISON_AND_SOURCE_GUIDE.md` - research companion, not authority.
- `validation/FINAL_DELIVERY_REPORT.md` - repository validation report.

## Exact owner-resolvable next action

The HF credential has been rotated and the secure post-connect path is now required. Do not ask for or place a secret
in this handoff. Acquire only the frozen MMRDR and C0/C1/C2 inputs after R1-P0 is authorized; do not train during
the preflight.

From a clean machine/session:

```powershell
git pull
```

Then follow `docs/R1_P0_ACQUISITION_PREFLIGHT.md`. Acquire only MMRDR and the approved C0/C1/C2 assets. Do not
execute R1-P0 and R1 in the same phase; after the new preflight, stop for review and update this handoff with the
evidence and final P0 status. IDRiD acquisition belongs to the later R2/R3 gate and its compute location requires
explicit governance clearance.

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

Inspect `git status --short --branch` before editing. Do not train or execute R1 as part of R1-P0. Training may begin
only after P0 is `PASS` or `PASS_WITH_WARNINGS` with no blocker; copy P0 warnings to every R1 artifact.

## External dependencies/assets

- MMRDR: `https://figshare.com/articles/dataset/MMRDR/29423747`, DOI `10.6084/m9.figshare.29423747.v2`.
- IDRiD R2/R3 source: `https://idrid.grand-challenge.org/Data/`, IEEE DOI `10.21227/H25W98`.
- DDR/OIA-DDR: `https://github.com/nkicsl/DDR-dataset` (not admitted).
- C0: official ConvNeXt V2 Tiny ImageNet-22K 384px checkpoint URL in the freeze record.
- C1: `jusiro2/FLAIR`, revision `5f6bdd0a068353dc41a896ba3abdd7c0f6d35938`.
- C2: `facebook/dinov3-vitb16-pretrain-lvd1689m`, revision `5931719e67bbdb9737e363e781fb0c67687896bc`, gated.

## Do-not-do / governance reminders

- Do not train models, execute R1, or create a long-run Pod during R1-P0. The owner-authorized short lifecycle smoke
  is infrastructure evidence only.
- Acquire only the frozen public records/assets through official paths; do not use mirrors or silently substitute.
- Do not put hospital images, PHI, credentials, secrets, private data, model weights, or machine-local secrets in Git or
  this handoff.
- Do not convert MMRDR image-level lesion presence into ROI supervision.
- Do not infer ordinal grades from binary `DR`/`no-DR` labels, or treat `no-DR` as adjudicated grade 0.
- Do not treat unannotated IDRiD regions as verified negatives; this policy remains active for R2/R3.
- Do not call foundation-model evaluation clean external evidence while overlap is unknown or contaminated.
- Do not treat MIL attention as lesion localization or fundus/UWF evidence as OCT-confirmed DME.
