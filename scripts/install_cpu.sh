#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -e ./eyes-detected-contracts -e ./eyes-detected-models -e ./eyes-detected-labeler -r requirements-dev.txt
