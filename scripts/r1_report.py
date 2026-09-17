"""Create an R1 report from observed evaluation output and an approved P0 decision."""

import argparse
import hashlib
import json
from pathlib import Path


REQUIRED = {"model_manifest_id", "checkpoint_sha256", "task", "split", "n", "labeled_n", "accuracy", "confusion_matrix", "qwk"}
P0_UNLOCK_STATES = {"PASS", "PASS_WITH_WARNINGS"}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_p0(path):
    p0 = json.loads(Path(path).read_text(encoding="utf-8"))
    state = p0.get("gate_state")
    if state not in P0_UNLOCK_STATES or p0.get("outcome") != state:
        raise ValueError("R1 report requires a PASS or PASS_WITH_WARNINGS P0 decision")
    if p0.get("blockers"):
        raise ValueError("R1 report cannot be created while P0 blockers remain")
    warnings = p0.get("warnings")
    if not isinstance(warnings, list):
        raise ValueError("R1 report requires the explicit P0 warning record")
    if any(
        not {"warning_id", "scope", "finding", "blocks_r1"}.issubset(warning)
        or warning["blocks_r1"] is not False
        for warning in warnings
    ):
        raise ValueError("R1 report requires explicit non-blocking P0 warnings")
    if state == "PASS_WITH_WARNINGS" and not warnings:
        raise ValueError("P0 PASS_WITH_WARNINGS must carry warnings into the R1 report")
    return p0


def build_report(path, p0_path):
    evaluation_path = Path(path)
    evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
    p0 = load_p0(p0_path)
    missing = REQUIRED - set(evaluation)
    if missing:
        raise ValueError(f"Evaluation is missing fields: {sorted(missing)}")
    if evaluation["task"] != "ordinal" or evaluation["split"] != "TEST":
        raise ValueError("R1 report requires ordinal TEST evaluation")
    if evaluation["n"] < 1 or evaluation["labeled_n"] < 1:
        raise ValueError("R1 report requires observed held-out cases")
    return {
        "schema_version": "r1_evaluation_report.v0.2",
        "artifact_schema_version": "r1_experiment_artifact.v1",
        "status": "OBSERVED_EVALUATION",
        "p0_gate_state": p0["gate_state"],
        "p0_outcome": p0["outcome"],
        "p0_blockers": p0.get("blockers", []),
        "p0_warnings": p0["warnings"],
        "evidence_audit_date": p0.get("evidence_audit_date"),
        "gate_decision_date": p0.get("gate_decision_date"),
        "evaluation_sha256": sha256(evaluation_path),
        "model_manifest_id": evaluation["model_manifest_id"],
        "checkpoint_sha256": evaluation["checkpoint_sha256"],
        "task": evaluation["task"],
        "split": evaluation["split"],
        "n": evaluation["n"],
        "labeled_n": evaluation["labeled_n"],
        "metrics": {
            "qwk": evaluation["qwk"],
            "accuracy": evaluation["accuracy"],
            "confusion_matrix": evaluation["confusion_matrix"],
        },
        "claim_ceiling": "Observed public benchmark evidence only; not clinical validation or diagnosis",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluation", required=True)
    parser.add_argument("--p0", required=True, help="Reviewed R1-P0 decision record")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    report = build_report(args.evaluation, args.p0)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
