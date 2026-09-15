import json
from pathlib import Path
import pytest
import jsonschema
from eyes_contracts.models import (
    ImageManifest,
    Geometry,
    LabelScope,
    BinaryAssessment,
    DatasetManifest,
    DRPrediction,
    Candidate,
    Prediction,
)
from eyes_contracts.validators import validate, check_splits, write_records, read_records
from eyes_contracts.protocol import load_protocol, check_protocol


def test_unknown_version():
    with pytest.raises(ValueError):
        validate({"schema_version": "prediction.v9"})


@pytest.mark.parametrize(
    "updates",
    [
        {"width_px": 0},
        {"laterality": "LEFT"},
        {"patient_name": "PRIVATE"},
        {"relative_uri": "../secret"},
        {"relative_uri": "https://example.com/image"},
        {"source_type": "LOCAL_PRIVATE", "cloud_eligible": True},
        {"file_sha256": "bad"},
    ],
)
def test_image_rejects(image, updates):
    with pytest.raises(ValueError):
        ImageManifest.model_validate(image.model_dump() | updates)


@pytest.mark.parametrize(
    "geometry",
    [
        {"type": "point", "coordinates_norm": [0.1]},
        {"type": "point", "coordinates_norm": [1.1, 0]},
        {"type": "point", "coordinates_norm": [float("nan"), 0]},
        {"type": "box", "coordinates_norm": [0.5, 0.5, 0.1, 0.1]},
        {"type": "polygon", "coordinates_norm": [0, 0, 0.5, 0.5, 1, 1]},
        {"type": "mask", "mask_size": [2, 2], "mask_rle": [2]},
    ],
)
def test_bad_geometry(geometry):
    with pytest.raises(ValueError):
        Geometry.model_validate(geometry)


def test_weak_label_not_pixel_gt():
    with pytest.raises(ValueError):
        LabelScope(dr_grade="IMAGE_LEVEL_ORDINAL", lesions="IMAGE_LEVEL_MULTILABEL", pixel_masks=True)


def test_binary_not_ordinal(image):
    im = ImageManifest.model_validate(image.model_dump() | {"binary_assessment": {"value": "DR"}})
    assert im.binary_assessment.ordinal_grade_available is False
    with pytest.raises(ValueError):
        BinaryAssessment(value="DR", dr_grade=1)


def test_binary_no_dr_not_grade_zero(image):
    im = ImageManifest.model_validate(image.model_dump() | {"binary_assessment": {"value": "NO_DR"}})
    assert not hasattr(im.binary_assessment, "dr_grade")


def test_mmrdr_localized_rejected():
    with pytest.raises(ValueError):
        DatasetManifest(
            dataset_id="mmrdr_uwf",
            modality=["UWF"],
            source_type="PUBLIC",
            label_scope={"dr_grade": "IMAGE_LEVEL_ORDINAL", "lesions": "LOCALIZED", "pixel_masks": True},
            split_unit="PATIENT",
            license_status="NOT_REVIEWED",
            data_root_env="MMRDR_ROOT",
        )


@pytest.mark.parametrize("field", ["patient_pseudo_id", "eye_id", "visit_id", "file_sha256"])
def test_split_leakage(image, field):
    a = image.model_dump()
    a[field] = "a" * 64 if field == "file_sha256" else "SAME"
    b = a | {"image_id": "SYNTH_002", "split": "SENTINEL"}
    with pytest.raises(ValueError):
        check_splits([ImageManifest.model_validate(a), ImageManifest.model_validate(b)])


def test_duplicate_image(image):
    with pytest.raises(ValueError):
        check_splits([image, image])


def test_prediction_roundtrip(prediction, tmp_path):
    write_records(tmp_path / "pred.jsonl", [prediction])
    assert read_records(tmp_path / "pred.jsonl")[0] == prediction


@pytest.mark.parametrize(
    "p,g", [([0.9, 0.8, 0.2, 0.1], 2), ([0.4, 0.3, 0.2, 0.1], 0), ([0.9, 0.8, 0.7, 0.6], 4)]
)
def test_ordinal_contract(p, g, protocol):
    assert DRPrediction(grade=g, ordinal_probs=p, confidence=0.5, grading_protocol=protocol).grade == g


def test_nonmonotone(protocol):
    with pytest.raises(ValueError):
        DRPrediction(grade=2, ordinal_probs=[0.9, 0.2, 0.8, 0.1], confidence=0.5, grading_protocol=protocol)


def test_attention_cannot_be_geometry():
    with pytest.raises(ValueError):
        Geometry(type="mil_attention", coordinates_norm=[0.1, 0.2])


def test_manual_first_nv():
    with pytest.raises(ValueError):
        Candidate(
            object_id="O",
            label="nvd",
            geometry={"type": "polygon", "coordinates_norm": [0, 0, 1, 0, 1, 1]},
            confidence=0.5,
            generator_kind="LOCALIZER",
        )


def test_dme_extra_forbidden(prediction):
    with pytest.raises(ValueError):
        Prediction.model_validate(prediction.model_dump() | {"dme_ground_truth": True})


def test_protocol_hash_and_change(tmp_path, protocol):
    root = Path(__file__).resolve().parents[2]
    path = root / "eyes-detected-contracts/protocols/ico_2017_dr.v0.1.json"
    data, ref = load_protocol(path)
    assert ref == protocol
    assert data["severe_reference"]["hemorrhages_per_quadrant_at_least"] == 20
    data["version"] = "0.2.0"
    p = tmp_path / "p.json"
    p.write_text(json.dumps(data))
    _, ref2 = load_protocol(p)
    assert ref2.config_sha256 != ref.config_sha256
    record = DRPrediction(grade=0, ordinal_probs=[0.4, 0.3, 0.2, 0.1], confidence=0.6, grading_protocol=ref)
    with pytest.raises(ValueError):
        check_protocol(record, ref2)


def test_generated_schemas(image, prediction):
    root = Path(__file__).resolve().parents[1] / "schemas"
    for record in [image, prediction]:
        schema = json.loads((root / (record.schema_version + ".schema.json")).read_text())
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.validate(record.model_dump(mode="json"), schema)
        bad = record.model_dump(mode="json") | {"unexpected": "bad"}
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(bad, schema)
