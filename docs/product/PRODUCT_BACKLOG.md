# OcuForge Product Backlog

**Status:** Product-track implementation sequence
**Starting branch:** `product/encoder-head-v0.1`
**Ordering principle:** Customer value first, with provenance and safety as prerequisites

## 1. Product-track guardrails

This backlog does not authorize model training, Pods, external experiments, R1 scientific blocker resolution, or
production clinical deployment. Research status and product status are independent:

```text
RESEARCH_BLOCKED != PRODUCT_BLOCKED
```

The first product POC uses synthetic or explicitly authorized local fixtures and a deterministic mock model adapter.
Private hospital data remains on-premise. Google Drive support is optional and policy-gated.

## 2. Ordered phases

### Phase 0 — Product contracts and vocabulary

**Customer value:** Prevents unsafe ambiguity before implementation.

Deliver:

- product document IDs and schema versions;
- source/destination terminology;
- queue states and transitions;
- separate system/human grade semantics;
- annotation provenance and revision rules;
- training eligibility values;
- adapter seams and local/cloud boundary;
- acceptance fixture strategy.

Exit criteria:

- all product teams use the same `case`, `image`, `prediction`, `annotation revision`, `review`, `export job`, and
  `manifest snapshot` definitions;
- no document treats system output as ground truth;
- contract ownership is agreed before code begins.

### Phase 1 — Local source ingestion and Queue

**Customer value:** Turns an unlabeled folder into a searchable, durable work queue.

Deliver:

- local folder `SourceAdapter`;
- `ImageIngestionService` with hash, deduplication, immutable object storage, and item-level errors;
- image/case/source documents;
- Queue query and required state badges;
- raster fixtures first, with DICOM routed through an explicit capability check.

Exit criteria:

- source bytes are preserved and hashed;
- duplicate content is not stored twice as authoritative data;
- partial ingestion is resumable and visible;
- Queue supports filtering by source folder, modality, laterality, and queue state.

### Phase 2 — First review loop with mock ModelAdapter

**Customer value:** Gives a clinician a complete local review loop without waiting for research model execution.

Deliver:

- explicit `Run AI` action;
- versioned deterministic mock model bundle manifest;
- immutable system prediction storage;
- Review & Label page;
- human DR grade, remark, and save/return flow;
- system/human distinction in UI and storage.

Exit criteria:

- AI never runs merely by opening a case;
- system prediction survives correction and rejection;
- Save persists review state before export;
- stale concurrent edits are rejected and recoverable.

### Phase 3 — Annotation editor and provenance history

**Customer value:** Makes review useful for localized labeling and correction.

Deliver:

- rectangle/box;
- point;
- circle/ellipse;
- polygon;
- translucent area fill presentation;
- system/user visual legend and accessible provenance labels;
- immutable revision history, undo/cancel, rejection, correction, and audit drawer;
- 1/2/4/8 layouts with independent image state.

Exit criteria:

- every edit creates a new revision or explicit event;
- original system geometry remains recoverable;
- all five geometry interactions are testable offline;
- changing one tile does not mutate another tile.

### Phase 4 — Local export and training manifest

**Customer value:** Produces usable review artifacts and a safe downstream dataset index.

Deliver:

- local `ExportAdapter`;
- deterministic artifact directory;
- metadata, predictions, annotations, review, audit, and optional preview artifacts;
- `manifest.csv` and `index.csv` builder;
- explicit `HUMAN`, `PSEUDO_LABEL`, `WEAK_LABEL`, and `UNREVIEWED_SYSTEM` eligibility;
- export verification and retry.

Exit criteria:

- no raw DICOM duplication by default;
- source references and hashes are preserved;
- export failure does not lose review state;
- unreviewed system rows cannot enter a training-eligible selection.

### Phase 5 — First-class DICOM support

**Customer value:** Makes the product useful for the common hospital input format.

Deliver:

- `DICOMAdapter` technical metadata extraction;
- immutable original DICOM persistence;
- display derivative pipeline;
- frame/orientation/windowing provenance;
- malformed/unsupported DICOM quarantine;
- DICOM privacy and local-only acceptance tests.

Exit criteria:

- original DICOM bytes remain identical after review/export;
- display previews link back to original source hash;
- no patient-identifying fields leave the local boundary;
- unsupported objects become actionable errors.

### Phase 6 — Summary, recovery, and operational polish

**Customer value:** Helps users understand throughput and recover from ordinary failures.

Deliver:

- source-folder and System Grade summary;
- separate Human Reviewed Grade summary;
- queue-state and export-state counts;
- retryable ingestion/model/export errors;
- idempotent jobs and recovery receipts;
- saved filters and clear empty/error/loading states.

Exit criteria:

- summary labels the grade dimension unambiguously;
- partial failures are visible at case and item level;
- retries do not duplicate revisions or artifacts.

### Phase 7 — Optional Google Drive source/output adapters

**Customer value:** Supports governed remote file workflows without changing the local authority model.

Deliver:

- Google Drive folder source adapter;
- Google Drive output adapter;
- provider authorization/read/write readiness states;
- resumable transfer and checksum verification;
- provider IDs/URLs in export receipts;
- no browser-held credentials or raw-data upload outside policy.

Exit criteria:

- Drive is optional and can be disabled without affecting local workflows;
- unauthorized/revoked access is visible and recoverable;
- the same logical artifact contract works for local and Drive output.

### Phase 8 — Optional internal HITL adapters

**Customer value:** Adds specialist review capacity without coupling the customer UI to a labeling vendor.

Deliver:

- Label Studio CE suggestion/confirm/correct/reject/escalate adapter;
- existing provenance sidecar mapping;
- optional CVAT advanced geometry adapter;
- import/export conflict detection.

Exit criteria:

- external task systems cannot overwrite system predictions;
- imported decisions retain source task, model, reviewer, and geometry provenance;
- core product review works with both adapters disabled.

### Phase 9 — Real versioned model bundles

**Customer value:** Replaces the mock adapter with locally deployable encoder + head bundles when approved.

Deliver:

- bundle registry and local runtime loading;
- encoder/head/preprocessing/calibration manifest validation;
- model health and compatibility checks;
- explicit model selection and audit record;
- inference latency/error state handling.

Exit criteria:

- UI remains architecture-agnostic;
- every prediction records the complete bundle identity;
- no model is presented as a diagnosis or clinical decision;
- deployment/license status is distinct from research evidence.

## 3. First working POC acceptance criteria

The first working POC is complete when synthetic or explicitly authorized local fixtures can demonstrate:

- local input-folder selection and local output-folder selection;
- ingestion of supported raster data and at least one DICOM fixture;
- immutable source hash and stable image/case IDs;
- duplicate detection;
- Queue with all six required states;
- explicit `Run AI` through a deterministic versioned mock adapter;
- separate system prediction and human grade;
- all five annotation geometry interactions;
- system/user visual and provenance distinction;
- independent 1/2/4/8 review layouts;
- Save & Return persistence before export;
- immutable audit/revision history;
- deterministic export artifacts and optional preview;
- `manifest.csv`/`index.csv` with training eligibility;
- `UNREVIEWED_SYSTEM` excluded from training eligibility;
- failed export retained as a retryable error;
- offline automated tests with no Pod, training run, external experiment, or R1 state change.

## 4. Test and verification backlog

- unit-test source adapters, hashing, deduplication, queue transitions, and idempotency;
- contract-test DICOM metadata extraction and immutable byte preservation;
- repository tests for optimistic concurrency and immutable revision keys;
- model-adapter tests for explicit invocation, manifest identity, deterministic mock output, and unavailable-model
  failure;
- annotation tests for all geometry types, normalized coordinates, correction/rejection provenance, and multi-image
  independence;
- export tests for deterministic paths, receipts, hash verification, retry, and no-DICOM-duplication default;
- manifest tests for all eligibility values and fail-closed ambiguous provenance;
- browser tests for source setup, Queue states, explicit Run AI, review save, export error, and responsive layouts;
- accessibility checks for keyboard navigation, focus, labels, contrast, reduced motion, and icon semantics.

## 5. Explicitly deferred

- training, SSL, fine-tuning, and encoder selection;
- Pods, GPU execution, and external experiments;
- R1 split-leakage resolution;
- scientific benchmark claims and model promotion;
- clinical deployment, diagnosis, referral, treatment, DICOM clinical integration certification, HL7/FHIR, and
  production IAM;
- automatic conversion of system predictions into human or training ground truth.
