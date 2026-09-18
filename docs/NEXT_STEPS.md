# Next steps — V3 handoff

R0 V3 is `R0_DATASET_TAXONOMY=PASS`. R1-P0 executed and is `BLOCKED` by two exact MMRDR duplicate-content groups
crossing the released `tr`/train and `ts`/test split. Do not begin R1 training or reshuffle the released split.

The immediate owner action is to review and resolve the split-leakage finding. After resolution, the sequence is:

1. Re-run only the affected R1-P0 split decision under the approved protocol and update the P0 contract; preserve the
   existing acquisition/model evidence and warnings. IDRiD acquisition is deferred to R2/R3.
2. If R1-P0 is `PASS` or `PASS_WITH_WARNINGS` with no blocker, continue R1 one candidate at a time: C0, C1, C2,
   carrying P0 warnings into every artifact.
3. Select a finalist from validation evidence, then run only the winner CE versus CORN ablation.
4. Calibrate the global model and select a versioned Global→ROI threshold from validation evidence.
5. Benchmark local/on-prem CPU inference and integrate the existing `templates/` workspace through contracts.
6. Continue R2–R8 in order: spatial ROI, lesion classifier, Label Studio QA, GUI integration, DICOM, drift, HL7/FHIR.

No current champion, clinical performance, public-data generalization, diagnosis, or deployment claim follows from
the repository’s synthetic smoke output or historical evidence.
