"""IDRiD R3 ROI inputs and target semantics.

These records are deliberately separate from the global DR and MIL contracts.  A target
record describes only evidence available for the selected ROI; it never turns missing
annotation into a negative target.
"""

from pathlib import PurePosixPath
from typing import Literal

from pydantic import Field, field_validator, model_validator

from .models import ID, Prob, SHA, Strict


SUPPORTED_LESION_CLASSES = (
    "MICROANEURYSM",
    "INTRARETINAL_HEMORRHAGE",
    "HARD_EXUDATE",
    "SOFT_EXUDATE",
)
SupportedLesion = Literal[
    "MICROANEURYSM",
    "INTRARETINAL_HEMORRHAGE",
    "HARD_EXUDATE",
    "SOFT_EXUDATE",
]

R3InputProvenance = Literal[
    "IDRID_MASK_FOREGROUND_BBOX",
    "PRESENT_EMPTY_MASK_ROI",
    "EXPLICIT_CLEAN_NEGATIVE_ROI",
    "UNANNOTATED_OR_UNSUPPORTED_REGION",
]
R3MaskStatus = Literal["PRESENT_NONEMPTY", "PRESENT_EMPTY", "MISSING", "UNANNOTATED"]
R3ROIPresence = Literal["PRESENT", "ABSENT", "UNKNOWN"]
R3TargetSemantic = Literal[
    "SUPPORTED_LESION",
    "NO_SUPPORTED_LESION_IN_ROI",
    "UNKNOWN_OR_UNSUPPORTED_FINDING",
    "WEAK_NEGATIVE_FOR_SUPPORTED_CLASS",
]


def _safe_relative_uri(value: str | None) -> str | None:
    if value is None:
        return None
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or ":" in value or "\\" in value:
        raise ValueError("R3 paths must be non-empty relative POSIX paths")
    return value


class R3ROIGeometry(Strict):
    """Pixel and normalized ROI geometry retained from the source derivation."""

    bbox_xyxy_px: tuple[int, int, int, int]
    bbox_xyxy_norm: tuple[Prob, Prob, Prob, Prob]
    provenance: Literal["IDRID_EXACT_MASK_FOREGROUND_BBOX", "EXPLICIT_ROI_PROVENANCE"]

    @model_validator(mode="after")
    def positive_extent(self):
        x0, y0, x1, y1 = self.bbox_xyxy_px
        nx0, ny0, nx1, ny1 = self.bbox_xyxy_norm
        if x0 < 0 or y0 < 0 or x1 <= x0 or y1 <= y0:
            raise ValueError("ROI pixel geometry must have a positive in-bounds-ready extent")
        if nx1 <= nx0 or ny1 <= ny0:
            raise ValueError("ROI normalized geometry must have a positive extent")
        return self


class R3MaskEvidence(Strict):
    """One supported-mask provenance entry for the source image and selected ROI."""

    lesion_class: SupportedLesion
    status: R3MaskStatus
    roi_presence: R3ROIPresence
    source_mask_relative_uri: str | None = None
    source_mask_sha256: SHA | None = None

    _validate_uri = field_validator("source_mask_relative_uri")(_safe_relative_uri)

    @model_validator(mode="after")
    def provenance_requirements(self):
        present = self.status in ["PRESENT_NONEMPTY", "PRESENT_EMPTY"]
        has_path_and_hash = self.source_mask_relative_uri is not None and self.source_mask_sha256 is not None
        if present != has_path_and_hash:
            raise ValueError("Present mask evidence requires both source path and SHA-256")
        if self.status == "PRESENT_EMPTY" and self.roi_presence != "ABSENT":
            raise ValueError("A present-but-empty mask can only have ABSENT ROI presence")
        if self.status in ["MISSING", "UNANNOTATED"] and self.roi_presence != "UNKNOWN":
            raise ValueError("Missing or unannotated masks must remain UNKNOWN in the ROI")
        return self


class R3ROIInput(Strict):
    """A crop/input row for the separate IDRiD ROI classifier."""

    schema_version: Literal["r3_roi_input.v0.1"] = "r3_roi_input.v0.1"
    dataset_id: ID
    source_type: Literal["PUBLIC_IDRID", "SYNTHETIC_FIXTURE"]
    roi_id: ID
    source_image_id: ID
    source_image_sha256: SHA
    source_image_relative_uri: str
    roi_image_sha256: SHA
    roi_image_relative_uri: str
    source_width_px: int = Field(gt=1)
    source_height_px: int = Field(gt=1)
    roi_width_px: int = Field(gt=1)
    roi_height_px: int = Field(gt=1)
    released_split: Literal["TRAIN", "TEST"]
    roi_class: SupportedLesion | None = None
    roi_provenance: R3InputProvenance
    mask_coverage: Literal["COMPLETE_SUPPORTED_MASK_COVERAGE", "INCOMPLETE_SUPPORTED_MASK_COVERAGE"]
    mask_evidence: list[R3MaskEvidence] = Field(min_length=4, max_length=4)
    geometry: R3ROIGeometry
    global_semantic: Literal["NOT_PROVIDED", "GLOBAL_NO_DR", "GLOBAL_DR_PRESENT_OR_UNCERTAIN"] = (
        "NOT_PROVIDED"
    )

    _validate_source_uri = field_validator("source_image_relative_uri")(_safe_relative_uri)
    _validate_roi_uri = field_validator("roi_image_relative_uri")(_safe_relative_uri)

    @model_validator(mode="after")
    def semantic_and_geometry_integrity(self):
        if self.dataset_id != "idrid_v1":
            raise ValueError("R3 is restricted to the IDRiD dataset identity")
        classes = [entry.lesion_class for entry in self.mask_evidence]
        if set(classes) != set(SUPPORTED_LESION_CLASSES) or len(classes) != len(set(classes)):
            raise ValueError("R3 input must contain exactly one mask evidence row per supported class")

        x0, y0, x1, y1 = self.geometry.bbox_xyxy_px
        if x1 > self.source_width_px or y1 > self.source_height_px:
            raise ValueError("ROI geometry exceeds source image dimensions")
        expected_norm = (
            x0 / self.source_width_px,
            y0 / self.source_height_px,
            x1 / self.source_width_px,
            y1 / self.source_height_px,
        )
        if any(abs(a - b) > 1e-6 for a, b in zip(self.geometry.bbox_xyxy_norm, expected_norm)):
            raise ValueError("Normalized ROI geometry does not match source dimensions")

        evidence = {entry.lesion_class: entry for entry in self.mask_evidence}
        if self.mask_coverage == "COMPLETE_SUPPORTED_MASK_COVERAGE":
            if any(entry.status in ["MISSING", "UNANNOTATED"] or entry.roi_presence == "UNKNOWN" for entry in evidence.values()):
                raise ValueError("Complete mask coverage cannot contain missing or unknown evidence")
        elif all(entry.status not in ["MISSING", "UNANNOTATED"] and entry.roi_presence != "UNKNOWN" for entry in evidence.values()):
            raise ValueError("Complete mask evidence must be declared as complete coverage")

        if self.roi_provenance == "IDRID_MASK_FOREGROUND_BBOX":
            if self.roi_class is None or self.geometry.provenance != "IDRID_EXACT_MASK_FOREGROUND_BBOX":
                raise ValueError("Mask-derived ROI requires a supported class and exact mask geometry")
            selected = evidence[self.roi_class]
            if selected.status != "PRESENT_NONEMPTY" or selected.roi_presence != "PRESENT":
                raise ValueError("Mask-derived ROI requires present non-empty source-mask evidence")
        elif self.roi_provenance == "PRESENT_EMPTY_MASK_ROI":
            if self.roi_class is None:
                raise ValueError("Present-empty ROI evidence requires the supported class it evaluates")
            selected = evidence[self.roi_class]
            if selected.status != "PRESENT_EMPTY" or selected.roi_presence != "ABSENT":
                raise ValueError("Weak-negative ROI evidence requires an explicit present-empty mask")
        elif self.roi_provenance == "EXPLICIT_CLEAN_NEGATIVE_ROI":
            if self.roi_class is not None or self.mask_coverage != "COMPLETE_SUPPORTED_MASK_COVERAGE":
                raise ValueError("Clean negative ROI requires complete supported-mask coverage")
            if any(entry.roi_presence != "ABSENT" for entry in evidence.values()):
                raise ValueError("Clean negative ROI requires explicit absence evidence for all supported classes")
        elif self.roi_class is not None:
            raise ValueError("Unknown or unsupported ROI cannot declare a supported class")
        return self


class R3ROITarget(Strict):
    """A target row whose semantic state is checked against an R3 input row."""

    schema_version: Literal["r3_roi_target.v0.1"] = "r3_roi_target.v0.1"
    dataset_id: ID
    roi_id: ID
    source_image_id: ID
    source_image_sha256: SHA
    released_split: Literal["TRAIN", "TEST"]
    target_semantic: R3TargetSemantic
    target_class: SupportedLesion | None = None
    global_semantic: Literal["NOT_PROVIDED", "GLOBAL_NO_DR", "GLOBAL_DR_PRESENT_OR_UNCERTAIN"] = (
        "NOT_PROVIDED"
    )

    @model_validator(mode="after")
    def target_shape(self):
        if self.dataset_id != "idrid_v1":
            raise ValueError("R3 targets are restricted to the IDRiD dataset identity")
        if self.target_semantic in ["SUPPORTED_LESION", "WEAK_NEGATIVE_FOR_SUPPORTED_CLASS"]:
            if self.target_class is None:
                raise ValueError("Class-specific R3 targets require target_class")
        elif self.target_class is not None:
            raise ValueError("Non-class-specific R3 targets cannot declare target_class")
        return self


R3_TYPES = {
    "r3_roi_input.v0.1": R3ROIInput,
    "r3_roi_target.v0.1": R3ROITarget,
}


def validate_r3_manifests(inputs, targets):
    """Validate complete input/target inventories and released image split identity."""

    inputs = [x if isinstance(x, R3ROIInput) else R3ROIInput.model_validate(x) for x in inputs]
    targets = [x if isinstance(x, R3ROITarget) else R3ROITarget.model_validate(x) for x in targets]
    if not inputs or not targets:
        raise ValueError("R3 input and target manifests must both be non-empty")
    input_by_roi = {row.roi_id: row for row in inputs}
    target_by_roi = {row.roi_id: row for row in targets}
    if len(input_by_roi) != len(inputs) or len(target_by_roi) != len(targets):
        raise ValueError("Duplicate R3 ROI ID")
    if set(input_by_roi) != set(target_by_roi):
        raise ValueError("R3 target inventory must exactly match the input inventory")

    image_identity = {}
    source_hash_identity = {}
    source_hashes = {}
    roi_hashes = {}
    for row in inputs:
        identity = image_identity.setdefault(row.source_image_id, (row.source_image_sha256, row.released_split))
        if identity != (row.source_image_sha256, row.released_split):
            raise ValueError("IDRiD source image identity or released split changed across ROI rows")
        previous_source_id = source_hash_identity.get(row.source_image_sha256)
        if previous_source_id is not None and previous_source_id != row.source_image_id:
            raise ValueError("Different IDRiD source image IDs share one image hash")
        source_hash_identity[row.source_image_sha256] = row.source_image_id
        previous_source_split = source_hashes.get(row.source_image_sha256)
        if previous_source_split is not None and previous_source_split != row.released_split:
            raise ValueError("R3 source image hash leaks across released train/test split")
        source_hashes[row.source_image_sha256] = row.released_split
        previous_split = roi_hashes.get(row.roi_image_sha256)
        if previous_split is not None and previous_split != row.released_split:
            raise ValueError("R3 ROI image hash leaks across released train/test split")
        roi_hashes[row.roi_image_sha256] = row.released_split

        target = target_by_roi[row.roi_id]
        if (
            target.dataset_id != row.dataset_id
            or target.source_image_id != row.source_image_id
            or target.source_image_sha256 != row.source_image_sha256
            or target.released_split != row.released_split
        ):
            raise ValueError("R3 target disagrees with input dataset, image identity, or split")
        evidence = {entry.lesion_class: entry for entry in row.mask_evidence}
        if target.target_semantic == "SUPPORTED_LESION":
            if row.roi_provenance != "IDRID_MASK_FOREGROUND_BBOX" or target.target_class != row.roi_class:
                raise ValueError("Supported-lesion target is not backed by the matching source mask ROI")
        elif target.target_semantic == "WEAK_NEGATIVE_FOR_SUPPORTED_CLASS":
            if row.roi_provenance != "PRESENT_EMPTY_MASK_ROI" or target.target_class != row.roi_class:
                raise ValueError("Weak negative requires matching present-empty mask provenance")
            if evidence[target.target_class].status != "PRESENT_EMPTY":
                raise ValueError("Weak negative target is missing present-empty mask evidence")
        elif target.target_semantic == "NO_SUPPORTED_LESION_IN_ROI":
            if row.roi_provenance != "EXPLICIT_CLEAN_NEGATIVE_ROI":
                raise ValueError("ROI negative target requires explicit clean-negative provenance")
        elif row.roi_provenance != "UNANNOTATED_OR_UNSUPPORTED_REGION":
            raise ValueError("Unknown target requires unknown or unsupported input provenance")

    train_count = sum(row.released_split == "TRAIN" for row in inputs)
    test_count = sum(row.released_split == "TEST" for row in inputs)
    semantic_counts = {
        semantic: sum(target.target_semantic == semantic for target in targets)
        for semantic in [
            "SUPPORTED_LESION",
            "NO_SUPPORTED_LESION_IN_ROI",
            "UNKNOWN_OR_UNSUPPORTED_FINDING",
            "WEAK_NEGATIVE_FOR_SUPPORTED_CLASS",
        ]
    }
    return {
        "input_rows": len(inputs),
        "target_rows": len(targets),
        "train_rows": train_count,
        "test_rows": test_count,
        "semantic_counts": semantic_counts,
        "source_images": len(image_identity),
        "released_split_preserved": True,
    }
