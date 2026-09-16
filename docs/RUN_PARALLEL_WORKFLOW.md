# RUN Parallel Workflow

**Module:** `RUN` — Runtime / developer workflow
**Status:** Team operating procedure
**Scope:** Parallel OcuForge development using separate Git branches, worktrees, terminals, agents, PRs, and cleanup
**Authority:** Repository workflow guidance subordinate to `AGENTS.md` and `docs/CTR_MODULE_CONTRACT.md`

The current POC sequence is the V3 evidence-driven two-track plan. See
[POC_MASTER_PLAN.md](POC_MASTER_PLAN.md) for the authoritative priority and
[R0_DATASET_SUPERVISION_FREEZE.md](R0_DATASET_SUPERVISION_FREEZE.md) for the current pre-execution gate.

---

## 1. Purpose

OcuForge supports parallel work so the Labeler and Research arms can progress independently without sharing one mutable working tree.

The default parallel topology is:

```text
OcuForge/          main integration worktree
OcuForge-LBL/      Labeler Arm worktree
OcuForge-RSC/      Research Arm worktree
```

Typical ownership:

| Arm | Primary modules | Typical work |
|---|---|---|
| Labeler Arm | `LBL`, `DAT`, local/on-prem `RUN` | Label Studio Community ROI QA, retained CVAT workflow, MongoDB, adjudication, local releases |
| Research Arm | `MDL`, `RSC`, public/synthetic `RUN` | R0 audit, C0/C1/C2 global candidates, ROI track, evaluation, public jobs |
| GUI integration | `RUN` with `LBL` and shared `CTR` | customer-facing ROI interaction, model API integration, confirm/change/reject UX |
| Shared boundary | `CTR` | schemas, protocols, shared provenance/semantic contracts |

`CTR` is not privately owned by either arm. A change to a shared contract is an integration decision, not an incidental feature edit.

---

## 2. Core Rules

1. One active agent owns one writable worktree.
2. Do not run two coding agents in the same working tree.
3. Keep the primary `main` worktree for integration/review whenever practical.
4. Use one branch per bounded objective.
5. Do not mix unrelated Labeler and Research changes in one branch.
6. Do not modify `CTR` concurrently from both arms.
7. Keep hospital/private data local/on-prem regardless of branch or machine.
8. Public GPU branches may use only reviewed public/synthetic data.
9. A completed branch is temporary: after integration, remove its worktree and delete the branch.
10. Never delete unmerged work unless the owner explicitly authorizes discarding it.

---

## 3. Manual Setup — Two Arms

From the clean primary repository:

```powershell
git switch main
git pull --ff-only origin main
git status
```

Create the two arm worktrees only when parallel work is actually needed:

```powershell
git worktree add ..\OcuForge-LBL -b arm/lbl
git worktree add ..\OcuForge-RSC -b arm/rsc
git worktree list
```

Suggested terminal layout:

```text
Terminal 1
C:\...\OcuForge-LBL
Labeler Arm

Terminal 2
C:\...\OcuForge-RSC
Research Arm

Primary terminal
C:\...\OcuForge
main / integration / review
```

If `arm/lbl` or `arm/rsc` already exists, do not recreate it blindly. Inspect:

```powershell
git branch --all
git worktree list
```

---

## 4. Preferred Feature-Branch Pattern

For clean history, an arm worktree should normally create a short-lived feature branch for each bounded objective.

Example — Labeler:

```powershell
cd ..\OcuForge-LBL
git fetch origin
git switch arm/lbl
git rebase origin/main
git switch -c feat/lbl-live-cvat
```

Example — Research:

```powershell
cd ..\OcuForge-RSC
git fetch origin
git switch arm/rsc
git rebase origin/main
git switch -c feat/mdl-public-baseline
```

Branch names should communicate module and intent, for example:

```text
feat/lbl-live-cvat
feat/dat-release-manifest
feat/mdl-dinov3-baseline
feat/rsc-public-dataset-audit
fix/run-vast-launcher
docs/ctr-schema-policy
```

Do not create a branch merely to rename or reorganize unrelated files.

---

## 5. Before Starting Work

In the feature worktree:

```powershell
git status
git branch --show-current
git log -1 --oneline
```

Confirm:

```text
working tree clean
correct feature branch
correct latest integration base
```

Then identify:

```text
Primary module:
Supporting module(s):
Shared CTR change required: yes/no
Runtime/data boundary affected: yes/no
Current phase/gate:
```

If a `CTR` change is required and the other arm may depend on it, stop and coordinate the contract change first.

---

## 6. While Two Arms Are Running

### Labeler Arm

Usually writes under:

```text
eyes-detected-labeler/
deploy/onprem/
docs/LBL_*
docs/DAT_*
```

### Research Arm

Usually writes under:

```text
eyes-detected-models/
deploy/vast/
docs/MDL_*
docs/RSC_*
validation/
```

### Shared / Integration-Controlled Areas

Treat these as coordination-sensitive:

```text
eyes-detected-contracts/
docs/CTR_*
AGENTS.md
docs/CTR_MODULE_CONTRACT.md
docs/PROJECT_MAP.md
shared root configs
shared CI workflows
```

Before an arm modifies a coordination-sensitive file, check whether the other arm has pending edits to the same area.

---

## 7. Validation Before Integration

Each branch must run the narrow tests for its objective and the repository gates required by `AGENTS.md`.

At minimum, when applicable:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe scripts\validate_configs.py
.\.venv\Scripts\python.exe scripts\package_check.py
git diff --check
```

Live gates remain real integration gates. Do not replace live MongoDB, CVAT, GPU, model-weight, or deployment checks with mocks and call them PASS.

---

## 8. Commit and Push

Review first:

```powershell
git status --short
git diff --check
git diff --stat
git diff
```

Then stage only intended files:

```powershell
git add <intended-files>
git diff --cached --check
git diff --cached --stat
git diff --cached
```

Commit:

```powershell
git commit -m "<concise imperative subject>"
```

Push the feature branch:

```powershell
git push -u origin <feature-branch>
```

Do not push unrelated feature work directly to `main` when parallel arms are active unless the owner explicitly chooses that integration mode.

---

## 9. Integration

Preferred integration path:

```text
feature branch
    ↓
Pull Request
    ↓
CI
    ↓
review
    ↓
merge to main
```

Before merge, ensure:

- tests for the feature branch pass;
- shared contract changes were coordinated;
- no hospital/private artifact entered Git;
- no unrelated arm work is included;
- branch is reasonably up to date with `main`.

If the owner explicitly chooses manual integration instead of PR, preserve the same review and validation discipline.

---

## 10. Mandatory Cleanup After Merge

A merged feature branch must not be left indefinitely.

### Step 1 — Verify main contains the merge

In the primary worktree:

```powershell
cd C:\path\to\OcuForge
git switch main
git pull --ff-only origin main
git log --oneline -5
git status
```

Only continue cleanup after the intended commit/merge is visible on `main`.

### Step 2 — Remove the completed feature worktree when dedicated to that branch

From outside that worktree:

```powershell
git worktree list
git worktree remove <path-to-feature-worktree>
```

If the arm worktree itself is being retained for the next objective, switch it back to the arm branch instead of deleting the whole arm worktree.

### Step 3 — Delete the merged local feature branch

```powershell
git branch -d <feature-branch>
```

Use `-d`, not `-D`, by default. `-d` protects against deleting unmerged work.

### Step 4 — Delete the merged remote feature branch

```powershell
git push origin --delete <feature-branch>
```

Do this after confirming the branch is fully integrated and no teammate still needs it.

### Step 5 — Prune stale metadata

```powershell
git fetch --prune
git worktree prune
```

### Step 6 — Verify repository hygiene

```powershell
git worktree list
git branch
git branch -r
git status
```

Expected end state:

```text
main is clean and up to date
no stale completed worktree
no stale merged feature branch
active arm branches/worktrees only if still intentionally in use
```

---

## 11. Closing an Entire Arm

When an arm has no remaining parallel work and its branch is fully integrated:

1. Verify all arm work is merged.
2. Remove the arm worktree.
3. Delete the local arm branch.
4. Delete the remote arm branch if one was pushed.
5. Fetch/prune.
6. Confirm only intentional branches remain.

Example:

```powershell
cd C:\path\to\OcuForge

git switch main
git pull --ff-only origin main

git worktree remove ..\OcuForge-LBL
git branch -d arm/lbl
git push origin --delete arm/lbl

git fetch --prune
git worktree prune
git worktree list
git branch --all
git status
```

Never use this cleanup sequence if `arm/lbl` contains unmerged commits.

---

## 12. Updating an Arm From Main

When `main` changes while an arm is still active:

```powershell
git fetch origin
git rebase origin/main
```

or, when the team intentionally prefers merge-based synchronization:

```powershell
git fetch origin
git merge origin/main
```

Use one strategy consistently within the active branch. Do not casually rewrite published branch history that teammates are using.

If conflicts involve `CTR` contracts or clinical/data semantics, stop and review them explicitly rather than resolving mechanically.

---

## 13. Failure / Recovery Rules

### Dirty worktree before switching

Do not reset automatically.

Inspect:

```powershell
git status
git diff
```

Commit, stash, or discard only with an explicit decision.

### Branch already exists

Inspect:

```powershell
git branch --all
git worktree list
```

Reuse or reconcile it; do not overwrite it blindly.

### Worktree removal fails

Check for uncommitted work:

```powershell
git -C <worktree-path> status
```

Do not force-remove a dirty worktree unless the owner explicitly authorizes discarding it.

### Remote branch deletion fails

Verify whether it was already removed:

```powershell
git fetch --prune
git branch -r
```

### Feature branch was merged but local branch says not merged

Verify the actual merge/rebase/squash strategy before using force deletion. With squash merges, Git may not recognize the branch as merged even though its content is present. Confirm the PR/commit/content first, then delete only with owner authorization if `-d` refuses.

---

## 14. Recommended Operating Model

```text
                         main
                 integration / review
                         │
              ┌──────────┴──────────┐
              │                     │
          Labeler Arm           Research Arm
        LBL + DAT + RUN        MDL + RSC + RUN
              │                     │
       feature branches       feature branches
              │                     │
              PR                    PR
              │                     │
              CI                    CI
              └──────────┬──────────┘
                         │
                       main
                         │
                  branch cleanup
```

`CTR` remains the controlled shared boundary between the arms.

---

## 15. End-of-Task Handoff Checklist

Before declaring a branch finished, report:

```text
Branch:
Primary module:
Objective:
Tests:
PR / merge result:
Main contains work: yes/no
Worktree removed: yes/no/not applicable
Local branch deleted: yes/no
Remote branch deleted: yes/no/not applicable
git fetch --prune: pass/fail
git worktree prune: pass/fail
Final main status: clean/dirty
Unresolved issue:
```

A task is not operationally closed until branch/worktree cleanup is complete or explicitly deferred with a reason.
