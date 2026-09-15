# OcuForge Project Map

This page is the short human handoff map for OcuForge. It explains where work belongs and which gate is current.
The normative rules are in [CTR_MODULE_CONTRACT.md](CTR_MODULE_CONTRACT.md); this page does not replace them.

## What OcuForge Is

OcuForge is a research and clinician-review foundation for retinal imaging workflows. It preserves shared
contracts, model research, annotation review, and local data governance. It is not a diagnostic product.

## Module Map

| ID | Module | Responsibility | Primary location / runtime |
|---|---|---|---|
| CTR | CONTRACTS | Schemas, protocols, provenance, validators, shared interfaces | `eyes-detected-contracts/` |
| MDL | MODELS | Encoders, training, inference, evaluation, model evidence | `eyes-detected-models/` |
| LBL | LABELER | CVAT integration, clinician review, correction, adjudication, export | `eyes-detected-labeler/` |
| DAT | DATA | Local image objects, Mongo metadata, revisions, releases, backup/restore | `labeler_bridge/storage.py`, `deploy/onprem/` |
| RUN | RUNTIME | Bootstrap, Docker/Compose, deployment, environment and execution boundaries | `bootstrap.cmd`, `scripts/`, `deploy/`, `.codex/` |
| RSC | RESEARCH | Experiments, leakage controls, metrics, reproducibility, evidence claims | `docs/`, `validation/`, experiment configuration |

Physical directories and architectural ownership are not identical. For example, DATA implementation currently
shares the labeler package because it is exposed through explicit storage/workflow interfaces.

Modules define stable architectural ownership. Phases define execution order and current project progress.

## Dependency Direction

```text
                         CTR / CONTRACTS
                       /        |        \\
                      v         v         v
                 MDL / MODELS  LBL / LABELER  DAT / DATA
                      |         |         |
                      +---------+---------+----> RSC / RESEARCH

RUN / RUNTIME executes modules and configures boundaries; it does not redefine their semantics.
MDL and LBL exchange versioned contracts or artifacts, never implementation imports.
```

Allowed implementation dependencies are `MODELS -> CONTRACTS`, `LABELER -> CONTRACTS`, and `DATA -> CONTRACTS`.
`MODELS -> LABELER` and `LABELER -> MODELS` implementation dependencies are forbidden. Cross-module behavior uses
shared contracts, versioned artifacts, explicit interfaces, or documented adapters.

## Runtime And Data Boundaries

GitHub may contain code, schemas, configuration templates, documentation, tests, synthetic fixtures, and public
references. Hospital images, clinical labels, patient linkage, hospital-derived features or embeddings, private
predictions, annotation revisions, hospital-trained checkpoints, backups, and credentials remain local/on-premises.

`PUBLIC_GPU` (Vast/RunPod) may use only explicitly reviewed public datasets, synthetic data, public model weights with
reviewed terms, and public/synthetic derived artifacts. It is not an extension of the hospital network. No module
may silently upload private data or provision cloud resources.

## Current Phase And Gate Status

| Work item | Status |
|---|---|
| Phase 0 - Repository foundation | PASS |
| Phase 1 - Baseline / portability | PASS |
| Machine bootstrap | PASS |
| Phase 2A - Docker-independent local data foundation | PASS |
| Phase 2B - Live MongoDB acceptance | PENDING / NOT RUN |

Phase 2A passing does not mean that Phase 2 overall has passed.

## Where Should I Work?

| Work type | Module |
|---|---|
| Contract, schema, or protocol | CTR |
| Model, training, or evaluation | MDL |
| CVAT or annotation workflow | LBL |
| Mongo, image, or release store | DAT |
| Docker, Vast, bootstrap, or runtime | RUN |
| Experiment, metric, or leakage control | RSC |

For cross-module changes, identify the primary module, check the shared contract impact, and read
[CTR_MODULE_CONTRACT.md](CTR_MODULE_CONTRACT.md) before editing.

## Human Entry Points

Run these commands from the repository root:

| Entry point | Use |
|---|---|
| `bootstrap.cmd` | Reconstruct and verify the normal Windows developer environment. |
| `02_phase2_local_data.cmd` | Run the synthetic-only Phase 2B live-Mongo gate on a Docker-capable machine. CVAT stays off. |
| `python -m pytest` | Run the offline test suite after bootstrap. |
| `python scripts/synthetic_roundtrip.py` | Run the synthetic research/annotation roundtrip; it does not prove clinical performance. |
| `deploy/onprem/README.md` | Read the local on-prem manual handoff and Phase 2B prerequisites. |

## Current Next Action

Run `02_phase2_local_data.cmd` on a Docker-capable machine. It must report the live Mongo acceptance result before
the team claims Phase 2B complete. Do not start CVAT or use hospital data as part of this synthetic gate.
