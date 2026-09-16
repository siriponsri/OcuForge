# R0 Dataset & Supervision Freeze Protocol

**Phase:** R0
**Purpose:** Prevent label leakage, supervision mismatch, and taxonomy invention before model training.

## R0 question

For every candidate public dataset, answer:

> What exact prediction task can this dataset supervise without semantic reinterpretation?

## Required dataset record

Each dataset entry must record:

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

Do not write `mask`/`box`/`point` unless verified in the source release actually used.

## Track A — Global DR grading

Eligible datasets need genuine whole-image DR targets.

Possible targets:
- ordinal DR grade;
- binary referable/non-referable DR;
- binary DR/no-DR;
- other versioned global tasks.

These tasks are not interchangeable.

Rules:
- binary labels never become ordinal;
- dataset-specific grade schemes must map through an explicit protocol;
- unknown/ambiguous labels remain unknown;
- ungradable images must have explicit handling.

## Track B — Spatial ROI lesion training

A dataset is ROI-supervision eligible only if it contains usable spatial annotation or a defensible derivation from verified spatial annotation.

Initial canonical classes:

```text
MICROANEURYSM
INTRARETINAL_HEMORRHAGE
HARD_EXUDATE
SOFT_EXUDATE
NO_SUPPORTED_LESION_IN_ROI
```

Candidate source priority:
- IDRiD spatial lesion annotations;
- DDR spatially annotated lesion subset;
- additional public sources only after audit.

MMRDR image-level lesion presence may inform global/multi-label experiments, but must not be converted into lesion coordinates or masks.

## Negative ROI policy

Unannotated does not automatically mean negative.

Every negative ROI must have a provenance category:

```text
VERIFIED_TRUE_NEGATIVE
CURATED_BACKGROUND
WEAK_NEGATIVE
UNKNOWN
```

Only categories approved by the R0 config may enter clean-negative evaluation.

`NO_SUPPORTED_LESION_IN_ROI` is an inference/UI class meaning no supported lesion was identified in the selected ROI at threshold. It is not synonymous with normal retina.

## Split protocol

Order is fixed:

```text
source records
-> identity normalization
-> patient/eye/image split
-> freeze split manifest
-> derive ROIs/patches
```

Forbidden:

```text
source images
-> generate many patches
-> random patch split
```

If patient IDs do not exist, document the limitation and use the strongest remaining identity key without claiming patient-level independence.

## Acceptance evidence

R0 can be `PASS` only if:

- every selected dataset has a source/version/license/access record;
- supervision type is verified;
- global vs spatial usage is explicit;
- taxonomy uses only supported classes;
- negative policy is explicit;
- split-before-derivation is enforced;
- dataset limitations are recorded;
- machine-readable config validates;
- tests cover supervision type, taxonomy mapping, and split leakage guards.

Otherwise: `R0_DATASET_TAXONOMY=BLOCKED` with the exact blocker.
