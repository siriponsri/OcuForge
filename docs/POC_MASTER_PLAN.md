# OcuForge Research & POC Master Plan

<!-- plan_version: 3.0 -->

**Status:** AUTHORITATIVE V3 DIRECTION · R0 V3 PASS / R1-P0 READY_NOT_EXECUTED
**Scope:** Research and clinician-review foundation; not a diagnostic product.

This is the only active OcuForge roadmap. Historical plans and prior Eye Detected results remain available under
[`history/`](history/), but they do not define current phase status, model selection, or execution order.

## Direction in one page

OcuForge freezes public data, supervision, identity splits, licenses, and model-asset provenance before any model run.
Global diabetic-retinopathy grading and spatial ROI lesion classification are separate model tracks with separate
identities, supervision, heads, evaluation protocols, artifacts, and versions. Global predictions can inform a soft,
reviewable Global→ROI triage default; they never hard-disable ROI review and never turn MIL attention into a lesion mask.

The existing `templates/` DR Review Workspace is the customer-facing POC reference. Label Studio Community is the
internal ROI QA/HITL workbench. CVAT remains optional advanced annotation infrastructure. Public GPU is temporary
training/experiment compute for reviewed public or synthetic data only. Local/on-premise is authoritative for
inference, clinical integration, and all hospital/private data and derived artifacts.

## Current status

```text
R0_V3=PASS
R1_P0_ACQUISITION_PREFLIGHT=READY_NOT_EXECUTED
R1_THREE_CANDIDATE_BENCHMARK=READY_NOT_EXECUTED
CURRENT_R1_CHAMPION=NONE
HISTORICAL_PRIOR=AVAILABLE
PHASE_2B_LIVE_MONGO=UNRESOLVED
```

R0 V3 scientific evidence review is complete and recorded as `R0_DATASET_TAXONOMY=PASS`; no datasets or model weights
were downloaded, no model was trained, R1 was not executed, and no cloud provider was provisioned. Synthetic smoke
output is engineering evidence only. Post-download checks are explicitly deferred to R1-P0. The exact findings and
future manifest are in
[`RSC_R0_DATASET_TAXONOMY_FREEZE_v0.1.json`](RSC_R0_DATASET_TAXONOMY_FREEZE_v0.1.json).

## Canonical architecture

```text
PUBLIC RETINAL DATA
        |
        v
R0 DATA / SUPERVISION / SPLIT / LICENSE / PRETRAINING-OVERLAP FREEZE
        |
        +------------------------------+
        |                              |
        v                              v
R1 GLOBAL DR TRACK                 R2–R3 ROI LESION TRACK
ordinal grade 0–4                 verified spatial supervision
        |                              |
        v                              v
GLOBAL MODEL                       ROI LESION MODEL
        |                              |
        +--------------+---------------+
                       v
                 VERSIONED MODEL API
                 /                 \
                v                   v
       LABEL STUDIO CE       DR REVIEW WORKSPACE
       internal QA/HITL      customer-facing POC
                |
       optional CVAT advanced annotation

Later: R6 DICOM · R7 model diff/drift · R8 HL7/FHIR mapping/demo
```

## R0 - data and supervision freeze

R0 is a CPU/document/data-contract gate, not a training phase. It records the exact source/version/access method,
terms, modality, image characteristics, target semantics, supervision granularity, identity availability, released
splits, leakage limitations, taxonomy mapping, negative-ROI policy, checksums, file-selection manifest, task
eligibility, and candidate model asset/license status.

R0 also audits foundation-model pretraining overlap for C1 and C2: corpus description, known public datasets,
overlap status (`CONFIRMED`, `EXCLUDED`, `UNKNOWN`, or `POTENTIALLY_CONTAMINATED`), and the resulting claim ceiling.
An overlapping pretraining corpus cannot be described as a clean external-generalization test.

MMRDR-UWF remains the primary R1 domain hypothesis only if R0 verifies genuine ordinal grades 0–4, released
identity-safe split semantics, source/version/access, license compatibility, acceptable leakage risk, and usable image
access. Its image-level lesion fields are auxiliary presence labels only and cannot become ROI coordinates or masks.
IDRiD remains a spatial R2/R3 candidate and is outside the R1 critical path; its exact audit is required before that
track executes. DDR remains deferred for separate external anchoring only after its own exact audit.

R0 V3 passed on 2026-09-17. It establishes that the source/version, task/modality, label semantics, supervision,
released split limitations, leakage policy, taxonomy, conservative negative policy, license/access path, overlap claim
limits, future manifest, and exact C0/C1/C2 source revisions are scientifically defined. Archive hashes, extracted
inventories, schema smoke, preprocessing smoke, gated access, model loading, and storage/runtime checks belong to
[`R1_P0_ACQUISITION_PREFLIGHT.json`](R1_P0_ACQUISITION_PREFLIGHT.json).

## R1-P0 - acquisition preflight

R1-P0 is `READY_NOT_EXECUTED`. It is the only next gate. The allowed states are `READY_NOT_EXECUTED`, `RUNNING`,
`PASS_WITH_WARNINGS`, `PASS`, and `BLOCKED`. Training may unlock after `PASS` or `PASS_WITH_WARNINGS` only when no
blocking finding remains and all warnings are carried into R1 artifacts. `BLOCKED` is reserved for a finding that
invalidates the experiment, violates access/license/governance, creates leakage, uses corrupt/incompatible required
assets, or makes execution impossible. P0 must not execute R1, provision cloud compute, or silently substitute data
or model assets.

R1-P0 Global requires only MMRDR-UWF, the C0/C1/C2 assets, storage/runtime readiness, and preprocessing/model-load
checks. IDRiD acquisition, mask coverage, image-level split verification, and its conservative negative policy are
preserved for R2/R3 preparation and must not block R1 training.

## R1 — three architecture hypotheses

The active registry is [`r1-global-benchmark.json`](../eyes-detected-models/configs/research/r1-global-benchmark.json).
The target is genuine ordinal DR grade 0–4. Binary workflow values may be derived from a calibrated grade
distribution, such as `P(any DR) = 1 - P(grade 0)`, but binary `DR`/`no-DR` experience labels are never grades 0–4.

| ID | Hypothesis | Initial architecture | Initial objective |
|---|---|---|---|
| C0 | Compact supervised transfer control | ConvNeXt V2-Tiny, approximately 384 px when technically appropriate | 5-class CE |
| C1 | Retina-specialist representation | FLAIR image encoder, frozen/lightweight head first | 5-class CE |
| C2 | High-resolution local-detail hypothesis | DINOv3 ViT-B/16, high-resolution patches, learned Attention MIL | 5-class CE |

All three are compared with CE first. No current champion is selected in configuration. C0/C1/C2 run one at a time;
after R1-P0 reaches `PASS` or `PASS_WITH_WARNINGS` without a blocker and `RUNPOD_AUTOMATION_SMOKE` reaches `PASS` or
`PASS_WITH_WARNINGS`, an authorized unattended overnight run may continue from each validated checkpoint to the next
candidate.
Checkpoint validation covers metrics, errors, cost, asset provenance, and warnings. After C2, the run stops at the
comparison/calibration/error-analysis evidence freeze for the
mandatory OWNER/morning architecture-selection gate.

Every candidate must distinguish research execution eligibility from deployment license status. A deployment or
commercial restriction may remain a non-blocking warning for a research-eligible candidate. Scientific and deployment
champions are separate decisions and neither is configured before evidence.

After an architecture winner/finalist is chosen from validation evidence, the only planned ordinal ablation is:

```text
winner + CE  vs  winner + CORN
```

Existing CORAL code and synthetic coverage remain reusable legacy capability. CORAL is not an active initial R1
candidate. No loss or architecture benefit is claimed before execution.

Required R1 evidence includes QWK as the primary metric; macro F1; per-grade recall; balanced accuracy; confusion
matrix; support; calibration curve; ECE; Brier score; meaningful any-DR and moderate-or-worse metrics; clearly
defined AUROC/AUPRC; preprocessing and CPU latency; peak RAM; serialized size; GPU runtime/VRAM/cost; and model
loading time where useful. There is no invented composite score, fixed QWK tolerance, or automatic champion promotion.

## Global→ROI soft triage

The versioned contract is in `eyes-detected-contracts/src/eyes_contracts/triage.py` and the shared boundary is:

```text
IMAGE
  -> QC / GRADABILITY GATE
  -> GLOBAL DR MODEL
  -> CALIBRATION + UNCERTAINTY / OOD ASSESSMENT
  -> GLOBAL→ROI SOFT TRIAGE
```

The default may skip opening lesion review only when the image is in scope and gradable, grade 0 is predicted, a
validated calibration threshold is met, no QC/OOD trigger is present, and the grading protocol is known. The current
threshold is intentionally unset until calibration evidence exists. The UI may say “No DR predicted — lesion review
not automatically opened,” but ROI interaction remains available through `Accept`, `Mark Incorrect`, `Correct Grade`,
`Comment`, and `Inspect ROI Anyway`.

Any non-zero grade, low confidence, QC uncertainty, OOD flag, unknown protocol, or reviewer override opens/escalates
ROI review. `GLOBAL_NO_DR` is a global model semantic; `NO_SUPPORTED_LESION_IN_ROI` means only that supported lesion
classes did not cross the configured threshold inside the selected ROI.

## R2–R8 roadmap

- **R2:** split original identities first, then derive spatial ROIs with geometry/source/hash/preprocessing provenance
  and explicit negative provenance.
- **R3:** separate ROI lesion classifier with supported classes `MICROANEURYSM`, `INTRARETINAL_HEMORRHAGE`,
  `HARD_EXUDATE`, `SOFT_EXUDATE`, and `NO_SUPPORTED_LESION_IN_ROI`. It is not MIL attention.
- **R4:** Label Studio Community internal workflow: model suggestion → confirm/correct/reject/escalate; no paid plugin.
- **R5:** integrate the existing `templates/` DR Review Workspace through contracts/adapters; do not replace it.
- **R6:** DICOM after model/workflow stability.
- **R7:** version, input, feature, prediction, and label-dependent performance/calibration drift as separate concerns.
- **R8:** HL7/FHIR mapping/demo only; no HIS compatibility claim without real integration testing.

## Deployment and governance boundary

GitHub stores code, safe configs/manifests, model metadata, hashes, reports, and synthetic fixtures. Public GPU may
hold reviewed public/synthetic training, extraction, and experiment artifacts temporarily. RunPod/Vast are optional
providers, not deployment or production storage. Local/on-premise owns authoritative inference, model archives,
clinical APIs, and all private images, labels, embeddings, predictions, checkpoints, backups, and derived artifacts.
Vercel is limited to a public/synthetic demo frontend or measured light inference and is not the clinical authority.

The system is research-only. It does not diagnose, refer, claim clinical utility, or claim OCT-confirmed DME from
fundus/UWF evidence. DME remains a separate axis. Model attention is aggregation evidence, not validated lesion
localization.

## Reading order and document classification

1. This plan.
2. [R0 protocol](R0_DATASET_SUPERVISION_FREEZE.md), [R1 protocol](R1_GLOBAL_MODEL_SELECTION.md), and the
   [implementation status](IMPLEMENTATION_STATUS.md).
3. [Module contract](CTR_MODULE_CONTRACT.md), [GUI integration](GUI_POC_INTEGRATION.md), and
   [GPU boundary](GPU_EXECUTION_TH.md).
4. [Diagrams](DIAGRAM_DESIGN.md) and the generated assets under `docs/diagrams/`.
5. Historical evidence under `history/` only for prior context; never as current R1 evidence.

Document status is tracked in [DOCUMENT_STATUS.md](DOCUMENT_STATUS.md). A document may be `AUTHORITATIVE`,
`ACTIVE_SUPPORTING`, or `HISTORICAL`; an `OBSOLETE` document is removed rather than left to conflict with this plan.

## Execution gate

The next permitted manual action is to execute the R1-P0 acquisition preflight. Do not train, execute R1, provision a
cloud provider, or promote a model until P0 passes. After P0 reaches `PASS` or `PASS_WITH_WARNINGS` without a blocker,
and `RUNPOD_AUTOMATION_SMOKE` reaches `PASS` or `PASS_WITH_WARNINGS`, the authorized unattended overnight run may
execute C0, C1,
and C2 in order with validated checkpoints between candidates. It must stop at the evidence freeze for the mandatory
OWNER/morning architecture-selection gate; no champion is selected and no CE-vs-CORN ablation is authorized by this
overnight continuation.
