# R1 Global DR Model Selection Protocol

**Status:** ACTIVE SUPPORTING PROTOCOL · `R1_P0_ACQUISITION_PREFLIGHT=BLOCKED` · `R1_GLOBAL_BENCHMARK=READY_NOT_EXECUTED`
**Authority:** [`POC_MASTER_PLAN.md`](POC_MASTER_PLAN.md)

R1 selects a defensible global ordinal DR architecture after R0 and R1-P0 reaches `PASS` or `PASS_WITH_WARNINGS`
without a blocking finding. This protocol defines the controlled execution conditions and does not claim a current
model result.

## Target and candidates

Target: genuine ordinal diabetic-retinopathy grade 0–4. The active registry is
[`r1-global-benchmark.json`](../eyes-detected-models/configs/research/r1-global-benchmark.json).

| ID | Architecture family | Research question | Initial loss |
|---|---|---|---|
| C0 | ConvNeXt V2-Tiny | Does a compact supervised transfer control solve enough of the task? | CE |
| C1 | FLAIR image encoder | Does a retina-specialist representation transfer to the selected domain? | CE |
| C2 | DINOv3 ViT-B/16 + high-resolution patch Attention MIL | Does local detail survive better than global resizing? | CE |

All three records require explicit asset revision, preprocessing, license/access status, research execution eligibility,
deployment license status, and hashes before execution. R1-P0 owns local weight hashes, access, preprocessing smoke,
and model loading; no candidate may train before P0 reaches `PASS` or `PASS_WITH_WARNINGS` with no blocker.
C1 must not silently become a different foundation model if FLAIR cannot be loaded. C2 attention is model aggregation
evidence only, never a lesion mask.

Unknown foundation overlap, unavailable row-level patient IDs with the released split preserved, and deployment rights
that need separate review are explicit warnings. They cap claims or deployment use but do not by themselves block a
valid research execution. A wrong target, leakage, corrupt/incompatible asset, or failed required load/forward pass
remains blocking.

## Controlled execution order

```text
C0 run -> validate checkpoint
  -> C1 run -> validate checkpoint
  -> C2 run -> validate checkpoint
  -> comparison/calibration/error-analysis evidence freeze
  -> mandatory OWNER/morning architecture-selection gate
  -> STOP
```

After R1-P0 reaches `PASS` or `PASS_WITH_WARNINGS` without a blocker and `RUNPOD_AUTOMATION_SMOKE` reaches `PASS` or
`PASS_WITH_WARNINGS`, the authorized unattended overnight run may continue from one validated checkpoint to the next.
The operator still runs one candidate at a time, and a blocker stops continuation; non-blocking warnings must be recorded and
propagated. No autonomous command trains all three or promotes a champion. The overnight run ends at the OWNER/morning
gate. The overnight run does not authorize CE-vs-CORN. The current champion is `NONE`.

Any later winner-only CE-vs-CORN, calibration/threshold selection, or local CPU/on-prem deployment benchmark requires
separate explicit OWNER authorization after the morning gate.

## Loss and target controls

The initial comparison is C0 + CE, C1 + CE, and C2 + CE. This prevents architecture/loss confounding. Any later
winner + CE versus winner + CORN comparison requires separate explicit owner authorization after the mandatory
OWNER/morning gate and is not part of the overnight run. CORAL remains supported legacy code and may remain covered by
tests, but is not a required initial R1 candidate.

Binary labels cannot train ordinal heads. `no-DR` experience labels are not adjudicated grade 0.

## Evaluation contract

Primary metric: QWK. Required companions: macro F1, per-grade recall, balanced accuracy, confusion matrix, class
support, calibration curve, ECE, Brier score, meaningful any-DR and moderate-or-worse metrics, and AUROC/AUPRC only
where binary semantics are explicit.

Required operational measurements: preprocessing latency, CPU inference latency, peak RAM, serialized model size, GPU
VRAM/runtime, training or extraction cost, and model-loading time where useful. No invented composite score or fixed
QWK/latency tolerance is allowed before measurement and intended-use discussion.

Selection uses validation evidence. The test split remains sealed for final evaluation. External data are not clean
generalization evidence when foundation-model pretraining overlap is confirmed or unresolved.

## R1-P0 outcome condition

`PASS` requires every required P0 check to pass. `PASS_WITH_WARNINGS` requires every required check to pass or carry a
non-blocking warning, no blocker, explicit warning records, and warning propagation into every R1 artifact. `BLOCKED`
is reserved for invalidating, unauthorized, corrupt, leaking, incompatible, or impossible R1 execution conditions.

## R1 PASS condition

R1 can pass only after real reviewed public data, authorized candidate assets, held-out evaluation, baseline comparison,
selected architecture and rationale, artifact metadata, deployment-practicality measurements, exact reproducible
configuration, and no leakage finding. Readiness is not PASS.
