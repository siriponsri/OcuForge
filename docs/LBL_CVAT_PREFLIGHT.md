# LBL CVAT Preflight

This is the offline readiness and handoff record for the `LBL` (LABELER)
module. It does not start CVAT or MongoDB and it does not claim live CVAT
acceptance.

## Purpose And Ownership

OcuForge is a research and clinician-review foundation for retinal imaging
workflows. The labeler workflow connects synthetic or approved local image
cases to CVAT, preserves clinician review provenance, and exports versioned
native annotations. It is not a diagnostic product.

| Module | Role in this workflow |
|---|---|
| `LBL` | CVAT adapter, task workflow, geometry conversion, review, export, adjudication |
| `CTR` | Annotation, prediction, image, geometry, protocol, and provenance contracts |
| `DAT` | Local image objects, Mongo workflow documents, immutable annotation revisions |
| `RUN` | Local deployment boundaries, Docker/Compose, environment and secret wiring |

Normative ownership and dependency rules are in
[`docs/CTR_MODULE_CONTRACT.md`](CTR_MODULE_CONTRACT.md). Human navigation is
in [`docs/PROJECT_MAP.md`](PROJECT_MAP.md).

## Current Status

| Gate | Status |
|---|---|
| Phase 2A - Docker-independent local data foundation | PASS |
| Phase 2B - Live MongoDB acceptance | PENDING / NOT RUN |
| LBL offline implementation audit | PASS with documented partial/live boundaries |
| Live CVAT acceptance | NOT RUN |

`LBL_OFFLINE_PREFLIGHT=true`

This status means the offline code paths, contracts, tests, and handoff are
audited. It does not mean CVAT compatibility, authentication, permissions,
browser behavior, or local-service operation has been accepted.

## Readiness Matrix

`IMPLEMENTED_OFFLINE` means the behavior is implemented and exercised without
requiring a live service. `PARTIAL` means the offline boundary is present but
has a known limitation or a live dependency. `REQUIRES_LIVE_CVAT` means the
offline repository cannot prove the behavior. `MISSING` means no supported
implementation was found.

| Area | Status | Offline evidence / boundary |
|---|---|---|
| CVAT health and project bootstrap | `PARTIAL` | `CVATClient.health()` and `create_project()` plus CLI commands exist; transport is local-only and fixture tests request shape. Real upstream release/API/auth compatibility requires live CVAT. |
| Task creation, attach, and sync | `IMPLEMENTED_OFFLINE` | `Workflow.create_task()`, `attach_task()`, `attach_share()`, and `sync()` are exercised with a filesystem share and a CVAT test component. Live task/data processing still requires CVAT. |
| Prediction import with explicit mappings | `IMPLEMENTED_OFFLINE` | `import_prediction()` requires label and `ed_annotation_id` attribute mappings when used by `Workflow`; duplicate image IDs, missing images, changed prediction fingerprints, and duplicate provenance are rejected. |
| Geometry conversion | `IMPLEMENTED_OFFLINE` | Point, box, polygon, polyline, ellipse, image-presence, and full/cropped mask conversions have round-trip and invalid-geometry tests. Rotated ellipses are intentionally unsupported and must use masks. |
| Correction and review provenance | `IMPLEMENTED_OFFLINE` | AI suggestions retain parent prediction/object IDs; `CONFIRM`, `CORRECT`, `REJECT`, `ESCALATE`, and append-only history are contract-validated. |
| Annotation export | `IMPLEMENTED_OFFLINE` | CVAT payloads, sidecars, frame mappings, decision journals, native JSONL, and session summaries are exercised without a live server. |
| Adjudication and finalization | `IMPLEMENTED_OFFLINE` | Human review is required before `ADJUDICATE`; `LOCK` requires adjudication; finalized output is written as a content-addressed native snapshot. |
| Immutable revision handling | `IMPLEMENTED_OFFLINE` | Terminal annotations require a versioned amendment; Mongo revision identity is content-hashed and exact retries are idempotent in offline store tests. Live Mongo behavior remains Phase 2B. |
| DR `ProtocolRef` propagation | `IMPLEMENTED_OFFLINE` | DR-grade export requires the supplied frozen `ProtocolRef`; grade values, `UNGRADABLE`, and `UNCERTAIN` are distinct and protocol changes are rejected as in-place edits. |
| Ordinal DR, binary DR/no-DR, DME, and lesion geometry separation | `PARTIAL` | CTR enforces ordinal-vs-binary separation, label geometry policy, and a separate DME protocol axis. The v0.1 LBL bridge has no DME annotation field/project config; do not treat DME as supported by this workflow. |
| Unsupported semantic conversions | `IMPLEMENTED_OFFLINE` | No geometry is created from MIL attention; manual-first lesion classes cannot use an unvalidated starter localizer; unsupported geometry/labels and missing mappings fail validation. |
| Duplicate and retry handling | `PARTIAL` | Create-task intent and `attach_task()` support timeout reconciliation; import fingerprints and provenance IDs protect sequential retries. Cross-system operations are not one transaction and concurrent/repeated network calls require operator reconciliation. |
| Frame-to-image identity | `IMPLEMENTED_OFFLINE` | Registration rejects duplicate frame basenames; share attach checks path containment and SHA-256; sync checks frame names, uniqueness, count, and dimensions; export rechecks frame/image identity. |
| Locked/finalized annotation behavior | `IMPLEMENTED_OFFLINE` | `LOCKED` and `REJECTED` are terminal lifecycle states; transitions fail and instruct the operator to create a versioned amendment. Workflow prevents export after finalization. |

The test suite uses explicit synthetic fixtures and test CVAT/storage
components for offline behavior. Those tests are evidence of bridge logic,
not evidence that a real CVAT server accepts the requests.

## Exact Live Prerequisites

The following must be true on the Docker-capable machine before live CVAT
acceptance:

1. Phase 2B has passed with `PHASE_2B_LIVE_MONGO=pass`.
2. A reviewed and pinned upstream CVAT release is running locally. Record the
   upstream commit/tag and deployment configuration.
3. CVAT's own PostgreSQL, Redis, and volumes are healthy. OcuForge MongoDB
   does not replace CVAT PostgreSQL.
4. A local CVAT operator account/token and role permissions are configured.
   Keep the token in the machine environment or local secret handling; never
   commit it.
5. `CVAT_URL` points to an allowed local endpoint only. Do not use Atlas,
   `mongodb+srv`, arbitrary remote hosts, or cloud CVAT endpoints.
6. Use synthetic images only for this acceptance. The same synthetic image
   object directory must be available to the bridge and CVAT according to the
   approved read-only mount/share arrangement.
7. Select one checked-in project spec from
   `eyes-detected-labeler/configs/projects/`; record the returned project ID
   and actual CVAT label/attribute IDs. Never assume IDs such as `1`.

## Future Live Acceptance Order

Run this sequence from the OcuForge repository root. Stop at the first
failure and preserve local IDs, request responses, and logs without putting
credentials or private data into Git.

```text
Phase 2B Mongo PASS
  -> pinned upstream CVAT release running locally
  -> eyes-labeler health
  -> eyes-labeler bootstrap-project <checked-in project spec>
  -> create one synthetic-only task
  -> attach the synthetic image share and sync metadata
  -> import one synthetic prediction using actual CVAT mappings
  -> perform clinician-style CONFIRM or CORRECT/REJECT in CVAT
  -> export CVAT payload plus explicit decision journal
  -> adjudicate with the specialist role
  -> finalize and LOCK
  -> verify native JSONL, ProtocolRef, frame/image identity, hashes, and history
  -> record PASS evidence
```

The current command surface is:

```text
eyes-labeler health
eyes-labeler bootstrap-project eyes-detected-labeler/configs/projects/ED_LESION_POINT_MA_V1.json
eyes-local register --batch <batch.json> --images <images.jsonl> --protocol eyes-detected-contracts/protocols/ico_2017_dr.v0.1.json --actor <operator>
eyes-local create-task <batch_id> --project-id <actual_id> --actor <operator>
eyes-local attach-share <batch_id> --share-root <local_synthetic_share> --actor <operator>
eyes-local sync <batch_id> --actor <operator>
eyes-local import-predictions <batch_id> --predictions <synthetic_predictions.jsonl> --actor <operator>
eyes-local export <batch_id> --decisions <decision_journal.json> --active-seconds <positive_value> --actor <reviewer>
eyes-local finalize <batch_id> --expert-attestation --actor <expert>
```

Use the project-specific runbook and actual generated batch/image paths on
the target machine. These examples are not a command to run on this machine.
The bridge's CVAT command is `eyes-labeler`; the durable local workflow
command is `eyes-local`.

## Evidence To Record

- Set `LIVE_CVAT_ACCEPTANCE=pass` only after every step succeeds on the real
  local CVAT deployment.
- Record CVAT upstream tag/commit, OcuForge commit, project ID, task ID, and
  actual label/attribute mappings without recording tokens.
- Record health response status, synthetic image SHA-256, expected frame
  order, dimensions, and frame-to-`image_id` mapping.
- Record prediction fingerprint, import result, post-import annotation count,
  and proof that retry does not create duplicate `ed_annotation_id` values.
- Preserve native annotation JSONL, CVAT export, decision journal, session
  summary, final content hash, ProtocolRef, and full provenance history in
  approved local storage.
- Record persistence results only for checks actually performed. Do not call a
  backup/restore pass unless the documented restore drill was completed.

## Retry And Duplicate Hazards

- `create_task` records intent before the network call. If transport times
  out, do not call it again; inspect CVAT and use `attach-task` with the
  matching batch task.
- Task creation, file attachment, CVAT import, and Mongo persistence are not a
  single transaction. Preserve request IDs and reconcile before retrying.
- Import protects sequential retries with prediction fingerprints and
  provenance IDs, but concurrent callers can race at the CVAT boundary. Use
  one operator per batch and reconcile duplicate provenance before retry.
- A changed prediction set or model output requires a new batch. Do not
  overwrite an existing import.
- A changed/finalized annotation requires a versioned amendment. Do not edit
  or delete the old native revision.
- CVAT numeric IDs are deployment-local. Use stable OcuForge annotation IDs
  and rebuild CVAT ID mappings after task restore.

## Semantic Guardrails

- `dr_grade` is an image-level ordinal clinician assignment with a frozen
  protocol reference. It is not inferred from lesion counts or AI attention.
- Binary doctor-experience `DR` / `NO_DR` remains a separate,
  non-adjudicated assessment and must never become ordinal grade 0-4.
- DME is a separate axis. Fundus/UWF evidence alone is not OCT-confirmed DME;
  this v0.1 LBL bridge does not provide a DME field.
- Lesion geometry must follow the CTR label policy. Attention/evidence maps
  are not lesion geometry.
- AI suggestions remain suggestions until an explicit human decision is
  recorded. Missing or rejected candidates do not prove lesion absence.
- `UNGRADABLE` and `UNCERTAIN` are not ordinary grades and must remain
  distinguishable.
- `LOCKED` output is a reviewed research artifact, not a diagnosis or
  production clinical decision.
- This gate uses synthetic data only. Never point it at hospital paths,
  private predictions, private revisions, or credentials.

## PASS Criteria

The future live gate may be marked PASS only when:

1. Phase 2B Mongo has already passed.
2. The pinned local CVAT release is healthy and accepts the checked-in project
   configuration.
3. One synthetic image completes task attach, sync, import, review, export,
   adjudication, and lock.
4. Native output validates against CTR contracts and preserves expected
   frame/image mapping, hashes, protocol reference, and provenance history.
5. Repeated import/task recovery creates no duplicate or silently changed
   revisions.
6. No CVAT, Mongo, cloud, or private-data operation outside the approved local
   synthetic gate was performed.

Until those criteria are met:

```text
LIVE_CVAT_ACCEPTANCE=not_run
```
