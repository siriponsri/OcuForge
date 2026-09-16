# OcuForge V3 validation report

**Status:** Engineering reconciliation report · not a scientific result

The current planning authority is [`docs/POC_MASTER_PLAN.md`](../docs/POC_MASTER_PLAN.md). At this gate:

```text
R0_V3 = PASS
R1_P0_ACQUISITION_PREFLIGHT = READY_NOT_EXECUTED
R1 C0/C1/C2 = READY_NOT_EXECUTED
CURRENT_R1_CHAMPION = NONE
```

This report records repository validation only. It does not certify a model, dataset, clinical workflow, deployment,
or generalization claim.

## R0 freeze outcome

The R0 evidence gate passed as `R0_DATASET_TAXONOMY=PASS`. MMRDR-UWF remains the primary R1 hypothesis, IDRiD
remains the primary spatial candidate, DDR/OIA-DDR is not admitted, and R1 remains `READY_NOT_EXECUTED` with no
champion. Byte-dependent checks are reclassified to R1-P0. Exact findings, asset revisions, overlap limits, and the
future download manifest are recorded in the
[machine-readable freeze](../docs/RSC_R0_DATASET_TAXONOMY_FREEZE_v0.1.json).

## Reconciliation scope

- Unified active documentation around the V3 master plan.
- Preserved old plans, starter specifications, and Eye Detected results under `docs/history/`.
- Registered exactly C0 ConvNeXt V2-Tiny, C1 FLAIR, and C2 DINOv3 high-resolution Attention MIL for CE-first R1.
- Added the winner-only CORN ablation path and kept CORAL as reusable legacy capability.
- Added the versioned Global-to-ROI soft triage contract without hard-disabling reviewer actions.
- Added editable HTML and standalone SVG workflow diagrams with a pinned Diagram Design integration.

## Not executed

No dataset was downloaded, no hospital/private data was inspected or uploaded, no model was trained, no approved
foundation weights were loaded, and no RunPod, Vast, Vercel, DICOM, MongoDB, CVAT, or clinical service was provisioned.

## Validation evidence

The final command results are recorded below after the repository checks complete.

| Check | Result |
|---|---|
| Pytest | PASS - 106 passed |
| Ruff | PASS |
| Configuration validation | PASS - 25 files |
| Package file validation | PASS - 327 reviewed files |
| Diagram Design HTML self-check | PASS - 5 HTML files |
| R0/R1/P0 machine-readable validator | PASS |
| Synthetic CPU roundtrip | PASS - 10 synthetic images; scientific result eligible: false |
| `git diff --check` | PASS |

## Claim ceiling

Synthetic smoke is engineering evidence only. Historical metrics are not current R1 evidence. Binary DR/no-DR
experience labels are not ordinal grades 0-4; MMRDR image-level lesion presence is not ROI geometry; MIL attention
is not a validated lesion mask; and fundus/UWF images do not establish OCT-confirmed DME.
