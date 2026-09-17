# Implementation status — OcuForge V3

**Authority:** [`POC_MASTER_PLAN.md`](POC_MASTER_PLAN.md)
**As of:** 2026-09-17

This page separates implemented, verified, planned, and unknown work. It does not turn preparation into a research
result.

## Current gates

| Gate | Status | Meaning |
|---|---|---|
| Repository foundation and CPU contracts | IMPLEMENTED / VERIFIED | Offline tests and synthetic checks cover the reusable foundation. |
| Phase 2A local data foundation | IMPLEMENTED / VERIFIED | Local adapters and provenance safeguards exist. |
| Phase 2B live Mongo acceptance | UNKNOWN / NOT RUN | Requires the target service; Phase 2 overall is not PASS. |
| R0 V3 data/supervision/asset freeze | PASS | Scientific source/task/supervision/split/taxonomy/license/overlap freeze is complete; byte-dependent checks moved to R1-P0. |
| R1-P0 acquisition preflight | BLOCKED | R1 is locked by P0. Model assets, gated access, and storage/runtime are blocked by the 2026-09-17 receipt; archive/schema, preprocessing, and model loading remain not executed because no bytes were acquired. IDRiD is deferred to R2/R3. |
| R1 C0/C1/C2 benchmark | READY_NOT_EXECUTED | Campaign cannot proceed while P0 is blocked; no candidate was trained or selected. |
| Current R1 champion | NONE | Selection is forbidden before measured evidence. |

The campaign cannot proceed: R1 is locked by R1-P0 `BLOCKED`. The requested RunPod IDRiD lane is separately blocked
by the frozen R0 `cloud_eligible=false` policy; this does not make IDRiD an R1-P0 dependency or blocker.

The owner-resolvable next action is to authenticate and accept the exact gated C2 asset through the official Hugging
Face path, configure sufficient local OcuForge roots/runtime, and obtain an explicit governance decision for any IDRiD
compute location before a new preflight. No secret is requested or recorded here.

## Implemented and verified

- Versioned contracts, ICO protocol identity, provenance, geometry, split checks, and binary-label semantics.
- Existing DINOv3 adapter with explicit local asset/hash/license checks and no synthetic fallback.
- Reusable Attention MIL, global pooling, CORAL, feature provenance, training, evaluation, and synthetic CPU paths.
- C0/C1 explicit local-asset adapter boundary and five-class CE image-classifier contract.
- CORN head contract with target encoding, conditional decoding, shapes, and synthetic unit coverage.
- Versioned Global→ROI triage policy/input/decision contracts with unset threshold and reviewer override.
- Existing labeler/CVAT bridge, local storage, and `templates/` customer-facing GUI reference.
- V3 candidate registry with separate research/deployment eligibility, completed R0 overlap/dataset audit record, R1-P0 acquisition contract and state machine, validation tests, editorial SVG/HTML diagrams, and pinned diagram
  setup metadata.

## Planned, not executed

- Recovery and re-execution of R1-P0 acquisition preflight after its blockers are resolved.
- R1 C0, C1, and C2 runs, model comparison, calibration, and winner-only CORN ablation.
- R2 spatial ROI dataset construction and R3 lesion classifier.
- R4 Label Studio Community live QA validation and R5 contract/API integration into the existing GUI.
- R6 DICOM, R7 model diff/drift, and R8 HL7/FHIR mapping/demo.

## Unknown or external gates

R1-P0 asset hashes and final access/load results; MMRDR archive checksums and schema/split smoke; IDRiD archive
checksums/inventory and negative examples for R2/R3; FLAIR/DINOv3 source-image overlap; live Mongo/CVAT/Docker/host governance;
intended local inference hardware; and any scientific performance.

## Prohibited claims

No page in this repository may claim a current champion, current R1 metric, diagnosis, clinical utility, OCT-confirmed
DME from fundus/UWF, or lesion localization from MIL attention. Historical values belong only in `docs/history/`.
