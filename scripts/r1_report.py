"""Create a report from observed evaluation output without inventing metrics."""

import argparse
import hashlib
import json
from pathlib import Path


REQUIRED = {"model_manifest_id", "checkpoint_sha256", "task", "split", "n", "labeled_n", "accuracy", "confusion_matrix", "qwk"}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_report(path):
    evaluation_path = Path(path)
    evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
    missing = REQUIRED - set(evaluation)
    if missing:
        raise ValueError(f"Evaluation is missing fields: {sorted(missing)}")
    if evaluation["task"] != "ordinal" or evaluation["split"] != "TEST":
        raise ValueError("R1 report requires ordinal TEST evaluation")
    if evaluation["n"] < 1 or evaluation["labeled_n"] < 1:
        raise ValueError("R1 report requires observed held-out cases")
    return {
        "schema_version": "r1_evaluation_report.v0.1",
        "status": "OBSERVED_EVALUATION",
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
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    report = build_report(args.evaluation)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
