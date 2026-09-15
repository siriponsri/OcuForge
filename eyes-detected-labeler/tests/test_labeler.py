import numpy as np
import pytest
from eyes_contracts.models import Annotation, Geometry, AnnotationBatch
from eyes_contracts.validators import training_annotations, validate_batch, write_records, read_records
from labeler_bridge.geometry.convert import from_cvat, to_cvat, rle_encode, rle_decode
from labeler_bridge.import_predictions.bridge import import_prediction
from labeler_bridge.export_annotations.bridge import export_annotations, session_summary
from labeler_bridge.provenance.lifecycle import transition
from labeler_bridge.cvat_client.client import CVATClient


@pytest.mark.parametrize(
    "g",
    [
        {"type": "point", "coordinates_norm": [0.25, 0.75]},
        {"type": "box", "coordinates_norm": [0.1, 0.2, 0.7, 0.8]},
        {"type": "polygon", "coordinates_norm": [0.1, 0.1, 0.8, 0.1, 0.5, 0.8]},
        {"type": "polyline", "coordinates_norm": [0.1, 0.1, 0.8, 0.2]},
        {"type": "ellipse", "coordinates_norm": [0.1, 0.2, 0.7, 0.8]},
        {"type": "image_presence"},
    ],
)
def test_geometry_roundtrip(g):
    geom = Geometry(**g)
    result = from_cvat(to_cvat(geom, 80, 48), 80, 48)
    assert result.type == geom.type
    assert np.allclose(result.coordinates_norm, geom.coordinates_norm)


def test_mask_roundtrip():
    mask = np.zeros((48, 80), np.uint8)
    mask[4:10, 8:20] = 1
    g = Geometry(type="mask", mask_size=(48, 80), mask_rle=rle_encode(mask))
    b = from_cvat(to_cvat(g, 80, 48), 80, 48)
    assert np.array_equal(rle_decode(b.mask_rle, b.mask_size), mask)


def test_cropped_mask():
    raw = {"type": "mask", "points": [0, 4, 1, 2, 2, 3]}
    g = from_cvat(raw, 10, 10)
    assert rle_decode(g.mask_rle, g.mask_size)[2:4, 1:3].sum() == 4


@pytest.mark.parametrize(
    "raw", [{"type": "points", "points": [99, 1]}, {"type": "mask", "points": [4, 0, 0, 10, 10]}]
)
def test_outside_geometry(raw):
    with pytest.raises(ValueError):
        from_cvat(raw, 10, 10)


def test_provenance_lifecycle(image, prediction, tmp_path):
    payload, sidecar = import_prediction(prediction, image)
    aid = next(iter(sidecar))
    a = Annotation.model_validate(sidecar[aid])
    assert a.origin == "AI_SUGGESTED"
    with pytest.raises(ValueError):
        training_annotations([a], [image])
    corrected = transition(
        a, "CORRECT", "REVIEWER", geometry={"type": "point", "coordinates_norm": [0.5, 0.6]}
    )
    assert corrected.parent_prediction_id == prediction.prediction_id and len(corrected.history) == 2
    with pytest.raises(ValueError):
        training_annotations([corrected], [image])
    assert training_annotations([corrected], [image], True)
    final = transition(transition(corrected, "ADJUDICATE", "EXPERT"), "LOCK", "EXPERT")
    assert len(final.history) == 4
    assert training_annotations([final], [image])
    write_records(tmp_path / "ann.jsonl", [final])
    assert read_records(tmp_path / "ann.jsonl")[0] == final
    with pytest.raises(ValueError):
        transition(final, "CORRECT", "X")
    with pytest.raises(ValueError):
        training_annotations([final], [image.model_copy(update={"split": "SENTINEL"})])


def test_export_requires_explicit_actions(image, prediction):
    payload, sidecar = import_prediction(prediction, image)
    aid = next(iter(sidecar))
    args = [payload, sidecar, {0: image}, {1: "microaneurysm"}, {1: "ed_annotation_id"}, "REVIEWER"]
    untouched = export_annotations(*args, {})[0]
    assert untouched.origin == "AI_SUGGESTED"
    payload["shapes"][0]["points"][0] += 1
    with pytest.raises(ValueError):
        export_annotations(*args, {})
    a = export_annotations(*args, {aid: "CORRECT"})[0]
    assert a.origin == "CLINICIAN_CORRECTED"
    payload["shapes"] = []
    with pytest.raises(ValueError):
        export_annotations(*args, {})
    assert export_annotations(*args, {aid: "REJECT"})[0].review_status == "REJECTED"


def test_manual_add(image):
    payload = {
        "shapes": [{"id": 7, "type": "points", "points": [2, 3], "frame": 0, "label_id": 1, "attributes": []}]
    }
    a = export_annotations(payload, {}, {0: image}, {1: "microaneurysm"}, {}, "REVIEWER", {"new:7": "ADD"})[0]
    assert a.origin == "CLINICIAN_ADDED" and a.parent_prediction_id is None
    assert transition(a, "SUBMIT", "REVIEWER").review_status == "SUBMITTED"


def test_missing_provenance(image, prediction):
    _, s = import_prediction(prediction, image)
    a = next(iter(s.values()))
    a.pop("origin")
    with pytest.raises(ValueError):
        Annotation.model_validate(a)


def test_batch_forgery(image):
    batch = AnnotationBatch(
        batch_id="B",
        dataset_id=image.dataset_id,
        selection={"strategy": "DIVERSITY", "model_manifest_id": "M"},
        requested_n=1,
        items=[{"image_id": image.image_id, "priority": 1, "reasons": ["DIVERSITY"], "split": "TRAIN"}],
    )
    with pytest.raises(ValueError):
        validate_batch(batch, [image.model_copy(update={"split": "SENTINEL"})])


def test_cvat_failure(monkeypatch):
    client = CVATClient()
    with pytest.raises(RuntimeError):
        client.health()
    with pytest.raises(ValueError):
        CVATClient("https://example.com")


def test_summary(image, prediction):
    _, s = import_prediction(prediction, image)
    a = transition(Annotation.model_validate(next(iter(s.values()))), "CONFIRM", "R")
    summary = session_summary([a], 60)
    assert summary["ai_objects_confirmed"] == 1 and summary["acceptance_rate"] == 1


def test_ico_grade_tag_export(image, protocol):
    payload = {"tags": [{"id": 9, "frame": 0, "label_id": 5, "attributes": [{"spec_id": 8, "value": "3"}]}]}
    a = export_annotations(
        payload,
        {},
        {0: image},
        {5: "dr_grade"},
        {8: "dr_grade"},
        "REVIEWER",
        {"new:9": "ADD"},
        grading_protocol=protocol,
    )[0]
    assert a.dr_grade == 3 and a.grading_protocol == protocol
    with pytest.raises(ValueError):
        export_annotations(
            payload, {}, {0: image}, {5: "dr_grade"}, {8: "dr_grade"}, "REVIEWER", {"new:9": "ADD"}
        )


def test_cvat_transport_fixture(monkeypatch):
    from labeler_bridge.cvat_client import client as module

    calls = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return b'{"id":12}'

    class Opener:
        def open(self, request, timeout):
            calls.append((request, timeout))
            return Response()

    monkeypatch.setattr(module, "build_opener", lambda *args: Opener())
    c = CVATClient(token="synthetic-value")
    assert c.create_project({"name": "SYNTHETIC", "labels": []})["id"] == 12
    assert calls[0][0].get_method() == "POST"
    c.import_annotations(12, {"version": 0, "shapes": [], "tracks": [], "tags": []})
    assert calls[-1][0].get_method() == "PATCH" and "action=create" in calls[-1][0].full_url


def test_history_retains_original_geometry(image, prediction):
    _, sidecar = import_prediction(prediction, image)
    a = Annotation.model_validate(next(iter(sidecar.values())))
    corrected = transition(
        a, "CORRECT", "REVIEWER", geometry={"type": "point", "coordinates_norm": [0.8, 0.9]}
    )
    assert corrected.history[0].geometry_snapshot.coordinates_norm == [0.4, 0.6]
    assert corrected.history[1].geometry_snapshot.coordinates_norm == [0.8, 0.9]
    with pytest.raises(ValueError):
        rle_encode([[256]])
