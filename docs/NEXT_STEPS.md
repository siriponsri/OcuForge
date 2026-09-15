# Next POC steps and remaining acceptance work

1. Complete **R0 / MDL — Dataset + Lesion Taxonomy Freeze**: audit public sources/licenses,
   exact lesion annotations and counts, semantic mapping, negative validity, identity-aware splits,
   baseline ladder, metrics, compute estimate, and the first experiment.
2. Train and evaluate the global baseline on reviewed public/synthetic data, preserving
   binary/ordinal semantics
   and reporting held-out evidence.
3. Build the ROI dataset and lesion classifier with audited negatives, top-k output, calibration, support,
   confusion matrix, and measured latency.
4. Validate the interactive workflow in Label Studio Community, then connect the shared model/API boundary to
   the custom customer-facing GUI with confirm/change/reject decisions.
5. Keep DICOM, model monitoring, and HL7/FHIR behind the model + GUI milestone. Separately run
   `02_phase2_local_data.cmd` and the on-prem synthetic gate when scheduled; do
   not claim Phase 2 overall PASS from Phase 2A alone.

Hospital images, labels, derived features and weights remain on-premises. No clinical-use or
clinical-performance claim follows from a synthetic smoke test or public benchmark POC alone.
