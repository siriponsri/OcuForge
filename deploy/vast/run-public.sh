#!/usr/bin/env bash
set -euo pipefail
# Use inside an already approved/prepared GPU container; no provisioning or transfers.
export OCUFORGE_EXECUTION_ZONE=PUBLIC_CLOUD
export HF_HUB_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 WANDB_MODE=disabled
umask 077
exec eyes-pipeline "$@"
