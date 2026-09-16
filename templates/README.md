# DR Review Workspace — Screening Support POC

This is OcuForge's preferred customer-facing UX reference for the current POC. Future implementation should
preserve its information architecture and connect through the versioned contracts and trusted adapters described
in [the integration contract](../docs/GUI_POC_INTEGRATION.md); this package is not the model or Label Studio
implementation.

A clean, multi-page HTML proof of concept for human-reviewed diabetic retinopathy screening support. The package is English-only, runs without a build step, and starts in mock mode.

## Open the mockup

Open `index.html` in a modern browser. For the most reliable local behavior, serve the extracted folder:

```bash
python -m http.server 4173
```

Then open `http://localhost:4173`.

## User journeys

### Clinical review

1. `index.html` — see the next required action.
2. `annotate.html` — inspect one ROI and record a reviewer decision.
3. `review.html` — resolve only low-confidence, conflicting, or missing predictions.

### Model lab

1. `explainability.html` — inspect case-level evidence and its limitations.
2. `model-diff.html` — compare Model A and Model B, then inspect improved and regressed cases.
3. `integrations.html` — configure Label Studio, the trusted API bridge, and model endpoints.

## Integration files

- `label-studio/roi-lesion-label-config.xml`
- `integration/config.js`
- `integration/adapter.js`
- `integration/mock-data.js`
- `integration/annotation-contract.example.json`
- `integration/explanation-contract.example.json`
- `integration/model-diff-contract.example.json`
- `docs/INTEGRATION_GUIDE.md`
- `docs/USER_STORY.md`

## Design direction

The interface uses the information architecture and component restraint of the official Nuxt UI dashboard template as a visual reference: a grouped sidebar, compact page navbar, quiet surfaces, subtle borders, and master-detail review patterns. This static package does not bundle Nuxt UI runtime code.

## Scope

This is an interface POC, not a diagnostic product. Demonstration predictions, comparisons, evidence overlays, and workflow counts are illustrative. Clinical, privacy, security, interoperability, and model-performance validation are outside the scope of this package. Label Studio Community remains an internal ROI QA workbench; CVAT remains optional advanced annotation infrastructure.
