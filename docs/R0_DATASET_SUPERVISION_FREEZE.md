# R0 Dataset, Supervision, Split, and Asset Freeze

**Status:** ACTIVE SUPPORTING PROTOCOL · `R0_V3=PASS / R0_DATASET_TAXONOMY=PASS`
**Authority:** [`POC_MASTER_PLAN.md`](POC_MASTER_PLAN.md)

R0 is a CPU/document/data-contract gate. It must finish before dataset download, model training, or R1 execution.
Post-download integrity and runtime checks belong to R1-P0.

## Required record for every candidate dataset

```yaml
dataset_id:
source:
version_or_revision:
access_status:
license_status:
modality:
image_count:
patient_id_available:
eye_id_available:
image_id_available:
global_labels:
ordinal_labels:
lesion_labels:
lesion_supervision:
  type: image_level | point | box | polygon | mask | none
  exhaustive: true | false | unknown
split_source:
known_limitations:
checksum_or_source_hash:
```

Do not claim a spatial supervision type that was not verified in the exact release under review.

## Task semantics

The R1 global target is genuine ordinal DR grade 0–4. Binary `DR`/`no-DR` experience labels remain binary and are
never mapped to grade 0–4. Unknown or ambiguous labels remain unknown. Ungradable images require an explicit policy.

The initial ROI classes are `MICROANEURYSM`, `INTRARETINAL_HEMORRHAGE`, `HARD_EXUDATE`, `SOFT_EXUDATE`, and
`NO_SUPPORTED_LESION_IN_ROI`. The last is an ROI inference/UI semantic, not proof of a normal eye. MMRDR image-level
lesion presence cannot create ROI coordinates, boxes, polygons, or masks.

Unannotated is not automatically negative. A negative ROI must be classified as verified true negative, curated
background, weak negative, or unknown, with the source annotation revision and geometry rule retained.

## Foundation-model overlap audit

For C1 FLAIR and C2 DINOv3, R0 records the pretraining corpus description, known included public datasets, overlap with
R1 selection/test/external data, status (`CONFIRMED`, `EXCLUDED`, `UNKNOWN`, or `POTENTIALLY_CONTAMINATED`), and claim
consequence. An overlap prevents a clean external-generalization claim unless resolved and disclosed.

## Split and leakage order

```text
source records
  -> normalize patient/eye/visit/image identity
  -> assign and freeze split
  -> derive ROIs/patches
```

Never generate patches/ROIs and then random-split them. If patient identity is unavailable, preserve the released split,
record the limitation, and do not claim patient-level independence.

## Current machine-readable record

[`RSC_R0_DATASET_TAXONOMY_FREEZE_v0.1.json`](RSC_R0_DATASET_TAXONOMY_FREEZE_v0.1.json) is the completed V3 freeze
record. It contains the candidate dataset decisions, reclassified acquisition findings, admitted taxonomy, negative
policy, split policy, model asset audit, and future download manifest. It does not contain downloaded dataset bytes or
model weights.

## R0 V3 outcome

```text
R0_DATASET_TAXONOMY=PASS
R1_P0_ACQUISITION_PREFLIGHT=READY_NOT_EXECUTED
R1_GLOBAL_BENCHMARK=READY_NOT_EXECUTED
CURRENT_R1_CHAMPION=NONE
```

MMRDR-UWF is eligible for R1-P0 as the primary R1 hypothesis; its released patient-level split and missing row-level
patient IDs remain a documented limitation. IDRiD is preserved as the primary spatial R2/R3 candidate and is outside
the R1 critical path; unannotated regions remain UNKNOWN/WEAK_NEGATIVE unless stronger evidence is obtained. DDR/OIA-DDR
is not admitted. C0/C1/C2 exact source revisions, licenses, preprocessing, overlap findings, and claim limits are
recorded. P0 owns all R1 local hash, archive, inventory, access, smoke, and loading checks.

## R0 PASS evidence

R0 passes when every selected dataset has verified source/version/license/access sufficient for planned acquisition,
supervision type, identity and split semantics, leakage limitations, taxonomy eligibility, conservative negative policy,
foundation overlap status/claim limits, exact future manifest, and exact model asset source/revision. Local file hashes,
archive integrity, byte inventories, and model loading are R1-P0 evidence rather than R0 requirements.
