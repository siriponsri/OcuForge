# OcuForge R1 + R2/R3 Overnight Runbook

**Document type:** Active supporting execution runbook  
**Scope:** Public-data overnight research execution on RunPod, coordinated from Orca  
**Authority:** Subordinate to current owner instruction, `AGENTS.md`, contracts, and `docs/POC_MASTER_PLAN.md`  
**Default coordinator:** Main Orca workspace, Luna Max reporter/coordinator  
**Default workers:** MaxPlus Codex + Luna Max in isolated Orca worktrees  
**Cloud boundary:** Public/synthetic data only; no hospital/private data or derived private artifacts  
**Network volume:** Not used by default  
**Termination policy:** Automatic only after verified export; otherwise stop and preserve the Pod
**Experiment mirror:** DagsHub/MLflow — `https://dagshub.com/siriponsri/OcuForge/experiments`

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

Before any long-run Pod is created, prove the normal overnight lifecycle path:

```text
create -> detect ready -> connect -> secure gated-asset access
-> write sentinel -> export sentinel -> hash verify
-> terminate -> confirm gone
```

Use one short-lived smoke Pod with the intended PyTorch/Jupyter-capable template family. It must not download full datasets, full model checkpoints, or train.

Credential safety is part of the smoke:

- never place `HF_TOKEN` or `RUNPOD_API_KEY` in Git, notebooks, DagsHub artifacts, receipts, or command output;
- do not use a Pod configuration/inspection path that reveals secret values in normal output;
- prefer secure post-connect secret propagation (for example SSH/stdin or an equivalent non-logging mechanism);
- if a secret is exposed in output, treat it as `BLOCKED_CREDENTIAL_SAFETY`, revoke/rotate it, and do not continue with that credential.

Inside `/workspace` create:

```text
ocuforge_smoke/
├── lifecycle.json
└── sentinel.txt
```

Required positive evidence:

1. create returns exactly one Pod ID;
2. the Pod reaches a usable running state;
3. remote command succeeds;
4. exact gated C2 access is verified without exposing credentials;
5. all four OcuForge roots are writable;
6. the sentinel is created under `/workspace`;
7. the sentinel is exported to the OWNER workstation;
8. local and remote SHA-256 match;
9. terminate/delete succeeds;
10. a subsequent query confirms the smoke Pod is gone.

A single `stop -> start` persistence attempt may be performed as a **recovery-path probe**, but it is not a mandatory success condition for the normal overnight path. If restart fails only because the provider reports insufficient GPU capacity, record `PASS_WITH_WARNINGS` when all normal-path controls above have passed and no required evidence is lost.

If export is uncertain during a real campaign, stop the Pod and preserve it for OWNER recovery review; do not terminate it.

Valid outcomes:

```text
RUNPOD_AUTOMATION_SMOKE=PASS
RUNPOD_AUTOMATION_SMOKE=PASS_WITH_WARNINGS
RUNPOD_AUTOMATION_SMOKE=BLOCKED
```

No long-run experiment may begin without `PASS` or `PASS_WITH_WARNINGS` and no remaining blocker.

---

## 8. R1-P0 ordering

R1 training remains locked until R1-P0 reaches `PASS` or `PASS_WITH_WARNINGS` with no blocking finding.

For this OWNER-authorized campaign, RunPod may be used for **infrastructure smoke and R1-P0 runtime/acquisition validation** using reviewed public/model assets. This does not authorize model training before P0 unlock.

The intended order is:

```text
infrastructure smoke
-> R1-P0 acquisition/runtime checks on the intended RunPod environment
-> R1-P0 PASS / PASS_WITH_WARNINGS with no blocker
-> C0 -> C1 -> C2
```

The lifecycle smoke is infrastructure evidence, not scientific P0 evidence.

If the authoritative main branch still states that no cloud provisioning is allowed during R1-P0, the coordinator must make the smallest documentation-only alignment required to encode the OWNER decision before paid P0 execution. Do not weaken dataset, split, target, model-asset, leakage, or license rules.

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

The authoritative training/evaluation execution should use durable project Python modules/scripts under process supervision such as `tmux`. JupyterLab is not required to stay open.

Notebooks are required **reproducibility and review artifacts**, not necessarily the process that performed the authoritative training.

For every completed research stage, preserve:

```text
1. authoritative script/module config + structured run artifacts
2. clean Colab-ready reproduction notebook using the same project modules/config
3. executed results/report notebook populated from authoritative run artifacts
4. HTML render when practical
5. compact machine-readable result JSON
```

Do not run a headless experiment and later represent a reconstructed report notebook as if it were the original training execution.

Colab-ready notebooks must avoid duplicating model logic. They should call the same reusable modules/configs used by RunPod and include environment/install, exact data/config inputs, exact model/revision identity, secure token instructions without embedded secrets, training/evaluation entry points, resume paths, metrics rendering, and export instructions.

Suggested R1 notebook outputs:

```text
notebooks/r1/colab/
├── C0_ConvNeXtV2_Tiny_COLAB.ipynb
├── C1_FLAIR_COLAB.ipynb
└── C2_DINOv3_MIL_COLAB.ipynb

notebooks/r1/reports/
└── R1_RESULTS_REPORT.ipynb
```

Suggested R2/R3 notebook outputs:

```text
notebooks/r2_r3/colab/
├── R2_IDRID_ROI_BUILD_COLAB.ipynb
└── R3_LESION_CLASSIFIER_COLAB.ipynb

notebooks/r2_r3/reports/
└── R2_R3_RESULTS_REPORT.ipynb
```

Never overwrite a previous executed report notebook.

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

Required notebook deliverables follow the reproduction/report contract in Section 10. The authoritative training code remains in reusable project modules/scripts.

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

Required notebook deliverables follow the reproduction/report contract in Section 10. R2/R3 construction, training, and evaluation remain implemented through reusable project modules/scripts.

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

Canonical experiment store:

```text
DagsHub repository:
https://dagshub.com/siriponsri/OcuForge

Experiments:
https://dagshub.com/siriponsri/OcuForge/experiments

MLflow tracking URI:
https://dagshub.com/siriponsri/OcuForge.mlflow
```

Preferred experiment names:

```text
ocuforge-r1-global
ocuforge-r2-spatial
ocuforge-r3-roi
```

Every bounded model/data checkpoint should attempt to create or update a corresponding DagsHub/MLflow run. Use stable run names such as:

```text
<campaign_id>__<lane>__<stage>__<candidate-or-task>
```

Required tags/params where applicable:

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
runtime_seconds
estimated_cost_usd
```

Log public-safe compact evidence such as metrics JSON/CSV, plots, confusion matrices, calibration figures, compact reports, and artifact manifests when appropriate.

Do not upload hospital/private data, PHI, credentials, raw private images, private predictions/embeddings, prohibited private-derived artifacts, raw datasets by default, or full checkpoints by default.

DagsHub/MLflow is the campaign observability/evidence mirror. Local structured artifacts and Git-tracked source/config/provenance remain authoritative. A DagsHub/MLflow outage alone is `PASS_WITH_WARNINGS` when local evidence is complete.

---

## 14A. Optional Colab MCP standby lane

After the infrastructure preflight passes and before the long run, the coordinator may configure `googlecolab/colab-mcp` as an **optional reproduction/fallback lane**.

Colab-ready reproduction notebooks are maintained through:

- Colab MCP: `https://github.com/googlecolab/colab-mcp`;
- OWNER shared Drive folder: `https://drive.google.com/drive/folders/1zfYxkamwA15N9l7Wwof0sWGkis20rh2h?usp=sharing`;
- headless Drive synchronization: `https://github.com/glotlabs/gdrive`.

Rules:

- Colab MCP is not an R1/R2/R3 scientific dependency;
- failure to configure it does not block RunPod when the RunPod path is valid;
- do not consume Colab GPU merely to keep the connection alive;
- use it for Colab-ready notebook smoke, reproduction, debugging, or later demo work;
- do not upload hospital/private data or secrets;
- record `COLAB_MCP=PASS`, `PASS_WITH_WARNINGS`, or `NOT_CONFIGURED`.

The authoritative overnight experiment remains the RunPod execution recorded by Git artifacts plus DagsHub/MLflow evidence.

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

Because no Network Volume is used, verified local export is mandatory before Pod termination.

The OWNER workstation is CPU-only with limited disk. Therefore the default export policy is **small, reviewable, reproducible artifacts first**.

Default OWNER-workstation destination:

```text
<repo>/local-state/campaigns/<campaign_id>/<lane>/
```

`local-state/` must remain Git-ignored.

Export by default:

```text
Colab-ready reproduction notebooks
executed results/report notebooks
HTML report renders
metrics JSON/CSV
figures
artifact_manifest.json
campaign_state.json
stage_state.json
small audit logs
exact configs
label mappings
preprocessing contract
calibration artifacts
backbone source/revision/hash metadata
lightweight trained head weights when scientifically valid
```

Do **not** export raw public datasets or duplicate large backbone checkpoints merely for redundancy.

For a large backbone/model asset that can be deterministically reacquired from an approved official source, record its exact source, revision, hash, preprocessing contract, and loading instructions instead of copying it to the limited local disk.

Export a full trained checkpoint only when it is uniquely required for continuation and local capacity has been positively verified.

For demo preparation, a lightweight head artifact may be exported when the corresponding backbone/feature contract is explicit. A head alone must never be represented as a standalone model if it requires a remote or separately loaded backbone.

Before termination verify:

1. local export path exists;
2. export manifest parses;
3. every required exported file exists locally;
4. hashes match the Pod manifest;
5. source branch is pushed;
6. no intended Git change exists only on the Pod;
7. DagsHub/MLflow run/status is recorded, including warnings;
8. no active process still owns required output;
9. large non-exported artifacts are reproducibly referenced by source/revision/hash or explicitly declared disposable.

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

Follow the runbook exactly: satisfy R1-P0 and protocol alignment; prove automatic RunPod create/start/stop/terminate with the mandatory short lifecycle smoke; if automation cannot be proven, mark BLOCKED and do not start long Pods; then run independent exp/r1-global and exp/r2-r3-roi lanes using durable headless project execution plus Colab-ready reproduction notebooks and executed results reports; checkpoint/commit/push, export results locally, mirror public-safe evidence to DagsHub/MLflow, and use no Network Volume.

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
[ ] DagsHub target is siriponsri/OcuForge experiments
[ ] local CPU/limited-disk export policy is accepted
[ ] local-state/ is Git-ignored
[ ] no existing OcuForge Pod will be duplicated
[ ] budget guard is accepted
```

Then launch only through the short `/goal`.
