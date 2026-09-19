# OcuForge Product Data Model

**Status:** Product-track planning specification
**Storage direction:** Local/on-prem NoSQL plus immutable local object storage
**Scope:** Product workflow state, provenance, review, export, and manifest eligibility

## 1. Modeling rules

The data model keeps five things separate:

1. original source objects;
2. system predictions;
3. user annotations and human grades;
4. operational materialized queue/review state;
5. downstream training eligibility.

The current `eyes-detected-contracts` identity, geometry, prediction, annotation, protocol, and model-manifest
semantics remain authoritative. Product-specific documents should be additive and versioned. Mongo documents may be
denormalized for reads, but immutable facts must not be overwritten.

All documents use a schema version, stable ID, created/updated timestamps, and an integrity hash where the document
is immutable or exported. Private documents and artifacts are local-only.

## 2. Collections and documents

### `sources`

```text
source_id
schema_version
provider_type: LOCAL_FOLDER | GOOGLE_DRIVE_FOLDER
source_reference
provider_item_id
display_name
folder_path_or_name
authorization_state
scan_options
source_policy
created_at
updated_at
```

`source_reference` may be a local path or provider URL/reference. The browser should not persist provider tokens.
`authorization_state` distinguishes `NOT_CHECKED`, `READY`, `UNAUTHORIZED`, `UNREACHABLE`, and `ERROR`.

### `destinations`

```text
destination_id
schema_version
provider_type: LOCAL_FOLDER | GOOGLE_DRIVE_FOLDER
destination_reference
provider_item_id
display_name
write_policy
authorization_state
created_at
updated_at
```

Destination references are configuration, not proof that an export succeeded. Export receipts provide that proof.

### `ingestion_jobs`

```text
job_id
schema_version
source_id
destination_id: optional
actor_id_hash
status: CREATED | SCANNING | PERSISTING | COMPLETED | COMPLETED_WITH_ERRORS | FAILED
counts: { discovered, accepted, duplicates, unsupported, failed, persisted }
scan_options
item_results_reference
started_at
completed_at
error_summary
```

Item results contain stable source references, file type, byte size, file hash when available, outcome, and error
code. Large result lists belong in separate documents or local files, not one unbounded document.

### `images`

```text
image_id
schema_version
case_id
source_id
source_item_reference
source_relative_path
original_file_name
file_sha256
byte_size
file_type: DICOM | JPEG | PNG | TIFF | OTHER
immutable_object_uri
modality
laterality
width_px
height_px
patient_pseudo_id: optional/local-only
study_id: optional/local-only
series_id: optional/local-only
eye_id: optional
visit_id: optional
acquisition_time_bucket: optional
dicom_metadata_reference: optional
display_derivative_reference: optional
ingested_at
```

The original object hash is the identity anchor. A duplicate source occurrence may refer to the same immutable
object while retaining its own source provenance.

### `cases`

```text
case_id
schema_version
source_folder_id
image_ids
queue_status
qc_status
system_dr_grade: optional
system_prediction_id: optional
human_reviewed_dr_grade: optional
human_review_id: optional
review_status
export_status
training_eligibility_summary
version
created_at
updated_at
```

`version` supports optimistic concurrency. `queue_status` is the materialized UI state; immutable events remain the
source for how it was reached.

### `predictions`

Each AI execution creates an immutable prediction document compatible with the existing `Prediction` contract.

```text
prediction_id
schema_version: prediction.v0.1 or newer additive version
image_id
file_sha256_at_run
model_manifest_id
model_bundle_version
preprocessing_version
calibration_version: optional
dr: { grading_protocol, grade, ordinal_probs, confidence }
lesion_presence
objects
evidence
ood
gradability_probability
origin: SYSTEM
created_at
run_parameters_hash
```

The existing contract uses `AI_SUGGESTED` for prediction candidates and retains a model manifest ID. Product storage
may expose a UI-level `SYSTEM` label while preserving the contract’s `AI_SUGGESTED` origin in the annotation object.

System predictions remain available after correction, rejection, replacement, or a later model run.

### `annotation_revisions`

Each revision is immutable and keyed by annotation ID plus revision hash, following the existing `MongoStore`
pattern.

```text
annotation_id
revision_hash
schema_version: annotation.v0.1 or newer additive version
image_id
label
geometry
coordinate_space: normalized_0_1
display_fill: optional { enabled, opacity, color_token }
origin: AI_SUGGESTED | CLINICIAN_CONFIRMED | CLINICIAN_CORRECTED | CLINICIAN_ADDED | EXPERT_ADJUDICATED
parent_prediction_id: optional
parent_object_id: optional
source_model_version: optional
annotator_id_hash
review_status
clinician_certainty
uncertain
grading_protocol: optional
dr_grade: optional
gradability
laterality
created_at
updated_at
history[]
```

Supported product geometry is point, box/rectangle, ellipse/circle, polygon, and area-fill presentation. The existing
contract uses normalized geometry and supports `point`, `box`, `ellipse`, `polygon`, and `mask`; a circle is stored as
an ellipse with equal extents unless a future contract adds a distinct shape.

An edited system annotation creates a new clinician revision with parent IDs. The original system annotation is never
overwritten.

### `reviews`

The review is a materialized user-facing document referencing immutable facts:

```text
review_id
schema_version
case_id
image_id
active_system_prediction_id: optional
active_human_annotation_revision_ids
system_dr_grade: optional
human_reviewed_dr_grade: optional
human_review_status: NOT_STARTED | DRAFT | SUBMITTED | ADJUDICATED | LOCKED
remark: optional
reviewer_id_hash
reviewer_certainty
last_saved_revision_hash
version
created_at
updated_at
```

System grade and human grade are never represented by one overloaded `grade` field.

### `export_jobs`

```text
export_job_id
schema_version
destination_id
case_ids
manifest_snapshot_id: optional
artifact_selection
idempotency_key
status: CREATED | WRITING | VERIFIED | FAILED | PARTIAL
artifact_receipts[]
error_code: optional
created_at
completed_at
```

An artifact receipt records logical path, provider/local reference, byte size, SHA-256, and verification time.

### `manifest_snapshots`

```text
manifest_snapshot_id
schema_version
manifest_version
selection_query_hash
row_count
eligibility_counts
source_hash_coverage
manifest_csv_reference
index_csv_reference
generation_hash
created_at
```

Manifest generation is reproducible from persisted records and a selection query hash.

### `audit_events`

```text
event_id
schema_version
aggregate_type
aggregate_id
action
actor_type: SYSTEM | USER | SERVICE
actor_id_hash
prior_state
next_state
reason
related_prediction_id: optional
related_annotation_id: optional
timestamp
```

Audit events are append-only. They must not include raw image bytes, credentials, or unnecessary patient-identifying
fields.

## 3. Annotation provenance and training eligibility

### Provenance rules

- `SYSTEM AUTO LABEL` is not `HUMAN GROUND TRUTH`.
- System prediction objects are immutable and retain model manifest, preprocessing, calibration, image hash, and
  creation metadata.
- Human confirmation/correction/rejection is a new revision/event linked to the original system object.
- User-created annotations start as explicit drafts and acquire human eligibility only after the configured review
  action is complete.
- Expert adjudication and lock remain separate from ordinary user submission where the deployment requires them.
- Unannotated regions are not silently converted to negative labels.
- Human grade remains distinct from system grade and carries its grading protocol.

### Training eligibility

Every manifest row has exactly one explicit eligibility value:

```text
HUMAN
PSEUDO_LABEL
WEAK_LABEL
UNREVIEWED_SYSTEM
```

`UNREVIEWED_SYSTEM` is the default for system-only output and is never included in a training-eligible selection.
`PSEUDO_LABEL` and `WEAK_LABEL` require explicit policy, source, confidence/quality metadata, and a downstream
selection that opts in. No UI save operation may silently promote either to `HUMAN`.

## 4. Queue state transitions

```text
NOT_PROCESSED --explicit Run AI success--> AI_PROCESSED
NOT_PROCESSED --ingestion/QC/model error--> ERROR
AI_PROCESSED --review materialized--> IN_REVIEW
AI_PROCESSED --valid human save--> HUMAN_REVIEWED
IN_REVIEW --valid human save--> HUMAN_REVIEWED
IN_REVIEW --persistence/export failure--> ERROR
HUMAN_REVIEWED --verified export--> EXPORTED
EXPORTED --new correction--> IN_REVIEW
ERROR --explicit retry--> prior state or NOT_PROCESSED
```

Every transition records actor/system origin, timestamp, reason, and prior/next state. `ERROR` must retain enough
context to retry without losing previous successful work.

## 5. DICOM boundary

- Accept DICOM as a first-class file type.
- Hash and persist original bytes before any display conversion.
- Keep original DICOM and derived display/preview objects separate.
- Extract only approved technical metadata into normal query documents.
- Keep patient-identifying values local and out of Google Drive, browser logs, public manifests, and reports.
- Record transfer syntax, frame selection, orientation/windowing, and display conversion as derivation metadata when
  relevant.
- Never draw annotations into or overwrite the original DICOM.
- Optional annotated previews reference the original DICOM hash and derivative hash.
- Unsupported DICOM objects become visible errors, not silently substituted raster files.

## 6. Export artifact contract

Default export avoids duplicating large source files. It writes references and hashes instead:

```text
<output-root>/<source-folder-id>/<case-id>/
  export_manifest.json
  image_metadata.json
  source_reference.json
  system_predictions.json
  annotations.json
  review.json
  audit_events.jsonl
  preview/annotated.<format>       optional
```

`export_manifest.json` includes schema versions, artifact list, source/image IDs, source SHA-256, generation time,
export job ID, and destination receipt. `source_reference.json` contains the original provider/path reference and
hash; it does not duplicate the DICOM by default.

The same logical layout is used for local and Google Drive destinations. Provider IDs/URLs are recorded in receipts,
not used as the only identity. Export is complete only after written artifact hashes are verified.

## 7. `manifest.csv` and `index.csv`

The canonical `manifest.csv` columns are:

```text
manifest_version
row_id
case_id
image_id
source_folder_id
source_folder_name
source_provider
source_reference
local_object_uri
file_name
file_extension
file_sha256
modality
laterality
width_px
height_px
study_id
series_id
patient_pseudo_id
eye_id
visit_id
qc_status
queue_status
system_dr_grade
system_dr_confidence
system_prediction_id
system_model_manifest_id
human_reviewed_dr_grade
human_review_status
human_reviewer_id_hash
human_reviewed_at
annotation_count
human_annotation_count
training_eligibility
label_provenance
export_status
export_uri
export_hash
created_at
updated_at
```

`index.csv` is an operationally compact index but must retain at least `manifest_version`, `row_id`, `case_id`,
`image_id`, `file_sha256`, `source_folder_id`, `queue_status`, `system_dr_grade`, `human_reviewed_dr_grade`,
`training_eligibility`, and `export_status`.

The builder must fail closed or mark an explicit error when source hash, prediction provenance, human review status,
or eligibility cannot be determined. It must never infer `HUMAN` from a system prediction.

## 8. Compatibility and migration notes

- Reuse `ImageManifest` for source identity where its current modality/source semantics fit.
- Reuse `Prediction`, `Annotation`, `Geometry`, `ProtocolRef`, and `ModelManifest` rather than redefining them in the
  product layer.
- Add product documents and schemas as new versioned contracts; do not change existing contract meaning in place.
- Preserve the existing Mongo revision key pattern `annotation_id:revision_hash`.
- Keep local storage path references relative and provider-neutral where possible.
- Store large exports and image bytes outside MongoDB; Mongo contains references, compact metadata, and revision data.
