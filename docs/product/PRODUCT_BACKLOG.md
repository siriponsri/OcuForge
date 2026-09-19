# OcuForge Product Backlog

**Status:** Product-track implementation sequence
**Starting branch:** product/encoder-head-v0.1
**Ordering principle:** Customer value first, with provenance, privacy, and recovery as prerequisites

## 1. Product-track guardrails

This backlog does not authorize model training, Pods, external experiments, R1 scientific blocker resolution, or
production clinical deployment. Product and research status are independent:

~~~
RESEARCH_BLOCKED != PRODUCT_BLOCKED
~~~

The first workflow POC uses synthetic or explicitly authorized local fixtures and a deterministic mock ModelAdapter.
Private hospital data, patient linkage, private predictions, and derived artifacts remain on-premise. Google Drive is
optional and policy-gated.

The current research conclusions, including the R1 blocker and no-champion state, are unchanged by this product plan.

## 2. Ordered phases

### Phase 0 - Contracts and vocabulary

**Customer value:** Prevents unsafe ambiguity before implementation.

Deliver:

- versioned product contracts for source, image, DICOM identity, derivative, case, review, prediction, annotation
  revision, export job, manifest snapshot, and future model bundle;
- canonical operational dimensions: review_status, ai_status, and export_status;
- derived Queue badge rules and idempotent retry semantics;
- source/destination and LocalFileSystemBridge vocabulary;
- output policies: REFERENCE_ONLY, COPY_ORIGINAL, DERIVED_IMAGE_ONLY, COPY_ORIGINAL_AND_DERIVED;
- system/human grade semantics, provenance, and eligibility values;
- adapter seams and local/cloud boundary;
- acceptance fixture strategy including valid, malformed, unsupported, multi-frame, and raster inputs.

Exit criteria:

- all product teams use the same terms and schema versions;
- no document treats system output as ground truth;
- a queue composite cannot replace its underlying status dimensions;
- contract ownership is agreed before implementation.

### Phase 1 - Local ingestion + first-class DICOM + Queue

**Customer value:** Turns a mostly unlabeled hospital folder into a safe, searchable, durable work queue.

Deliver:

- LocalFileSystemBridge / LocalPathAdapter capability detection and provider-neutral folder references;
- local folder source and destination adapters;
- DICOM discovery as a core ingestion path, not a late integration;
- immutable source-byte preservation and SHA-256 before conversion;
- DICOM technical metadata extraction, including study/series/SOP/frame/transfer-syntax identifiers where applicable;
- explicit local identity fields: `study_instance_uid`, `series_instance_uid`, `sop_instance_uid`, `frame_number`,
  and `transfer_syntax_uid` where applicable;
- local privacy-safe metadata boundary;
- display derivative generation with frame, orientation, windowing, color, and preprocessing provenance;
- Queue creation for accepted DICOM and raster objects;
- malformed/unsupported DICOM quarantine with stable reasons and retry/review path;
- explicit raster adapters for supported JPEG, PNG, and TIFF inputs;
- deduplication, resumable ingestion, and item-level audit records.

Exit criteria:

- an accepted DICOM retains byte-identical original storage and a verified SHA-256;
- accepted DICOM has a display derivative linked to the source hash;
- technical identifiers are retained locally without PHI entering browser logs, public manifests, Git, cloud services, or telemetry;
- frame/orientation/windowing provenance is present where applicable;
- malformed/unsupported DICOM is quarantined and not silently rasterized;
- Queue can filter source, modality, laterality, ingestion outcome, and derived operational badge;
- raster remains supported but DICOM is the tested hospital-default path.

### Phase 2 - Mock ModelAdapter + first review loop

**Customer value:** Gives a clinician a complete local review loop without waiting for research model execution.

Deliver:

- explicit Run AI action;
- deterministic versioned mock bundle manifest;
- immutable system prediction storage;
- independent ai_status transitions and retry;
- Review & Label page with human DR grade, remark, and save/return;
- system/human distinction in UI and storage;
- durable review state before any export attempt.

Exit criteria:

- opening a case never runs AI;
- system prediction survives correction and rejection;
- AI failure does not erase existing review or annotations;
- Save persists review state before export;
- stale concurrent edits are rejected and recoverable;
- no mock result is presented as a diagnosis or human ground truth.

### Phase 3 - Annotation editor + multi-image review

**Customer value:** Makes review useful for localized labeling and correction.

Deliver:

- rectangle/box, point, circle/ellipse, polygon, and translucent area fill;
- system/user style and accessible provenance legend;
- immutable revision history, undo/cancel, reject, correct, confirm, and audit drawer;
- 1/2/4/8 layouts with independent image state;
- exact parent prediction/object links for edited system annotations;
- annotation schema version and revision hash capture.

Exit criteria:

- every edit creates a new revision or explicit event;
- original system geometry remains recoverable;
- all geometry types are tested offline;
- changing one tile does not mutate another tile;
- annotation provenance is never inferred from visual appearance alone.

### Phase 4 - Export + manifest

**Customer value:** Produces usable review artifacts and a safe downstream dataset index.

Deliver:

- local ExportAdapter;
- explicit output-policy selection and receipts;
- deterministic artifact directory;
- metadata, predictions, annotation revisions, review, audit, and optional annotated preview artifacts;
- manifest.csv and index.csv builder;
- annotation_artifact_uri, annotation_revision_hash, annotation_schema_version;
- training_image_uri, training_image_sha256, derivative_preprocessing_version;
- human_grading_protocol;
- explicit `SYSTEM AUTO LABEL != HUMAN GROUND TRUTH` semantics;
- explicit HUMAN, PSEUDO_LABEL, WEAK_LABEL, and UNREVIEWED_SYSTEM eligibility;
- export verification and idempotent retry.

Exit criteria:

- REFERENCE_ONLY is the default for large DICOM workflows;
- original DICOM is never overwritten or annotated;
- COPY_ORIGINAL behavior is explicit and policy-gated;
- export failure does not lose review state or revert HUMAN_REVIEWED;
- ROI rows locate an exact annotation revision, not only a count;
- unreviewed system rows cannot enter a training-eligible selection;
- all exported artifact hashes verify before EXPORTED.

### Phase 5 - Summary, recovery, and workflow polish

**Customer value:** Helps users understand throughput and recover from ordinary failures.

Deliver:

- source-folder and System Grade summary;
- separate Human Reviewed Grade summary;
- review, AI, export, quarantine, and ingestion counts;
- retryable ingestion/model/export errors;
- idempotent jobs and recovery receipts;
- saved filters and clear empty/error/loading states;
- derived composite Queue badges that explain the underlying failure dimension.

Exit criteria:

- summary labels its grade dimension unambiguously;
- partial failures are visible at case and item level;
- AI/export retries do not duplicate revisions or artifacts;
- successful review stays durable through export failure;
- Queue badges never hide a failed operational dimension.

### Phase 6 - Optional Google Drive adapters

**Customer value:** Supports governed remote file workflows without changing local authority.

Deliver:

- Google Drive folder source adapter;
- Google Drive output adapter;
- provider authorization/read/write readiness states;
- resumable transfer and checksum verification;
- provider IDs/URLs in receipts;
- no browser-held credentials or policy-forbidden raw-data upload.

Exit criteria:

- Drive can be disabled without affecting local workflows;
- unauthorized/revoked access is visible and recoverable;
- the same output policy and artifact contract works for local and Drive destinations;
- local/on-prem remains authoritative.

### Phase 7 - Optional Label Studio CE / CVAT adapters

**Customer value:** Adds specialist review capacity without coupling the customer UI to a vendor.

Deliver:

- Label Studio CE suggestion/confirm/correct/reject/escalate adapter;
- provenance sidecar and annotation-revision mapping;
- optional CVAT advanced geometry adapter;
- import/export conflict detection and idempotent synchronization.

Exit criteria:

- external task systems cannot overwrite system predictions;
- imported decisions retain source task, model, reviewer, and geometry provenance;
- core product review works with both adapters disabled;
- Label Studio CE remains internal HITL infrastructure.

### Phase 8 - Real versioned model bundles

**Customer value:** Replaces the mock adapter with locally deployable encoder + head bundles after explicit approval.

Deliver:

- local model registry and runtime loading;
- architecture-agnostic encoder/head/preprocessing/calibration manifest validation;
- model health, compatibility, and input constraints;
- explicit model selection and audit record;
- prediction latency/error state handling;
- deployment/license status separate from research evidence.

Exit criteria:

- UI remains independent of a concrete encoder architecture;
- every prediction records complete bundle identity;
- local deployment has a reproducible rollback target;
- no model is presented as a diagnosis or clinical decision;
- this phase does not claim scientific validation by itself.

### Phase 9+ - Product Model Factory

**Customer value:** Lets a hospital progressively create and maintain a hospital-specific encoder + head model from
clinician-reviewed supervision.

The future loop is:

~~~
Reviewed Dataset
    -> Dataset Snapshot
    -> patient/identity-safe split
    -> SSL / encoder adaptation
    -> lightweight task-specific head training
    -> validation
    -> calibration
    -> versioned encoder + head bundle
    -> local deployment
    -> Review Workspace
    -> iterative relabel / retrain loop
~~~

Planned subphases:

- **9A - Dataset snapshots:** freeze a reproducible reviewed selection, identity-safe split policy, source/hash
  coverage, annotation revision references, and eligibility policy;
- **9B - SSL / encoder adaptation:** future local or approved execution path for unlabeled hospital images, with
  explicit data boundary and lineage;
- **9C - Supervised task head:** train a lightweight task-specific head from explicitly eligible human/policy-approved
  rows while retaining system-vs-human semantics;
- **9D - Validation and calibration:** record validation, calibration, uncertainty, and error-analysis artifacts before
  deployment decisions;
- **9E - Registry and local deployment:** register versioned encoder + head + preprocessing + calibration bundles with
  rollback and deployment audit;
- **9F - Iterative loop:** route reviewed corrections back into a new snapshot and retraining decision without silently
  modifying a prior dataset or bundle.

Exit criteria for each subphase require explicit governance, lineage, identity-safe splits, reproducible artifacts,
privacy review, and owner approval. These phases are planned only; they are not implemented or scientifically
validated by this product POC.

## 3. First working POC acceptance criteria

The first POC is complete when synthetic or explicitly authorized local fixtures demonstrate:

- local input and output selection through a supported filesystem bridge;
- one DICOM fixture and one supported raster fixture ingested without source-byte modification;
- DICOM SHA-256, safe technical metadata, display derivative, and derivation provenance;
- malformed/unsupported DICOM quarantine;
- independent review, AI, and export statuses plus derived Queue badges;
- explicit deterministic mock Run AI with immutable prediction;
- separate system prediction and human grade;
- all five annotation geometries and system/user provenance;
- independent 1/2/4/8 review layouts;
- Save & Return persistence before export;
- export failure retaining HUMAN_REVIEWED and remaining retryable;
- deterministic output artifacts and optional annotated preview;
- manifest.csv/index.csv with exact annotation and training-image references;
- HUMAN, PSEUDO_LABEL, WEAK_LABEL, and UNREVIEWED_SYSTEM eligibility;
- UNREVIEWED_SYSTEM excluded from training selection;
- offline tests with no Pod, training run, external experiment, or R1 state change.

## 4. Test and verification backlog

- unit-test filesystem bridges, source adapters, hashing, deduplication, and quarantine;
- contract-test DICOM discovery, technical metadata, frame/orientation/windowing provenance, and byte preservation;
- repository tests for optimistic concurrency and immutable revision keys;
- ModelAdapter tests for explicit invocation, manifest identity, deterministic mock output, unavailable-model failure,
  and independent ai_status;
- annotation tests for all geometry types, normalized coordinates, correction/rejection provenance, and
  multi-image independence;
- export tests for all output policies, deterministic paths, receipts, hash verification, retry, and no-DICOM-copy
  default;
- manifest tests for eligibility, annotation revision references, training image hashes, and fail-closed ambiguity;
- browser tests for source setup, Queue states, explicit Run AI, review save, export failure, recovery, and responsive
  layouts;
- accessibility checks for keyboard navigation, focus, labels, contrast, reduced motion, and icon semantics.

## 5. Explicitly deferred

- implementation of SSL, fine-tuning, supervised head training, validation, calibration, registry, and deployment;
- Pods, GPU execution, and external experiments;
- R1 split-leakage resolution and any change to current scientific conclusions;
- clinical deployment certification, diagnosis/referral/treatment claims, HL7/FHIR, and production IAM;
- automatic conversion of system predictions into human or training ground truth.
