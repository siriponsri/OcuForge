# OcuForge Research & POC Master Plan V2

**Status:** Authoritative owner-provided POC/research direction
**Purpose:** Replace the previous architecture-first R0/R1 assumptions with an evidence-driven model-selection plan while preserving OcuForge governance, contracts, privacy rules, and the existing GUI POC.

## 1. Decision summary

The project should **keep DINOv3 + patch Attention MIL as the leading global-DR candidate**, but it must no longer be treated as the predetermined champion.

The revised strategy is:

1. freeze data/supervision semantics first;
2. run controlled global-model baselines;
3. let held-out evidence select pooling/head/fine-tuning;
4. build the ROI lesion model as a **separate task** from global DR grading;
5. integrate the selected models into the existing DR Review Workspace rather than creating a competing frontend.

The current GUI package already supports the intended product direction: Overview, Screening/ROI review, Review Queue, Explainability, Model Comparison, Integrations, plus Label Studio configuration and explicit adapter/model contracts.

## 2. Non-negotiable invariants

- Hospital/private images, labels, embeddings, predictions, checkpoints, and derived artifacts remain on-prem only.
- Public cloud GPU may receive only reviewed public/synthetic data.
- Binary `DR` / `no-DR` labels must never be silently converted to ordinal grades 0–4.
- `no-DR` does not imply adjudicated ordinal grade 0.
- CORAL or any ordinal objective may be used only with genuine ordinal labels.
- DME remains a separate axis.
- MIL attention is aggregation evidence, not validated lesion localization.
- Research/POC output is decision support, not diagnosis.
- Split by patient/eye/image identity **before** generating derived ROIs/patches.
- Never random-split derived patches across train/test.
- GitHub contains code/config/safe manifests only; not dataset bytes, public model weights, feature caches, or scientific checkpoints.

## 3. Product architecture

```text
PUBLIC RETINAL DATA
        |
        +-----------------------+
        |                       |
        v                       v
 GLOBAL DR TRACK          ROI LESION TRACK
        |                       |
 DINOv3 candidate         spatial annotations
 + controlled pooling     + ROI/context crops
 + head ablation          + lesion classifier
        |                       |
        +-----------+-----------+
                    |
             VERSIONED MODEL API
                    |
        +-----------+------------+
        |                        |
 Label Studio CE          DR Review Workspace
 internal QA              customer-facing POC
        |
 optional CVAT advanced annotation
```

The two ML tracks may share encoder technology and common contracts, but they must have separate heads, objectives, evaluation protocols, and model identities.

## 4. Revised roadmap

### R0 — Dataset, supervision, taxonomy and split freeze

**Goal:** Establish exactly what each dataset can supervise.

Required outputs:

- dataset source/version/access/license record;
- modality and image characteristics;
- global labels available;
- lesion labels available;
- whether lesion supervision is image-level, point, box, polygon, or mask;
- patient/eye/image identifiers and limitations;
- split policy;
- taxonomy mapping;
- negative-ROI policy;
- machine-readable manifest/config;
- checksum/source provenance where possible.

**Important:** A dataset with image-level lesion labels does **not** become a spatial ROI dataset.

Initial ROI taxonomy target:

- `MICROANEURYSM`
- `INTRARETINAL_HEMORRHAGE`
- `HARD_EXUDATE`
- `SOFT_EXUDATE`
- `NO_SUPPORTED_LESION_IN_ROI`

Additional lesion classes may be admitted only when usable spatial supervision is verified. Do not invent classes to reach seven. Do not count optic disc as a lesion.

`NO_SUPPORTED_LESION_IN_ROI` means no supported lesion class is identified within the selected ROI at the configured decision threshold. It does not mean normal eye, no DR, or no retinal pathology.

R0 exits only as `PASS` when source, supervision semantics, taxonomy, split policy, and limitations are documented and internally consistent.

---

### R1 — Global DR model benchmark

**Goal:** Select the global DR architecture from controlled evidence, not prior preference.

Run the smallest useful ladder first:

- **G0** compact supervised sanity baseline (e.g. EfficientNet/ConvNeXt class)
- **G1** frozen DINOv3 + global pooling
- **G2** frozen DINOv3 + patch mean / GeM pooling
- **G3** frozen DINOv3 + Attention MIL
- **G4** global + local/Attention fusion if G1–G3 justify it
- **G5** best prior model + limited partial fine-tuning (e.g. last block) only if justified

For true ordinal DR labels, compare at minimum:
- standard multiclass head/loss;
- CORAL or another explicitly versioned ordinal head.

Do **not** assume CORAL is better before ablation.

Primary selection:
- QWK for genuine ordinal grading.

Companions:
- macro F1;
- per-class recall/sensitivity;
- balanced accuracy;
- confusion matrix;
- AUROC/AUPRC where meaningful;
- calibration;
- class support;
- inference latency;
- model size/VRAM;
- external/domain-shift evaluation when a valid independent dataset is available.

Attention visualization is explanatory aggregation evidence only.

R1 becomes `PASS` only after real public data + real authorized DINOv3 weights + held-out results + versioned artifact metadata exist.

---

### R2 — Spatial ROI dataset builder

**Goal:** Convert verified spatial lesion annotations into leakage-safe ROI examples.

Rules:

- split original patient/eye/image identities first;
- only then derive lesion-centered ROIs;
- retain source image hash, dataset, source annotation identity, original geometry, crop geometry, preprocessing version;
- generate context-aware crops;
- record exact positive lesion source;
- do not treat arbitrary unannotated retina as a true negative unless annotation exhaustiveness is verified.

Negative hierarchy:

1. verified/exhaustively annotated true negative region;
2. curated background/normal region with documented rule;
3. weak negative with explicit weak status;
4. unknown region — not usable as a clean negative.

Build multi-scale ROI views where practical:
- tight ROI;
- context ROI;
- optional wider retinal context.

---

### R3 — ROI lesion classifier benchmark

**Goal:** Select a model for user-selected ROI → ranked lesion suggestion.

The ROI model is **not** the MIL attention map.

Preferred benchmark families:

- crop-only compact baseline;
- DINOv3 frozen ROI feature baseline;
- ROI + context dual/multi-scale feature fusion;
- partial fine-tuning only after frozen baselines;
- detector/segmenter branch only if the supervision/task requires automatic localization.

Output contract:

```text
ROI + image identity + geometry
    -> top label
    -> calibrated probability
    -> top-k alternatives
    -> model name/version
    -> threshold/status
```

Evaluate:
- macro F1;
- per-class precision/recall;
- balanced accuracy;
- confusion matrix;
- AUROC/AUPRC where meaningful;
- calibration;
- class counts;
- no-supported-lesion behavior;
- latency.

For microaneurysm and other tiny lesions, preserve sufficient native resolution and evaluate crop/context size rather than relying on aggressively resized full images.

SAM2/SAM3 may later refine a region boundary, but should not be the primary lesion classifier unless a separate experiment demonstrates that role.

---

### R4 — Label Studio Community interactive POC

Internal QA workbench only.

Required flow:
`model suggestion -> confirm / correct / reject / escalate`

Use the existing GUI package taxonomy/decision semantics as a starting contract:
- point / rectangle / polygon ROI;
- original model output retained;
- reviewer decision stored separately;
- reviewer certainty/note may be recorded;
- Label Studio credentials remain server-side behind a trusted bridge.

No dependence on paid Label Studio browser plugin features.

CVAT remains available for advanced CV annotation/segmentation work and is not removed.

---

### R5 — DR Review Workspace integration

The uploaded **DR Review Workspace — Screening Support POC** is the preferred customer-facing UX reference.

Do not build a competing dashboard unless the owner explicitly requests replacement.

Preserve its current information architecture:

- Overview
- Screening / ROI annotation
- Review Queue
- Explainability
- Model Comparison
- Integrations

Current intended model endpoints:

- `POST /v1/infer/global`
- `POST /v1/infer/lesion-roi`
- `GET /v1/models`
- `POST /v1/explain/roi`
- `POST /v1/evaluate/model-diff`

The latter two remain proposed integration targets until implemented.

The browser should depend on an adapter/bridge rather than direct Label Studio credentials or model-internal implementation details.

---

### R6 — DICOM integration

Deferred until R1–R5 are stable.

Preserve:
- StudyInstanceUID
- SeriesInstanceUID
- SOPInstanceUID
- laterality
- modality/device/acquisition metadata

Support DIMSE/DICOMweb only when required by the deployment target. Do not let DICOM integration mutate model semantics.

---

### R7 — Model diff and drift

Separate:
- version-to-version model diff on a frozen evaluation set;
- input drift;
- embedding/feature drift;
- prediction distribution drift;
- calibration/performance drift only where labels exist.

Never call unlabeled distribution change “accuracy drift.”

The existing GUI Model Comparison page is the UX target for changed/improved/regressed case inspection.

---

### R8 — HL7/FHIR demo

Internal result -> adapter -> HL7 v2 / FHIR resource mapping.

No HIS compatibility claim before live integration testing.

## 5. Evidence anchors

The current plan is motivated by the following evidence themes:

- Gong et al. (2026 preprint): high-resolution UWF patch representation, frozen DINO-family encoders, and Attention MIL are strong candidates; patch preservation can outperform aggressive global resizing; partial fine-tuning can improve frozen transfer. Results are external research results, not OcuForge performance.
- RETFound (Nature 2023): retinal-domain self-supervised pretraining is a strong comparator and evidence that domain-specific representation learning can benefit downstream retinal tasks.
- IDRiD: spatial lesion supervision for core DR lesions including microaneurysm, hemorrhage, hard exudate, and soft exudate.
- DDR: public DR data with a spatially annotated lesion subset useful for lesion-focused work, subject to exact source/version/license audit.
- MMRDR: useful for multimodal/global DR and image-level lesion information, but image-level lesion presence must not be reinterpreted as ROI localization supervision.

## 6. Compute strategy

Preferred research storage design:

```text
GitHub
  code / config / safe manifests

RunPod Network Volume (public research only)
  /workspace/data
  /workspace/models
  /workspace/cache
  /workspace/artifacts
```

Storage roots must remain configurable so the same code works on RunPod, Vast, local Linux, and on-prem systems.

Recommended GPU-spend strategy:

1. R0 on CPU.
2. Preload reviewed public datasets to persistent volume.
3. Cache frozen DINOv3 features once where scientifically valid.
4. Compare cheap heads/pooling from the same frozen feature source.
5. Only after a winner emerges, pay for partial fine-tuning.
6. Keep ROI and global experiments independently versioned.
7. Avoid provisioning expensive GPU merely to download/unpack data.

## 7. Change relative to the previous plan

Keep:
- DINOv3;
- patch processing;
- Attention MIL;
- CORAL support;
- Label Studio concept;
- custom GUI;
- CVAT;
- DICOM/model-diff/HL7 roadmap.

Change:
- DINOv3 + Attention MIL is a leading candidate, not a frozen champion.
- CORAL becomes an ablation for genuine ordinal labels, not an assumed final head.
- global DR and ROI lesion training become explicitly separate model tracks.
- ROI taxonomy starts from spatially supported classes, not a target count.
- MMRDR image-level lesion labels must not be used as ROI coordinates.
- R1 becomes a controlled benchmark ladder before expensive tuning.
- partial fine-tuning is postponed until frozen baselines justify it.
- external/domain-shift evaluation becomes a planned gate rather than an optional afterthought.

## 8. Immediate next action

Luna Max should first perform a **planning/reconciliation commit**:

1. inspect the current repository;
2. reconcile this V2 plan with current authoritative docs;
3. preserve working code and validated contracts;
4. update roadmap/status/config only where needed;
5. do not start large dataset download or GPU training;
6. stop after validation and push.

Only after that commit should R0 execute.
