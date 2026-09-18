# R1-P0 Owner Review: MMRDR Released-Split Duplicate Blocker

**Recorded:** 2026-09-19
**Review state:** `OWNER_DECISION_REQUIRED`
**P0 state:** `R1_P0_ACQUISITION_PREFLIGHT=BLOCKED`
**Training state:** `R1_TRAINING_READY=NO`
**Smoke state:** `RUNPOD_AUTOMATION_SMOKE=PASS_WITH_WARNINGS` (reused)

## Decision in one line

The only blocking R1-P0 gate is `P0-DATA-SCHEMA-SPLIT`: two exact duplicate-content groups cross the released
MMRDR `tr`/train and `ts`/test boundary. The released split remains unchanged. OWNER must approve and record
the protocol-level treatment of both groups before re-running the affected check. P0 can become `PASS` or
`PASS_WITH_WARNINGS`.

No split repair, row removal, label reinterpretation, or blocker resolution is made by this review.

## Exact blocker

The recorded duplicate groups and their released memberships are:

| Group | Released train member | Released test member | Finding |
| --- | --- | --- | --- |
| 1 | `tr003656.jpg` (`tr` / train) | `ts002433.jpg` (`ts` / test) | Exact cross-split duplicate content |
| 2 | `tr007667.jpg` (`tr` / train) | `ts002038.jpg` (`ts` / test) | Exact cross-split duplicate content |

These are the two groups named by the P0 blocker. The finding is content-level; no patient identity is
inferred.
Row-level patient IDs remain unavailable under the recorded non-blocking limitation.

## Released split integrity

- MMRDR archive integrity and extracted inventory passed: 10,404 UWF rows/images with ordinal grades `0`-`4`.
- The released `tr`/`ts` membership was preserved at 7,807/2,597, which sums to 10,404.
- No rows were silently reshuffled or excluded. The duplicate pairs remain recorded in their released sides
  above.
- The 2026-09-19 revalidation confirmed that the blocker was unchanged; it did not reacquire data or model
  bytes.
- The available compact export is runtime-scope evidence only and records `training_executed=false` and
  `benchmark_executed=false`; it does not replace the committed P0 split evidence.

## P0 check ledger

| Required check | Result | Decision-relevant evidence |
| --- | --- | --- |
| `P0-DATA-ARCHIVE` | `PASS` | Official archive integrity and extracted inventory passed. |
| `P0-DATA-SCHEMA-SPLIT` | `BLOCKED` | Grades/membership verified; two exact duplicate groups block. |
| `P0-MODEL-ASSETS` | `PASS` | Exact C0/C1/C2 assets matched the approved sources. |
| `P0-PREPROCESSING` | `PASS` | Candidate-specific preprocessing and geometry smoke passed. |
| `P0-MODEL-LOAD` | `PASS` | Approved loaders and CUDA synthetic forward checks passed. |
| `P0-GATED-ACCESS` | `PASS` | Required public access/terms checks passed without credentials in evidence. |
| `P0-STORAGE-RUNTIME` | `PASS` | Provider-neutral roots and runtime checks passed. |

Operational evidence does not change the gate: the accepted smoke result is
`PASS_WITH_WARNINGS`, and DagsHub/MLflow connectivity is a non-blocking warning. The compact revalidation
export was hash-verified. These are not resolutions of the split blocker.

## Why R1 remains forbidden

The P0 contract permits training only when the state is `PASS` or `PASS_WITH_WARNINGS`
**and no blocking finding remains**. Split leakage is an explicit blocking condition. Therefore:

- C0, C1, and C2 training must not start.
- The R1 benchmark and any comparison, calibration, or champion selection must not start.
- No R1 metric, model result, or current champion exists.
- Reusing the infrastructure smoke result does not unlock scientific execution.

## OWNER protocol decision required

OWNER must approve a versioned, reproducible protocol disposition for both duplicate groups. The decision
record must state, for each pair:

1. the approved treatment of the released train/test membership;
2. the exact source and derived-manifest identities, including a complete row-level diff if membership
   changes;
3. how the sealed-test rule and original released split are preserved in the audit trail;
4. the acceptance rule for the duplicate check and the authorization to re-run the affected P0 gate.

This artifact does not select the treatment. The original released split and evidence must remain recoverable
even if OWNER later approves a derived evaluation protocol. No rows may be silently removed or reshuffled, and
labels must remain unchanged.

P0 may transition to `PASS` or `PASS_WITH_WARNINGS` only after the approved protocol is recorded, the affected
schema/split check is re-run, its blocker is cleared under that protocol, and the completion rule is
satisfied.
Until then, the blocker remains active.

## Evidence used

- `docs/R1_P0_ACQUISITION_PREFLIGHT.json`: committed machine-readable status, check ledger, blocker, warnings,
  and completion/next-gate rules.
- `docs/R1_P0_ACQUISITION_PREFLIGHT.md`: committed gate narrative and training lock.
- `docs/R1_P0_RUNPOD_20260919_RECEIPT.md`: committed revalidation receipt confirming the unchanged duplicate
  finding, preserved split, no training/benchmark execution, and reused smoke result.
- `HANDOFF.md`: committed split counts and operational owner action.
- `local-state/campaigns/ocuforge-r1-p0-20260919/r1-p0/remote_compact_export.json`: available ignored compact
  export corroborating runtime scope and that training/benchmark execution did not occur; it contains no image
  bytes, credentials, checkpoints, or model outputs.
