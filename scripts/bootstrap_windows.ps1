[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$VenvPath = Join-Path $RepositoryRoot ".venv"
$script:VenvPython = Join-Path $VenvPath "Scripts\python.exe"
$DockerReady = $false

function Get-PythonVersion {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Executable,
        [string[]]$PrefixArguments = @()
    )

    $PythonArguments = @($PrefixArguments) + @("--version")
    try {
        $Output = & $Executable @PythonArguments 2>&1
        $ExitCode = $LASTEXITCODE
    }
    catch {
        return $null
    }

    if ($ExitCode -ne 0) {
        return $null
    }

    $VersionLine = ([string]($Output | Select-Object -Last 1)).Trim()
    if ($VersionLine -match "Python\s+(?<Version>\d+\.\d+)") {
        return $Matches["Version"]
    }
    return $null
}

function Find-SupportedPython {
    $Candidates = @(
        @{ Label = "py -3.12"; Command = "py"; PrefixArguments = @("-3.12") },
        @{ Label = "py -3.11"; Command = "py"; PrefixArguments = @("-3.11") },
        @{ Label = "python"; Command = "python"; PrefixArguments = @() }
    )

    foreach ($Candidate in $Candidates) {
        $Command = Get-Command $Candidate.Command -CommandType Application -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($null -eq $Command) {
            continue
        }

        $Version = Get-PythonVersion -Executable $Command.Source -PrefixArguments $Candidate.PrefixArguments
        if ($Version -in @("3.11", "3.12")) {
            return @{
                Label = $Candidate.Label
                Executable = $Command.Source
                PrefixArguments = $Candidate.PrefixArguments
                Version = $Version
            }
        }

        if ($Version) {
            Write-Host "Skipping $($Candidate.Label): Python $Version is not supported."
        }
    }

    return $null
}

function Assert-Repository {
    $RequiredPaths = @(
        ".git",
        "README.md",
        "requirements-dev.txt",
        ".codex\bootstrap-skills.ps1",
        "eyes-detected-contracts\pyproject.toml",
        "eyes-detected-models\pyproject.toml",
        "eyes-detected-labeler\pyproject.toml"
    )
    foreach ($RelativePath in $RequiredPaths) {
        if (-not (Test-Path -LiteralPath (Join-Path $RepositoryRoot $RelativePath))) {
            throw "This does not look like an OcuForge repository: missing $RelativePath"
        }
    }

    $GitRootOutput = & git -C $RepositoryRoot rev-parse --show-toplevel 2>$null
    $GitRootExitCode = $LASTEXITCODE
    $GitRoot = ([string]($GitRootOutput | Select-Object -Last 1)).Trim()
    if ($GitRootExitCode -ne 0 -or -not $GitRoot) {
        throw "The OcuForge directory is not a Git work tree."
    }
    if (-not ([System.IO.Path]::GetFullPath($GitRoot) -ieq $RepositoryRoot)) {
        throw "Run bootstrap from the OcuForge repository root."
    }

    $CommitOutput = & git -C $RepositoryRoot rev-parse --verify HEAD 2>$null
    $CommitExitCode = $LASTEXITCODE
    $Commit = ([string]($CommitOutput | Select-Object -Last 1)).Trim()
    if ($CommitExitCode -ne 0 -or -not $Commit) {
        throw "Unable to determine the current Git commit."
    }
    Write-Host "Repository: $RepositoryRoot"
    Write-Host "Git commit: $Commit"

    $Status = @(& git -C $RepositoryRoot status --porcelain 2>$null)
    $StatusExitCode = $LASTEXITCODE
    if ($StatusExitCode -ne 0) {
        throw "Unable to inspect the Git working tree."
    }
    if ($Status.Count -gt 0) {
        $Warning = "WARNING: Git working tree is dirty; existing changes will be preserved."
        Write-Host $Warning -ForegroundColor Yellow
    }
}

function Invoke-VenvPython {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    & $script:VenvPython @Arguments
    $ExitCode = $LASTEXITCODE
    if ($ExitCode -ne 0) {
        throw "Python command failed with exit code ${ExitCode}: $($Arguments -join ' ')"
    }
}

function Invoke-CodexSkillsBootstrap {
    $SkillsScript = Join-Path $RepositoryRoot ".codex\bootstrap-skills.ps1"
    $PowerShell = Get-Command powershell.exe -CommandType Application -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -eq $PowerShell) {
        throw "powershell.exe is required to bootstrap the pinned Codex skills."
    }

    Write-Host "Bootstrapping pinned Codex skills..."
    & $PowerShell.Source -NoProfile -ExecutionPolicy Bypass -File $SkillsScript
    $ExitCode = $LASTEXITCODE
    if ($ExitCode -ne 0) {
        throw "Codex skill bootstrap failed with exit code $ExitCode."
    }

    foreach ($Skill in @("karpathy-guidelines", "debugging-code", "wayfinder", "ocuforge-ai-research")) {
        $SkillFile = Join-Path $RepositoryRoot ".codex\skills\$Skill\SKILL.md"
        if (-not (Test-Path -LiteralPath $SkillFile -PathType Leaf)) {
            throw "Codex skill verification failed: $SkillFile"
        }
    }
    Write-Host "Required Codex skills verified."
}

function Test-DockerCapability {
    $Docker = Get-Command docker.exe -CommandType Application -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -eq $Docker) {
        Write-Host "docker version: NOT AVAILABLE"
        Write-Host "docker compose version: NOT AVAILABLE"
        Write-Host "DOCKER_READY=false"
        $Message = "OPTIONAL/NOT READY FOR DOCKER PHASES: docker.exe was not found."
        Write-Host $Message -ForegroundColor Yellow
        return $false
    }

    Write-Host "Checking Docker capability (no services will be started)..."
    Write-Host "docker version"
    $VersionOutput = @(& $Docker.Source version 2>&1)
    $VersionExitCode = $LASTEXITCODE
    $VersionOutput | ForEach-Object { Write-Host "  $_" }

    Write-Host "docker compose version"
    $ComposeOutput = @(& $Docker.Source compose version 2>&1)
    $ComposeExitCode = $LASTEXITCODE
    $ComposeOutput | ForEach-Object { Write-Host "  $_" }

    if ($VersionExitCode -eq 0 -and $ComposeExitCode -eq 0) {
        Write-Host "DOCKER_READY=true"
        return $true
    }

    Write-Host "DOCKER_READY=false"
    if ($VersionExitCode -ne 0) {
        $Message = "OPTIONAL/NOT READY FOR DOCKER PHASES: Docker Engine is unavailable or stopped."
        Write-Host $Message -ForegroundColor Yellow
    }
    else {
        $Message = "OPTIONAL/NOT READY FOR DOCKER PHASES: Docker Compose v2 is unavailable."
        Write-Host $Message -ForegroundColor Yellow
    }
    Write-Host "Docker is required before on-prem/CVAT/GPU container phases." -ForegroundColor Yellow
    return $false
}

try {
    Set-Location $RepositoryRoot
    Assert-Repository

    if (Test-Path -LiteralPath $VenvPath) {
        if (-not (Test-Path -LiteralPath $script:VenvPython -PathType Leaf)) {
            throw (".venv exists but its Python executable is missing or invalid; " +
                "it will not be replaced automatically.")
        }
        Write-Host "Reusing existing .venv."
    }
    else {
        $SelectedPython = Find-SupportedPython
        if ($null -eq $SelectedPython) {
            throw "Supported Python was not found. Install Python 3.11 or 3.12, then rerun bootstrap.cmd."
        }
        Write-Host "Using $($SelectedPython.Label) (Python $($SelectedPython.Version))."
        Write-Host "Creating .venv..."
        $VenvArguments = @($SelectedPython.PrefixArguments) + @("-m", "venv", $VenvPath)
        & $SelectedPython.Executable @VenvArguments
        $ExitCode = $LASTEXITCODE
        if ($ExitCode -ne 0) {
            throw "Virtual environment creation failed with exit code $ExitCode."
        }
    }

    $VenvVersion = Get-PythonVersion -Executable $script:VenvPython
    if ($VenvVersion -notin @("3.11", "3.12")) {
        if ($VenvVersion) {
            throw ".venv uses unsupported Python $VenvVersion; it will not be replaced automatically."
        }
        throw ".venv Python could not be executed; it will not be replaced automatically."
    }
    Write-Host "Using .venv Python $VenvVersion."

    Write-Host "Installing CPU PyTorch baseline..."
    Invoke-VenvPython -Arguments @(
        "-m", "pip", "install", "torch==2.5.1",
        "--index-url", "https://download.pytorch.org/whl/cpu"
    )
    Write-Host "Installing editable OcuForge packages and development requirements..."
    Invoke-VenvPython -Arguments @(
        "-m", "pip", "install", "-e", "./eyes-detected-contracts",
        "-e", "./eyes-detected-models", "-e", "./eyes-detected-labeler",
        "-r", "requirements-dev.txt"
    )

    Invoke-CodexSkillsBootstrap

    Write-Host "Running pytest..."
    Invoke-VenvPython -Arguments @("-m", "pytest")

    Write-Host "Running synthetic roundtrip..."
    Invoke-VenvPython -Arguments @("scripts/synthetic_roundtrip.py")
    $MetricsPath = Join-Path $RepositoryRoot "artifacts\smoke\smoke_metrics.json"
    if (-not (Test-Path -LiteralPath $MetricsPath -PathType Leaf)) {
        throw "Synthetic roundtrip completed without its expected metrics file: $MetricsPath"
    }
    try {
        $Metrics = Get-Content -Raw -Encoding UTF8 $MetricsPath | ConvertFrom-Json
        $WeightsUpdated = $Metrics.weights_updated
        $ScientificResultEligible = $Metrics.scientific_result_eligible
    }
    catch {
        throw "Synthetic roundtrip metrics could not be read: $MetricsPath"
    }
    if ($WeightsUpdated -ne $true -or $ScientificResultEligible -ne $false) {
        throw ("Synthetic roundtrip invariants failed: weights_updated must be true and " +
            "scientific_result_eligible must be false.")
    }
    Write-Host "Synthetic invariants verified: weights_updated=true; scientific_result_eligible=false."

    $DockerReady = Test-DockerCapability

    Write-Host ""
    Write-Host "CORE_DEV_READY=true" -ForegroundColor Green
    if ($DockerReady) {
        Write-Host "DOCKER_READY=true"
    }
    else {
        Write-Host "DOCKER_READY=false"
        Write-Host "Docker is required before on-prem/CVAT/GPU container phases." -ForegroundColor Yellow
    }
    exit 0
}
catch {
    Write-Host "BOOTSTRAP_FAILED: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "CORE_DEV_READY=false"
    Write-Host "DOCKER_READY=false (not ready or not checked)"
    exit 1
}
