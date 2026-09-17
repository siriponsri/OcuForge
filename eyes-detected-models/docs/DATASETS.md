# Dataset registry

Declarations live in `configs/datasets/`. They identify source/license/split semantics and never download data.

R0 V3 candidate register after the taxonomy freeze; acquisition and integrity checks are separated into R1-P0:

- **MMRDR UWF (`mmrdr_uwf_v1`)** is the candidate global source: Figshare record version 2,
  DOI `10.6084/m9.figshare.29423747.v2`, CC BY 4.0, 10,404 UWF images, genuine ordinal DR grades 0-4,
  and seven image-level lesion-presence fields. The manifest records Figshare multipart MD5 metadata.
- **IDRiD (`idrid_v1`)** is the deferred R2/R3 ROI source: 516 CFP images, released 413/103 split, and localized
  MA, hemorrhage, hard-exudate, and soft-exudate masks. It remains `cloud_eligible: false` until local terms, file
  inventory, and SHA-256 checksums are verified, and it is not an R1 global training dependency.

MMRDR lesion presence never becomes ROI geometry. DDR, DeepDRiD, EyePACS, and Messidor-2 remain deferred or
not selected for the first audit set. No registry entry downloads data; a future GPU run must download directly
from the official/public source to the configured data root only after the relevant gate passes. R0 passes; R1-P0
Global must complete MMRDR acquisition and integrity checks after the V3 supervision/taxonomy/pretraining-overlap
re-audit. IDRiD acquisition and integrity checks belong to the later R2/R3 gate.

Local source: DR/no-DR experience-based assessment, no ordinal grades, masks or points. A future local importer must use de-identified IDs, exact file hashes and metadata; preserve UNKNOWN values where grouping/camera information is unavailable. Do not infer patient grouping from a filename without a verified mapping.

Dataset-specific HE ambiguity is encoded in `label_mapping.json`: MMRDR HE means hard exudate, IDRiD HE means hemorrhage. NV and VB/IRMA are presence groups, not automatic NVD/NVE or geometry labels.

Raw-data audit, file inventory, checksum verification, and corruption scanning remain required before using any
downloaded bytes. No hospital data was inspected in this R0 V3 reconciliation change.
