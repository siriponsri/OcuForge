# OcuForge Repository Guidelines

## Mission

OcuForge is a research and clinician-review foundation for retinal imaging workflows. It is not a diagnostic product.
The repository contains three Python packages:

- `eyes-detected-contracts/src/eyes_contracts`: versioned schemas, protocol identity, provenance, and validators.
- `eyes-detected-models/src/eyes_detected`: research pipelines, encoders, MIL/ordinal models, evaluation, QC, and active-learning utilities.
- `eyes-detected-labeler/src/labeler_bridge`: CVAT/local storage, geometry, provenance, and annotation import/export.

Keep the contracts-first boundary: models and labeler may depend on contracts, but models and labeler must not depend on each other.

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

If the request is ambiguous in a way that can materially change behavior, surface the ambiguity before implementing. If a simpler approach exists, prefer it.

## Clinical and Data Invariants

These rules are non-negotiable unless the owner explicitly changes the governing specification:

- Never commit or upload hospital images, PHI, credentials, model checkpoints, local state, or private derived artifacts.
- Hospital/clinical data and derived artifacts remain local/on-prem only. Public cloud GPU, Hugging Face, Vercel, Vast, RunPod, and GitHub may receive only synthetic or explicitly authorized public data.
- Preserve image, annotation, prediction, protocol, provenance, and revision identities/hashes.
- Never reinterpret local binary `DR` / `no-DR` experience labels as ordinal DR grades 0-4.
- `no-DR` does not imply adjudicated ordinal grade 0.
- DR grading protocol versions are immutable historical references. New guidance requires a new protocol version or explicit migration; do not silently rewrite historical labels.
- DME remains a separate axis. Fundus/UWF evidence alone must not be described as OCT-confirmed DME.
- MIL attention/evidence maps are model aggregation evidence, not validated lesion localization unless a lesion-specific method and evaluation establish that claim.
- Research outputs must not be presented as diagnoses or production clinical decisions.

## Repository Text and Cross-Platform I/O

Repository-controlled text files are UTF-8. When Python reads or writes project JSON, JSONL, Markdown, source, or other text files, use explicit `encoding="utf-8"` rather than relying on the OS default.

Keep paths reasonably short and cross-platform. Avoid unnecessarily nesting long content hashes in filenames/directories when a semantically equivalent shorter layout preserves identity.

## Build, Test, and Validation

From the repository root, after editable installation:

```bash
make test
make smoke
make lint
make config
```

Equivalent focused commands are acceptable, for example:

```bash
python -m pytest path/to/test_file.py -q
python -m ruff check .
python scripts/validate_configs.py
python scripts/synthetic_roundtrip.py
```

Default tests must remain offline. Live CVAT, MongoDB, GPU, model-weight, and deployment checks are separate integration gates and must not be faked in the default suite.

When fixing a defect, first reproduce the actual failure with the smallest useful loop. Fix the root cause, then run the narrow regression test before the broader suite.

## Coding Style

Use four-space indentation, `snake_case` for modules/functions/variables, `PascalCase` for classes, and lowercase package names. Keep lines at 110 characters or fewer unless existing code requires otherwise.

Match surrounding style. Do not reformat unrelated code. Remove only imports, variables, or helpers made obsolete by the current change.

## Agent Skills Policy

External skills supplement this file; they do not override OcuForge's safety, data, clinical, architecture, or scope rules.

### `karpathy-guidelines`

Use for non-trivial implementation, review, refactor, and configuration work. Apply its core discipline: surface assumptions, prefer the simplest viable solution, keep edits surgical, and define verifiable success criteria.

### `debugging-code`

Use when a bug cannot be resolved reliably from static inspection and tests alone, especially for runtime state, hangs, call flow, or difficult state-dependent failures. Prefer evidence and a reproducible failure over speculative fixes. Do not make OcuForge runtime depend on the debugger tooling.

### `wayfinder`

Use only when explicitly invoked for work that genuinely spans multiple agent sessions and has unresolved architectural/product decisions. It is a planning/decision-mapping tool, not the default implementation workflow. When the route is already decided, skip it and implement the bounded task.

If a skill conflicts with this `AGENTS.md`, the OcuForge rules in this file win.

## Commit and Handoff Rules

Before claiming completion, report:

- files changed;
- the root cause or implementation rationale;
- commands/tests run and their exact pass/fail result;
- assumptions or external dependencies not verified;
- unresolved issues, if any.

Use concise imperative commit subjects. Do not commit generated artifacts, datasets, weights, credentials, or machine-local configuration.

For multi-machine work, keep repository policy and safe templates in Git. Keep machine-specific Codex configuration and secrets outside the repository, using `.codex.example/` only as the tracked bootstrap template.
