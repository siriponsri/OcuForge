"""Semantic and cross-record checks supplement generated JSON schemas."""

import json
from pathlib import Path
from .models import TYPES, Annotation, AnnotationBatch


def validate(record):
    kind = record.get("schema_version")
    if kind not in TYPES:
        raise ValueError(f"Unsupported schema version: {kind}")
    return TYPES[kind].model_validate(record)


def read_records(path):
    p = Path(path)
    text = p.read_text()
    raw = (
        [json.loads(x) for x in text.splitlines() if x.strip()] if p.suffix == ".jsonl" else json.loads(text)
    )
    return [validate(x) for x in (raw if isinstance(raw, list) else [raw])]


def write_records(path, records):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        validate(x.model_dump() if hasattr(x, "model_dump") else x).model_dump(mode="json") for x in records
    ]
    p.write_text(
        "".join(json.dumps(x, allow_nan=False) + "\n" for x in rows)
        if p.suffix == ".jsonl"
        else json.dumps(rows[0] if len(rows) == 1 else rows, indent=2, allow_nan=False) + "\n"
    )


def check_splits(images):
    seen = {}
    ids = set()
    for r in images:
        if r.image_id in ids:
            raise ValueError("Duplicate image ID")
        ids.add(r.image_id)
        for field in ["patient_pseudo_id", "eye_id", "visit_id", "file_sha256"]:
            value = getattr(r, field)
            if not value or r.split == "UNASSIGNED":
                continue
            key = (field, value)
            if key in seen and seen[key] != r.split:
                raise ValueError(f"Split leakage via {field}")
            seen[key] = r.split
    return True


def validate_batch(batch, images):
    batch = AnnotationBatch.model_validate(batch.model_dump())
    check_splits(images)
    index = {i.image_id: i for i in images}
    for item in batch.items:
        if item.image_id not in index:
            raise ValueError("Unknown batch image")
        im = index[item.image_id]
        if im.dataset_id != batch.dataset_id or im.split != item.split:
            raise ValueError("Batch disagrees with authoritative image manifest")
        if (im.split == "SENTINEL") != item.locked_sentinel:
            raise ValueError("Sentinel status mismatch")
    return batch


def training_annotations(annotations, images, allow_submitted=False):
    check_splits(images)
    index = {i.image_id: i for i in images}
    seen = set()
    out = []
    for a in annotations:
        a = Annotation.model_validate(a.model_dump())
        if a.annotation_id in seen:
            raise ValueError("Duplicate annotation ID")
        seen.add(a.annotation_id)
        if a.image_id not in index:
            raise ValueError("Unknown image")
        if index[a.image_id].split != "TRAIN":
            raise ValueError("Training ingest requires TRAIN split")
        eligible = {"ADJUDICATED", "LOCKED"} | ({"SUBMITTED"} if allow_submitted else set())
        if a.origin == "AI_SUGGESTED" or a.review_status not in eligible or a.uncertain:
            raise ValueError("Annotation not training-eligible")
        out.append(a)
    return out
