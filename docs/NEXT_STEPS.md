# Next steps — V3 handoff

The only next manual action is owner/architect review of the V3 reconciliation. Do not begin the next phase in the
same task.

After approval, the sequence is:

1. Execute R0 on CPU: verify datasets, labels, spatial supervision, identity/split semantics, negative policy,
   licenses/checksums, and C1/C2 foundation pretraining overlap.
2. If R0 passes, run R1 one candidate at a time: C0, C1, C2. Stop after each run for human review.
3. Select a finalist from validation evidence, then run only the winner CE versus CORN ablation.
4. Calibrate the global model and select a versioned Global→ROI threshold from validation evidence.
5. Benchmark local/on-prem CPU inference and integrate the existing `templates/` workspace through contracts.
6. Continue R2–R8 in order: spatial ROI, lesion classifier, Label Studio QA, GUI integration, DICOM, drift, HL7/FHIR.

No current champion, clinical performance, public-data generalization, diagnosis, or deployment claim follows from
the repository’s synthetic smoke output or historical evidence.
