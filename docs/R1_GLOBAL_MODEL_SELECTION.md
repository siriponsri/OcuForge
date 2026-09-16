# R1 Global DR Model Selection Protocol

**Phase:** R1
**Purpose:** Select a defensible global DR architecture using controlled baselines.

## Principle

DINOv3 + Attention MIL is the leading candidate, not the predetermined result.

The experiment must answer three separate questions:

1. Does DINOv3 representation transfer well to the selected retinal dataset?
2. Does preserving local patches beat global resizing/pooling?
3. Does learned attention aggregation beat simple pooling enough to justify added complexity?

## Baseline ladder

### G0 — Compact sanity baseline

Use a standard compact supervised image classifier.

Purpose:
- validate dataset/split/training/evaluation path;
- provide a non-foundation baseline;
- detect pipeline bugs before expensive experiments.

### G1 — Frozen DINOv3 + global representation

Purpose:
- isolate encoder transfer quality;
- establish lowest-complexity DINOv3 baseline.

### G2 — Frozen DINOv3 + local patch pooling

Compare at least:
- mean pooling;
- GeM where implementation is clean and justified.

Max pooling may be included as a diagnostic but is not assumed competitive.

Purpose:
- test whether high-resolution local preservation improves grading.

### G3 — Frozen DINOv3 + Attention MIL

Patch features -> positional information where appropriate -> learned attention aggregation -> classifier/head.

Purpose:
- test adaptive regional aggregation.

Attention weights are not lesion masks.

### G4 — Global/local fusion

Run only if G1 and G2/G3 show complementary error patterns.

Purpose:
- preserve whole-retina context while retaining local lesion evidence.

### G5 — Limited partial fine-tuning

Unfreeze a bounded encoder portion, e.g. final block(s), only after a frozen candidate wins.

Do not begin with full fine-tuning.

## Head ablation

For genuine 0–4 ordinal DR targets, compare:

- standard multiclass CE head;
- CORAL or another explicitly versioned ordinal head.

Do not use ordinal losses for binary/non-ordinal targets.

## Experimental control

For fair G1–G3 comparison, hold constant where possible:

- frozen split;
- image preprocessing;
- patch geometry;
- encoder checkpoint/revision;
- training seed set;
- optimizer policy;
- early stopping policy;
- evaluation code;
- class weighting strategy;
- model-selection metric.

Use multiple seeds for the final shortlist when budget permits.

## Metrics

Primary for true ordinal grading:
- QWK.

Required companions:
- macro F1;
- per-class recall;
- balanced accuracy;
- confusion matrix;
- calibration;
- class support;
- AUROC/AUPRC where task semantics justify;
- latency;
- VRAM / runtime.

Do not select a champion from accuracy alone.

## External/generalization gate

Where an independent compatible dataset exists, evaluate the frozen selected model without reusing the final test labels for tuning.

Report:
- in-domain result;
- external/domain-shift result;
- differences in modality, acquisition, demographic/source mix, label protocol.

Do not imply external validity from an internal held-out split.

## Feature caching

Frozen DINOv3 stages may cache deterministic versioned features when:
- preprocessing and encoder revision are frozen;
- cache identity includes source image hash, model revision, patch/crop config, and preprocessing version.

Never reuse a cache across incompatible preprocessing/model revisions.

## R1 PASS condition

`R1_GLOBAL_MODEL=PASS` requires:

- real reviewed public data;
- authorized real DINOv3 weights;
- held-out evaluation;
- baseline comparison;
- selected architecture and rationale;
- artifact/model metadata;
- exact reproducible config/command;
- no leakage finding.

Preparation alone is `R1_READY`, not `PASS`.
