# Source review and limitations

Review date: 2026-09-15. Supplied PDFs were inspected locally; no patient images or model artifacts were opened. Source claims are separated from local validation.

| Source | Inspection | Implementation consequence |
|---|---|---|
| ICO Guidelines for Diabetic Eye Care, Updated 2017 | Supplied PDF, Table 1, printed p.2 / PDF p.7; original hash in protocol config | Primary grading terminology and criteria; independent DME axis; local protocol versioning |
| Gong et al., Representation Transfer of Foundation Models for Ultra-Widefield Retinal Imaging, arXiv:2608.00586 | Supplied PDF; abstract/methods | DINOv3 patch-MIL target; reported benchmark result is not local accuracy |
| Wang et al., Deep semi-supervised multiple instance learning with self-correction for DME classification from OCT images, Medical Image Analysis 83, 102673 | Supplied PDF | OCT volume-level DME work; not evidence for fundus DME or pixel GT |
| Kim et al., Active Learning Under Expert-Budget Constraints, Bioengineering 13(7), 762 | Supplied PDF | Strategy depends on stage; paper reports no significant overall labeling-time reduction in crossover, so no time-saving claim |
| Zhou et al., A foundation model for generalizable disease detection from retinal images, Nature 622, 156–163 | Supplied PDF | RETFound challenger planned; no local zero-label accuracy inference |
| [Official DINOv3 repository](https://github.com/facebookresearch/dinov3) | Official README inspected | Local torch.hub loader interface; weights require separate access |
| [Official ViT-B/16 model card](https://huggingface.co/facebook/dinov3-vitb16-pretrain-lvd1689m) and [license page](https://huggingface.co/facebook/dinov3-vitb16-pretrain-lvd1689m/blob/main/LICENSE.md) | Public identity/access metadata inspected; no weight download | Gated custom terms; license acceptance is not completed by starter |
| [CVAT SDK](https://docs.cvat.ai/docs/api_sdk/sdk/) and [shape request API](https://docs.cvat.ai/docs/api_sdk/sdk/reference/models/labeled-shape-request/) | Official docs inspected | API-shaped bridge; actual local server compatibility remains external |
| MMRDR Figshare record [29423747](https://figshare.com/articles/dataset/MMRDR/29423747), version 2 | Public record/API metadata checked; CC BY 4.0, 10,404 UWF images, multipart MD5 metadata recorded | Candidate global source `mmrdr_uwf_v1`; preserve the released patient-level split and verify downloaded files during R0 |
| MMRDR Scientific Data DOI 10.1038/s41597-026-07005-9 | UWF ordinal grades, seven image-level lesion fields, UWF split and laterality semantics reviewed | Image-level lesion presence never becomes ROI geometry |
| IDRiD Grand Challenge / IEEE DataPort | 516 CFP images, 413/103 release split, localized MA/hemorrhage/hard-exudate/soft-exudate masks | Candidate ROI source `idrid_v1`, but license terms and SHA-256 inventory remain local-audit gates; not public-cloud eligible yet |
| DDR, DeepDRiD, EyePACS, Messidor-2 | Candidate sources compared against the smallest R0 audit set | Deferred or not selected; see the R0 audit record for reasons |

The user's old Drive runbook/license notes were read for project continuity. No old metric, weight, deployment or license status is promoted into this release. Longitudinal prediction and SAM3 remain outside this starter.

The paper PDFs and ICO PDF are not redistributed. Keep the supplied originals in the project's controlled documentation area. Public links above are source references, not upload targets.

## Current POC research position

The authoritative evidence-driven plan is [POC_MASTER_PLAN_V2.md](POC_MASTER_PLAN_V2.md). The former
model-first interactive lesion plan is retained only as a superseded historical pointer. The current plan is a
planning decision, not evidence that a final taxonomy, dataset license, class count, or model performance has been validated. The
active-learning source supports AI suggestion plus human
review pattern, but it does not establish the exact OcuForge lesion classes or clinical utility.

R0 V2 is READY TO EXECUTE, not passed. MMRDR is a candidate global source and IDRiD is a candidate spatial ROI
source pending the new audit. The initial ROI taxonomy is limited to spatially supported classes and may not be
expanded merely to reach a target count. MMRDR image-level presence labels remain separate from ROI supervision;
optic disc is structural, not a lesion, and DME remains a separate OCT axis. Unannotated ROIs are not automatic
negatives. No private clinical data or derived artifact is eligible for public GPU execution.

The next implementation gate after R0 is the R1 G0-G5 global benchmark. DINOv3 plus Attention MIL is a leading
candidate, not a frozen champion; CE versus CORAL is an ablation for genuine ordinal labels only. It is ready but
not executed; no real data download, RunPod provisioning, or large GPU run is included in this documentation update.
