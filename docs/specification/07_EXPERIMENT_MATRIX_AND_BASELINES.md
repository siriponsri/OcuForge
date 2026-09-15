# EXPERIMENT MATRIX & BASELINES — TRACK A

This document prevents the project from jumping straight to a single “hero model”.

---

# 1. Experiment principles

- one question per experiment;
- config-driven;
- freeze data split;
- log Git/Docker/data/seed;
- compare against simpler baselines;
- no metric cherry-picking;
- do not tune on locked sentinel.

---

# 2. E0 — Data/patch sanity

Question:
Does patching preserve usable UWF field and deterministic coordinates?

Compare:
- full image resize;
- 3×3 patches;
- 5×5 patches;
- configurable overlap.

Outputs:
- visual grid;
- patch coverage;
- runtime;
- storage.

---

# 3. E1 — Encoder frozen representation bake-off

Candidates:
- DINOv3 ViT-B/16;
- RETFound ViT-L;
- optional EyeCLIP/RetiZero;
- conventional supervised baseline.

Aggregation:
- global;
- patch mean;
- patch max;
- attention MIL.

Primary:
QWK on 5-grade DR.

---

# 4. E2 — Ordinal vs categorical head

Compare:
- softmax cross-entropy 5-class;
- CORAL ordinal.

Metrics:
- QWK;
- macro-F1;
- severe-grade errors;
- confusion distance.

---

# 5. E3 — Lesion auxiliary

Compare:
- DR-only;
- DR + seven MMRDR lesion-presence auxiliary.

Question:
Does lesion-aware auxiliary supervision improve grade performance/generalization?

Do not claim lesion localization from this experiment.

---

# 6. E4 — Fine-tuning policy

Compare:
- frozen encoder;
- last block(s) trainable;
- partial fine-tuning.

Track:
- VRAM;
- time;
- QWK;
- overfit;
- domain generalization.

---

# 7. E5 — Local domain shift

No local labels required.

Measures:
- embedding cluster shift;
- prototype distances;
- camera/site separation;
- confidence shift;
- QC shift;
- OOD score distribution.

---

# 8. E6 — Zero-label adaptation baselines

B0:
No adaptation.

B1:
Prototype/reference matching only.

B2:
Confidence pseudo-labeling.

B3:
Consistency learning.

B4:
Published source-free adaptation baseline where reproducible.

B5:
Multi-signal gated adaptation:
classifier + prototype + consistency + optional VLM + OOD.

No local accuracy claim until labels arrive.

---

# 9. E7 — Lesion pre-label

Separate by lesion.

MA:
- detector/point conversion from localized public GT.

Hard exudate:
- segmentation baseline.

Hemorrhage:
- segmentation/detection baseline.

Cotton-wool:
- segmentation baseline.

NV:
- image-level weak candidate only initially unless localized training data are acquired.

Metrics:
- candidate precision/recall;
- false candidates/image;
- correction burden.

---

# 10. E8 — Active learning cold start

After first eligible local pool selection.

Compare:
- random;
- cluster diversity;
- uncertainty;
- diversity + disagreement;
- OOD-aware mix.

First objective:
coverage and information, not only uncertainty.

---

# 11. E9 — Active learning mature rounds

Compare:
- random;
- Hybrid-Diversity;
- MC Dropout;
- ensemble disagreement;
- lesion rarity weighted.

Metrics:
- learning curve;
- metric gain/100 labels;
- gain/clinician-hour;
- correction yield.

---

# 12. E10 — Verification cascade business metric

Future when a baseline screening output is available.

Question:
Can Eye Detected verification reduce unnecessary referral while preserving sensitivity?

Compare:
- primary screening only;
- primary + Eye Detected verification;
- human-review routing for disagreement/OOD.

Hero concept:
```text
Referral reduction at fixed sensitivity
```

This must be evaluated on appropriately labeled local/clinical data before any claim.

---

# 13. Minimum metrics table

| Task | Primary | Secondary |
|---|---|---|
| 5-grade DR | QWK | macro-F1, AUROC, AUPRC |
| Referable DR | sensitivity at target specificity | PPV/NPV, referral rate |
| Calibration | ECE | Brier |
| OOD | AUROC / risk-coverage | FPR95 |
| Lesion pre-label | lesion recall/precision | false candidates/image |
| Annotation | correction yield/hour | time/case |
| Active learning | gain/clinician-hour | AULC |
| Business cascade | referral reduction at fixed sensitivity | review workload |

---

# 14. Experiment naming

```text
A_<stage>_<model>_<task>_<NNN>
```

Examples:
```text
A_R2_DINOV3_PATCHMEAN_DR_001
A_R3_DINOV3_ATTN_CORAL_001
A_R4_MULTISIGNAL_SFDA_001
A_R6_HYBRID_AL_001
```

Every experiment gets:
- config;
- run manifest;
- result summary;
- artifact pointer.
