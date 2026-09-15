$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
python -m pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu
if ($LASTEXITCODE -ne 0) { throw "PyTorch install failed" }
python -m pip install -e ./eyes-detected-contracts -e ./eyes-detected-models -e ./eyes-detected-labeler -r requirements-dev.txt
if ($LASTEXITCODE -ne 0) { throw "Package install failed" }
