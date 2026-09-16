import copy
from pathlib import Path

import pytest
import torch

from eyes_detected.mil.global_average import GlobalAveragePooling
from scripts.validate_r0_r1 import load_json, validate_freeze, validate_r1, validate_r1_p0


ROOT = Path(__file__).resolve().parents[1]


def test_global_average_pooling_uses_only_valid_patches():
    pooling = GlobalAveragePooling(2)
    features = torch.tensor([[[2.0, 4.0], [6.0, 8.0], [100.0, 100.0]]])
    result = pooling(features, torch.tensor([[True, True, False]]))
    assert torch.equal(result["embedding"], torch.tensor([[4.0, 6.0]]))


def test_r0_freeze_rejects_unannotated_negative_policy():
    freeze = load_json(ROOT / "docs/RSC_R0_DATASET_TAXONOMY_FREEZE_v0.1.json")
    validate_freeze(freeze)
    mutated = copy.deepcopy(freeze)
    mutated["negative_roi_policy"]["unannotated_roi_is_true_negative"] = True
    with pytest.raises(ValueError, match="automatic true negative"):
        validate_freeze(mutated)


def test_r0_freeze_requires_explicit_supervision_fields():
    freeze = load_json(ROOT / "docs/RSC_R0_DATASET_TAXONOMY_FREEZE_v0.1.json")
    mutated = copy.deepcopy(freeze)
    del mutated["candidate_datasets"][0]["lesion_supervision"]
    with pytest.raises(ValueError, match="supervision audit fields"):
        validate_freeze(mutated)


def test_r0_freeze_records_pass_and_reclassifies_acquisition_checks():
    freeze = load_json(ROOT / "docs/RSC_R0_DATASET_TAXONOMY_FREEZE_v0.1.json")
    assert freeze["status"] == "R0_V3=PASS"
    assert freeze["r0_taxonomy_status"] == "R0_DATASET_TAXONOMY=PASS"
    assert freeze["r1_p0_status"] == "R1_P0_ACQUISITION_PREFLIGHT=READY_NOT_EXECUTED"
    assert freeze["reclassified_findings"]
    validate_freeze(freeze)
    mutated = copy.deepcopy(freeze)
    mutated["blockers"] = ["local hash not yet computed"]
    with pytest.raises(ValueError, match="active blockers"):
        validate_freeze(mutated)


def test_r1_p0_blocks_training_and_stays_not_executed():
    preflight = load_json(ROOT / "docs/R1_P0_ACQUISITION_PREFLIGHT.json")
    validate_r1_p0(preflight, ROOT)
    mutated = copy.deepcopy(preflight)
    mutated["training_unlock"] = "ALLOWED"
    with pytest.raises(ValueError, match="block candidate training"):
        validate_r1_p0(mutated, ROOT)


def test_r1_registry_requires_r1_p0_before_training():
    config = load_json(ROOT / "eyes-detected-models/configs/research/r1-global-benchmark.json")
    mutated = copy.deepcopy(config)
    mutated["acquisition_preflight"]["required_before_training"] = False
    with pytest.raises(ValueError, match="require R1-P0 before training"):
        validate_r1(mutated, ROOT)


def test_r1_freeze_requires_provider_neutral_storage():
    config = load_json(ROOT / "eyes-detected-models/configs/research/r1-global-benchmark.json")
    validate_r1(config, ROOT)
    mutated = copy.deepcopy(config)
    mutated["storage_roots"]["provider_required"] = True
    with pytest.raises(ValueError, match="RunPod must remain optional"):
        validate_r1(mutated, ROOT)


def test_r1_freeze_requires_all_three_v3_candidates():
    config = load_json(ROOT / "eyes-detected-models/configs/research/r1-global-benchmark.json")
    mutated = copy.deepcopy(config)
    mutated["candidates"].pop()
    with pytest.raises(ValueError, match="C0, C1, and C2"):
        validate_r1(mutated, ROOT)


def test_r1_freeze_rejects_fake_metrics_and_architecture_loss_confounding():
    config = load_json(ROOT / "eyes-detected-models/configs/research/r1-global-benchmark.json")
    mutated = copy.deepcopy(config)
    mutated["candidates"][0]["metrics_artifact_path"] = "metrics.json"
    with pytest.raises(ValueError, match="fake measured metrics"):
        validate_r1(mutated, ROOT)
    mutated = copy.deepcopy(config)
    mutated["candidates"][1]["loss"] = "CORN"
    with pytest.raises(ValueError, match="CE for every candidate"):
        validate_r1(mutated, ROOT)
