# OcuForge Repository Guidelines

## Mission

OcuForge is a research and clinician-review foundation for retinal imaging workflows. It is not a diagnostic product.

- `eyes-detected-contracts/src/eyes_contracts`: versioned schemas, protocol identity, provenance, and validators.
- `eyes-detected-models/src/eyes_detected`: research pipelines, encoders, MIL/ordinal models, evaluation, QC, and active-learning utilities.
- `eyes-detected-labeler/src/labeler_bridge`: CVAT/local storage, geometry, provenance, and annotation import/export.

Keep the contracts-first boundary: models and labeler may depend on contracts, but models and labeler must not depend on each other.

Before cross-package or cross-runtime work, read `docs/CTR_MODULE_CONTRACT.md`. Respect module ownership, dependency direction,
and data/runtime boundaries. Phases define execution order; modules define architectural ownership. Use `docs/PROJECT_MAP.md`
for human/team navigation.

## Source of Truth and Scope Discipline

Before editing, inspect the relevant code, tests, configuration, and nearby documentation. Do not infer behavior from filenames alone.

For implementation work:

1. Restate the requested outcome as a checkable goal.
2. Make the smallest change that can satisfy that goal.
3. Do not expand scope into adjacent cleanup, refactors, formatting, or features.
4. Do not weaken tests, contracts, provenance rules, or clinical/data-governance rules to make a change pass.
5. Do not replace real behavior with mocks, stubs, or silent fallbacks merely to make tests green.
6. Stop after the requested phase or gate. Do not start the next phase unless explicitly asked.

Prefer one objective, one bounded patch, and one commit. Every changed line should trace to the requested objective or to a necessary regression fix discovered while verifying it.

## Clinical and Data Invariants

These rules are non-negotiable unless the owner explicitly changes the governing specification:

- Never commit or upload hospital images, PHI, credentials, model checkpoints, local state, or private derived artifacts.
- Hospital/clinical data and derived artifacts remain local/on-prem only. Public cloud GPU, Hugging Face, Vercel, Vast, RunPod, and GitHub may receive only synthetic or explicitly authorized public data.
- Preserve image, annotation, prediction, protocol, provenance, and revision identities/hashes.
- Never reinterpret local binary `DR` / `no-DR` experience labels as ordinal DR grades 0-4.
- `no-DR` does not imply adjudicated ordinal grade 0.
- DR grading protocol versions are immutable historical references. New guidance requires a new protocol version or explicit migration.
- DME remains a separate axis. Fundus/UWF evidence alone must not be described as OCT-confirmed DME.
- MIL attention/evidence maps are model aggregation evidence, not validated lesion localization unless lesion-specific validation establishes that claim.
- Research outputs must not be presented as diagnoses or production clinical decisions.

## Repository Text and Cross-Platform I/O

Repository-controlled text files are UTF-8. Use explicit `encoding="utf-8"` for project text I/O instead of relying on the OS default.

Keep paths reasonably short and cross-platform. Avoid unnecessarily nesting long content hashes when a semantically equivalent shorter layout preserves identity.

## Build, Test, and Validation

From the repository root, after editable installation:

```bash
make test
make smoke
make lint
make config
```

Focused equivalents are acceptable:

```bash
python -m pytest path/to/test_file.py -q
python -m ruff check .
python scripts/validate_configs.py
python scripts/synthetic_roundtrip.py
```

Default tests must remain offline. Live CVAT, MongoDB, GPU, model-weight, and deployment checks are separate integration gates and must not be faked.

When fixing a defect, reproduce the smallest useful failure, fix the root cause, run the narrow regression test, then run the broader suite.

## Coding Style

Use four-space indentation, `snake_case` for modules/functions/variables, `PascalCase` for classes, and lowercase package names. Keep lines at 110 characters or fewer unless existing code requires otherwise.

Match surrounding style. Do not reformat unrelated code. Remove only imports, variables, or helpers made obsolete by the current change.

## Instruction and Skill Precedence

Priority is:

1. Explicit owner/task instruction and the current phase/gate.
2. This `AGENTS.md`.
3. OcuForge specifications, contracts, and tests.
4. Repo-local or third-party skill procedures.

A skill may improve method, but it must not broaden scope, weaken tests, move clinical/private data to cloud services, or change clinical semantics without explicit owner authorization.

Third-party skills must not silently install tooling, create or mutate remote issues/branches, upload data, or change external systems unless the owner explicitly requested that side effect.

## Repo-local Codex Skills

Codex skills live under `.codex/skills/`. On a fresh Windows machine, the default human onboarding entrypoint is root `bootstrap.cmd`; `.codex/bootstrap-skills.ps1` remains the internal/reusable skill bootstrap invoked by it. On macOS/Linux, the skill bootstrap remains available through `.codex/bootstrap-skills.sh`.

Machine bootstrap reconstructs and verifies local developer state. It does not reset repository changes or restart the current project phase/state.

- `karpathy-guidelines` — `.codex/skills/karpathy-guidelines/SKILL.md`. Use for non-trivial implementation, review, refactor, and configuration work.
- `debugging-code` — `.codex/skills/debugging-code/SKILL.md`. Use for hard runtime bugs when static inspection and tests are insufficient. Do not install debugger tooling without owner approval.
- `wayfinder` — `.codex/skills/wayfinder/SKILL.md`. Explicit invocation only, for genuinely multi-session work with unresolved decisions. Its support skills may be installed by the bootstrap script.
- `ocuforge-ai-research` — `.codex/skills/ocuforge-ai-research/SKILL.md`. Use for literature-gap analysis, research-question framing, dataset/model selection, experiment design, leakage audit, baselines, ablations, metrics, statistical validation, and evidence-backed research claims.

If a listed third-party skill is missing, do not invent its contents. Either run the bootstrap with owner approval or continue using this repository's rules without that skill.

## Human Team Handoff Naming

- Keep one canonical human entrypoint per project phase or gate; do not add aliases or parallel setup scripts.
- Name human phase/gate entrypoints as `<NN>_<phase>_<gate-purpose>.<ext>`: two-digit execution order followed by lowercase `snake_case`, for example `02_phase2_local_data.cmd`.
- Name platform-specific implementations under `scripts/` as `<NN>_<phase>_<gate-purpose>_<platform>.<ext>`; they are internal, not separate human entrypoints.
- Keep `bootstrap.cmd` as the fixed Windows machine entrypoint because it is the repository-wide onboarding contract.
- Each phase README must contain a short handoff index mapping the order, canonical command, prerequisites, expected status output, and next manual action.
- Handoff commands reconstruct or verify local environment/state only; they must not reset project phase/state or start a later phase.

## Commit and Handoff Rules

Before claiming completion, report:

- files changed;
- root cause or implementation rationale;
- commands/tests run and exact pass/fail result;
- assumptions or external dependencies not verified;
- unresolved issues, if any.

Use concise imperative commit subjects. Do not commit generated artifacts, datasets, weights, credentials, or machine-local configuration.

For multi-machine work, keep repository policy, `.codex/`, and safe templates in Git. Keep machine-specific Codex configuration and secrets outside the repository, using `.codex.example/` only as the tracked config template.
