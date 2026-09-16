# R1 Global DR Model Selection Protocol

**Status:** ACTIVE SUPPORTING PROTOCOL · `R1_GLOBAL_BENCHMARK=READY_NOT_EXECUTED`
**Authority:** [`POC_MASTER_PLAN.md`](POC_MASTER_PLAN.md)

R1 selects a defensible global ordinal DR architecture after R0 passes. It is not a training instruction for this
reconciliation and it does not claim a current model result.

## Target and candidates

Target: genuine ordinal diabetic-retinopathy grade 0–4. The active registry is
[`r1-global-benchmark.json`](../eyes-detected-models/configs/research/r1-global-benchmark.json).

| ID | Architecture family | Research question | Initial loss |
|---|---|---|---|
| C0 | ConvNeXt V2-Tiny | Does a compact supervised transfer control solve enough of the task? | CE |
| C1 | FLAIR image encoder | Does a retina-specialist representation transfer to the selected domain? | CE |
| C2 | DINOv3 ViT-B/16 + high-resolution patch Attention MIL | Does local detail survive better than global resizing? | CE |

All three records require explicit asset revision, preprocessing, license/access status, and hashes before execution.
C1 must not silently become a different foundation model if FLAIR cannot be loaded. C2 attention is model aggregation
evidence only, never a lesion mask.

## Controlled execution order

```text
C0 run -> STOP -> owner/reviewer inspect metrics, errors, cost
  -> C1 run -> STOP -> review
  -> C2 run -> STOP -> review
  -> architecture decision
  -> winner-only CE vs CORN
  -> STOP
  -> calibration and threshold selection
  -> local CPU/on-prem deployment benchmark
```

The operator runs one candidate at a time. No autonomous command trains all three or promotes a champion. The current
champion is `NONE`.

## Loss and target controls

The initial comparison is C0 + CE, C1 + CE, and C2 + CE. This prevents architecture/loss confounding. After a
winner/finalist is selected from validation evidence, compare winner + CE against winner + CORN once. CORAL remains
supported legacy code and may remain covered by tests, but is not a required initial R1 candidate.

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

## PASS condition

R1 can pass only after real reviewed public data, authorized candidate assets, held-out evaluation, baseline comparison,
selected architecture and rationale, artifact metadata, deployment-practicality measurements, exact reproducible
configuration, and no leakage finding. Readiness is not PASS.
