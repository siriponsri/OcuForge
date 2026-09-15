---
name: ocuforge-ai-research
description: Evidence-driven AI research workflow for OcuForge. Use when framing retinal-AI research questions, auditing novelty, selecting datasets/models, designing baselines/ablations, preventing leakage, choosing metrics, planning validation, interpreting results, or deciding whether evidence supports a research claim.
---

# OcuForge AI Research

Use this skill for scientific reasoning and experiment design, not routine code edits.

The goal is to turn a research idea into a falsifiable, reproducible, governance-safe experiment whose claims do not outrun the evidence.

## 1. Orient before proposing

Read the minimum relevant local sources first:

- root `AGENTS.md`;
- `docs/IMPLEMENTATION_STATUS.md`;
- relevant files under `docs/specification/`;
- dataset/model configs touched by the question;
- existing validation or experiment records if present.

Do not infer implementation status from plans alone. Separate `implemented`, `verified`, `planned`, and `unknown`.

When external literature is needed and network access is allowed, prefer primary sources: original papers, official dataset/model pages, and authoritative guidelines. Never invent a citation, result, dataset property, or benchmark number.

## 2. Write the research contract

Before recommending an experiment, make the scientific contract explicit:

- **Question:** what uncertainty are we resolving?
- **Population/domain:** fundus, UWF, OCT, public benchmark, local hospital, or another clearly named domain.
- **Task:** binary classification, multi-label disease detection, ordinal DR grading, lesion localization, QC/OOD, longitudinal risk, representation learning, or another explicit target.
- **Hypothesis:** a statement that can be falsified.
- **Primary endpoint:** one metric and one decision rule that determine success.
- **Baselines:** the minimum credible comparators.
- **Data boundary:** train/selection/test ownership and which assets are public versus local/private.
- **Claim ceiling:** the strongest statement the experiment could support if successful.

If any field is unknown and materially changes the design, surface it instead of silently guessing.

## 3. Respect OcuForge clinical semantics

The following are hard constraints:

- Local binary `DR` / `no-DR` experience labels are not ordinal grades 0-4.
- `no-DR` is not automatically adjudicated grade 0.
- DME is a separate axis; fundus/UWF alone is not OCT-confirmed DME.
- MIL attention is evidence for aggregation behavior, not validated lesion localization.
- Synthetic smoke results are engineering evidence only and are not scientific performance.
- Private clinical data and derived artifacts stay local/on-prem unless the owner explicitly authorizes another policy.

Do not design an evaluation that quietly violates these semantics.

## 4. Audit leakage before model choice

Check leakage risks before discussing architecture:

- patient/eye/visit overlap across splits;
- duplicate or near-duplicate images;
- longitudinal leakage across visits;
- train-time preprocessing fitted on validation/test data;
- model or threshold selection on the sealed test set;
- repeated peeking at the final test set;
- external benchmark contamination or pretraining overlap when relevant;
- pseudo-labels or active-learning feedback crossing evaluation boundaries.

Prefer patient-level or identity-aware splitting when identities exist.

Keep **selection** and **final evaluation** separate. Once a final test pool is declared sealed, do not use it for model, threshold, feature, or ablation selection.

## 5. Build the minimum experiment ladder

Start with the simplest credible baseline, then add one scientific idea at a time.

For retinal representation/MIL work, a typical ladder may include:

1. simple global-image baseline;
2. frozen encoder + simple head;
3. patch features + mean/max aggregation;
4. patch attention MIL;
5. ordinal head when the target is truly ordinal;
6. fine-tuning/adaptation only after the frozen baseline is understood.

Do not bundle multiple architectural changes into one comparison if the goal is causal interpretation.

For unlabeled local data, distinguish among:

- self-supervised/domain adaptation;
- pseudo-label or semi-supervised learning;
- active learning for expert-budget efficiency;
- purely unsupervised QC/OOD analysis.

Do not claim supervised local accuracy without appropriate local labels.

## 6. Require baselines, ablations, and negative controls

Each non-trivial method claim should have:

- a baseline that could plausibly win;
- an ablation isolating the claimed contribution;
- a compute-matched or parameter-matched comparison when relevant;
- a negative control or sanity check when practical;
- failure criteria decided before looking at the final result.

Examples:

- Patch attention claim -> compare global, patch mean, patch max, and patch attention.
- New ordinal method -> compare against a straightforward ordinal/classification baseline using the same encoder/data.
- Active learning claim -> compare against random sampling at equal labeling budget.
- Domain adaptation claim -> compare against no-adaptation and simple fine-tuning baselines.

## 7. Match metrics to the task

Use metrics that answer the scientific question.

- Binary/multi-label classification: AUROC plus AUPRC; include class prevalence and thresholded metrics when deployment behavior matters.
- Ordinal DR grading: QWK as a primary agreement metric when appropriate; also inspect confusion by grade and clinically important error distance.
- Imbalanced lesion tasks: precision-recall metrics and per-lesion results; do not hide rare-class failure behind a macro average alone.
- Calibration-sensitive use: calibration error/Brier score and reliability analysis.
- Longitudinal risk: time-aware validation and metrics appropriate to the prediction horizon.

AUC is not per-image probability of being correct. Do not describe it that way.

## 8. Statistical and reproducibility requirements

Record:

- exact dataset revision and inclusion/exclusion policy;
- split-generation rule and seed;
- model/encoder revision;
- preprocessing and patching policy;
- training seed(s);
- selection metric and stopping rule;
- hardware/runtime class when material;
- evaluation script/config revision.

Prefer confidence intervals or repeated seeds when the experiment supports them. For patient-level outcomes, bootstrap or resample at the patient level rather than pretending correlated images are independent.

Do not manufacture significance from tiny samples.

## 9. Literature-gap workflow

When auditing novelty:

1. State the proposed contribution in one sentence.
2. Search for the closest prior art, not just supportive papers.
3. Build a compact matrix: paper, data/modality, supervision, method, evaluation, key claim, limitation, overlap with proposal.
4. Try to falsify novelty.
5. Classify the gap as:
   - **defensible**;
   - **conditional**;
   - **incremental**;
   - **not defensible with current evidence**.
6. Separate novelty of the **method**, **evaluation**, **dataset/domain**, and **workflow**. Do not blur them together.

A paper being newer does not make the project novel.

## 10. Result interpretation

Interpret only after checking the predefined endpoint and experiment integrity.

Report:

- what changed;
- effect size and uncertainty;
- whether the primary endpoint passed;
- which ablations support or weaken the mechanism claim;
- important failure modes;
- domain limits;
- what evidence is still missing.

Use a strict claim ladder:

- **engineering works** -> pipeline executes correctly;
- **benchmark improvement** -> metric improves on a defined evaluation;
- **generalization** -> improvement holds on an external or appropriately separated domain;
- **clinical utility** -> requires clinical validation beyond benchmark performance.

Never jump levels.

## 11. Output format

For a research-design request, return a compact research brief with:

1. Research question and falsifiable hypothesis.
2. Evidence/prior-art status.
3. Data and split contract.
4. Baselines and experiment matrix.
5. Primary/secondary metrics.
6. Leakage and governance audit.
7. Acceptance/failure criteria.
8. Compute/budget notes.
9. Risks and unresolved decisions.
10. Exact next experiment only.

Do not launch the next project phase automatically. Stop at the requested gate.
