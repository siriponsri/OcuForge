# REFERENCES & SOURCE LIMITATIONS

This file records the evidence base behind the starter architecture and, equally importantly, what each source **does not** prove.

---

# 1. MMRDR

**A multimodal retinal image dataset for diabetic retinopathy detection using foundation models.**  
Scientific Data, 2026.  
DOI: `10.1038/s41597-026-07005-9`

Key verified facts:
- 24,460 images total;
- 11,118 CFP;
- 10,404 UWF;
- 2,938 OCT;
- 5-grade DR severity;
- seven lesion types recorded for CFP/UWF;
- three-class DME grading on OCT;
- UWF/OCT splits performed at patient level;
- UWF/CFP CSV lesion field is a seven-element binary array.

Critical limitation:
- lesion field is image-level presence, not pixel-level lesion localization.

Public data record:
`https://figshare.com/articles/dataset/MMRDR/29423747`

---

# 2. DINOv3

Official repository:
`https://github.com/facebookresearch/dinov3`

The official package metadata currently declares Python `>=3.11`.

License:
DINOv3-specific license agreement applies; the starter must record/review it rather than assume unrestricted redistribution.

Do not bundle weights in the GPT Work starter.

---

# 3. UWF representation transfer

**Representation Transfer of Foundation Models for Ultra-Widefield Retinal Imaging.**  
Gong et al., arXiv:2608.00586, 2026.

Key contribution for this plan:
- patch-based MIL evaluation for UWF;
- controlled foundation-model representation comparison;
- DINOv3 strong overall frozen-transfer result;
- five-grade DR QWK reported around 0.863 in the paper's setting.

Limitation:
- paper results do not establish performance on the local hospital dataset;
- attention is not lesion ground truth.

---

# 4. RETFound

**A foundation model for generalizable disease detection from retinal images.**  
Nature 622, 156–163 (2023).  
DOI: `10.1038/s41586-023-06555-x`

Key verified fact:
RETFound learned retinal representations from ~1.6 million unlabeled retinal images and was adapted to downstream disease tasks with labels.

Limitation:
- not UWF-specific;
- not a zero-label local DR grader.

---

# 5. IDRiD

Official challenge data page:
`https://idrid.grand-challenge.org/Data/`

Key verified facts:
- 516 conventional fundus images;
- Kowa VX-10 alpha, ~50° FOV;
- 81 images with pixel-level lesion annotations;
- lesion masks include microaneurysms, soft exudates, hard exudates, and hemorrhages;
- optic disc and fovea information available.

Use:
- lesion-localization bootstrapping;
- annotation workflow test.

Limitation:
- conventional fundus domain differs from UWF;
- local/UWF generalization must be tested.

---

# 6. OIA-DDR / DDR

Official repository:
`https://github.com/nkicsl/DDR-dataset`

Described as a dataset for:
- DR classification;
- lesion segmentation;
- lesion detection.

Before production use:
- verify exact files/subsets;
- verify dataset license and redistribution terms;
- register label scope.

---

# 7. DeepDRiD

Repository:
`https://github.com/deepdrdoc/DeepDRiD`

Paper:
**DeepDRiD: Diabetic Retinopathy—Grading and Image Quality Estimation Challenge.**  
Patterns, 2022.

Use:
- grading;
- image-quality research;
- external benchmark.

Do not assume IDRiD-style lesion masks.

---

# 8. Active learning / expert budget

**Active Learning Under Expert-Budget Constraints: A Human-in-the-Loop Pipeline for Diabetic Retinopathy Lesion Detection.**  
Kim et al., Bioengineering 2026, 13(7), 762.  
DOI: `10.3390/bioengineering13070762`

Verified elements:
- YOLOv8x lesion detector;
- MA/hemorrhage/exudate detection;
- in-hospital clinician refinement of AI pre-labels;
- random, confidence, Hybrid-Diversity, MC Dropout strategies;
- started from 81 labeled images and expanded by 50/round to 481;
- illustrates that active learning strategy should account for expert-budget constraints.

Use:
- design inspiration for Track B pre-label review;
- active-learning strategy matrix.

Limitation:
- does not prove the same strategy is optimal for the local UWF workflow.

---

# 9. CVAT

Official docs:
- annotation manual: `https://docs.cvat.ai/docs/annotation/manual-annotation/`
- AI tools: `https://docs.cvat.ai/docs/annotation/tools/ai-tools/`
- automatic annotation: `https://docs.cvat.ai/docs/annotation/auto-annotation/`
- annotator specification: `https://docs.cvat.ai/docs/annotation/specification/`

Verified capabilities:
- manual shape annotation;
- AI-assisted/automatic annotation workflows;
- model integration pathways;
- project/task annotator guides.

SAM2 support varies by deployment mode/version; verify exact local/self-hosted capability before promising it to clinicians.

---

# 10. FiftyOne

Official CVAT integration walkthrough:
`https://docs.voxel51.com/tutorials/cvat_annotation.html`

Use:
- dataset curation;
- selecting samples;
- sending subsets to CVAT;
- importing annotations back.

Optional in v0.1.

---

# 11. MONAI Label

Official docs:
`https://docs.monai.io/projects/label/en/latest/`

Potential future role:
- OCT/medical image interactive labeling;
- active-learning-assisted medical annotation.

Not required for the initial UWF/fundus Track B starter.

---

# 12. Scientific boundary table

| Claim | Supported now? |
|---|---|
| MMRDR has 10,404 UWF images | yes |
| MMRDR UWF has 5-grade DR | yes |
| MMRDR UWF has seven lesion presence labels | yes |
| MMRDR UWF has pixel masks for all seven lesions | **no** |
| IDRiD has pixel masks for MA/HE/EX/SE | yes |
| DINOv3 patch-attention MIL is strong on published UWF benchmark | yes, in Gong et al.'s setting |
| DINOv3 is clinically validated on local hospital UWF | **no** |
| MIL attention is lesion ground truth | **no** |
| Fundus/UWF alone equals OCT-confirmed DME | **no** |
| CVAT can be used for AI-assisted annotation | yes |
| A specific CVAT SAM2 mode is guaranteed in every self-hosted configuration | **no; verify deployment** |
| active learning will reduce doctor time in our site | **not established** |
| local zero-label adaptation improves local clinical accuracy | **not established until labeled evaluation** |

---

# 13. Reference update rule

Before main experiments:
- re-check model repository/version;
- re-check dataset access/license;
- re-check CVAT integration mode;
- freeze DOI/repository commit where possible.

The starter package should not hard-code assumptions that change silently.
