import numpy as np
import pytest
import torch
from eyes_contracts.models import ImageManifest
from eyes_detected.tiling.grid import PatchConfig, tile, source_to_canvas, canvas_to_source
from eyes_detected.ordinal.coral import encode, CoralHead, loss, predict, class_probabilities
from eyes_detected.mil.attention import AttentionMIL
from eyes_detected.encoders.dinov3_adapter import DINOv3Adapter
from eyes_detected.features.store import NPZFeatureStore
from eyes_detected.data.splits import assign_splits
from eyes_detected.active_learning.select import select_batch
from eyes_detected.ood.prototype import PrototypeOOD
from eyes_detected.evaluation.metrics import qwk


def test_primary_patch_geometry():
    image = np.random.default_rng(1).integers(0, 255, (300, 500, 3), dtype=np.uint8)
    a, m = tile(image)
    b, n = tile(image)
    assert a.shape == (25, 224, 224, 3)
    assert np.array_equal(a, b)
    assert m == n
    for p in m["patches"]:
        x0, y0, x1, y1 = p["canvas_xyxy"]
        assert 0 <= x0 < x1 <= 1024 and 0 <= y0 < y1 <= 1024
    for point in [(0, 0), (250, 150), (500, 300)]:
        assert np.allclose(canvas_to_source(*source_to_canvas(*point, m), m), point)
    coverage = np.zeros((1024, 1024), bool)
    for p in m["patches"]:
        x0, y0, x1, y1 = p["canvas_xyxy"]
        coverage[y0:y1, x0:x1] = True
    assert coverage.all()


def test_patch_invalid():
    with pytest.raises(ValueError):
        PatchConfig(canvas=1024, grid=2, patch=224)


def test_coral_encoding():
    assert torch.equal(
        encode(torch.arange(5)),
        torch.tensor(
            [[0, 0, 0, 0], [1, 0, 0, 0], [1, 1, 0, 0], [1, 1, 1, 0], [1, 1, 1, 1]], dtype=torch.float
        ),
    )


@pytest.mark.parametrize("g", [-1, 5])
def test_bad_grade(g):
    with pytest.raises(ValueError):
        encode(torch.tensor([g]))


def test_coral_monotonic_and_backprop():
    head = CoralHead(8)
    logits = head(torch.randn(5, 8))
    loss(logits, torch.arange(5)).backward()
    grade, p = predict(logits)
    assert torch.all(p[:, 1:] <= p[:, :-1])
    assert torch.allclose(class_probabilities(p).sum(1), torch.ones(5))
    assert head.gaps.grad is not None


def test_mil_mask_forward_backward():
    m = AttentionMIL(8)
    x = torch.randn(2, 5, 8, requires_grad=True)
    mask = torch.tensor([[True, True, False, False, False], [True] * 5])
    r = m(x, mask)
    assert torch.allclose(r["attention"].sum(1), torch.ones(2))
    assert (r["attention"][0, 2:] == 0).all()
    loss(r["dr_logits"], torch.tensor([0, 4])).backward()
    assert torch.isfinite(x.grad).all()
    assert (x.grad[0, 2:] == 0).all()
    with pytest.raises(ValueError):
        m(x, torch.zeros((2, 5), dtype=torch.bool))


def test_dino_unavailable(tmp_path):
    with pytest.raises(RuntimeError, match="no TinyTestEncoder fallback"):
        DINOv3Adapter(tmp_path, tmp_path / "missing.pth", "0" * 64, True)
    with pytest.raises(RuntimeError, match="license"):
        DINOv3Adapter(tmp_path, tmp_path / "missing", "0" * 64)


def test_dino_hash_failure(tmp_path):
    (tmp_path / "hubconf.py").write_text("# test only", encoding="utf-8")
    (tmp_path / "weights").write_bytes(b"not model")
    with pytest.raises(RuntimeError, match="SHA256 mismatch"):
        DINOv3Adapter(tmp_path, tmp_path / "weights", "0" * 64, True)


def test_feature_store(tmp_path):
    f = np.zeros((25, 8), np.float32)
    meta = {
        "dataset_id": "S",
        "image_id": "I",
        "encoder_id": "TINY",
        "encoder_weight_hash": "a" * 64,
        "preprocessing_config_hash": "b" * 64,
        "patch_geometry": {"mean": (0, 0, 0)},
        "tensor_shape": [25, 8],
        "feature_dtype": "float32",
        "extraction_time": "2026-09-09",
        "git_sha": "test",
        "docker_image": "none",
    }
    s = NPZFeatureStore(tmp_path)
    key = s.put(f, meta)
    assert np.array_equal(s.get(key, meta), f)
    with pytest.raises(ValueError):
        s.get(key, meta | {"encoder_weight_hash": "c" * 64})
    with pytest.raises(ValueError):
        s.put(f, {})


def test_group_split(image):
    data = [
        ImageManifest.model_validate(
            image.model_dump()
            | {
                "image_id": f"I{i}",
                "file_sha256": f"{i:064x}",
                "patient_pseudo_id": f"P{i // 2}",
                "split": "UNASSIGNED",
            }
        )
        for i in range(10)
    ]
    a, meta = assign_splits(data)
    b, _ = assign_splits(list(reversed(data)))
    assert {i.image_id: i.split for i in a} == {i.image_id: i.split for i in b}
    assert not meta["leakage_risk"]
    for i in range(0, 10, 2):
        assert a[i].split == a[i + 1].split
    with pytest.raises(ValueError):
        assign_splits(a)


def test_al_excludes_sentinel(image):
    images = [
        ImageManifest.model_validate(
            image.model_dump()
            | {
                "image_id": f"I{i}",
                "file_sha256": f"{i:064x}",
                "split": "SENTINEL" if i == 3 else "TRAIN",
                "site_id": f"S{i % 2}",
            }
        )
        for i in range(4)
    ]
    batch = select_batch(images, np.eye(4), 3)
    assert all(x.image_id != "I3" for x in batch.items)
    with pytest.raises(ValueError):
        select_batch(images, np.eye(4), 4)


def test_ood():
    assert PrototypeOOD([[0, 0]], 1).score([[2, 0]])[0]["abstain_recommended"]


def test_qwk():
    assert qwk([0, 1, 2, 3, 4], [0, 1, 2, 3, 4]) == 1
    assert qwk([0, 1, 2, 3, 4], [4, 3, 2, 1, 0]) < 0
    assert qwk([0, 0], [0, 0]) is None
