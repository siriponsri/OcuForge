# Next steps — V3 handoff

R0 V3 is `R0_DATASET_TAXONOMY=PASS`. The next manual action is to execute
[`R1_P0_ACQUISITION_PREFLIGHT.json`](R1_P0_ACQUISITION_PREFLIGHT.json). Do not begin R1 training in the same task.

After approval, the sequence is:

1. `git pull` and execute R1-P0 Global: verify MMRDR archive/file hashes, inventory, schema/split, preprocessing,
   gated access, C0/C1/C2 model loading, and storage/runtime readiness. Record `PASS`, `PASS_WITH_WARNINGS`, or
   `BLOCKED` using the P0 contract; IDRiD acquisition is deferred to R2/R3.
2. If R1-P0 is `PASS` or `PASS_WITH_WARNINGS` with no blocker, run R1 one candidate at a time: C0, C1, C2. Stop
   after each run for human review and carry P0 warnings into every artifact.
3. Select a finalist from validation evidence, then run only the winner CE versus CORN ablation.
4. Calibrate the global model and select a versioned Global→ROI threshold from validation evidence.
5. Benchmark local/on-prem CPU inference and integrate the existing `templates/` workspace through contracts.
6. Continue R2–R8 in order: spatial ROI, lesion classifier, Label Studio QA, GUI integration, DICOM, drift, HL7/FHIR.

No current champion, clinical performance, public-data generalization, diagnosis, or deployment claim follows from
the repository’s synthetic smoke output or historical evidence.
