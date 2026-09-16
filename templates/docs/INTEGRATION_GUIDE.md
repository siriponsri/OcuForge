# Integration Guide

This package is a static proof of concept for a human-reviewed diabetic retinopathy screening support workflow. It is not a diagnostic device and must not be used for patient care.

## 1. Run the mock interface

Open `index.html` directly, or serve this directory with a local static server:

```bash
python -m http.server 4173
```

Then open `http://localhost:4173`. The default adapter mode is `mock`; no server or token is required.

## 2. Create the Label Studio project

The source project's currently documented local-labeling workflow may use a different annotation tool. The Label Studio bridge in this package is a proposed POC integration path, not a claim that Label Studio is already implemented in that workflow.

1. Run Label Studio Community Edition in the approved local environment.
2. Create a project for ROI lesion review.
3. Import `label-studio/roi-lesion-label-config.xml` into the project's labeling interface.
4. Import tasks whose data includes at least `image` and `case_context`.
5. Keep image storage and access control inside the approved environment.

The XML supports point, rectangle, and polygon ROIs with these canonical labels:

- `MICROANEURYSM`
- `INTRARETINAL_HEMORRHAGE`
- `HARD_EXUDATE`
- `SOFT_EXUDATE`
- `NO_SUPPORTED_LESION_IN_ROI`

`NO_SUPPORTED_LESION_IN_ROI` means that the selected ROI does not contain one of the supported lesion classes. It is not a patient-level normal diagnosis.

## 3. Connect a model API

The UI adapter expects these local endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/v1/infer/global` | Whole-image support response |
| `POST` | `/v1/infer/lesion-roi` | Ranked lesion suggestions for one ROI |
| `GET` | `/v1/models` | Deployed model manifest |
| `POST` | `/v1/explain/roi` | Case-level evidence response; proposed POC endpoint |
| `POST` | `/v1/evaluate/model-diff` | Version-to-version case diff; proposed POC endpoint |

Use `integration/annotation-contract.example.json` as the POC mapping target. Label Studio image-region exports use coordinates from 0 to 100; the example application contract uses normalized coordinates from 0 to 1. Convert explicitly at the adapter boundary and preserve the original geometry, model name, model version, prediction scores, original suggestion, and final human decision.

The two model-lab pages also include proposed, non-implemented contracts:

- `integration/explanation-contract.example.json`
- `integration/model-diff-contract.example.json`

These contracts are UI integration targets, not claims that the current repository implements attention serving or model-diff evaluation endpoints.

## 4. Switch from mock to live mode

Edit `integration/config.js`:

```js
mode: "live"
```

Then configure the Label Studio, API bridge, and model API base URLs. The browser adapter sends task and decision calls to the trusted bridge so Label Studio credentials are never embedded in the package.

## 5. Add a trusted bridge

Do not embed a Label Studio API token in this static package. For a real deployment, place a small trusted backend between the browser and Label Studio. That bridge should:

- hold Label Studio credentials server-side;
- expose the small browser-facing routes configured under `apiBridge.endpoints`;
- map Label Studio tasks, annotations, and predictions to the versioned contract;
- validate label names, decision states, ROI geometry, and model metadata;
- enforce authentication, authorization, audit logging, and CORS policy;
- avoid logging image content or patient-identifying fields;
- submit reviewer decisions without overwriting the original model output.

The mockup expects this small browser-facing bridge contract:

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/api/ui/project` | Return the mapped project summary |
| `GET` | `/api/ui/tasks/{taskId}` | Return one mapped task and its prediction |
| `POST` | `/api/ui/decisions` | Validate and store a reviewer decision |
| `GET` | `/api/health/label-studio` | Verify bridge-to-Label-Studio connectivity |

## 6. Adapter boundary

`integration/adapter.js` exposes a small interface:

- `getProject()`
- `getTask(taskId)`
- `inferGlobal(imageId)`
- `inferLesionRoi(payload)`
- `getExplanation(payload)`
- `compareModels(payload)`
- `submitDecision(payload)`
- `openLabelStudio(taskId)`
- `testConnection(kind)`

Keep page code dependent on this interface rather than on a specific Label Studio or model client. This allows the mock adapter to be replaced by a versioned live implementation without redesigning the UI.

## Safety boundary

- Use synthetic, public, or appropriately governed de-identified data only.
- Treat all suggestions as annotation assistance that requires human review.
- Do not show diagnosis, referral, treatment, or patient-level risk claims.
- Do not interpret a missing supported lesion in one ROI as a normal retinal examination.
- Run clinical, security, privacy, and performance validation outside this UI POC before any operational use.
