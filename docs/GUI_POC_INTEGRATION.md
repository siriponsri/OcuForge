# DR Review Workspace Integration Contract

**Artifact:** DR Review Workspace — Screening Support POC
**Role:** Customer-facing GUI reference for OcuForge
**Status:** Static HTML/CSS/JS package, mock-first

## 1. Preserve the existing UX

The package already implements the preferred information architecture:

```text
Review Workspace
  Overview
  Screening
  Review Queue

Model Lab
  Explainability
  Model Comparison

System
  Integrations
```

Do not replace this with a generic all-in-one dashboard.

The production implementation may migrate to Vue/Nuxt later, but should preserve the current user story and adapter boundaries.

## 2. Primary clinical-review flow

```text
Open Overview
-> Continue Screening
-> inspect source image / laterality / modality / ROI
-> inspect AI suggestion
-> Confirm | Correct | Reject | Escalate
-> retain original prediction
-> store reviewer decision separately
-> continue
```

The image remains primary. Model suggestion is secondary.

## 3. Supported ROI interaction

Current package supports:

- point;
- rectangle;
- polygon.

Canonical labels in the package:

```text
MICROANEURYSM
INTRARETINAL_HEMORRHAGE
HARD_EXUDATE
SOFT_EXUDATE
NO_SUPPORTED_LESION_IN_ROI
```

Review decisions:

```text
CONFIRM
CORRECT
REJECT
ESCALATE
```

Reviewer certainty:

```text
HIGH
MEDIUM
LOW
```

These align with the revised R0 spatial-taxonomy starting point.

## 4. Model boundary

Current intended endpoints:

```text
POST /v1/infer/global
POST /v1/infer/lesion-roi
GET  /v1/models
POST /v1/explain/roi
POST /v1/evaluate/model-diff
```

`/v1/explain/roi` and `/v1/evaluate/model-diff` are integration targets until implemented.

Page code should depend on an adapter, not direct model internals.

## 5. Annotation contract

A reviewer record must preserve:

- task identity;
- image/study identity;
- laterality/modality where available;
- ROI identity;
- ROI type;
- coordinate space;
- original ROI geometry;
- original model name/version;
- ranked model predictions/scores;
- original suggestion;
- reviewer decision;
- final reviewer label when applicable;
- reviewer note/certainty when enabled;
- review timestamp;
- reviewer identity or approved pseudonymous identifier.

A correction must never overwrite the original model prediction.

## 6. Coordinate systems

The current example contract uses normalized coordinates 0–1.

Label Studio region exports may use 0–100 coordinate conventions.

The trusted bridge/adapter must:
- convert explicitly;
- preserve original geometry;
- record coordinate-space metadata;
- reject unknown coordinate spaces rather than guess.

## 7. Label Studio role

Label Studio Community Edition is the preferred internal ROI review/QA workbench.

Use the supplied ROI lesion labeling configuration as the POC starting point.

Browser clients must not contain Label Studio API secrets.

Use a trusted backend bridge for:
- authentication/authorization;
- task mapping;
- prediction mapping;
- decision submission;
- audit logging;
- schema validation;
- CORS;
- credential storage.

CVAT remains optional for advanced boxes/polygons/masks/segmentation workflows.

## 8. Explainability boundary

The GUI already states the correct interpretation:

- case-first;
- source image vs attention vs ROI;
- ranked evidence regions;
- explicit limitation.

MIL attention must be labeled as **aggregation evidence**, not lesion localization, segmentation, or validated causal explanation.

ROI classifier output and MIL evidence must not be visually conflated.

## 9. Model comparison boundary

The GUI supports:
- Improved
- Regressed
- Changed
- Unchanged

A live implementation must bind these categories to:
- a versioned evaluation set;
- a reference-status definition;
- task-specific metric/protocol;
- model A and model B immutable versions.

No mock metric becomes a scientific claim.

## 10. Safety/UI language

Allowed framing:
- Screening Support
- Research Review
- AI Suggestion
- Reviewer Decision
- Evidence
- Model Comparison

Avoid unsupported framing:
- diagnosis;
- confirmed disease;
- treatment/referral instruction;
- whole-eye normal based on one negative ROI.

`No lesion detected` in the UI must map internally to `NO_SUPPORTED_LESION_IN_ROI` and retain the narrower meaning.
