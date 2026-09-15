# HANDOFF TO GPT WORK — ASTRA LOW

## Use case

This document is intentionally optimized for a lower-reasoning drafting pass.

Do not ask Astra Low to decide the scientific architecture from scratch. The architecture is already specified. Astra Low should **implement the starter faithfully**.

---

# 1. Paste this instruction to GPT Work

```text
Implement the Eye Detected dual-track starter workspace using
00_GPT_WORK_MASTER_PROMPT_TH.md as the authoritative implementation command.

Read all Markdown files in this package before making files.

Output:
eyes-detected-dual-track-starter-v0.1.zip

Important:
- This is a starter foundation only.
- Do not run full training.
- Do not download medical datasets.
- Do not use paid APIs.
- Do not use PHI.
- Do not make clinical claims.
- Track A, Track B, and shared contracts must remain separable.
- Use synthetic fixtures so validation works offline.
- Do not fake external model integrations.
- If DINOv3/RETFound/CVAT external access cannot be verified, scaffold the adapter,
  mark the dependency clearly, and test error handling.
- CVAT is the initial labeler backend; do not build a full custom medical labeling UI.
- Implement provenance and shared contracts first.
- Run the Final Delivery Gate and include validation/FINAL_DELIVERY_REPORT.md.
```

---

# 2. Astra Low priority order

If token/time constrained:

## Priority 0
- contracts;
- tests;
- package structure;
- safety.

## Priority 1
Track A:
- data registry;
- tiling;
- synthetic MIL;
- CORAL;
- predictions;
- AL batch.

Track B:
- geometry;
- provenance;
- CVAT bridge interface;
- synthetic import/export.

## Priority 2
- Docker/devcontainer;
- docs;
- examples.

## Priority 3
- optional FiftyOne;
- optional external model adapter extras.

Never sacrifice provenance/schema correctness to add visual polish.

---

# 3. Decisions Astra Low must not change

- DINOv3 ViT-B/16 = primary encoder target.
- RETFound = challenger.
- patch-based MIL = primary UWF aggregation path.
- CORAL = primary ordinal head.
- MMRDR-UWF = primary public UWF source.
- IDRiD = primary early lesion-localization bootstrap.
- CVAT = initial annotation backend.
- MA = point-primary annotation.
- NV = manual region first; no fake pixel pre-label from MMRDR.
- DME separated by modality.
- active learning starts diversity-first.
- Track A does not wait for doctor.
- Track B does not own model training.

---

# 4. Acceptable simplifications

Allowed:
- TinyTestEncoder for offline tests, explicitly test-only.
- synthetic 64×64/224×224 images for unit tests.
- local JSON fixtures instead of real dataset.
- mock CVAT transport in unit tests.
- plain Python scripts instead of complex orchestration.
- Mermaid diagrams instead of generated images.

Not allowed:
- fake DINOv3 class named as if real inference happened;
- dummy result hard-coded to pass metrics;
- AI labels stored as clinician ground truth;
- deleting provenance on export.

---

# 5. Required final summary from GPT Work

```text
1. ZIP path
2. file tree
3. validation status
4. tests run + counts
5. implemented vs scaffolded
6. external dependencies
7. known limitations
8. next 5 commands for the beginner user
```

---

# 6. After Work returns ZIP

Recommended next agent:
- Codex / GPT-5.6 Sol or stronger engineering mode.

Tasks:
1. unpack;
2. hostile audit;
3. run tests locally;
4. inspect Docker;
5. verify external package versions;
6. patch defects;
7. initialize Git repositories;
8. push;
9. run first public-data smoke job on GPU.

Do not involve the doctor yet.
