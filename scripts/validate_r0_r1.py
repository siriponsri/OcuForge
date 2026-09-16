"""Validate the checked-in R0 pre-execution and R1 benchmark contracts."""

import json
from pathlib import Path
from pathlib import PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "docs/RSC_R0_DATASET_TAXONOMY_FREEZE_v0.1.json"
R1 = ROOT / "eyes-detected-models/configs/research/r1-global-benchmark.json"
REQUIRED_ROI = {
    "MICROANEURYSM",
    "INTRARETINAL_HEMORRHAGE",
    "HARD_EXUDATE",
    "SOFT_EXUDATE",
    "NO_SUPPORTED_LESION_IN_ROI",
}
STORAGE_ENVS = {
    "data_env": "OCUFORGE_DATA_ROOT",
    "model_env": "OCUFORGE_MODEL_ROOT",
    "cache_env": "OCUFORGE_CACHE_ROOT",
    "artifact_env": "OCUFORGE_ARTIFACT_ROOT",
}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def relative_path(value):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ValueError("R1 storage paths must be relative POSIX strings")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("R1 storage paths must stay below configured roots")
    return value


def validate_freeze(data):
    if data.get("status") != "R0_V2=READY_TO_EXECUTE":
        raise ValueError("R0 V2 must be ready to execute, not marked passed")
    selected = {row["role"]: row for row in data.get("candidate_datasets", [])}
    required_fields = {
        "source",
        "version_or_revision",
        "access_status",
        "license_status",
        "modality",
        "image_count",
        "patient_id_available",
        "eye_id_available",
        "image_id_available",
        "global_labels",
        "ordinal_labels",
        "lesion_labels",
        "lesion_supervision",
        "split_source",
        "known_limitations",
        "checksum_or_source_hash",
        "limitations",
    }
    if any(not required_fields.issubset(row) for row in selected.values()):
        raise ValueError("R0 candidate dataset records are missing supervision audit fields")
    valid_supervision_types = {"image_level", "point", "box", "polygon", "mask", "none"}
    if any(
        row["lesion_supervision"].get("type") not in valid_supervision_types
        for row in selected.values()
    ):
        raise ValueError("R0 lesion supervision type is not explicit")
    if selected.get("GLOBAL_DR", {}).get("dataset_id") != "mmrdr_uwf_v1":
        raise ValueError("R0 candidate global dataset must be MMRDR UWF")
    if selected.get("ROI_LESION_CLASSIFIER", {}).get("dataset_id") != "idrid_v1":
        raise ValueError("R0 candidate ROI dataset must be IDRiD")
    if not selected["GLOBAL_DR"].get("cloud_eligible"):
        raise ValueError("R0 candidate global dataset must be public-cloud eligible")
    if selected["ROI_LESION_CLASSIFIER"].get("cloud_eligible"):
        raise ValueError("R0 candidate ROI dataset is not cleared for public cloud")
    if set(data["taxonomy"]["roi_classifier"]["admitted"]) != REQUIRED_ROI:
        raise ValueError("R0 ROI taxonomy changed without updating the gate")
    if "OPTIC_DISC" in set(data["taxonomy"]["global_image_level_presence"]):
        raise ValueError("Optic disc is not a lesion taxonomy class")
    no_lesion = data["taxonomy"]["no_lesion_semantics"]
    if no_lesion.get("canonical_label") != "NO_SUPPORTED_LESION_IN_ROI":
        raise ValueError("Missing frozen no-lesion semantic")
    if data["negative_roi_policy"].get("unannotated_roi_is_true_negative"):
        raise ValueError("Unannotated ROI cannot be an automatic true negative")
    split = data["split_policy"]
    if not split.get("split_before_roi_generation") or split.get("derived_patch_random_split"):
        raise ValueError("R0 split policy permits leakage")
    metrics = data["metrics"]
    for key in ["QWK for genuine ordinal grades", "macro F1", "accuracy"]:
        if key not in metrics["global_dr"]:
            raise ValueError(f"Missing global metric: {key}")
    for key in ["macro F1", "balanced accuracy", "confusion matrix", "calibration", "inference latency"]:
        if key not in metrics["roi_lesion"]:
            raise ValueError(f"Missing ROI metric: {key}")
    return True


def validate_r1(data, root=ROOT):
    if data.get("status") != "R1_GLOBAL_BENCHMARK=READY_NOT_EXECUTED":
        raise ValueError("R1 benchmark must be ready but not executed")
    candidate_ids = [candidate["id"] for candidate in data["baseline_ladder"]]
    if candidate_ids != ["G0", "G1", "G2", "G3", "G4", "G5"]:
        raise ValueError("R1 baseline ladder must contain G0 through G5 in order")
    if data["baseline_ladder"][3]["aggregation"] != "attention_mil":
        raise ValueError("R1 G3 must be the Attention MIL candidate")
    if data["head_ablation"]["eligible_target"] != "GENUINE_ORDINAL_0_TO_4":
        raise ValueError("R1 head ablation must be limited to genuine ordinal labels")
    if set(data["head_ablation"]["heads"]) != {"CE", "CORAL"}:
        raise ValueError("R1 must compare CE and CORAL heads")
    if data["metrics"]["primary"] != "QWK":
        raise ValueError("R1 primary metric must be QWK")
    if data.get("selection_split") != "VAL" or data.get("held_out_split") != "TEST":
        raise ValueError("R1 must select on VAL and hold out TEST")
    if data["dataset"]["dataset_id"] != "mmrdr_uwf_v1":
        raise ValueError("R1 must use the frozen MMRDR global dataset")
    roots = data["storage_roots"]
    if {key: roots[key] for key in STORAGE_ENVS} != STORAGE_ENVS:
        raise ValueError("R1 storage roots must use the four OcuForge root environment variables")
    for value in roots["layout"].values():
        relative_path(value)
    if roots["provider_required"]:
        raise ValueError("RunPod must remain optional")
    gate = data["public_gpu_gate"]
    if gate["private_data_allowed"] or gate["provisioning"]:
        raise ValueError("R1 public GPU gate permits unsafe data or provisioning")
    for key in ["dataset_config", "encoder_config", "train_config", "protocol"]:
        path = root / data.get(key, data["dataset"].get(key, ""))
        if not path.is_file():
            raise ValueError(f"Missing R1 referenced file: {path.relative_to(root).as_posix()}")
    if "TinyTestEncoder" in json.dumps(data) or "/workspace/" in json.dumps(data):
        raise ValueError("R1 config must not hard-code a test encoder or provider path")
    return True


def validate(root=ROOT):
    freeze = load_json(root / FREEZE.relative_to(ROOT))
    r1 = load_json(root / R1.relative_to(ROOT))
    validate_freeze(freeze)
    validate_r1(r1, root)
    return {"r0": freeze["status"], "r1": r1["status"]}


if __name__ == "__main__":
    result = validate()
    print(f"PASS: {result['r0']}; {result['r1']}")
