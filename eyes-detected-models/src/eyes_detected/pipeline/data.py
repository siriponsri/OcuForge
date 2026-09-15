import hashlib, json, os
from pathlib import Path
from PIL import Image
from pydantic import Field, model_validator
from typing import Literal
from eyes_contracts.models import Strict, ID, ImageManifest, DatasetManifest
from eyes_contracts.validators import read_records, check_splits


class Target(Strict):
    image_id: ID
    dr_grade: int | None = Field(default=None, ge=0, le=4, strict=True)
    binary_dr: int | None = Field(default=None, ge=0, le=1, strict=True)
    lesions: list[int | None] | None = Field(default=None, min_length=7, max_length=7)
    gradable: int | None = Field(default=None, ge=0, le=1, strict=True)
    source: Literal["SYNTHETIC", "IMPORTED_PUBLIC_GT", "DOCTOR_EXPERIENCE", "EXPERT_ADJUDICATED"]

    @model_validator(mode="after")
    def semantics(self):
        if self.source == "DOCTOR_EXPERIENCE" and (self.dr_grade is not None or self.lesions is not None):
            raise ValueError("Experience labels cannot supply ordinal or lesion targets")
        if self.dr_grade is not None and self.binary_dr is not None:
            raise ValueError("Declare one primary task; no implicit binary/ordinal conversion")
        if self.lesions and any(v not in [0, 1, None] for v in self.lesions):
            raise ValueError("Lesions require binary presence or null")
        return self


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_path(root, relative):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("Missing file or path escapes declared root")
    return path


def load_images(path, dataset_path=None, cloud=False):
    cloud = cloud or os.environ.get("OCUFORGE_EXECUTION_ZONE") == "PUBLIC_CLOUD"
    images = read_records(path)
    if not images or not all(isinstance(x, ImageManifest) for x in images):
        raise ValueError("Image manifest JSONL required")
    check_splits(images)
    if any(
        i.source_type == "LOCAL_PRIVATE" and i.split != "UNASSIGNED" and not i.patient_pseudo_id
        for i in images
    ):
        raise ValueError("Private data requires patient grouping before training/evaluation")
    dataset = None
    if dataset_path:
        import yaml

        dataset = DatasetManifest.model_validate(
            yaml.safe_load(Path(dataset_path).read_text(encoding="utf-8"))
        )
        if any(i.dataset_id != dataset.dataset_id or i.source_type != dataset.source_type for i in images):
            raise ValueError("Image/dataset identity mismatch")
    if cloud:
        if (
            dataset is None
            or dataset.source_type == "LOCAL_PRIVATE"
            or not dataset.cloud_eligible
            or dataset.license_status not in ["REVIEWED", "SYNTHETIC"]
        ):
            raise ValueError("Cloud requires reviewed eligible PUBLIC/SYNTHETIC dataset")
        if any(not i.cloud_eligible or i.source_type not in ["PUBLIC", "SYNTHETIC"] for i in images):
            raise ValueError("Cloud data gate refused image")
    return images, dataset


def load_targets(path, images):
    rows = [
        Target.model_validate(json.loads(line))
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    index = {r.image_id: r for r in rows}
    ids = {i.image_id for i in images}
    if len(index) != len(rows) or not set(index) <= ids:
        raise ValueError("Duplicate or unknown target image ID")
    for im in images:
        if (
            im.image_id in index
            and im.source_type == "SYNTHETIC"
            and index[im.image_id].source != "SYNTHETIC"
        ):
            raise ValueError("Synthetic images require synthetic target provenance")
    return index


def audit(manifest, data_root, out, dataset_path=None, cloud=False):
    images, dataset = load_images(manifest, dataset_path, cloud)
    rows = []
    failures = 0
    for im in images:
        status = "OK"
        try:
            path = safe_path(data_root, im.relative_uri)
            if sha256(path) != im.file_sha256:
                raise ValueError("HASH_MISMATCH")
            with Image.open(path) as img:
                img.load()
                if img.size != (im.width_px, im.height_px):
                    raise ValueError("DIMENSION_MISMATCH")
                if img.mode != "RGB":
                    raise ValueError("RGB_REQUIRED")
        except (ValueError, OSError):
            status = "INVALID_IMAGE"
            failures += 1
        rows.append(
            {
                "image_id": im.image_id,
                "status": status,
                "width": im.width_px,
                "height": im.height_px,
                "site": im.site_id,
                "camera": im.camera_model,
                "split": im.split,
            }
        )
    report = {
        "images": len(images),
        "failures": failures,
        "rows": rows,
        "license_status": dataset.license_status if dataset else "UNKNOWN",
        "cloud_checked": cloud,
    }
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    if failures:
        raise ValueError(f"Audit failed for {failures} image(s); inspect local audit report")
    return report
