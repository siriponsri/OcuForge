# GPU_RUNBOOK

See the maintained [workspace document](../../docs/GPU_EXECUTION_TH.md).

This package implements research interfaces and synthetic execution only. See the delivery report for measured validation.

R1 G0-G5 is ready but not executed. Use `eyes-detected-models/configs/research/r1-global-benchmark.json` and configure
`OCUFORGE_DATA_ROOT`, `OCUFORGE_MODEL_ROOT`, `OCUFORGE_CACHE_ROOT`, and `OCUFORGE_ARTIFACT_ROOT`. RunPod
Network Volume is an optional persistent public-data workspace/cache, not a required provider. Only reviewed public or
synthetic inputs and public research artifacts may be mounted in the public GPU environment. RunPod/Vast are temporary
training, feature-extraction, and experiment compute, not authoritative deployment or production storage. Local/on-premise
hosts archive champion weights and own authoritative inference; Vercel is limited to public/synthetic demo frontend
components and measured optional CPU inference.
