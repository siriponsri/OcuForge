# Phase 2: Local MongoDB adapter

Read `docs/ON_PREMISE_NOSQL_PLAN_TH.md` first. This stack has no public database port and does not replace CVAT PostgreSQL. Docker build and live database authentication still require verification on the target host.

## Team handoff index

| Order | Entry point | Purpose |
|---|---|---|
| 0 | `bootstrap.cmd` | Reconstruct and verify the local Python/Codex developer environment. |
| 2A | `tests/test_local_storage.py` and offline gates | Verify local image storage and Mongo architecture without Docker. |
| 2B | `02_phase2_local_data.cmd` | Run the synthetic-only live Mongo acceptance gate on a Docker-enabled machine. |
| Manual | This README and `compose.yaml` | Continue with reviewed on-prem setup when the project phase explicitly requires it. |

Run `02_phase2_local_data.cmd` from the repository root on the Docker-enabled home machine. It creates only synthetic local state/secrets under `local-state/phase2/`, starts only MongoDB, runs `eyes-local health`, checks a synthetic document and annotation revision across a Mongo restart, and leaves CVAT off. It does not restart project phases or reset state. The manual on-prem secret location `deploy/onprem/secrets/` is separate and is not used by this synthetic gate.

1. Install a reviewed, pinned CVAT release locally using `eyes-detected-labeler/docs/CVAT_SETUP_TH.md`; identify its network and mount the same image object directory at the CVAT share path read-only.
2. Create `deploy/onprem/secrets/` locally, mode 0700. Generate distinct >=24-character random files `mongo_root_password` and `mongo_app_password` (no placeholders); mode 0400. Docker Compose file secrets preserve host ownership. On the pinned Linux Mongo image, verify its mongodb UID (normally 999). Set root-secret owner to that UID. Make a second file `mongo_app_password_init` with the **same bytes** as mongo_app_password, owned by the Mongo UID; keep the operator copy owned by UID 10001. All three files mode 0400. This lets database initialization and the non-root operator read only their respective mounts; never make secret files world-readable. If the target image uses another UID, adapt file ownership before startup.
3. Set LOCAL_DATA_ROOT, LOCAL_OBJECT_ROOT, LOCAL_EXPORT_ROOT to absolute local directories, and CVAT_NETWORK. Give UID 10001 write access only to objects/exports. CVAT_TOKEN is a local runtime credential; do not commit an environment file.
4. `docker compose -f deploy/onprem/compose.yaml up -d mongo`
5. `docker compose -f deploy/onprem/compose.yaml --profile operator run --rm operator eyes-local health`
6. Run `eyes-local --help` in the operator service for ingest, register, task lifecycle, prediction import, reviewed export, expert finalization, and local document backup/restore. For exports pass global `--exports /exports` before subcommand.

`eyes-local` is a trusted administrator CLI, not an authenticated multi-user web service. The expert attestation flag records an explicit operator action; it does not prove medical credentials. CVAT provides the clinician UI and its own user roles. Do not expose this CLI through an unauthenticated API.

A fresh Mongo volume runs mongo-init.js once. Changing secret files does not rotate existing DB users; rotate through an authenticated local maintenance procedure. Keep authentication, TLS/firewall, egress and restore-drill checks in the hospital acceptance gate.
