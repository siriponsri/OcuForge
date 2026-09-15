param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$SkillsRoot = Join-Path $PSScriptRoot "skills"
$LicenseRoot = Join-Path $PSScriptRoot "THIRD_PARTY_LICENSES"

New-Item -ItemType Directory -Force -Path $SkillsRoot | Out-Null
New-Item -ItemType Directory -Force -Path $LicenseRoot | Out-Null

function Assert-Git {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        throw "git is required to bootstrap OcuForge Codex skills."
    }
}

function Invoke-Git {
    param([string[]]$GitArgs)
    & git @GitArgs
    if ($LASTEXITCODE -ne 0) {
        throw "git failed: git $($GitArgs -join ' ')"
    }
}

function Copy-Skill {
    param(
        [string]$Source,
        [string]$DestinationName
    )

    $Destination = Join-Path $SkillsRoot $DestinationName
    if (Test-Path $Destination) {
        Remove-Item -Recurse -Force $Destination
    }

    Copy-Item -Recurse -Force $Source $Destination
    if (-not (Test-Path (Join-Path $Destination "SKILL.md"))) {
        throw "Installed skill '$DestinationName' is missing SKILL.md."
    }
}

function Install-RepoSkills {
    param(
        [string]$Name,
        [string]$Repo,
        [string]$Ref,
        [hashtable]$Mappings
    )

    $Temp = Join-Path ([System.IO.Path]::GetTempPath()) ("ocuforge-codex-" + [guid]::NewGuid().ToString("N"))

    try {
        Invoke-Git -GitArgs @("clone", "--quiet", "--filter=blob:none", "--sparse", "--no-checkout", $Repo, $Temp)

        $Paths = @($Mappings.Keys)
        $SparseArgs = @("-C", $Temp, "sparse-checkout", "set") + $Paths
        Invoke-Git -GitArgs $SparseArgs

        Invoke-Git -GitArgs @("-C", $Temp, "checkout", "--quiet", $Ref)

        foreach ($Path in $Paths) {
            $DestName = $Mappings[$Path]
            Copy-Skill -Source (Join-Path $Temp $Path) -DestinationName $DestName
        }

        $License = Join-Path $Temp "LICENSE"
        if (Test-Path $License) {
            Copy-Item -Force $License (Join-Path $LicenseRoot ($Name + ".txt"))
        }
    }
    finally {
        if (Test-Path $Temp) {
            Remove-Item -Recurse -Force $Temp
        }
    }
}

Assert-Git

Install-RepoSkills `
    -Name "andrej-karpathy-skills" `
    -Repo "https://github.com/multica-ai/andrej-karpathy-skills.git" `
    -Ref "2c606141936f1eeef17fa3043a72095b4765b9c2" `
    -Mappings @{"skills/karpathy-guidelines" = "karpathy-guidelines"}

Install-RepoSkills `
    -Name "debug-skill" `
    -Repo "https://github.com/AlmogBaku/debug-skill.git" `
    -Ref "26ef325fe2188209d053f42a6ca0000942a94932" `
    -Mappings @{"skills/debugging-code" = "debugging-code"}

Install-RepoSkills `
    -Name "mattpocock-skills" `
    -Repo "https://github.com/mattpocock/skills.git" `
    -Ref "3cca18b368ae95cdbdebbff572ccafa662551015" `
    -Mappings @{
        "skills/engineering/wayfinder" = "wayfinder"
        "skills/productivity/grilling" = "grilling"
        "skills/engineering/domain-modeling" = "domain-modeling"
        "skills/engineering/research" = "research"
        "skills/engineering/prototype" = "prototype"
    }

$Expected = @(
    "karpathy-guidelines",
    "debugging-code",
    "wayfinder",
    "grilling",
    "domain-modeling",
    "research",
    "prototype",
    "ocuforge-ai-research"
)

foreach ($Skill in $Expected) {
    $SkillFile = Join-Path (Join-Path $SkillsRoot $Skill) "SKILL.md"
    if (-not (Test-Path $SkillFile)) {
        throw "Skill verification failed: $SkillFile"
    }
}

Write-Host "OcuForge Codex skills ready:" -ForegroundColor Green
$Expected | ForEach-Object { Write-Host " - $_" }
Write-Host "Pins: .codex/skills.lock.json"
