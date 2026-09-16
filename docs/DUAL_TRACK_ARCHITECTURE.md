# Dual-track architecture

```mermaid
flowchart TD
 A["Reviewed public / synthetic data"] --> G["MDL-A global retinal model"]
 A --> R["Audited ROI annotations"]
 R --> L["MDL-B ROI lesion classifier"]
 G --> C["Shared CTR model / provenance contracts"]
 L --> C
 C --> S["Label Studio Community internal ROI QA"]
 C --> U["Custom GUI customer POC"]
 S --> H["Confirm / change / reject"]
 U --> H
 V["CVAT optional advanced labeling"] --> C
```

The current POC follows the evidence-driven sequence in [POC_MASTER_PLAN_V2.md](POC_MASTER_PLAN_V2.md): R0
supervision audit, R1 global G0-G5 benchmark, separate spatial ROI track, then review/integration milestones.
Label Studio Community is an internal ROI labeling/QA workbench; `templates/` is the preferred customer-facing
GUI reference; CVAT remains optional advanced infrastructure. Contracts contain no
torch, GUI, Label Studio, or CVAT implementation. The root
integration script orchestrates packages through files. Seven schemas are generated from Pydantic models. JSON
Schema validates structural constraints; the Python validator also enforces geometry,
modality/provenance, protocol and cross-record invariants.

Image coordinates use normalized pixel centers: x=0..width-1, y=0..height-1. Patches use canvas crop edges and explicit source affine mapping; source coordinates may extend into letterbox padding and must be clipped only for display. Source images are never silently cropped.

Feature cache identity covers encoder weights, preprocessing, geometry, dimensions, dataset/image identity and runtime provenance. Sentinel/validation/test records cannot enter trainable annotation queues. Training ingest additionally requires a TRAIN image, non-AI origin and eligible review state. Patient, eye, visit and exact-hash overlaps fail validation.

ICO protocol identity belongs to each grading record. Binary experience assessments are source metadata, not a missing ordinal grade to fill automatically. A future schema change needs a migration note and explicit revalidation.
