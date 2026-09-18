"""Small, non-MIL IDRiD ROI baseline with masked supported-lesion supervision."""

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from eyes_contracts.r3 import (
    R3ROIInput,
    R3ROITarget,
    SUPPORTED_LESION_CLASSES,
    validate_r3_manifests,
)
from eyes_contracts.validators import read_records


MODEL_TYPE = "R3_MASKED_LINEAR_RGB_BASELINE"
_SEMANTICS = [
    "SUPPORTED_LESION",
    "NO_SUPPORTED_LESION_IN_ROI",
    "UNKNOWN_OR_UNSUPPORTED_FINDING",
    "WEAK_NEGATIVE_FOR_SUPPORTED_CLASS",
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_path(root: str | Path, relative_uri: str) -> Path:
    root_path = Path(root).resolve()
    path = (root_path / relative_uri).resolve()
    if not path.is_relative_to(root_path) or not path.is_file():
        raise ValueError("R3 image path is missing or escapes the declared data root")
    return path


def _read_manifests(input_manifest, target_manifest):
    inputs = read_records(input_manifest)
    targets = read_records(target_manifest)
    if not all(isinstance(row, R3ROIInput) for row in inputs):
        raise ValueError("R3 input manifest must contain only r3_roi_input.v0.1 records")
    if not all(isinstance(row, R3ROITarget) for row in targets):
        raise ValueError("R3 target manifest must contain only r3_roi_target.v0.1 records")
    summary = validate_r3_manifests(inputs, targets)
    return inputs, targets, summary


def _feature_vector(row: R3ROIInput, data_root, feature_size: int) -> np.ndarray:
    source_path = _safe_path(data_root, row.source_image_relative_uri)
    roi_path = _safe_path(data_root, row.roi_image_relative_uri)
    if _sha256(source_path) != row.source_image_sha256:
        raise ValueError(f"Source image hash mismatch for {row.source_image_id}")
    if _sha256(roi_path) != row.roi_image_sha256:
        raise ValueError(f"ROI image hash mismatch for {row.roi_id}")
    with Image.open(source_path) as source:
        if source.size != (row.source_width_px, row.source_height_px) or source.mode != "RGB":
            raise ValueError(f"Source image geometry/mode mismatch for {row.source_image_id}")
    with Image.open(roi_path) as roi:
        if roi.size != (row.roi_width_px, row.roi_height_px) or roi.mode != "RGB":
            raise ValueError(f"ROI image geometry/mode mismatch for {row.roi_id}")
        resized = roi.resize((feature_size, feature_size), Image.Resampling.BILINEAR)
        pixels = np.asarray(resized, dtype=np.float32) / 255.0
    return np.concatenate((pixels.reshape(-1), pixels.mean(axis=(0, 1)), pixels.std(axis=(0, 1))))


def _validate_config(config):
    if (
        config["task"] != "r3_supported_lesion_multilabel"
        or config["model_type"] != MODEL_TYPE
        or config["dataset_id"] != "idrid_v1"
        or config.get("train_split", "TRAIN") != "TRAIN"
        or config.get("evaluation_split", "TEST") != "TEST"
    ):
        raise ValueError("R3 config must select the separate masked linear ROI baseline")
    if config["classes"] != list(SUPPORTED_LESION_CLASSES):
        raise ValueError("R3 config must contain exactly the four supported lesion classes")
    if not isinstance(config["feature_size"], int) or not 2 <= config["feature_size"] <= 64:
        raise ValueError("R3 feature_size must be an integer from 2 through 64")
    if not isinstance(config["epochs"], int) or config["epochs"] < 1:
        raise ValueError("R3 epochs must be positive")
    if not np.isfinite(config["learning_rate"]) or config["learning_rate"] <= 0:
        raise ValueError("R3 learning_rate must be finite and positive")
    for key in ["l2", "threshold"]:
        if not np.isfinite(config[key]) or config[key] < 0:
            raise ValueError(f"R3 {key} must be finite and non-negative")
    if config["threshold"] > 1:
        raise ValueError("R3 threshold must be at most 1")
    return config


def _config(config_path):
    config = {
        "task": "r3_supported_lesion_multilabel",
        "model_type": MODEL_TYPE,
        "dataset_id": "idrid_v1",
        "classes": list(SUPPORTED_LESION_CLASSES),
        "feature_size": 16,
        "epochs": 100,
        "learning_rate": 0.1,
        "l2": 0.0001,
        "threshold": 0.5,
        "seed": 42,
    }
    if config_path is not None:
        supplied = json.loads(Path(config_path).read_text(encoding="utf-8"))
        config.update(supplied)
    return _validate_config(config)


def _target_arrays(inputs, targets):
    target_by_roi = {target.roi_id: target for target in targets}
    values = np.zeros((len(inputs), len(SUPPORTED_LESION_CLASSES)), dtype=np.float32)
    observed = np.zeros_like(values, dtype=bool)
    class_index = {name: index for index, name in enumerate(SUPPORTED_LESION_CLASSES)}
    for row_index, row in enumerate(inputs):
        target = target_by_roi[row.roi_id]
        if target.target_semantic == "SUPPORTED_LESION":
            observed[row_index, class_index[target.target_class]] = True
            values[row_index, class_index[target.target_class]] = 1
        elif target.target_semantic == "WEAK_NEGATIVE_FOR_SUPPORTED_CLASS":
            observed[row_index, class_index[target.target_class]] = True
        elif target.target_semantic == "NO_SUPPORTED_LESION_IN_ROI":
            observed[row_index, :] = True
        elif target.target_semantic not in _SEMANTICS:
            raise ValueError("Unknown R3 target semantic")
    return values, observed


def _loss_and_grad(features, values, observed, weights, bias, l2):
    logits = features @ weights + bias
    probabilities = 1 / (1 + np.exp(-np.clip(logits, -60, 60)))
    count = max(int(observed.sum()), 1)
    residual = (probabilities - values) * observed
    loss = -np.sum(
        observed * (values * np.log(np.clip(probabilities, 1e-7, 1))
                    + (1 - values) * np.log(np.clip(1 - probabilities, 1e-7, 1)))
    ) / count
    loss += l2 * float(np.sum(weights * weights)) / 2
    gradient_w = features.T @ residual / count + l2 * weights
    gradient_b = residual.sum(axis=0) / count
    return float(loss), gradient_w, gradient_b


def _fingerprint(config, inputs, targets):
    payload = {
        "config": config,
        "inputs": [row.model_dump(mode="json") for row in sorted(inputs, key=lambda row: row.roi_id)],
        "targets": [row.model_dump(mode="json") for row in sorted(targets, key=lambda row: row.roi_id)],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def train_roi_classifier(input_manifest, target_manifest, data_root, out, config_path=None):
    """Train the four independent supported-lesion heads on explicit R3 supervision."""

    inputs, targets, manifest_summary = _read_manifests(input_manifest, target_manifest)
    config = _config(config_path)
    train_indices = [index for index, row in enumerate(inputs) if row.released_split == "TRAIN"]
    if not train_indices:
        raise ValueError("R3 training requires released TRAIN ROI rows")
    features = np.stack([_feature_vector(inputs[index], data_root, config["feature_size"]) for index in train_indices])
    values, observed = _target_arrays(inputs, targets)
    train_values = values[train_indices]
    train_observed = observed[train_indices]
    if not train_observed.any():
        raise ValueError("R3 training has no learned target; UNKNOWN rows cannot become negatives")
    if not train_observed.any(axis=0).all():
        raise ValueError("R3 training requires explicit supervision for every supported class")

    weights = np.zeros((features.shape[1], len(SUPPORTED_LESION_CLASSES)), dtype=np.float32)
    bias = np.zeros(len(SUPPORTED_LESION_CLASSES), dtype=np.float32)
    history = []
    for epoch in range(config["epochs"]):
        loss, gradient_w, gradient_b = _loss_and_grad(
            features, train_values, train_observed, weights, bias, config["l2"]
        )
        weights -= config["learning_rate"] * gradient_w
        bias -= config["learning_rate"] * gradient_b
        if not np.isfinite(loss) or not np.isfinite(weights).all() or not np.isfinite(bias).all():
            raise RuntimeError("R3 training produced non-finite values")
        history.append({"epoch": epoch, "loss": loss})

    fingerprint = _fingerprint(config, inputs, targets)
    out_path = Path(out)
    out_path.mkdir(parents=True, exist_ok=True)
    model_path = out_path / "model.npz"
    if model_path.exists():
        raise ValueError("R3 output already exists; choose a fresh output directory")
    np.savez_compressed(
        model_path,
        weights=weights,
        bias=bias,
        classes=np.asarray(SUPPORTED_LESION_CLASSES),
        feature_size=np.asarray(config["feature_size"]),
        fingerprint=np.asarray(fingerprint),
        config_json=np.asarray(json.dumps(config, sort_keys=True)),
    )
    target_by_roi = {target.roi_id: target for target in targets}
    eligible_train_indices = [
        index for local_index, index in enumerate(train_indices) if train_observed[local_index].any()
    ]
    unknown_ids = [
        row.roi_id
        for row in inputs
        if target_by_roi[row.roi_id].target_semantic == "UNKNOWN_OR_UNSUPPORTED_FINDING"
    ]
    run = {
        "status": "COMPLETED",
        "model_type": MODEL_TYPE,
        "dataset_id": "idrid_v1",
        "classifier_is_mil": False,
        "global_dr_model": False,
        "supported_classes": list(SUPPORTED_LESION_CLASSES),
        "manifest": manifest_summary,
        "training_roi_ids": [inputs[index].roi_id for index in eligible_train_indices],
        "released_train_roi_ids": [inputs[index].roi_id for index in train_indices],
        "excluded_from_training_roi_ids": [
            inputs[index].roi_id for index in train_indices if index not in eligible_train_indices
        ],
        "excluded_unknown_roi_ids": unknown_ids,
        "history": history,
        "fingerprint": fingerprint,
        "scientific_result_eligible": False,
    }
    (out_path / "run.json").write_text(json.dumps(run, indent=2), encoding="utf-8")
    return run


def _load_model(model_path):
    with np.load(model_path, allow_pickle=False) as model:
        classes = tuple(str(value) for value in model["classes"].tolist())
        if classes != SUPPORTED_LESION_CLASSES:
            raise ValueError("R3 model class identity mismatch")
        weights = model["weights"].astype(np.float32)
        bias = model["bias"].astype(np.float32)
        feature_size = int(model["feature_size"])
        fingerprint = str(model["fingerprint"].tolist())
        config = json.loads(str(model["config_json"].tolist()))
    _validate_config(config)
    if weights.shape[1] != len(SUPPORTED_LESION_CLASSES) or bias.shape != (len(SUPPORTED_LESION_CLASSES),):
        raise ValueError("R3 model shape mismatch")
    if weights.shape[0] != feature_size * feature_size * 3 + 6 or not np.isfinite(weights).all():
        raise ValueError("R3 model feature provenance mismatch")
    return weights, bias, feature_size, fingerprint, config


def evaluate_roi_classifier(
    input_manifest, target_manifest, data_root, model_path, out, split="TEST", threshold=None
):
    """Evaluate the baseline on an explicit released split; metrics remain engineering evidence only."""

    if split not in ["TRAIN", "TEST"]:
        raise ValueError("R3 evaluation requires released TRAIN or TEST split")
    inputs, targets, manifest_summary = _read_manifests(input_manifest, target_manifest)
    weights, bias, feature_size, model_fingerprint, config = _load_model(model_path)
    expected_fingerprint = _fingerprint(config, inputs, targets)
    if model_fingerprint != expected_fingerprint:
        raise ValueError("R3 model/config/manifest fingerprint mismatch")
    selected = [row for row in inputs if row.released_split == split]
    if not selected:
        raise ValueError("Requested R3 split is empty")
    features = np.stack([_feature_vector(row, data_root, feature_size) for row in selected])
    probabilities = 1 / (1 + np.exp(-np.clip(features @ weights + bias, -60, 60)))
    decision_threshold = 0.5 if threshold is None else threshold
    if not 0 <= decision_threshold <= 1:
        raise ValueError("R3 evaluation threshold must be between 0 and 1")

    target_by_roi = {target.roi_id: target for target in targets}
    class_index = {name: index for index, name in enumerate(SUPPORTED_LESION_CLASSES)}
    values, observed = _target_arrays(selected, [target_by_roi[row.roi_id] for row in selected])
    score_rows = []
    for row_index, row in enumerate(selected):
        predicted_classes = [
            name
            for class_index_value, name in enumerate(SUPPORTED_LESION_CLASSES)
            if probabilities[row_index, class_index_value] >= decision_threshold
        ]
        score_rows.append(
            {
                "roi_id": row.roi_id,
                "source_image_id": row.source_image_id,
                "released_split": row.released_split,
                "probabilities": {
                    name: float(probabilities[row_index, class_index_value])
                    for class_index_value, name in enumerate(SUPPORTED_LESION_CLASSES)
                },
                "prediction_semantic": (
                    "SUPPORTED_LESION_PRESENT" if predicted_classes else "NO_SUPPORTED_LESION_IN_ROI"
                ),
                "predicted_supported_classes": predicted_classes,
                "global_semantic": row.global_semantic,
            }
        )

    per_class = {}
    for name, index in class_index.items():
        mask = observed[:, index]
        predicted = probabilities[:, index] >= decision_threshold
        per_class[name] = {
            "observed_n": int(mask.sum()),
            "positive_target_n": int(values[mask, index].sum()),
            "thresholded_accuracy": (
                float((predicted[mask] == values[mask, index]).mean()) if mask.any() else None
            ),
        }
    unknown_ids = [
        row.roi_id
        for row in selected
        if target_by_roi[row.roi_id].target_semantic == "UNKNOWN_OR_UNSUPPORTED_FINDING"
    ]
    output_path = Path(out)
    output_path.mkdir(parents=True, exist_ok=True)
    (output_path / "scores.json").write_text(json.dumps(score_rows, indent=2), encoding="utf-8")
    report = {
        "model_type": MODEL_TYPE,
        "dataset_id": "idrid_v1",
        "split": split,
        "rows": len(selected),
        "excluded_unknown_roi_ids": unknown_ids,
        "manifest": manifest_summary,
        "threshold": decision_threshold,
        "per_class": per_class,
        "scientific_result_eligible": False,
        "interpretation": "ENGINEERING_BASELINE_ONLY_NO_SCIENTIFIC_PERFORMANCE_CLAIM",
    }
    (output_path / "evaluation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
