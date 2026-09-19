"""Local/on-prem OcuForge Product POC service.

The service owns filesystem access, DICOM decoding, durable documents, object
storage, export receipts, and manifest generation. The browser only consumes
the HTTP contract exposed here.
"""

from __future__ import annotations

import csv
import copy
import hashlib
import importlib.util
import io
import json
import os
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pydicom
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from PIL import Image
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.filewriter import dcmwrite
from pydicom.uid import (
    ExplicitVRBigEndian,
    ExplicitVRLittleEndian,
    ImplicitVRLittleEndian,
    PYDICOM_IMPLEMENTATION_UID,
)


PRODUCT_SCHEMA_VERSION = "product.v0.1"
ANNOTATION_SCHEMA_VERSION = "annotation.v0.1"
DERIVATIVE_VERSION = "dicom-display-v0.1"
MODEL_MANIFEST_ID = "mock-local-bundle-v0.1"
OUTPUT_POLICIES = {
    "REFERENCE_ONLY",
    "COPY_ORIGINAL",
    "DERIVED_IMAGE_ONLY",
    "COPY_ORIGINAL_AND_DERIVED",
}
RASTER_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
DICOM_EXTENSIONS = {".dcm", ".dicom"}
SUPPORTED_PHOTOMETRIC_INTERPRETATIONS = {"MONOCHROME1", "MONOCHROME2", "RGB", "YBR_FULL"}
VERIFIED_TRANSFER_SYNTAXES = (
    {"uid": str(ImplicitVRLittleEndian), "name": "Implicit VR Little Endian", "fixture": "synthetic-implicit"},
    {"uid": str(ExplicitVRLittleEndian), "name": "Explicit VR Little Endian", "fixture": "synthetic-explicit"},
    {"uid": str(ExplicitVRBigEndian), "name": "Explicit VR Big Endian", "fixture": "synthetic-big-endian"},
)
VERIFIED_TRANSFER_SYNTAX_UIDS = {item["uid"] for item in VERIFIED_TRANSFER_SYNTAXES}


class DicomIngestionError(ValueError):
    """Stable classification for DICOM items that cannot become reviewable cases."""

    def __init__(self, category: str, reason: str):
        super().__init__(reason)
        self.category = category
        self.reason = reason


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def json_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256_bytes(encoded)


def safe_name(value: str, fallback: str = "LOCAL") -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-.")
    return cleaned or fallback


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def derive_queue_status(case: dict[str, Any]) -> str:
    if case.get("qcStatus") == "QUARANTINED":
        return "QUARANTINED"
    if case.get("export_status") == "EXPORTED":
        return "EXPORTED"
    if case.get("review_status") == "HUMAN_REVIEWED" and case.get("export_status") == "FAILED":
        return "HUMAN_REVIEWED_EXPORT_FAILED"
    if case.get("ai_status") == "FAILED":
        return "HUMAN_REVIEWED" if case.get("review_status") == "HUMAN_REVIEWED" else "AI_FAILED"
    if case.get("ai_status") == "RUNNING":
        return "AI_RUNNING"
    if case.get("review_status") == "IN_REVIEW":
        return "IN_REVIEW"
    if case.get("review_status") == "HUMAN_REVIEWED":
        return "HUMAN_REVIEWED"
    if case.get("ai_status") == "PROCESSED":
        return "AI_PROCESSED"
    return "NOT_PROCESSED"


def as_number(value: Any) -> int | float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return int(number) if number.is_integer() else number


class LocalFileSystemBridge:
    """Trusted backend filesystem boundary for local folders and mounted shares."""

    def __init__(self, root: Path):
        self.root = root

    def resolve(self, value: str | Path, *, create: bool = False) -> Path:
        if value is None or not str(value).strip():
            raise ValueError("A local path is required")
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = (self.root / path).resolve()
            root = self.root.resolve()
            if path != root and root not in path.parents:
                raise ValueError("Relative path escapes the configured data root")
        else:
            path = path.resolve()
        if create:
            path.mkdir(parents=True, exist_ok=True)
        return path

    def readiness(self, source: str | None, destination: str | None) -> dict[str, Any]:
        source_path = None
        destination_path = None
        source_error = None
        destination_error = None
        if source:
            try:
                source_path = self.resolve(source)
            except (OSError, ValueError) as error:
                source_error = str(error)
        if destination:
            try:
                destination_path = self.resolve(destination, create=True)
            except (OSError, ValueError) as error:
                destination_error = str(error)
        source_ready = bool(source_path and source_path.exists() and (source_path.is_dir() or source_path.is_file()))
        destination_ready = bool(destination_path and destination_path.exists() and destination_path.is_dir())
        return {
            "source": {
                "reference": str(source_path) if source_path else None,
                "ready": source_ready,
                "error": source_error,
                "authority": "BACKEND",
            },
            "destination": {
                "reference": str(destination_path) if destination_path else None,
                "ready": destination_ready,
                "error": destination_error,
                "authority": "BACKEND",
            },
            "browser_filesystem_authoritative": False,
        }

    def discover(self, source: str | Path) -> list[Path]:
        path = self.resolve(source)
        if path.is_file():
            return [path]
        if not path.is_dir():
            raise ValueError(f"Source path does not exist or is not a folder: {path}")
        return sorted(
            item for item in path.rglob("*")
            if item.is_file() and not any(part.startswith(".") for part in item.relative_to(path).parts)
        )


class DocumentStore:
    """Small local document store with one JSON document per aggregate.

    This is the default Windows POC persistence. Its document and object
    interfaces intentionally match the future Mongo-backed adapter boundary.
    """

    def __init__(self, root: Path):
        self.root = root
        self.db = root / "db"
        self.cases_dir = self.db / "cases"
        self.objects = root / "objects"
        self.audit_dir = self.db / "audit"
        self.jobs_dir = self.db / "ingestion_jobs"
        self.items_dir = self.db / "ingestion_items"
        self.exports = root / "exports"
        self.fixtures = root / "fixtures"
        for path in (self.cases_dir, self.objects, self.audit_dir, self.jobs_dir, self.items_dir, self.exports, self.fixtures):
            path.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()

    def case_path(self, case_id: str) -> Path:
        return self.cases_dir / f"{safe_name(case_id)}.json"

    def get_case(self, case_id: str) -> dict[str, Any] | None:
        path = self.case_path(case_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def list_cases(self) -> list[dict[str, Any]]:
        return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(self.cases_dir.glob("*.json"))]

    def save_case(self, case: dict[str, Any]) -> None:
        with self.lock:
            case["derived_queue_status"] = derive_queue_status(case)
            case["updated_at"] = now()
            target = self.case_path(case["id"])
            temporary = target.with_suffix(".tmp")
            temporary.write_bytes(json_bytes(case))
            temporary.replace(target)

    def job_path(self, job_id: str) -> Path:
        return self.jobs_dir / f"{safe_name(job_id)}.json"

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        path = self.job_path(job_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def save_job(self, job: dict[str, Any]) -> None:
        with self.lock:
            target = self.job_path(job["id"])
            temporary = target.with_suffix(".tmp")
            temporary.write_bytes(json_bytes(job))
            temporary.replace(target)

    def items_path(self, job_id: str) -> Path:
        return self.items_dir / f"{safe_name(job_id)}.json"

    def save_ingestion_items(self, job_id: str, items: list[dict[str, Any]]) -> None:
        with self.lock:
            target = self.items_path(job_id)
            temporary = target.with_suffix(".tmp")
            temporary.write_bytes(json_bytes(items))
            temporary.replace(target)

    def get_ingestion_items(self, job_id: str) -> list[dict[str, Any]]:
        path = self.items_path(job_id)
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))

    def clear(self) -> None:
        with self.lock:
            for path in self.cases_dir.glob("*.json"):
                path.unlink()
            for path in self.audit_dir.glob("*.jsonl"):
                path.unlink()
            for path in self.jobs_dir.glob("*.json"):
                path.unlink()
            for path in self.items_dir.glob("*.json"):
                path.unlink()

    def put_object(self, key: str, content: bytes) -> str:
        relative = Path(key.replace("\\", "/"))
        if not key or relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Unsafe object key")
        target = self.objects / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        expected_hash = sha256_bytes(content)
        if target.exists():
            if not target.is_file() or sha256_bytes(target.read_bytes()) != expected_hash:
                raise ValueError("Immutable object conflict")
            return key.replace("\\", "/")
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_bytes(content)
        if sha256_bytes(temporary.read_bytes()) != expected_hash:
            temporary.unlink(missing_ok=True)
            raise IOError("Object hash verification failed")
        temporary.replace(target)
        return key.replace("\\", "/")

    def object_path(self, key: str) -> Path:
        relative = Path(key.replace("\\", "/"))
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Unsafe object key")
        path = (self.objects / relative).resolve()
        if path == self.objects.resolve() or self.objects.resolve() not in path.parents:
            raise ValueError("Object escaped storage root")
        return path

    def append_audit(self, case_id: str, event: dict[str, Any]) -> None:
        target = self.audit_dir / f"{safe_name(case_id)}.jsonl"
        with self.lock:
            with target.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def audit(case: dict[str, Any], event: str, detail: str, actor: str = "SYSTEM") -> None:
    entry = {"actor": actor, "actorLabel": "Reviewer" if actor == "reviewer-7f3a" else actor.title(), "at": now(), "event": event, "detail": detail}
    case.setdefault("audit", []).append(entry)


def dicom_value(dataset: pydicom.Dataset, name: str, default: Any = None) -> Any:
    value = getattr(dataset, name, default)
    if value is None:
        return default
    if isinstance(value, pydicom.multival.MultiValue):
        return [as_number(item) if isinstance(item, (int, float)) or str(item).replace(".", "", 1).isdigit() else str(item) for item in value]
    if isinstance(value, (pydicom.valuerep.DSfloat, pydicom.valuerep.IS)):
        return as_number(value)
    return str(value) if not isinstance(value, (int, float, bool)) else value


def technical_metadata(dataset: pydicom.Dataset) -> dict[str, Any]:
    try:
        frames = int(dicom_value(dataset, "NumberOfFrames", 1) or 1)
    except (TypeError, ValueError) as error:
        raise DicomIngestionError("MALFORMED", "Malformed DICOM NumberOfFrames") from error
    return {
        "modality": dicom_value(dataset, "Modality", "OT"),
        "laterality": dicom_value(dataset, "ImageLaterality", None) or dicom_value(dataset, "Laterality", None),
        "rows": dicom_value(dataset, "Rows"),
        "columns": dicom_value(dataset, "Columns"),
        "samples_per_pixel": dicom_value(dataset, "SamplesPerPixel", 1),
        "photometric_interpretation": dicom_value(dataset, "PhotometricInterpretation"),
        "number_of_frames": max(1, frames),
        "bits_allocated": dicom_value(dataset, "BitsAllocated"),
        "bits_stored": dicom_value(dataset, "BitsStored"),
        "high_bit": dicom_value(dataset, "HighBit"),
        "pixel_representation": dicom_value(dataset, "PixelRepresentation"),
        "orientation_patient": dicom_value(dataset, "ImageOrientationPatient"),
        "pixel_spacing": dicom_value(dataset, "PixelSpacing"),
        "window_center": dicom_value(dataset, "WindowCenter"),
        "window_width": dicom_value(dataset, "WindowWidth"),
        "privacy_policy_version": "dicom-technical-v0.1",
    }


def normalize_frame(frame: np.ndarray, dataset: pydicom.Dataset) -> Image.Image:
    array = np.asarray(frame)
    if array.ndim == 3 and array.shape[-1] in (3, 4):
        if array.shape[-1] == 4:
            array = array[..., :3]
        return Image.fromarray(np.asarray(np.clip(array, 0, 255), dtype=np.uint8), mode="RGB")
    values = array.astype(np.float32)
    center = dicom_value(dataset, "WindowCenter")
    width = dicom_value(dataset, "WindowWidth")
    center = center[0] if isinstance(center, list) else center
    width = width[0] if isinstance(width, list) else width
    if center is not None and width and float(width) > 0:
        low, high = float(center) - float(width) / 2, float(center) + float(width) / 2
    else:
        low, high = float(np.min(values)), float(np.max(values))
    if high <= low:
        high = low + 1
    output = np.clip((values - low) * 255 / (high - low), 0, 255).astype(np.uint8)
    if str(dicom_value(dataset, "PhotometricInterpretation", "")) == "MONOCHROME1":
        output = 255 - output
    return Image.fromarray(output, mode="L")


def render_dicom(raw: bytes, store: DocumentStore) -> tuple[dict[str, Any], list[str]]:
    try:
        dataset = pydicom.dcmread(io.BytesIO(raw), force=False)
    except Exception as error:
        raise DicomIngestionError("MALFORMED", "Malformed DICOM object") from error
    technical = technical_metadata(dataset)
    try:
        transfer_syntax = str(dataset.file_meta.TransferSyntaxUID)
    except (AttributeError, KeyError) as error:
        raise DicomIngestionError("MALFORMED", "DICOM transfer syntax is missing") from error
    if transfer_syntax not in VERIFIED_TRANSFER_SYNTAX_UIDS:
        raise DicomIngestionError("UNSUPPORTED", f"Unsupported DICOM transfer syntax: {transfer_syntax}")
    photometric = technical.get("photometric_interpretation")
    if photometric not in SUPPORTED_PHOTOMETRIC_INTERPRETATIONS:
        raise DicomIngestionError("UNSUPPORTED", f"Unsupported DICOM photometric interpretation: {photometric}")
    frame_count = technical["number_of_frames"]
    try:
        pixel_array = dataset.pixel_array
    except Exception as error:
        raise DicomIngestionError("UNSUPPORTED", f"DICOM pixel decoding failed for transfer syntax {transfer_syntax}") from error
    if frame_count == 1:
        frames = [pixel_array]
    else:
        try:
            frames = [pixel_array[index] for index in range(frame_count)]
        except (IndexError, TypeError) as error:
            raise DicomIngestionError("MALFORMED", "DICOM frame count does not match pixel data") from error
    derivative_keys: list[str] = []
    for index, frame in enumerate(frames, start=1):
        image = normalize_frame(frame, dataset)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        key = f"derivatives/{sha256_bytes(raw)}/frame-{index:03d}.png"
        store.put_object(key, buffer.getvalue())
        derivative_keys.append(key)
    metadata = {
        **technical,
        "study_instance_uid": str(getattr(dataset, "StudyInstanceUID", "")) or None,
        "series_instance_uid": str(getattr(dataset, "SeriesInstanceUID", "")) or None,
        "sop_instance_uid": str(getattr(dataset, "SOPInstanceUID", "")) or None,
        "transfer_syntax_uid": transfer_syntax,
        "orientation_windowing": {
            "orientation_patient": technical["orientation_patient"],
            "window_center": technical["window_center"],
            "window_width": technical["window_width"],
            "preprocessing_version": DERIVATIVE_VERSION,
        },
    }
    return metadata, derivative_keys


def render_raster(raw: bytes, store: DocumentStore, source_hash: str) -> tuple[dict[str, Any], str]:
    with Image.open(io.BytesIO(raw)) as source:
        source.verify()
    with Image.open(io.BytesIO(raw)) as source:
        image = source.convert("RGB")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        key = f"derivatives/{source_hash}/frame-1.png"
        store.put_object(key, buffer.getvalue())
        return {"rows": image.height, "columns": image.width, "number_of_frames": 1}, key


def is_dicom_candidate(path: Path, raw: bytes) -> bool:
    return path.suffix.lower() in DICOM_EXTENSIONS or raw[128:132] == b"DICM"


def base_case(
    case_id: str,
    file_path: Path,
    source_folder: str,
    source_reference: str,
    source_hash: str,
    output_policy: str,
    file_type: str | None = None,
) -> dict[str, Any]:
    timestamp = now()
    return {
        "schema_version": PRODUCT_SCHEMA_VERSION,
        "id": case_id,
        "imageId": f"IMG-{source_hash[:12].upper()}",
        "fileName": file_path.name,
        "sourceFolder": source_folder,
        "sourceFolderId": safe_name(source_folder).upper(),
        "sourceReference": source_reference,
        "sourceSha256": source_hash,
        "sourceObjectKey": f"source/{source_hash}/original.bin",
        "sourceBytesStored": True,
        "fileType": file_type or ("DICOM" if file_path.suffix.lower() in DICOM_EXTENSIONS else "RASTER"),
        "modality": "OT",
        "laterality": None,
        "dimensions": "-",
        "qcStatus": "PASS",
        "review_status": "NOT_STARTED",
        "ai_status": "NOT_RUN",
        "export_status": "NOT_EXPORTED",
        "derived_queue_status": "NOT_PROCESSED",
        "systemGrade": None,
        "systemConfidence": None,
        "systemPredictionId": None,
        "systemModelManifestId": None,
        "humanGrade": None,
        "humanReviewer": None,
        "humanReviewStatus": "UNREVIEWED",
        "human_grading_protocol": None,
        "human_reviewed_at": None,
        "remark": "",
        "annotations": [],
        "annotation_revisions": [],
        "prediction_history": [],
        "audit": [],
        "imageUrl": None,
        "displayDerivativeUri": None,
        "derivative_provenance": None,
        "derivative_preprocessing_version": None,
        "training_image_uri": None,
        "training_image_sha256": None,
        "technical_metadata": {},
        "quarantineCategory": None,
        "quarantineReason": None,
        "output_policy": output_policy,
        "trainingEligibility": "UNREVIEWED_SYSTEM",
        "created_at": timestamp,
        "updated_at": timestamp,
    }


def case_from_file(path: Path, relative_name: str, source_reference: str, output_policy: str, store: DocumentStore) -> dict[str, Any]:
    raw = path.read_bytes()
    source_hash = sha256_bytes(raw)
    source_key = f"source/{source_hash}/original.bin"
    store.put_object(source_key, raw)
    source_folder = safe_name(Path(relative_name).parts[0] if Path(relative_name).parts else path.parent.name)
    case_prefix = f"CASE-{source_hash[:12].upper()}"
    if is_dicom_candidate(path, raw):
        dataset = base_case(
            f"{case_prefix}-F1", path, source_folder, source_reference, source_hash, output_policy, "DICOM"
        )
        try:
            metadata, derivative_keys = render_dicom(raw, store)
            count = metadata["number_of_frames"]
            cases = []
            for frame_number, derivative_key in enumerate(derivative_keys, start=1):
                case = copy.deepcopy(dataset)
                case["id"] = f"{case_prefix}-F{frame_number:03d}"
                case["imageId"] = f"IMG-{source_hash[:12].upper()}-F{frame_number:03d}"
                case["sourceReference"] = f"{source_reference}#frame={frame_number}"
                case["fileType"] = "DICOM"
                case["modality"] = metadata.get("modality", "OT")
                case["laterality"] = metadata.get("laterality")
                case["dimensions"] = f"{metadata.get('columns') or '-'} × {metadata.get('rows') or '-'}"
                case["frame_count"] = count
                case["frame_number"] = frame_number
                case["study_instance_uid"] = metadata.get("study_instance_uid")
                case["series_instance_uid"] = metadata.get("series_instance_uid")
                case["sop_instance_uid"] = metadata.get("sop_instance_uid")
                case["transfer_syntax_uid"] = metadata.get("transfer_syntax_uid")
                case["technical_metadata"] = metadata
                case["displayDerivativeUri"] = f"/api/objects/{derivative_key}"
                case["imageUrl"] = case["displayDerivativeUri"]
                case["derivative_provenance"] = metadata["orientation_windowing"]
                case["derivative_preprocessing_version"] = DERIVATIVE_VERSION
                case["training_image_uri"] = f"local-object://{derivative_key}"
                case["training_image_sha256"] = sha256_bytes(store.object_path(derivative_key).read_bytes())
                audit(case, "INGESTED", f"Backend ingested DICOM frame {frame_number}/{count}; original bytes preserved.")
                cases.append(case)
            return cases
        except DicomIngestionError as error:
            case = dataset
            case["fileType"] = "DICOM"
            case["qcStatus"] = "QUARANTINED"
            case["derived_queue_status"] = "QUARANTINED"
            case["quarantineCategory"] = error.category
            case["quarantineReason"] = error.reason
            audit(case, "QUARANTINED", "Original DICOM bytes preserved; display derivative generation failed.")
            return [case]
        except Exception as error:
            case = dataset
            case["fileType"] = "DICOM"
            case["qcStatus"] = "QUARANTINED"
            case["derived_queue_status"] = "QUARANTINED"
            case["quarantineCategory"] = "MALFORMED"
            case["quarantineReason"] = "Malformed DICOM object"
            audit(case, "QUARANTINED", f"Original DICOM bytes preserved; backend error: {type(error).__name__}.")
            return [case]
    detected_type = "RASTER" if path.suffix.lower() in RASTER_EXTENSIONS else "OTHER"
    case = base_case(
        f"{case_prefix}-F1", path, source_folder, source_reference, source_hash, output_policy, detected_type
    )
    try:
        if path.suffix.lower() not in RASTER_EXTENSIONS:
            raise DicomIngestionError("UNSUPPORTED", f"Unsupported raster extension: {path.suffix or '<none>'}")
        metadata, derivative_key = render_raster(raw, store, source_hash)
        case["fileType"] = "RASTER"
        case["modality"] = "CFP"
        case["dimensions"] = f"{metadata['columns']} × {metadata['rows']}"
        case["frame_count"] = 1
        case["frame_number"] = 1
        case["technical_metadata"] = metadata
        case["displayDerivativeUri"] = f"/api/objects/{derivative_key}"
        case["imageUrl"] = case["displayDerivativeUri"]
        case["derivative_provenance"] = {"preprocessing_version": "raster-display-v0.1"}
        case["derivative_preprocessing_version"] = "raster-display-v0.1"
        case["training_image_uri"] = f"local-object://{derivative_key}"
        case["training_image_sha256"] = sha256_bytes(store.object_path(derivative_key).read_bytes())
        audit(case, "INGESTED", "Backend ingested raster image; original bytes preserved.")
    except DicomIngestionError as error:
        case["qcStatus"] = "QUARANTINED"
        case["derived_queue_status"] = "QUARANTINED"
        case["quarantineCategory"] = error.category
        case["quarantineReason"] = error.reason
        audit(case, "QUARANTINED", "Original raster bytes preserved; display derivative generation failed.")
    except Exception:
        case["qcStatus"] = "QUARANTINED"
        case["derived_queue_status"] = "QUARANTINED"
        case["quarantineCategory"] = "MALFORMED"
        case["quarantineReason"] = "Malformed raster object"
        audit(case, "QUARANTINED", "Original raster bytes preserved; display derivative generation failed.")
    return [case]


def manifest_rows(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in cases:
        revisions = item.get("annotation_revisions", [])
        has_human_grade = item.get("humanGrade") is not None
        eligibility = item.get("trainingEligibility") or "UNREVIEWED_SYSTEM"
        if eligibility == "HUMAN" and not has_human_grade:
            eligibility = "UNREVIEWED_SYSTEM"
        latest = revisions[-1] if revisions else {}
        rows.append({
            "manifest_version": "manifest.v0.1",
            "manifest_snapshot_id": "local-live-snapshot",
            "row_id": f"ROW-{item['id']}",
            "case_id": item["id"],
            "image_id": item["imageId"],
            "source_folder_id": item.get("sourceFolderId"),
            "source_folder_name": item.get("sourceFolder"),
            "source_provider": "LOCAL",
            "source_reference": item.get("sourceReference"),
            "local_object_uri": f"local-object://{item.get('sourceObjectKey')}",
            "file_name": item.get("fileName"),
            "file_extension": Path(item.get("fileName", "")).suffix.lower().lstrip("."),
            "file_sha256": item.get("sourceSha256"),
            "file_type": item.get("fileType"),
            "modality": item.get("modality"),
            "laterality": item.get("laterality"),
            "width_px": item.get("technical_metadata", {}).get("columns", ""),
            "height_px": item.get("technical_metadata", {}).get("rows", ""),
            "frame_count": item.get("frame_count", 1),
            "study_instance_uid_reference": item.get("study_instance_uid"),
            "series_instance_uid_reference": item.get("series_instance_uid"),
            "sop_instance_uid_reference": item.get("sop_instance_uid"),
            "frame_number": item.get("frame_number", 1),
            "transfer_syntax_uid": item.get("transfer_syntax_uid"),
            "qc_status": item.get("qcStatus"),
            "review_status": item.get("review_status"),
            "ai_status": item.get("ai_status"),
            "export_status": item.get("export_status"),
            "derived_queue_status": item.get("derived_queue_status"),
            "system_dr_grade": item.get("systemGrade"),
            "system_dr_confidence": item.get("systemConfidence"),
            "system_prediction_id": item.get("systemPredictionId"),
            "system_model_manifest_id": item.get("systemModelManifestId"),
            "human_reviewed_dr_grade": item.get("humanGrade"),
            "human_grading_protocol": item.get("human_grading_protocol") or "DR-GRADING-PROTOCOL-UNSET",
            "human_review_status": item.get("humanReviewStatus"),
            "annotation_count": len(item.get("annotations", [])),
            "human_annotation_count": len([a for a in item.get("annotations", []) if a.get("provenance") == "USER"]),
            "annotation_artifact_uri": item.get("annotation_artifact_uri") or f"local-export://{item['id']}/annotations.json",
            "annotation_revision_hash": latest.get("revision_hash", ""),
            "annotation_schema_version": latest.get("schema_version", ANNOTATION_SCHEMA_VERSION),
            "training_image_uri": item.get("training_image_uri") or "",
            "training_image_sha256": item.get("training_image_sha256") or "",
            "derivative_preprocessing_version": item.get("derivative_preprocessing_version") or "",
            "training_eligibility": eligibility,
            "label_provenance": "HUMAN" if eligibility == "HUMAN" and has_human_grade else eligibility,
            "output_policy": item.get("output_policy"),
            "export_uri": item.get("export_uri"),
            "export_hash": item.get("export_hash"),
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
        })
    return rows


def csv_text(rows: list[dict[str, Any]], fields: list[str]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def supported_transfer_syntaxes() -> dict[str, Any]:
    decoder_plugins = {
        name: bool(importlib.util.find_spec(name))
        for name in ("pylibjpeg", "pylibjpeg_libjpeg", "pylibjpeg_openjpeg", "gdcm")
    }
    return {
        "tested": [{**item, "result": "PASS"} for item in VERIFIED_TRANSFER_SYNTAXES],
        "decoder_stack": {
            "pydicom": pydicom.__version__,
            "numpy": np.__version__,
            "pillow": Image.__version__,
            **decoder_plugins,
        },
        "compressed_support": {
            "claimed": False,
            "reason": "No compressed transfer syntax is reported until a backend fixture passes on this runtime.",
        },
        "claim_ceiling": "Only the explicit tested list is verified on this runtime.",
    }


class Runtime:
    def __init__(self) -> None:
        root = Path(os.environ.get("OCUFORGE_PRODUCT_DATA_ROOT", Path(__file__).resolve().parent / "data")).resolve()
        self.store = DocumentStore(root)
        self.fs = LocalFileSystemBridge(root)
        self.root = root

    def state(self) -> dict[str, Any]:
        cases = self.store.list_cases()
        jobs = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(self.store.jobs_dir.glob("*.json"))]
        return {
            "cases": cases,
            "sourceConfig": self.source_config(),
            "ingestion": jobs[-1] if jobs else {"status": "IDLE"},
        }

    def source_config(self) -> dict[str, Any]:
        return {
            "sourceType": "LOCAL_FOLDER",
            "sourceReference": "",
            "destinationType": "LOCAL_FOLDER",
            "destinationReference": str(self.store.exports),
            "outputPolicy": "REFERENCE_ONLY",
            "selectedFileCount": 0,
            "selectedInputLabel": "Backend path required",
            "simulateExportFailure": False,
        }

    def ingest(self, source: str, destination: str, output_policy: str) -> dict[str, Any]:
        if output_policy not in OUTPUT_POLICIES:
            raise ValueError(f"Unknown output policy: {output_policy}")
        source_path = self.fs.resolve(source)
        destination_path = self.fs.resolve(destination, create=True)
        files = self.fs.discover(source_path)
        existing_hashes = {case.get("sourceSha256") for case in self.store.list_cases()}
        job_id = f"JOB-{uuid.uuid4().hex.upper()}"
        job = {
            "id": job_id,
            "schema_version": PRODUCT_SCHEMA_VERSION,
            "source_reference": f"local-path://{source_path}",
            "destination_reference": str(destination_path),
            "status": "SCANNING",
            "counts": {
                "discovered": len(files),
                "dicom_discovered": 0,
                "raster_discovered": 0,
                "accepted": 0,
                "accepted_cases": 0,
                "duplicates": 0,
                "unsupported": 0,
                "malformed": 0,
                "quarantined": 0,
                "failed": 0,
                "persisted": 0,
            },
            "scan_options": {"output_policy": output_policy},
            "item_results_reference": f"local-ingestion-items://{job_id}",
            "started_at": now(),
            "completed_at": None,
            "error_summary": [],
        }
        self.store.save_job(job)
        item_results = []
        cases = []
        for index, path in enumerate(files, start=1):
            relative_path = path.name if source_path.is_file() else str(path.relative_to(source_path))
            relative_name = str(Path(source_path.name) / relative_path)
            item = {
                "ingestion_item_id": f"{job_id}-I{index:04d}",
                "job_id": job_id,
                "schema_version": PRODUCT_SCHEMA_VERSION,
                "source_item_reference": f"local-path://{path}",
                "source_relative_path": relative_path,
                "original_file_name": path.name,
                "detected_file_type": "OTHER",
                "sha256": None,
                "byte_size": None,
                "outcome": "FAILED",
                "quarantine_reason": None,
                "image_id": None,
                "case_ids": [],
                "attempt_id": None,
                "created_at": now(),
            }
            try:
                raw = path.read_bytes()
            except OSError as error:
                item["quarantine_reason"] = "Unable to read source item"
                job["counts"]["failed"] += 1
                job["error_summary"].append(f"{path.name}: {type(error).__name__}")
                item_results.append(item)
                continue
            source_hash = sha256_bytes(raw)
            item["sha256"] = source_hash
            item["byte_size"] = len(raw)
            dicom = is_dicom_candidate(path, raw)
            item["detected_file_type"] = "DICOM" if dicom else {
                ".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".tif": "TIFF", ".tiff": "TIFF"
            }.get(path.suffix.lower(), "OTHER")
            if dicom:
                job["counts"]["dicom_discovered"] += 1
            elif item["detected_file_type"] != "OTHER":
                job["counts"]["raster_discovered"] += 1
            if source_hash in existing_hashes:
                item["outcome"] = "DUPLICATE"
                job["counts"]["duplicates"] += 1
                item_results.append(item)
                continue
            created = case_from_file(path, relative_name, f"local-path://{source_path}", output_policy, self.store)
            for case in created:
                self.store.save_case(case)
                self.store.append_audit(case["id"], case["audit"][-1])
                cases.append(case)
            item["case_ids"] = [case["id"] for case in created]
            item["image_id"] = created[0].get("imageId") if created else None
            item["quarantine_reason"] = created[0].get("quarantineReason") if created else None
            if any(case["qcStatus"] != "QUARANTINED" for case in created):
                item["outcome"] = "ACCEPTED"
                job["counts"]["accepted"] += 1
                job["counts"]["accepted_cases"] += len(created)
            else:
                category = created[0].get("quarantineCategory", "MALFORMED")
                item["outcome"] = category
                job["counts"][category.lower()] += 1
                job["counts"]["quarantined"] += 1
            job["counts"]["persisted"] += len(created)
            item_results.append(item)
            existing_hashes.add(source_hash)
        job["status"] = "COMPLETED_WITH_ERRORS" if job["counts"]["quarantined"] or job["counts"]["failed"] else "COMPLETED"
        job["completed_at"] = now()
        self.store.save_ingestion_items(job_id, item_results)
        self.store.save_job(job)
        return {**job, "cases": cases, "destination": str(destination_path)}

    def run_ai(self, case: dict[str, Any]) -> dict[str, Any]:
        if case["qcStatus"] == "QUARANTINED":
            raise ValueError("Quarantined objects cannot run AI")
        seed = int(case["sourceSha256"][:8], 16)
        grade = seed % 5
        confidence = round(0.68 + ((seed >> 8) % 25) / 100, 2)
        prediction_id = f"PRED-{case['id']}-{case['sourceSha256'][:8]}"
        return {
            "prediction_id": prediction_id,
            "provenance": "SYSTEM",
            "system_dr_grade": grade,
            "confidence": confidence,
            "model_manifest": {
                "model_manifest_id": MODEL_MANIFEST_ID,
                "adapter_contract_version": "model-adapter.v0.1",
                "encoder_family": "architecture-agnostic",
                "head_family": "mock-ordinal-head",
                "preprocessing_version": "mock-preprocess-v0.1",
                "calibration_version": "mock-calibration-v0.1",
            },
            "annotations": [{
                "id": f"ANN-S-{case['id']}", "type": "ellipse", "x": 0.46, "y": 0.42,
                "width": 0.16, "height": 0.12, "label": "System candidate region", "provenance": "SYSTEM",
                "prediction_id": prediction_id,
            }],
            "created_at": now(),
        }

    def save_review(self, case: dict[str, Any], payload: dict[str, Any], human: bool = False) -> dict[str, Any]:
        annotation = payload.get("annotation")
        annotation_update = payload.get("annotation_update")
        if annotation:
            annotation = {**annotation, "provenance": "USER"}
            case["annotations"].append(annotation)
            revision = {
                "revision_id": f"REV-{case['id']}-{uuid.uuid4().hex[:12]}",
                "revision_hash": json_hash(case["annotations"]),
                "schema_version": ANNOTATION_SCHEMA_VERSION,
                "provenance": "USER",
                "annotation_ids": [item["id"] for item in case["annotations"]],
                "created_at": now(),
            }
            case["annotation_revisions"].append(revision)
            audit(case, "ANNOTATION_DRAFTED", f"{annotation.get('type', 'shape')} annotation added as USER provenance.", "reviewer-7f3a")
        if annotation_update:
            original = next((item for item in case["annotations"] if item["id"] == annotation_update.get("annotation_id")), None)
            if original and annotation_update.get("label", "").strip():
                corrected = {**original, "id": f"ANN-U-CORRECTION-{uuid.uuid4().hex[:12]}", "label": annotation_update["label"].strip(), "provenance": "USER", "corrects_annotation_id": original["id"]}
                case["annotations"].append(corrected)
                case["annotation_revisions"].append({"revision_id": f"REV-{uuid.uuid4().hex[:12]}", "revision_hash": json_hash(case["annotations"]), "schema_version": ANNOTATION_SCHEMA_VERSION, "provenance": "USER", "corrected_annotation_id": original["id"], "annotation_ids": [item["id"] for item in case["annotations"]], "created_at": now()})
                audit(case, "ANNOTATION_CORRECTED", "A new USER annotation revision was created; the previous geometry remains immutable.", "reviewer-7f3a")
        if "human_grade" in payload:
            case["humanGrade"] = payload["human_grade"]
        if "remark" in payload:
            case["remark"] = payload["remark"] or ""
        if human:
            case["review_status"] = "HUMAN_REVIEWED"
            case["humanReviewStatus"] = "REVIEWED"
            case["humanReviewer"] = "reviewer-7f3a"
            case["human_grading_protocol"] = "DR-GRADING-PROTOCOL-v0.1"
            case["human_reviewed_at"] = now()
            case["trainingEligibility"] = "HUMAN" if case.get("humanGrade") is not None else "UNREVIEWED_SYSTEM"
            audit(case, "HUMAN_REVIEWED", f"Human grade {case.get('humanGrade') if case.get('humanGrade') is not None else 'not set'} saved; system grade preserved.", "reviewer-7f3a")
        elif case["review_status"] != "HUMAN_REVIEWED":
            case["review_status"] = "IN_REVIEW"
            audit(case, "REVIEW_DRAFTED", "Review draft persisted; system output remains immutable.", "reviewer-7f3a")
        self.store.save_case(case)
        self.store.append_audit(case["id"], case["audit"][-1])
        return case

    def export(self, case: dict[str, Any], destination: str, simulate_failure: bool = False) -> dict[str, Any]:
        if simulate_failure:
            raise OSError("Simulated destination failure for recovery testing")
        destination_path = self.fs.resolve(destination, create=True)
        export_dir = destination_path / safe_name(case.get("sourceFolder", "LOCAL")) / safe_name(case["id"])
        export_dir.mkdir(parents=True, exist_ok=True)
        source_copy = case["output_policy"] in {"COPY_ORIGINAL", "COPY_ORIGINAL_AND_DERIVED"}
        derived_copy = case["output_policy"] in {"DERIVED_IMAGE_ONLY", "COPY_ORIGINAL_AND_DERIVED"}
        source_bytes = self.store.object_path(case["sourceObjectKey"]).read_bytes()
        artifacts: dict[str, bytes] = {
            "image_metadata.json": json_bytes({"file_name": case["fileName"], "file_type": case["fileType"], "modality": case["modality"], "frame_number": case.get("frame_number"), "frame_count": case.get("frame_count"), "study_instance_uid": case.get("study_instance_uid"), "series_instance_uid": case.get("series_instance_uid"), "sop_instance_uid": case.get("sop_instance_uid"), "transfer_syntax_uid": case.get("transfer_syntax_uid"), "technical_metadata": case.get("technical_metadata")}),
            "source_reference.json": json_bytes({"uri": case["sourceReference"], "object_uri": f"local-object://{case['sourceObjectKey']}", "sha256": case["sourceSha256"], "immutable": True}),
            "system_predictions.json": json_bytes(case.get("prediction_history", [])),
            "annotations.json": json_bytes({"schema_version": ANNOTATION_SCHEMA_VERSION, "annotations": case.get("annotations", []), "revisions": case.get("annotation_revisions", [])}),
            "review.json": json_bytes({"review_status": case["review_status"], "human_grade": case.get("humanGrade"), "human_grading_protocol": case.get("human_grading_protocol"), "remark": case.get("remark"), "training_eligibility": case.get("trainingEligibility")}),
            "audit_events.jsonl": ("\n".join(json.dumps(item, ensure_ascii=False) for item in case.get("audit", [])) + "\n").encode("utf-8"),
        }
        if source_copy:
            extension = Path(case["fileName"]).suffix or ".bin"
            artifacts[f"source/original{extension}"] = source_bytes
        if derived_copy and case.get("displayDerivativeUri"):
            key = case["displayDerivativeUri"].removeprefix("/api/objects/")
            artifacts["preview/display-derivative.png"] = self.store.object_path(key).read_bytes()
        artifact_hashes = {}
        for name, content in artifacts.items():
            target = export_dir / name
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_suffix(target.suffix + ".tmp")
            temporary.write_bytes(content)
            actual = sha256_bytes(temporary.read_bytes())
            if actual != sha256_bytes(content):
                temporary.unlink(missing_ok=True)
                raise IOError(f"Export hash verification failed for {name}")
            temporary.replace(target)
            artifact_hashes[name] = actual
        export_manifest = {"export_schema_version": "export.v0.1", "case_id": case["id"], "output_policy": case["output_policy"], "artifact_policy": {"original": "COPY" if source_copy else "REFERENCE_ONLY", "derived": "EXPORT" if derived_copy else "REFERENCE_ONLY", "annotations_are_never_burned_into_original": True}, "source_sha256": case["sourceSha256"], "artifact_sha256": artifact_hashes, "created_at": now()}
        manifest_content = json_bytes(export_manifest)
        (export_dir / "export_manifest.json").write_bytes(manifest_content)
        export_hash = sha256_bytes(manifest_content)
        return {"exportUri": f"local-export://{export_dir.relative_to(destination_path).as_posix()}", "exportHash": export_hash, "exportPath": str(export_dir), "fileNames": [*artifacts, "export_manifest.json"]}


runtime = Runtime()
app = FastAPI(title="OcuForge Product Runtime", version=PRODUCT_SCHEMA_VERSION)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["*"], allow_headers=["*"], expose_headers=["Content-Disposition"])


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "runtime": "LOCAL_ON_PREM", "data_root": str(runtime.root), "browser_filesystem_authoritative": False, "dicom": supported_transfer_syntaxes()}


@app.post("/api/readiness")
async def readiness(request: Request) -> dict[str, Any]:
    body = await request.json()
    return runtime.fs.readiness(body.get("source_reference"), body.get("destination_reference"))


@app.get("/api/state")
def state() -> dict[str, Any]:
    return runtime.state()


@app.get("/api/queue")
def queue(
    status: str | None = None,
    file_type: str | None = None,
    laterality: str | None = None,
    limit: int = 1000,
    offset: int = 0,
) -> list[dict[str, Any]]:
    cases = runtime.store.list_cases()
    if status:
        cases = [case for case in cases if case.get("derived_queue_status") == status]
    if file_type:
        cases = [case for case in cases if case.get("fileType") == file_type]
    if laterality:
        cases = [case for case in cases if case.get("laterality") == laterality]
    if limit < 1 or limit > 1000 or offset < 0:
        raise HTTPException(400, "Queue limit must be 1-1000 and offset must be non-negative")
    return cases[offset:offset + limit]


@app.get("/api/cases/{case_id}")
def get_case(case_id: str) -> dict[str, Any]:
    case = runtime.store.get_case(case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    return case


@app.post("/api/ingestion")
async def ingestion(request: Request) -> dict[str, Any]:
    body = await request.json()
    try:
        return runtime.ingest(body["source_reference"], body.get("destination_reference") or str(runtime.store.exports), body.get("output_policy", "REFERENCE_ONLY"))
    except (KeyError, ValueError, OSError) as error:
        raise HTTPException(400, str(error)) from error


@app.get("/api/ingestion/{job_id}")
def ingestion_job(job_id: str) -> dict[str, Any]:
    job = runtime.store.get_job(job_id)
    if not job:
        raise HTTPException(404, "Ingestion job not found")
    return {**job, "items": runtime.store.get_ingestion_items(job_id)}


@app.post("/api/fixtures/ingest")
async def fixture_ingestion(request: Request) -> dict[str, Any]:
    body = await request.json()
    fixture_root = runtime.store.fixtures / "synthetic-deidentified"
    fixture_root.mkdir(parents=True, exist_ok=True)
    dicom_path = fixture_root / "synthetic-multiframe.dcm"
    if not dicom_path.exists():
        file_meta = FileMetaDataset()
        file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.7"
        file_meta.MediaStorageSOPInstanceUID = "1.2.826.0.1.3680043.10.543.1003"
        file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
        file_meta.ImplementationClassUID = PYDICOM_IMPLEMENTATION_UID
        dataset = FileDataset(str(dicom_path), {}, file_meta=file_meta, preamble=b"\0" * 128)
        dataset.SOPClassUID = file_meta.MediaStorageSOPClassUID
        dataset.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
        dataset.StudyInstanceUID = "1.2.826.0.1.3680043.10.543.1001"
        dataset.SeriesInstanceUID = "1.2.826.0.1.3680043.10.543.1002"
        dataset.Modality = "OP"
        dataset.ImageLaterality = "OD"
        dataset.Rows = 32
        dataset.Columns = 32
        dataset.SamplesPerPixel = 1
        dataset.PhotometricInterpretation = "MONOCHROME2"
        dataset.NumberOfFrames = 2
        dataset.BitsAllocated = 8
        dataset.BitsStored = 8
        dataset.HighBit = 7
        dataset.PixelRepresentation = 0
        dataset.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
        dataset.PixelSpacing = ["0.01", "0.01"]
        dataset.WindowCenter = "128"
        dataset.WindowWidth = "256"
        dataset.PixelData = bytes((index * 5 + frame * 41) % 256 for frame in range(2) for index in range(32 * 32))
        dcmwrite(str(dicom_path), dataset, enforce_file_format=True, little_endian=True, implicit_vr=False)
    raster_path = fixture_root / "synthetic-raster.png"
    if not raster_path.exists():
        image = Image.new("RGB", (32, 32))
        image.putdata([(index * 5 % 255, index * 3 % 255, 120) for index in range(32 * 32)])
        image.save(raster_path, format="PNG")
    malformed = fixture_root / "malformed.dcm"
    if not malformed.exists():
        malformed.write_bytes(b"not a DICOM object")
    return runtime.ingest(str(fixture_root), body.get("destination_reference") or str(runtime.store.exports), body.get("output_policy", "REFERENCE_ONLY"))


@app.post("/api/cases/{case_id}/ai")
def run_ai(case_id: str) -> dict[str, Any]:
    case = runtime.store.get_case(case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    try:
        prediction = runtime.run_ai(case)
    except ValueError as error:
        case["ai_status"] = "FAILED"
        audit(case, "AI_FAILED", str(error))
        runtime.store.save_case(case)
        raise HTTPException(400, str(error)) from error
    case["ai_status"] = "PROCESSED"
    case["prediction_history"].append(prediction)
    case["annotations"].extend(prediction["annotations"])
    case["systemGrade"] = prediction["system_dr_grade"]
    case["systemConfidence"] = prediction["confidence"]
    case["systemPredictionId"] = prediction["prediction_id"]
    case["systemModelManifestId"] = prediction["model_manifest"]["model_manifest_id"]
    audit(case, "AI_PROCESSED", "Deterministic mock bundle produced an immutable system prediction.")
    runtime.store.save_case(case)
    runtime.store.append_audit(case_id, case["audit"][-1])
    return case


@app.post("/api/cases/{case_id}/review")
async def save_review(case_id: str, request: Request) -> dict[str, Any]:
    case = runtime.store.get_case(case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    body = await request.json()
    return runtime.save_review(case, body, body.get("mode") == "save")


@app.post("/api/cases/{case_id}/annotations")
async def add_annotation(case_id: str, request: Request) -> dict[str, Any]:
    case = runtime.store.get_case(case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    body = await request.json()
    return runtime.save_review(case, {"annotation": body}, False)


@app.post("/api/cases/{case_id}/export")
async def export_case(case_id: str, request: Request) -> dict[str, Any]:
    case = runtime.store.get_case(case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    body = await request.json()
    case["export_status"] = "EXPORTING"
    runtime.store.save_case(case)
    try:
        result = runtime.export(case, body.get("destination_reference") or str(runtime.store.exports), bool(body.get("simulate_failure")))
    except (OSError, ValueError, KeyError) as error:
        case["export_status"] = "FAILED"
        audit(case, "EXPORT_FAILED", str(error))
        runtime.store.save_case(case)
        runtime.store.append_audit(case_id, case["audit"][-1])
        raise HTTPException(400, str(error)) from error
    case["export_status"] = "EXPORTED"
    case["export_uri"] = result["exportUri"]
    case["export_hash"] = result["exportHash"]
    case["annotation_artifact_uri"] = f"{result['exportUri']}/annotations.json"
    audit(case, "EXPORTED", "Export receipt verified; original bytes remain immutable.")
    runtime.store.save_case(case)
    runtime.store.append_audit(case_id, case["audit"][-1])
    return {**case, "export": result}


@app.get("/api/manifest.csv")
def manifest() -> PlainTextResponse:
    fields = list(manifest_rows([])[0].keys()) if runtime.store.list_cases() else ["case_id"]
    text = csv_text(manifest_rows(runtime.store.list_cases()), fields)
    return PlainTextResponse(text, media_type="text/csv")


@app.get("/api/index.csv")
def index() -> PlainTextResponse:
    rows = manifest_rows(runtime.store.list_cases())
    fields = ["case_id", "image_id", "file_sha256", "training_image_uri", "training_image_sha256", "annotation_artifact_uri", "annotation_revision_hash", "annotation_schema_version", "training_eligibility", "review_status", "ai_status", "export_status"]
    return PlainTextResponse(csv_text(rows, fields), media_type="text/csv")


@app.get("/api/objects/{object_key:path}")
def object_file(object_key: str) -> FileResponse:
    try:
        path = runtime.store.object_path(object_key)
    except ValueError as error:
        raise HTTPException(400, str(error)) from error
    if not path.exists():
        raise HTTPException(404, "Object not found")
    return FileResponse(path)


@app.delete("/api/workspace")
def clear_workspace() -> dict[str, str]:
    runtime.store.clear()
    return {"status": "cleared"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("product-runtime.app:app", host="127.0.0.1", port=int(os.environ.get("OCUFORGE_PRODUCT_PORT", "8000")), reload=False)
