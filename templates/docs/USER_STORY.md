# User Story and UX Flow

## Primary persona: clinical reviewer

### Story

As a clinical reviewer, I want to inspect one retinal region at a time, compare it with an AI suggestion, and record a clear human decision so uncertain cases can be resolved without treating model output as ground truth.

### Happy path

1. Open **Overview**.
2. Select **Continue screening**.
3. Confirm the image, laterality, modality, and selected ROI.
4. Inspect the source image before reading the model suggestion.
5. Choose **Confirm**, **Correct**, or **Reject suggestion**.
6. Continue to the next case.
7. Use **Review queue** only for low-confidence, disagreement, or missing-prediction cases.

### UX requirements

- One primary action is visible on each page.
- Model suggestions are visually secondary to the image.
- Review state, task identity, ROI identity, and mock/live status remain visible.
- A corrected reviewer label does not overwrite the original model output.
- Uncertain cases can be escalated instead of forced into a label.
- Missing supported lesion in one ROI is not presented as a patient-level normal diagnosis.

## Secondary persona: model or research reviewer

### Explainability story

As a model reviewer, I want to compare the source image with case-level model evidence so I can identify whether the model relied on plausible regions while keeping the limits of attention-based explanations explicit.

### Explainability flow

1. Select a task.
2. Toggle **Original**, **Attention**, and **ROI** views.
3. Inspect ranked relative evidence regions.
4. Compare the top evidence region with the reviewer-selected ROI.
5. Record an observation outside the POC when deeper research review is required.

### Model comparison story

As a model reviewer, I want to compare two versioned models on the same evaluation set and inspect improved and regressed cases so I can decide whether a candidate version is ready for deeper evaluation.

### Model comparison flow

1. Select Model A, Model B, and a versioned evaluation set.
2. Load or run the comparison through the model adapter.
3. Start with **Regressed** cases.
4. Inspect the reference, both predictions, confidence change, image, and evidence.
5. Review **Improved** and **Changed** cases.
6. Group repeated failure patterns into clusters.
7. Export or record findings through a future versioned evaluation contract.

### Diff definitions

- **Improved:** Model B matches the reference while Model A does not.
- **Regressed:** Model A matches the reference while Model B does not.
- **Changed:** the output changed without a clear reference-aligned win.
- **Unchanged:** both models return the same top label; confidence may still differ.

These definitions are demonstration rules for the mockup. A live system must define task-specific metrics, thresholds, reference status, and uncertainty policy in a versioned protocol.

## Safety boundary

- The application supports research review and annotation workflow only.
- AI suggestions are not confirmed diagnoses.
- MIL attention is not validated lesion localization.
- Evidence overlays cannot replace direct image review.
- No cloud deployment or browser token storage is implied by this POC.
