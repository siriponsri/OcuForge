# OcuForge Product POC Phase 0–4 Runbook

**Status:** EXECUTION RUNBOOK  
**Target branch:** `product/encoder-head-v0.1`  
**Scope:** Product implementation only — Phases 0 through 4  
**Primary objective:** Deliver a working end-to-end local/on-prem clinician-review POC from image ingestion through reviewed export and training manifest generation.

---

## 1. Authority and reading order

Before implementation, read and treat these as the active product specifications:

1. `docs/product/PRODUCT_UX_SPEC.md`
2. `docs/product/PRODUCT_ARCHITECTURE.md`
3. `docs/product/PRODUCT_DATA_MODEL.md`
4. `docs/product/PRODUCT_BACKLOG.md`

This runbook controls execution order and stop conditions.

```text
RESEARCH_BLOCKED != PRODUCT_BLOCKED
```

Do not alter scientific conclusions, R1 status, or research claims in this run.

---

## 2. Product goal

Build the first working OcuForge customer workflow:

```text
Choose input source
    -> ingest local DICOM / supported raster
    -> Queue
    -> open image
    -> explicit Run AI
    -> system DR Grade + mock system annotations
    -> clinician review / annotation / correction / remark
    -> Save & Return
    -> local NoSQL persistence
    -> export artifacts
    -> manifest.csv / index.csv
```

The first POC validates workflow, provenance, persistence, export, and training-data lineage.

It does **not** validate model quality.

---

## 3. Execution principles

Use:

```text
PASS
PASS_WITH_WARNINGS
BLOCKED
```

Warnings must not stop a valid POC.

Use `BLOCKED` only when continuing would:
- corrupt or overwrite source data;
- violate privacy/governance;
- create training-label provenance ambiguity;
- create unrecoverable state inconsistency;
- make the required workflow technically impossible.

Normal implementation defects should be fixed and continued, not promoted into project-wide scientific blockers.

---

## 4. Branch and change discipline

Work only from:

```text
product/encoder-head-v0.1
```

Rules:
- do not create additional long-lived product branches;
- temporary worker branches are allowed only when Orca requires them;
- merge/reconcile temporary work immediately, then delete it;
- do not merge archived research/recovery branches wholesale;
- selectively reuse existing code only when it matches current product contracts;
- keep `main` untouched during this implementation goal;
- never commit hospital/private data, credentials, PHI-bearing DICOM, model weights, or machine-local secrets.

Use synthetic/de-identified fixtures only.

---

# 5. Implementation sequence

## Phase 0 — Product contracts and vocabulary

Implement the minimum versioned contract layer needed by Phases 1–4.

Required concepts:
- Source
- Destination
- DICOM identity
- Display derivative
- Image
- Case
- Prediction
- Annotation revision
- Review
- Export job / receipt
- Manifest snapshot
- operational statuses
- output policy
- training eligibility

Canonical operational fields:

```text
review_status:
  NOT_STARTED
  IN_REVIEW
  HUMAN_REVIEWED

ai_status:
  NOT_RUN
  RUNNING
  PROCESSED
  FAILED

export_status:
  NOT_EXPORTED
  EXPORTING
  EXPORTED
  FAILED
```

Canonical eligibility:

```text
HUMAN
PSEUDO_LABEL
WEAK_LABEL
UNREVIEWED_SYSTEM
```

Invariant:

```text
SYSTEM AUTO LABEL != HUMAN GROUND TRUTH
```

Canonical output policies:

```text
REFERENCE_ONLY
COPY_ORIGINAL
DERIVED_IMAGE_ONLY
COPY_ORIGINAL_AND_DERIVED
```

`REFERENCE_ONLY` is the default for large DICOM workflows.

### Phase 0 gate

PASS when:
- contracts are versioned;
- status terms are consistent;
- review / AI / export states are independent;
- system output cannot silently become `HUMAN`;
- tests cover validation and incompatible states.

---

## Phase 1 — Local ingestion + first-class DICOM + Queue

Implement local input/output first.

### Required components

```text
LocalFileSystemBridge / LocalPathAdapter
SourceAdapter
DestinationAdapter
ImageIngestionService
DICOMAdapter
RasterAdapter
CaseRepository
local immutable object storage
Queue service/API
```

### Local path rule

Do not assume a normal browser has unrestricted filesystem access.

The UI consumes provider-neutral references behind `LocalFileSystemBridge`.

Acceptable implementations include:
- local backend path picker;
- desktop/native bridge;
- supported browser filesystem capability.

### DICOM is mandatory Phase 1

Support:
- discovery;
- original-byte preservation;
- SHA-256 before conversion;
- safe technical metadata extraction;
- display derivative generation;
- provenance for frame/orientation/windowing/color/preprocessing where applicable;
- quarantine of malformed/unsupported objects;
- Queue creation.

Preserve, where applicable:

```text
study_instance_uid
series_instance_uid
sop_instance_uid
frame_number
transfer_syntax_uid
```

Never write annotations into original DICOM.

### Multi-frame rule

Treat the source object and reviewable frame identity separately.

Every reviewable frame must have deterministic lineage back to:
- source object SHA-256;
- SOP Instance UID where available;
- exact frame number.

Do not allow one annotation to ambiguously refer to an entire multi-frame object.

### Queue

Queue must expose:
- image/case ID;
- source/folder;
- modality/laterality;
- system grade if available;
- human grade if available;
- review status;
- AI status;
- export status;
- derived presentation badge;
- retry/recovery action.

The derived badge is UI only and never replaces canonical status fields.

### Phase 1 gate

PASS when fixtures demonstrate:
- at least one valid DICOM ingestion;
- at least one raster ingestion;
- byte-identical DICOM preservation;
- verified hashes;
- usable display derivative;
- malformed DICOM quarantine;
- resumable/idempotent ingestion;
- Queue state persistence.

---

## Phase 2 — Mock ModelAdapter + first review loop

Implement an architecture-agnostic deterministic mock `ModelAdapter`.

The UI must not import or name a concrete encoder architecture.

A future real model bundle will contain:

```text
encoder
head
preprocessing
calibration
model manifest
runtime / license / compatibility metadata
```

### Required workflow

```text
Open case
    -> no automatic inference
    -> user clicks Run AI
    -> ai_status=RUNNING
    -> immutable mock prediction
    -> ai_status=PROCESSED
```

Mock output may include:
- DR grade;
- grade probabilities/confidence;
- synthetic system lesion suggestions;
- model bundle identity.

Never present mock output as a clinical result.

### Review persistence

User can:
- record human DR grade;
- add remark;
- confirm/correct/reject system suggestion;
- save review.

System prediction remains immutable after human correction.

### Phase 2 gate

PASS when:
- opening a case never triggers AI;
- `Run AI` is explicit;
- retry is idempotent;
- system and human grades remain separate;
- review survives AI failure;
- Save persists before export.

---

## Phase 3 — Annotation editor + multi-image review

Implement:

```text
Rectangle / Box
Point
Circle / Ellipse
Polygon
Translucent area presentation
```

System and user annotations must differ by more than color:
- line style;
- fill style/opacity;
- provenance badge;
- accessible text/legend.

Human correction creates a new immutable revision linked to the original system object.

Never overwrite system geometry.

### Multi-image review

Support layouts:

```text
1
2
4
8
```

Each tile owns independent:
- image/frame;
- zoom/pan;
- annotation state;
- system result;
- human edits;
- dirty state;
- save state;
- error state.

One tile failure must not invalidate another tile's successful review.

### Phase 3 gate

PASS when:
- every geometry interaction is testable;
- revision lineage is preserved;
- system geometry remains recoverable;
- multi-tile state does not cross-mutate;
- Save & Return works from single and multi-image review.

---

## Phase 4 — Export + Manifest

Implement local export first.

### Export behavior

Save order:

```text
1. Persist review + annotation revisions locally
2. Update local dataset eligibility/index state
3. Start/export selected artifacts
4. Verify exported hashes
5. Update export_status
```

Important:

```text
Manifest / dataset eligibility must NOT depend on export success.
```

If export fails after review persistence:

```text
review_status = HUMAN_REVIEWED
export_status = FAILED
```

The reviewed case remains available for local dataset selection.

### Artifact layout

Recommended logical structure:

```text
<output-root>/<source-folder-id>/<case-id>/
  export_manifest.json
  image_metadata.json
  source_reference.json
  system_predictions.json
  annotations.json
  review.json
  audit_events.jsonl
  preview/annotated.<format>        optional
  source/original.<format>          only when copy policy allows
```

No annotation may be burned into the original DICOM.

### Manifest requirements

`manifest.csv` / `index.csv` must include enough lineage to train downstream code deterministically.

Required training-lineage fields include:

```text
annotation_artifact_uri
annotation_revision_hash
annotation_schema_version
training_image_uri
training_image_sha256
derivative_preprocessing_version
human_grading_protocol
training_eligibility
```

ROI/lesion records must identify exact annotation geometry/revision, not only counts.

`UNREVIEWED_SYSTEM` is never selected as human ground truth.

### Phase 4 gate

PASS when:
- export policies work locally;
- output is deterministic/idempotent;
- export hashes verify;
- export failure preserves review;
- manifest generation works independently of export success;
- manifest rows identify exact review/annotation/training image lineage.

---

# 6. UI acceptance path

The first POC must support this user story end-to-end:

```text
Sources
  -> choose local input folder
  -> choose local output folder
  -> choose output policy
  -> Start ingestion

Queue
  -> view/filter cases
  -> open unreviewed image

Review & Label
  -> Run AI
  -> inspect System result
  -> draw/edit annotations
  -> enter human DR grade
  -> optional remark
  -> Save & Return

Queue
  -> immediately reflect human-reviewed state
  -> independently show export success/failure

Summary
  -> group by source folder
  -> group by SYSTEM DR grade
  -> separate Human Reviewed Grade view

Dataset / Manifest
  -> inspect eligibility
  -> verify exact annotation/training lineage
  -> export manifest/index
```

---

# 7. Privacy and external-service boundary

Hospital/private data is local/on-prem authoritative.

Google Drive is optional and not required for this goal.

Future rule:

```text
Google Drive may receive hospital/private source or output artifacts only when
explicitly authorized by local hospital governance and configured through the
governed Drive adapter.
```

All other public/cloud services remain prohibited for hospital/private data by default.

No public GPU use in this goal.

---

# 8. Explicitly out of scope

Do NOT:
- resolve R1 duplicate leakage;
- train C0/C1/C2;
- run SSL;
- train an encoder/head;
- create RunPod/Vast jobs;
- select a research champion;
- implement Phase 9 Product Model Factory execution;
- make diagnostic or clinical-performance claims;
- implement HL7/FHIR;
- implement production IAM;
- require Label Studio or CVAT for the core review loop;
- push private/hospital DICOM anywhere external.

Phase 9 remains planned only.

---

# 9. Forward-compatibility requirements for Phase 9

Do not implement training yet, but Phase 0–4 must not block the future unlabeled-first model factory:

```text
Hospital unlabeled pool
    -> identity registry + QC
    -> patient/identity-safe split
    -> TRAIN identities
    -> SSL encoder adaptation
    -> embedding / representative sampling
    -> clinician labeling subset
    -> lightweight head training
    -> held-out validation
    -> calibration
    -> versioned model bundle
```

Do not design Phase 0–4 in a way that assumes all images must be human-labeled before encoder adaptation.

---

# 10. Validation

Before declaring the goal complete, run the repository's applicable validation suite, including:

```text
python -m pytest
python -m ruff check .
python scripts/validate_configs.py
python scripts/package_check.py
git diff --check
```

Also run appropriate frontend build/tests and browser interaction tests for the implemented UI stack.

Required POC tests:
- DICOM byte preservation;
- DICOM technical metadata/privacy boundary;
- multi-frame frame identity;
- hash/deduplication;
- ingestion retry/idempotency;
- Queue independent statuses;
- explicit mock Run AI;
- prediction immutability;
- human revision lineage;
- all annotation geometries;
- 1/2/4/8 independent review;
- persistence-before-export;
- export failure recovery;
- all output policies;
- manifest lineage and eligibility;
- `UNREVIEWED_SYSTEM` exclusion.

---

# 11. Completion criteria

The goal is complete only when a clean local demonstration can show:

```text
local folder
-> DICOM ingestion
-> Queue
-> Review
-> explicit mock Run AI
-> human annotation / DR grade / remark
-> Save & Return
-> persistent local state
-> export artifacts
-> manifest.csv / index.csv
```

No training is required for this goal.

Final status must report:

```text
PRODUCT_PHASE_0
PRODUCT_PHASE_1
PRODUCT_PHASE_2
PRODUCT_PHASE_3
PRODUCT_PHASE_4
TEST_STATUS
BUILD_STATUS
MAIN_UNCHANGED
PRODUCT_BRANCH_SHA
KNOWN_WARNINGS
BLOCKERS
NEXT_RECOMMENDED_GOAL
```
