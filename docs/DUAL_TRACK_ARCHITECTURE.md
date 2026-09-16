# OcuForge dual-track architecture

**Status:** ACTIVE SUPPORTING ARCHITECTURE NOTE
**Authority:** [`POC_MASTER_PLAN.md`](POC_MASTER_PLAN.md)

Global DR grading and spatial ROI lesion classification are intentionally separate tracks. They may reuse runtime
infrastructure or encoder technology, but never share model identity, supervision semantics, objective, evaluation
protocol, artifacts, or version without an explicit contract decision.

```text
R0 freeze
  +--> R1 Global DR: genuine ordinal grade 0–4 -> Global Model
  +--> R2/R3 ROI: verified spatial supervision -> ROI Lesion Model
                                      |
                                      v
                              Versioned Model API
                              /                 \
                             v                   v
                   Label Studio Community   DR Review Workspace
                   internal ROI QA/HITL     existing customer POC
```

The Global→ROI path is a soft triage default. `GLOBAL_NO_DR` never means `NO_SUPPORTED_LESION_IN_ROI`, and MIL
attention never becomes lesion ground truth. R6 DICOM, R7 drift, and R8 HL7/FHIR are later integrations.
