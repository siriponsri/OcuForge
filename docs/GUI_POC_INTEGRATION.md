# DR Review Workspace integration contract

**Status:** ACTIVE SUPPORTING CONTRACT
**Authority:** [`POC_MASTER_PLAN.md`](POC_MASTER_PLAN.md)
**Artifact:** existing `templates/` static HTML/CSS/JS customer-facing POC reference

## Preserve the existing workspace

Do not replace the current information architecture with a competing dashboard:

```text
Review Workspace: Overview · Screening · Review Queue
Model Lab: Explainability · Model Comparison
System: Integrations
```

The image remains primary and the model suggestion remains secondary. Reviewer decisions are stored separately from
the original prediction, with image/study identity, laterality/modality, ROI identity and geometry, model version,
scores, reviewer action, note, timestamp, and approved reviewer identity.

## V3 review flow

```text
image -> QC/gradability -> global DR suggestion -> calibration/OOD -> soft Global→ROI triage
                                                        |
                         default ROI skip <-------------+-------------> open ROI review
                                                        |
             reviewer can always Inspect ROI Anyway / Correct Grade / Comment / Accept / Mark Incorrect
```

The versioned contract is `global_roi_triage_policy.v0.1`, `global_roi_triage_input.v0.1`, and
`global_roi_triage_decision.v0.1` in the contracts package. The confidence threshold is unset until calibration
evidence validates a policy version; the GUI must not invent `0.5`, `0.8`, or another constant.

`GLOBAL_NO_DR` is not `NO_SUPPORTED_LESION_IN_ROI`. The ROI negative semantic is limited to supported lesion classes
inside the selected ROI. It is not a statement about the whole eye or pathology outside the ROI.

## Adapter boundary

Future integration targets include `/v1/infer/global`, `/v1/infer/lesion-roi`, `/v1/models`, `/v1/explain/roi`, and
`/v1/evaluate/model-diff`. The page code depends on an adapter and shared contracts, never MDL internals. AI evidence
is labeled as aggregation evidence when it comes from MIL attention; it is not lesion localization.

Label Studio Community is the internal ROI QA/HITL workbench (`suggestion → confirm/correct/reject/escalate`). CVAT is
optional advanced annotation infrastructure. Browser clients never hold service secrets.

## Clinical and governance boundary

Allowed language: Screening Support, Research Review, AI Suggestion, Reviewer Decision, Evidence, Model Comparison.
Avoid diagnosis, confirmed disease, treatment/referral instruction, and whole-eye normal claims. DME remains a separate
axis and fundus/UWF alone is not OCT-confirmed DME. The templates package remains the GUI target.
