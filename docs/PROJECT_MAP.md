# OcuForge project map

**Status:** ACTIVE SUPPORTING HANDOFF
**Authority:** [`POC_MASTER_PLAN.md`](POC_MASTER_PLAN.md)

OcuForge is a research and clinician-review foundation, not a diagnostic product. The current gate is R0 V3 `PASS`;
R1-P0 Global execution is complete but `BLOCKED` by released-split duplicate leakage. R1 remains
`READY_NOT_EXECUTED` with no champion. Resolve the blocker before any R1 training; `PASS` or `PASS_WITH_WARNINGS`
can unlock it only when no blocker remains.

## Ownership

| ID | Module | Owns |
|---|---|---|
| CTR | Contracts | schemas, protocol identity, provenance, validators, shared interfaces |
| MDL | Models | C0/C1/C2 adapters, encoders, heads, training, inference, evaluation |
| LBL | Labeler | Label Studio QA, optional CVAT, review and annotation import/export |
| DAT | Data | local metadata, immutable image objects, revisions, backup/restore |
| RUN | Runtime | bootstrap, Docker, public/synthetic GPU boundary, local runtime |
| RSC | Research | dataset audits, leakage controls, metrics, reproducibility, claim ceiling |

Models and labeler depend on CTR, never on each other’s implementation. Local/private data and derived artifacts remain
on-premise. Public GPU accepts reviewed public/synthetic data only.

## Phase handoff

| Order | Canonical artifact | Gate | Next manual action |
|---|---|---|---|
| 01 | `docs/POC_MASTER_PLAN.md` | V3 direction | owner/architect review |
| 02 | `docs/R0_DATASET_SUPERVISION_FREEZE.md` | R0 V3 | PASS; scientific freeze complete |
| 03 | `docs/R1_P0_ACQUISITION_PREFLIGHT.md` | R1-P0 Global | BLOCKED on released-split duplicate leakage; runtime audit complete; IDRiD is deferred to R2/R3 |
| 04 | `docs/R1_GLOBAL_MODEL_SELECTION.md` | C0/C1/C2 | run one candidate at a time after R1-P0 |
| 05 | `docs/GUI_POC_INTEGRATION.md` | R4/R5 | integrate existing `templates/` through contracts |
| 06 | `docs/GPU_EXECUTION_TH.md` | public/synthetic runtime | verify host only when authorized |

No handoff command resets phase state or starts a later phase.
