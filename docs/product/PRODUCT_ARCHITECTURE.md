# OcuForge Product Architecture

**Status:** Product-track planning specification
**Primary boundary:** Local/on-prem authoritative system with optional source/output adapters
**Scope:** Ingestion, review, provenance, export, and model-bundle integration; no production implementation here

## 1. Architectural intent

OcuForge is an on-prem retinal model factory and clinician review system. The architecture must support the path:

```text
unlabeled hospital images
    -> QC / ingestion
    -> future encoder adaptation / SSL
    -> clinician labeling subset
    -> lightweight task-specific head
    -> validation / calibration
    -> versioned encoder + head bundle
    -> local inference and review
```

The product path is independent of research execution. Product interfaces may be built and tested with synthetic
fixtures and a deterministic mock adapter while R1 remains blocked.

## 2. Ownership and dependency direction

```text
Browser/UI
    -> Product application services
        -> SourceAdapter / ExportAdapter / DICOMAdapter
        -> CaseRepository / AnnotationRepository / ManifestBuilder
        -> ModelAdapter
        -> versioned CONTRACTS objects

ModelAdapter -> model bundle interface only
Label Studio/CVAT -> optional review/integration adapters
```

The product layer may depend on `eyes-detected-contracts`. Models and labeler must not depend on each other’s
implementation. Local/private data and all private derived artifacts remain on-premise.

## 3. Core interfaces

These are planning interfaces. Names and payloads should become versioned contracts before implementation.

### `SourceAdapter`

```text
validate(source_ref) -> SourceReadiness
enumerate(source_ref, scan_options) -> iterator[SourceItem]
read(item_ref) -> SourceObjectStream
source_identity(source_ref) -> SourceIdentity
```

Responsibilities:

- support local folder and optional Google Drive folder URL adapters;
- return stable provider/source/folder references;
- never expose provider credentials to the browser;
- distinguish reachable, authorized, unsupported, and failed items;
- preserve the original source reference and provider item ID when available.

### `ImageIngestionService`

```text
ingest(source_ref, destination_policy, actor) -> IngestionJob
resume(job_id, actor) -> IngestionJob
get_status(job_id) -> IngestionStatus
```

Responsibilities:

- enumerate through `SourceAdapter`;
- classify file type and route DICOM through `DICOMAdapter`;
- hash source bytes before persistence;
- deduplicate by content hash without silently merging unrelated metadata;
- persist immutable objects through local storage;
- create image/case records and queue state;
- record accepted, duplicate, unsupported, and failed item results;
- never annotate or overwrite original source bytes.

### `DICOMAdapter`

```text
inspect(source_object) -> DicomTechnicalMetadata
extract_pixels(source_object, display_policy) -> DisplayDerivative
source_reference(source_object) -> ImmutableSourceReference
```

Responsibilities:

- treat DICOM as a first-class input, not a renamed raster file;
- preserve original DICOM bytes and SHA-256 in local authoritative storage;
- extract only metadata approved by the local privacy policy;
- keep patient-identifying metadata local and out of browser logs, manifests, and cloud adapters;
- provide a display derivative with a provenance link to the original object;
- keep any windowing, color conversion, orientation normalization, or frame selection explicit;
- reject or quarantine malformed/unsupported objects with a visible error;
- never write annotations into original DICOM.

Annotated previews are separate derived artifacts. They are never replacements for the original clinical source.

### `CaseRepository`

```text
create_case(case_record) -> Case
get_case(case_id) -> Case
query_queue(filters, page) -> QueuePage
save_case(case_id, expected_version, update) -> Case
record_queue_transition(case_id, transition) -> AuditEvent
```

Use the existing local Mongo optimistic version pattern. Queue materialization may be denormalized for fast UI
queries, but immutable source, prediction, annotation, and audit records remain independently addressable.

### `ModelAdapter`

```text
list_models(scope) -> list[ModelBundleSummary]
get_model_manifest(model_manifest_id) -> ModelBundleManifest
run(image_ref, model_manifest_id, options) -> SystemPrediction
health(model_manifest_id) -> AdapterHealth
```

The UI and product services must not import or name a concrete encoder architecture. A model bundle contains:

- encoder identity and version;
- task-specific head identity and version;
- preprocessing identity/config hash;
- calibration identity/version and calibration artifact hash;
- model manifest ID and bundle version;
- weight/checkpoint or package hash;
- supported modality and input constraints;
- output schema/protocol references;
- runtime requirements and license/deployment status;
- known limitations and intended use.

`run` is explicit and idempotent for the same image hash, model manifest, preprocessing version, and options. A new
run may create a new prediction ID while retaining the prior immutable prediction.

### `AnnotationRepository`

```text
save_revision(annotation_revision) -> AnnotationRevision
get_history(annotation_id) -> list[AnnotationRevision]
save_review(review, expected_version) -> Review
append_audit(event) -> AuditEvent
```

Reuse the contracts package geometry/provenance concepts and the labeler lifecycle pattern. Never mutate a system
prediction to represent a human correction. Save a new human revision linked to its parent prediction/object.

### `ExportAdapter`

```text
validate(destination_ref) -> DestinationReadiness
write(export_plan) -> ExportReceipt
retry(export_job_id) -> ExportReceipt
```

Implement local output first. Google Drive is optional and must be a provider adapter behind the same interface. Every
write is content-addressed or idempotent, records provider/local references, and verifies checksums before reporting
`EXPORTED`.

### `ManifestBuilder`

```text
build(selection, manifest_version) -> ManifestSnapshot
write(snapshot, destination_ref) -> ExportReceipt
```

Build from persisted case/review/prediction/annotation state, not directly from UI memory. Reject or flag ambiguous
provenance. Never promote an unreviewed system prediction to a human training label.

## 4. Runtime and data boundary

Local/on-prem is authoritative for:

- original DICOM and raster source objects;
- pixel/display derivatives;
- patient/visit/eye linkage;
- predictions, annotations, review history, and audit events;
- manifests, exports, embeddings, checkpoints, and model bundles.

Google Drive may be configured as an optional source/output adapter only when local governance permits it. The product
must not assume Drive is a clinical authority or a backup. Browser clients hold no provider secrets. Public GPU,
Vercel, GitHub, and other external systems must not receive hospital/private data or derived artifacts.

## 5. Request flow

```text
User selects source/destination
    -> validate adapters and policy
    -> ingestion job enumerates items
    -> hash + classify + persist immutable source
    -> create image/case + NOT_PROCESSED queue state
    -> user opens review
    -> explicit Run AI
    -> ModelAdapter returns immutable system prediction
    -> user creates human grade/annotations/remark
    -> AnnotationRepository persists revision + audit history
    -> CaseRepository materializes HUMAN_REVIEWED
    -> ExportAdapter writes selected artifacts
    -> verify output hashes
    -> queue becomes EXPORTED
    -> ManifestBuilder updates manifest/index
```

Persistence precedes export. If export fails, review state remains durable and the export job is retryable.

## 6. Reuse map

| Existing capability | Product reuse |
|---|---|
| `templates/` | Information architecture, review layout, safety language, mock/live adapter idea, Lucide-compatible icon direction |
| `templates/integration/adapter.js` | Browser adapter seam; expand for sources, queue, review, export, and manifests |
| `ImageManifest`, `Prediction`, `Annotation`, `ModelManifest` | Existing identity, geometry, model, protocol, and provenance semantics |
| `MongoStore` | Local-only Mongo endpoint guard, optimistic document updates, immutable revision collection, document hashes |
| `LocalImageStore` | Content-addressed local object storage pattern; extend through a DICOM-specific adapter |
| `provenance.lifecycle` | Immutable transitions, event history, correction, rejection, adjudication, and lock semantics |
| Label Studio bridge | Optional internal HITL integration; not the customer-facing core editor |
| CVAT bridge | Optional advanced annotation adapter |

## 7. Failure and recovery policy

- Source unreachable: no ingestion state is promoted; show retryable readiness failure.
- Source item unreadable: create an item-level `ERROR` record with source reference and reason.
- Hash mismatch or source mutation: reject persistence and retain the failure audit event.
- Duplicate hash: reuse the immutable object; keep source occurrence references separate.
- DICOM unsupported or malformed: quarantine the item; do not silently rasterize.
- Model unavailable: preserve `NOT_PROCESSED` or transition to `ERROR` according to whether the run was attempted;
  never create a fake system label.
- Concurrent review update: reject stale version, reload latest, and require explicit merge/retry.
- Export failure: preserve database review state and retry with the same idempotency key.
- Manifest ambiguity: fail closed for training eligibility and report the affected rows.

## 8. Non-goals for this product planning increment

- no training or self-supervised learning execution;
- no Pod or external experiment;
- no selection of a research encoder champion;
- no R1 blocker resolution;
- no production authentication, clinical integration, or diagnostic claim;
- no requirement that Label Studio or CVAT be running for the first POC.
