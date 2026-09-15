# OcuForge Skill Sources

The active repo-local skill pack lives under `.codex/`. Bootstrap it on each fresh clone:

- Windows: `.\.codex\bootstrap-skills.ps1`
- macOS/Linux: `bash .codex/bootstrap-skills.sh`

Primary skills:

| Skill | Source | Intended use | Default? |
|---|---|---|---|
| `karpathy-guidelines` | `multica-ai/andrej-karpathy-skills` | Simple, surgical, goal-driven engineering | Yes for non-trivial code/config work |
| `debugging-code` | `AlmogBaku/debug-skill` | Runtime state/debugger workflow | On demand |
| `wayfinder` | `mattpocock/skills` | Multi-session decision mapping | Explicit invocation only |
| `ocuforge-ai-research` | Local OcuForge skill | Research questions, prior art, experiment design, leakage, baselines, ablations, metrics, evidence claims | Yes for AI-research tasks |

Pinned third-party revisions are recorded in `.codex/skills.lock.json`.

## Precedence

1. Owner request and explicit phase/gate.
2. Root `AGENTS.md`.
3. OcuForge specifications/contracts/tests.
4. Skill procedures.

Skills must not broaden scope, weaken tests, move private clinical data to cloud services, or change clinical semantics without explicit owner authorization.
