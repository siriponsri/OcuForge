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
when no blocking finding remains. Owner authorization permits P0 acquisition/runtime validation on public RunPod; it
does not authorize training or execute R1 itself.

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
- Executed the authorized R1-P0 acquisition/runtime checks on RunPod. MMRDR archive integrity, extracted inventory,
  schema, released split, model-asset hashes, official C0/C1/C2 loading, synthetic preprocessing, gated access,
  and storage/runtime checks are recorded in the redacted local evidence under `local-state/campaigns/`.

## R1-P0 decision and checks

R1 training cannot proceed because R1-P0 remains `BLOCKED`. The acquisition/runtime checks passed except for a released
MMRDR split-leakage finding: two exact duplicate-content groups cross the documented `tr`/train and `ts`/test
boundary. The official split is preserved; no rows were reshuffled or silently excluded. This is a blocking finding
until OWNER resolves the split protocol. The accepted lifecycle result remains `RUNPOD_AUTOMATION_SMOKE=PASS_WITH_WARNINGS`
because the normal path passed and stop/start persistence is recovery-path evidence only. The secure credential path
did not place the HF token in Pod metadata/environment or evidence. DagsHub/MLflow connectivity remains unresolved
and is non-blocking because complete local evidence exists. IDRiD research-only RunPod execution is authorized for
R2/R3, but its independent preflight remains pending authorized archive access.

See the machine-readable P0 contract and its redacted execution receipt. The short form is:

- `PASS`: MMRDR archive integrity and extracted inventory; 10,404 UWF rows/images with grades `0`-`4`, and the
  released `tr`/`ts` split preserved as 7,807/2,597.
- `PASS`: exact C0/C1/C2 asset hashes, gated access, official model loading, synthetic preprocessing, and CUDA
  forward passes. C0/C1/C2 outputs are recorded without exporting full checkpoints.
- `PASS`: Pod-side provider-neutral roots, remote execution, compact local evidence export, and matching SHA-256.
- `BLOCKED`: two exact duplicate-content groups cross the released MMRDR train/test split; R1 training remains locked.
- `PASS_WITH_WARNINGS`: `RUNPOD_AUTOMATION_SMOKE`; normal-path controls passed and the recovery-only stop/start probe
  was not a mandatory success condition. The Pod was terminated and confirmed gone.
- `PASS`: credential safety; the rotated HF credential was propagated only after SSH connection through a non-logging
  stdin path and was not placed in Pod metadata/environment or recorded in repository evidence.
- `PASS_WITH_WARNINGS`: DagsHub/MLflow read-only connectivity probe remained unresolved; local evidence is authoritative.
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
- `local-state/campaigns/ocuforge-r1-p0-20260918/r1-p0/` - ignored, compact P0 evidence and hash-verified export.

## Exact owner-resolvable next action

The immediate owner action is to review the two exact duplicate-content groups crossing the released MMRDR train/test
split. Do not ask for or place a secret in this handoff. Until the split-leakage finding is resolved in the governing
protocol, do not train R1 or create another long-run Pod. IDRiD remains an independent R2/R3 lane and DDR/OIA-DDR
remains not admitted.

From a clean machine/session:

```powershell
git pull
```

Then review `docs/R1_P0_ACQUISITION_PREFLIGHT.md` and the compact local evidence. Do not bypass the split-leakage
blocker, reshuffle the released split, or start R1 until OWNER approves a protocol-level resolution.

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

Inspect `git status --short --branch` before editing. The R1-P0 acquisition/runtime validation is complete and its
blocking split finding must be resolved before training. Training may begin only after P0 is `PASS` or
`PASS_WITH_WARNINGS` with no blocker; copy P0 warnings to every R1 artifact.

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
