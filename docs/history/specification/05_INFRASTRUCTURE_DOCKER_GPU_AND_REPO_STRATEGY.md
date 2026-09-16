# INFRASTRUCTURE — REPOSITORIES, DOCKER, LOCAL LABELING, GPU EXECUTION

## 0. Principle

Use the right tool for each job:

```text
Git repository = source of truth
Docker         = reproducible runtime
Local server   = clinical data + annotation
GPU provider   = burst public/synthetic research compute
Local/on-prem  = authoritative inference and clinical integration
Artifact store = checkpoints / features / reports
```

Do not use Docker “instead of” Git.

---

# 1. Repository strategy

Initial starter ZIP contains three workspaces:

```text
eyes-detected-models
eyes-detected-labeler
eyes-detected-contracts
```

Recommended later:
- push each to its own GitHub repository;
- or keep in a monorepo temporarily only if team size/operations justify.

Shared contracts must not be duplicated manually.

---

# 2. Docker strategy

## Track A image

Targets:
```text
dev
gpu-research
cpu-test
```

Requirements:
- Python >=3.11 because current official DINOv3 package metadata requires it;
- pinned Python dependencies;
- PyTorch/CUDA versions chosen from a tested compatibility matrix during implementation;
- no weights baked into image;
- no datasets baked into image.

## Track B

Docker Compose:
- labeler bridge service;
- optional FiftyOne;
- CVAT deployment/integration instructions.

Because CVAT has its own official deployment topology, starter should avoid unnecessarily repackaging the whole CVAT stack inside a custom image.

---

# 3. Local annotation topology

Preferred:

```text
Hospital LAN
  ├── Local NAS
  │    └── retinal images
  ├── CVAT
  ├── Eye Detected labeler bridge
  ├── optional FiftyOne
  └── optional local GPU pre-label service
```

No external internet dependency should be required for ordinary clinician annotation after setup, except where organization chooses otherwise.

---

# 4. Local GPU server — later procurement profile

Not required for starter, but architecture should accommodate:

```text
CPU: Ryzen 9 / Core i9 / workstation class
RAM: 64–128 GB
GPU: 24–32 GB VRAM class preferred for local pre-label workloads
Storage: fast NVMe + secure NAS
Network: 2.5/10 GbE depending image volume
UPS: appropriate to server load
OS: Ubuntu LTS
```

Do not encode one vendor SKU as a hard software dependency.

---

# 5. Burst GPU

Provider-agnostic scripts should support any Linux/NVIDIA environment with Docker.

Candidate providers:
- Vast.ai;
- RunPod;
- institutional GPU;
- on-prem workstation.

Public/synthetic model training, temporary feature extraction, and temporary experiment compute may use the cheapest
suitable provider. A persistent cloud volume is optional training workspace/cache only; it is not authoritative
deployment infrastructure or production storage. The local/on-premise environment remains authoritative for inference,
model archives, clinical integrations, and all hospital/private data and derived artifacts.

Local hospital images:
- local-only by default;
- de-identified export only after governance approval;
- secure/compliant provider selection is a separate decision.

---

# 6. GPU execution pattern

```text
VS Code
  ↓ git push
GitHub
  ↓ CI
Container build
  ↓
registry
  ↓
GPU machine
  ↓
docker pull
  ↓
run config
  ↓
artifact store
```

Every run records:
- Git SHA;
- image digest/tag;
- config hash;
- dataset version;
- seed;
- GPU model;
- runtime versions.

Deployment evaluation also records CPU inference latency, peak RAM, serialized model size, preprocessing latency, and
GPU training cost. Scientific accuracy alone does not select the deployment champion.

---

# 7. Dataset mount pattern

Never:

```dockerfile
COPY local_uwf /data
```

Use mounts:

```text
/data/public
/data/local
/artifacts
/cache
```

Paths must be environment/config driven.

---

# 8. Artifact strategy

Git:
- code;
- configs;
- metrics summaries;
- small reports.

Artifact store:
- feature banks;
- model checkpoints;
- large logs;
- exports.

Public cloud volumes may hold temporary public/synthetic research artifacts during an approved run. Champion weights and
model archives are downloaded from training infrastructure and retained locally/on-premise for authoritative inference.
GitHub stores code, configs, safe manifests, model metadata, hashes, and appropriate metrics/reports, but not large
weights, DINOv3 base weights, feature caches, or scientific checkpoints. Any future public/private artifact hosting
requires upstream license compliance and explicit approval.

Potential stores:
- local NAS;
- S3-compatible MinIO;
- approved object storage;
- Hugging Face repositories for eligible public artifacts.

Any external artifact host is optional and requires explicit approval plus upstream license review; it is never the
authoritative store for hospital/private artifacts.

Raw local medical data should not be placed on public model/dataset hubs.

---

# 9. CI

CPU-only CI:

```text
ruff/lint
unit tests
contract validation
synthetic smoke train
Docker build or config validation
secret scan
large-file scan
```

CI must not:
- download MMRDR;
- download DINOv3 weights;
- require GPU;
- access hospital data.

---

# 10. Secrets

Use:
```text
.env.example
```
with dummy keys.

Real values:
- GitHub secret;
- local secret manager;
- environment variable.

Never commit:
- CVAT token;
- cloud API key;
- hospital credentials.

---

# 11. DevContainer

Recommended:
- VS Code Dev Containers config;
- CPU development by default;
- optional GPU profile documented.

This reduces local/Vast/RunPod environment drift.

---

# 12. Reproducibility

For a publishable result, reconstruct:

```text
code
+ environment
+ config
+ data manifest
+ split manifest
+ random seed
+ model weight identity
```

Docker alone is not enough if data/split versions are missing.

---

# 13. Cloud/offline failure policy

If network/model download fails:
- do not silently use a different model;
- fail with clear instructions;
- offline tests remain green using explicit synthetic/test components.

---

# 14. DINOv3 external dependency policy

The starter should provide:
- adapter code;
- install instructions;
- license/access note;
- model name config;
- model version field;
- weight path env var.

Do not redistribute DINOv3 weights in the starter ZIP.

---

# 15. Labeler availability

If CVAT is not running:
- bridge unit tests still work with fixtures;
- CLI should return clear connection error;
- no fake “annotation succeeded”.

---

# 16. Recommended commands in generated starter

Track A:

```bash
make test
make smoke
make docker-build
python -m eyes_detected.cli validate-dataset ...
python -m eyes_detected.cli smoke-train ...
```

Track B:

```bash
make test
docker compose config
python -m labeler_bridge.cli validate-schema
python -m labeler_bridge.cli import-demo-predictions
```

Contracts:

```bash
python -m eyes_contracts.cli validate examples/...
```

Exact commands may differ but beginner documentation must be copy/paste ready.
