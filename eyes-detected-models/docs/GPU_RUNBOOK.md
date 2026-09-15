# GPU_RUNBOOK

See the maintained [workspace document](../../docs/GPU_EXECUTION_TH.md).

This package implements research interfaces and synthetic execution only. See the delivery report for measured validation.

R1 B1 is ready but not executed. Use `eyes-detected-models/configs/research/r1-global-b1.json` and configure
`OCUFORGE_DATA_ROOT`, `OCUFORGE_MODEL_ROOT`, `OCUFORGE_CACHE_ROOT`, and `OCUFORGE_ARTIFACT_ROOT`. RunPod
Network Volume is the preferred persistent public-data option, not a required provider. Only reviewed public or
synthetic inputs and public research artifacts may be mounted in the public GPU environment.
