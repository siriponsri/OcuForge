# OcuForge Module Contract

**Status:** Normative repository architecture contract
**Scope:** Repository-wide module boundaries, ownership, dependency rules, runtime/data boundaries, and file-naming guidance
**Project:** OcuForge / Eyes Detected
**Applies to:** Humans, Codex/Luna agents, local development, on-prem deployment, and public/synthetic GPU workflows

---

## 1. Purpose

This document defines the stable **module structure** of OcuForge.

A **module** describes a long-lived architectural responsibility.
A **phase** describes the current execution order of project work.

They are intentionally different:

- Modules should remain relatively stable across the lifetime of the repository.
- Phases may change, split, pause, or be reordered.
- A phase may touch more than one module.
- The existence of another module does **not** authorize work outside the current phase.

The primary goal is to let multiple contributors or agents work in parallel without creating hidden coupling between model research, clinician annotation, local data storage, runtime infrastructure, and research governance.

---

## 2. Canonical Module IDs

Use these six canonical module IDs in plans, issues, handoffs, specifications, and architecture discussions.

| Module ID | Short code | Primary responsibility |
|---|---:|---|
| `CONTRACTS` | `CTR` | Shared schemas, protocols, provenance, validation, interface contracts |
| `MODELS` | `MDL` | Encoders, feature extraction, MIL/CORAL, training, inference, evaluation |
| `LABELER` | `LBL` | CVAT integration, clinician review, correction, adjudication, annotation export |
| `DATA` | `DAT` | Local/on-prem metadata, immutable image objects, revisions, releases, backup/restore |
| `RUNTIME` | `RUN` | Docker, local deployment, GPU execution, environment/bootstrap, public-cloud execution boundaries |
| `RESEARCH` | `RSC` | Research design, dataset manifests, leakage controls, baselines, metrics, reproducibility, evidence claims |

Do **not** use `M1`, `M2`, etc. as module names because those labels are easily confused with roadmap milestones and phases.

---

## 3. Module Contracts

### 3.1 `CONTRACTS` — Shared Interfaces

**Canonical code:** `CTR`

**Owns**

- versioned schemas;
- protocol identity and hashes;
- provenance structures;
- annotation/prediction/image manifest contracts;
- shared validators;
- split and semantic validation rules;
- immutable meaning of labels and protocol references.

**Current primary area**

```text
eyes-detected-contracts/
```

**May depend on**

- standard/runtime libraries required to implement the contracts.

**Must not depend on**

- `MODELS`;
- `LABELER`;
- `DATA` implementation;
- `RUNTIME` deployment implementation.

**Key rule**

`CONTRACTS` is the interface source of truth. Other modules may consume it, but should not redefine competing versions of the same shared semantic object.

---

### 3.2 `MODELS` — Model Research and Evaluation

**Canonical code:** `MDL`

**Owns**

- retinal encoders;
- DINOv3 adapters;
- feature extraction;
- patch/grid processing;
- MIL aggregation;
- ordinal heads such as CORAL;
- binary/multilabel heads where semantically valid;
- training loops;
- checkpoint handling;
- prediction generation;
- model-side evaluation;
- active-learning/OOD research utilities;
- model evidence generation.

**Current primary area**

```text
eyes-detected-models/
```

**May depend on**

```text
MODELS -> CONTRACTS
```

**Must not depend on**

```text
MODELS -X-> LABELER implementation
```

**Important semantic constraints**

- Local binary `DR / no-DR` doctor-experience labels must not be silently converted into ordinal grade `0-4`.
- MIL attention is aggregation evidence, not validated lesion localization.
- Model outputs are research outputs, not diagnoses.
- Hospital-derived features/checkpoints remain local/on-prem.

---

### 3.3 `LABELER` — Clinician Annotation Workflow

**Canonical code:** `LBL`

**Owns**

- CVAT integration;
- annotation task creation/synchronization;
- prediction suggestion import;
- geometry conversion;
- clinician correction workflow;
- adjudication;
- annotation revision history;
- annotation export;
- review provenance;
- labeling UX integration.

**Current primary area**

```text
eyes-detected-labeler/
```

**May depend on**

```text
LABELER -> CONTRACTS
```

**Must not depend on**

```text
LABELER -X-> MODELS implementation
```

Predictions reach the labeler through shared contracts or exported artifacts, not by importing model internals.

**Important semantic constraints**

- AI suggestions are not ground truth.
- Missing lesion annotation does not mean confirmed absence of a lesion.
- DME remains a separate assessment axis.
- Fundus/UWF alone must not be described as OCT-confirmed DME.

---

### 3.4 `DATA` — Local Data and Release Foundation

**Canonical code:** `DAT`

**Owns**

- local/on-prem MongoDB document storage;
- immutable image/object storage;
- SHA-256 content identity;
- annotation revisions;
- workflow persistence;
- dataset release manifests;
- backup/restore design;
- patient-group split integrity;
- release immutability;
- local data lifecycle.

**Current primary areas**

```text
eyes-detected-labeler/src/labeler_bridge/storage.py
eyes-detected-labeler/src/labeler_bridge/workflow.py
deploy/onprem/
docs/ON_PREMISE_NOSQL_PLAN_TH.md
```

The code may currently reside partly inside the labeler package. That does not change the architectural responsibility defined here.

**May depend on**

```text
DATA -> CONTRACTS
```

**May integrate with**

```text
DATA <-> LABELER
```

through explicit storage/workflow interfaces.

**Must not**

- upload hospital/private data to cloud services;
- use public GPU infrastructure for hospital data;
- treat pseudonymization alone as permission to move data off-prem;
- silently overwrite immutable image objects or locked annotation revisions.

---

### 3.5 `RUNTIME` — Environment, Deployment, and Compute Execution

**Canonical code:** `RUN`

**Owns**

- developer bootstrap;
- Docker/Compose runtime;
- on-prem deployment configuration;
- service health checks;
- local secret wiring;
- environment validation;
- public/synthetic GPU execution adapters;
- Vast.ai / RunPod launch boundaries;
- reproducible runtime configuration.

**Current primary areas**

```text
bootstrap.cmd
scripts/bootstrap_windows.ps1
deploy/onprem/
deploy/vast/
.codex/
.codex.example/
```

**Runtime classes**

```text
LOCAL_DEV
ON_PREM_CLINICAL
PUBLIC_GPU
CI_OFFLINE
```

**Cloud rule**

`PUBLIC_GPU` may receive only:

- public datasets explicitly reviewed for cloud eligibility;
- synthetic data;
- public model weights with reviewed terms;
- non-private configuration/code.

It must never receive:

- hospital images;
- hospital labels;
- hospital-derived features;
- hospital-trained checkpoints;
- private credentials;
- patient linkage data.

---

### 3.6 `RESEARCH` — Research Control and Scientific Claims

**Canonical code:** `RSC`

**Owns**

- research questions;
- hypotheses;
- dataset selection rationale;
- leakage audits;
- baseline definitions;
- ablations;
- metric selection;
- statistical validation;
- experiment manifests;
- reproducibility records;
- novelty/prior-art analysis;
- claim ceilings;
- scientific interpretation.

**Current primary areas**

```text
docs/
validation/
experiment/run configuration
dataset manifests
research plans
```

**May consume outputs from**

```text
CONTRACTS
MODELS
DATA
RUNTIME
LABELER
```

but should not silently mutate their implementation contracts.

**Key rule**

Engineering success, benchmark performance, generalization, and clinical utility are separate evidence levels and must not be conflated.

---

## 4. Dependency Contract

The intended dependency direction is:

```text
                 CONTRACTS
                 /   |   \
                /    |    \
               v     v     v
            MODELS  DATA  LABELER
               \      |      /
                \     |     /
                 v    v    v
                  RESEARCH

RUNTIME supports execution of all modules,
but must not redefine their semantics.
```

Hard rules:

```text
MODELS   -> CONTRACTS      ALLOWED
LABELER  -> CONTRACTS      ALLOWED
DATA     -> CONTRACTS      ALLOWED

MODELS   -> LABELER        FORBIDDEN
LABELER  -> MODELS         FORBIDDEN

RUNTIME  -> semantic redefinition    FORBIDDEN
RESEARCH -> silent contract mutation FORBIDDEN
```

When cross-module behavior is required, prefer:

1. shared contract/schema;
2. exported versioned artifact;
3. explicit service/storage interface;
4. documented adapter.

Avoid direct imports across implementation modules.

---

## 5. Data Boundary Contract

### 5.1 GitHub-eligible

```text
source code
schemas
configuration templates
documentation
synthetic fixtures
tests
public references
non-secret manifests
```

### 5.2 On-prem/local only

```text
hospital images
clinical labels
patient linkage
hospital-derived features
hospital-derived embeddings
hospital-trained checkpoints
private predictions
private annotation revisions
backups
credentials/secrets
```

### 5.3 Public GPU eligible

```text
explicitly reviewed public datasets
synthetic datasets
public model weights
public/synthetic features
public/synthetic checkpoints
non-private experiment configuration
```

`Vast.ai` and `RunPod` are `PUBLIC_GPU`, not extensions of the hospital network.

---

## 6. File Naming Contract

### 6.1 Do not prefix every source file

Internal Python modules should remain idiomatic:

```text
storage.py
workflow.py
training.py
evaluation.py
validators.py
```

Do **not** rename normal source files into names such as:

```text
DAT_storage.py
MDL_training.py
```

unless there is a specific technical reason.

Module prefixes are most useful for **cross-project artifacts** where ownership would otherwise be unclear.

### 6.2 Recommended prefixes for project-level artifacts

Use:

```text
CTR_  -> CONTRACTS
MDL_  -> MODELS
LBL_  -> LABELER
DAT_  -> DATA
RUN_  -> RUNTIME
RSC_  -> RESEARCH
```

Examples:

```text
docs/CTR_SCHEMA_CHANGE_POLICY.md
docs/MDL_DINOV3_BASELINE_PLAN.md
docs/LBL_CVAT_WORKFLOW.md
docs/DAT_LOCAL_RELEASE_POLICY.md
docs/RUN_VAST_EXECUTION.md
docs/RSC_EXPERIMENT_001.md
```

For files intended to span multiple modules, use a descriptive project-level name rather than concatenating many prefixes:

```text
docs/PROJECT_MAP.md
docs/CTR_MODULE_CONTRACT.md
docs/SAFETY_AND_SCOPE.md
```

### 6.3 Existing files

These naming rules apply to **new artifacts**. Existing files should not be mass-renamed solely for consistency.

### 6.4 Optional structured experiment naming

For research artifacts:

```text
RSC_<study-or-experiment>_<artifact>_v<major>.<minor>.<ext>
```

Examples:

```text
RSC_DR_MIL_BASELINE_PLAN_v0.1.md
RSC_DR_MIL_ABLATION_MATRIX_v0.1.csv
RSC_DR_MIL_RESULTS_v0.1.json
```

For model configs:

```text
MDL_<task>_<architecture>_<purpose>_v<major>.<minor>.json
```

Example:

```text
MDL_DR_DINOV3_ATTENTION_MIL_TRAIN_v0.1.json
```

For data/release artifacts:

```text
DAT_<dataset-or-release>_<artifact>_v<major>.<minor>.<ext>
```

Examples:

```text
DAT_DDR_SPLIT_MANIFEST_v1.0.jsonl
DAT_LOCAL_RELEASE_2026Q3_v1.0.json
```

---

## 7. Phase vs Module Naming

Use this format when defining work:

```text
Phase 2A — Local Data Foundation
Primary module: DATA
Supporting module: RUNTIME
```

Example:

```text
Phase 5 — Public GPU Model Experiments
Primary module: MODELS
Supporting modules: RUNTIME, RESEARCH
```

This keeps execution order separate from architecture ownership.

---

## 8. Change Ownership Rule

Before editing, identify:

```text
Primary module:
Secondary module(s):
Shared contract affected: yes/no
Clinical/data semantics affected: yes/no
Runtime boundary affected: yes/no
```

If more than one primary module appears necessary, split the work unless the integration itself is the explicit objective.

A change to shared semantics should normally begin in `CONTRACTS`, then propagate outward.

---

## 9. Agent Contract

All coding/research agents should follow this sequence:

1. Read root `AGENTS.md`.
2. Identify the current phase/gate.
3. Identify the primary module using this document.
4. Inspect the implementation and tests owned by that module.
5. Check whether a shared contract is affected.
6. Make the smallest bounded change.
7. Run the relevant acceptance gate.
8. Stop before entering another phase/module without explicit authorization.

Agents must not broaden scope merely because adjacent modules exist.

---

## 10. Current OcuForge Mapping

A practical mapping of the present repository:

```text
OcuForge/
├─ eyes-detected-contracts/      -> CONTRACTS
├─ eyes-detected-models/         -> MODELS
├─ eyes-detected-labeler/        -> LABELER
│  └─ storage/workflow portions  -> DATA responsibility
├─ deploy/
│  ├─ onprem/                    -> RUNTIME + DATA
│  └─ vast/                      -> RUNTIME
├─ scripts/                      -> module-specific or RUNTIME depending on purpose
├─ validation/                   -> RESEARCH
├─ docs/                         -> ownership determined by document prefix/topic
├─ .codex/                       -> RUNTIME / agent tooling
└─ AGENTS.md                     -> repository-wide governance
```

Physical directory and architectural ownership are not required to be identical. Avoid moving working code solely to make directory names match this document.

---

## 11. Stability Rule

This module contract should change rarely.

Changes that justify a new version include:

- introducing a new top-level module;
- changing allowed dependency direction;
- changing hospital/public-cloud data boundaries;
- moving ownership of a shared contract;
- adding a new runtime class with different data permissions.

Ordinary feature work does not require changing this file.

---

## 12. Suggested Repository Location

Recommended authoritative path:

```text
docs/CTR_MODULE_CONTRACT.md
```

`AGENTS.md` should reference this file rather than duplicating the full module definition.

Suggested `AGENTS.md` addition:

```text
Before cross-package or cross-runtime changes, read docs/CTR_MODULE_CONTRACT.md.
Respect module ownership, dependency direction, and data/runtime boundaries.
Phases define execution order; modules define architecture ownership.
```
