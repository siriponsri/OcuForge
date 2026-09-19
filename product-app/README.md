# OcuForge Product POC

This is a browser-only product workflow POC for `product/encoder-head-v0.1`.

It demonstrates the planned customer path with synthetic fixtures:

- Sources and local source/destination readiness;
- Queue with the six required states;
- explicit deterministic mock `ModelAdapter` invocation;
- separate SYSTEM prediction and USER review provenance;
- rectangle, point, ellipse, polygon, and translucent-area annotation tools;
- 1 / 2 / 4 / 8 review layouts with independent case state;
- Save & Return, immutable audit events, and export receipt simulation;
- Summary grouped by source folder or SYSTEM DR grade;
- manifest eligibility and local `manifest.csv` download.

The POC does not decode DICOM in the browser, connect to NoSQL, upload to Google Drive, run a model, train a model,
create Pods, or change research state. Source and destination controls are adapter-shaped UI fixtures for the next
implementation phases. The existing `templates/` workspace remains the behavioral reference.

## Run

```bash
npm install
npm run dev
```

Open the local Vite URL printed by the command. Use the sidebar to walk through Sources, Queue, Review & Label,
Summary, and Dataset / Manifest. The demo state is persisted to browser local storage and can be reset from the
sidebar.
