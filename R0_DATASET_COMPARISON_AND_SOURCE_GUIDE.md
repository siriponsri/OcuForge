# OcuForge R0 Dataset Comparison & Source Guide
## Companion evidence guide for the OcuForge R0 V3 freeze

**Status:** RESEARCH COMPANION — NOT A PASS RECORD; R0 V3 ended `R0_DATASET_TAXONOMY=PASS`
**Date prepared:** 2026-09-16  
**Repository authority remains:** `docs/POC_MASTER_PLAN.md` and `docs/R0_DATASET_SUPERVISION_FREEZE.md`

This document exists to help the implementing agent understand **why each dataset is being considered, what it can and cannot supervise, which source should be treated as authoritative, and what R1-P0 still has to verify after acquisition**.

It is not a substitute for the machine-readable R0 freeze record. If this guide conflicts with an official source inspected during R0, the official source wins and the discrepancy must be documented.

---

# 1. Decision summary

The smallest useful dataset strategy for OcuForge is:

| Dataset | Primary role | Current disposition | Why it matters |
|---|---|---|---|
| **MMRDR-UWF** | R1 global DR grading | **Primary hypothesis / R0 PASS; R1-P0 pending** | UWF modality, ordinal DR labels, released patient-level train/test split; archive hashes and byte checks move to R1-P0 |
| **IDRiD** | R2/R3 lesion ROI supervision | **Primary spatial candidate / R0 PASS; R1-P0 pending** | Pixel-level masks for MA, hemorrhage, hard exudate, soft exudate; archive inventory/hashes move to R1-P0 and negatives stay conservative |
| **DDR / OIA-DDR** | Secondary spatial source + historical global anchor | **NOT ADMITTED** | Reported five-grade fundus set plus lesion-localization subset, but official data terms and archive evidence are missing |
| **EyePACS/Kaggle DR** | Large conventional-fundus robustness reference | **Deferred** | 0–4 grading, patient left/right naming, very large and restricted by competition terms |
| **RFMiD** | Historical multi-disease reference | **Historical / not R1 grading source** | Useful for retinal multi-label evidence, not a clean 0–4 DR grading source |
| **Messidor-2** | Possible external robustness source | **Deferred** | Paired fundus exams but official release has no official DR ground-truth labels |
| **DeepDRiD / other quality datasets** | Future QC/domain robustness | **Watchlist** | Potentially useful for image-quality or external testing, not required to freeze R0 core |
| **FGADR** | Possible expanded lesion supervision | **Watchlist** | Strong lesion annotation potential, but access/version/license must be audited before admission |

**Core R0 should not expand automatically.**  
MMRDR-UWF + IDRiD are the minimum primary pair. DDR may be admitted only if its exact data terms, files, split semantics, and spatial annotations are verified and add value beyond IDRiD.

---

# 2. Source priority rule

When evidence conflicts, use this order:

1. **Official dataset landing page / archive record**
2. **Official data descriptor or challenge documentation**
3. **Original publication describing the dataset**
4. **Official project repository**
5. Secondary papers describing the dataset
6. Mirrors, Kaggle reposts, personal repositories, blog posts

Do not infer the license of dataset bytes from the license of a code repository.

Do not use a mirror merely because it is easier to download.

---

# 3. Dataset cards

## 3.1 MMRDR — Multimodal Retinal Image Dataset for Diabetic Retinopathy

### Official sources

- Figshare dataset:  
  https://figshare.com/articles/dataset/MMRDR/29423747
- Published data descriptor:  
  https://www.nature.com/articles/s41597-026-07005-9
- DOI currently recorded by OcuForge pre-audit:  
  https://doi.org/10.6084/m9.figshare.29423747.v2

### What it contains

MMRDR is a multimodal DR dataset with separate CFP, OCT, and UWF subsets.

The Scientific Data descriptor states that each modality is released with train/test partitions. For **UWF and OCT**, the published split is patient-level. The CFP subset originates from OIA-DDR and lacks patient identifiers, so its released split is image-level.

The completed OcuForge R0 evidence record describes the UWF subset as:

- 10,404 UWF images
- ordinal DR grade 0–4
- additional image-level lesion-presence labels
- released patient-level train/test partition
- no documented row-level patient identifier in the published CSV description

The R0 freeze record verifies the source/version and semantics. R1-P0 must verify the downloaded bytes, schema, and split smoke.

### Why OcuForge wants it

**Primary hypothesis for R1 global grading.**

It is attractive because the target deployment story includes UWF, and using a UWF benchmark avoids pretending that strong performance on narrow-field CFP automatically transfers to UWF.

### What it can supervise

```text
global image
→ DR grade 0 / 1 / 2 / 3 / 4
```

Potential auxiliary labels:

```text
image-level lesion presence
```

### What it cannot supervise

The lesion-presence vector is **not spatial supervision**.

It does not provide a valid basis to synthesize lesion ROI coordinates, boxes, masks, lesion boundaries, or "clean negative" regions unless an independent spatial source is linked and verified.

### Split rule

Preserve the released UWF test set as sealed.

Only derive TRAIN / VALIDATION / CALIBRATION inside released training identities.

Do not reshuffle the released test images back into development.

### R0 findings and R1-P0 checks

- Exact Figshare version/revision?
- Exact file inventory needed for UWF only?
- Can UWF be downloaded separately, or does the release require the whole multipart archive?
- Exact license text attached to the chosen version?
- Exact meaning and provenance of the 0–4 grade?
- Are image names/laterality sufficient for internal validation grouping?
- Is any patient grouping information recoverable from metadata without violating the release contract?
- Are ungradable cases present and how are they encoded?
- Exact checksum/download manifest?
- Is MMRDR known to overlap with any R1 foundation model pretraining set?

### OcuForge role

```text
R1_GLOBAL_DR = PRIMARY_CANDIDATE
R2_R3_SPATIAL_ROI = NOT_ELIGIBLE_FROM_IMAGE_LEVEL_LESION_LABELS
```

---

## 3.2 IDRiD — Indian Diabetic Retinopathy Image Dataset

### Official sources

- Challenge home: https://idrid.grand-challenge.org/
- Data page: https://idrid.grand-challenge.org/Data/
- IEEE DataPort citation/record: https://doi.org/10.21227/H25W98
- Data descriptor: https://doi.org/10.3390/data3030025

### What it contains

The official data page describes:

- 516 color fundus images
- Kowa VX-10 alpha camera
- 50-degree field of view
- 4288 × 2848 JPEG images
- image-level DR/DME grading for the full set
- 81 images in the pixel-level lesion annotation subset

Pixel-level binary masks are provided for:

- microaneurysms (MA)
- hemorrhages (HE)
- hard exudates (EX)
- soft exudates (SE)

The official page states MA masks: 81 images, hard-exudate masks: 81, hemorrhage masks: 80, and soft-exudate masks: 40.

Optic-disc masks also exist, but **optic disc is anatomy, not a lesion class**.

### Why OcuForge wants it

**Primary spatial source for R2/R3.**

It directly supports the initial ROI taxonomy:

```text
MICROANEURYSM
INTRARETINAL_HEMORRHAGE
HARD_EXUDATE
SOFT_EXUDATE
```

### What it can supervise

```text
source lesion mask
→ lesion-centered ROI
→ tight crop + context crop
→ ROI classifier example
```

The original mask identity and geometry must be retained.

### What it cannot automatically supervise

An area with no mask is **not automatically a verified true negative**.

R0/R2 must determine whether absence of a particular mask means exhaustively reviewed absence, missing/partial annotation, or unknown.

Until proven, use:

```text
VERIFIED_TRUE_NEGATIVE
CURATED_BACKGROUND
WEAK_NEGATIVE
UNKNOWN
```

### Important license discrepancy to resolve

The current official IDRiD Grand Challenge data page displays a **CC BY 4.0** statement.

The completed OcuForge freeze record records:

```text
license_status = CC_BY_4.0_DISPLAYED_ON_OFFICIAL_IDRID_DATA_PAGE; IEEE_DATAPORT_ACCESS_REQUIRED
```

The source-level access path is sufficient for planned acquisition. R1-P0 verifies authorized access, archive inventory, and local hashes.

### Split limitation

The challenge has a released image-level split, but public challenge metadata does not establish a patient/eye grouping contract comparable to MMRDR-UWF.

Do not claim patient-level independence unless an authoritative mapping is found.

### OcuForge role

```text
R2_R3_SPATIAL_ROI = PRIMARY_CANDIDATE
R1_UWF_GLOBAL = NOT_PRIMARY
LOCAL_UWF_VALIDATION = NO
```

---

## 3.3 DDR / OIA-DDR

### Official sources

- Official repository: https://github.com/nkicsl/DDR-dataset
- Original publication: https://doi.org/10.1016/j.ins.2019.06.011

### What it contains

The original DDR publication describes:

- 13,673 fundus images
- five gradable DR severity classes: no DR, mild, moderate, severe, proliferative
- an additional poor-quality/ungradable category
- 757 images with lesion localization annotations
- four lesion types: microaneurysm, hemorrhage, hard exudate, soft exudate
- pixel-level and bounding-box-level lesion annotations

### Why it is attractive

DDR could provide a larger conventional-fundus grading reference, additional lesion-positive images for R2/R3, and a bridge to the project's historical Eye Detected experiments.

### Why it is not automatically Priority A

OcuForge already has IDRiD as a clean, well-described spatial starting point.

DDR adds value only if R0 verifies the exact current archive/file structure, split files, annotation format, data-use terms, checksums, and taxonomy compatibility.

### License warning

The official GitHub repository is MIT-licensed as a repository.

**Do not assume that the repository's MIT license automatically grants the same rights over downloaded medical-image data.**

DDR/OIA-DDR remains NOT_ADMITTED because its data-release terms are not sufficient for R0 selection; no R1-P0 acquisition is planned.

### FLAIR contamination warning

The official retinal FLAIR repository lists **OIA-DDR** in its retinal pretraining assembly.

Therefore DDR/OIA-DDR must not be treated as a clean unseen external-generalization test for C1 FLAIR without resolving the exact checkpoint/pretraining corpus.

### OcuForge role

```text
R2_R3_SPATIAL_ROI = SECONDARY_CANDIDATE_PENDING_R0
R1_GLOBAL = HISTORICAL_OR_SECONDARY
C1_FLAIR_EXTERNAL_TEST = POTENTIALLY_CONTAMINATED
```

---

## 3.4 EyePACS / Kaggle Diabetic Retinopathy Detection

### Official source

- Kaggle competition data: https://www.kaggle.com/c/diabetic-retinopathy-detection/data

### What it contains

The original competition provides high-resolution retinal images graded 0–4:

```text
0 No DR
1 Mild
2 Moderate
3 Severe
4 Proliferative DR
```

Image names encode subject and side such as `1_left.jpeg` and `1_right.jpeg`.

The release is very large; Kaggle currently shows approximately 88 GB across multipart archives.

### Why it is useful

- large-scale conventional-fundus robustness reference;
- natural camera/image-quality variation;
- patient left/right pairing is visible in naming.

### Why it is deferred

- competition access terms apply;
- no lesion ROI/mask supervision;
- large storage/download burden;
- not UWF;
- not necessary to answer the first R1 question.

### FLAIR contamination warning

The official retinal FLAIR repository explicitly lists **EyePACS** as part of its retinal pretraining assembly.

Therefore EyePACS is not an appropriate "clean unseen external dataset" for C1 FLAIR unless the exact checkpoint used can be proven not to include it.

### OcuForge role

```text
R1_PRIMARY = NO
FUTURE_ROBUSTNESS = POSSIBLE
ROI_SPATIAL = NO
C1_CLEAN_EXTERNAL = NO_UNLESS_EXACT_CHECKPOINT_PROVES_EXCLUSION
```

---

## 3.5 RFMiD — Retinal Fundus Multi-disease Image Dataset

### Useful source

- PubMed / Medical Image Analysis challenge report: https://pubmed.ncbi.nlm.nih.gov/39395210/

### What it is

RFMiD is designed for retinal **multi-disease screening and multi-label pathology classification**, not specifically for the five-level ordinal DR grading problem.

### Why OcuForge keeps it

The old Eye Detected work already produced useful RFMiD evidence and class-specific attribution behavior.

That evidence is historical and useful for multi-disease feasibility context, explainability/error-analysis lessons, and regression comparison of old artifacts.

### Why it is not an R1 dataset

R1 asks:

```text
What is the global DR severity grade 0–4?
```

RFMiD asks a different question.

Do not force its multi-label pathology labels into the R1 ordinal target.

### OcuForge role

```text
HISTORICAL_EVIDENCE = YES
R1_ORDINAL_SOURCE = NO
R2_R3_SPATIAL_SOURCE = NO
```

---

## 3.6 Messidor-2

### Official source

- ADCIS current page: https://www.adcis.net/en/third-party/messidor2/

### What it contains

The official page describes:

- 874 examinations
- 1,748 macula-centered fundus images
- two eye images per examination

### Critical limitation

The official Messidor-2 release states that it **does not contain official diabetic-retinopathy ground-truth annotations**.

Third-party annotations exist, but the official provider does not distribute or validate them as part of the official dataset.

### Terms

The official page states:

- free for research and educational use;
- copy/redistribution prohibited;
- unauthorized commercial use prohibited;
- download requires a form/personal access link.

### Why OcuForge defers it

It may later help external robustness work, but using third-party labels introduces a new provenance/version problem.

### OcuForge role

```text
R1_PRIMARY = NO
EXTERNAL_ROBUSTNESS = POSSIBLE_LATER
GROUND_TRUTH_PROVENANCE = MUST_BE_RESOLVED
```

---

# 4. Watchlist datasets

These are **not automatically admitted into R0**.

## FGADR

Potential strength:

- grading plus rich lesion annotations;
- useful expansion source for R2/R3.

Risks/questions:

- original data access may require request/approval;
- exact current release/version must be identified;
- license and redistribution/cloud-use terms must be reviewed;
- patient/split identities must be audited.

Decision:

```text
WATCHLIST
Do not download or add to training merely because a mirror exists.
```

## DeepDRiD / image-quality datasets

Potential value:

- image-quality assessment;
- grading/domain robustness.

Not required for the first R1 UWF benchmark or initial four-class ROI lesion classifier.

Decision:

```text
DEFER_TO_QC_OR_EXTERNAL_ROBUSTNESS
```

## DRAC 2022

DRAC 2022 includes grading, image-quality, and lesion-segmentation tasks, but its modality/task design differs from the core OcuForge UWF fundus pathway.

Decision:

```text
DO_NOT_EXPAND_R0_CORE_WITHOUT_OWNER_DECISION
```

---

# 5. R1 foundation-model overlap implications

R0 audited **datasets and pretrained assets together**; R1-P0 later verifies the exact local bytes and access/load evidence.

## C0 — ConvNeXt V2-Tiny

R0 records the exact pretrained checkpoint/source, license, preprocessing contract, source framework, and revision; local hashes and loading are R1-P0 checks.

Do not merely write "ImageNet pretrained" without the exact asset.

## C1 — retinal FLAIR

Official repository:

https://github.com/jusiro/FLAIR

The official repository currently states that code and model weights are released under Apache 2.0.

Its retinal pretraining assembly explicitly lists datasets including:

- EyePACS
- OIA-DDR
- APTOS
- ODIR-5K
- LAG
- AGAR300
- G1020
- HEI-MED
- AIROGS
- ScarDat
- ACRIMA

Implications:

- EyePACS is contaminated for a clean C1 external claim unless the exact checkpoint proves otherwise.
- DDR/OIA-DDR is contaminated or potentially contaminated for C1 depending on the exact selected checkpoint.
- IDRiD is **not automatically clean or contaminated** from this summary alone; verify the exact checkpoint/corpus documentation.
- MMRDR-UWF should not be declared clean solely because it is newer; confirm the actual pretraining corpus/revision.

Use:

```text
CONFIRMED
EXCLUDED
UNKNOWN
POTENTIALLY_CONTAMINATED
```

## C2 — DINOv3 ViT-B/16

DINOv3 uses large generic visual pretraining rather than a retinal-specific curated set.

That does **not** justify writing "no retinal overlap."

If exact source-image membership cannot be proven:

```text
overlap_status = UNKNOWN
```

is acceptable and scientifically preferable to a guessed `EXCLUDED`.

---

# 6. Recommended R0 task assignment

## Global grading

Primary candidate:

```text
MMRDR-UWF
```

R0 decided `ELIGIBLE_FOR_R1_P0` for MMRDR-UWF; R1-P0 must complete before any candidate training.

No automatic fallback should silently replace it.

## Spatial lesion classifier

Primary:

```text
IDRiD
```

Secondary only if verified and useful:

```text
DDR/OIA-DDR
```

Do not blend spatial datasets before class mapping, mask/box semantics, split identity, preprocessing, and negative policy are frozen.

## Historical datasets

Keep old DDR, IDRiD, and RFMiD results in historical evidence documents where applicable.

Historical evidence is not current R1 performance.

---

# 7. Taxonomy mapping cautions

Canonical initial ROI classes:

```text
MICROANEURYSM
INTRARETINAL_HEMORRHAGE
HARD_EXUDATE
SOFT_EXUDATE
NO_SUPPORTED_LESION_IN_ROI
```

Examples:

```text
IDRiD MA → MICROANEURYSM
IDRiD HE → INTRARETINAL_HEMORRHAGE
IDRiD EX → HARD_EXUDATE
IDRiD SE → SOFT_EXUDATE
```

Do not map based on abbreviation alone without reading the source legend.

Especially avoid confusing:

```text
HE = hemorrhage in one source
HE = hard exudate in another project's shorthand
```

Use full canonical names in machine-readable OcuForge contracts.

---

# 8. Negative ROI policy

Do not generate "negative lesion" ROIs by selecting arbitrary unannotated retina.

Every negative ROI must carry provenance:

```text
VERIFIED_TRUE_NEGATIVE
CURATED_BACKGROUND
WEAK_NEGATIVE
UNKNOWN
```

For evaluation, prefer only evidence-backed clean negatives.

`NO_SUPPORTED_LESION_IN_ROI` means none of the supported ROI lesion classes crossed the configured threshold inside this selected ROI. It does not mean normal retina, no DR, no disease, or no lesion elsewhere.

---

# 9. Download policy for R0

Allowed during R0:

- official metadata;
- README/data descriptors;
- CSV schema/header where legally and technically available;
- tiny manifest/source files;
- checksum metadata;
- access/license records.

Avoid during R0 unless strictly needed:

- tens of GB of image archives;
- full EyePACS;
- full MMRDR image extraction;
- GPU provisioning.

R0 should produce the **exact future download manifest** so R1 preparation knows what is needed.

---

# 10. R0 comparison matrix for the final freeze

| Field | MMRDR-UWF | IDRiD | DDR/OIA-DDR | EyePACS | RFMiD | Messidor-2 |
|---|---|---|---|---|---|---|
| Intended role | R1 global | R2/R3 ROI | secondary ROI/global | robustness | historical multi-label | external robustness |
| Modality | UWF | CFP | CFP | CFP | CFP | CFP |
| Genuine 0–4 DR target | verify/favored | yes | yes + ungradable category | yes | not primary task | official GT absent |
| Spatial lesion supervision | no | masks | masks + boxes reported | no | no | no official |
| Patient-safe split | released patient-level UWF split | not verified | verify | subject naming available; split terms matter | task-dependent | paired exams |
| Clean C1 FLAIR external | audit | audit | no/potential contamination | no/known overlap | audit | audit |
| Primary R0 admission | yes | yes | conditional | no | historical only | no |
| Large download needed now | no | no | no | no | no | no |

---

# 11. Exact outputs R0 should leave behind

At the end of R0, the repository should make these facts obvious without chat history:

```text
R0 status
dataset selected for R1
dataset selected for R2/R3
dataset versions
official URLs
licenses/access constraints
exact splits
identity limitations
label semantics
spatial supervision semantics
negative policy
foundation-model overlap status
asset eligibility
future download manifest
checksums/provenance
blockers
```

No field should be filled with an invented value just to achieve `PASS`.

---

# 12. Source index

## MMRDR
- Dataset: https://figshare.com/articles/dataset/MMRDR/29423747
- Data descriptor: https://www.nature.com/articles/s41597-026-07005-9

## IDRiD
- Home: https://idrid.grand-challenge.org/
- Data: https://idrid.grand-challenge.org/Data/
- IEEE DataPort DOI: https://doi.org/10.21227/H25W98
- Descriptor: https://doi.org/10.3390/data3030025

## DDR / OIA-DDR
- Official repository: https://github.com/nkicsl/DDR-dataset
- Original paper: https://doi.org/10.1016/j.ins.2019.06.011

## EyePACS
- Kaggle competition dataset: https://www.kaggle.com/c/diabetic-retinopathy-detection/data

## RFMiD
- Challenge report / PubMed: https://pubmed.ncbi.nlm.nih.gov/39395210/

## Messidor-2
- Official current page: https://www.adcis.net/en/third-party/messidor2/

## FLAIR
- Official repository: https://github.com/jusiro/FLAIR

---

# 13. Final instruction to the implementing agent

Use this guide to understand dataset roles and known risks.

Then independently verify official evidence and update the authoritative R0 record.

Do not:

- promote a dataset because this guide calls it "Priority A";
- silently substitute another dataset when one is not admitted;
- use a mirror as authoritative evidence;
- reinterpret image-level lesion labels as spatial labels;
- convert binary labels into ordinal labels;
- call a foundation-model evaluation "external" without overlap audit;
- download large data merely to make R0 look active.

The current R0 outcome is `PASS`; if future source-level evidence changes, re-audit R0 rather than weakening R1-P0 or silently substituting inputs.

Both are scientifically valid outcomes.
