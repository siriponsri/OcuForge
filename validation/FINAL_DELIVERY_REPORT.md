# FINAL DELIVERY REPORT — v0.2

Overall status: **PARTIAL — offline implementation gates pass; live deployment gates remain open**

Release: eyes-detected-dual-track-starter-v0.2 · Date: 2026-09-09

This release extends the earlier v0.1 starter. The historical work-package Markdown and all 12 supplied Markdown files were read before implementation. Subsequent user requirements take precedence: ICO 2017 is the versioned grading reference; local DR/no-DR assessments are binary doctor-experience labels; all hospital images, labels, derived features/checkpoints and backups stay on-premises. GitHub is the target code source of truth, with no hospital data in the repository.

The current planning authority is [POC_MASTER_PLAN_V2.md](../docs/POC_MASTER_PLAN_V2.md). The V2 reconciliation
status is `R0_V2=READY_TO_EXECUTE` and `R1_GLOBAL_BENCHMARK=READY_NOT_EXECUTED`; this report's implementation
evidence must not be read as proof that either research gate has passed. The customer-facing GUI reference is
the static package under `templates/`.

## V2 reconciliation gate — 2026-09-16

The repository was reconciled to the evidence-driven V2 plan without downloading data, provisioning a provider,
running DINOv3, or training a model. The current machine-readable statuses are `R0_V2=READY_TO_EXECUTE` and
`R1_GLOBAL_BENCHMARK=READY_NOT_EXECUTED`. The commands run for this reconciliation were: 94 pytest tests passed;
Ruff passed; configuration validation passed for 25 files; the package file gate passed for 283 files; and
`git diff --check` passed. The historical delivery results below remain evidence for the earlier starter release.

## Delivered implementation

- Three independent packages with seven shared versioned contracts, geometry/provenance validation and split safeguards. Models and labeler import shared contracts, not each other.
- Existing CVAT bridge and clinical guides plus durable task registration, creation intent/reconciliation, local share hash verification, frame/label mapping, idempotent prediction import, explicit review journal, immutable export snapshots and expert finalization.
- Local MongoDB adapter: optimistic concurrency, immutable annotation revisions, integrity-checked document backup/restore into an empty database. Tests use mongomock; this is not a live MongoDB certification.
- Local content-addressed image store and ingest CLI; authenticated MongoDB Compose with no published database port. CVAT keeps its own PostgreSQL and volumes. `eyes-local` is a trusted operator CLI; CVAT is the clinician UI. No new multi-user web editor or enterprise IAM is claimed.
- Thai NoSQL plan covering schema, protocol versions, local NAS/disk objects, PHI boundaries, capacity estimates, encryption, access control, retention decisions and consistent full-system backup/restore.
- Dataset/image audit, local frozen-encoder extraction, metadata-checked feature cache, binary or ordinal Attention MIL training, VAL-based checkpoint selection, matching-config resume, held-out evaluation and versioned model/prediction export.
- Real synthetic CPU execution for both binary and ordinal pipelines. No automatic conversion from binary experience to ordinal or lesion labels. Attention is evidence, not lesion localization. Auxiliary outputs without verified supervision are not exported as trained probabilities.
- Vast/RunPod Dockerfile, GPU Compose and in-container launcher. The public-cloud zone requires eligible public/synthetic manifests even when the operator omits --cloud. No provisioning or transfer operation.
- Professional README, minimal SVG logo, workflow diagram, Thai runbooks and commit-ready source.

## Tests and evidence

| Check | Result | Evidence |
|---|---|---|
| Unit/schema/model/geometry/provenance/storage/workflow tests | **86 passed**, 0 failed | pytest.txt |
| Final model-manifest change | **4 pipeline tests passed**, 0 failed | pipeline-regression.txt |
| Ruff | PASS | lint.txt |
| Configuration validation | PASS: 22 files plus protocol/patch checks | configs.txt |
| Synthetic CPU roundtrip | PASS, 10 images; 5 optimizer steps; weights changed | smoke.txt |
| Local operator and model pipeline CLI | PASS help parsing/imports | local-cli.txt, pipeline-cli.txt |
| Mongo concurrency and backup/restore | PASS mocked repository; corrupt revision rejected | test_local_storage.py |
| CVAT task/import/review/finalize | PASS API-shaped fake; retry avoids duplicate suggestions | test_local_storage.py |
| Binary + ordinal train/resume/evaluate | PASS synthetic CPU; no clinical inference | test_pipeline.py |
| Docker executable/build/runtime | NOT RUN: executable/daemon unavailable | external-validation.txt |
| Live MongoDB/CVAT/TLS/firewall/restore drill | NOT RUN: target services unavailable | external-validation.txt |
| Actual DINO weights and CUDA execution | NOT RUN: no approved weights/GPU used | external-validation.txt |
| GitHub push | BLOCKED: HTTP 403 Resource not accessible by integration | GITHUB_HANDOFF_TH.md |

Synthetic loss 0.857662 → 0.792030 is an engineering diagnostic, not medical performance. Tests block outbound socket connections. Source packages target Python 3.11–3.12; tested on Python 3.12, torch 2.5.1+cpu, NumPy 2.3.5, Pydantic 2.13.5, Pillow 12.3.0, PyYAML 6.0.3, PyMongo 4.13.2 and mongomock 4.3.0. Direct dependencies are pinned; a full transitive/OS lock is not claimed.

## Final Delivery Gate

| Required gate | Result |
|---|---|
| Inspect every distributable file | PASS: UTF-8, Python/JSON parsing, file/path/type allowlist |
| Tests and included linter | PASS |
| Config validators | PASS static; Docker runtime remains open |
| Synthetic smoke | PASS |
| Secrets check | PASS common credential patterns and reviewed generated content |
| Raw medical data check | PASS: no hospital data; only allowlisted public GUI demonstration assets are included |
| Large training/model artifact check | PASS; no checkpoint/features/binary training outputs in archive |
| ZIP structure and content | See ZIP_STRUCTURE.txt: CRC, unique safe paths, required files and exact source hashes |
| Final report | This document |

The archive excludes caches, .git, credentials, local-state, raw images, model weights and generated run artifacts. Code/config/docs and synthetic text fixtures only are distributable. No hospital images were downloaded from Drive or sent to an external service. Google Drive/Hugging Face/Vercel were not used as clinical storage. No paid instance was provisioned.

## Remaining scope and honest limits

Before hospital use: install and test real MongoDB/CVAT, verify the exact Docker image/UID/secret permissions, mount the same read-only image share, test clinician review end-to-end, approve ICO protocol/SOP, enforce role access and local HTTPS/egress controls, and complete a consistent full-system restore drill. Application document backup alone does not restore CVAT or images.

Before public GPU research: verify exact public model/dataset licenses and artifacts, record runtime image digest and git SHA, validate official DINO dependencies/CUDA on the target host, then run an explicitly approved experiment. No trained lesion detector, adaptation experiment, clinical calibration, main benchmark or clinical validation is claimed.

GitHub repository writes were authorized by the user but rejected by the integration. A local commit is supplied as a handoff; no remote commit, push or Vercel deployment is claimed. The v0.1 deliverable is preserved separately. The new ZIP is the v0.2 continuation, not a silent replacement of the earlier archive.
