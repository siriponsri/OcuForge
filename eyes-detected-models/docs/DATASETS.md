# Dataset registry

Declarations live in `configs/datasets/`. Public resources are NOT_REVIEWED until exact files, license, source version and subtask labels are verified. No registry entry downloads data.

MMRDR UWF: image-level ordinal DR and seven lesion presence categories, never masks. IDRiD/DDR localization declarations require checking the actual subtask; classification-only records do not inherit pixel labels. DeepDRiD is grading/QC, not assumed lesion masks.

Local source: DR/no-DR experience-based assessment, no ordinal grades, masks or points. A future local importer must use de-identified IDs, exact file hashes and metadata; preserve UNKNOWN values where grouping/camera information is unavailable. Do not infer patient grouping from a filename without a verified mapping.

Dataset-specific HE ambiguity is encoded in `label_mapping.json`: MMRDR HE means hard exudate, IDRiD HE means hemorrhage. NV and VB/IRMA are presence groups, not automatic NVD/NVE or geometry labels.

Raw-data audit, file inventory and corruption scanning are planned for the local environment; no hospital data was inspected in starter generation.
