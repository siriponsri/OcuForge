# Diagram Design Integration

**Status:** ACTIVE SUPPORTING · V3 visual language

OcuForge uses the pinned [Diagram Design](https://github.com/cathrynlavery/diagram-design) skill to author editable
workflow diagrams. The pinned checkout is recorded in [`tools/diagram-design.lock.json`](../tools/diagram-design.lock.json)
and is intentionally ignored from Git. Generated deliverables are the tracked HTML/SVG pairs under
[`docs/diagrams/`](diagrams/).

## Authoring contract

- Use the warm editorial palette: paper `#f5f5f5`, ink `#2d3142`, muted `#4f5d75`, coral `#eb6c36`, and link blue
  `#2e5aa8`.
- Keep diagrams static, accessible, self-contained, and readable when embedded in Markdown.
- Use orthogonal connectors with visible label gaps. Do not reintroduce raw Mermaid in active documentation.
- Keep the V3 semantics explicit: R0 precedes execution, global and ROI tracks stay separate, public GPU is not
  clinical deployment, and human review remains available.
- Preserve the editable HTML as the source and the standalone SVG as the Markdown embedding artifact.

## Verification

From the repository root:

```powershell
.\scripts\setup_diagram_design.ps1
$checker = ".\.tools\diagram-design\skills\diagram-design\scripts\self_check.py"
Get-ChildItem docs\diagrams\*.html | ForEach-Object { .\.venv\Scripts\python.exe $checker $_.FullName }
```

The HTML files must pass the skill's accessible-SVG and single-file checks. SVG files are reviewed alongside their
HTML source and must retain a `title`, `desc`, and `role="img"` contract.

## Diagram index

| Diagram | Purpose |
|---|---|
| [`ocuforge-system-architecture.html`](diagrams/ocuforge-system-architecture.html) | Contracts-first system architecture |
| [`ocuforge-r0-r8-roadmap.html`](diagrams/ocuforge-r0-r8-roadmap.html) | V3 execution order and later integrations |
| [`ocuforge-global-to-roi-triage.html`](diagrams/ocuforge-global-to-roi-triage.html) | Soft, reviewable Global→ROI gate |
| [`ocuforge-deployment-boundary.html`](diagrams/ocuforge-deployment-boundary.html) | Public/synthetic versus local/on-premise boundary |
| [`ocuforge-r1-human-review-loop.html`](diagrams/ocuforge-r1-human-review-loop.html) | One-candidate-at-a-time R1 review loop |
