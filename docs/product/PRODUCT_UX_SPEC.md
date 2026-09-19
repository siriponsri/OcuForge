# OcuForge Product UX Specification

**Status:** Product-track planning specification
**Audience:** Product, design, frontend, runtime, data, and clinician-review implementers
**Scope:** On-prem retinal model factory and clinician review POC; not a diagnostic product

## 1. Product promise

OcuForge turns mostly unlabeled hospital retinal images into a controlled local workflow for ingestion, review,
human labeling, model-assisted screening support, export, and downstream dataset preparation. The system keeps the
original source object, system output, human review, and training eligibility visibly separate.

Research evidence supports the product, but the current R1 scientific blocker does not block this product track. The
first product POC may use a deterministic mock `ModelAdapter`; that validates workflow and provenance, not model
quality.

## 2. Information architecture

The primary navigation has five areas:

| Area | User question | Primary action |
|---|---|---|
| Sources | Where are images coming from and where should results go? | Configure source and destination |
| Queue | Which images need attention? | Filter, select, and open review |
| Review & Label | What should I record for this image? | Run AI explicitly, annotate, grade, save |
| Summary | What has been processed and reviewed? | Group, compare, and inspect completion |
| Dataset / Manifest | What is eligible for downstream use? | Inspect and export manifest |

The existing `templates/` workspace remains the behavioral reference. Its Overview, Screening, Review Queue,
Explainability, Model Comparison, and Integrations concepts may be reused, but the product navigation should make
Sources, Queue, Review & Label, Summary, and Dataset / Manifest primary. Model-lab and integration details remain
secondary or administrative surfaces.

## 3. Page-by-page flow

### 3.1 Sources

The user selects one input source:

- local image folder;
- Google Drive folder URL through an optional governed adapter.

The user selects one output destination:

- local folder;
- Google Drive folder URL through an optional governed adapter.

Before ingestion, show source type, source reference, authorization/read readiness, output readiness, supported file
types, scan scope, and the policy that original files are preserved. The primary action is `Start ingestion`.

Validation must distinguish:

- source reachable but not authorized;
- source authorized but scan failed;
- destination configured but not writable;
- valid configuration ready to run.

No image is uploaded to Google Drive by default merely because a Drive URL was entered. The adapter and local policy
must explicitly permit the operation.

### 3.2 Ingestion progress

Show a resumable progress view with discovered, accepted, duplicate, unsupported, failed, and persisted counts.
Each failure has a stable item reference and a retry action. Discovery is not presented as persistence.

After ingestion, the user can go to Queue even when some files failed. Partial ingestion is visible and auditable.

### 3.3 Queue

Queue is a searchable, sortable, filterable table or adaptive card list. It shows:

- image/case ID;
- source folder;
- filename or source reference;
- modality and laterality;
- QC state;
- System DR Grade, if present;
- Human Reviewed Grade, if present;
- review status;
- export status;
- last updated time.

Required top-level queue states are:

```text
NOT_PROCESSED
AI_PROCESSED
IN_REVIEW
HUMAN_REVIEWED
EXPORTED
ERROR
```

System grade and human grade are separate columns and filters. A missing human grade is not rendered as a system
grade, and an unreviewed system grade is not shown as ground truth.

The queue supports multi-select for review and export, but each image retains independent state. Opening an item
changes its state to `IN_REVIEW` only when the review session is materialized; merely previewing a row may remain
read-only.

### 3.4 Review & Label

The review page is image-first. The user must explicitly click `Run AI`. Opening an image does not trigger model
execution.

The page contains:

1. case context: source folder, image ID, modality, laterality, QC state, and queue status;
2. image canvas: zoom, pan, fit-to-view, and annotation overlays;
3. annotation toolbar: pointer/select, rectangle, point, circle/ellipse, polygon, and translucent area fill;
4. system panel: model bundle identity, preprocessing/calibration identity, DR grade, confidence, evidence, and
   generated system annotations;
5. human panel: human DR grade, annotation label, certainty, remark, and review action;
6. history drawer: immutable prediction, revisions, actor, timestamps, and audit events;
7. save controls: `Save & Return`, `Save draft`, and `Cancel changes` where the implementation supports drafts.

System annotations are never edited in place. A correction creates a user annotation/revision linked to the original
system prediction. Rejecting a system annotation preserves it and records the rejection.

Allowed review actions are explicit and provenance-bearing: confirm, correct, add, reject, escalate, grade, and
remark. `HUMAN_REVIEWED` requires a valid human review according to the configured product policy; it must not be
inferred from simply opening the page.

### 3.5 Multi-image review

The user can choose 1, 2, 4, or 8 image layouts. Layout changes affect presentation only. Every tile owns its image
selection, zoom, annotations, system output, human edits, dirty state, and save/error state.

If one tile fails to save or export, the UI identifies that tile and preserves successful saves for the other tiles.
The user cannot mistake a batch-level success message for all-image success.

### 3.6 Save & Return

`Save & Return` persists review revisions and the current case materialization to local NoSQL before writing export
artifacts. It then returns to Queue and shows the resulting state.

If persistence succeeds but output writing fails, the review remains saved, the case remains `HUMAN_REVIEWED`, and
the export error is visible and retryable. The UI must not show `EXPORTED` until the selected artifacts have been
verified at the destination.

### 3.7 Summary

Summary groups primarily by source folder and SYSTEM DR Grade. A separate view groups by Human Reviewed Grade.
The header must state which grade dimension is active.

Useful first-POC summary measures are counts by queue state, source folder, modality, QC status, system grade,
human grade, and export status. Do not expose research benchmark metrics or imply clinical performance in the
customer-facing summary.

### 3.8 Dataset / Manifest

Dataset / Manifest shows manifest version, generated time, source selection, row counts, hash coverage, human-review
coverage, training-eligibility counts, export location, and unresolved errors.

Rows marked `UNREVIEWED_SYSTEM` are clearly excluded from training-eligible counts. The UI must distinguish
`HUMAN`, `PSEUDO_LABEL`, `WEAK_LABEL`, and `UNREVIEWED_SYSTEM` rather than collapsing them into a generic label.

## 4. Layout and adaptive behavior

Use Chakra UI as the future adaptive component and layout system. Use Lucide icons for navigation, tools, status, and
actions. The current static HTML/CSS package is a reference and must not be treated as the production component
implementation.

### Desktop

- persistent grouped sidebar;
- compact context header;
- responsive content panels;
- queue table with filters and saved view state;
- review canvas as the dominant surface;
- system and human panels side-by-side where width allows.

### Tablet

- collapse secondary panels into drawers;
- keep image, active annotation tool, current grade, and save action visible;
- preserve source/case context while switching images.

### Small screens

- single-image focus;
- annotation tools in an accessible toolbar or bottom sheet;
- system output and human decision in ordered drawers;
- persistent save state and case identity;
- no destructive or finalizing action hidden behind an unlabeled icon.

Target checks are 375px, 768px, 1024px, and 1440px widths, plus keyboard navigation and reduced-motion mode.

### Component/layout hierarchy

The future Chakra-based application should compose these reusable layers:

```text
AppShell
├── PrimaryNavigation
│   ├── SourcesNavItem
│   ├── QueueNavItem
│   ├── ReviewNavItem
│   ├── SummaryNavItem
│   └── ManifestNavItem
├── ContextHeader
│   ├── Breadcrumbs / source context
│   ├── Connection and privacy status
│   └── User/session menu
└── PageRegion
    ├── PageHeader
    ├── FilterToolbar / ActionToolbar
    ├── MainContent
    └── FeedbackRegion

SourcesPage
├── SourcePicker
├── DestinationPicker
├── ReadinessSummary
└── IngestionJobPanel

QueuePage
├── QueueFilters
├── QueueTableOrCardList
├── QueueStateBadge
└── BulkActionBar

ReviewPage
├── CaseHeader
├── ReviewLayoutSelector
├── ImageReviewGrid
│   └── ReviewTile
│       ├── ImageCanvas
│       ├── AnnotationToolbar
│       ├── ProvenanceLegend
│       └── TileSaveState
├── SystemEvidencePanel
├── HumanDecisionPanel
├── AuditHistoryDrawer
└── SaveReturnBar

SummaryPage
├── SummaryDimensionSwitcher
├── SummaryFilters
├── SummaryGroupList
└── SummaryDetailDrawer

ManifestPage
├── ManifestOverview
├── EligibilityBreakdown
├── ManifestTable
└── ExportHistoryPanel
```

Components should consume semantic tokens and contract-shaped data. They must not contain DICOM parsing, model
architecture logic, provider credentials, or direct MongoDB calls.

## 5. Visual direction

The design should be colorful and interesting within a minimal, professional clinical tone. Color roles are not
bound to a fixed palette table. The supplied KKU colors are a seed, not a prescription:

```text
#A73B24  #7C291A  #F4E5E0  #C99A45
#202428  #667085  #FCFBFA  #FFFFFF  #E5E7EB
```

Designers may introduce complementary cool clinical colors, neutral ramps, dark-theme values, and semantic status
colors. The implementation must preserve sufficient contrast, avoid neon and AI-purple/pink gradients, and keep
status colors distinct from provenance colors. The same semantic token must be used consistently across light/dark
themes; component-level colors should not be hard-coded to brand values.

Recommended visual characteristics:

- warm or neutral base surfaces with a small number of vivid accents;
- clear status chips and progress indicators;
- subtle elevation and borders rather than decorative glass or dense shadows;
- restrained motion, 150–300ms transitions, and reduced-motion fallback;
- Public Sans or an equivalent highly legible sans-serif for interface text;
- IBM Plex Mono or equivalent for IDs, hashes, and technical references;
- Lucide outline icons with accessible labels.

System-vs-user annotation distinction must never rely on color alone. Combine configurable color, line style, fill
opacity, legend label, provenance badge, and accessible text.

## 6. UX states and transitions

```text
NOT_PROCESSED --Run AI success--> AI_PROCESSED
NOT_PROCESSED --ingestion/QC/model failure--> ERROR
AI_PROCESSED --review materialized--> IN_REVIEW
AI_PROCESSED --valid review saved--> HUMAN_REVIEWED
IN_REVIEW --valid review saved--> HUMAN_REVIEWED
IN_REVIEW --persistence/export failure--> ERROR
HUMAN_REVIEWED --verified export--> EXPORTED
EXPORTED --new correction--> IN_REVIEW
ERROR --explicit retry--> prior state or NOT_PROCESSED
```

All transitions must show a cause, timestamp, and actor/system origin in the history view. Retry must be explicit and
idempotent.

## 7. Reuse and future implementation boundary

Reuse the current `templates/` information architecture and safety language. Reuse its mock/live adapter concept,
master-detail review layout, queue patterns, review decision controls, explanation boundary, and integration page
ideas. The future product adapter expands beyond the current `getTask`, `inferGlobal`, `inferLesionRoi`,
`submitDecision`, and connection checks to cover sources, queue, cases, annotations, exports, and manifests.

Label Studio Community remains an internal ROI QA/HITL workbench. CVAT remains optional advanced labeling
infrastructure. Neither is required for the first customer-facing review loop.

## 8. UX acceptance criteria for the first POC

- Source and destination can be selected locally without external services.
- At least one DICOM and supported raster fixture can be ingested without modifying source bytes.
- Queue shows all six required states and keeps system/human grades separate.
- `Run AI` is explicit and records a versioned mock model result.
- Review supports rectangle, point, ellipse, polygon, and translucent area annotations.
- System output remains recoverable after correction or rejection.
- 1/2/4/8 layouts preserve independent image state.
- Save persists before export; export failure does not lose review state.
- Summary and Dataset / Manifest identify system grade, human grade, and training eligibility separately.
- Keyboard, focus, contrast, reduced-motion, and small-screen checks pass.
