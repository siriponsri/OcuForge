# SHARED CONTRACTS, DATA GOVERNANCE & PROVENANCE

## 0. Purpose

This is the interface between Track A and Track B.

The contract layer should be stable even when:
- model encoder changes;
- annotation backend changes;
- GPU provider changes;
- Docker base changes;
- custom clinician UI replaces CVAT.

---

# 1. Repository

`eyes-detected-contracts`

Contains:
- JSON Schema;
- Pydantic models or language-neutral schemas;
- sample fixtures;
- versioning policy;
- validation CLI;
- migrations only when needed.

No training code.  
No CVAT-specific code.

---

# 2. Core contract types

1. `image_manifest.v0.1`
2. `dataset_manifest.v0.1`
3. `prediction.v0.1`
4. `annotation.v0.1`
5. `annotation_batch.v0.1`
6. `experiment_run.v0.1`
7. `model_manifest.v0.1`

---

# 3. Image manifest

Example:

```json
{
  "schema_version": "image_manifest.v0.1",
  "image_id": "IMG_001",
  "file_sha256": "…",
  "relative_uri": "images/IMG_001.jpg",
  "patient_pseudo_id": "P_001",
  "eye_id": "P_001_OD",
  "visit_id": "V_001",
  "laterality": "OD",
  "modality": "UWF",
  "camera_make": "UNKNOWN",
  "camera_model": "UNKNOWN",
  "width_px": 3900,
  "height_px": 3072,
  "site_id": "SITE_A",
  "split": "UNASSIGNED",
  "cloud_eligible": false
}
```

No patient name, hospital number or plaintext PHI.

---

# 4. Dataset manifest

Must describe label scope.

Example:

```json
{
  "schema_version": "dataset_manifest.v0.1",
  "dataset_id": "mmrdr_uwf_v1",
  "modality": ["UWF"],
  "source_type": "PUBLIC",
  "label_scope": {
    "dr_grade": "IMAGE_LEVEL_ORDINAL",
    "lesions": "IMAGE_LEVEL_MULTILABEL",
    "pixel_masks": false
  },
  "split_unit": "PATIENT",
  "license_status": "REVIEWED",
  "data_root_env": "MMRDR_ROOT"
}
```

This prevents accidental use of weak labels as segmentation GT.

---

# 5. Prediction contract

Must distinguish:
- classification;
- lesion presence;
- object candidates;
- evidence maps;
- OOD.

Example:

```json
{
  "schema_version": "prediction.v0.1",
  "prediction_id": "PRED_001",
  "image_id": "IMG_001",
  "model_manifest_id": "MODEL_001",
  "dr": {
    "grade": 2,
    "ordinal_probs": [0.93, 0.81, 0.33, 0.05],
    "confidence": 0.81
  },
  "lesion_presence": {
    "microaneurysm": 0.92,
    "hard_exudate": 0.44
  },
  "objects": [
    {
      "object_id": "OBJ_001",
      "label": "microaneurysm",
      "geometry": {
        "type": "point",
        "coordinates_norm": [0.431, 0.617]
      },
      "confidence": 0.72,
      "origin": "AI_SUGGESTED"
    }
  ],
  "ood": {
    "method": "prototype_distance_v1",
    "score": 0.11,
    "abstain_recommended": false
  }
}
```

---

# 6. Evidence map contract

Evidence/saliency must be separate from annotation objects.

```json
{
  "type": "mil_attention",
  "patch_scores": [0.01, 0.02],
  "disclaimer": "MODEL_EVIDENCE_NOT_LESION_GROUND_TRUTH"
}
```

Track B may show it as overlay but must not import it as a lesion annotation automatically.

---

# 7. Annotation contract

Example:

```json
{
  "schema_version": "annotation.v0.1",
  "annotation_id": "ANN_001",
  "image_id": "IMG_001",
  "label": "microaneurysm",
  "geometry": {
    "type": "point",
    "coordinates_norm": [0.429, 0.620]
  },
  "origin": "CLINICIAN_CORRECTED",
  "parent_prediction_id": "PRED_001",
  "parent_object_id": "OBJ_001",
  "annotator_id_hash": "USR_HASH",
  "review_status": "SUBMITTED",
  "clinician_certainty": "HIGH"
}
```

---

# 8. Batch manifest

Example:

```json
{
  "schema_version": "annotation_batch.v0.1",
  "batch_id": "LOCAL_R0_001",
  "dataset_id": "local_uwf_2026q3",
  "selection": {
    "strategy": "diversity_plus_disagreement_v1",
    "model_manifest_id": "MODEL_001"
  },
  "items": [
    {
      "image_id": "IMG_001",
      "priority": 0.92,
      "reasons": ["OOD", "GRADE_DISAGREEMENT"],
      "locked_sentinel": false
    }
  ]
}
```

---

# 9. Experiment run manifest

Required for every non-trivial run:

```text
run_id
timestamp
git_sha
docker_image
config_hash
dataset_manifest_ids
model_manifest_parent
random_seed
gpu_name
cuda_version
framework_version
metrics_path
artifact_path
status
```

This enables reproducibility.

---

# 10. Model manifest

A model release/candidate must include:

```text
model_manifest_id
name
version
status: RESEARCH | CANDIDATE | LOCKED_VALIDATION | PRODUCTION
architecture
encoder
weight_hash
training_run_id
training_dataset_ids
known_limitations
intended_research_use
calibration_version
ood_method
created_at
```

Production status is future-only.

---

# 11. Data lineage

Every trainable annotation should be traceable:

```text
original image
  ↓
AI prediction (optional)
  ↓
clinician annotation
  ↓
adjudication
  ↓
dataset release version
  ↓
experiment run
  ↓
model candidate
```

If any link is missing, lineage status must be incomplete.

---

# 12. Hashing

Use SHA-256 for:
- files;
- configs;
- model weights;
- manifests when practical.

Do not use hashes as a substitute for access control.

---

# 13. Split integrity

The contract validator must detect:
- same patient in train and sentinel;
- same image hash in multiple splits;
- annotation batch includes forbidden split;
- accidental train use of sentinel labels.

---

# 14. PHI rules

Contracts must not require:
- patient name;
- national ID;
- medical record number;
- phone;
- address;
- exact birth date.

If linkage to hospital systems is later required, retain only a local mapping key under hospital governance.

---

# 15. Cloud eligibility

Every dataset/image record should support:

```text
cloud_eligible: true|false
```

Default for local hospital data:
```text
false
```

Changing this requires governance decision outside the model code.

---

# 16. Contract compatibility

Semantic versioning:

- patch = backward-compatible metadata clarification;
- minor = additive fields;
- major = incompatible semantics.

Track A and B must declare supported contract versions at startup.

---

# 17. Test fixtures

Contracts repo must include synthetic examples:
- normal valid record;
- malformed coordinates;
- invalid DR grade;
- missing provenance;
- weak label incorrectly marked as pixel GT;
- sentinel leakage;
- unknown schema version.

All validators must have unit tests.
