[CmdletBinding()]
param(
    [string]$SkillRoot = (Join-Path $PSScriptRoot "..\.tools\diagram-design")
)

$ErrorActionPreference = "Stop"
$lockPath = Join-Path $PSScriptRoot "..\tools\diagram-design.lock.json"
$lock = Get-Content -Raw -Encoding UTF8 $lockPath | ConvertFrom-Json
$resolvedSkill = (Resolve-Path $SkillRoot -ErrorAction SilentlyContinue).Path

if (-not $resolvedSkill) {
    throw "Diagram Design checkout is missing at '$SkillRoot'. Clone the pinned repository before using the authoring skill."
}

$head = (git -C $resolvedSkill rev-parse HEAD).Trim()
if ($head -ne $lock.commit) {
    throw "Diagram Design checkout is at '$head'; expected pinned commit '$($lock.commit)'."
}

$skillFile = Join-Path $resolvedSkill $lock.skill_path
if (-not (Test-Path $skillFile)) {
    throw "Pinned Diagram Design skill file is missing: $skillFile"
}

Write-Output "Diagram Design $($lock.version) verified at $head"
