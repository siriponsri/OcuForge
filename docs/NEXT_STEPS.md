# Next POC steps and remaining acceptance work

1. Execute **R0 V2 — Dataset, supervision, taxonomy and split audit** on CPU. Record source/version/access/license,
   supervision type, identity limitations, negative-ROI policy, split-before-derivation rules, taxonomy mapping,
   and checksum/provenance evidence. Do not download a large dataset in this documentation gate.
2. After R0 passes, run the controlled **R1 G0-G5 global benchmark**. Compare global, simple patch pooling,
   Attention MIL, conditional fusion, and conditional limited fine-tuning; compare CE and CORAL only for genuine
   ordinal labels. Publish held-out evidence without overstating benchmark evidence as clinical validation.
3. Complete the spatial IDRiD audit, then build the separate ROI dataset/classifier with audited negatives, top-k
   output, calibration, support, confusion matrix, and measured latency. MMRDR image-level lesion labels are not
   ROI supervision.
4. Validate the internal Label Studio Community workflow, then connect the shared model/API boundary to the
   customer-facing `templates/` GUI reference through contracts/adapters with confirm/change/reject decisions.
5. Keep DICOM, model monitoring, and HL7/FHIR behind the R1-R5 milestones. Separately run
   `02_phase2_local_data.cmd` and the on-prem synthetic gate when scheduled; do
   not claim Phase 2 overall PASS from Phase 2A alone.

Hospital images, labels, derived features and weights remain on-premises. Public GPU volumes may contain only
reviewed public/synthetic data and public research artifacts. Do not provision RunPod or download a large dataset
as part of the current R0 V2 reconciliation documentation gate. No clinical-use or clinical-performance claim follows
from a synthetic smoke test or public benchmark POC alone.
