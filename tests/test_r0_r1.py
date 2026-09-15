import copy
from pathlib import Path

import pytest
import torch

from eyes_detected.mil.global_average import GlobalAveragePooling
from scripts.validate_r0_r1 import load_json, validate_freeze, validate_r1


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


def test_r1_freeze_requires_provider_neutral_storage():
    config = load_json(ROOT / "eyes-detected-models/configs/research/r1-global-b1.json")
    validate_r1(config, ROOT)
    mutated = copy.deepcopy(config)
    mutated["storage_roots"]["provider_required"] = True
    with pytest.raises(ValueError, match="RunPod must remain optional"):
        validate_r1(mutated, ROOT)
