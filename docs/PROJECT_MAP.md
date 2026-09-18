# OcuForge project map

**Status:** ACTIVE SUPPORTING HANDOFF
**Authority:** [`POC_MASTER_PLAN.md`](POC_MASTER_PLAN.md)

OcuForge is a research and clinician-review foundation, not a diagnostic product. The current gate is R0 V3 `PASS`;
R1-P0 is `BLOCKED` by two exact MMRDR duplicate-content groups crossing the released train/test split; R1 is
`READY_NOT_EXECUTED` with no champion. Do not train, reshuffle the released split, or silently exclude rows until the
owner resolves the leakage protocol and P0 reaches `PASS` or `PASS_WITH_WARNINGS` with no blocker.

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
| 03 | `docs/R1_P0_ACQUISITION_PREFLIGHT.md` | R1-P0 Global | BLOCKED on released-split duplicate leakage; owner review required; IDRiD is deferred to R2/R3 |
| 04 | `docs/R1_GLOBAL_MODEL_SELECTION.md` | C0/C1/C2 | run one candidate at a time after R1-P0 |
| 05 | `docs/GUI_POC_INTEGRATION.md` | R4/R5 | integrate existing `templates/` through contracts |
| 06 | `docs/GPU_EXECUTION_TH.md` | public/synthetic runtime | verify host only when authorized |

No handoff command resets phase state or starts a later phase.
