# Luna Max Handoff — Replan Before R0

## Owner decision

OcuForge is moving from an architecture-first training plan to an evidence-driven two-track model plan.

Do not discard current implementation. Reconcile the repository with the new plan while preserving validated contracts and safety/data-governance rules.

## Documents in this package

1. `POC_MASTER_PLAN_V2.md` — authoritative research/POC direction.
2. `R0_DATASET_SUPERVISION_FREEZE.md` — R0 acceptance protocol.
3. `R1_GLOBAL_MODEL_SELECTION.md` — controlled global-model benchmark.
4. `GUI_POC_INTEGRATION.md` — how the existing HTML POC maps to backend/model work.

## Key changes

- Keep DINOv3 + Attention MIL, but treat it as a leading candidate rather than a preselected champion.
- R1 must benchmark global, simple patch pooling, and Attention MIL before partial fine-tuning.
- CORAL is an ablation for genuine ordinal labels, not an assumed final head.
- Global DR and ROI lesion classification are separate training tracks.
- ROI lesion taxonomy begins with spatially supported classes.
- MMRDR image-level lesion labels must not be converted into ROI supervision.
- Existing DR Review Workspace is the customer-facing UX reference.
- Label Studio CE is the internal ROI QA/annotation workbench.
- CVAT remains optional advanced CV infrastructure.
- RunPod/Vast are public-data compute only; hospital/private data remain on-prem.
- No large GPU training/download in the planning-reconciliation commit.

## Required repository action before R0 execution

Luna Max should:

1. inspect the current repo and current authoritative docs;
2. identify conflicts between existing R0/R1 text and the V2 plan;
3. update only the docs/configs/contracts necessary to reconcile direction;
4. preserve working packages and tests;
5. add/adjust tests only where contract/config changes require them;
6. run the full repository validation suite;
7. make one bounded planning commit;
8. push only after validation passes;
9. stop before dataset download or model training.

R0 execution should be a later goal after this reconciliation commit is reviewed.
