# TRACK A — MODEL RESEARCH & TRAINING SPECIFICATION

## 0. Mission

Track A exists so the AI program can move immediately **without waiting for ophthalmologist annotation**.

The first local clinician labels should arrive only after the project already has:

- a public-data source model;
- a local unlabeled feature bank;
- domain-shift/OOD diagnostics;
- preliminary lesion pre-label generators;
- an active-learning candidate selector;
- a stable prediction contract.

Track A must therefore maximize what can be learned from:
1. public labeled retinal datasets; and
2. local **unlabeled** retinal images.

---

# 1. Track A success definition

Track A is considered ready to request the first clinician batch when all of the following exist:

```text
Public source model
        +
Local unlabeled feature bank
        +
QC / OOD diagnostics
        +
Candidate lesion pre-labels where scientifically supported
        +
Active-learning batch selector
        +
Stable prediction schema
        +
Locked first-label evaluation protocol
```

This is a **readiness condition**, not clinical validation.

---

# 2. Data sources

## 2.1 Primary public UWF source — MMRDR-UWF

Role:
- primary public UWF source;
- 5-grade DR supervision;
- image-level lesion-presence auxiliary supervision;
- UWF-domain feature learning;
- source-model benchmarking.

Known facts to preserve:
- 10,404 UWF images;
- DR grades 0–4;
- 7 lesion-presence categories;
- UWF split at patient level in the released dataset;
- lesion field is image-level multi-label, not pixel mask.

Seven lesion categories reported by MMRDR:
- MA;
- HE;
- IH;
- VB/IRMA;
- NV;
- VH;
- RD.

Use cases:
- CORAL DR grade;
- lesion-aware multi-label auxiliary head;
- source-domain representation learning;
- weak lesion-aware MIL.

Not allowed:
- deriving pixel MA coordinates as ground truth;
- deriving NV polygons as ground truth.

## 2.2 IDRiD

Role:
- high-resolution conventional CFP lesion segmentation/bootstrap;
- test lesion geometry pipelines;
- train/evaluate early lesion pre-label models.

Known properties:
- 516 fundus images;
- 81 images with pixel-level lesion masks;
- masks for MA, hard exudate, hemorrhage, soft exudate;
- optic disc mask; fovea information;
- 50° conventional fundus, not UWF.

Use cases:
- MA candidate detector;
- hard-exudate segmenter;
- hemorrhage segmenter;
- cotton-wool/soft-exudate segmenter;
- annotation import/export test.

Generalization warning:
An IDRiD lesion model is not automatically validated on local UWF.

## 2.3 OIA-DDR / DDR

Role:
- DR classification;
- lesion segmentation/detection;
- additional conventional CFP lesion localization source;
- robustness benchmark.

Must verify the exact subtask files and license/access before use.

## 2.4 DeepDRiD

Role:
- DR grading;
- image-quality estimation;
- external benchmark;
- robustness/QC research.

Do not assume the same lesion geometry labels as IDRiD.

## 2.5 EyePACS / Messidor-2

Role:
- conventional fundus DR grading;
- external classification validation;
- domain diversity.

Access/licensing must be checked before automated download.

## 2.6 Local hospital data

Initial state:
```text
labels = 0
```

Required metadata where legally/operationally available:
- stable de-identified image ID;
- de-identified patient/case ID;
- eye/laterality;
- visit ID/date bucket if allowed;
- modality;
- camera manufacturer/model;
- acquisition resolution;
- source site;
- gradability unknown/known;
- file hash;
- ingestion timestamp.

Raw PHI is outside the cloud-GPU workflow by default.

---

# 3. Data registry

Implement a registry that treats datasets as **declared resources**, not hard-coded folders.

Example:

```yaml
dataset_id: mmrdr_uwf_v1
modality: UWF
source_type: public
root_uri: /data/mmrdr/UWF
label_scope:
  dr_grade: image_level
  lesions: image_level_multilabel
  pixel_masks: false
split_policy: released_patient_level
license_status: REVIEWED
```

Local example:

```yaml
dataset_id: local_hospital_uwf_2026q3
modality: UWF
source_type: local_private
root_uri: /secure/local_uwf
label_scope:
  dr_grade: none
  lesions: none
split_policy: patient_grouped
cloud_eligible: false
```

Validation must reject unknown or contradictory label scope.

---

# 4. Leakage controls

Default split unit:
```text
patient > eye > visit > image
```

If patient IDs exist, no patient may cross train/validation/sentinel.

If only eye-level IDs exist, split by eye and record weaker provenance.

If no grouping ID exists:
- mark leakage risk;
- do not call the split patient-level;
- do not use it for strong clinical claims.

A future local sentinel set must be **locked before active-learning training uses the remaining clinician labels**.

---

# 5. Stage A0 — Data audit

Deliverables:

- file inventory;
- extension counts;
- corrupted-image detection;
- image dimensions;
- aspect ratio;
- color channel status;
- duplicate/exact-hash report;
- optional perceptual duplicate report;
- camera/site distribution;
- label availability matrix;
- data license/access status.

Do not use OCR or metadata scraping that may leak PHI.

---

# 6. Stage A1 — Preprocessing and patching

Primary UWF reproduction target based on the 2026 UWF representation-transfer study:

```text
UWF
→ normalized/resized working canvas around 1024×1024
→ 5×5 patch grid
→ 25 patches
→ approximately 224×224 input patches
→ overlapping layout
```

Important:
- patch extraction must be deterministic;
- exact overlap/padding must be configuration;
- preserve a mapping from patch index back to source-image coordinates;
- store patch coordinate metadata;
- do not crop peripheral retina silently.

Required tests:
- same image + same config → identical patches;
- coordinate roundtrip;
- no patch outside canvas;
- patch count exactly expected;
- non-square source handling explicit.

---

# 7. Stage A2 — Encoder bake-off

## Primary encoder

**DINOv3 ViT-B/16**

Role:
- frozen feature extractor first;
- patch embedding bank;
- primary MIL representation.

Why:
- 2026 UWF representation-transfer work reported strong frozen-transfer performance for DINOv3 in patch-attention MIL.

Integration requirements:
- explicit adapter;
- explicit model name/version;
- weight hash if locally downloaded;
- DINOv3 license recorded;
- fail closed if weights unavailable.

## Challenger 1 — RETFound ViT-L

Role:
- retinal foundation model comparator;
- label-efficiency benchmark.

Caveat:
RETFound was pretrained on retinal images but is not specifically UWF-native.

## Challenger 2 — EyeCLIP / RetiZero

Role:
- semantic/vision-language challenger;
- possible teacher or agreement signal;
- zero/few-shot semantic reference where licensing permits.

Do not make either mandatory for v0.1.

## Baseline

At least one conventional supervised image classifier baseline must exist in the research plan, e.g. ResNet/ViT family. Exact implementation can be deferred in starter.

---

# 8. Feature extraction strategy

When the encoder is frozen:

```text
images
→ patch extraction
→ encoder once
→ feature store
→ many cheap MIL experiments
```

Feature store requirements:
- dataset_id;
- image_id;
- encoder_id;
- encoder weight hash/version;
- preprocessing config hash;
- patch geometry;
- tensor shape;
- feature dtype;
- extraction time;
- git SHA;
- Docker image identifier.

Never reuse features when preprocessing or encoder hash mismatches.

Recommended storage format candidates:
- Zarr;
- HDF5;
- `.pt` shards;
- Parquet only for metadata, not arbitrary high-dimensional tensors unless designed carefully.

Starter may implement `.npz`/`.pt` small fixtures, with pluggable store interface.

---

# 9. Stage A3 — Core source model

Architecture:

```text
Patch embeddings
      ↓
Attention MIL pooling
      ↓
Bag embedding
      ├──────────────────────────────┐
      ↓                              ↓
CORAL ordinal DR head      lesion-presence auxiliary head
      │                              │
grade 0..4                multi-label lesion probabilities
      │                              │
      └──────────┬───────────────────┘
                 ↓
           verification record
```

Optional:
- gradability/QC auxiliary head;
- uncertainty estimators.

## 9.1 Attention MIL

Requirements:
- attention weights sum to 1 over valid patches;
- padding mask support;
- export patch attention;
- attention described as evidence weighting, not lesion GT.

## 9.2 CORAL

DR grade order:
```text
0 No DR
1 Mild NPDR
2 Moderate NPDR
3 Severe NPDR
4 PDR
```

Implement cumulative ordinal targets for four thresholds.

Required test:
- grade 0 → [0,0,0,0]
- grade 1 → [1,0,0,0]
- grade 2 → [1,1,0,0]
- grade 3 → [1,1,1,0]
- grade 4 → [1,1,1,1]

Prediction must enforce monotonic threshold interpretation according to the chosen CORAL implementation.

## 9.3 Lesion auxiliary head

For MMRDR-UWF:
- predicts image-level presence of seven lesion groups.
- do not localize directly from these labels.

Potential task weighting must be configurable.

---

# 10. Stage A4 — Lesion pre-label subsystem

This subsystem serves Track B.

It is separate from the UWF MIL classifier because annotation geometries require localization supervision.

## 10.1 Microaneurysm

Desired output:
```text
candidate points
```

Potential bootstrapping:
- IDRiD MA masks → connected components → centroid points;
- DDR detection/segmentation data where verified.

Evaluation:
- point matching within configurable tolerance;
- lesion-level precision/recall;
- sensitivity per image;
- false candidates per image.

Do not call candidate points ground truth.

## 10.2 Hard exudate / cotton-wool / hemorrhage

Desired output:
- masks/polygons;
- confidence;
- source model version.

Initial supervision:
- IDRiD masks;
- DDR localization if available/verified.

Segmentation options in research matrix:
- U-Net family;
- DeepLab family;
- SegFormer;
- SAM-assisted prompt refinement after a detector proposes ROI.

SAM is an annotation accelerator, not necessarily the lesion detector.

## 10.3 Neovascularization

Public source limitation is important:
- MMRDR provides NV presence at image level for UWF;
- that does not provide NVD/NVE regions.

Starter policy:
- allow image-level `nv_present_candidate`;
- allow MIL evidence/weak region for **review prioritization only**;
- manual region annotation in Track B;
- specialized NV localization model is a later milestone after suitable localized labels exist.

Do not fake NVD/NVE segmenter availability.

## 10.4 DME / edema

Track A must represent modality correctly:

Fundus/UWF candidate outputs:
- macular hard-exudate evidence;
- maculopathy suspected;
- foveal involvement suspected if a validated landmark/lesion method exists.

OCT outputs:
- no DME / NCI-DME / CI-DME if using appropriate labels;
- fluid segmentation only when a specific segmentation source exists.

---

# 11. Stage A5 — Local zero-label analysis

Before adaptation:
- compare source vs local embedding distributions;
- visualize clusters for exploratory use;
- detect gross camera/site domains;
- quantify nearest-prototype agreement;
- estimate source classifier confidence;
- estimate OOD.

Allowed techniques:
- prototype matching;
- nearest-centroid or kNN reference;
- teacher/student consistency;
- augmentation consistency;
- source-free adaptation baselines;
- entropy/confidence filtering;
- VLM agreement where available.

Important:
prototype/cosine matching is a baseline/auxiliary signal, not the novelty claim.

---

# 12. Multi-signal adaptation gate

For each local unlabeled case, compute signals such as:

```text
classifier grade
classifier confidence
prototype grade
prototype similarity
augmentation consistency
VLM semantic agreement
QC status
OOD score
```

Policy classes:

### HIGH-AGREEMENT
Eligible for cautious pseudo-supervision under experiment config.

### MEDIUM / UNCERTAIN
Use consistency objectives only; no hard pseudo-label by default.

### DISAGREEMENT / OOD
Do not pseudo-label. Send to quarantine or future expert batch.

All thresholds must be config-driven and logged.

---

# 13. OOD / abstention

Starter must define interface, even if algorithms remain research-stage.

Potential research methods:
- distance-to-prototype;
- Mahalanobis in feature space;
- energy score;
- deep ensembles;
- MC Dropout;
- conformal/selective prediction later.

Core output:

```json
{
  "ood_score": 0.0,
  "abstain_recommended": false,
  "ood_method": "..."
}
```

No production threshold is frozen in starter.

---

# 14. Stage A6 — Active-learning selection

First local label budget must not simply be “highest uncertainty”.

Cold start priority:
1. diversity;
2. representativeness;
3. device/site coverage;
4. disagreement/OOD inclusion;
5. borderline DR grades.

Later rounds may use:
- Hybrid-Diversity;
- entropy/margin;
- MC Dropout;
- ensemble disagreement;
- lesion rarity;
- expected correction yield.

Selection output must be a versioned `annotation_batch_manifest`.

Example:

```json
{
  "batch_id": "LOCAL_R0_001",
  "strategy": "diversity_plus_disagreement_v1",
  "requested_n": 100,
  "model_version": "source_model_0.3.0",
  "items": [
    {
      "image_id": "IMG_001",
      "selection_reasons": ["cluster_representative", "model_disagreement"],
      "priority": 0.91
    }
  ]
}
```

---

# 15. First expert budget protocol

Recommended planning range:
```text
50–300 cases
```

This is a planning range, not a universal statistical requirement.

Split the first clinician effort into:
- **locked sentinel/validation subset**;
- **trainable cold-start subset**.

The same label must not be both sentinel and training.

Record:
- annotation time;
- corrections per case;
- pre-label acceptance rate;
- lesion additions;
- clinician certainty;
- adjudication need.

---

# 16. Evaluation

## DR ordinal
Primary:
- QWK.

Companions:
- macro AUROC;
- macro AUPRC;
- macro-F1;
- confusion matrix;
- per-grade sensitivity/specificity.

## Referable DR
- sensitivity at fixed/selected specificity;
- specificity at fixed/selected sensitivity;
- PPV/NPV;
- referral rate.

## Calibration
- ECE;
- Brier score;
- reliability curve.

## OOD/selective prediction
- AUROC/FPR95 where meaningful;
- risk-coverage;
- selective accuracy;
- abstention rate.

## Active learning
- learning curve area;
- delta QWK per 100 labels;
- delta sensitivity per 100 labels;
- delta metric per clinician-hour;
- correction yield per clinician-hour.

---

# 17. Research baselines

Must include:

B0. conventional supervised baseline  
B1. frozen DINOv3 global/image representation  
B2. DINOv3 patch mean pooling  
B3. DINOv3 patch max pooling  
B4. DINOv3 patch attention MIL  
B5. Attention MIL + CORAL  
B6. Attention MIL + CORAL + lesion auxiliary  
B7. no local adaptation  
B8. prototype-only local baseline  
B9. source-free adaptation baseline  
B10. proposed multi-signal gated adaptation  
B11. random annotation selection  
B12. diversity-first selection  
B13. uncertainty-only selection  
B14. hybrid-diversity / disagreement selection.

Not all baselines need to run in starter.

---

# 18. Track A starter repository expectations

Suggested modules:

```text
src/eyes_detected/
├── contracts/
├── data/
├── tiling/
├── encoders/
├── features/
├── mil/
├── ordinal/
├── lesions/
├── qc/
├── ood/
├── adaptation/
├── active_learning/
├── evaluation/
└── provenance/
```

CLIs:

```text
eyes-data-validate
eyes-patch-preview
eyes-extract-features
eyes-train-source
eyes-evaluate
eyes-score-local
eyes-select-annotation-batch
eyes-export-predictions
```

Starter must include synthetic commands that work CPU-only.

---

# 19. Track A completion gate before doctor dependency

**DO NOT WAIT FOR DOCTOR** until:

- [ ] public dataset registry ready;
- [ ] patch pipeline deterministic;
- [ ] DINOv3 adapter documented;
- [ ] feature store ready;
- [ ] Attention MIL + CORAL smoke-train passes;
- [ ] lesion pre-label contract works on synthetic/public fixture;
- [ ] local unlabeled ingest contract ready;
- [ ] OOD interface ready;
- [ ] AL selector can produce a batch manifest;
- [ ] prediction schema frozen v0.1;
- [ ] Track B can ingest predictions.

Then clinician annotation becomes the deliberate next bottleneck.
