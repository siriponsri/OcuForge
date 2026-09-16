# Implementation status — OcuForge V3

**Authority:** [`POC_MASTER_PLAN.md`](POC_MASTER_PLAN.md)
**As of:** 2026-09-16

This page separates implemented, verified, planned, and unknown work. It does not turn preparation into a research
result.

## Current gates

| Gate | Status | Meaning |
|---|---|---|
| Repository foundation and CPU contracts | IMPLEMENTED / VERIFIED | Offline tests and synthetic checks cover the reusable foundation. |
| Phase 2A local data foundation | IMPLEMENTED / VERIFIED | Local adapters and provenance safeguards exist. |
| Phase 2B live Mongo acceptance | UNKNOWN / NOT RUN | Requires the target service; Phase 2 overall is not PASS. |
| R0 V3 data/supervision/asset freeze | READY_TO_EXECUTE / NOT_YET_PASSED | No dataset bytes were downloaded by this reconciliation. |
| R1 C0/C1/C2 benchmark | READY_NOT_EXECUTED | No candidate was trained or selected. |
| Current R1 champion | NONE | Selection is forbidden before measured evidence. |

## Implemented and verified

- Versioned contracts, ICO protocol identity, provenance, geometry, split checks, and binary-label semantics.
- Existing DINOv3 adapter with explicit local asset/hash/license checks and no synthetic fallback.
- Reusable Attention MIL, global pooling, CORAL, feature provenance, training, evaluation, and synthetic CPU paths.
- C0/C1 explicit local-asset adapter boundary and five-class CE image-classifier contract.
- CORN head contract with target encoding, conditional decoding, shapes, and synthetic unit coverage.
- Versioned Global→ROI triage policy/input/decision contracts with unset threshold and reviewer override.
- Existing labeler/CVAT bridge, local storage, and `templates/` customer-facing GUI reference.
- V3 candidate registry, R0 overlap-audit record, validation tests, editorial SVG/HTML diagrams, and pinned diagram
  setup metadata.

## Planned, not executed

- R0 source/license/supervision/split/pretraining-overlap execution.
- R1 C0, C1, and C2 runs, model comparison, calibration, and winner-only CORN ablation.
- R2 spatial ROI dataset construction and R3 lesion classifier.
- R4 Label Studio Community live QA validation and R5 contract/API integration into the existing GUI.
- R6 DICOM, R7 model diff/drift, and R8 HL7/FHIR mapping/demo.

## Unknown or external gates

Approved foundation assets, exact revisions and licenses; FLAIR API/asset availability; DINOv3 runtime; public dataset
overlap; live Mongo/CVAT/Docker/host governance; intended local inference hardware; and any scientific performance.

## Prohibited claims

No page in this repository may claim a current champion, current R1 metric, diagnosis, clinical utility, OCT-confirmed
DME from fundus/UWF, or lesion localization from MIL attention. Historical values belong only in `docs/history/`.
