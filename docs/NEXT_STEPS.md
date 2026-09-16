# Next steps — V3 handoff

R0 V3 ended as `R0_DATASET_TAXONOMY=BLOCKED`. The next manual action is to resolve the exact blockers in
[`RSC_R0_DATASET_TAXONOMY_FREEZE_v0.1.json`](RSC_R0_DATASET_TAXONOMY_FREEZE_v0.1.json) and re-audit R0. Do not
begin R1 in the same task.

After approval, the sequence is:

1. Re-open R0 on CPU: reconcile dataset terms, verify checksums/file inventory and identity/split semantics, establish
   evidence-backed negative policy, and hash/approve C0/C1/C2 assets and pretraining overlap.
2. If R0 passes, run R1 one candidate at a time: C0, C1, C2. Stop after each run for human review.
3. Select a finalist from validation evidence, then run only the winner CE versus CORN ablation.
4. Calibrate the global model and select a versioned Global→ROI threshold from validation evidence.
5. Benchmark local/on-prem CPU inference and integrate the existing `templates/` workspace through contracts.
6. Continue R2–R8 in order: spatial ROI, lesion classifier, Label Studio QA, GUI integration, DICOM, drift, HL7/FHIR.

No current champion, clinical performance, public-data generalization, diagnosis, or deployment claim follows from
the repository’s synthetic smoke output or historical evidence.
