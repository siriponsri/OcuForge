# Colab MCP Utility Readiness

**Scope:** Optional, non-blocking Colab reproduction utility lane from
`docs/runbooks/R1_R2R3_OVERNIGHT_RUNBOOK.md`.

## Decision

```text
COLAB_LANE=PASS_WITH_WARNINGS
COLAB_MCP=NOT_CONFIGURED
DRIVE_SYNC=NOT_CONFIGURED
NOTEBOOK_REPRO_SMOKE=PASS (structural validation only)
AUTHENTICATED_RUNTIME_SMOKE=NOT_CONFIGURED
```

The tracked notebook is a clean reproduction entry point and calls the existing
`scripts/synthetic_roundtrip.py` workflow. No Colab runtime, GPU, Drive mount, MCP session, or credentialed
request was started. The utility lane does not block R1 or R2/R3 and does not claim that Colab or Drive access
is ready.

## Evidence inspected

- Branch: `siriponsri/exp-colab-mcp-utility`.
- Baseline commit inspected: `a0accc0` (`Align campaign execution gate semantics`).
- Runbook: `docs/runbooks/R1_R2R3_OVERNIGHT_RUNBOOK.md`, including the optional Colab lane and notebook-first
  contract.
- Notebook: `notebooks/colab/OCUFORGE_REPRO_SMOKE.ipynb`.
- Validator: `scripts/validate_colab_lane.py`.
- MaxPlus launcher: `C:\Users\Siripon Sri\bin\maxplus-codex.cmd` was present; it was not invoked to launch
  another worker.
- Local readiness probe: no `gdrive` command, configured headless Drive sync state, or named Colab MCP
  command/local MCP config entry was detected.
- Secret safety: no authentication was attempted and no credential value was read, printed, or stored.

## Public reference verification

On 2026-09-19, metadata-only checks verified the runbook's public references without authentication or artifact
download:

- `https://github.com/googlecolab/colab-mcp.git`: `HEAD` and `refs/heads/main` resolved to
  `b9ab3899e0f1fa493390b1fd6d54aa2e464ecdf1`.
- `https://github.com/glotlabs/gdrive.git`: `HEAD` and `refs/heads/main` resolved to
  `855155649a5911565c9134eac6a1f9b9bf235494`.
- OWNER Drive reference from the runbook: `https://drive.google.com/drive/folders/1zfYxkamwA15N9l7Wwof0sWGkis20rh2h?usp=sharing`
  returned HTTP `200` for a metadata-only `HEAD` request. No folder contents were listed or downloaded.

The validator intentionally does not inspect generic local MCP configuration files: those files may contain
credentials. It checks only dedicated Colab MCP config paths by file presence, so `NOT_CONFIGURED` remains the
conservative result until an owner-approved named integration is configured and separately smoke-tested.

## Validation

Run from the repository root:

```powershell
python scripts/validate_colab_lane.py --write-report
python -m pytest tests/test_colab_lane.py -q
```

The validator performs notebook JSON/metadata/marker checks and presence-only integration checks. It never
logs credential values, mounts Drive, starts a Colab GPU, or uploads files. The checked-in report is
`docs/COLAB_MCP_READINESS.json`.

The local authoritative synthetic roundtrip was attempted during this review and could not start because the
editable OcuForge packages are not installed in the current Python environment
(`ModuleNotFoundError: eyes_detected`). This is an environment limitation, not a fabricated result;
rerun it only after the approved local or Colab environment is installed.

## Next safe action

If the optional lane is needed, configure `googlecolab/colab-mcp` and the owner-approved headless Drive sync
outside Git, then rerun the validator and perform a small public/synthetic notebook smoke. Do not place tokens in
the notebook or reports, upload private data, or keep a Colab GPU running for standby.
