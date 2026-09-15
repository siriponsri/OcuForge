"""Durable CVAT task lifecycle. No cloud destinations and no implicit clinician decisions."""

import json
from pathlib import Path, PurePosixPath
from copy import deepcopy
from eyes_contracts.models import ImageManifest, Prediction, Annotation
from eyes_contracts.validators import validate_batch, write_records
from labeler_bridge.import_predictions.bridge import import_prediction
from labeler_bridge.export_annotations.bridge import export_annotations, session_summary
from labeler_bridge.provenance.lifecycle import transition, utcnow
from labeler_bridge.storage import document_hash


class Workflow:
    def __init__(self, store, cvat, export_root):
        self.store = store
        self.cvat = cvat
        self.root = Path(export_root)
        self.root.mkdir(parents=True, exist_ok=True)

    def register(self, batch, images, protocol, actor):
        validate_batch(batch, images)
        index = {i.image_id: i for i in images}
        selected = [index[i.image_id] for i in batch.items]
        if len({PurePosixPath(i.relative_uri).name for i in selected}) != len(selected):
            raise ValueError("CVAT frame basenames must be unique")
        key = "batch:" + batch.batch_id
        body = {
            "batch": batch.model_dump(mode="json"),
            "images": [i.model_dump(mode="json") for i in selected],
            "protocol": protocol.model_dump(mode="json"),
            "status": "REGISTERED",
            "task_id": None,
            "events": [{"action": "REGISTER", "actor": actor, "at": utcnow()}],
            "updated_at": utcnow(),
        }
        return self.store.create(key, "batch", body)

    def _save(self, doc, body, action, actor):
        body = deepcopy(body)
        body["updated_at"] = utcnow()
        body["events"].append({"action": action, "actor": actor, "at": body["updated_at"]})
        return self.store.update(doc["key"], doc["version"], body)

    def create_task(self, batch_id, project_id, actor):
        doc = self.store.get("batch:" + batch_id)
        body = doc["body"]
        if body["status"] != "REGISTERED":
            raise ValueError(
                "Task creation already attempted; inspect/attach existing task after uncertain transport failure"
            )
        body["status"] = "CREATING_TASK"
        doc = self._save(doc, body, "CREATE_TASK_INTENT", actor)
        task = self.cvat.create_task(batch_id, project_id)
        body = doc["body"]
        body["task_id"] = int(task["id"])
        body["status"] = "TASK_CREATED"
        return self._save(doc, body, "TASK_CREATED", actor)

    def attach_task(self, batch_id, task_id, actor):
        doc = self.store.get("batch:" + batch_id)
        if doc["body"]["status"] != "CREATING_TASK":
            raise ValueError("Only unresolved creation can attach a reconciled task")
        task = self.cvat.request("GET", f"/api/tasks/{int(task_id)}")
        if task["name"] != batch_id:
            raise ValueError("Reconciled task name mismatch")
        body = doc["body"]
        body["task_id"] = int(task_id)
        body["status"] = "TASK_CREATED"
        return self._save(doc, body, "TASK_RECONCILED", actor)

    def attach_share(self, batch_id, actor, share_root):
        doc = self.store.get("batch:" + batch_id)
        body = doc["body"]
        if body["status"] != "TASK_CREATED":
            raise ValueError("Task must be newly created before attaching shared files")
        files = [i["relative_uri"] for i in body["images"]]
        for f in files:
            p = PurePosixPath(f)
            if p.is_absolute() or ".." in p.parts or ":" in f:
                raise ValueError("Invalid shared path")
        import hashlib

        root = Path(share_root).resolve()
        for im in body["images"]:
            file = (root / im["relative_uri"]).resolve()
            if not file.is_relative_to(root) or not file.is_file():
                raise ValueError("CVAT share path missing or escapes root")
            h = hashlib.sha256()
            with file.open("rb") as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    h.update(chunk)
            if h.hexdigest() != im["file_sha256"]:
                raise ValueError("CVAT share image hash mismatch")
        body["status"] = "ATTACHING_DATA"
        doc = self._save(doc, body, "ATTACH_SHARE_INTENT", actor)
        result = self.cvat.request(
            "POST",
            f"/api/tasks/{body['task_id']}/data",
            {
                "server_files": files,
                "image_quality": 100,
                "sorting_method": "lexicographical",
                "use_cache": True,
                "copy_data": True,
            },
        )
        body = doc["body"]
        body["request_id"] = result.get("rq_id")
        body["status"] = "DATA_PENDING"
        return self._save(doc, body, "DATA_QUEUED", actor)

    def sync(self, batch_id, actor):
        doc = self.store.get("batch:" + batch_id)
        body = doc["body"]
        if body["status"] not in ["ATTACHING_DATA", "DATA_PENDING", "READY", "IMPORTING", "IMPORTED"]:
            raise ValueError("Task data not attached")
        if body.get("request_id"):
            from urllib.parse import quote

            request = self.cvat.request("GET", "/api/requests/" + quote(str(body["request_id"]), safe=""))
            if request["status"] == "failed":
                raise RuntimeError("CVAT data processing failed; inspect task locally")
            if request["status"] != "finished":
                return doc
        meta = self.cvat.request("GET", f"/api/tasks/{body['task_id']}/data/meta")
        frames = meta.get("frames", [])
        index = {PurePosixPath(i["relative_uri"]).name: i for i in body["images"]}
        if len(frames) != len(index):
            raise ValueError("CVAT frame count mismatch or data still processing")
        mapping = {}
        seen = set()
        for n, frame in enumerate(frames):
            name = PurePosixPath(frame["name"]).name
            if name not in index or name in seen:
                raise ValueError("Unknown or duplicate CVAT frame")
            im = index[name]
            seen.add(name)
            if frame["width"] != im["width_px"] or frame["height"] != im["height_px"]:
                raise ValueError("CVAT image dimensions mismatch")
            mapping[str(n)] = im
        labels = []
        page = 1
        while True:
            response = self.cvat.request(
                "GET", f"/api/labels?task_id={body['task_id']}&page={page}&page_size=100"
            )
            labels.extend(response["results"])
            if not response.get("next"):
                break
            page += 1
            if page > 100:
                raise ValueError("CVAT label pagination limit")
        body["frames"] = mapping
        body["labels"] = labels
        if body["status"] in ["ATTACHING_DATA", "DATA_PENDING"]:
            body["status"] = "READY"
        return self._save(doc, body, "SYNC", actor)

    def import_predictions(self, batch_id, predictions, actor):
        doc = self.store.get("batch:" + batch_id)
        body = doc["body"]
        if body["status"] not in ["READY", "IMPORTING", "IMPORTED"]:
            raise ValueError("Sync task metadata before importing predictions")
        index = {p.image_id: p for p in predictions}
        if len(index) != len(predictions):
            raise ValueError("Duplicate prediction image ID")
        label_ids = {x["name"]: x["id"] for x in body["labels"]}
        attrs = {x["name"]: {a["name"]: a["id"] for a in x["attributes"]} for x in body["labels"]}
        shapes = []
        tags = []
        sidecar = {}
        for frame, raw in body["frames"].items():
            im = ImageManifest.model_validate(raw)
            if im.image_id not in index:
                raise ValueError("Missing prediction for task image")
            pred = index[im.image_id]
            filtered = Prediction.model_validate(
                pred.model_dump()
                | {"objects": [o.model_dump() for o in pred.objects if o.label in label_ids]}
            )
            payload, local = import_prediction(filtered, im, int(frame), label_ids, attrs)
            shapes.extend(payload["shapes"])
            tags.extend(payload["tags"])
            sidecar.update(local)
        if not sidecar:
            raise ValueError("No supported lesion candidates; use manual grading/annotation workflow")
        fingerprint = document_hash(
            [p.model_dump(mode="json") for p in sorted(predictions, key=lambda p: p.image_id)]
        )
        if body.get("import_fingerprint", fingerprint) != fingerprint:
            raise ValueError("Prediction contents changed; create a new batch")
        body["import_fingerprint"] = fingerprint
        old = body.get("sidecar", {})
        if old:
            if set(old) != set(sidecar):
                raise ValueError("Prediction set changed; create new batch")
            sidecar = old
        body["sidecar"] = sidecar
        body["status"] = "IMPORTING"
        doc = self._save(doc, body, "IMPORT_INTENT", actor)
        existing = self.cvat.get_annotations(body["task_id"])
        attr_ids = {
            a["id"] for x in body["labels"] for a in x["attributes"] if a["name"] == "ed_annotation_id"
        }
        existing_ids = [
            a["value"]
            for s in existing.get("shapes", []) + existing.get("tags", [])
            for a in s.get("attributes", [])
            if a["spec_id"] in attr_ids and a["value"]
        ]
        if len(existing_ids) != len(set(existing_ids)):
            raise ValueError("Duplicate provenance in CVAT; reconcile before retry")

        def absent(s):
            return all(a["value"] not in existing_ids for a in s["attributes"] if a["spec_id"] in attr_ids)

        missing = {
            "version": existing.get("version", 0),
            "shapes": [s for s in shapes if absent(s)],
            "tags": [s for s in tags if absent(s)],
            "tracks": [],
        }
        if missing["shapes"] or missing["tags"]:
            self.cvat.import_annotations(body["task_id"], missing)
        body = doc["body"]
        body["status"] = "IMPORTED"
        return self._save(doc, body, "IMPORTED", actor)

    def export(self, batch_id, decisions, actor, active_seconds):
        from eyes_contracts.models import ProtocolRef

        doc = self.store.get("batch:" + batch_id)
        body = doc["body"]
        if body["status"] not in ["READY", "IMPORTED"]:
            raise ValueError("Batch must be ready/imported and not previously finalized")
        payload = self.cvat.get_annotations(body["task_id"])
        names = {x["id"]: x["name"] for x in body["labels"]}
        attrs = {a["id"]: a["name"] for x in body["labels"] for a in x["attributes"]}
        annotations = export_annotations(
            payload,
            body.get("sidecar", {}),
            {int(k): ImageManifest.model_validate(v) for k, v in body["frames"].items()},
            names,
            attrs,
            actor,
            decisions,
            grading_protocol=ProtocolRef.model_validate(body["protocol"]),
        )
        # Namespace manual IDs by stable batch to avoid collisions across CVAT instances.
        normalized = []
        for a in annotations:
            if a.origin == "CLINICIAN_ADDED":
                a = Annotation.model_validate(
                    a.model_dump()
                    | {
                        "annotation_id": "ANN_"
                        + document_hash({"batch": batch_id, "annotation": a.annotation_id})[:32]
                    }
                )
                a = transition(a, "SUBMIT", actor)
            normalized.append(a)
        annotations = normalized
        if not annotations:
            raise ValueError("Empty review cannot be finalized")
        self.store.save_annotations(annotations)
        location = self.root / batch_id / document_hash([a.model_dump(mode="json") for a in annotations])
        location.mkdir(parents=True, exist_ok=True)
        write_records(location / "annotations.reviewed.jsonl", annotations)
        (location / "cvat_export.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        (location / "decision_journal.json").write_text(json.dumps(decisions, indent=2), encoding="utf-8")
        summary = session_summary(annotations, active_seconds)
        (location / "session_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        body["reviewed_annotations"] = [a.model_dump(mode="json") for a in annotations]
        body["status"] = "REVIEWED"
        body["export_path"] = str(location)
        return self._save(doc, body, "REVIEW_EXPORTED", actor)

    def finalize(self, batch_id, actor, lock=True):
        doc = self.store.get("batch:" + batch_id)
        body = doc["body"]
        if body["status"] != "REVIEWED":
            raise ValueError("Export reviewed annotations before adjudication")
        annotations = []
        for raw in body["reviewed_annotations"]:
            a = Annotation.model_validate(raw)
            if a.review_status == "REJECTED":
                annotations.append(a)
                continue
            if a.origin == "AI_SUGGESTED":
                raise ValueError("Human confirmation/correction required before adjudication")
            a = transition(a, "ADJUDICATE", actor)
            if lock:
                a = transition(a, "LOCK", actor)
            annotations.append(a)
        self.store.save_annotations(annotations)
        final_hash = document_hash(
        [a.model_dump(mode="json") for a in annotations]
        )
        final_path = self.root / batch_id / "final" / f"{final_hash}.jsonl"
        write_records(final_path, annotations)
        body["final_path"] = str(final_path)
        body["status"] = "LOCKED" if lock else "ADJUDICATED"
        return self._save(doc, body, "FINALIZED", actor)
