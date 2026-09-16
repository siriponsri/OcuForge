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
    status = data.get("status")
    if status not in {"R0_V3=PASS", "R0_DATASET_TAXONOMY=BLOCKED"}:
        raise ValueError("R0 V3 must be PASS or explicitly BLOCKED")
    if data.get("authority") != "docs/POC_MASTER_PLAN.md and docs/R0_DATASET_SUPERVISION_FREEZE.md":
        raise ValueError("R0 audit must name the V3 authority")
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
    valid_supervision_types = {"image_level", "point", "box", "polygon", "mask", "none", "unknown"}
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
    overlap = data.get("foundation_model_overlap_audit")
    if not isinstance(overlap, list) or {row.get("candidate_id") for row in overlap} != {"C1", "C2"}:
        raise ValueError("R0 must audit pretraining overlap for C1 and C2")
    required_overlap = {
        "candidate_id",
        "pretraining_corpus_description",
        "known_included_public_datasets",
        "overlap_status",
        "claim_consequence",
    }
    if any(not required_overlap.issubset(row) for row in overlap):
        raise ValueError("Foundation overlap audit fields are incomplete")
    if any(
        row["overlap_status"] not in ["CONFIRMED", "EXCLUDED", "UNKNOWN", "POTENTIALLY_CONTAMINATED"]
        for row in overlap
    ):
        raise ValueError("Foundation overlap status is not explicit")
    assets = data.get("model_asset_audit")
    if not isinstance(assets, list) or {row.get("candidate_id") for row in assets} != {"C0", "C1", "C2"}:
        raise ValueError("R0 must audit assets and overlap for C0, C1, and C2")
    required_asset_fields = {
        "candidate_id",
        "asset",
        "source",
        "asset_revision",
        "access_status",
        "license_status",
        "preprocessing",
        "pretraining_corpus",
        "overlap_with_r1_mmrdr",
        "overlap_status",
        "weight_sha256",
        "claim_consequence",
    }
    if any(not required_asset_fields.issubset(row) for row in assets):
        raise ValueError("Model asset audit fields are incomplete")
    if status == "R0_DATASET_TAXONOMY=BLOCKED":
        blockers = data.get("blockers")
        if not isinstance(blockers, list) or not blockers:
            raise ValueError("Blocked R0 freeze must record exact blockers")
        if data.get("r1_status") != "R1_GLOBAL_BENCHMARK=READY_NOT_EXECUTED":
            raise ValueError("Blocked R0 freeze must preserve R1 readiness")
        if data.get("current_r1_champion") != "NONE":
            raise ValueError("Blocked R0 freeze cannot claim an R1 champion")
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
    if data.get("schema_version") != "r1_global_benchmark.v3.0":
        raise ValueError("R1 benchmark must use the V3 schema")
    if data.get("authority") != "docs/POC_MASTER_PLAN.md":
        raise ValueError("R1 benchmark must name the canonical V3 plan")
    candidates = data.get("candidates", [])
    candidate_ids = [candidate.get("id") for candidate in candidates]
    if candidate_ids != ["C0", "C1", "C2"]:
        raise ValueError("R1 candidate registry must contain C0, C1, and C2 in order")
    required_candidate_fields = {
        "id",
        "architecture_family",
        "backbone",
        "asset_identifier",
        "asset_revision",
        "adaptation_mode",
        "input_preprocessing_contract",
        "aggregation",
        "head",
        "loss",
        "target_type",
        "license_access",
        "execution_status",
        "metrics_artifact_path",
        "deployment_artifact_path",
    }
    if any(not required_candidate_fields.issubset(candidate) for candidate in candidates):
        raise ValueError("R1 candidate record is incomplete")
    if any(candidate["loss"] != "CE" for candidate in candidates):
        raise ValueError("Initial R1 architecture comparison must use CE for every candidate")
    if any(candidate["metrics_artifact_path"] is not None for candidate in candidates):
        raise ValueError("R1 candidates must not contain fake measured metrics")
    if any(candidate["deployment_artifact_path"] is not None for candidate in candidates):
        raise ValueError("R1 candidates must not contain unmeasured deployment artifacts")
    if data["architecture_comparison"].get("current_champion") is not None:
        raise ValueError("R1 cannot claim a champion before execution")
    if data["architecture_comparison"].get("initial_candidates") != ["C0", "C1", "C2"]:
        raise ValueError("R1 architecture comparison must enumerate C0, C1, and C2")
    if data["architecture_comparison"].get("one_candidate_per_run") is not True:
        raise ValueError("R1 execution must run one candidate at a time")
    if data["winner_only_ordinal_ablation"]["eligible_target"] != "GENUINE_ORDINAL_0_TO_4":
        raise ValueError("R1 head ablation must be limited to genuine ordinal labels")
    if set(data["winner_only_ordinal_ablation"]["heads"]) != {"CE", "CORN"}:
        raise ValueError("R1 winner-only ablation must compare CE and CORN")
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
    for key in ["dataset", "candidate_training", "protocol"]:
        path = root / data["configs"].get(key, "")
        if not path.is_file():
            raise ValueError(f"Missing R1 referenced file: {path.relative_to(root).as_posix()}")
    c2_path = root / data["configs"].get("c2_encoder", "")
    if not c2_path.is_file():
        raise ValueError("Missing R1 C2 encoder configuration")
    if "TinyTestEncoder" in json.dumps(data) or "/workspace/" in json.dumps(data) or "G0" in json.dumps(data):
        raise ValueError("R1 config must not hard-code a test encoder, provider path, or old ladder")
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
