# OcuForge Product Architecture

**Status:** Product-track planning specification
**Primary boundary:** Local/on-prem authoritative system with optional source/output adapters
**Scope:** Ingestion, review, provenance, export, and future model-factory integration; no production implementation here

## 1. Architectural intent

OcuForge is an on-prem retinal model factory and clinician review system. It starts with mostly unlabeled hospital
retinal images, commonly DICOM, and supports this future product loop:

```text
unlabeled hospital images
    -> local QC / ingestion
    -> clinician-reviewed supervision
    -> reviewed dataset snapshot
    -> patient/identity-safe split
    -> future SSL / encoder adaptation
    -> lightweight task-specific head training
    -> validation
    -> calibration
    -> versioned encoder + head bundle
    -> local deployment
    -> Review Workspace
    -> iterative relabel / retrain loop
```

The product track can progress while research is blocked. Product planning, synthetic fixtures, contracts, and the
deterministic mock adapter do not claim scientific validity or authorize training.

## 2. Ownership and dependency direction

```text
UI / desktop or browser shell
    -> Product application services
        -> LocalFileSystemBridge / LocalPathAdapter
        -> SourceAdapter / DestinationAdapter
        -> ImageIngestionService / DICOMAdapter / RasterAdapter
        -> CaseRepository / AnnotationRepository / ManifestBuilder
        -> ModelAdapter
        -> ExportAdapter
        -> versioned CONTRACTS objects

Product Model Factory services (future)
    -> DatasetSnapshotService
    -> SplitPolicyService
    -> EncoderAdaptationService
    -> HeadTrainingService
    -> ValidationService / CalibrationService
    -> ModelRegistry / LocalDeploymentService

ModelAdapter -> versioned model bundle interface only
Label Studio CE / CVAT -> optional review/integration adapters
```

The product layer may depend on `eyes-detected-contracts`. Models and labeler must not depend on each other’s
implementation. Local/private data and all private derived artifacts remain on-premise.

### Module mapping

| Product responsibility | Repository module | Boundary |
|---|---|---|
| Shared schemas, protocol, provenance | `CONTRACTS` | versioned contracts first |
| Local metadata, immutable objects, revisions | `DATA` | local/on-prem authority |
| Model adapters, future factory execution | `MODELS` | consumes contracts; no labeler import |
| Review and annotation integrations | `LABELER` | consumes contracts; no model import |
| Local runtime and deployment | `RUNTIME` | executes services; does not redefine semantics |
| Research claims and evidence | `RESEARCH` | separate from product readiness |

## 3. Runtime and filesystem boundary

An ordinary browser does not have unrestricted local path access. The UI must depend on a clean local runtime
abstraction rather than a browser-specific filesystem API.

### `LocalFileSystemBridge` / `LocalPathAdapter`

```text
capabilities() -> LocalFileSystemCapabilities
pick_input_folder(request) -> LocalFolderReference
pick_output_folder(request) -> LocalFolderReference
enumerate(folder_ref, scan_options) -> iterator[LocalSourceItem]
read(item_ref) -> SourceObjectStream
write(destination_ref, artifact) -> LocalWriteReceipt
```

Valid implementations may be:

- an on-prem backend path picker;
- a desktop/native shell bridge;
- a browser File System Access API adapter where supported.

The product UI receives a provider-neutral reference and readiness state. It does not assume a Windows path is readable
by the browser, and it does not expose local credentials or private paths to public telemetry.

## 4. Core interfaces

These are planning interfaces. Names and payloads become versioned contracts before implementation.

### `SourceAdapter`

```text
validate(source_ref) -> SourceReadiness
enumerate(source_ref, scan_options) -> iterator[SourceItem]
read(item_ref) -> SourceObjectStream
source_identity(source_ref) -> SourceIdentity
```

Responsibilities:

- support local folders through `LocalFileSystemBridge`;
- support optional Google Drive folder URLs through a governed adapter;
- return stable provider/source/folder/item references;
- distinguish reachable, authorized, unsupported, and failed items;
- never expose provider credentials to the browser;
- preserve the original source reference and provider item ID when available.

### `DestinationAdapter`

```text
validate(destination_ref) -> DestinationReadiness
resolve(destination_ref) -> DestinationIdentity
```

The output destination is local first, with optional Google Drive support behind the same provider-neutral seam.

### `ImageIngestionService`

```text
ingest(source_ref, destination_policy, actor) -> IngestionJob
resume(job_id, actor) -> IngestionJob
get_status(job_id) -> IngestionStatus
quarantine(item_ref, reason, actor) -> QuarantineRecord
retry_item(item_ref, idempotency_key, actor) -> IngestionItemResult
```

Responsibilities:

- enumerate through `SourceAdapter`;
- classify DICOM before raster fallbacks;
- route DICOM to `DICOMAdapter` and raster to an explicit `RasterAdapter`;
- hash source bytes before persistence;
- deduplicate by content hash without silently merging source occurrences or metadata;
- persist immutable source objects locally;
- create image/case records and Queue materialization;
- record accepted, duplicate, unsupported, malformed, quarantined, and failed item results;
- never annotate or overwrite original source bytes.

### `DICOMAdapter`

```text
inspect(source_object) -> DicomTechnicalMetadata
extract_pixels(source_object, display_policy) -> DisplayDerivative
derive_display(source_object, frame_policy, orientation_policy, window_policy) -> DisplayDerivative
source_reference(source_object) -> ImmutableSourceReference
quarantine_reason(source_object) -> optional[DicomError]
```

DICOM is a Phase-1/core ingestion capability, not a late integration. The adapter must:

- discover DICOM objects and common multi-frame objects;
- preserve original DICOM bytes and SHA-256 in local authoritative storage before conversion;
- extract approved technical metadata and explicit DICOM identifiers;
- preserve `study_instance_uid`, `series_instance_uid`, `sop_instance_uid`, `frame_number`, and
  `transfer_syntax_uid` where applicable in the local-governed identity record;
- keep patient-identifying metadata local and out of browser logs, public manifests, cloud adapters, Git, and telemetry;
- generate a display derivative linked to the original object;
- record transfer syntax, frame number, orientation, color conversion, windowing, and preprocessing provenance where
  applicable;
- support Queue creation for accepted objects;
- quarantine malformed or unsupported objects with a stable reason and retry/review path;
- never write annotations into original DICOM.

The adapter does not claim diagnostic correctness. Windowing, orientation, and display transformations are derivative
operations with provenance, not changes to the source object.

### `RasterAdapter`

```text
inspect(source_object) -> RasterTechnicalMetadata
derive_display(source_object, display_policy) -> DisplayDerivative
source_reference(source_object) -> ImmutableSourceReference
```

JPEG, PNG, TIFF, and other explicitly supported raster formats remain supported adapters. They are not the primary
hospital-input assumption and must use the same hashing, identity, provenance, Queue, and export contracts.

### `CaseRepository`

```text
create_case(case_record) -> Case
get_case(case_id) -> Case
query_queue(filters, page) -> QueuePage
save_case(case_id, expected_version, update) -> Case
record_operational_transition(case_id, dimension, transition) -> AuditEvent
```

Use optimistic concurrency. Queue materialization may be denormalized for fast reads, but source, prediction,
annotation, review, export, and audit records remain independently addressable.

### `ModelAdapter`

```text
list_models(scope) -> list[ModelBundleSummary]
get_model_manifest(model_manifest_id) -> ModelBundleManifest
run(image_ref, model_manifest_id, options, idempotency_key) -> SystemPrediction
health(model_manifest_id) -> AdapterHealth
```

The UI and product services must not import or name a concrete encoder architecture. A versioned bundle contains:

- encoder identity and version;
- task-specific head identity and version;
- preprocessing identity/config hash;
- calibration identity/version and calibration artifact hash;
- model manifest ID and bundle version;
- weight/checkpoint or package hash;
- supported modality and input constraints;
- output schema and grading protocol references;
- runtime requirements and deployment/license status;
- intended use, known limitations, and provenance.

`run` is explicit and idempotent for the same image hash, model manifest, preprocessing version, options, and
idempotency key. Every attempt is recorded; a new successful prediction never deletes a prior immutable prediction.

### `AnnotationRepository`

```text
save_revision(annotation_revision) -> AnnotationRevision
get_history(annotation_id) -> list[AnnotationRevision]
save_review(review, expected_version) -> Review
append_audit(event) -> AuditEvent
```

Use contracts geometry/provenance concepts and the labeler lifecycle pattern. Human correction is a new revision linked
to the system object; it never mutates the system prediction.

### `ExportAdapter`

```text
validate(destination_ref) -> DestinationReadiness
write(export_plan, idempotency_key) -> ExportReceipt
retry(export_job_id, idempotency_key) -> ExportReceipt
```

Support these policies:

```text
REFERENCE_ONLY
COPY_ORIGINAL
DERIVED_IMAGE_ONLY
COPY_ORIGINAL_AND_DERIVED
```

`REFERENCE_ONLY` is the default for large DICOM workflows. Every write is idempotent or content-addressed, records
policy and provider/local references, and verifies checksums before reporting `EXPORTED`. Annotated previews are
derived artifacts and never replace or modify the original DICOM.

### `ManifestBuilder`

```text
build(selection, manifest_version) -> ManifestSnapshot
write(snapshot, destination_ref, idempotency_key) -> ExportReceipt
```

Build from persisted case, review, prediction, annotation-revision, derivative, and export state. Fail closed or mark
an explicit row error when provenance is ambiguous. Never promote an unreviewed system prediction to a human training
label.

The builder's row contract includes exact `annotation_artifact_uri`, `annotation_revision_hash`,
`annotation_schema_version`, `training_image_uri`, `training_image_sha256`, `derivative_preprocessing_version`, and
`human_grading_protocol`, plus independent operational statuses and explicit
training eligibility (`HUMAN`, `PSEUDO_LABEL`, `WEAK_LABEL`, or `UNREVIEWED_SYSTEM`). An annotation count alone is
insufficient for ROI training. `SYSTEM AUTO LABEL != HUMAN GROUND TRUTH` remains a product invariant.

## 5. Independent operational state dimensions

The canonical operational fields are:

```text
review_status: NOT_STARTED | IN_REVIEW | HUMAN_REVIEWED
ai_status: NOT_RUN | RUNNING | PROCESSED | FAILED
export_status: NOT_EXPORTED | EXPORTING | EXPORTED | FAILED
```

The Queue badge is a derived view, for example:

```text
NOT_STARTED + NOT_RUN + NOT_EXPORTED -> NOT_PROCESSED
IN_REVIEW + NOT_RUN + NOT_EXPORTED -> IN_REVIEW
HUMAN_REVIEWED + PROCESSED + NOT_EXPORTED -> HUMAN_REVIEWED
HUMAN_REVIEWED + PROCESSED + FAILED -> HUMAN_REVIEWED / EXPORT_FAILED
* + FAILED + * -> AI_FAILED (review state preserved)
* + * + EXPORTED -> EXPORTED
```

The derived badge is never the source of truth. AI and export failure cannot revert or destroy durable review state.
Retries are scoped, explicit, idempotent operations.

## 6. Runtime and data boundary

Local/on-prem is authoritative for:

- original DICOM and raster source objects;
- DICOM identifiers and patient/visit/eye linkage;
- display derivatives and preprocessing metadata;
- predictions, annotations, reviews, manifests, and audit events;
- dataset snapshots, split decisions, embeddings, checkpoints, and model bundles.

Google Drive is an optional source/output adapter only when local governance permits. It is not the clinical authority
or default backup. Browser clients hold no provider secrets. Public GPU, Vercel, GitHub, and other external systems
must not receive hospital/private data or derived artifacts.

## 7. Request flows

### 7.1 Ingestion

```text
User selects source/destination through adapters
    -> validate readiness and output policy
    -> ingestion enumerates items
    -> classify DICOM/raster
    -> hash and persist immutable source bytes locally
    -> extract safe technical metadata
    -> create display derivative with derivation provenance
    -> create image/case + NOT_STARTED / NOT_RUN / NOT_EXPORTED
    -> quarantine malformed/unsupported items
```

### 7.2 Review and export

```text
User opens case -> review_status=IN_REVIEW
    -> explicit Run AI -> ai_status=RUNNING -> PROCESSED or FAILED
    -> user creates human grade/annotations/remark
    -> persist immutable revisions and audit events
    -> review_status=HUMAN_REVIEWED
    -> ExportAdapter writes selected artifacts
    -> export_status=EXPORTING -> EXPORTED or FAILED
    -> ManifestBuilder updates manifest/index references
```

Persistence precedes export. Export failure never changes `HUMAN_REVIEWED` back to an error queue state.

### 7.3 Future Product Model Factory

```text
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
```

This is a future product capability. The planning documents do not claim that training, calibration, registry, or
deployment is implemented or scientifically validated.

## 8. Reuse map

| Existing capability | Product reuse |
|---|---|
| `templates/` | information architecture, review layout, queue patterns, safety language |
| `templates/integration/adapter.js` | reference adapter seam; expand for sources, queue, review, exports, manifests |
| `ImageManifest`, `Prediction`, `Annotation`, `ModelManifest` | existing identity, geometry, protocol, model, provenance semantics |
| `MongoStore` | local-only Mongo guard, optimistic updates, immutable revisions, document hashes |
| `LocalImageStore` | content-addressed local object storage pattern; extend through DICOM adapter |
| `provenance.lifecycle` | immutable transitions, correction, rejection, adjudication, and lock semantics |
| Label Studio bridge | optional internal HITL integration; not customer-facing core editor |
| CVAT bridge | optional advanced geometry adapter |

## 9. Failure and recovery policy

- source unreachable: do not promote ingestion; show retryable readiness failure;
- local path capability unavailable: show adapter setup state, never claim a path was scanned;
- source item unreadable: record item-level failure with stable reference and reason;
- hash mismatch or source mutation: reject persistence and retain audit evidence;
- duplicate hash: reuse immutable object and retain source occurrences separately;
- malformed/unsupported DICOM: quarantine, do not silently rasterize;
- model unavailable: set `ai_status=FAILED` for an attempted run, preserve all review state, and never fabricate a label;
- concurrent review update: reject stale version, reload latest, and require explicit merge/retry;
- export failure: set `export_status=FAILED`, preserve review state, and retry with the same idempotency key;
- manifest ambiguity: fail closed for training eligibility and report affected rows;
- factory job failure: preserve the dataset snapshot and prior registered bundle; never partially promote a new bundle.

## 10. Non-goals for this planning increment

- no product training or self-supervised learning execution;
- no Pod or external experiment;
- no selection of a research encoder champion;
- no R1 blocker resolution or change to scientific conclusions;
- no production authentication, clinical certification, HL7/FHIR, or diagnostic claim;
- no requirement that Label Studio or CVAT run for the first customer-facing POC.
