# Implementation status — v0.2 / V2 replan

The v0.1 foundation is extended with MongoDB/local-object adapters, durable CVAT task lifecycle,
immutable review
snapshots, and feature extraction/training/resume/evaluation commands. The current POC direction is the
evidence-driven two-track plan; see [POC_MASTER_PLAN_V2.md](POC_MASTER_PLAN_V2.md) for the authoritative
sequence. See validation/FINAL_DELIVERY_REPORT.md for current evidence.

Current gates: Phase 0 - Repository foundation: PASS; Phase 1 - Baseline / portability: PASS; machine bootstrap: PASS;
Phase 2A - Docker-independent local data foundation: PASS; Phase 2B - Live MongoDB acceptance:
PENDING / NOT RUN; R0 V2 - Dataset, Supervision, Taxonomy and Split Audit: READY TO EXECUTE / NOT PASSED;
R1 G0-G5 - Global model benchmark: READY / NOT EXECUTED.
Phase 2A passing does not mean that Phase 2 overall has passed.

Implemented: shared contracts, geometry/provenance, ICO protocol, binary experience semantics, synthetic tests, local Mongo repository, compare-and-swap, document backup/restore integrity, local image hash ingestion, trusted operator CLI, CVAT task/reconciliation/import/export/finalize workflow, frozen DINO adapter, binary/ordinal MIL training scripts, global-average pooling candidate, held-out evaluation, R0/R1 readiness validation, and public-only Vast/RunPod launch adapters. The existing static GUI reference is registered under `templates/`.

Not verified on target services: MongoDB authentication/volumes/restore drill, CVAT live import/edit/export and clinician usability, Docker build/runtime, GPU/DINO real weights, server firewall/TLS and clinical access governance. A mocked repository does not certify MongoDB server operations.

Not implemented: execution of the real R1 G0-G5 benchmark, ROI model baseline, Label Studio Community ROI QA integration,
customer-facing interactive GUI, enterprise IAM, automatic amendment UI, full clinical
calibration/metrics/validation, trained lesion localization, adaptation training,
automatic public dataset downloads or cloud transfers. Existing CVAT workflow remains
retained infrastructure; it is not deleted or migrated. The authoritative local Model API and production
inference integration remain future work. Vercel public/synthetic demo deployment is also future work; it must not become a
clinical inference or production storage environment.

R0 candidate evidence and decisions are in [RSC_R0_DATASET_TAXONOMY_FREEZE_v0.1.json](RSC_R0_DATASET_TAXONOMY_FREEZE_v0.1.json),
with the acceptance protocol in [R0_DATASET_SUPERVISION_FREEZE.md](R0_DATASET_SUPERVISION_FREEZE.md). MMRDR is a
candidate global source; IDRiD remains local-audit-only for now. R1 storage uses configurable
`OCUFORGE_DATA_ROOT`, `OCUFORGE_MODEL_ROOT`, `OCUFORGE_CACHE_ROOT`, and `OCUFORGE_ARTIFACT_ROOT` values.
RunPod/Vast are possible temporary public/synthetic training, feature-extraction, and experiment environments; an
optional persistent volume is a workspace/cache, not authoritative deployment or production storage. No provider is
required by the code. The R1 benchmark definition is [R1_GLOBAL_MODEL_SELECTION.md](R1_GLOBAL_MODEL_SELECTION.md);
no candidate is a predetermined champion. R1/R3 selection must include CPU inference latency, peak RAM, model
size, preprocessing latency, and GPU training cost alongside scientific metrics.

The repository is live at https://github.com/siriponsri/OcuForge. Remote publication and local validation are reported
separately; live MongoDB, CVAT, Docker, and GPU acceptance remain external gates.
