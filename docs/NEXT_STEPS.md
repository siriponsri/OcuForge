# Next POC steps and remaining acceptance work

1. Run the approved **R1 / B1 global baseline** on MMRDR after mounting an approved persistent public-data
   filesystem and recording the DINOv3 checkout, weights, SHA-256, license decision, image digest, and commit.
   Use the configurable storage roots documented in the [GPU runbook](GPU_EXECUTION_TH.md); do not add provider
   paths to model/data logic.
2. Publish the held-out TEST evidence report without overstating benchmark evidence as clinical validation.
3. Complete the IDRiD local audit, then build the ROI dataset and lesion classifier with audited negatives, top-k output, calibration, support,
   confusion matrix, and measured latency.
4. Validate the interactive workflow in Label Studio Community, then connect the shared model/API boundary to
   the custom customer-facing GUI with confirm/change/reject decisions.
5. Keep DICOM, model monitoring, and HL7/FHIR behind the model + GUI milestone. Separately run
   `02_phase2_local_data.cmd` and the on-prem synthetic gate when scheduled; do
   not claim Phase 2 overall PASS from Phase 2A alone.

Hospital images, labels, derived features and weights remain on-premises. Public GPU volumes may contain only
reviewed public/synthetic data and public research artifacts. Do not provision RunPod or download a large dataset
as part of the current R0/R1-ready documentation gate. No clinical-use or clinical-performance claim follows
from a synthetic smoke test or public benchmark POC alone.
