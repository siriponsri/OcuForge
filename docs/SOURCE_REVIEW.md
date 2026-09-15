# Source review and limitations

Review date: 2026-09-09. Supplied PDFs were inspected locally; no patient images or model artifacts were opened. Source claims are separated from local validation.

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
| MMRDR Scientific Data DOI 10.1038/s41597-026-07005-9 | Supplied specification; fresh web page retrieval failed | Registry stays NOT_REVIEWED; no download/license clearance claim |
| IDRiD, DDR, DeepDRiD, EyePACS, Messidor-2 | Declared research sources from specification; exact files/license not newly audited | Registry entries are declarations, not working download adapters or commercial clearance |

The user's old Drive runbook/license notes were read for project continuity. No old metric, weight, deployment or license status is promoted into this release. Longitudinal prediction and SAM3 remain outside this starter.

The paper PDFs and ICO PDF are not redistributed. Keep the supplied originals in the project's controlled documentation area. Public links above are source references, not upload targets.
