# External Skill Sources

This file records the upstream skill sources considered for OcuForge developer workflows.

| Skill | Upstream | Intended use in OcuForge | Default? |
|---|---|---|---|
| `karpathy-guidelines` | https://github.com/multica-ai/andrej-karpathy-skills/tree/main/skills/karpathy-guidelines | Careful, simple, surgical, goal-driven engineering | Yes for non-trivial code/config work |
| `wayfinder` | https://github.com/mattpocock/skills/tree/main/skills/engineering/wayfinder | Multi-session decision mapping | No; explicit invocation only |
| `debugging-code` | https://github.com/AlmogBaku/debug-skill | Runtime debugger workflow and DAP tooling | On demand for hard runtime bugs |

## Precedence

1. Owner request and explicit phase/gate.
2. Root `AGENTS.md`.
3. OcuForge specifications/contracts/tests.
4. External skill procedures.

A skill may improve method, but it must not broaden scope, weaken tests, move clinical/private data to cloud services, or change clinical semantics without explicit owner authorization.
