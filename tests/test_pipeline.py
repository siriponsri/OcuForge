import json
from pathlib import Path
import hashlib
import pytest
from PIL import Image
from eyes_contracts.models import ImageManifest
from eyes_contracts.validators import write_records, read_records
from eyes_detected.pipeline.data import audit, load_images, Target
from eyes_detected.pipeline.extract import extract
from eyes_detected.pipeline.train import train
from eyes_detected.pipeline.evaluate import infer

ROOT = Path(__file__).resolve().parents[1]


def prepare(root):
    images = []
    targets = []
    for i, split in enumerate(["TRAIN", "TRAIN", "VAL", "VAL", "TEST", "TEST"]):
        path = root / f"SYN_{i}.png"
        Image.new("RGB", (64, 48), (20 + i * 30, 40 + i, 60)).save(path)
        images.append(
            ImageManifest(
                image_id=f"SYN_{i}",
                dataset_id="SYNTHETIC_V1",
                file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                relative_uri=path.name,
                width_px=64,
                height_px=48,
                source_type="SYNTHETIC",
                split=split,
                patient_pseudo_id=f"P_{i}",
            )
        )
        targets.append({"image_id": f"SYN_{i}", "source": "SYNTHETIC", "dr_grade": i % 5})
    write_records(root / "images.jsonl", images)
    (root / "targets.jsonl").write_text(
        "".join(json.dumps(t) + "\n" for t in targets), encoding="utf-8"
    )
    (root / "train.json").write_text(
        json.dumps(
            {
                "task": "ordinal",
                "device": "cpu",
                "epochs": 2,
                "batch_size": 2,
                "seed": 42,
                "loss_weights": {"primary": 1, "lesions": 0, "qc": 0},
            }
        ),
        encoding="utf-8",
    )
    return root / "images.jsonl"


def test_synthetic_extract_train_resume_evaluate(tmp_path):
    manifest = prepare(tmp_path)
    assert audit(manifest, tmp_path, tmp_path / "audit.json")["failures"] == 0
    extract(
        manifest,
        tmp_path,
        tmp_path / "features",
        ROOT / "eyes-detected-models/configs/pipeline/extract-tiny.json",
    )
    args = [
        manifest,
        tmp_path / "targets.jsonl",
        tmp_path / "features",
        tmp_path / "run",
        tmp_path / "train.json",
        ROOT / "eyes-detected-contracts/protocols/ico_2017_dr.v0.1.json",
    ]
    result = train(*args)
    assert result["status"] == "COMPLETED"
    assert len(result["train_ids"]) == 2 and len(result["val_ids"]) == 2
    assert train(*args, resume=tmp_path / "run/last.pt")["epochs_completed"] == 2
    report = infer(
        manifest,
        tmp_path / "features",
        tmp_path / "run/best.pt",
        tmp_path / "eval",
        "TEST",
        tmp_path / "targets.jsonl",
    )
    assert report["n"] == 2 and report["labeled_n"] == 2 and report["scientific_result_eligible"] is False
    predictions = read_records(tmp_path / "eval/predictions.jsonl")
    model_manifest = read_records(tmp_path / "eval/model_manifest.json")[0]
    assert all(p.model_manifest_id == model_manifest.model_manifest_id for p in predictions)
    assert all(p.dr is not None and not p.objects and p.evidence for p in predictions)
    # Corrupted feature provenance must refuse inference.
    index = tmp_path / "features/index.json"
    rows = json.loads(index.read_text(encoding="utf-8"))
    rows[-1]["metadata"]["image_sha256"] = "f" * 64
    index.write_text(json.dumps(rows), encoding="utf-8")
    with pytest.raises(ValueError, match="provenance"):
        infer(manifest, tmp_path / "features", tmp_path / "run/best.pt", tmp_path / "bad", "TEST")


def test_binary_experience_cannot_be_ordinal():
    with pytest.raises(ValueError):
        Target(image_id="IMG_1", source="DOCTOR_EXPERIENCE", dr_grade=2)
    with pytest.raises(ValueError):
        Target(image_id="IMG_1", source="DOCTOR_EXPERIENCE", binary_dr=1, lesions=[0] * 7)
    assert Target(image_id="IMG_1", source="DOCTOR_EXPERIENCE", binary_dr=1).dr_grade is None


def test_cloud_zone_cannot_skip_manifest_gate(tmp_path, monkeypatch):
    manifest = prepare(tmp_path)
    monkeypatch.setenv("OCUFORGE_EXECUTION_ZONE", "PUBLIC_CLOUD")
    with pytest.raises(ValueError, match="Cloud requires"):
        load_images(manifest)


def test_binary_pipeline_keeps_scores_out_of_ordinal_contract(tmp_path):
    manifest = prepare(tmp_path)
    targets = [{"image_id": f"SYN_{i}", "source": "SYNTHETIC", "binary_dr": i % 2} for i in range(6)]
    (tmp_path / "targets.jsonl").write_text(
        "".join(json.dumps(t) + "\n" for t in targets), encoding="utf-8"
    )
    cfg = json.loads((tmp_path / "train.json").read_text(encoding="utf-8"))
    cfg["task"] = "binary"
    (tmp_path / "train.json").write_text(json.dumps(cfg), encoding="utf-8")
    extract(
        manifest,
        tmp_path,
        tmp_path / "features",
        ROOT / "eyes-detected-models/configs/pipeline/extract-tiny.json",
    )
    train(
        manifest,
        tmp_path / "targets.jsonl",
        tmp_path / "features",
        tmp_path / "run",
        tmp_path / "train.json",
        ROOT / "eyes-detected-contracts/protocols/ico_2017_dr.v0.1.json",
    )
    report = infer(
        manifest,
        tmp_path / "features",
        tmp_path / "run/best.pt",
        tmp_path / "eval",
        "TEST",
        tmp_path / "targets.jsonl",
    )
    assert report["task"] == "binary" and len(report["confusion_matrix"]) == 2
    assert all(p.dr is None for p in read_records(tmp_path / "eval/predictions.jsonl"))
    assert all(
        0 <= r["binary_dr_probability"] <= 1
        for r in json.loads((tmp_path / "eval/scores.json").read_text(encoding="utf-8"))
    )
