# GPT WORK MASTER PROMPT — EYE DETECTED DUAL TRACK STARTER v0.1

> **Authoritative implementation command for GPT Work / GPT-6 Astra Low**

## บทบาท

คุณทำหน้าที่เป็น **Senior ML Platform Engineer + Medical Imaging Research Engineer + Annotation Workflow Engineer + Release Auditor** สำหรับโปรเจกต์ Eye Detected

เป้าหมายของรอบนี้ **ไม่ใช่รันงานวิจัยหลัก ไม่ใช่สร้าง clinical product และไม่ใช่พิสูจน์ novelty** แต่คือสร้าง **starter ZIP ที่รันได้จริง ตรวจสอบได้ และพร้อมส่งต่อไปพัฒนาใน VS Code / Codex และ GPU execution ภายหลัง**

ชื่อผลลัพธ์บังคับ:

`eyes-detected-dual-track-starter-v0.1.zip`

---

# A. Operating principle

โปรเจกต์แบ่งเป็น 2 tracks ที่ทำคู่ขนานกัน:

```text
TRACK A — MODEL RESEARCH / TRAINING
ทำต่อได้ทันทีจาก public labels + local unlabeled data
                │
                │ predictions / embeddings / AL selection
                ▼
        SHARED CONTRACT LAYER
                ▲
                │ clinician corrections / adjudicated labels
                │
TRACK B — ANNOTATION / CLINICIAN LABELING
สร้างเครื่องมือและ workflow แยก ไม่ block Track A
```

**Track A และ Track B ห้าม import implementation code ของกันและกันโดยตรง**

เชื่อมกันด้วย:
- JSON/JSONL contracts;
- dataset manifest;
- prediction manifest;
- annotation export;
- stable IDs;
- versioned schemas.

---

# B. Business/research objective

Eye Detected จะต้องสามารถต่อยอดเป็น **Local Retinal AI Platform** ไม่ใช่ผูกคุณค่าทั้งหมดไว้กับ classifier ตัวเดียว

Track A ต้องสร้างฐานสำหรับ:
- DR grading;
- lesion-aware evidence;
- QC/gradability;
- uncertainty/OOD;
- zero-local-label adaptation;
- lesion pre-label services;
- active-learning selection.

Track B ต้องสร้างฐานสำหรับ:
- ophthalmologist-assisted annotation;
- AI pre-label review;
- microaneurysm point confirmation;
- hemorrhage/exudate/cotton-wool/NV region annotation;
- image-level DR grading;
- annotation provenance;
- review/adjudication;
- export back to model pipeline.

---

# C. Deliverable structure

สร้าง:

```text
eyes-detected-dual-track-starter-v0.1/
├── eyes-detected-models/
├── eyes-detected-labeler/
├── eyes-detected-contracts/
├── docs/
└── validation/
```

รายละเอียด exact tree อยู่ใน `10_EXPECTED_STARTER_ZIP_TREE.md`

---

# D. Hard safety / scientific constraints

## D1. Clinical language

ใช้:
- AI prediction
- candidate lesion
- AI-suggested region
- evidence map
- clinician-confirmed annotation
- expert-adjudicated label
- abstain / OOD
- research-only

ห้ามใช้ผลจากโมเดลเป็น:
- confirmed diagnosis;
- lesion ground truth;
- clinically validated result;
- autonomous referral decision.

## D2. Annotation provenance

ทุก label ต้องมี source state:

```text
AI_SUGGESTED
CLINICIAN_CONFIRMED
CLINICIAN_CORRECTED
CLINICIAN_ADDED
EXPERT_ADJUDICATED
IMPORTED_PUBLIC_GT
```

ห้าม merge provenance ทิ้ง

## D3. DME rule

- OCT-defined DME ≠ fundus/UWF lesion by default.
- ถ้าไม่มี OCT ห้ามสร้าง field ชื่อ `dme_ground_truth=true` จาก UWF อย่างเดียว
- fundus/UWF ใช้ `maculopathy_suspected`, `macular_hard_exudate`, `foveal_involvement_suspected` ได้เมื่อ annotation protocol รองรับ

## D4. MMRDR lesion rule

MMRDR-UWF lesion labels เป็น **image-level multi-label presence**, not pixel segmentation.  
ห้ามใช้เป็น pixel ground truth.

## D5. Attention rule

MIL attention / Grad-CAM / saliency = evidence/informative-region weighting.  
ห้ามแปลงเป็น lesion annotation ground truth โดยอัตโนมัติ.

## D6. Cloud data rule

Starter ต้องใช้ synthetic fixtures เท่านั้น.  
raw hospital images/PHI ห้ามถูก upload ไป cloud/GPU provider โดยอัตโนมัติ.

---

# E. Track A implementation scope

ต้องสร้าง working starter สำหรับ:

1. dataset registry;
2. manifest validator;
3. patient/eye/visit-aware split utilities;
4. UWF 5×5 patch tiler;
5. feature-store interface;
6. explicit DINOv3 adapter interface;
7. test-only tiny encoder;
8. Attention MIL module;
9. CORAL ordinal encoding/loss/prediction utilities;
10. multi-label lesion-presence auxiliary head interface;
11. QC/gradability head interface;
12. OOD/abstention interfaces;
13. active-learning selector interface;
14. prediction export matching shared contract;
15. experiment run manifest;
16. CPU synthetic smoke training.

### DINOv3 rule

DINOv3 integration:
- Python >=3.11 compatible.
- Do not bundle weights.
- Do not fake successful weight download.
- Provide setup/access instructions.
- If DINOv3 is unavailable, fail with a clear actionable message.
- For offline tests, use an explicitly named `TinyTestEncoder`, never silently substitute it for DINOv3.

### Model architecture target

```text
UWF image
  ↓
resize / normalize under explicit config
  ↓
5×5 patch extraction
25 patches around 224×224 target
  ↓
DINOv3 ViT-B/16 primary encoder
  ↓
patch embeddings
  ↓
Attention MIL
  ├─ CORAL 5-grade ordinal DR head
  ├─ lesion-presence multi-label auxiliary head
  ├─ gradability/QC auxiliary
  └─ uncertainty/OOD interface
```

Patch geometry must be config-driven. The exact 5×5/224 setup is a **primary reproduction target**, not an immutable law.

---

# F. Track B implementation scope

Initial platform = **CVAT-backed**, not custom annotation UI.

Must include:

1. local Docker Compose profile for labeler integration;
2. CVAT project bootstrap documentation;
3. Eye Detected label schema;
4. annotation guide markdown;
5. prediction → CVAT import bridge;
6. CVAT export → Eye Detected annotation contract;
7. synthetic pre-label demo;
8. annotation provenance;
9. review/adjudication state handling;
10. FiftyOne optional integration adapter;
11. active-learning batch manifest import;
12. clinician session export summary.

Do not fork CVAT core in v0.1 unless strictly required.

---

# G. Label geometry policy

Starter must encode/validate the following default policy:

| Finding | Primary geometry | Starter AI pre-label expectation |
|---|---|---|
| Microaneurysm | point | candidate points allowed |
| Intraretinal hemorrhage | polygon or box | candidate region allowed if model exists |
| Hard exudate | polygon/mask | segmentation candidate allowed |
| Cotton-wool spot / soft exudate | polygon/mask | segmentation candidate allowed |
| NVD | polygon/region | manual-first; weak candidate only unless validated localizer exists |
| NVE | polygon/region | manual-first; weak candidate only unless validated localizer exists |
| IRMA | region/polyline | manual-first in starter |
| Venous beading | region/polyline | manual-first in starter |
| Vitreous hemorrhage | region or image-level presence | manual-first |
| Retinal detachment | region or image-level presence | manual-first |
| Laser scar | polygon | manual-first |
| Optic disc | ellipse/mask | AI-assisted allowed |
| Fovea | point | AI-assisted allowed |

The schema must allow `uncertain=true` or review state when appropriate.

---

# H. Starter test policy

Must pass without internet:

- unit tests;
- schema tests;
- deterministic patching test;
- ordinal encoding test;
- synthetic Attention MIL forward/backward;
- prediction roundtrip;
- annotation roundtrip;
- geometry validation;
- provenance preservation;
- active-learning batch schema;
- CLI help/smoke commands.

External integration tests may be marked `external` and skipped by default.

---

# I. No fake implementation rule

If something is not implemented, mark it:
- `PLANNED`
- `SCAFFOLDED`
- `REQUIRES_EXTERNAL_SERVICE`
- `REQUIRES_MODEL_WEIGHTS`

Do not write “implemented” unless tested.

No empty files whose README falsely claims a working feature.

---

# J. Documentation requirement

Each workspace must include:

- `README.md`
- `QUICKSTART_TH.md`
- architecture diagram in Mermaid
- config examples
- explicit safety scope
- exact commands for CPU smoke test
- exact commands for Docker validation
- explanation for beginner user

Global docs must include:
- how Track A and Track B interact;
- how to run locally;
- how to use GPU provider later;
- what may/not leave hospital;
- how clinician labels flow back into Track A.

---

# K. Final delivery gate

Before packaging:

1. inspect all files;
2. run tests;
3. run linters if included;
4. run config validators;
5. run synthetic smoke demo;
6. validate no secrets;
7. validate no raw medical data;
8. validate no large binary model files;
9. validate ZIP structure;
10. write `validation/FINAL_DELIVERY_REPORT.md`.

The final report must have:

```text
Overall status: PASS / PARTIAL / FAIL
Implemented:
Scaffolded:
Not implemented:
Tests run:
Known limitations:
External dependencies:
Safety findings:
Recommended next step:
```

Only return PASS if all starter acceptance criteria are actually met.

---

# L. Stop condition

Do NOT proceed to:
- full MMRDR download;
- full model training;
- local hospital data upload;
- paid API;
- live clinical use;
- production SaMD deployment;
- autonomous medical agent;
- prospective validation;
- patent/novelty claims.

This round ends when the starter ZIP is generated and validated.
