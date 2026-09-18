"""Build and execute one bounded IDRiD R3 ROI baseline checkpoint."""

import argparse
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
from eyes_contracts.validators import write_records
from eyes_detected.lesions.roi_classifier import evaluate_roi_classifier, train_roi_classifier


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative_uri(path: Path, root: Path) -> str:
    try:
        relative = path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"Checkpoint path is outside data root: {path}") from exc
    return relative.as_posix()


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _verify_acquisition(acquisition: dict, r2: dict) -> dict:
    source_provenance = acquisition["source"]["source_provenance"]
    if source_provenance != "OWNER_ACQUIRED_OFFICIAL_IDRID":
        raise ValueError("R3 checkpoint requires OWNER_ACQUIRED_OFFICIAL_IDRID provenance")
    if acquisition["dataset_id"] != "idrid_v1" or r2["dataset_id"] != "idrid_v1":
        raise ValueError("R3 checkpoint is restricted to idrid_v1")
    archive = acquisition["archive"]
    inventory = acquisition["inventory"]
    if archive["extraction_integrity"] != "PASS_ZIP_CRC_AND_EXTRACTED_INVENTORY":
        raise ValueError("IDRiD archive integrity evidence is not passing")
    if inventory["copy_integrity"] != "PASS" or inventory["source_dest_sha256_mismatches"]:
        raise ValueError("IDRiD source copy integrity evidence is not passing")
    if r2["qa"]["train_test_image_id_overlap"]:
        raise ValueError("R2 manifest contains released train/test image identity overlap")
    if r2["qa"]["geometry_qa"] != "PASS":
        raise ValueError("R2 ROI geometry evidence is not passing")
    classes = tuple(r2["derivation"]["supported_classes"])
    if classes != SUPPORTED_LESION_CLASSES:
        raise ValueError("R2 supported class taxonomy does not match the R3 contract")
    return {
        "source_provenance": source_provenance,
        "archive_sha256": archive["sha256"],
        "archive_crc_and_extraction": archive["extraction_integrity"],
        "inventory_copy_integrity": inventory["copy_integrity"],
        "supported_classes": list(SUPPORTED_LESION_CLASSES),
    }


def _verify_source_row(r2_root: Path, image_row: dict, expected_hash: str) -> Path:
    image_path = r2_root / image_row["image_relative_path"]
    if not image_path.is_file() or _sha256(image_path) != expected_hash:
        raise ValueError(f"IDRiD source image hash mismatch for {image_row['image_id']}")
    with Image.open(image_path) as image:
        if image.mode != "RGB" or list(image.size) != image_row["image_size"]:
            raise ValueError(f"IDRiD source image geometry/mode mismatch for {image_row['image_id']}")
    return image_path


def _mask_evidence(
    r2_root: Path,
    data_root: Path,
    image_row: dict,
    bbox: tuple[int, int, int, int],
    mask_cache: dict,
) -> list[dict]:
    evidence = []
    for lesion_class in SUPPORTED_LESION_CLASSES:
        mask_record = image_row["masks"][lesion_class]
        if mask_record["status"] == "UNKNOWN":
            evidence.append(
                {
                    "lesion_class": lesion_class,
                    "status": "MISSING",
                    "roi_presence": "UNKNOWN",
                    "source_mask_relative_uri": None,
                    "source_mask_sha256": None,
                }
            )
            continue

        source = mask_record["source"]
        mask_path = r2_root / source["mask_relative_path"]
        if not mask_path.is_file() or _sha256(mask_path) != source["mask_sha256"]:
            raise ValueError(f"IDRiD mask hash mismatch for {image_row['image_id']} {lesion_class}")
        cached = mask_cache.get(lesion_class)
        if cached is None:
            with Image.open(mask_path) as mask:
                if list(mask.size) != source["mask_size"]:
                    raise ValueError(
                        f"IDRiD mask geometry mismatch for {image_row['image_id']} {lesion_class}"
                    )
                mask_array = np.asarray(mask.convert("L"))
            cached = {
                "path": mask_path,
                "hash": source["mask_sha256"],
                "array": mask_array,
                "has_global_foreground": bool(np.any(mask_array > 0)),
            }
            mask_cache[lesion_class] = cached
        x0, y0, x1, y1 = bbox
        has_global_foreground = cached["has_global_foreground"]
        has_roi_foreground = bool(np.any(cached["array"][y0:y1, x0:x1] > 0))
        evidence.append(
            {
                "lesion_class": lesion_class,
                "status": "PRESENT_NONEMPTY" if has_global_foreground else "PRESENT_EMPTY",
                "roi_presence": "PRESENT" if has_roi_foreground else "ABSENT",
                "source_mask_relative_uri": _relative_uri(cached["path"], data_root),
                "source_mask_sha256": cached["hash"],
            }
        )
    return evidence


def build_r3_manifests(r2_manifest_path: Path, acquisition_path: Path, output_root: Path, data_root: Path):
    if output_root.exists() and any(output_root.iterdir()):
        raise ValueError(f"R3 checkpoint output already exists; refusing duplicate run: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)
    r2 = _read_json(r2_manifest_path)
    acquisition = _read_json(acquisition_path)
    source_audit = _verify_acquisition(acquisition, r2)
    r2_root = Path(r2["source_root"]).resolve()
    if not r2_root.is_dir() or not data_root.resolve().is_dir():
        raise ValueError("R3 source/data root does not exist")

    images = {row["image_id"]: row for row in r2["images"]}
    rois = list(r2["rois"])
    if len(images) != 81 or len(rois) != 282:
        raise ValueError("R2 inventory must contain exactly 81 images and 282 ROI rows")
    train_images = {row["image_id"] for row in r2["images"] if row["split"] == "train"}
    test_images = {row["image_id"] for row in r2["images"] if row["split"] == "test"}
    if len(train_images) != 54 or len(test_images) != 27 or train_images & test_images:
        raise ValueError("R2 released split is not exactly 54 TRAIN / 27 TEST identities")
    if len({row["image_sha256"] for row in r2["images"]}) != 81:
        raise ValueError("R2 image hashes are not unique")

    inputs = []
    targets = []
    crop_dir = output_root / "roi_crops"
    crop_dir.mkdir()
    rois_by_image = {}
    for roi in rois:
        rois_by_image.setdefault(roi["image_id"], []).append(roi)
    for image_id, image_rois in rois_by_image.items():
        image_row = images[image_id]
        source_path = _verify_source_row(r2_root, image_row, image_row["image_sha256"])
        mask_cache = {}
        with Image.open(source_path) as image:
            if image.mode != "RGB":
                raise ValueError(f"IDRiD source image is not RGB for {image_id}")
            for roi in image_rois:
                if roi["image_sha256"] != image_row["image_sha256"]:
                    raise ValueError(f"R2 ROI source hash differs from image inventory for {roi['roi_id']}")
                bbox = tuple(roi["bbox_xyxy_pixels"])
                if len(bbox) != 4:
                    raise ValueError(f"Invalid R2 ROI geometry for {roi['roi_id']}")
                x0, y0, x1, y1 = bbox
                out_of_bounds = (
                    x0 < 0
                    or y0 < 0
                    or x1 <= x0
                    or y1 <= y0
                    or x1 > image_row["image_size"][0]
                    or y1 > image_row["image_size"][1]
                )
                if out_of_bounds:
                    raise ValueError(f"R2 ROI geometry out of bounds for {roi['roi_id']}")
                crop_path = crop_dir / f"{roi['roi_id']}.jpg"
                image.crop((x0, y0, x1, y1)).save(crop_path, format="JPEG", quality=90, optimize=True)
                with Image.open(crop_path) as crop:
                    if crop.mode != "RGB" or crop.size != (x1 - x0, y1 - y0):
                        raise ValueError(f"R3 ROI crop geometry/mode mismatch for {roi['roi_id']}")
                split = roi["split"].upper()
                mask_evidence = _mask_evidence(r2_root, data_root, image_row, bbox, mask_cache)
                mask_coverage = (
                    "INCOMPLETE_SUPPORTED_MASK_COVERAGE"
                    if any(entry["status"] in ["MISSING", "UNANNOTATED"] for entry in mask_evidence)
                    else "COMPLETE_SUPPORTED_MASK_COVERAGE"
                )
                input_row = R3ROIInput.model_validate(
                    {
                        "dataset_id": "idrid_v1",
                        "source_type": "PUBLIC_IDRID",
                        "roi_id": roi["roi_id"],
                        "source_image_id": roi["image_id"],
                        "source_image_sha256": roi["image_sha256"],
                        "source_image_relative_uri": _relative_uri(source_path, data_root),
                        "roi_image_sha256": _sha256(crop_path),
                        "roi_image_relative_uri": _relative_uri(crop_path, data_root),
                        "source_width_px": image_row["image_size"][0],
                        "source_height_px": image_row["image_size"][1],
                        "roi_width_px": x1 - x0,
                        "roi_height_px": y1 - y0,
                        "released_split": split,
                        "roi_class": roi["class"],
                        "roi_provenance": "IDRID_MASK_FOREGROUND_BBOX",
                        "mask_coverage": mask_coverage,
                        "mask_evidence": mask_evidence,
                        "geometry": {
                            "bbox_xyxy_px": list(bbox),
                            "bbox_xyxy_norm": roi["bbox_xyxy_normalized"],
                            "provenance": "IDRID_EXACT_MASK_FOREGROUND_BBOX",
                        },
                    }
                )
                target_row = R3ROITarget.model_validate(
                    {
                        "dataset_id": "idrid_v1",
                        "roi_id": roi["roi_id"],
                        "source_image_id": roi["image_id"],
                        "source_image_sha256": roi["image_sha256"],
                        "released_split": split,
                        "target_semantic": "SUPPORTED_LESION",
                        "target_class": roi["class"],
                    }
                )
                inputs.append(input_row)
                targets.append(target_row)

    summary = validate_r3_manifests(inputs, targets)
    if {row.roi_id for row in inputs} != {row["roi_id"] for row in rois}:
        raise ValueError("R3 manifest does not preserve the complete R2 ROI identity set")
    input_path = output_root / "r3_inputs.jsonl"
    target_path = output_root / "r3_targets.jsonl"
    write_records(input_path, inputs)
    write_records(target_path, targets)
    build = {
        "status": "PASS",
        "dataset_id": "idrid_v1",
        "source_provenance": source_audit["source_provenance"],
        "r2_manifest": str(r2_manifest_path),
        "r2_source_root": str(r2_root),
        "data_root": str(data_root.resolve()),
        "r2_image_count": len(images),
        "r2_train_image_count": len(train_images),
        "r2_test_image_count": len(test_images),
        "r2_roi_count": len(rois),
        "r3_input_count": len(inputs),
        "r3_target_count": len(targets),
        "r3_summary": summary,
        "supported_classes": list(SUPPORTED_LESION_CLASSES),
        "missing_mask_semantics": "UNKNOWN_OR_UNSUPPORTED_FINDING",
        "weak_negative_semantics": "WEAK_NEGATIVE_FOR_SUPPORTED_CLASS_ONLY_WITH_PRESENT_EMPTY_MASK",
        "negative_rows_created": 0,
        "r2_roi_ids_preserved": True,
        "source_audit": source_audit,
    }
    (output_root / "r3_manifest_build.json").write_text(json.dumps(build, indent=2), encoding="utf-8")
    return input_path, target_path, build


def _file_record(path: Path) -> dict:
    return {"path": path.name, "bytes": path.stat().st_size, "sha256": _sha256(path)}


def run_checkpoint(args):
    output_root = Path(args.out).resolve()
    data_root = Path(args.data_root).resolve()
    input_path, target_path, build = build_r3_manifests(
        Path(args.r2_manifest).resolve(), Path(args.acquisition_manifest).resolve(), output_root, data_root
    )
    train_dir = output_root / "train"
    test_dir = output_root / "test"
    train_result = train_roi_classifier(
        input_path, target_path, data_root, train_dir, str(Path(args.config).resolve())
    )
    test_result = evaluate_roi_classifier(
        input_path, target_path, data_root, train_dir / "model.npz", test_dir, split="TEST"
    )
    receipt = {
        "schema_version": "r3_idrid_execution_receipt.v0.1",
        "status": "PASS_WITH_WARNINGS",
        "outcome": "R3_ENGINEERING_EVIDENCE_COMPLETE",
        "lane": "R3_IDRID_ROI",
        "execution_host": "LOCAL_CPU",
        "model_type": "R3_MASKED_LINEAR_RGB_BASELINE",
        "dataset_id": "idrid_v1",
        "train_split": "TRAIN",
        "evaluation_split": "TEST",
        "build": build,
        "train": train_result,
        "evaluation": test_result,
        "scientific_result_eligible": False,
        "claims_permitted": ["ENGINEERING_PIPELINE_EXECUTION_ONLY"],
        "claims_forbidden": ["SCIENTIFIC_ELIGIBILITY", "CHAMPION", "CLINICAL_UTILITY", "LESION_LOCALIZATION"],
        "mlflow_dagshub": "REUSED_PRIOR_READ_ONLY_PROBE_HTTP_404_NO_WRITE",
        "runpod": "NOT_USED_LOCAL_NUMPY_COMPLETED",
        "estimated_cost_usd": 0,
        "warnings": [
            "R2 contains only positive mask-derived ROI rows; no negative rows were invented.",
            "Missing masks remain UNKNOWN and are excluded from supervision.",
            "The baseline is engineering evidence only and is not lesion localization.",
            "DagsHub/MLflow prior read-only probe returned HTTP 404; no write was attempted.",
            "R1-P0 remains BLOCKED by the accepted MMRDR released-split duplicate groups.",
        ],
    }
    receipt_path = output_root / "r3_execution_receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    artifact_paths = [
        output_root / "r3_inputs.jsonl",
        output_root / "r3_targets.jsonl",
        output_root / "r3_manifest_build.json",
        output_root / "train" / "run.json",
        output_root / "test" / "evaluation.json",
        receipt_path,
    ]
    manifest = {
        "schema_version": "r3_idrid_artifact_manifest.v0.1",
        "status": "PASS",
        "artifacts": [_file_record(path) for path in artifact_paths],
        "local_only_artifacts": [_file_record(output_root / "train" / "model.npz")],
    }
    (output_root / "artifact_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r2-manifest", required=True)
    parser.add_argument("--acquisition-manifest", required=True)
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    run_checkpoint(args)


if __name__ == "__main__":
    main()
