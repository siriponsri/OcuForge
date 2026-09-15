# Eye Detected — Dual-Track GPT Work Package v1.0

**Purpose:** authoritative handoff package for GPT Work / GPT-6 Astra Low to draft a **starter ZIP workspace** for the next stage of the Eye Detected project.

This package intentionally separates the work into two parallel tracks:

- **Track A — Model Research & Training:** build the retinal AI research pipeline now, without waiting for local ophthalmologist labels.
- **Track B — Annotation & Clinician Labeling Platform:** build a local, AI-assisted annotation workflow in parallel so clinician time is used only after the model/data pipeline is ready.

A small **Shared Contract Layer** connects the tracks but must not couple their implementations.

---

## 1. Strategic premise

Eye Detected must not be framed as “another DR classifier” only. Thailand already has multiple DR screening systems and implementation programs. The technical program should therefore produce reusable assets for a **Local Retinal AI Platform** while still benchmarking its native model against market-relevant DR screening capabilities.

The starter package must support:

1. public-data model development;
2. zero-local-label analysis/adaptation;
3. local lesion pre-label generation;
4. AI-assisted clinician annotation;
5. active-learning batch selection;
6. strict annotation/model provenance;
7. later transition to local inference/product deployment.

The starter is a **research + engineering foundation**, not a clinical product.

---

## 2. Target workspace to be drafted by GPT Work

GPT Work should produce one ZIP:

`eyes-detected-dual-track-starter-v0.1.zip`

containing three independently understandable workspaces:

```text
eyes-detected-dual-track-starter-v0.1/
├── eyes-detected-models/       # Track A
├── eyes-detected-labeler/      # Track B
├── eyes-detected-contracts/    # Shared schemas/contracts
├── docs/
│   ├── START_HERE_TH.md
│   ├── LOCAL_SETUP_TH.md
│   ├── GPU_EXECUTION_TH.md
│   └── SAFETY_AND_SCOPE.md
└── validation/
    └── FINAL_DELIVERY_REPORT.md
```

The three workspaces may live in one starter ZIP for convenience, but they must remain cleanly separable into independent Git repositories later.

---

## 3. Non-negotiable scope

### Starter MUST

- be runnable with synthetic/small fixtures without downloading medical datasets;
- include tests for core contracts, config validation, tiling, ordinal target encoding, annotation geometry, import/export, and provenance;
- make every external model/dataset integration explicit;
- use configuration rather than hard-coded paths;
- provide a Docker-first runtime;
- support provider-agnostic GPU execution scripts;
- use CVAT as the initial annotation backend rather than rebuilding a full annotation editor;
- preserve the ability to replace CVAT later;
- preserve the ability to replace DINOv3 later;
- use stable image/case identifiers and annotation provenance;
- include a final delivery report that states what is implemented, what is scaffolded, and what remains external.

### Starter MUST NOT

- download or commit raw hospital data;
- commit credentials, tokens, PHI, large checkpoints, or large datasets;
- make clinical performance claims;
- silently label AI predictions as ground truth;
- auto-update a production model from clinician feedback;
- pretend a DINOv3/RETFound/EyeCLIP integration works if weights or license/access were not actually verified;
- claim pixel-level localization from image-level lesion labels;
- claim UWF/fundus can directly establish OCT-defined DME;
- train a full benchmark during starter generation;
- require a paid API for tests or demo;
- require a cloud GPU to run unit tests.

---

## 4. How to use this package

Read in this order:

1. `00_GPT_WORK_MASTER_PROMPT_TH.md`
2. `01_TRACK_A_MODEL_RESEARCH_AND_TRAINING_SPEC.md`
3. `02_TRACK_B_ANNOTATION_PLATFORM_SPEC.md`
4. `03_LABEL_SCHEMA_AND_CLINICAL_ANNOTATION_PROTOCOL_V1.md`
5. `04_SHARED_CONTRACTS_DATA_GOVERNANCE_AND_PROVENANCE.md`
6. `05_INFRASTRUCTURE_DOCKER_GPU_AND_REPO_STRATEGY.md`
7. `06_IMPLEMENTATION_ROADMAP_GATES_AND_ACCEPTANCE.md`
8. `07_EXPERIMENT_MATRIX_AND_BASELINES.md`
9. `08_GPT_WORK_ASTRA_LOW_HANDOFF.md`
10. `09_REFERENCES_AND_SOURCE_LIMITATIONS.md`
11. `10_EXPECTED_STARTER_ZIP_TREE.md`

If two documents appear to conflict, precedence is:

```text
Safety / data provenance
> 00 Master Prompt
> Shared contracts
> Track-specific spec
> implementation convenience
```

---

## 5. Research truth that must remain explicit

### MMRDR-UWF

MMRDR contains **10,404 UWF images** and provides **5-grade DR labels plus seven lesion-presence labels** for CFP/UWF. Those lesion fields are multi-label image-level annotations, not pixel masks. Therefore MMRDR-UWF is suitable for DR grading and lesion-aware weak supervision, but is **not sufficient by itself for pixel-level MA/NV localization**.

### IDRiD

IDRiD contains 516 CFP images; 81 lesion-annotated images include pixel-level masks for microaneurysms, hard exudates, hemorrhages, and soft exudates. It is useful for localization/segmentation bootstrapping but is conventional ~50° CFP, not UWF.

### DME

DME must be handled by modality. In MMRDR, 3-class DME grading is on OCT. Fundus/UWF can provide macular signs or suspicion labels only if a protocol explicitly defines them; it must not be silently equated with OCT-defined edema.

---

## 6. Desired outcome after GPT Work

A beginner should be able to:

1. unzip the starter;
2. run CPU/offline tests;
3. understand how public datasets will be registered;
4. understand how DINOv3/MIL/CORAL will be executed on GPU later;
5. start CVAT locally and understand the Eye Detected label schema;
6. import synthetic AI pre-labels into the labeler;
7. export clinician-corrected annotations with provenance;
8. see how an active-learning batch will be selected later;
9. move Track A and Track B independently without blocking each other.

This document does not authorize clinical deployment.
