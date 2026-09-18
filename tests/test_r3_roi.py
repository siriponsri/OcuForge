import hashlib
import json

import pytest
from PIL import Image

from eyes_contracts.r3 import (
    R3ROIInput,
    R3ROITarget,
    SUPPORTED_LESION_CLASSES,
    validate_r3_manifests,
)
from eyes_contracts.validators import validate, write_records
from eyes_detected.lesions.roi_classifier import evaluate_roi_classifier, train_roi_classifier


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mask_evidence(tmp_path, *, statuses=None, roi_presence=None):
    statuses = statuses or {name: "PRESENT_NONEMPTY" for name in SUPPORTED_LESION_CLASSES}
    roi_presence = roi_presence or {name: "PRESENT" for name in SUPPORTED_LESION_CLASSES}
    rows = []
    for index, name in enumerate(SUPPORTED_LESION_CLASSES):
        status = statuses[name]
        mask_path = tmp_path / f"mask_{index}.tif" if status.startswith("PRESENT") else None
        if mask_path:
            mask_path.write_bytes(f"mask-{name}".encode())
        rows.append(
            {
                "lesion_class": name,
                "status": status,
                "roi_presence": roi_presence[name],
                "source_mask_relative_uri": mask_path.name if mask_path else None,
                "source_mask_sha256": digest(mask_path) if mask_path else None,
            }
        )
    return rows


def roi_row(tmp_path, roi_id="ROI_1", split="TRAIN", provenance="IDRID_MASK_FOREGROUND_BBOX"):
    source = tmp_path / f"{roi_id}_source.jpg"
    crop = tmp_path / f"{roi_id}_crop.jpg"
    color = 20 + sum(roi_id.encode()) % 150
    Image.new("RGB", (20, 20), (color, 40, 20)).save(source)
    Image.new("RGB", (10, 10), (color, 40, 20)).save(crop)
    clean = provenance == "EXPLICIT_CLEAN_NEGATIVE_ROI"
    empty = provenance == "PRESENT_EMPTY_MASK_ROI"
    if clean:
        statuses = {name: "PRESENT_EMPTY" for name in SUPPORTED_LESION_CLASSES}
        presence = {name: "ABSENT" for name in SUPPORTED_LESION_CLASSES}
    elif empty:
        statuses = {name: "MISSING" for name in SUPPORTED_LESION_CLASSES}
        statuses["MICROANEURYSM"] = "PRESENT_EMPTY"
        presence = {name: "UNKNOWN" for name in SUPPORTED_LESION_CLASSES}
        presence["MICROANEURYSM"] = "ABSENT"
    else:
        statuses = {name: "PRESENT_NONEMPTY" for name in SUPPORTED_LESION_CLASSES}
        presence = {name: "PRESENT" if name == "MICROANEURYSM" else "ABSENT" for name in SUPPORTED_LESION_CLASSES}
    return {
        "dataset_id": "idrid_v1",
        "source_type": "SYNTHETIC_FIXTURE",
        "roi_id": roi_id,
        "source_image_id": f"IDRiD_{roi_id}",
        "source_image_sha256": digest(source),
        "source_image_relative_uri": source.name,
        "roi_image_sha256": digest(crop),
        "roi_image_relative_uri": crop.name,
        "source_width_px": 20,
        "source_height_px": 20,
        "roi_width_px": 10,
        "roi_height_px": 10,
        "released_split": split,
        "roi_class": None if clean else "MICROANEURYSM",
        "roi_provenance": provenance,
        "mask_coverage": "COMPLETE_SUPPORTED_MASK_COVERAGE" if clean or not empty else "INCOMPLETE_SUPPORTED_MASK_COVERAGE",
        "mask_evidence": mask_evidence(tmp_path, statuses=statuses, roi_presence=presence),
        "geometry": {
            "bbox_xyxy_px": [0, 0, 10, 10],
            "bbox_xyxy_norm": [0, 0, 0.5, 0.5],
            "provenance": "EXPLICIT_ROI_PROVENANCE" if clean or empty else "IDRID_EXACT_MASK_FOREGROUND_BBOX",
        },
    }


def target_for(row, semantic="SUPPORTED_LESION", target_class=None):
    return {
        "dataset_id": row["dataset_id"],
        "roi_id": row["roi_id"],
        "source_image_id": row["source_image_id"],
        "source_image_sha256": row["source_image_sha256"],
        "released_split": row["released_split"],
        "target_semantic": semantic,
        "target_class": row.get("roi_class") if target_class is None else target_class,
    }


def test_r3_contract_preserves_mask_and_split_semantics(tmp_path):
    row = roi_row(tmp_path)
    input_record = R3ROIInput.model_validate(row)
    target_record = R3ROITarget.model_validate(target_for(row))
    summary = validate_r3_manifests([input_record], [target_record])
    assert summary["released_split_preserved"] is True
    assert validate(input_record.model_dump()).roi_id == "ROI_1"
    assert input_record.global_semantic != "NO_SUPPORTED_LESION_IN_ROI"
    with pytest.raises(ValueError):
        R3ROITarget.model_validate(target_for(row, "GLOBAL_NO_DR"))


def test_r3_weak_negative_requires_present_empty_mask(tmp_path):
    row = roi_row(tmp_path, provenance="PRESENT_EMPTY_MASK_ROI")
    input_record = R3ROIInput.model_validate(row)
    target = R3ROITarget.model_validate(
        target_for(row, "WEAK_NEGATIVE_FOR_SUPPORTED_CLASS", "MICROANEURYSM")
    )
    validate_r3_manifests([input_record], [target])

    row["mask_evidence"] = mask_evidence(
        tmp_path,
        statuses={name: "MISSING" for name in SUPPORTED_LESION_CLASSES},
        roi_presence={name: "UNKNOWN" for name in SUPPORTED_LESION_CLASSES},
    )
    row["roi_class"] = None
    row["roi_provenance"] = "UNANNOTATED_OR_UNSUPPORTED_REGION"
    row["mask_coverage"] = "INCOMPLETE_SUPPORTED_MASK_COVERAGE"
    unknown_input = R3ROIInput.model_validate(row)
    with pytest.raises(ValueError, match="matching present-empty"):
        validate_r3_manifests([unknown_input], [target])


def test_r3_rejects_missing_mask_as_negative_and_requires_clean_negative_provenance(tmp_path):
    row = roi_row(tmp_path)
    row["mask_evidence"] = mask_evidence(
        tmp_path,
        statuses={name: "MISSING" for name in SUPPORTED_LESION_CLASSES},
        roi_presence={name: "UNKNOWN" for name in SUPPORTED_LESION_CLASSES},
    )
    row["roi_class"] = None
    row["roi_provenance"] = "UNANNOTATED_OR_UNSUPPORTED_REGION"
    row["mask_coverage"] = "INCOMPLETE_SUPPORTED_MASK_COVERAGE"
    input_record = R3ROIInput.model_validate(row)
    unknown = R3ROITarget.model_validate(target_for(row, "UNKNOWN_OR_UNSUPPORTED_FINDING"))
    validate_r3_manifests([input_record], [unknown])
    with pytest.raises(ValueError, match="explicit clean-negative"):
        validate_r3_manifests(
            [input_record], [R3ROITarget.model_validate(target_for(row, "NO_SUPPORTED_LESION_IN_ROI"))]
        )


def test_r3_rejects_cross_split_source_identity_leakage(tmp_path):
    train = roi_row(tmp_path, "ROI_T", "TRAIN")
    test = roi_row(tmp_path, "ROI_E", "TEST")
    test["source_image_id"] = train["source_image_id"]
    test["source_image_sha256"] = train["source_image_sha256"]
    with pytest.raises(ValueError, match="identity or released split"):
        validate_r3_manifests(
            [R3ROIInput.model_validate(train), R3ROIInput.model_validate(test)],
            [
                R3ROITarget.model_validate(target_for(train)),
                R3ROITarget.model_validate(target_for(test)),
            ],
        )


def test_r3_numpy_baseline_trains_and_evaluates_without_mil_or_global_path(tmp_path):
    rows = [
        roi_row(tmp_path, "ROI_T", "TRAIN"),
        roi_row(tmp_path, "ROI_N", "TRAIN", "EXPLICIT_CLEAN_NEGATIVE_ROI"),
        roi_row(tmp_path, "ROI_E", "TEST"),
    ]
    targets = [
        target_for(rows[0]),
        target_for(rows[1], "NO_SUPPORTED_LESION_IN_ROI"),
        target_for(rows[2]),
    ]
    input_path = tmp_path / "inputs.jsonl"
    target_path = tmp_path / "targets.jsonl"
    write_records(input_path, [R3ROIInput.model_validate(row) for row in rows])
    write_records(target_path, [R3ROITarget.model_validate(row) for row in targets])
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "task": "r3_supported_lesion_multilabel",
                "model_type": "R3_MASKED_LINEAR_RGB_BASELINE",
                "epochs": 3,
                "learning_rate": 0.1,
            }
        ),
        encoding="utf-8",
    )
    run = train_roi_classifier(input_path, target_path, tmp_path, tmp_path / "run", config_path)
    report = evaluate_roi_classifier(
        input_path, target_path, tmp_path, tmp_path / "run/model.npz", tmp_path / "eval"
    )
    assert run["classifier_is_mil"] is False
    assert run["global_dr_model"] is False
    assert report["split"] == "TEST" and report["scientific_result_eligible"] is False
    assert len(json.loads((tmp_path / "eval/scores.json").read_text(encoding="utf-8"))) == 1
