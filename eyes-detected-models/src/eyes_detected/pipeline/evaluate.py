"""Evaluation/inference of frozen-encoder MIL checkpoints; no localization claims."""

import json
from pathlib import Path
import numpy as np
import torch
from eyes_detected.pipeline.data import load_images, load_targets, sha256
from eyes_detected.features.store import digest
from eyes_detected.pipeline.train import ResearchMIL, load_features, collate
from eyes_detected.evaluation.metrics import qwk
from eyes_contracts.models import Prediction, ModelManifest
from eyes_contracts.validators import write_records


def infer(
    manifest, features_dir, checkpoint, out, split="TEST", targets_path=None, dataset_path=None, cloud=False
):
    images, _ = load_images(manifest, dataset_path, cloud)
    if split not in ["TRAIN", "VAL", "TEST", "SENTINEL", "UNASSIGNED", "ALL"]:
        raise ValueError("Invalid split")
    selected = [im for im in images if split == "ALL" or im.split == split]
    if not selected:
        raise ValueError("Requested split empty")
    features, identity = load_features(features_dir, selected)
    ckpt = torch.load(checkpoint, map_location="cpu", weights_only=True)
    if list(identity) != ckpt["feature_identity"]:
        raise ValueError("Checkpoint encoder/preprocessing mismatch")
    model = ResearchMIL(ckpt["dim"], ckpt["task"], ckpt.get("pooling", "attention_mil"))
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    model_id = "MIL_" + sha256(checkpoint)[:32]
    rows = []
    predictions = []
    with torch.inference_mode():
        for im in selected:
            x, mask = collate([im.image_id], features, "cpu")
            r = model(x, mask)
            probs = r["dr_logits"][0].sigmoid().tolist()
            grade = sum(p > 0.5 for p in probs)
            binary = float(r["binary_logits"][0].sigmoid())
            distribution = [1 - probs[0]] + [probs[i - 1] - probs[i] for i in range(1, 4)] + [probs[-1]]
            rows.append(
                {
                    "image_id": im.image_id,
                    "split": im.split,
                    "prediction": grade if ckpt["task"] == "ordinal" else int(binary >= 0.5),
                    "binary_dr_probability": binary if ckpt["task"] == "binary" else None,
                }
            )
            # Auxiliary heads may have no supervision. Do not publish their probabilities as trained results.
            predictions.append(
                Prediction(
                    prediction_id="P_" + digest({"checkpoint": model_id, "image_id": im.image_id})[:40],
                    image_id=im.image_id,
                    model_manifest_id=model_id,
                    dr={
                        "grading_protocol": ckpt["protocol"],
                        "grade": grade,
                        "ordinal_probs": probs,
                        "confidence": distribution[grade],
                    }
                    if ckpt["task"] == "ordinal"
                    else None,
                    evidence=(
                        {"patch_scores": r["attention"][0].tolist()}
                        if "attention" in r
                        else None
                    ),
                )
            )
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    manifest_record = ModelManifest(
        model_manifest_id=model_id,
        name="Frozen encoder MIL research pipeline",
        version="0.2.0",
        architecture=(
            "GlobalAveragePooling-CORAL"
            if ckpt.get("pooling") == "global_average" and ckpt["task"] == "ordinal"
            else "GlobalAveragePooling-binary"
            if ckpt.get("pooling") == "global_average"
            else "AttentionMIL-CORAL"
            if ckpt["task"] == "ordinal"
            else "AttentionMIL-binary"
        ),
        encoder=identity[0],
        weight_hash=sha256(checkpoint),
        training_run_id="RUN_" + ckpt["fingerprint"][:32],
        training_dataset_ids=ckpt["training_dataset_ids"],
        known_limitations=[
            "RESEARCH_ONLY",
            "NO_CLINICAL_VALIDATION",
            "NO_TRAINED_LOCALIZER",
            "UNCALIBRATED",
        ]
        + (["NO_PATCH_ATTENTION_EVIDENCE"] if ckpt.get("pooling") == "global_average" else []),
        intended_research_use="Offline research evaluation; binary and ordinal tasks remain separate",
        calibration_version=None,
        ood_method=None,
        created_at=ckpt["created_at"],
    )
    write_records(out / "model_manifest.json", [manifest_record])
    write_records(out / "predictions.jsonl", predictions)
    (out / "scores.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    report = {
        "model_manifest_id": model_id,
        "checkpoint_sha256": sha256(checkpoint),
        "task": ckpt["task"],
        "split": split,
        "n": len(rows),
        "scientific_result_eligible": False,
        "localization_available": False,
        "binary_scores_file": "scores.json" if ckpt["task"] == "binary" else None,
    }
    if targets_path:
        if split not in ["VAL", "TEST", "SENTINEL"]:
            raise ValueError("Evaluation requires an explicit held-out split")
        targets = load_targets(targets_path, images)
        field = "dr_grade" if ckpt["task"] == "ordinal" else "binary_dr"
        pairs = [
            (getattr(targets[r["image_id"]], field), r["prediction"])
            for r in rows
            if r["image_id"] in targets and getattr(targets[r["image_id"]], field) is not None
        ]
        if not pairs:
            raise ValueError("No held-out labels")
        a, b = map(np.asarray, zip(*pairs))
        nclasses = 5 if ckpt["task"] == "ordinal" else 2
        matrix = np.zeros((nclasses, nclasses), dtype=int)
        np.add.at(matrix, (a, b), 1)
        report.update(
            labeled_n=len(a),
            accuracy=float((a == b).mean()),
            confusion_matrix=matrix.tolist(),
            qwk=qwk(a, b) if nclasses == 5 else None,
        )
    (out / "evaluation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
