# Implementation status — v0.2

The v0.1 foundation is extended with MongoDB/local-object adapters, durable CVAT task lifecycle,
immutable review
snapshots, and feature extraction/training/resume/evaluation commands. The current POC direction is
model-first interactive lesion classification; see
[POC_MASTER_PLAN_INTERACTIVE_LESION.md](POC_MASTER_PLAN_INTERACTIVE_LESION.md)
for the authoritative sequence. See validation/FINAL_DELIVERY_REPORT.md for current evidence.

Current gates: Phase 0 - Repository foundation: PASS; Phase 1 - Baseline / portability: PASS; machine bootstrap: PASS;
Phase 2A - Docker-independent local data foundation: PASS; Phase 2B - Live MongoDB acceptance:
PENDING / NOT RUN;
R0 / MDL - Dataset + Lesion Taxonomy Freeze: PENDING.
Phase 2A passing does not mean that Phase 2 overall has passed.

Implemented: shared contracts, geometry/provenance, ICO protocol, binary experience semantics, synthetic tests, local Mongo repository, compare-and-swap, document backup/restore integrity, local image hash ingestion, trusted operator CLI, CVAT task/reconciliation/import/export/finalize workflow, frozen DINO adapter, binary/ordinal MIL training scripts, held-out evaluation and public-only Vast/RunPod launch adapters.

Not verified on target services: MongoDB authentication/volumes/restore drill, CVAT live import/edit/export and clinician usability, Docker build/runtime, GPU/DINO real weights, server firewall/TLS and clinical access governance. A mocked repository does not certify MongoDB server operations.

Not implemented: global/ROI model baselines for the new POC, Label Studio Community ROI QA integration,
customer-facing interactive GUI, enterprise IAM, automatic amendment UI, full clinical
calibration/metrics/validation, trained lesion localization, adaptation training,
automatic public dataset downloads or cloud transfers. Existing CVAT workflow remains
retained infrastructure; it is not deleted or migrated. Vercel clinical deployment is
excluded by the user's on-premises requirement.

The repository is live at https://github.com/siriponsri/OcuForge. Remote publication and local validation are reported
separately; live MongoDB, CVAT, Docker, and GPU acceptance remain external gates.
