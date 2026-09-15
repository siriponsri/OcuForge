# OcuForge Codex Pack

This directory is the repo-local Codex workflow pack for OcuForge.

Codex supports repo-local skills under `.codex/skills/`. OcuForge keeps its project-specific research skill in Git and installs third-party skills from pinned upstream commits so every machine can recreate the same setup without vendoring third-party prompt bodies into this repository.

## Quick start

Windows PowerShell:

```powershell
.\.codex\bootstrap-skills.ps1
```

macOS/Linux:

```bash
bash .codex/bootstrap-skills.sh
```

Bootstrap requires network access to GitHub and a working `git` executable. It does not upload OcuForge data.

After bootstrap, these primary skills are available:

- `karpathy-guidelines`
- `debugging-code`
- `wayfinder`
- `ocuforge-ai-research`

The bootstrap also installs the upstream support skills `grilling`, `domain-modeling`, `research`, and `prototype` because the selected Wayfinder version refers to them.

## Reproducibility

Third-party source repositories and pinned commits are recorded in `skills.lock.json`. Do not silently move pins during unrelated work. Update pins in a dedicated change, inspect upstream changes, bootstrap again, and verify the resulting skills before committing the lock update.

Generated third-party skill directories are intentionally ignored by Git. The local `ocuforge-ai-research` skill is tracked because it is OcuForge-specific.

## Safety

Repository and clinical rules in the root `AGENTS.md` outrank skill instructions.

In particular, an external skill may not:

- upload hospital/private data;
- auto-install developer tooling without owner approval;
- create or modify remote issues, branches, or services unless requested;
- weaken tests or clinical/provenance rules;
- reinterpret local labels or make unsupported clinical claims.

## Machine-specific Codex config

Keep the actual Codex `config.toml` outside this repository. Use `.codex.example/config.toml` as the tracked template.
