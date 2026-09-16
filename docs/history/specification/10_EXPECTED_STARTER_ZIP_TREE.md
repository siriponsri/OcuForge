# EXPECTED STARTER ZIP TREE

GPT Work may adjust filenames slightly only when necessary, but must preserve capabilities and separation.

```text
eyes-detected-dual-track-starter-v0.1/
│
├── eyes-detected-contracts/
│   ├── README.md
│   ├── pyproject.toml
│   ├── src/eyes_contracts/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── validators.py
│   │   └── cli.py
│   ├── schemas/
│   │   ├── image_manifest.v0.1.schema.json
│   │   ├── dataset_manifest.v0.1.schema.json
│   │   ├── prediction.v0.1.schema.json
│   │   ├── annotation.v0.1.schema.json
│   │   ├── annotation_batch.v0.1.schema.json
│   │   ├── experiment_run.v0.1.schema.json
│   │   └── model_manifest.v0.1.schema.json
│   ├── examples/
│   └── tests/
│
├── eyes-detected-models/
│   ├── README.md
│   ├── QUICKSTART_TH.md
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── compose.yaml
│   ├── .devcontainer/
│   ├── .env.example
│   ├── configs/
│   │   ├── datasets/
│   │   ├── encoders/
│   │   ├── models/
│   │   └── experiments/
│   ├── src/eyes_detected/
│   │   ├── data/
│   │   ├── tiling/
│   │   ├── encoders/
│   │   │   ├── base.py
│   │   │   ├── dinov3_adapter.py
│   │   │   └── tiny_test_encoder.py
│   │   ├── features/
│   │   ├── mil/
│   │   ├── ordinal/
│   │   ├── lesions/
│   │   ├── qc/
│   │   ├── ood/
│   │   ├── adaptation/
│   │   ├── active_learning/
│   │   ├── evaluation/
│   │   └── provenance/
│   ├── scripts/
│   ├── jobs/gpu/
│   ├── examples/
│   ├── tests/
│   └── docs/
│       ├── ARCHITECTURE.md
│       ├── DATASETS.md
│       ├── DINO_SETUP.md
│       ├── GPU_RUNBOOK.md
│       └── SAFETY.md
│
├── eyes-detected-labeler/
│   ├── README.md
│   ├── QUICKSTART_TH.md
│   ├── pyproject.toml
│   ├── compose.yaml
│   ├── .env.example
│   ├── src/labeler_bridge/
│   │   ├── cvat_client/
│   │   ├── geometry/
│   │   ├── import_predictions/
│   │   ├── export_annotations/
│   │   ├── provenance/
│   │   └── cli.py
│   ├── annotation_guides/
│   │   ├── DR_GRADING_GUIDE_DRAFT_TH.md
│   │   ├── MA_POINT_GUIDE_DRAFT_TH.md
│   │   ├── LESION_REGION_GUIDE_DRAFT_TH.md
│   │   └── NV_GUIDE_DRAFT_TH.md
│   ├── fiftyone_adapter/
│   ├── examples/
│   ├── tests/
│   └── docs/
│       ├── CVAT_SETUP_TH.md
│       ├── CLINICIAN_WORKFLOW_TH.md
│       ├── PROVENANCE.md
│       └── BACKUP_EXPORT.md
│
├── docs/
│   ├── START_HERE_TH.md
│   ├── DUAL_TRACK_ARCHITECTURE.md
│   ├── LOCAL_SETUP_TH.md
│   ├── GPU_EXECUTION_TH.md
│   ├── SAFETY_AND_SCOPE.md
│   └── NEXT_STEPS.md
│
├── scripts/
│   ├── validate_all.sh
│   └── package_check.py
│
└── validation/
    └── FINAL_DELIVERY_REPORT.md
```

---

# Required demo path

The generated starter must demonstrate this synthetic roundtrip:

```text
synthetic image manifest
       ↓
Track A synthetic/test model
       ↓
prediction.v0.1
       ↓
Track B import/geometry conversion
       ↓
synthetic clinician correction fixture
       ↓
annotation.v0.1
       ↓
Track A/Contracts validator
       ↓
active-learning batch fixture
```

No real patient image is needed to prove the integration.
