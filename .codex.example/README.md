# `.codex.example/`

Tracked, non-secret bootstrap material for using OcuForge with Codex across multiple machines.

This directory is **not** intended to be treated as an automatically loaded Codex configuration directory.
Use it as a repository-owned template and source of operating guidance.

## Per-machine setup

Copy the desired settings from `config.toml` into the real Codex config on each machine:

- Windows: `%USERPROFILE%\.codex\config.toml`
- macOS/Linux: `~/.codex/config.toml`

Do not commit the real machine configuration if it contains credentials, private paths, MCP secrets, or machine-specific access details.

## Recommended skills

OcuForge uses skills as optional operating procedures. Repository rules in the root `AGENTS.md` always take precedence.

### Karpathy Guidelines

Source:
`https://github.com/multica-ai/andrej-karpathy-skills/tree/main/skills/karpathy-guidelines`

Use for non-trivial coding/review/refactor/configuration work. Its useful role here is behavioral:
think before coding, keep the solution simple, make surgical changes, and define a verifiable goal.

### Wayfinder

Source:
`https://github.com/mattpocock/skills/tree/main/skills/engineering/wayfinder`

Use only for a genuinely multi-session effort with unresolved decisions. OcuForge's normal phase-by-phase implementation workflow should not invoke Wayfinder automatically.

### Debug Skill

Source:
`https://github.com/AlmogBaku/debug-skill`

Use for difficult runtime debugging when tests/static inspection do not provide enough evidence. The upstream project provides a `debugging-code` skill plus a DAP CLI. Treat it as developer tooling, not an OcuForge runtime dependency.

## Installation policy

Install external skills using the method supported by the Codex/agent version on each machine. Do not vendor or auto-update third-party skill repositories inside OcuForge unless the owner explicitly decides to pin and audit them.

Before enabling a skill, inspect its `SKILL.md` and any referenced scripts. Third-party skill instructions never override OcuForge data-governance, clinical-safety, architecture, or scope rules.

## Multi-machine rule

Keep these items in Git:

- root `AGENTS.md`;
- `.codex.example/`;
- public, non-secret skill source references;
- reproducible project commands.

Keep these items per machine:

- actual Codex `config.toml`;
- tokens and credentials;
- private MCP configuration;
- hospital/private data paths;
- locally installed skill caches/tool binaries.
