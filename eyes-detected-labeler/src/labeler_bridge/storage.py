"""Local-only MongoDB document repository and immutable filesystem image objects."""

import hashlib, json, os, tempfile
from pathlib import Path
from urllib.parse import urlsplit
from copy import deepcopy


class ConflictError(ValueError):
    pass


def document_hash(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def local_mongo_uri(uri):
    u = urlsplit(uri)
    if u.scheme != "mongodb" or u.hostname not in ["localhost", "127.0.0.1", "mongo"] or "," in u.netloc:
        raise ValueError("Only explicit local MongoDB endpoints allowed; Atlas/SRV/cloud are disabled")
    return uri


class MongoStore:
    def __init__(self, uri=None, database="ocuforge", client=None):
        from pymongo import MongoClient

        self.client = (
            client
            if client is not None
            else MongoClient(
                local_mongo_uri(uri or os.environ.get("MONGO_URI", "mongodb://localhost:27017")),
                serverSelectionTimeoutMS=5000,
            )
        )
        self.db = self.client[database]
        self.docs = self.db["workflow_documents"]
        self.revisions = self.db["annotation_revisions"]
        self.docs.create_index([("kind", 1), ("updated_at", -1)])
        self.revisions.create_index([("annotation_id", 1), ("revision_hash", 1)], unique=True)
        self.revisions.create_index([("image_id", 1), ("annotation_id", 1)])

    def health(self):
        self.client.admin.command("ping")
        return True

    def get(self, key):
        doc = self.docs.find_one({"_id": key})
        if doc is None:
            raise KeyError(key)
        return {k: v for k, v in doc.items() if k != "_id"} | {"key": doc["_id"]}

    def list(self, kind):
        return [self.get(x["_id"]) for x in self.docs.find({"kind": kind}).sort("_id", 1)]

    def create(self, key, kind, body):
        from pymongo.errors import DuplicateKeyError

        doc = {
            "_id": key,
            "kind": kind,
            "version": 0,
            "body": deepcopy(body),
            "updated_at": body.get("updated_at", ""),
        }
        if len(json.dumps(doc)) > 12 * 1024 * 1024:
            raise ValueError("Document too large; store export outside MongoDB")
        try:
            self.docs.insert_one(doc)
        except DuplicateKeyError:
            raise ConflictError("Document already exists") from None
        return self.get(key)

    def update(self, key, version, body):
        if len(json.dumps(body)) > 12 * 1024 * 1024:
            raise ValueError("Document too large")
        result = self.docs.update_one(
            {"_id": key, "version": version},
            {
                "$set": {"body": deepcopy(body), "updated_at": body.get("updated_at", "")},
                "$inc": {"version": 1},
            },
        )
        if result.modified_count != 1:
            raise ConflictError("Concurrent update; reload latest state")
        return self.get(key)

    def save_annotations(self, annotations):
        from pymongo.errors import DuplicateKeyError

        for annotation in annotations:
            body = annotation.model_dump(mode="json")
            h = document_hash(body)
            doc = {
                "_id": annotation.annotation_id + ":" + h,
                "annotation_id": annotation.annotation_id,
                "image_id": annotation.image_id,
                "revision_hash": h,
                "body": body,
                "cloud_eligible": False,
            }
            if len(json.dumps(doc)) > 12 * 1024 * 1024:
                raise ValueError("Annotation too large; use explicit external geometry storage migration")
            try:
                self.revisions.insert_one(doc)
            except DuplicateKeyError:
                if self.revisions.find_one({"_id": doc["_id"]}) != doc:
                    raise ConflictError("Immutable revision differs")

    def export_documents(self):
        return {
            "schema_version": "local_backup.v1",
            "workflow_documents": list(self.docs.find()),
            "annotation_revisions": list(self.revisions.find()),
        }

    def restore_documents(self, backup):
        if backup.get("schema_version") != "local_backup.v1":
            raise ValueError("Unknown backup version")
        if self.docs.count_documents({}) or self.revisions.count_documents({}):
            raise ValueError("Restore requires an empty database")
        for collection, key in [(self.docs, "workflow_documents"), (self.revisions, "annotation_revisions")]:
            rows = backup[key]
            if len({x["_id"] for x in rows}) != len(rows):
                raise ValueError("Duplicate backup ID")
        from eyes_contracts.models import Annotation

        for row in backup["annotation_revisions"]:
            annotation = Annotation.model_validate(row["body"])
            h = document_hash(annotation.model_dump(mode="json"))
            if (
                row["revision_hash"] != h
                or row["_id"] != annotation.annotation_id + ":" + h
                or row["annotation_id"] != annotation.annotation_id
                or row["image_id"] != annotation.image_id
            ):
                raise ValueError("Backup revision integrity failure")
        if backup["workflow_documents"]:
            self.docs.insert_many(backup["workflow_documents"])
        if backup["annotation_revisions"]:
            self.revisions.insert_many(backup["annotation_revisions"])


class LocalImageStore:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def ingest(self, source, expected_sha256):
        source = Path(source)
        suffix = source.suffix.lower()
        if suffix not in [".png", ".jpg", ".jpeg", ".tif", ".tiff"]:
            raise ValueError("Unsupported image extension")
        h = hashlib.sha256()
        with source.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        if h.hexdigest() != expected_sha256:
            raise ValueError("Image SHA256 mismatch")
        relative = f"{expected_sha256[:2]}/{expected_sha256}{suffix}"
        dest = self.root / relative
        dest.parent.mkdir(exist_ok=True)
        if dest.exists():
            if hashlib.sha256(dest.read_bytes()).hexdigest() != expected_sha256:
                raise ValueError("Existing local object corrupted")
            return relative
        fd, tmp = tempfile.mkstemp(dir=dest.parent, prefix=".incoming-")
        try:
            h = hashlib.sha256()
            with os.fdopen(fd, "wb") as out, source.open("rb") as src:
                for chunk in iter(lambda: src.read(1024 * 1024), b""):
                    out.write(chunk)
                    h.update(chunk)
                out.flush()
                os.fsync(out.fileno())
            if h.hexdigest() != expected_sha256:
                raise ValueError("Source changed during ingestion")
            os.replace(tmp, dest)
        finally:
            Path(tmp).unlink(missing_ok=True)
        return relative
