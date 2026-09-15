[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$ComposeFile = Join-Path $RepositoryRoot "deploy\onprem\compose.yaml"
$StateRoot = Join-Path $RepositoryRoot "local-state\phase2"
$SecretRoot = Join-Path $RepositoryRoot "local-state\phase2\secrets"
$ProjectName = "ocuforge-phase2"
$SyntheticNetwork = "ocuforge-phase2-internal"
$script:DockerPath = $null
$script:ComposeArguments = @(
    "compose",
    "--project-name", $ProjectName,
    "--file", $ComposeFile
)
$CreatedSyntheticNetwork = $false
$FailureMessage = $null

function Assert-Repository {
    $RequiredPaths = @(
        ".git",
        "README.md",
        "deploy\onprem\compose.yaml",
        "deploy\onprem\mongo-init.js",
        "deploy\onprem\entrypoint.py",
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
        throw "Run 02_phase2_local_data.cmd from the OcuForge repository."
    }

    $Commit = ([string](& git -C $RepositoryRoot rev-parse --verify HEAD 2>$null)).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $Commit) {
        throw "Unable to determine the current Git commit."
    }
    Write-Host "Repository: $RepositoryRoot"
    Write-Host "Git commit: $Commit"
}

function Invoke-Docker {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    & $script:DockerPath @Arguments
    $ExitCode = $LASTEXITCODE
    if ($ExitCode -ne 0) {
        throw "Docker command failed with exit code ${ExitCode}: docker $($Arguments -join ' ')"
    }
}

function Read-SecretValue {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$Label
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required local $Label secret is missing: $Path"
    }
    $Value = (Get-Content -LiteralPath $Path -Raw -ErrorAction Stop).Trim()
    if ($Value.Length -lt 24) {
        throw "Local $Label secret must contain at least 24 characters: $Path"
    }
    return $Value
}

function New-SyntheticSecret {
    $Bytes = New-Object byte[] 32
    $Generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $Generator.GetBytes($Bytes)
    }
    finally {
        $Generator.Dispose()
    }
    return [Convert]::ToBase64String($Bytes)
}

function Write-SecretValue {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$Value
    )

    [System.IO.File]::WriteAllText($Path, $Value, [System.Text.Encoding]::ASCII)
}

function Ensure-SyntheticSecrets {
    New-Item -ItemType Directory -Force -Path $SecretRoot | Out-Null

    $RootPath = Join-Path $SecretRoot "mongo_root_password"
    $AppPath = Join-Path $SecretRoot "mongo_app_password"
    $InitPath = Join-Path $SecretRoot "mongo_app_password_init"

    if (-not (Test-Path -LiteralPath $RootPath)) {
        Write-SecretValue -Path $RootPath -Value (New-SyntheticSecret)
    }
    if (-not (Test-Path -LiteralPath $AppPath)) {
        Write-SecretValue -Path $AppPath -Value (New-SyntheticSecret)
    }

    $RootPassword = Read-SecretValue -Path $RootPath -Label "Mongo root"
    $AppPassword = Read-SecretValue -Path $AppPath -Label "Mongo application"
    if ($RootPassword -eq $AppPassword) {
        throw "Mongo root and application secrets must be distinct."
    }

    if (-not (Test-Path -LiteralPath $InitPath)) {
        Write-SecretValue -Path $InitPath -Value $AppPassword
    }
    $InitPassword = Read-SecretValue -Path $InitPath -Label "Mongo initialization"
    if ($InitPassword -ne $AppPassword) {
        throw "Mongo initialization and application secrets must contain the same bytes."
    }
    $env:MONGO_ROOT_PASSWORD_FILE = ConvertTo-ComposePath $RootPath
    $env:MONGO_APP_PASSWORD_INIT_FILE = ConvertTo-ComposePath $InitPath
    $env:MONGO_APP_PASSWORD_FILE = ConvertTo-ComposePath $AppPath
    Write-Host "Synthetic-only Mongo secrets are ready under local-state\phase2\secrets (gitignored)."
}

function ConvertTo-ComposePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    return ([System.IO.Path]::GetFullPath($Path)).Replace("\", "/")
}

function Set-SyntheticComposeEnvironment {
    $DataRoot = Join-Path $StateRoot "data"
    $ObjectRoot = Join-Path $StateRoot "objects"
    $ExportRoot = Join-Path $StateRoot "exports"
    foreach ($Path in @($StateRoot, $DataRoot, $ObjectRoot, $ExportRoot)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
    }

    $env:LOCAL_DATA_ROOT = ConvertTo-ComposePath $DataRoot
    $env:LOCAL_OBJECT_ROOT = ConvertTo-ComposePath $ObjectRoot
    $env:LOCAL_EXPORT_ROOT = ConvertTo-ComposePath $ExportRoot
    $env:CVAT_NETWORK = $SyntheticNetwork
    $env:CVAT_TOKEN = ""
}

function Ensure-SyntheticNetwork {
    $InspectOutput = & $script:DockerPath network inspect $SyntheticNetwork --format "{{.Internal}}" 2>$null
    $InspectExitCode = $LASTEXITCODE
    $Internal = ([string]($InspectOutput | Select-Object -Last 1)).Trim()
    if ($InspectExitCode -eq 0) {
        if ($Internal -ne "true") {
            throw "Existing Docker network $SyntheticNetwork is not internal."
        }
        return
    }

    Invoke-Docker -Arguments @("network", "create", "--internal", $SyntheticNetwork)
    $script:CreatedSyntheticNetwork = $true
}

function Wait-ForMongoHealth {
    $HealthArguments = $script:ComposeArguments + @("ps", "--format", "{{.Health}}", "mongo")
    for ($Attempt = 1; $Attempt -le 30; $Attempt++) {
        $HealthOutput = & $script:DockerPath @HealthArguments 2>$null
        $HealthExitCode = $LASTEXITCODE
        $Health = ([string]($HealthOutput | Select-Object -Last 1)).Trim()
        if ($HealthExitCode -eq 0 -and $Health -eq "healthy") {
            Write-Host "MongoDB health: healthy"
            return
        }
        Start-Sleep -Seconds 2
    }
    throw "MongoDB did not become healthy within 60 seconds."
}

function Invoke-OperatorHealth {
    param(
        [Parameter(Mandatory = $true)]
        [bool]$Build
    )

    $RunArguments = $script:ComposeArguments + @(
        "--profile", "operator", "run", "--rm", "--no-deps"
    )
    if ($Build) {
        $RunArguments += "--build"
    }
    $RunArguments += @("operator", "eyes-local", "health")
    Invoke-Docker -Arguments $RunArguments
}

function Invoke-SyntheticMongoCheck {
    $SmokeCode = @'
from eyes_contracts.models import Annotation, Geometry
from labeler_bridge.provenance.lifecycle import event
from labeler_bridge.storage import MongoStore, document_hash

timestamp = "2026-01-01T00:00:00+00:00"
geometry = Geometry(type="point", coordinates_norm=[0.25, 0.75])
annotation = Annotation(
    annotation_id="PHASE2_SYNTH_ANNOTATION",
    image_id="PHASE2_SYNTH_IMAGE",
    label="microaneurysm",
    geometry=geometry,
    origin="CLINICIAN_ADDED",
    annotator_id_hash="PHASE2_SYNTH_ACTOR",
    review_status="DRAFT",
    created_at=timestamp,
    updated_at=timestamp,
    history=[
        event("CLINICIAN_ADDED", "DRAFT", "PHASE2_SYNTH_ACTOR", "ADD", timestamp, geometry, "microaneurysm")
    ],
)
store = MongoStore()
document = store.docs.find_one({"_id": "phase2:synthetic"})
if document is None:
    store.create("phase2:synthetic", "phase2_smoke", {"marker": "synthetic-only", "version": 1})
document = store.get("phase2:synthetic")
assert document["body"] == {"marker": "synthetic-only", "version": 1}
store.save_annotations([annotation])
revision_hash = document_hash(annotation.model_dump(mode="json"))
revision = store.revisions.find_one({"_id": "PHASE2_SYNTH_ANNOTATION:" + revision_hash})
assert revision is not None
assert revision["image_id"] == "PHASE2_SYNTH_IMAGE"
assert revision["revision_hash"] == revision_hash
assert revision["cloud_eligible"] is False
print("PHASE2_SYNTHETIC_MONGO_OK")
'@
    $RunArguments = $script:ComposeArguments + @(
        "--profile", "operator", "run", "--rm", "--no-deps", "operator", "python", "-c", $SmokeCode
    )
    Invoke-Docker -Arguments $RunArguments
}

try {
    Set-Location $RepositoryRoot
    Assert-Repository

    $DockerCommand = Get-Command docker.exe -CommandType Application -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -eq $DockerCommand) {
        throw "docker.exe was not found. Run this handoff on the Docker-enabled home machine."
    }
    $script:DockerPath = $DockerCommand.Source
    Invoke-Docker -Arguments @("version")
    Invoke-Docker -Arguments @("compose", "version")

    Ensure-SyntheticSecrets
    Set-SyntheticComposeEnvironment
    Ensure-SyntheticNetwork

    Write-Host "Starting only the local MongoDB component..."
    Invoke-Docker -Arguments ($script:ComposeArguments + @("up", "--detach", "mongo"))
    Wait-ForMongoHealth

    Write-Host "Running the real eyes-local health check..."
    Invoke-OperatorHealth -Build $true
    Write-Host "Running the synthetic Mongo document/revision check..."
    Invoke-SyntheticMongoCheck

    Write-Host "Restarting only the MongoDB container to verify persistence..."
    Invoke-Docker -Arguments ($script:ComposeArguments + @("restart", "mongo"))
    Wait-ForMongoHealth
    Invoke-OperatorHealth -Build $false
    Invoke-SyntheticMongoCheck
}
catch {
    $FailureMessage = $_.Exception.Message
}
finally {
    if ($CreatedSyntheticNetwork -and $null -ne $script:DockerPath) {
        & $script:DockerPath network rm $SyntheticNetwork *> $null
    }
}

if ($null -ne $FailureMessage) {
    Write-Host "PHASE_2B_LIVE_MONGO=fail" -ForegroundColor Red
    Write-Host "LIVE_MONGO_ACCEPTANCE_FAILED: $FailureMessage" -ForegroundColor Red
    exit 1
}

Write-Host "PHASE_2B_LIVE_MONGO=pass" -ForegroundColor Green
Write-Host "CORE_DEV_READY is outside this gate; no CVAT service was started."
Write-Host "MongoDB and its synthetic local state remain available for the next local phase."
exit 0
