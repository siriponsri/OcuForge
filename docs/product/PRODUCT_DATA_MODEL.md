# OcuForge Product Data Model

**Status:** Product-track planning specification
**Storage direction:** Local/on-prem NoSQL plus immutable local object storage
**Scope:** Ingestion, DICOM identity, review, export, manifest eligibility, and future model-factory lineage

## 1. Modeling rules

The model keeps immutable source objects, DICOM identity, display derivatives, system predictions, human revisions,
operational state, training eligibility, dataset snapshots, and future model-factory lineage separate.

Existing eyes-detected-contracts identity, geometry, prediction, annotation, protocol, and model-manifest semantics
remain authoritative. Product documents are additive and versioned. Mongo documents may be denormalized for reads,
but immutable facts and source bytes are never overwritten. Hospital/private records and artifacts remain local-only.

The data layer is reached through `LocalFileSystemBridge` / `LocalPathAdapter` and `ModelAdapter` interfaces; it does
not depend on a browser-specific filesystem API or a concrete encoder architecture.

## 2. Canonical vocabulary and states

~~~
review_status: NOT_STARTED | IN_REVIEW | HUMAN_REVIEWED
ai_status:     NOT_RUN | RUNNING | PROCESSED | FAILED
export_status: NOT_EXPORTED | EXPORTING | EXPORTED | FAILED
~~~

queue_status is a derived presentation value, not a replacement for the three dimensions. It may be materialized
for query speed only when it remains recomputable.

Every manifest row has exactly one training eligibility value:

~~~
HUMAN | PSEUDO_LABEL | WEAK_LABEL | UNREVIEWED_SYSTEM
~~~

UNREVIEWED_SYSTEM is the default for system-only output and is never included in a human/training-eligible
selection. PSEUDO_LABEL and WEAK_LABEL require explicit policy, source, confidence/quality metadata, and downstream
opt-in. No save operation silently promotes system output to HUMAN.

Output policy is also explicit:

~~~
REFERENCE_ONLY | COPY_ORIGINAL | DERIVED_IMAGE_ONLY | COPY_ORIGINAL_AND_DERIVED
~~~

REFERENCE_ONLY is the default for large DICOM workflows.

## 3. Collections and documents

All documents include schema_version, a stable ID, timestamps, and an integrity hash when immutable/exported.

### sources

~~~
source_id
schema_version
provider_type: LOCAL_FOLDER | GOOGLE_DRIVE_FOLDER
source_reference
provider_item_id: optional
display_name
folder_path_or_name: local-only when sensitive
authorization_state: NOT_CHECKED | READY | UNAUTHORIZED | UNREACHABLE | ERROR
filesystem_bridge: LOCAL_BACKEND | DESKTOP_SHELL | BROWSER_FILE_SYSTEM | GOOGLE_DRIVE
scan_options
source_policy
created_at
updated_at
~~~

The browser stores no provider token. A local path reference is governed local metadata, not proof that a browser can
access that path.

### destinations

~~~
destination_id
schema_version
provider_type: LOCAL_FOLDER | GOOGLE_DRIVE_FOLDER
destination_reference
provider_item_id: optional
display_name
filesystem_bridge: LOCAL_BACKEND | DESKTOP_SHELL | BROWSER_FILE_SYSTEM | GOOGLE_DRIVE
output_policy: REFERENCE_ONLY | COPY_ORIGINAL | DERIVED_IMAGE_ONLY | COPY_ORIGINAL_AND_DERIVED
authorization_state
created_at
updated_at
~~~

Configuration is not proof of a successful write; receipts provide that proof.

### ingestion_jobs and ingestion_items

~~~
ingestion_jobs:
  job_id, schema_version, source_id, destination_id, actor_id_hash
  status: CREATED | SCANNING | PERSISTING | COMPLETED | COMPLETED_WITH_ERRORS | FAILED
  counts: { discovered, dicom_discovered, raster_discovered, accepted, duplicates,
            unsupported, malformed, quarantined, failed, persisted }
  scan_options, item_results_reference, started_at, completed_at, error_summary

ingestion_items:
  ingestion_item_id, job_id, source_item_reference, source_relative_path, original_file_name
  detected_file_type: DICOM | JPEG | PNG | TIFF | OTHER
  sha256, byte_size
  outcome: ACCEPTED | DUPLICATE | UNSUPPORTED | MALFORMED | QUARANTINED | FAILED
  quarantine_reason, image_id, case_id, attempt_id, created_at
~~~

Large item-result lists remain in separate local documents/files. Malformed/unsupported DICOM is not silently treated
as raster.

### images

~~~
image_id, schema_version, case_id, source_id, source_item_reference
source_relative_path, original_file_name, file_sha256, byte_size
file_type: DICOM | JPEG | PNG | TIFF | OTHER
immutable_object_uri, modality, laterality, width_px, height_px, frame_count
patient_pseudo_id: optional/local-only
study_id: optional/local-only
series_id: optional/local-only
eye_id: optional/local-only
visit_id: optional/local-only
acquisition_time_bucket: optional/local-only
dicom_metadata_reference: optional/local-only
display_derivative_reference: optional
ingested_at
~~~

The original object hash is the identity anchor. Duplicate occurrences can share an immutable object while retaining
independent source provenance.

### dicom_identities

This local-governed document is never sent to browser logs, public manifests, Git, cloud services, or external
telemetry.

~~~
image_id, schema_version
study_instance_uid: optional
series_instance_uid: optional
sop_instance_uid: optional
frame_number: optional
transfer_syntax_uid: optional
specific_character_set: optional/local-only
patient_id_reference: optional/local-only
patient_name_reference: optional/local-only
technical_metadata_hash
privacy_policy_version
created_at
~~~

UID and frame identity support exact source/derivative linkage. Patient-identifying values remain local and governed.

### display_derivatives

~~~
derivative_id, schema_version, image_id, source_file_sha256
derivative_uri, derivative_sha256, derivative_format, width_px, height_px
frame_number: optional
orientation_transform: optional
windowing: optional { center, width, function }
color_transform: optional
preprocessing_version, generation_parameters_hash, generated_at
~~~

Derivatives are reproducible display artifacts; they never replace original bytes.

### cases

~~~
case_id, schema_version, source_folder_id, image_ids
review_status: NOT_STARTED | IN_REVIEW | HUMAN_REVIEWED
ai_status: NOT_RUN | RUNNING | PROCESSED | FAILED
export_status: NOT_EXPORTED | EXPORTING | EXPORTED | FAILED
derived_queue_status: optional
qc_status
system_dr_grade, system_prediction_id
human_reviewed_dr_grade, human_review_id
training_eligibility_summary
version, created_at, updated_at
~~~

The derived Queue badge may be NOT_PROCESSED, AI_PROCESSED, IN_REVIEW, HUMAN_REVIEWED, EXPORTED, AI_FAILED, or
HUMAN_REVIEWED / EXPORT_FAILED. It cannot replace the canonical fields.

### predictions

Each AI attempt creates an immutable document compatible with the existing Prediction contract.

~~~
prediction_id, schema_version, attempt_id, idempotency_key
image_id, file_sha256_at_run
model_manifest_id, model_bundle_version, encoder_identity, head_identity
preprocessing_version, calibration_version
dr: { grading_protocol, grade, ordinal_probs, confidence }
lesion_presence, objects, evidence, ood, gradability_probability
origin: SYSTEM
created_at, run_parameters_hash
~~~

The contract may use AI_SUGGESTED for prediction candidates. Product UI may say SYSTEM, while contract origin is
preserved. A later run never deletes an earlier prediction.

### annotation_revisions

~~~
annotation_id, revision_hash, schema_version, image_id, label
geometry, coordinate_space: normalized_0_1
display_fill: optional { enabled, opacity, color_token }
origin: AI_SUGGESTED | CLINICIAN_CONFIRMED | CLINICIAN_CORRECTED | CLINICIAN_ADDED | EXPERT_ADJUDICATED
parent_prediction_id, parent_object_id, source_model_version
annotator_id_hash
review_status: DRAFT | CONFIRMED | CORRECTED | REJECTED | ADJUDICATED | LOCKED
clinician_certainty, uncertain, grading_protocol, dr_grade, gradability, laterality
created_at, history[]
~~~

Supported geometry is point, rectangle/box, ellipse/circle, polygon, and translucent area presentation. The existing
contract stores normalized point, box, ellipse, polygon, and mask geometry; a circle is an ellipse with equal extents.
Human edits create new revisions linked to parent IDs; system revisions are never overwritten.

### reviews

~~~
review_id, schema_version, case_id, image_id
active_system_prediction_id, active_human_annotation_revision_ids
system_dr_grade, human_reviewed_dr_grade
human_review_status: NOT_STARTED | DRAFT | SUBMITTED | ADJUDICATED | LOCKED
remark, reviewer_id_hash, reviewer_certainty
last_saved_revision_hash, version, created_at, updated_at
~~~

System and human grades are never represented by one overloaded grade field. Review content status is distinct from
case-level review_status.

### export_jobs

~~~
export_job_id, schema_version, destination_id, case_ids, manifest_snapshot_id
output_policy: REFERENCE_ONLY | COPY_ORIGINAL | DERIVED_IMAGE_ONLY | COPY_ORIGINAL_AND_DERIVED
artifact_selection, idempotency_key
status: CREATED | WRITING | VERIFIED | FAILED | PARTIAL
artifact_receipts[], error_code, created_at, completed_at
~~~

Receipts record logical path, local/provider reference, byte size, SHA-256, source-hash relation, and verification
time. Export failure never changes review state or deletes history.

### manifest_snapshots

~~~
manifest_snapshot_id, schema_version, manifest_version, selection_query_hash
identity_split_policy_reference: optional
row_count, eligibility_counts, source_hash_coverage, annotation_revision_coverage
manifest_csv_reference, index_csv_reference, generation_hash, created_at
~~~

A snapshot is immutable input to a future split/adaptation job. Creating one does not train or validate a model.

### dataset_factory_jobs and model_bundles (future)

~~~
dataset_factory_jobs:
  factory_job_id, schema_version, manifest_snapshot_id
  job_type: IDENTITY_SPLIT | SSL_ADAPTATION | HEAD_TRAINING | VALIDATION | CALIBRATION | BUNDLE_BUILD
  status: PLANNED | READY | RUNNING | SUCCEEDED | FAILED | CANCELLED
  input_hash, output_artifact_references, policy_reference, run_environment_reference
  created_at, completed_at

model_bundles:
  model_manifest_id, schema_version, encoder_identity, encoder_version
  head_identity, head_version, preprocessing_version, calibration_version
  bundle_version, artifact_uri, artifact_sha256, supported_inputs
  output_protocol_references, deployment_status, license_status, created_at
~~~

These are future lineage documents only. They do not authorize training, Pods, experiments, or changes to research
conclusions. The product boundary remains architecture-agnostic.

### audit_events

~~~
event_id, schema_version, aggregate_type, aggregate_id
dimension: REVIEW | AI | EXPORT | INGESTION | ANNOTATION | FACTORY
action, actor_type: SYSTEM | USER | SERVICE, actor_id_hash, attempt_id
prior_state, next_state, reason
related_prediction_id, related_annotation_id, timestamp
~~~

Audit events are append-only and contain no raw bytes, credentials, or unnecessary patient-identifying fields.

## 4. Provenance and training eligibility

- SYSTEM AUTO LABEL is not HUMAN GROUND TRUTH.
- Predictions retain model bundle, preprocessing, calibration, image hash, and creation metadata.
- Human confirmation/correction/rejection creates a linked revision/event.
- User annotations start as drafts and gain HUMAN eligibility only after configured review.
- Expert adjudication and lock remain separate where deployment requires them.
- Unannotated regions are not silently converted to negative labels.
- Human grade remains distinct from system grade and carries human_grading_protocol.
- PSEUDO_LABEL and WEAK_LABEL are explicit, policy-governed alternatives.

## 5. Independent operational transitions

~~~
review_status: NOT_STARTED -> IN_REVIEW -> HUMAN_REVIEWED
review_status: HUMAN_REVIEWED -> IN_REVIEW             (new correction)

ai_status: NOT_RUN -> RUNNING -> PROCESSED
ai_status: RUNNING -> FAILED
ai_status: FAILED -> RUNNING                           (explicit idempotent retry)

export_status: NOT_EXPORTED -> EXPORTING -> EXPORTED
export_status: EXPORTING -> FAILED
export_status: FAILED -> EXPORTING                     (explicit idempotent retry)
~~~

AI failure does not destroy review or annotation revisions. Export failure does not revert HUMAN_REVIEWED. Retries
use stable idempotency keys and never duplicate immutable revisions or verified artifacts. Every transition records
actor/system origin, timestamp, reason, attempt ID, and prior/next state.

## 6. DICOM boundary

- DICOM is a first-class Phase-1 file type.
- Hash and persist original bytes before pixel extraction or display conversion.
- Preserve study_instance_uid, series_instance_uid, sop_instance_uid, frame_number, and transfer_syntax_uid where
  applicable in the local identity document.
- Keep source DICOM and display/annotated preview objects separate.
- Record frame selection, orientation, windowing, color conversion, and preprocessing as derivative metadata.
- Keep patient-identifying values local; never expose them in browser logs, public manifests, Git, cloud services, or
  external telemetry.
- Never draw annotations into or overwrite original DICOM.
- Unsupported/malformed objects become quarantined records with actionable reasons.

## 7. Export artifact contract

The default REFERENCE_ONLY layout is:

~~~
<output-root>/<source-folder-id>/<case-id>/
  export_manifest.json
  image_metadata.json
  source_reference.json
  system_predictions.json
  annotations.json
  review.json
  audit_events.jsonl
  preview/annotated.<format>       optional derived artifact
  source/original.<format>         only for explicit copy policy
~~~

export_manifest.json includes schemas, artifact list, IDs, source SHA-256, output policy, generation time, export job
ID, and destination receipt. The same logical layout applies to local and Google Drive destinations. Provider IDs and
URLs are receipts, not the only identity. Export is complete only after output hashes are verified.

## 8. manifest.csv and index.csv

The canonical manifest.csv columns are:

~~~
manifest_version
manifest_snapshot_id
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
file_type
modality
laterality
width_px
height_px
frame_count
study_instance_uid_reference
series_instance_uid_reference
sop_instance_uid_reference
frame_number
transfer_syntax_uid
patient_pseudo_id
eye_id
visit_id
qc_status
review_status
ai_status
export_status
derived_queue_status
system_dr_grade
system_dr_confidence
system_prediction_id
system_model_manifest_id
human_reviewed_dr_grade
human_grading_protocol
human_review_status
human_reviewer_id_hash
human_reviewed_at
annotation_count
human_annotation_count
annotation_artifact_uri
annotation_revision_hash
annotation_schema_version
training_image_uri
training_image_sha256
derivative_preprocessing_version
training_eligibility
label_provenance
output_policy
export_uri
export_hash
created_at
updated_at
~~~

Identity fields ending in _reference are approved local or de-identified references only. Raw PHI is never written to a
public-safe or external manifest.

For lesion/ROI training, annotation_artifact_uri, annotation_revision_hash, and annotation_schema_version are required
when annotations exist; counts alone cannot locate exact geometry. For image training, training_image_uri,
training_image_sha256, and derivative_preprocessing_version identify exact downstream input. human_grading_protocol
identifies the human grade protocol.

index.csv is compact but retains at least:

~~~
manifest_version, manifest_snapshot_id, row_id, case_id, image_id, file_sha256
training_image_uri, training_image_sha256, source_folder_id
review_status, ai_status, export_status
system_dr_grade, human_reviewed_dr_grade, human_grading_protocol
annotation_artifact_uri, annotation_revision_hash, annotation_schema_version
derivative_preprocessing_version, training_eligibility, export_status
~~~

The builder fails closed or marks an explicit error when source hash, prediction provenance, human review status,
annotation revision, training image identity, or eligibility cannot be determined. It never infers HUMAN from a system
prediction.

## 9. Compatibility and migration notes

- Reuse ImageManifest, Prediction, Annotation, Geometry, ProtocolRef, and ModelManifest where semantics fit.
- Add product documents and schemas as new versioned contracts; do not mutate existing shared meaning in place.
- Preserve the existing annotation_id:revision_hash key pattern.
- Keep storage paths relative and provider-neutral where possible.
- Keep large exports, images, derivatives, embeddings, and checkpoints outside MongoDB; Mongo stores references,
  compact metadata, and revision data.
