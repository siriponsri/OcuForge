# OcuForge Product UX Specification

**Status:** Product-track planning specification
**Audience:** Product, design, frontend, runtime, data, and clinician-review implementers
**Scope:** On-prem retinal model factory and clinician review system; not a diagnostic product

## 1. Product promise

OcuForge helps a hospital start with mostly unlabeled retinal images, commonly DICOM, and progressively build a
governed hospital-specific encoder plus lightweight task head. The product loop is:

```text
mostly unlabeled hospital images
    -> local ingestion and QC
    -> clinician-reviewed labels
    -> reviewed dataset snapshot
    -> future encoder adaptation / SSL
    -> lightweight task-specific head
    -> validation and calibration
    -> versioned encoder + head bundle
    -> local deployment and Review Workspace
    -> iterative relabel / retrain loop
```

Research evidence supports product engineering, but `RESEARCH_BLOCKED != PRODUCT_BLOCKED`. The current R1 scientific
blocker remains unchanged and does not authorize training or experiments. The first product POC may use a
deterministic mock `ModelAdapter`; that validates workflow and provenance, not model quality.

## 2. Information architecture

The five primary areas remain:

| Area | User question | Primary action |
|---|---|---|
| Sources | Where are images coming from and where should results go? | Configure source and destination |
| Queue | Which images need attention? | Filter, select, and open review |
| Review & Label | What should I record for this image? | Run AI explicitly, annotate, grade, save |
| Summary | What has been processed and reviewed? | Group, compare, and inspect recovery |
| Dataset / Manifest | What is eligible for downstream use? | Inspect, snapshot, and export a manifest |

The existing `templates/` DR Review Workspace remains the behavioral reference. Its review layout, queue patterns,
decision controls, and safety language can be reused. Label Studio CE remains optional internal HITL infrastructure;
CVAT remains optional advanced annotation infrastructure.

## 3. Page-by-page flow

### 3.1 Sources

The user selects an input source and output destination through adapter-shaped controls:

- local folder or mounted hospital share;
- Google Drive folder URL through an optional governed adapter.

The user selects an output destination:

- local folder or mounted output share;
- Google Drive folder URL through an optional governed adapter.

The UI depends on `SourceAdapter`, `DestinationAdapter`, and `LocalPathAdapter` readiness, not directly on browser filesystem APIs. A local
deployment may provide a backend path picker, a desktop/native shell may provide a native picker, and a browser may
use the File System Access API where supported. Unsupported browser capabilities must produce a clear setup state,
not a false local-path promise.

Before ingestion, show source type, destination type, adapter readiness, scan scope, supported formats, DICOM policy,
output policy, and the fact that original objects are preserved. The primary action is `Start ingestion`.

No provider credential is placed in the browser log, public manifest, Git, or external telemetry. Entering a Drive URL
does not upload data until the governed adapter and local policy permit it.

### 3.2 Ingestion progress and quarantine

Show a resumable job with discovered, DICOM, raster, accepted, duplicate, unsupported, malformed, quarantined,
failed, and persisted counts. Every item has a stable reference and retry/quarantine action.

Phase-1/core DICOM behavior must be visible:

- discover DICOM objects, including common multi-frame objects;
- hash and preserve immutable source bytes before conversion;
- extract approved technical metadata;
- generate a display derivative with orientation, frame, color, and windowing provenance where applicable;
- create an image/case and Queue entry when accepted;
- quarantine malformed or unsupported DICOM without silently treating it as raster.

Where applicable, the local technical identity includes `study_instance_uid`, `series_instance_uid`,
`sop_instance_uid`, `frame_number`, and `transfer_syntax_uid`. These are shown only through the approved local
privacy boundary; patient-identifying values are not exposed.

Patient-identifying DICOM metadata remains in the local governed boundary. The UI shows safe technical metadata only.
Partial ingestion is usable and auditable; a failed item does not hide successfully ingested cases.

### 3.3 Queue

Queue is a searchable, sortable, filterable table or adaptive card list. It shows:

- image/case ID and source reference;
- modality, laterality, and safe technical metadata;
- system DR grade, if present;
- human reviewed DR grade, if present;
- review status, AI status, export status, and a derived composite badge;
- last updated time and retry/recovery affordance.

The three durable operational dimensions are independent:

```text
review_status: NOT_STARTED | IN_REVIEW | HUMAN_REVIEWED
ai_status:     NOT_RUN | RUNNING | PROCESSED | FAILED
export_status: NOT_EXPORTED | EXPORTING | EXPORTED | FAILED
```

Queue badges may render a derived composite such as `READY FOR REVIEW`, `AI FAILED`, `HUMAN REVIEWED / EXPORT
FAILED`, or `EXPORTED`. The composite is never stored as the only state.

The Queue must make these rules apparent:

- successful human review remains durable if export fails;
- export failure never reverts `HUMAN_REVIEWED`;
- AI failure never destroys an existing review or annotation history;
- retry is explicit, idempotent, and scoped to the failed operation;
- system grade and human grade remain separate and neither is silently substituted for the other.

Opening a row materializes `IN_REVIEW` only when a review session is created. Read-only preview does not change review
state.

### 3.4 Review & Label

The user must explicitly click `Run AI`. Opening an image never starts AI execution. The page contains:

1. case context: source folder, IDs, modality, laterality, safe DICOM metadata, QC, and operational statuses;
2. image canvas: zoom, pan, fit-to-view, frame selection where applicable, and overlays;
3. annotation toolbar: select, rectangle, point, circle/ellipse, polygon, and translucent area fill;
4. system panel: versioned bundle identity, preprocessing, calibration, grade, confidence, and system annotations;
5. human panel: human DR grade, annotation label, certainty, remark, and review action;
6. history drawer: immutable predictions, annotation revisions, operational events, actor, and timestamps;
7. save controls: `Save draft`, `Save & Return`, `Retry export`, and explicit cancel where supported.

System annotations use a distinct line/fill style, provenance badge, and accessible label. User annotations use a
different style and provenance badge. Color is not the only distinction. A correction creates a new user revision
linked to the system object; it never edits or overwrites the original prediction.

Allowed actions include confirm, correct, add, reject, escalate, grade, and remark. `HUMAN_REVIEWED` requires the
configured valid human review action, not merely opening the page or running AI.

### 3.5 Multi-image review

The user can choose 1, 2, 4, or 8 image layouts. Layout changes affect presentation only. Each tile retains its own
selection, zoom, annotations, system output, human edits, dirty state, operational statuses, and save/export result.
One tile failing does not make another tile appear failed or erase a successful review.

### 3.6 Save & Return and recovery

`Save & Return` first persists review revisions and the materialized review to local NoSQL. Export is then scheduled or
performed through `ExportAdapter` according to output policy.

If persistence succeeds and export fails:

- `review_status` remains `HUMAN_REVIEWED`;
- `export_status` becomes `FAILED`;
- the Queue shows a composite `HUMAN REVIEWED / EXPORT FAILED` badge;
- the failed export is retryable with the same idempotency key;
- the original DICOM and all review history remain intact.

If AI fails, `ai_status` becomes `FAILED` while prior review and annotations remain unchanged. If a retry succeeds,
the new immutable prediction is linked to the prior attempt; it does not rewrite history.

### 3.7 Summary

Summary groups primarily by source folder and SYSTEM DR Grade, with a separate Human Reviewed Grade view. The active
dimension is always stated. First product measures include counts by source folder, modality, QC, review status, AI
status, export status, system grade, human grade, and quarantine/failure reason. Do not show research benchmark
metrics or imply clinical performance in customer-facing Summary.

### 3.8 Dataset / Manifest

Dataset / Manifest shows manifest version, snapshot ID, source selection, row counts, hash coverage, human-review
coverage, training eligibility, annotation revision coverage, output policy, export location, and unresolved errors.

Rows marked `UNREVIEWED_SYSTEM` are visible for audit but excluded from training-eligible selections. The UI must keep
`HUMAN`, `PSEUDO_LABEL`, `WEAK_LABEL`, and `UNREVIEWED_SYSTEM` visibly distinct. The semantic rule is explicit:
`SYSTEM AUTO LABEL != HUMAN GROUND TRUTH`.

For each eligible training row, show or provide a safe reference to the exact `annotation_artifact_uri`,
`annotation_revision_hash`, `annotation_schema_version`, `training_image_uri`, `training_image_sha256`,
`derivative_preprocessing_version`, and `human_grading_protocol`. An annotation count alone is not a usable ROI
training reference.

The UI supports a future `Create dataset snapshot` action. Snapshot creation records the selected reviewed rows and
the identity-safe split policy; it does not start SSL, head training, validation, or calibration.

## 4. Output policy

The user or local policy selects one output policy:

```text
REFERENCE_ONLY
COPY_ORIGINAL
DERIVED_IMAGE_ONLY
COPY_ORIGINAL_AND_DERIVED
```

`REFERENCE_ONLY` is the default for large DICOM workflows. It writes source references and hashes without duplicating
large original bytes. Copying is explicit and policy-gated. `DERIVED_IMAGE_ONLY` writes display/preview derivatives
without replacing the source. `COPY_ORIGINAL_AND_DERIVED` writes both when policy permits.

Annotated previews are derived artifacts. An annotation is never burned into, written into, or used to overwrite the
original DICOM. The review UI must display the selected policy before export and the receipt must record the policy.

## 5. Layout and adaptive behavior

Use Chakra UI as the future adaptive component/layout system and Lucide icons for navigation, tools, status, and
actions. The current static HTML/CSS POC is a reference, not the production component implementation.

### Desktop

- persistent grouped sidebar;
- compact context header with privacy/adapter status;
- queue table with filters and derived state badges;
- review canvas as the dominant surface;
- system and human panels side-by-side where width allows.

### Tablet and small screens

- collapse secondary panels into drawers;
- keep image, active tool, current grade, operational status, and save action visible;
- use an accessible annotation toolbar or bottom sheet;
- keep case identity and persistence/export status visible;
- do not hide a finalizing action behind an unlabeled icon.

Target checks are 375px, 768px, 1024px, and 1440px widths, plus keyboard navigation and reduced-motion mode.

## 6. Component hierarchy

```text
AppShell
|-- PrimaryNavigation
|-- ContextHeader
|   |-- adapter/readiness status
|   |-- privacy boundary status
|   `-- user/session menu
`-- PageRegion
    |-- PageHeader
    |-- ActionToolbar
    |-- MainContent
    `-- FeedbackRegion

SourcesPage
|-- SourcePicker
|-- DestinationPicker
|-- LocalFileSystemBridge status
|-- OutputPolicyPicker
|-- ReadinessSummary
`-- IngestionJobPanel / QuarantinePanel

QueuePage
|-- QueueFilters
|-- QueueTableOrCardList
|-- OperationalStatusBadges
`-- RecoveryActionBar

ReviewPage
|-- CaseHeader
|-- ReviewLayoutSelector (1 / 2 / 4 / 8)
|-- ImageReviewGrid
|   `-- ReviewTile -> ImageCanvas -> AnnotationToolbar -> ProvenanceLegend
|-- SystemEvidencePanel
|-- HumanDecisionPanel
|-- AuditHistoryDrawer
`-- SaveReturnBar

SummaryPage
|-- SummaryDimensionSwitcher
|-- SummaryFilters
`-- SummaryGroupList / RecoveryDetail

ManifestPage
|-- SnapshotControls
|-- EligibilityBreakdown
|-- ManifestTable
`-- ExportHistoryPanel
```

Components consume semantic contract-shaped data. They do not parse DICOM, import model architecture code, hold
provider credentials, or call MongoDB directly.

## 7. UX states and transitions

The UI renders independent dimensions and a derived composite:

```text
review_status: NOT_STARTED -> IN_REVIEW -> HUMAN_REVIEWED
review_status: HUMAN_REVIEWED -> IN_REVIEW     (new correction)

ai_status: NOT_RUN -> RUNNING -> PROCESSED
ai_status: RUNNING -> FAILED
ai_status: FAILED -> RUNNING                   (explicit idempotent retry)

export_status: NOT_EXPORTED -> EXPORTING -> EXPORTED
export_status: EXPORTING -> FAILED
export_status: FAILED -> EXPORTING             (explicit idempotent retry)
```

AI and export transitions never rewrite review state. Every transition shows a cause, timestamp, actor/system origin,
attempt ID, and related immutable object. Queue composite examples are presentation rules, not additional canonical
states.

## 8. Reuse and POC acceptance criteria

Reuse the current `templates/` information architecture, master/detail review layout, queue patterns, adapter seam,
and safety language. Preserve explicit Run AI, system-vs-human provenance, all five annotation geometries, 1/2/4/8
layouts, Save & Return, immutable history, NoSQL/object-storage direction, optional Google Drive, Label Studio CE,
CVAT, and architecture-agnostic model bundles.

The first POC is accepted when synthetic or explicitly authorized local fixtures demonstrate:

- local source/destination adapter selection without assuming unrestricted browser filesystem access;
- at least one DICOM fixture and one supported raster fixture ingested without source-byte modification;
- DICOM SHA-256, safe technical metadata, display derivative, and derivation provenance;
- malformed/unsupported DICOM quarantine;
- Queue dimensions for review, AI, and export statuses;
- explicit deterministic mock `Run AI` with immutable prediction;
- all five annotation geometries and system/user distinction;
- independent 1/2/4/8 review state;
- Save & Return before export;
- export failure retaining `HUMAN_REVIEWED` and remaining retryable;
- manifest fields sufficient to locate annotation revisions and training images;
- no training, Pod, experiment, or R1 scientific state change.
