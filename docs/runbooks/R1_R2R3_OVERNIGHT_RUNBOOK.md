# OcuForge R1 + R2/R3 Overnight Runbook

**Document type:** Active supporting execution runbook  
**Scope:** Public-data overnight research execution on RunPod, coordinated from Orca  
**Authority:** Subordinate to current owner instruction, `AGENTS.md`, contracts, and `docs/POC_MASTER_PLAN.md`  
**Default coordinator:** Main Orca workspace, Luna Max reporter/coordinator  
**Default workers:** MaxPlus Codex + Luna Max in isolated Orca worktrees  
**Cloud boundary:** Public/synthetic data only; no hospital/private data or derived private artifacts  
**Network volume:** Not used by default  
**Termination policy:** Automatic only after verified export; otherwise stop and preserve the Pod

---

## 1. Purpose

Run the next OcuForge research campaign as two supervised, independent lanes:

```text
main / Reporter
├── exp/r1-global
│   └── RunPod A
└── exp/r2-r3-roi
    └── RunPod B
```

The campaign is notebook-first for review and presentation, while reusable data/model/evaluation logic remains in normal Python modules.

Desired morning state:

- source branches committed and pushed at bounded checkpoints;
- executed notebooks with outputs available locally;
- compact machine-readable results and artifact manifests available locally;
- selected public-safe metrics/artifacts mirrored to DagsHub/MLflow where configured;
- no required result existing only inside a live Pod;
- long-run Pods automatically terminated after verified export;
- if safe termination cannot be proven, the affected Pod is stopped rather than terminated and the lane is `BLOCKED` pending OWNER review.

This runbook does **not** select an R1 architecture winner and does **not** authorize CE-vs-CORN.

---

## 2. Required authority and reading order

Before any mutation, the coordinator and workers read:

1. `AGENTS.md`
2. `HANDOFF.md`
3. `docs/POC_MASTER_PLAN.md`
4. `docs/R1_P0_ACQUISITION_PREFLIGHT.md`
5. `docs/R1_P0_ACQUISITION_PREFLIGHT.json`
6. `docs/R1_GLOBAL_MODEL_SELECTION.md`
7. `docs/GPU_EXECUTION_TH.md`
8. `docs/RUN_PARALLEL_WORKFLOW.md`
9. this runbook
10. relevant contracts, registries, configs, and tests for the assigned lane

Use:

```text
PASS
PASS_WITH_WARNINGS
BLOCKED
```

`BLOCKED` is reserved for an invalid experiment, leakage, governance/license/access violation, corrupt/incompatible required input, invalid target/split, impossible execution, or an explicit automation safety gate in this runbook.

Warnings do not stop a valid POC.

---

## 3. Protocol-alignment precondition

Current repository protocols may require a manual stop after each R1 candidate.

The overnight campaign may autonomously continue:

```text
C0 checkpoint -> C1 checkpoint -> C2 checkpoint
```

**only if current authoritative documentation explicitly allows checkpointed unattended continuation after `PASS` or `PASS_WITH_WARNINGS` with no blocker.**

This automation does not allow automatic champion selection.

If `POC_MASTER_PLAN.md` or `R1_GLOBAL_MODEL_SELECTION.md` still requires a human stop after every candidate, the coordinator must:

1. not start the long R1 campaign;
2. report `BLOCKED_PROTOCOL_ALIGNMENT`;
3. propose the smallest owner-reviewable documentation patch;
4. wait for OWNER approval and merge before unattended C0/C1/C2 execution.

Do not silently reinterpret the current protocol.

---

## 4. Provider and credential boundary

RunPod automation may use an already configured local CLI/API credential.

Rules:

- never print, paste, commit, or log the RunPod API key;
- never ask the OWNER to paste a secret into chat;
- inspect only whether required credential/configuration is available;
- if automated RunPod control cannot authenticate, return `BLOCKED_RUNPOD_AUTOMATION`;
- do not fall back to manual web clicks unless OWNER explicitly changes this runbook.

Preferred automation surface:

```text
runpodctl
or
official RunPod REST API
```

The same control surface that passes lifecycle smoke should be used for the long-run Pods where practical.

---

## 5. Cost and duplicate-resource guard

Before any paid resource creation:

1. inspect current RunPod Pods;
2. identify existing OcuForge-named resources;
3. do not create duplicates for an already-live campaign/lane;
4. record existing Pod IDs and states;
5. record the estimated hourly GPU rate before long-run creation.

Default guardrails:

```text
preferred GPU             = RTX 4090 or equivalent >=24 GB VRAM
preferred GPU count       = 1 per lane
preferred rate            <= USD 0.80/hour per Pod when practical
campaign GPU budget       <= USD 50 total
max unattended runtime    = 10 hours per long-run Pod
network volume            = none
private data              = forbidden
```

If expected spending would exceed the campaign budget, do not launch the long run.

---

## 6. Storage model without a Network Volume

This campaign intentionally does not require a RunPod Network Volume.

Use the Pod's `/workspace` volume disk for campaign working state.

```text
/workspace/
├── OcuForge/
├── ocuforge_store/
│   ├── data/
│   ├── cache/
│   ├── models/
│   ├── manifests/
│   └── artifacts/campaigns/<campaign_id>/<lane>/
└── executed_notebooks/
```

Set provider-neutral roots:

```text
OCUFORGE_DATA_ROOT=/workspace/ocuforge_store/data
OCUFORGE_MODEL_ROOT=/workspace/ocuforge_store/models
OCUFORGE_CACHE_ROOT=/workspace/ocuforge_store/cache
OCUFORGE_ARTIFACT_ROOT=/workspace/ocuforge_store/artifacts
```

Important:

- `/workspace` volume-disk data is expected to survive a **stop** while the Pod remains allocated;
- **termination deletes Pod-local data when no Network Volume is attached**;
- therefore verified export is mandatory before termination;
- container-disk-only paths such as `/tmp` are never authoritative.

---

## 7. Mandatory RunPod lifecycle smoke gate

Before any long-run Pod is created, prove that the agent can automatically:

```text
create -> detect ready -> connect -> write sentinel -> export sentinel
-> stop -> start -> verify -> terminate -> confirm gone
```

Use one short-lived smoke Pod with the intended PyTorch/Jupyter-capable template family. It must not download datasets or model weights and must not train.

Inside `/workspace` create:

```text
ocuforge_smoke/
├── lifecycle.json
└── sentinel.txt
```

`lifecycle.json` records campaign ID, Pod ID, timestamps, GPU type, base Git SHA, and sentinel SHA-256.

Required positive evidence:

1. create request returns exactly one Pod ID;
2. Pod reaches usable running state;
3. remote command/terminal succeeds;
4. sentinel is created under `/workspace`;
5. sentinel is exported to the local machine;
6. local and remote SHA-256 match;
7. automatic stop succeeds;
8. automatic start succeeds and the same `/workspace` sentinel remains readable;
9. automatic terminate/delete succeeds;
10. a subsequent query confirms the smoke Pod is gone.

Outcome:

```text
RUNPOD_AUTOMATION_SMOKE=PASS
```

Use `PASS_WITH_WARNINGS` only when automation itself is positively proven and any warning is non-blocking.

If any required lifecycle mutation cannot be automated, or cleanup state is uncertain:

```text
RUNPOD_AUTOMATION_SMOKE=BLOCKED
```

Then do not create either long-run Pod. Preserve the smoke receipt, report any possibly-live resource, and stop for OWNER review.

**No long-run experiment may begin without a positive lifecycle-smoke pass.**

---

## 8. R1-P0 ordering

R1 training remains locked until R1-P0 reaches `PASS` or `PASS_WITH_WARNINGS` with no blocking finding.

Follow the current R1-P0 contract exactly.

If current authority still forbids cloud provisioning during R1-P0, complete R1-P0 before the lifecycle smoke and long-run Pod creation.

The lifecycle smoke is infrastructure validation only. It does not count as R1-P0 evidence unless an authoritative contract explicitly says so.

Warnings from R1-P0 must propagate into every R1 artifact.

---

## 9. Orca execution topology

The main workspace is coordinator/reporter only. It must not become a training implementation workspace.

Create supervised independent worktrees:

```text
exp-r1-global
exp-r2-r3-roi
```

Experiment workers must launch through:

```text
C:\Users\Siripon Sri\bin\maxplus-codex.cmd
```

Do not use Orca's default official-Codex launcher for experiment workers.

Use Orca structured Tasks/Dispatches and lifecycle receipts.

Every Task must state `TARGET`, `CHANGE`, `CONSTRAINTS`, `OWNERSHIP`, and `OBSERVABLE ACCEPTANCE`.

---

## 10. Notebook-first execution contract

Notebooks are first-class review artifacts. Reusable logic stays in Python modules.

Each important notebook should contain:

1. objective;
2. scientific question/gate;
3. environment and Git identity;
4. dataset/model provenance;
5. QC summary;
6. exact configuration;
7. execution;
8. metrics;
9. figures;
10. error analysis/caveats;
11. gate result;
12. artifact locations;
13. next allowed action.

Preserve:

```text
source notebook
executed notebook with outputs
HTML render when practical
compact result JSON
```

Long-running notebook execution must not depend on an open browser.

Preferred:

```text
tmux -> papermill if available
     -> otherwise jupyter nbconvert --execute
```

JupyterLab is for human inspection, not process durability.

Never overwrite a previous executed notebook.

---

## 11. Lane A — R1 global DR

Dataset: **MMRDR-UWF only**.

Preserve released train/test semantics and the sealed-test rule.

After R1-P0 unlock and protocol-alignment pass:

```text
C0 ConvNeXt V2-Tiny + CE
-> checkpoint
C1 FLAIR + CE
-> checkpoint
C2 DINOv3 ViT-B/16 + Patch Attention MIL + CE
-> checkpoint
comparison/calibration/error-analysis evidence freeze
-> OWNER architecture-selection gate
```

No automatic champion. No CE-vs-CORN. No IDRiD in R1.

Suggested notebooks:

```text
notebooks/r1/
├── 00_environment.ipynb
├── 01_p0_evidence_summary.ipynb
├── 02_c0_convnext_v2_tiny.ipynb
├── 03_c1_flair.ipynb
├── 04_c2_dinov3_patch_attention_mil.ipynb
└── 05_compare_calibrate_error_analysis.ipynb
```

Required evidence where applicable:

- QWK primary;
- macro F1;
- balanced accuracy;
- per-grade recall;
- confusion matrix and support;
- calibration curve, ECE, Brier score;
- explicitly defined any-DR and moderate-or-worse metrics;
- AUROC/AUPRC only with explicit binary semantics;
- runtime, peak VRAM, estimated cost;
- model loading time where useful;
- preprocessing identity;
- asset revision/hash;
- data manifest hash;
- Git SHA, seed, warnings.

MIL attention is aggregation evidence, not lesion localization.

Reusable feature caching is allowed when scientifically valid and provenance-safe. Do not introduce asymmetric protocol changes merely for speed.

---

## 12. Lane B — R2/R3 ROI

Dataset: **IDRiD only**. DDR/OIA-DDR is not admitted.

Sequence:

```text
IDRiD acquisition/preflight
-> identity/split/leakage review
-> R2 spatial/ROI derivation
-> geometry/provenance QA
-> R3 supported-lesion baseline
-> R3 evaluation/error analysis
-> STOP
```

R2 is dataset/spatial construction, not a model.

Suggested notebooks:

```text
notebooks/r2_r3/
├── 00_environment.ipynb
├── 01_idrid_preflight.ipynb
├── 02_r2_spatial_roi_build.ipynb
├── 03_r2_geometry_provenance_qa.ipynb
├── 04_r3_roi_classifier_train.ipynb
└── 05_r3_roi_classifier_evaluate.ipynb
```

Supported R3 lesion classes:

```text
MICROANEURYSM
INTRARETINAL_HEMORRHAGE
HARD_EXUDATE
SOFT_EXUDATE
```

Preserve:

```text
GLOBAL_NO_DR
!= NO_SUPPORTED_LESION_IN_ROI
!= UNKNOWN_OR_UNSUPPORTED_FINDING
```

Unannotated does not automatically mean true negative. `UNKNOWN_OR_UNSUPPORTED_FINDING` remains a clinician-review outcome and is not automatically a learned class.

---

## 13. Checkpoint policy

At every completed bounded checkpoint:

1. validate;
2. inspect intended Git diff;
3. commit intended changes;
4. push feature branch;
5. write/update local campaign state;
6. preserve executed notebook and result JSON;
7. update artifact manifest and checksums;
8. mirror selected public-safe evidence to DagsHub/MLflow when configured;
9. update Orca Task/worktree status;
10. continue only when the next step is scientifically unlocked.

A DagsHub/MLflow logging failure alone is `PASS_WITH_WARNINGS` if the experiment remains valid and complete local evidence exists.

---

## 14. DagsHub / MLflow

Preferred experiments:

```text
ocuforge-r1-global
ocuforge-r2-spatial
ocuforge-r3-roi
```

Useful tags/params:

```text
campaign_id
lane
stage
branch
git_commit
dataset_manifest_hash
model_revision
seed
gate_result
warning_count
execution_host
pod_id
gpu_type
```

Log public-safe compact evidence only.

Do not upload hospital/private data, PHI, credentials, raw private images, private predictions/embeddings, prohibited private-derived artifacts, raw datasets by default, or full checkpoints by default.

DagsHub/MLflow is an evidence/observability mirror, not the sole authoritative store.

---

## 15. Pod-side campaign state

Each lane keeps:

```text
/workspace/ocuforge_store/artifacts/campaigns/<campaign_id>/<lane>/
├── campaign_state.json
├── stage_state.json
├── artifact_manifest.json
├── metrics/
├── figures/
├── logs/
├── reports/
└── exports/
```

`stage_state.json` includes stage, timestamps, status, Git SHA, source/executed notebook paths, metrics path, artifact manifest path, warnings, blocker, runtime, and estimated cost.

Update after each major stage.

---

## 16. Mandatory local export contract

Because no Network Volume is used, local export is mandatory before Pod termination.

Default OWNER-workstation destination:

```text
<repo>/local-state/campaigns/<campaign_id>/<lane>/
```

`local-state/` must remain Git-ignored.

Each lane creates a bounded export bundle containing, where applicable:

```text
executed notebooks
HTML notebook renders
metrics JSON/CSV
figures
artifact_manifest.json
campaign_state.json
stage_state.json
small logs needed for audit
exact configs
compact reports
selected trained model artifact needed for local continuation
model manifest/hash
```

Do not copy raw public datasets back merely for redundancy unless required by OWNER. Do not export secrets.

Large trained model artifacts required for continuation go to approved local/on-prem model storage, never Git, with path and SHA-256 recorded.

Before termination verify:

1. local export path exists;
2. export manifest parses;
3. required files exist locally;
4. hashes match Pod manifest;
5. source branch is pushed;
6. no intended Git change exists only on the Pod;
7. DagsHub/MLflow status is recorded, including warnings;
8. no active process still owns required output.

Only then set:

```text
EXPORT_VERIFIED=true
```

---

## 17. Automatic long-run Pod shutdown policy

### Successful export

When a lane reaches its stopping boundary and `EXPORT_VERIFIED=true`:

1. record final runtime and estimated cost;
2. write final manifest/state;
3. verify remote branch push;
4. terminate/delete the Pod automatically;
5. positively confirm the Pod is gone;
6. record `POD_TERMINATED=true`.

No additional OWNER confirmation is required for this runbook-authorized termination.

### Export or lifecycle uncertainty

If export cannot be verified, or termination outcome is uncertain, **do not destroy the Pod**.

Instead:

1. automatically stop the Pod if stop authority is positively available;
2. verify stopped state;
3. record Pod ID;
4. mark:

```text
RESULT=BLOCKED
BLOCKER=EXPORT_OR_TERMINATION_UNCERTAIN
POD_STOPPED_FOR_OWNER_REVIEW=true
```

5. stop the affected lane and wait for OWNER review.

This minimizes GPU cost without destroying the only copy of evidence.

### Runaway-cost guard

If a Pod approaches the configured unattended runtime or budget before completion:

1. checkpoint state;
2. persist available outputs under `/workspace`;
3. attempt verified local export;
4. stop rather than terminate when completion/export is uncertain;
5. report `BLOCKED_BUDGET_GUARD`.

---

## 18. Failure isolation

R1 and R2/R3 are independent research lanes.

If one becomes `BLOCKED`, the other may continue when scientifically valid.

Do not create duplicate replacement Pods without positive evidence that the original attempt is stopped/terminated and the orchestration recovery path authorizes replacement.

---

## 19. Morning-review deliverables

Campaign summary:

```text
CAMPAIGN_ID:
BASE_MAIN_SHA:
RUNPOD_AUTOMATION_SMOKE:
TOTAL_ESTIMATED_COST:
ACTIVE_PODS:
STOPPED_PODS:
TERMINATED_PODS:
OWNER_DECISION_NEEDED:
```

Per lane:

```text
STATUS:
COMPLETED_CHECKPOINTS:
BRANCH:
LATEST_COMMIT:
LOCAL_ARTIFACT_ROOT:
EXECUTED_NOTEBOOKS:
KEY_METRICS:
DAGSHUB_RUNS:
WARNINGS:
BLOCKERS:
POD_ID:
POD_TERMINATED:
EXPORT_VERIFIED:
NEXT_SAFE_ACTION:
```

Morning review must be possible without recreating the Pods.

---

## 20. Hard stopping boundary

This runbook ends at:

```text
R1 architecture evidence freeze
+
R2/R3 baseline/evaluation evidence freeze
+
verified local export
+
automatic long-run Pod cleanup
```

Do not merge experiment branches to `main`, select the R1 winner, run CE-vs-CORN, change lesion taxonomy, start R4/R5, move hospital/private data, or deploy a clinical service.

---

## 21. Short `/goal` launcher

```text
/goal

Run the OcuForge overnight research campaign from the current clean main.

Read AGENTS.md, HANDOFF.md, docs/POC_MASTER_PLAN.md, and
docs/runbooks/R1_R2R3_OVERNIGHT_RUNBOOK.md first.

Act only as the Main Reporter/Coordinator. Use supervised Orca workers launched through MaxPlus Codex + Luna Max.

Follow the runbook exactly: satisfy R1-P0 and protocol alignment; prove automatic RunPod create/start/stop/terminate with the mandatory short lifecycle smoke; if automation cannot be proven, mark BLOCKED and do not start long Pods; then run independent exp/r1-global and exp/r2-r3-roi notebook-first lanes; checkpoint/commit/push, export results locally, mirror public-safe evidence to DagsHub/MLflow, and use no Network Volume.

After verified local export, automatically terminate long-run Pods. If export or lifecycle safety is uncertain, stop the affected Pod and wait for OWNER review.

Do not merge to main, select the R1 winner, or run CE-vs-CORN. Stop at the morning-review boundary.
```

---

## 22. Resume `/goal`

```text
/goal

Resume the active OcuForge overnight campaign from Orca state and docs/runbooks/R1_R2R3_OVERNIGHT_RUNBOOK.md.

Inspect existing Tasks, Dispatches, worktrees, RunPod resources, Git branches, local campaign state, and DagsHub runs before mutating anything. Do not duplicate Pods, worktrees, Tasks, or experiment runs. Continue only from positively verified state and stop at the same morning-review boundary.
```

---

## 23. Owner pre-launch checklist

```text
[ ] main is clean and synchronized
[ ] runbook committed
[ ] protocol docs allow unattended C0 -> C1 -> C2 checkpoint continuation
[ ] HANDOFF points to the correct next execution path
[ ] RunPod automation exists locally without exposing secrets
[ ] DagsHub/MLflow credentials remain outside Git
[ ] local-state/ is Git-ignored
[ ] no existing OcuForge Pod will be duplicated
[ ] budget guard is accepted
```

Then launch only through the short `/goal`.
