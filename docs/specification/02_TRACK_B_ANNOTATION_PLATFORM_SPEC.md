# TRACK B — ANNOTATION & CLINICIAN LABELING PLATFORM SPECIFICATION

## 0. Mission

Track B builds the ophthalmologist-facing labeling workflow **in parallel** with model research.

The goal is not to ask clinicians to create a dataset from scratch. The goal is:

> **AI proposes; clinician confirms/corrects; the system preserves provenance and sends high-value corrected labels back to Track A.**

Initial backend: **CVAT self-hosted/local**.

Dataset curation/selection integration: **FiftyOne optional but recommended**.

SAM2/SAM3 may assist interactive segmentation when technically appropriate, but must not be treated as lesion ground truth.

---

# 1. Why separate Track B

Track B must not block Track A because:

- the doctor is the scarce resource;
- software UX can be tested using public/synthetic images first;
- annotation schema can be frozen before local annotation;
- pre-label import can be built before pre-label models are good;
- model outputs may change while the clinician UI contract remains stable.

Therefore:

```text
Track A produces prediction contract
            ↓
Track B displays it
            ↓
clinician corrects
            ↓
Track B exports annotation contract
            ↓
Track A consumes it
```

---

# 2. Initial product choice

## CVAT as backend

Reasons:
- mature image annotation editor;
- supports shapes such as point, box, polygon, mask and other geometry;
- supports manual and automated annotation workflows;
- provides AI tool/auto-annotation mechanisms;
- can be self-hosted;
- provides SDK/API pathways;
- has built-in annotator specification/guide capability.

Track B starter should **integrate with CVAT**, not fork its entire UI.

## FiftyOne

Use cases:
- dataset exploration;
- sample curation;
- active-learning subset inspection;
- send selected samples to CVAT;
- import corrected labels back.

FiftyOne is optional in the minimal startup path so labeler remains usable without it.

---

# 3. Clinician personas

### P1 — Ophthalmologist annotator
Needs:
- fast image navigation;
- zoom;
- clear lesion hotkeys;
- confirm/reject AI candidates;
- add missed lesion;
- image-level grade;
- uncertainty;
- minimal clicks.

### P2 — Retinal specialist reviewer/adjudicator
Needs:
- compare original annotation vs revision;
- see disputed lesions;
- see annotator certainty;
- finalize adjudicated label;
- audit history.

### P3 — Research data manager
Needs:
- create project/task;
- import batch;
- export labels;
- track status;
- detect incomplete cases;
- keep identifiers/provenance intact.

### P4 — ML researcher
Should not require CVAT access to train.
Consumes only exported, versioned contracts.

---

# 4. Annotation modes

Track B must support separate tasks, not one overloaded screen.

## Mode A — Image-level DR grading

Fields:
- DR grade 0–4;
- referable status if protocol defines;
- gradability;
- laterality validation;
- uncertain flag;
- free-text comment optional, not required.

## Mode B — Lesion localization

Geometry constrained by lesion class.

## Mode C — AI pre-label review

Clinician actions:
- confirm;
- reject;
- correct geometry;
- relabel;
- add missing;
- mark uncertain;
- escalate to adjudication.

## Mode D — Adjudication

Specialist resolves:
- grade disagreement;
- lesion disagreement;
- uncertain cases;
- NV subtype;
- edge cases.

---

# 5. Lesion vocabulary

Core v0.1:

```text
microaneurysm
intraretinal_hemorrhage
hard_exudate
cotton_wool_spot
nvd
nve
irma
venous_beading
vitreous_hemorrhage
retinal_detachment
laser_scar
optic_disc
fovea
```

Optional but not active by default:
- drusen;
- epiretinal membrane;
- myopic degeneration;
- other retinal findings.

Do not expand multi-disease scope before DR annotation workflow is stable.

---

# 6. Geometry design

## Microaneurysm
Primary:
```text
POINT
```

Rationale:
- tiny lesion;
- precise pixel boundary is expensive and often unnecessary for early detector training;
- AI can suggest candidate points.

Optional research export may convert public segmentation masks to centroids, but public GT provenance must be retained.

## Intraretinal hemorrhage
Primary:
```text
POLYGON
```
Alternative:
```text
BOX
```
Project protocol must choose one default per task.

## Hard exudate
```text
POLYGON or MASK
```

## Cotton-wool spot
```text
POLYGON or MASK
```

## NVD/NVE
```text
POLYGON / REGION
```

Starter must distinguish:
- NVD;
- NVE;
- `NV_UNCERTAIN` only if protocol approves.

Do not request individual vessel tracing in v0.1.

## IRMA
```text
POLYLINE or REGION
```

## Venous beading
```text
POLYLINE or REGION
```

## Vitreous hemorrhage / retinal detachment
Region where feasible; image-level presence may be used by a separate weak-label task.

## Optic disc
```text
ELLIPSE or MASK
```

## Fovea
```text
POINT
```

---

# 7. Edema / DME policy

This is a mandatory scientific guardrail.

For UWF/fundus annotation, use findings such as:
- `macular_hard_exudate`;
- `maculopathy_suspected`;
- `foveal_involvement_suspected`.

Do not call a fundus-only label `OCT_CONFIRMED_DME`.

If OCT is added later:
- no DME;
- NCI-DME;
- CI-DME.

Fluid segmentation requires a dedicated OCT segmentation protocol and is not v0.1 scope.

---

# 8. Annotation provenance model

Every object/label must preserve:

```text
annotation_id
image_id
label_name
geometry
source
source_model_version
created_by
created_at
updated_by
updated_at
review_status
confidence_if_ai
clinician_certainty_if_recorded
adjudicator
adjudication_timestamp
```

`source` enum:

```text
AI_SUGGESTED
CLINICIAN_CONFIRMED
CLINICIAN_CORRECTED
CLINICIAN_ADDED
EXPERT_ADJUDICATED
IMPORTED_PUBLIC_GT
```

Example lifecycle:

```text
AI_SUGGESTED
    ↓ doctor accepts
CLINICIAN_CONFIRMED
```

or:

```text
AI_SUGGESTED
    ↓ doctor moves point
CLINICIAN_CORRECTED
```

or:

```text
no AI object
    ↓ doctor adds
CLINICIAN_ADDED
```

Adjudication must create a new provenance event, not overwrite history silently.

---

# 9. Suggested clinician workflow

```text
Open case
   ↓
Verify laterality / image quality
   ↓
Set DR grade
   ↓
Review AI candidates
   ├─ confirm
   ├─ reject
   ├─ edit
   └─ add missing
   ↓
Mark uncertain if needed
   ↓
Submit
   ↓
If disagreement/uncertain → specialist queue
   ↓
Finalize/adjudicate
```

The UI should never require clinicians to review model internals.

---

# 10. Microaneurysm interaction design

Desired behavior:

- AI candidate point visible;
- click/toggle = confirm;
- delete/reject = false candidate;
- click on image = add missed MA;
- candidate confidence visible optionally but should not dominate clinician judgment;
- bulk-confirm only if the clinician explicitly chooses it;
- zoom retention between nearby lesions desirable.

Record:
- candidates offered;
- candidates confirmed;
- candidates rejected;
- manual additions;
- time spent.

These become annotation-efficiency metrics.

---

# 11. Larger lesion interaction design

For hard exudates / CWS / hemorrhage:

Preferred:
```text
AI region proposal
→ clinician adjusts polygon/mask
→ submit
```

SAM-assisted workflow:
```text
detector/ROI
→ SAM interactive mask
→ clinician corrects
→ save as clinician-corrected annotation
```

SAM output remains `AI_SUGGESTED` until clinician action.

---

# 12. NV interaction design

Because public UWF image-level NV labels are not localized:

Starter behavior:
- show image-level NV candidate only if Track A emits it;
- optionally show weak evidence map with explicit label `MODEL_EVIDENCE_NOT_GT`;
- clinician draws NVD/NVE region manually;
- expert adjudication recommended for uncertain NV.

Do not auto-create NVD/NVE polygons from MIL attention.

---

# 13. Active-learning batch intake

Track B accepts:

`annotation_batch_manifest.json`

Required:
- batch ID;
- selection strategy;
- model version;
- requested sample count;
- image IDs;
- selection reasons;
- priority;
- dataset split status.

The labeler must refuse samples marked `locked_sentinel=true` for trainable annotation queues unless the task is explicitly a sentinel evaluation task.

---

# 14. CVAT project structure

Suggested projects:

```text
ED_DR_GRADE_V1
ED_LESION_POINT_MA_V1
ED_LESION_REGION_V1
ED_ADJUDICATION_V1
```

Do not put every geometry/class into one giant task initially.

Each project should have an embedded annotation guide.

---

# 15. CVAT bootstrap requirements

Starter should provide scripts/config that help:

- create projects;
- create labels;
- load task images by declared paths/URLs allowed by deployment;
- import synthetic predictions;
- export annotations;
- normalize CVAT geometry to Eye Detected contracts.

Credentials must be environment variables, never committed.

---

# 16. Prediction import

Track A prediction example:

```json
{
  "schema_version": "prediction.v0.1",
  "image_id": "IMG_001",
  "model_version": "lesion-prelabel-0.1",
  "objects": [
    {
      "label": "microaneurysm",
      "geometry_type": "point",
      "coordinates_norm": [0.431, 0.617],
      "confidence": 0.72,
      "provenance": "AI_SUGGESTED"
    }
  ]
}
```

Track B bridge converts normalized geometry to CVAT pixel coordinates based on manifest width/height.

Must test roundtrip tolerance.

---

# 17. Annotation export

Export to Eye Detected native JSONL in addition to any CVAT-native export.

Native export is the stable interface. CVAT format is implementation-specific.

Example:

```json
{
  "schema_version": "annotation.v0.1",
  "annotation_id": "ANN_...",
  "image_id": "IMG_001",
  "label": "microaneurysm",
  "geometry": {
    "type": "point",
    "coordinates_norm": [0.429, 0.620]
  },
  "source": "CLINICIAN_CORRECTED",
  "parent_prediction_id": "PRED_...",
  "annotator_id_hash": "ANON_...",
  "review_status": "SUBMITTED"
}
```

---

# 18. Review states

Enum:

```text
DRAFT
SUBMITTED
NEEDS_REVIEW
ADJUDICATED
LOCKED
REJECTED
```

Track A training ingest by default accepts:
```text
ADJUDICATED
LOCKED
```
and optionally:
```text
SUBMITTED
```
only under explicit experiment config.

---

# 19. Annotation QA

Automated checks:
- geometry inside bounds;
- allowed geometry for label;
- no NaN;
- normalized coords [0,1];
- grade in 0..4;
- laterality valid;
- source provenance present;
- reviewer state valid;
- no sentinel/train overlap;
- no duplicate annotation ID.

Human QA:
- random re-review subset;
- disagreement log;
- adjudication rate;
- inter-rater agreement where dual review exists.

---

# 20. Clinician efficiency metrics

Track B must make it possible to record:

- time/case;
- objects offered;
- AI acceptance rate;
- AI rejection rate;
- manual-add rate;
- geometry correction rate;
- grade correction rate;
- adjudication rate;
- number of confirmed lesions;
- annotation yield per hour.

Do not interpret shorter time as better if lesion recall drops.

---

# 21. Public-data dry run before doctor

Before exposing local data:

1. create synthetic cases;
2. import public examples where license permits;
3. load public GT as `IMPORTED_PUBLIC_GT`;
4. generate fake/real pre-labels;
5. test confirm/correct workflow;
6. test export;
7. compare export to known GT when appropriate;
8. collect UX feedback from non-clinical team first.

The doctor should not be the first software tester.

---

# 22. Security / local deployment

Default:
```text
hospital/local network
```

Requirements:
- HTTPS when networked;
- secrets in environment/secret store;
- least-privilege users;
- raw image path not exposed publicly;
- audit log;
- backups;
- no telemetry containing PHI unless approved;
- no auto-upload to external AI services.

Starter can document but need not implement enterprise IAM.

---

# 23. Track B repository structure

Suggested:

```text
eyes-detected-labeler/
├── compose/
├── bridge/
│   ├── cvat_client/
│   ├── import_predictions/
│   ├── export_annotations/
│   └── provenance/
├── schemas/
├── annotation_guides/
├── fiftyone_adapter/
├── examples/
├── tests/
└── docs/
```

No custom full frontend required in v0.1.

---

# 24. Track B completion gate before doctor session

- [ ] CVAT local start documented;
- [ ] label projects/schema defined;
- [ ] synthetic prediction import works;
- [ ] point/polygon/mask roundtrip works;
- [ ] provenance preserved;
- [ ] reviewer states preserved;
- [ ] annotation batch manifest accepted;
- [ ] exports consumable by Track A validator;
- [ ] annotation guide available in Thai;
- [ ] doctor never sees raw IDs that are not required;
- [ ] MA workflow is fast enough for pilot;
- [ ] NV limitation prominently documented;
- [ ] DME modality rule documented;
- [ ] backup/export procedure documented.

Only then schedule first expert labeling batch.
