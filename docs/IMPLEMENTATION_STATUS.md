# Implementation status — v0.2

The v0.1 foundation is extended with MongoDB/local-object adapters, durable CVAT task lifecycle,
immutable review
snapshots, and feature extraction/training/resume/evaluation commands. The current POC direction is
model-first interactive lesion classification; see
[POC_MASTER_PLAN_INTERACTIVE_LESION.md](POC_MASTER_PLAN_INTERACTIVE_LESION.md)
for the authoritative sequence. See validation/FINAL_DELIVERY_REPORT.md for current evidence.

Current gates: Phase 0 - Repository foundation: PASS; Phase 1 - Baseline / portability: PASS; machine bootstrap: PASS;
Phase 2A - Docker-independent local data foundation: PASS; Phase 2B - Live MongoDB acceptance:
PENDING / NOT RUN; R0 / MDL - Dataset + Lesion Taxonomy Freeze: PASS;
R1 / B1 - Global public baseline: READY / NOT EXECUTED.
Phase 2A passing does not mean that Phase 2 overall has passed.

Implemented: shared contracts, geometry/provenance, ICO protocol, binary experience semantics, synthetic tests, local Mongo repository, compare-and-swap, document backup/restore integrity, local image hash ingestion, trusted operator CLI, CVAT task/reconciliation/import/export/finalize workflow, frozen DINO adapter, binary/ordinal MIL training scripts, global-average B1 pooling, held-out evaluation, R0/R1 validation, and public-only Vast/RunPod launch adapters.

Not verified on target services: MongoDB authentication/volumes/restore drill, CVAT live import/edit/export and clinician usability, Docker build/runtime, GPU/DINO real weights, server firewall/TLS and clinical access governance. A mocked repository does not certify MongoDB server operations.

Not implemented: execution of the real global B1 run, ROI model baseline, Label Studio Community ROI QA integration,
customer-facing interactive GUI, enterprise IAM, automatic amendment UI, full clinical
calibration/metrics/validation, trained lesion localization, adaptation training,
automatic public dataset downloads or cloud transfers. Existing CVAT workflow remains
retained infrastructure; it is not deleted or migrated. Vercel clinical deployment is
excluded by the user's on-premises requirement.

R0 evidence and decisions are in [RSC_R0_DATASET_TAXONOMY_FREEZE_v0.1.json](RSC_R0_DATASET_TAXONOMY_FREEZE_v0.1.json).
MMRDR is the reviewed global source; IDRiD remains local-audit-only for now. R1 storage uses configurable
`OCUFORGE_DATA_ROOT`, `OCUFORGE_MODEL_ROOT`, `OCUFORGE_CACHE_ROOT`, and `OCUFORGE_ARTIFACT_ROOT` values.
RunPod Network Volume is the preferred persistent public-data option, but no provider is required by the code.

The repository is live at https://github.com/siriponsri/OcuForge. Remote publication and local validation are reported
separately; live MongoDB, CVAT, Docker, and GPU acceptance remain external gates.
