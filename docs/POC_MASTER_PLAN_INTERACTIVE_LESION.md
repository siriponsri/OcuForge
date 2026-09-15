# OcuForge POC Master Plan V2 — Model First + Interactive Lesion GUI

**Status:** Proposed authoritative POC direction
**Project:** OcuForge / Eyes Detected
**Priority:** Train useful models first, then expose them through a clinician-facing interactive GUI.
**Primary interaction:** user clicks / draws / boxes a retinal region and receives an immediate lesion-class suggestion.
**Customer-facing POC:** global retinal inference + interactive lesion classification + GUI.
**Labeling tool:** Label Studio Community as the preferred free internal ROI labeling / QA workbench.
**CVAT:** retained as optional advanced computer-vision annotation infrastructure; not the primary POC UI.
**Audience:** Luna Max, Codex, project owner, model/research team, frontend team.

---

## 1. Requirement Reset

The current POC requirement is:

> **Train the model first, then connect it to a GUI where a user can select a retinal region and immediately receive an AI lesion suggestion.**

The POC should feel interactive:

```text
retinal image
    ↓
global model result
    ↓
user clicks / drags / draws ROI
    ↓
ROI lesion model
    ↓
instant lesion suggestion
    ↓
confirm / change / reject
```

Example user-visible suggestions:

```text
No lesion detected
Microaneurysm
Hemorrhage
Hard Exudate
Cotton Wool Spot
...
```

The final lesion taxonomy must be frozen from actual dataset support before model training.

Do not invent classes merely to reach a target class count.

---

## 2. How Much This Changes the Previous Plan

This is a **direction adjustment, not a full rewrite**.

The following prior work remains useful:

- DINOv3 / retinal model research;
- MIL/CORAL global DR work;
- shared contracts;
- model provenance/versioning;
- local data safety;
- Labeler/CVAT bridge;
- Mongo/local storage;
- model monitoring design;
- DICOM/HL7/FHIR architecture;
- Windows/bootstrap/tests;
- public-only GPU rules.

The major changes are:

1. **Interactive lesion classification becomes a core POC requirement.**
2. **Model training moves ahead of interoperability work.**
3. **Label Studio Community becomes the preferred fast ROI labeling/QA workbench.**
4. **The customer GUI remains custom OcuForge GUI; Label Studio is an internal tool.**
5. **CVAT becomes optional/advanced rather than blocking the POC.**
6. **DICOM, HL7/FHIR, monitoring remain planned, but move behind the Model + Interactive GUI milestone.**

---

## 3. POC Success Definition

The first strong customer demo should support:

```text
Open retinal image
      ↓
Show global AI result
      ↓
Select ROI by point / box / polygon / brush
      ↓
AI classifies selected region
      ↓
show top lesion probabilities
      ↓
user confirms / changes / rejects
```

### Minimum visible POC

The stakeholder should see:

- retinal image viewer;
- global image quality / gradability if supported;
- global DR/disease model result;
- model name/version;
- point or rectangular ROI selection;
- lesion suggestion returned quickly;
- lesion confidence;
- top-k alternatives;
- `No lesion detected` option;
- confirm / change / reject workflow;
- evidence that the ROI result is linked to the exact selected region;
- research/POC disclaimer.

The POC does not require a full hospital deployment before this demo.

---

## 4. Model Architecture

Use separate model capabilities.

```text
                    RETINAL IMAGE
                         │
            ┌────────────┴────────────┐
            │                         │
      MDL-A GLOBAL                MDL-B ROI
      RETINAL MODEL            LESION CLASSIFIER
            │                         │
     DR / disease / QC          selected region
            │                         │
            │                  lesion probabilities
            │                         │
            └────────────┬────────────┘
                         │
                 OcuForge Model API
                         │
               ┌─────────┴─────────┐
               │                   │
          Custom GUI         Label Studio
          customer POC       internal QA
```

### MDL-A — Global Retinal Model

Primary purposes:

- gradability / image QC where dataset supports it;
- DR disease/severity classification;
- global confidence;
- model evidence.

Recommended baseline ladder:

```text
B0 simple baseline
B1 frozen DINOv3 + global average pooling
B2 frozen DINOv3 + patch mean/max pooling
B3 DINOv3 + attention MIL
B4 DINOv3 + attention MIL + CORAL
   only for genuine ordinal DR grades
B5 partial fine-tuning only when justified
```

### MDL-B — ROI Lesion Classifier

This becomes a primary POC feature.

Input:

```text
image
+ selected ROI
+ optional surrounding context
```

Output:

```text
top lesion class
probability
top-k alternatives
model version
ROI identity
```

Example:

```text
Microaneurysm       0.87
Hemorrhage          0.08
No lesion detected  0.03
Hard Exudate        0.02
```

The ROI model may use:

- crop-only view;
- crop + contextual margin;
- multi-scale ROI features;
- DINOv3/retinal encoder features;
- a lightweight classification head.

Do not assume the same architecture that works for global DR must be optimal for ROI lesions.

---

## 5. Lesion Taxonomy — Freeze Before Training

The owner is considering **approximately seven lesion categories** for the POC.

Do not freeze seven classes only because seven sounds convenient.

The final taxonomy must be based on:

- actual annotations available;
- label definitions;
- class counts;
- inter-dataset semantic compatibility;
- clinical usefulness;
- visual separability;
- expected POC value.

### Currently supported by supplied project evidence

The supplied DR active-learning paper explicitly discusses:

- microaneurysms (`MA`);
- hemorrhages (`HE`);
- exudates (`EX`);

and its IDRiD-oriented multi-class detector additionally reports:

- soft exudates (`SE`);
- optic disc (`OD`) as a structural class, not a retinal lesion.

Therefore the POC taxonomy should **not** automatically treat optic disc as one of the lesion classes.

### Candidate POC taxonomy structure

Target:

```text
UP_TO_7_LESION_CLASSES
+
NO_SUPPORTED_LESION_IN_ROI
```

The exact 7 lesion classes are **TAXONOMY_PENDING_AUDIT**.

Initial high-priority classes to validate first:

```text
MICROANEURYSM
HEMORRHAGE
HARD_EXUDATE
SOFT_EXUDATE / COTTON_WOOL_SPOT
```

Additional classes must be admitted only after source/dataset audit confirms usable supervision.

Potential additional clinically relevant candidates may be considered later, but must not be committed to the contract until verified.

### `No lesion` semantics

Internal meaning:

```text
NO_SUPPORTED_LESION_IN_ROI
```

User-facing display:

```text
No lesion detected
```

Meaning:

> The model did not identify any **supported lesion class within the selected ROI** at the configured threshold.

It must **not** mean:

- the whole eye is normal;
- the patient has no DR;
- no retinal pathology exists anywhere else.

---

## 6. ROI Training Dataset Construction

The training program should convert lesion annotations into ROI-classification examples.

Conceptually:

```text
lesion annotation
      ↓
lesion-centered ROI
      ↓
context expansion
      ↓
class label
```

For example:

```text
MA annotation → ROI patch → MICROANEURYSM
HE annotation → ROI patch → HEMORRHAGE
EX annotation → ROI patch → HARD_EXUDATE
SE annotation → ROI patch → COTTON_WOOL_SPOT
```

Negative examples:

```text
retinal background ROI
      ↓
verify no supported lesion annotation overlaps ROI
      ↓
NO_SUPPORTED_LESION_IN_ROI
```

### Negative-class warning

Negative patches must not be generated carelessly.

A region is not a reliable negative merely because no annotation exists.

Before using public annotations for `NO_SUPPORTED_LESION_IN_ROI`, audit whether:

- lesion annotations are intended to be exhaustive;
- the annotation protocol covers the supported classes;
- small lesions may be omitted;
- masks/points/boxes represent all visible lesions or only selected ones.

If exhaustiveness cannot be established, classify negatives as weak negatives and record the limitation.

---

## 7. Split / Leakage Policy

Do not split extracted ROI patches randomly across train/validation/test.

The split unit must remain at least the original image, and preferably patient/eye where identifiers allow it.

Correct:

```text
patient/image split
      ↓
then generate ROIs inside each split
```

Incorrect:

```text
generate ROIs
      ↓
randomly split patches
```

The incorrect approach can leak nearly identical image context across train and test.

Record:

- source dataset;
- patient/eye/image identifiers if available;
- split seed/version;
- source image hash;
- ROI geometry;
- lesion annotation source;
- preprocessing version.

---

## 8. ROI Model Evaluation

The POC should not be judged by accuracy alone.

Minimum lesion-classification metrics:

- macro F1;
- per-class precision;
- per-class recall/sensitivity;
- confusion matrix;
- balanced accuracy;
- multiclass AUROC/AUPRC where statistically meaningful;
- calibration / confidence reliability;
- class support counts.

Also report:

- performance by ROI size;
- performance by source dataset;
- performance by image quality if possible;
- `No lesion` false-positive / false-negative behavior;
- inference latency.

For the interactive POC, latency matters.

Target architecture should make one ROI classification feel near-immediate on the intended demo machine.

Do not declare a hard latency SLA until measured.

---

## 9. Label Studio Community Role

Use **Label Studio Community** as the preferred free internal workbench for:

- ROI annotation;
- lesion-class assignment;
- correction;
- model suggestion review;
- model QA;
- rapid dataset curation.

It is not the final customer product UI.

Architecture:

```text
                    OcuForge Model API
                       /          \
                      /            \
          Custom Clinical GUI     Label Studio
             customer POC          internal QA
```

The same ROI classification API should eventually serve both.

### Preferred Label Studio interaction

```text
user selects ROI
      ↓
Label Studio sends image + ROI context
      ↓
OcuForge ML backend / API
      ↓
model predicts lesion class
      ↓
prediction appears as suggestion
      ↓
reviewer confirms / edits
```

Do not depend on paid Label Studio plugin features for the POC.

Keep Community/self-hosted compatibility as the default assumption until separately reviewed.

---

## 10. CVAT Role

Do not delete existing CVAT work.

Retain CVAT as an optional advanced annotation tool for:

- large-scale computer-vision labeling;
- bounding boxes;
- polygons;
- masks;
- segmentation;
- future detection/segmentation datasets;
- workflows where CVAT is operationally preferable.

For the immediate POC:

```text
Label Studio → preferred fast ROI classification workbench
CVAT         → optional advanced CV labeling infrastructure
Custom GUI   → customer-facing product
```

No migration of validated CVAT code is required solely because priority changed.

---

## 11. Custom GUI Direction

The frontend already being built by the team remains the customer-facing GUI.

Do not replace it with Label Studio.

Add an interaction mode:

```text
Pointer
Point
Rectangle
Polygon / Brush (optional for first POC)
```

When the user selects a region:

```text
ROI
 ↓
POST lesion classification
 ↓
AI LESION SUGGESTION
```

Suggested panel:

```text
AI Lesion Suggestion

Microaneurysm       87%
Hemorrhage           8%
No lesion detected   3%

[Confirm] [Change Label] [Reject]
```

The confirmed result should record:

- original image/study identity;
- ROI geometry;
- AI prediction;
- model/version;
- user decision;
- timestamp;
- optional reviewer identity hash.

---

## 12. SAM Role

SAM2/SAM3 is optional for the first lesion-classification POC.

Preferred later interaction:

```text
point / box
    ↓
ROI lesion classifier
    ↓
lesion class
    ↓
optional SAM refinement
    ↓
mask / region
```

Do not let SAM define the lesion class by itself.

Do not block the first POC on SAM integration.

---

## 13. Model API Boundary

Create one product-facing inference boundary rather than separate GUI-specific code.

Suggested conceptual endpoints:

```text
POST /v1/infer/global
POST /v1/infer/lesion-roi
GET  /v1/models
```

Illustrative ROI request:

```json
{
  "image_id": "IMG001",
  "roi": {
    "type": "rectangle",
    "x": 0.32,
    "y": 0.41,
    "width": 0.12,
    "height": 0.10
  }
}
```

Illustrative response:

```json
{
  "model": {
    "name": "ocuforge-lesion",
    "version": "0.1.0"
  },
  "roi_id": "ROI001",
  "predictions": [
    {"label": "MICROANEURYSM", "score": 0.87},
    {"label": "HEMORRHAGE", "score": 0.08},
    {"label": "NO_SUPPORTED_LESION_IN_ROI", "score": 0.03}
  ]
}
```

The exact contract belongs under `CTR`.

---

## 14. DICOM / HL7 / Monitoring Priority

These requirements remain valid, but are no longer the immediate critical path.

Priority order:

```text
1. Dataset / taxonomy freeze
2. Global model baseline
3. ROI lesion model
4. Label Studio interactive validation
5. Custom GUI integration
6. DICOM image/study ingestion
7. model version diff / drift monitoring
8. HL7/FHIR integration demo
```

Do not discard interoperability architecture.

Simply defer heavy implementation until a useful model-driven GUI POC exists.

---

## 15. Revised Parallel Workstreams

### Arm A — MODEL / RESEARCH

Primary modules:

```text
MDL + RSC
```

Immediate work:

- dataset audit;
- lesion taxonomy freeze;
- global baseline;
- ROI dataset generation;
- ROI lesion classifier;
- evaluation;
- model packaging/versioning;
- GPU experiments.

### Arm B — GUI / LABEL WORKBENCH

Primary responsibilities:

```text
GUI + LBL + RUN
```

Immediate work:

- Label Studio Community local workbench;
- ROI annotation configuration;
- ML backend/API integration;
- connect custom frontend to model API;
- confirm/change/reject UX;
- preserve annotation provenance.

### Shared boundary

```text
CTR
```

Any change to shared result/ROI/label contracts must be coordinated across both arms.

---

## 16. Immediate Roadmap

### P0 — Direction / Taxonomy Freeze

Deliver:

- this plan;
- repo docs aligned;
- dataset candidates reviewed;
- lesion taxonomy decision;
- `No lesion` semantics frozen;
- split policy;
- primary metrics.

### P1 — Global Baseline

Deliver:

- public-data global DR baseline;
- real DINOv3 runtime;
- held-out metrics;
- packaged model.

### P2 — ROI Dataset + Lesion Baseline

Deliver:

- ROI-generation pipeline;
- lesion-positive examples;
- audited negative strategy;
- first lesion classifier;
- class-by-class metrics;
- confusion matrix.

### P3 — Label Studio Interactive POC

Deliver:

```text
select ROI
→ model inference
→ lesion suggestion
→ confirm / change / reject
```

Use Label Studio Community.

### P4 — Custom GUI Integration

Deliver the same interaction in the team frontend.

Do not fork the model implementation.

Both Label Studio and the custom GUI consume the same model/API contract.

### P5 — DICOM / Model Monitoring

Add:

- DICOM study identity;
- model version diff;
- drift summary.

### P6 — HL7/FHIR Demonstration

Add synthetic integration mappings.

No live-HIS compatibility claim without actual acceptance testing.

---

## 17. Public Data / GPU Policy

Before GPU training:

- verify dataset source;
- verify access/license;
- record file hashes;
- freeze split;
- freeze label mapping;
- record preprocessing.

Vast/RunPod may receive only:

- reviewed public data;
- synthetic data;
- public model weights with reviewed access terms;
- public/synthetic derived artifacts.

Never upload:

- hospital images;
- clinical/private labels;
- private embeddings;
- hospital-derived predictions;
- hospital-trained checkpoints;
- PHI;
- credentials.

---

## 18. Research Guardrails

Global DR:

- use ordinal CORAL only with genuine ordinal labels;
- binary `DR / no-DR` must remain binary semantics;
- `no-DR` is not automatically grade 0.

Lesions:

- ROI classification is not whole-image disease diagnosis;
- `NO_SUPPORTED_LESION_IN_ROI` is ROI-local;
- MIL attention is not lesion localization;
- lesion classifier confidence is not clinical certainty;
- annotation incompleteness must be reflected in negative-sample claims;
- do not claim clinical performance from public benchmark POC alone.

---

## 19. Evidence From Supplied Project Sources

The supplied active-learning DR paper demonstrates a relevant HITL pattern where clinicians refine AI pre-labels rather than always drawing from scratch. It reports an NMC dataset with three lesion classes—microaneurysms, hemorrhages, and exudates—and a separate multi-class evaluation involving MA, HE, EX, soft exudates, and optic disc.

This supports the feasibility of:

```text
AI suggestion
    ↓
human review / correction
```

but does not prove that the exact OcuForge lesion taxonomy or performance is already validated.

The final OcuForge taxonomy therefore remains an explicit audit/freeze gate.

---

## 20. Documentation Alignment

After accepting this plan, audit/update:

```text
README.md
AGENTS.md
docs/CTR_MODULE_CONTRACT.md
docs/PROJECT_MAP.md
docs/RUN_PARALLEL_WORKFLOW.md
docs/IMPLEMENTATION_STATUS.md
docs/NEXT_STEPS.md
docs/DUAL_TRACK_ARCHITECTURE.md
docs/SOURCE_REVIEW.md
docs/GPU_EXECUTION_TH.md
```

Add this document as:

```text
docs/POC_MASTER_PLAN_INTERACTIVE_LESION.md
```

Do not mass-delete old plans.

Mark superseded priorities clearly.

Retain prior validated infrastructure.

---

## 21. Acceptance State for the Planning Pivot

The planning pivot is complete when repository documentation consistently states:

```text
POC_PRIMARY=MODEL_INTERACTIVE_GUI
MODEL_TRAINING_PRIORITY=HIGH
GLOBAL_MODEL=PRIMARY
ROI_LESION_CLASSIFIER=PRIMARY_POC_FEATURE
LESION_TAXONOMY=FREEZE_BEFORE_TRAINING
TARGET_LESION_COUNT=APPROXIMATELY_7_PENDING_AUDIT
NO_LESION=NO_SUPPORTED_LESION_IN_ROI
LABEL_STUDIO_COMMUNITY=INTERNAL_ROI_QA_WORKBENCH
CUSTOM_GUI=CUSTOMER_FACING
CVAT=OPTIONAL_ADVANCED_LABELING
SAM=OPTIONAL_REFINEMENT
DICOM=PLANNED_AFTER_MODEL_GUI
MODEL_MONITORING=PLANNED_AFTER_MODEL_GUI
HL7_FHIR=PLANNED_AFTER_MODEL_GUI
PUBLIC_GPU_PRIVATE_DATA=FORBIDDEN
```

No large GPU run should be launched in the same planning commit.

---

## 22. First Implementation Objective After This Pivot

The next technical objective should be:

> **R0 / MDL — Dataset + Lesion Taxonomy Freeze**

Required outputs:

1. selected public datasets;
2. exact lesion annotations available from each source;
3. verified class counts;
4. class-name mapping;
5. proposed final lesion taxonomy;
6. definition of `NO_SUPPORTED_LESION_IN_ROI`;
7. negative-sampling validity assessment;
8. patient/image split policy;
9. baseline model ladder;
10. metrics;
11. compute estimate;
12. exact first training experiment.

Only after R0 passes should the first real lesion-model training run begin.
