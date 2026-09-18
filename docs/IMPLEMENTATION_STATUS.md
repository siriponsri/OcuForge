# Implementation status — OcuForge V3

**Authority:** [`POC_MASTER_PLAN.md`](POC_MASTER_PLAN.md)
**As of:** 2026-09-18

This page separates implemented, verified, planned, and unknown work. It does not turn preparation into a research
result.

## Current gates

| Gate | Status | Meaning |
|---|---|---|
| Campaign start readiness | YES | Owner authorization permits R1-P0 acquisition/runtime validation and independent R2/R3 and Colab lanes. |
| R1-P0 execution readiness | YES | The authorized public RunPod P0 runtime path is available; current P0 evidence is recorded. |
| Repository foundation and CPU contracts | IMPLEMENTED / VERIFIED | Offline tests and synthetic checks cover the reusable foundation. |
| Phase 2A local data foundation | IMPLEMENTED / VERIFIED | Local adapters and provenance safeguards exist. |
| Phase 2B live Mongo acceptance | UNKNOWN / NOT RUN | Requires the target service; Phase 2 overall is not PASS. |
| R0 V3 data/supervision/asset freeze | PASS | Scientific source/task/supervision/split/taxonomy/license/overlap freeze is complete; byte-dependent checks moved to R1-P0. |
| R1-P0 acquisition preflight | BLOCKED | R1 is locked by two exact MMRDR duplicate-content groups crossing the released `tr`/train and `ts`/test split. Archive integrity, schema, asset hashes, gated access, preprocessing, official C0/C1/C2 loading, and storage/runtime checks passed. |
| R1 training readiness | NO | Training remains forbidden while P0 is `BLOCKED`; no candidate was trained or selected. |
| R1 C0/C1/C2 benchmark | READY_NOT_EXECUTED | The benchmark remains locked by the P0 leakage finding, not by campaign-start or runtime authorization. |
| Current R1 champion | NONE | Selection is forbidden before measured evidence. |

The R1 training lane cannot proceed: R1 is locked by R1-P0 `BLOCKED` until OWNER resolves the released-split duplicate
leakage. IDRiD research-only RunPod execution is authorized independently, but its R2/R3 preflight remains pending
authorized archive access and does not make IDRiD an R1-P0 dependency or resolution.

The owner-resolvable next action is to review the two exact cross-split duplicate groups and resolve the leakage
protocol without reshuffling or silently excluding rows. DagsHub/MLflow connectivity is an evidence-mirror warning only;
no secret is requested or recorded here.

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
- R1-P0 public acquisition/runtime evidence: MMRDR archive/inventory, schema/split audit, exact C0/C1/C2 hashes,
  official loader/forward checks, asset-specific preprocessing, gated access, and storage/runtime validation.

## Planned, not executed

- OWNER resolution and, if accepted, recovery/re-execution of R1-P0 after the released-split leakage blocker is resolved.
- R1 C0, C1, and C2 runs, model comparison, calibration, and winner-only CORN ablation.
- R2 spatial ROI dataset construction and R3 lesion classifier.
- R4 Label Studio Community live QA validation and R5 contract/API integration into the existing GUI.
- R6 DICOM, R7 model diff/drift, and R8 HL7/FHIR mapping/demo.

## Unknown or external gates

IDRiD archive checksums/inventory and negative examples for R2/R3; FLAIR/DINOv3 source-image overlap; DagsHub/MLflow
connectivity; live Mongo/CVAT/Docker/host governance; intended local inference hardware; and any scientific performance.

## Prohibited claims

No page in this repository may claim a current champion, current R1 metric, diagnosis, clinical utility, OCT-confirmed
DME from fundus/UWF, or lesion localization from MIL attention. Historical values belong only in `docs/history/`.
