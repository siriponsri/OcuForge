# EYE DETECTED — LABEL SCHEMA & CLINICAL ANNOTATION PROTOCOL v0.1

> Draft protocol for engineering alignment. Final clinical definitions must be reviewed and approved by the ophthalmology team before local annotation begins.

---

# 1. Objectives

The schema must simultaneously support:

- DR grading;
- lesion localization;
- AI pre-label review;
- human correction;
- expert adjudication;
- model training;
- audit;
- active learning;
- future product analytics.

It must **not** merge AI suggestion and clinician truth into one untraceable label.

---

# 2. Case hierarchy

```text
patient_pseudo_id
  └── eye_id
       └── visit_id
            └── image_id
```

Required image fields:

```text
image_id
file_hash_sha256
patient_pseudo_id (if available)
eye_id (if available)
visit_id (if available)
laterality: OD | OS | UNKNOWN
modality: UWF | CFP | OCT | OTHER
camera_make
camera_model
width_px
height_px
source_site
acquisition_time_bucket (optional)
data_split
```

`data_split`:
```text
TRAIN
VAL
TEST
SENTINEL
UNASSIGNED
```

---

# 3. Image-level labels

## DR grade

```text
0 = No DR
1 = Mild NPDR
2 = Moderate NPDR
3 = Severe NPDR
4 = PDR
U = Ungradable
X = Uncertain / needs adjudication
```

Storage should separate:
- `dr_grade` integer nullable;
- `gradable` boolean/enum;
- `needs_adjudication`.

Do not encode ungradable as grade 5.

## Gradability

```text
GRADABLE
PARTIALLY_GRADABLE
UNGRADABLE
UNKNOWN
```

Optional reason:
- blur;
- underexposure;
- overexposure;
- media opacity;
- eyelid/eyelash;
- field-of-view issue;
- artifact;
- other.

## Referability

Do not hard-code a universal referable rule in schema.

Store:
```text
referable_by_protocol: boolean|null
referable_protocol_id: string|null
```

So rule changes do not rewrite raw grade labels.

---

# 4. Lesion taxonomy

Canonical names:

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

Synonyms must be normalized:
- MA → microaneurysm
- HE in MMRDR terminology may refer to hard exudate; do not confuse with hemorrhage abbreviation in other sources.
- IH → intraretinal_hemorrhage
- NV → neovascularization, but local annotation should prefer nvd/nve where determinable.
- SE → soft exudate → cotton_wool_spot in local canonical vocabulary.

A dataset-specific mapping file is mandatory.

---

# 5. Geometry mapping

| Canonical label | Allowed geometry v0.1 | Primary |
|---|---|---|
| microaneurysm | point | point |
| intraretinal_hemorrhage | polygon, box | polygon |
| hard_exudate | polygon, mask | mask/polygon |
| cotton_wool_spot | polygon, mask | mask/polygon |
| nvd | polygon | polygon |
| nve | polygon | polygon |
| irma | polyline, polygon | polygon |
| venous_beading | polyline, polygon | polyline |
| vitreous_hemorrhage | polygon, image_presence | polygon |
| retinal_detachment | polygon, image_presence | polygon |
| laser_scar | polygon | polygon |
| optic_disc | ellipse, mask | mask/ellipse |
| fovea | point | point |

The annotation project may restrict to one geometry per lesion for consistency.

---

# 6. Provenance

Every annotation has:

```text
origin:
  IMPORTED_PUBLIC_GT
  AI_SUGGESTED
  CLINICIAN_CONFIRMED
  CLINICIAN_CORRECTED
  CLINICIAN_ADDED
  EXPERT_ADJUDICATED
```

Separate:
```text
origin
review_status
```

because a clinician-added object may still require adjudication.

---

# 7. Confidence / certainty

AI:
```text
model_confidence: 0..1
```

Human:
```text
clinician_certainty:
  HIGH
  MEDIUM
  LOW
  NOT_RECORDED
```

Do not numerically equate AI confidence with human certainty.

---

# 8. Parent-child provenance

If clinician edits an AI proposal:

```text
prediction_id
    ↓
annotation_id
```

Store:
```text
parent_prediction_id
```

This enables:
- acceptance rate;
- correction distance;
- detector quality;
- annotation efficiency.

---

# 9. Microaneurysm protocol

Default:
- mark center point of each visible MA;
- one point per lesion;
- do not expand into diameter mask unless specific research subprotocol requires;
- ambiguous red dots may be `LOW` certainty or omitted/escalated according to ophthalmology-approved guide.

AI review:
- candidate points are suggestions;
- clinicians confirm/reject/add;
- rejection reason optional.

---

# 10. Hemorrhage protocol

Default:
- outline lesion region as polygon;
- if time burden is high, a separate box-only task may be created;
- do not mix box and polygon within the same task unless training pipeline explicitly supports both.

---

# 11. Exudates and cotton-wool

Hard exudate:
- polygon/mask around contiguous region or cluster according to approved guide.

Cotton-wool:
- polygon/mask;
- canonical term `cotton_wool_spot`;
- mapping from dataset term `soft_exudate`.

---

# 12. Neovascularization protocol

Fields:

```text
label: nvd | nve
geometry: polygon
certainty
comment optional
```

If type cannot be resolved:
- mark for specialist review;
- do not silently map to NVE.

Weak AI evidence may be displayed as a non-annotation overlay but must be labeled as model evidence.

---

# 13. DME / edema protocol

## Fundus/UWF

Allowed future fields:
```text
macular_hard_exudate_present
maculopathy_suspected
foveal_involvement_suspected
```

These are not equivalent to OCT-confirmed DME.

## OCT

When OCT workflow is added:

```text
dme_grade:
  NO_DME
  NCI_DME
  CI_DME
```

If fluid segmentation is later needed:
- intraretinal fluid;
- subretinal fluid;
- retinal thickening metrics;
must be defined in a separate OCT annotation protocol.

---

# 14. Review protocol

Suggested levels:

```text
L0 AI suggestion
L1 clinician annotation
L2 specialist adjudication
L3 locked reference
```

Training eligibility:

| Level | Default trainable? |
|---|---|
| L0 | no |
| L1 | yes only by experiment policy |
| L2 | yes |
| L3 | yes; may be validation-only depending split |

Sentinel annotations are never training examples.

---

# 15. Batch design

First local batch should cover:
- source-like cases;
- local domain extremes;
- each camera/site;
- each predicted grade;
- uncertainty;
- OOD;
- model disagreement;
- rare lesion candidates.

Do not select only easy/high-confidence cases.

---

# 16. Annotation time telemetry

Per image:
```text
opened_at
submitted_at
active_annotation_seconds
ai_objects_offered
ai_objects_confirmed
ai_objects_rejected
ai_objects_corrected
human_objects_added
```

This data is operational/research telemetry, not a clinician performance score.

---

# 17. Annotation guide content required before pilot

The ophthalmology team must approve:
- class definitions;
- positive/negative examples;
- geometry examples;
- ambiguous cases;
- grade hierarchy;
- what counts as ungradable;
- how to handle laser scars;
- NVD vs NVE;
- when to mark uncertain;
- when to escalate.

Engineering must not invent clinical definitions that are absent from the guide.

---

# 18. Change control

Schema changes require:
- new semantic version;
- migration note;
- dataset compatibility declaration.

Examples:
```text
annotation.v0.1
annotation.v0.2
```

Do not silently reinterpret historical labels.
