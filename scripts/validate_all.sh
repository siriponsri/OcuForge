#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m ruff check .
python -m pytest
python scripts/validate_configs.py
python scripts/synthetic_roundtrip.py
python scripts/package_check.py
