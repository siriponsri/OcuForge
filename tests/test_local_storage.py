import copy
import hashlib
import mongomock
import pytest
from labeler_bridge.storage import MongoStore, ConflictError, LocalImageStore, local_mongo_uri
from labeler_bridge.workflow import Workflow
from eyes_contracts.models import AnnotationBatch, ImageManifest, Prediction
from eyes_contracts.validators import read_records


def store():
    return MongoStore(client=mongomock.MongoClient())


def test_compare_and_swap_and_backup_restore():
    s = store()
    doc = s.create("batch:X", "batch", {"status": "REGISTERED"})
    s.update(doc["key"], doc["version"], {"status": "READY"})
    with pytest.raises(ConflictError):
        s.update(doc["key"], doc["version"], {"status": "BAD"})
    restored = store()
    restored.restore_documents(s.export_documents())
    assert restored.get("batch:X")["body"]["status"] == "READY"
    with pytest.raises(ValueError, match="empty"):
        restored.restore_documents(s.export_documents())


@pytest.mark.parametrize(
    "uri",
    [
        "mongodb+srv://example.com",
        "mongodb://remote.example:27017",
        "mongodb://mongo,evil:27017",
        "https://mongo",
    ],
)
def test_remote_database_refused(uri):
    with pytest.raises(ValueError):
        local_mongo_uri(uri)


def test_image_store_hash_and_corruption(tmp_path):
    source = tmp_path / "input.png"
    source.write_bytes(b"synthetic fixture")
    h = hashlib.sha256(source.read_bytes()).hexdigest()
    s = LocalImageStore(tmp_path / "objects")
    relative = s.ingest(source, h)
    assert relative == f"{h[:2]}/{h}.png"
    destination = s.root / relative
    assert hashlib.sha256(destination.read_bytes()).hexdigest() == h
    destination_mtime = destination.stat().st_mtime_ns
    assert s.ingest(source, h) == relative
    assert destination.stat().st_mtime_ns == destination_mtime
    with pytest.raises(ValueError, match="mismatch"):
        s.ingest(source, "a" * 64)
    (s.root / relative).write_bytes(b"corrupted")
    with pytest.raises(ValueError, match="corrupted"):
        s.ingest(source, h)


@pytest.mark.parametrize("extension", [".bmp", ".txt"])
def test_image_store_rejects_unsupported_extension(tmp_path, extension):
    source = tmp_path / f"input{extension}"
    source.write_bytes(b"synthetic fixture")
    expected_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()

    with pytest.raises(ValueError, match="Unsupported image extension"):
        LocalImageStore(tmp_path / "objects").ingest(source, expected_sha256)


def test_image_store_rejects_hash_path_traversal(tmp_path):
    source = tmp_path / "input.png"
    source.write_bytes(b"synthetic fixture")

    with pytest.raises(ValueError, match="Expected SHA256"):
        LocalImageStore(tmp_path / "objects").ingest(source, "../" + "a" * 61)


class FakeCVAT:
    def __init__(self, image):
        self.image = image
        self.shapes = []
        self.creates = 0
        self.labels = [
            {"name": "microaneurysm", "id": 1, "attributes": [{"name": "ed_annotation_id", "id": 1}]}
        ]

    def create_task(self, name, project_id):
        self.creates += 1
        return {"id": 7}

    def request(self, method, path, data=None):
        if path.endswith("/data") and method == "POST":
            return {"rq_id": "rq:7"}
        if path.startswith("/api/requests/"):
            return {"status": "finished"}
        if path.endswith("/data/meta"):
            return {
                "frames": [
                    {
                        "name": self.image.relative_uri,
                        "width": self.image.width_px,
                        "height": self.image.height_px,
                    }
                ]
            }
        if path.startswith("/api/labels?"):
            return {"results": self.labels, "next": None}
        raise AssertionError(path)

    def get_annotations(self, task_id):
        return {"version": 0, "shapes": copy.deepcopy(self.shapes), "tags": [], "tracks": []}

    def import_annotations(self, task_id, payload):
        for shape in payload["shapes"]:
            self.shapes.append(shape | {"id": len(self.shapes) + 1})


def test_durable_workflow_retry_and_locked_revisions(tmp_path, image, prediction, protocol):
    root = tmp_path / "share"
    source = root / image.relative_uri
    source.parent.mkdir(parents=True)
    source.write_bytes(b"synthetic content")
    im = ImageManifest.model_validate(
        image.model_dump() | {"file_sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
    )
    batch = AnnotationBatch(
        batch_id="BATCH_001",
        dataset_id=im.dataset_id,
        selection={"strategy": "manual", "model_manifest_id": "TINY_TEST"},
        requested_n=1,
        items=[{"image_id": im.image_id, "priority": 1, "reasons": ["test"], "split": "TRAIN"}],
    )
    s = store()
    c = FakeCVAT(im)
    flow = Workflow(s, c, tmp_path / "exports")
    flow.register(batch, [im], protocol, "USER_1")
    flow.create_task(batch.batch_id, 1, "USER_1")
    with pytest.raises(ValueError):
        flow.create_task(batch.batch_id, 1, "USER_1")
    assert c.creates == 1
    flow.attach_share(batch.batch_id, "USER_1", root)
    flow.sync(batch.batch_id, "USER_1")
    flow.import_predictions(batch.batch_id, [prediction], "USER_1")
    flow.import_predictions(batch.batch_id, [prediction], "USER_1")
    assert len(c.shapes) == 1
    changed = Prediction.model_validate(prediction.model_dump() | {"model_manifest_id": "OTHER"})
    with pytest.raises(ValueError, match="changed"):
        flow.import_predictions(batch.batch_id, [changed], "USER_1")
    aid = c.shapes[0]["attributes"][0]["value"]
    flow.export(batch.batch_id, {aid: "CONFIRM"}, "USER_1", 120)
    final = flow.finalize(batch.batch_id, "EXPERT_1")
    assert final["body"]["status"] == "LOCKED"
    annotations = read_records(final["body"]["final_path"])
    assert annotations[0].review_status == "LOCKED"
    assert annotations[0].parent_prediction_id == prediction.prediction_id
    assert s.revisions.count_documents({"annotation_id": aid}) == 2
    restored = store()
    restored.restore_documents(s.export_documents())
    assert restored.revisions.count_documents({}) == 2
    tampered = s.export_documents()
    tampered["annotation_revisions"][0]["revision_hash"] = "f" * 64
    with pytest.raises(ValueError, match="integrity"):
        store().restore_documents(tampered)
