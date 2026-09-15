"""Trusted local-operator commands; never sends data to a remote storage service."""

import argparse
import json
import os
from pathlib import Path
from eyes_contracts.models import ImageManifest
from eyes_contracts.protocol import load_protocol
from eyes_contracts.validators import read_records, write_records
from labeler_bridge.storage import MongoStore, LocalImageStore
from labeler_bridge.workflow import Workflow
from labeler_bridge.cvat_client.client import CVATClient


def main():
    p = argparse.ArgumentParser(description="On-premise document store and CVAT workflow")
    p.add_argument("--database", default="ocuforge")
    p.add_argument("--exports", default="./local-state/exports")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("health")
    sub.add_parser("list-batches")
    q = sub.add_parser("ingest")
    q.add_argument("--images", required=True)
    q.add_argument("--source-root", required=True)
    q.add_argument("--object-root", required=True)
    q.add_argument("--out", required=True)
    for name in ["backup", "restore"]:
        q = sub.add_parser(name)
        q.add_argument("file")
    q = sub.add_parser("register")
    q.add_argument("--batch", required=True)
    q.add_argument("--images", required=True)
    q.add_argument("--protocol", required=True)
    q.add_argument("--actor", required=True)
    for name in [
        "create-task",
        "attach-task",
        "attach-share",
        "sync",
        "import-predictions",
        "export",
        "finalize",
    ]:
        q = sub.add_parser(name)
        q.add_argument("batch_id")
        q.add_argument("--actor", required=True)
        if name == "create-task":
            q.add_argument("--project-id", type=int, required=True)
        if name == "attach-task":
            q.add_argument("--task-id", type=int, required=True)
        if name == "attach-share":
            q.add_argument("--share-root", required=True)
        if name == "import-predictions":
            q.add_argument("--predictions", required=True)
        if name == "export":
            q.add_argument("--decisions", required=True)
            q.add_argument("--active-seconds", type=float, required=True)
        if name == "finalize":
            q.add_argument("--expert-attestation", action="store_true", required=True)
    a = p.parse_args()
    try:
        store = MongoStore(database=a.database)
        if a.command == "health":
            store.health()
            print("LOCAL_MONGO_OK")
            return
        if a.command == "list-batches":
            print(
                json.dumps(
                    [
                        {"key": d["key"], "version": d["version"], "status": d["body"]["status"]}
                        for d in store.list("batch")
                    ],
                    indent=2,
                )
            )
            return
        if a.command == "backup":
            target = Path(a.file)
            target.parent.mkdir(parents=True, exist_ok=True)
            # Exclusive create and owner-only mode; operator must quiesce writers first.
            fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(store.export_documents(), f, indent=2)
            print("LOCAL_DOCUMENT_BACKUP_ONLY")
            return
        if a.command == "restore":
            store.restore_documents(json.loads(Path(a.file).read_text(encoding="utf-8")))
            print("RESTORED_IN_EMPTY_DATABASE")
            return
        if a.command == "ingest":
            from PIL import Image

            source_root = Path(a.source_root).resolve()
            objects = LocalImageStore(a.object_root)
            rows = []
            for im in read_records(a.images):
                if not isinstance(im, ImageManifest):
                    raise ValueError("Image manifest required")
                source = (source_root / im.relative_uri).resolve()
                if not source.is_relative_to(source_root):
                    raise ValueError("Source path escapes root")
                with Image.open(source) as img:
                    img.load()
                    if img.size != (im.width_px, im.height_px) or img.mode != "RGB":
                        raise ValueError("Image dimensions/RGB mismatch")
                relative = objects.ingest(source, im.file_sha256)
                updated = ImageManifest.model_validate(im.model_dump() | {"relative_uri": relative})
                store.create("image:" + im.image_id, "image", updated.model_dump(mode="json"))
                rows.append(updated)
            write_records(a.out, rows)
            print(f"INGESTED {len(rows)}")
            return
        flow = Workflow(store, CVATClient(), a.exports)
        if a.command == "register":
            _, ref = load_protocol(a.protocol)
            doc = flow.register(read_records(a.batch)[0], read_records(a.images), ref, a.actor)
        elif a.command == "create-task":
            doc = flow.create_task(a.batch_id, a.project_id, a.actor)
        elif a.command == "attach-task":
            doc = flow.attach_task(a.batch_id, a.task_id, a.actor)
        elif a.command == "attach-share":
            doc = flow.attach_share(a.batch_id, a.actor, a.share_root)
        elif a.command == "sync":
            doc = flow.sync(a.batch_id, a.actor)
        elif a.command == "import-predictions":
            doc = flow.import_predictions(a.batch_id, read_records(a.predictions), a.actor)
        elif a.command == "export":
            doc = flow.export(
                a.batch_id,
                json.loads(Path(a.decisions).read_text(encoding="utf-8")),
                a.actor,
                a.active_seconds,
            )
        elif a.command == "finalize":
            doc = flow.finalize(a.batch_id, a.actor)
        print(json.dumps({"key": doc["key"], "version": doc["version"], "status": doc["body"]["status"]}))
    except Exception:
        # Database URI or local patient paths must not leak in command logs.
        p.exit(2, "Operation failed; inspect input/state locally. No credential or patient paths logged.\n")


if __name__ == "__main__":
    main()
