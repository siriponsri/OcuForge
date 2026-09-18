"""Validate the non-blocking Colab reproduction lane without authenticating or uploading data."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks/colab/OCUFORGE_REPRO_SMOKE.ipynb"
REPORT = ROOT / "docs/COLAB_MCP_READINESS.json"
SECRET_PATTERNS = (
    re.compile(r"(?:hf|ghp|github_pat|sk)-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"ya29\.[0-9A-Za-z_-]{20,}"),
    re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----"),
)
REQUIRED_NOTEBOOK_MARKERS = (
    "scripts/synthetic_roundtrip.py",
    "OCUFORGE_RUN_SMOKE",
    "Authentication attempted: no",
)


def _git_output(*args: str) -> str | None:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def validate_notebook(path: Path = NOTEBOOK) -> dict[str, Any]:
    """Check that the tracked notebook is clean, parseable, and secret-free."""

    if not path.is_file():
        return {"status": "BLOCKED", "reason": f"Missing notebook: {path.relative_to(ROOT).as_posix()}"}
    raw = path.read_text(encoding="utf-8")
    for pattern in SECRET_PATTERNS:
        if pattern.search(raw):
            return {"status": "BLOCKED", "reason": "Potential credential pattern in notebook"}
    try:
        notebook = json.loads(raw)
    except json.JSONDecodeError as exc:
        return {"status": "BLOCKED", "reason": f"Invalid notebook JSON: {exc.msg}"}
    if notebook.get("nbformat") != 4 or not isinstance(notebook.get("cells"), list):
        return {"status": "BLOCKED", "reason": "Notebook is not nbformat 4 with a cell list"}
    if not notebook.get("metadata", {}).get("kernelspec", {}).get("name"):
        return {"status": "BLOCKED", "reason": "Notebook is missing a kernelspec"}

    source = "\n".join(
        "".join(cell.get("source", [])) if isinstance(cell.get("source"), list) else cell.get("source", "")
        for cell in notebook["cells"]
        if isinstance(cell, dict)
    )
    missing = [marker for marker in REQUIRED_NOTEBOOK_MARKERS if marker not in source]
    if missing:
        return {"status": "BLOCKED", "reason": f"Notebook missing required markers: {', '.join(missing)}"}
    for index, cell in enumerate(notebook["cells"]):
        if not isinstance(cell, dict) or cell.get("cell_type") not in {"code", "markdown"}:
            return {"status": "BLOCKED", "reason": f"Unsupported cell at index {index}"}
        if cell.get("cell_type") == "code" and cell.get("outputs"):
            return {"status": "BLOCKED", "reason": f"Notebook is not clean; cell {index} has outputs"}
    return {
        "status": "PASS",
        "path": path.relative_to(ROOT).as_posix(),
        "cells": len(notebook["cells"]),
        "execution": "structural-only; no Colab runtime was started",
    }


def _local_mcp_config_present() -> bool:
    """Detect a dedicated local Colab MCP config path without reading its contents."""

    config_paths = (
        Path.home() / ".config/colab-mcp",
        Path.home() / ".config/colab-mcp/config.json",
        Path.home() / ".config/googlecolab",
        Path.home() / ".config/googlecolab/config.json",
    )
    return any(path.is_file() for path in config_paths)


def assess_integrations() -> dict[str, Any]:
    """Assess local readiness by presence only; never authenticates or prints secret values."""

    mcp_command = shutil.which("colab-mcp") or shutil.which("googlecolab-colab-mcp")
    mcp_config = _local_mcp_config_present()
    gdrive_command = shutil.which("gdrive")
    gdrive_config = any(
        path.is_file()
        for path in (
            Path.home() / ".config/gdrive",
            Path.home() / ".config/gdrive/config.json",
            Path.home() / "AppData/Roaming/gdrive",
        )
    )
    if mcp_command or mcp_config:
        mcp_status = "PASS_WITH_WARNINGS"
        mcp_reason = "Colab MCP command/config entry detected; authenticated smoke was not attempted."
    else:
        mcp_status = "NOT_CONFIGURED"
        mcp_reason = "No Colab MCP command or named local MCP config entry was detected."
    if gdrive_command and gdrive_config:
        drive_status = "PASS_WITH_WARNINGS"
        drive_reason = "Drive sync command/config detected; authenticated folder access was not attempted."
    else:
        drive_status = "NOT_CONFIGURED"
        drive_reason = "No configured headless Drive sync command and config were detected."

    return {
        "colab_mcp": {"status": mcp_status, "reason": mcp_reason},
        "drive_sync": {"status": drive_status, "reason": drive_reason},
        "maxplus_launcher": {
            "status": (
                "PASS"
                if Path(r"C:\Users\Siripon Sri\bin\maxplus-codex.cmd").is_file()
                else "PASS_WITH_WARNINGS"
            ),
            "reason": "Required MaxPlus launcher presence checked without invoking a child agent.",
        },
        "security": {
            "auth_attempted": False,
            "credential_values_logged": False,
        },
    }


def build_report() -> dict[str, Any]:
    notebook = validate_notebook()
    integrations = assess_integrations()
    statuses = [notebook["status"], integrations["colab_mcp"]["status"], integrations["drive_sync"]["status"]]
    if "BLOCKED" in statuses:
        overall = "BLOCKED"
    elif all(status == "PASS" for status in statuses):
        overall = "PASS"
    else:
        overall = "PASS_WITH_WARNINGS"
    return {
        "schema_version": "0.1",
        "status": overall,
        "branch": _git_output("branch", "--show-current"),
        "commit_checked": _git_output("rev-parse", "HEAD"),
        "baseline_commit_inspected": "a0accc0",
        "commits_inspected": (_git_output("log", "-5", "--format=%h %s") or "").splitlines(),
        "files_inspected": [
            "AGENTS.md",
            "HANDOFF.md",
            "docs/POC_MASTER_PLAN.md",
            "docs/CTR_MODULE_CONTRACT.md",
            "docs/runbooks/R1_R2R3_OVERNIGHT_RUNBOOK.md",
            "notebooks/colab/OCUFORGE_REPRO_SMOKE.ipynb",
            "scripts/synthetic_roundtrip.py",
            "scripts/validate_colab_lane.py",
        ],
        "scope": "non-blocking public/synthetic Colab reproduction utility; no scientific gate dependency",
        "checks": {
            "notebook": notebook,
            "integrations": integrations,
        },
        "next_safe_action": (
            "If needed, configure googlecolab/colab-mcp and headless Drive sync using owner-approved local "
            "auth; rerun this validator and perform a small public/synthetic notebook smoke. Do not upload private "
            "data or keep a Colab GPU running for standby."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-report", action="store_true", help=f"write JSON report to {REPORT}")
    args = parser.parse_args()
    report = build_report()
    if args.write_report:
        REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 1 if report["status"] == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
