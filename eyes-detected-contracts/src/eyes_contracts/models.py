"""Versioned, extra-field-forbidden contracts. No training or CVAT dependencies."""

from typing import Annotated, Literal
from pathlib import PurePosixPath
from pydantic import BaseModel, ConfigDict, Field, model_validator

ID = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")]
SHA = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
Prob = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
Split = Literal["TRAIN", "VAL", "TEST", "SENTINEL", "UNASSIGNED"]
Origin = Literal[
    "AI_SUGGESTED",
    "CLINICIAN_CONFIRMED",
    "CLINICIAN_CORRECTED",
    "CLINICIAN_ADDED",
    "EXPERT_ADJUDICATED",
    "IMPORTED_PUBLIC_GT",
]
Review = Literal["DRAFT", "SUBMITTED", "NEEDS_REVIEW", "ADJUDICATED", "LOCKED", "REJECTED"]
Modality = Literal["UWF", "CFP", "OCT", "OTHER"]
POLICY = {
    "microaneurysm": ["point"],
    "intraretinal_hemorrhage": ["polygon", "box"],
    "hard_exudate": ["polygon", "mask"],
    "cotton_wool_spot": ["polygon", "mask"],
    "nvd": ["polygon"],
    "nve": ["polygon"],
    "irma": ["polyline", "polygon"],
    "venous_beading": ["polyline", "polygon"],
    "vitreous_hemorrhage": ["polygon", "image_presence"],
    "retinal_detachment": ["polygon", "image_presence"],
    "laser_scar": ["polygon"],
    "optic_disc": ["ellipse", "mask"],
    "fovea": ["point"],
    "dr_grade": ["image_presence"],
}
Label = Literal[
    "microaneurysm",
    "intraretinal_hemorrhage",
    "hard_exudate",
    "cotton_wool_spot",
    "nvd",
    "nve",
    "irma",
    "venous_beading",
    "vitreous_hemorrhage",
    "retinal_detachment",
    "laser_scar",
    "optic_disc",
    "fovea",
    "dr_grade",
]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, validate_default=True)


class BinaryAssessment(Strict):
    value: Literal["DR", "NO_DR"]
    source: Literal["DOCTOR_EXPERIENCE"] = "DOCTOR_EXPERIENCE"
    verification: Literal["USER_REPORTED_NOT_ADJUDICATED"] = "USER_REPORTED_NOT_ADJUDICATED"
    protocol_id: ID | None = None
    ordinal_grade_available: Literal[False] = False
    localized_labels_available: Literal[False] = False


class ImageManifest(Strict):
    schema_version: Literal["image_manifest.v0.1"] = "image_manifest.v0.1"
    image_id: ID
    dataset_id: ID
    file_sha256: SHA
    relative_uri: str
    patient_pseudo_id: ID | None = None
    eye_id: ID | None = None
    visit_id: ID | None = None
    laterality: Literal["OD", "OS", "UNKNOWN"] = "UNKNOWN"
    modality: Modality = "UWF"
    camera_make: ID = "UNKNOWN"
    camera_model: ID = "UNKNOWN"
    width_px: Annotated[int, Field(gt=1)]
    height_px: Annotated[int, Field(gt=1)]
    site_id: ID = "SYNTHETIC"
    acquisition_time_bucket: str | None = None
    split: Split = "UNASSIGNED"
    cloud_eligible: bool = False
    source_type: Literal["SYNTHETIC", "PUBLIC", "LOCAL_PRIVATE"] = "LOCAL_PRIVATE"
    binary_assessment: BinaryAssessment | None = None

    @model_validator(mode="after")
    def safety(self):
        p = PurePosixPath(self.relative_uri)
        if p.is_absolute() or ".." in p.parts or ":" in self.relative_uri or "\\" in self.relative_uri:
            raise ValueError("relative_uri must be a local relative POSIX path")
        if self.source_type == "LOCAL_PRIVATE" and self.cloud_eligible:
            raise ValueError("Local private data is local-only in starter")
        return self


class LabelScope(Strict):
    dr_grade: Literal["NONE", "IMAGE_LEVEL_ORDINAL", "IMAGE_LEVEL_BINARY_EXPERIENCE"]
    lesions: Literal["NONE", "IMAGE_LEVEL_MULTILABEL", "LOCALIZED"]
    pixel_masks: bool

    @model_validator(mode="after")
    def scope(self):
        if self.pixel_masks and self.lesions != "LOCALIZED":
            raise ValueError("Pixel masks require localized supervision")
        return self


class DatasetManifest(Strict):
    schema_version: Literal["dataset_manifest.v0.1"] = "dataset_manifest.v0.1"
    dataset_id: ID
    modality: list[Modality] = Field(min_length=1)
    source_type: Literal["SYNTHETIC", "PUBLIC", "LOCAL_PRIVATE"]
    label_scope: LabelScope
    split_unit: Literal["PATIENT", "EYE", "VISIT", "IMAGE"]
    license_status: Literal["NOT_REVIEWED", "REVIEWED", "RESTRICTED", "SYNTHETIC"]
    data_root_env: Annotated[str, Field(pattern=r"^[A-Z][A-Z0-9_]+$")]
    cloud_eligible: bool = False
    source_url: str | None = None

    @model_validator(mode="after")
    def scope(self):
        if "mmrdr" in self.dataset_id.lower() and self.label_scope.lesions == "LOCALIZED":
            raise ValueError("MMRDR lesions are image-level presence, not localized")
        if self.source_type == "LOCAL_PRIVATE" and self.cloud_eligible:
            raise ValueError("Local private data cannot leave hospital")
        if self.cloud_eligible and self.license_status not in ["REVIEWED", "SYNTHETIC"]:
            raise ValueError("Cloud eligibility requires reviewed license")
        return self


class Geometry(Strict):
    type: Literal["point", "box", "polygon", "polyline", "ellipse", "mask", "image_presence"]
    coordinates_norm: list[Prob] = Field(default_factory=list)
    mask_size: tuple[Annotated[int, Field(gt=0)], Annotated[int, Field(gt=0)]] | None = None
    mask_rle: list[Annotated[int, Field(ge=0)]] | None = None

    @model_validator(mode="after")
    def shape(self):
        c = self.coordinates_norm
        n = len(c)
        if self.type == "mask":
            if (
                n
                or self.mask_size is None
                or not self.mask_rle
                or sum(self.mask_rle) != self.mask_size[0] * self.mask_size[1]
            ):
                raise ValueError("Mask requires full row-major alternating 0/1 RLE and [height,width]")
        else:
            if self.mask_size is not None or self.mask_rle is not None:
                raise ValueError("Mask metadata on non-mask")
            if self.type == "point" and n != 2:
                raise ValueError("Point needs x,y")
            if self.type in ["box", "ellipse"] and (n != 4 or c[0] >= c[2] or c[1] >= c[3]):
                raise ValueError("Box/ellipse needs positive extent x0,y0,x1,y1")
            if self.type in ["polygon", "polyline"] and (n % 2 or n < (6 if self.type == "polygon" else 4)):
                raise ValueError("Invalid vertex count")
            if self.type == "image_presence" and n:
                raise ValueError("Presence has no coordinates")
            if self.type == "polygon":
                p = list(zip(c[::2], c[1::2]))
                area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(p, p[1:] + p[:1]))
                if abs(area) < 1e-12:
                    raise ValueError("Degenerate polygon")
        return self


class Candidate(Strict):
    object_id: ID
    label: Label
    geometry: Geometry
    confidence: Prob
    origin: Literal["AI_SUGGESTED"] = "AI_SUGGESTED"
    generator_kind: Literal["LOCALIZER", "SYNTHETIC_FIXTURE"]

    @model_validator(mode="after")
    def policy(self):
        if self.geometry.type not in POLICY[self.label]:
            raise ValueError("Geometry forbidden for label")
        if (
            self.label
            in [
                "nvd",
                "nve",
                "irma",
                "venous_beading",
                "vitreous_hemorrhage",
                "retinal_detachment",
                "laser_scar",
            ]
            and self.generator_kind != "SYNTHETIC_FIXTURE"
        ):
            raise ValueError("Manual-first lesion; no validated starter localizer")
        return self


class ProtocolRef(Strict):
    protocol_id: ID
    version: ID
    config_sha256: SHA


class DRPrediction(Strict):
    grading_protocol: ProtocolRef
    grade: Annotated[int, Field(ge=0, le=4)]
    ordinal_probs: list[Prob] = Field(min_length=4, max_length=4)
    confidence: Prob

    @model_validator(mode="after")
    def ordinal(self):
        p = self.ordinal_probs
        if any(a < b for a, b in zip(p, p[1:])) or self.grade != sum(x > 0.5 for x in p):
            raise ValueError("Non-monotone or inconsistent CORAL output")
        return self


class OOD(Strict):
    method: ID
    score: Annotated[float, Field(ge=0, allow_inf_nan=False)]
    abstain_recommended: bool


class Evidence(Strict):
    type: Literal["mil_attention"] = "mil_attention"
    patch_scores: list[Prob] = Field(min_length=1)
    disclaimer: Literal["MODEL_EVIDENCE_NOT_LESION_GROUND_TRUTH"] = "MODEL_EVIDENCE_NOT_LESION_GROUND_TRUTH"

    @model_validator(mode="after")
    def normalized(self):
        if abs(sum(self.patch_scores) - 1) > 1e-5:
            raise ValueError("Attention must sum to 1")
        return self


class Prediction(Strict):
    schema_version: Literal["prediction.v0.1"] = "prediction.v0.1"
    prediction_id: ID
    image_id: ID
    model_manifest_id: ID
    dr: DRPrediction | None = None
    lesion_presence: dict[str, Prob] = Field(default_factory=dict)
    objects: list[Candidate] = Field(default_factory=list)
    evidence: Evidence | None = None
    ood: OOD | None = None
    gradability_probability: Prob | None = None
    research_only: Literal[True] = True

    @model_validator(mode="after")
    def unique(self):
        if len({x.object_id for x in self.objects}) != len(self.objects):
            raise ValueError("Duplicate object ID")
        if any(x not in set(POLICY) | {"vb_irma", "nv"} for x in self.lesion_presence):
            raise ValueError("Unknown lesion-presence key")
        return self


class Event(Strict):
    geometry_snapshot: Geometry | None = None
    label_snapshot: Label | None = None
    event_id: ID
    origin: Origin
    review_status: Review
    actor_id_hash: ID
    timestamp: str
    action: Literal[
        "PROPOSE", "IMPORT", "CONFIRM", "CORRECT", "ADD", "SUBMIT", "REJECT", "ESCALATE", "ADJUDICATE", "LOCK"
    ]


class Annotation(Strict):
    schema_version: Literal["annotation.v0.1"] = "annotation.v0.1"
    annotation_id: ID
    image_id: ID
    label: Label
    geometry: Geometry
    origin: Origin
    parent_prediction_id: ID | None = None
    parent_object_id: ID | None = None
    source_model_version: ID | None = None
    annotator_id_hash: ID
    review_status: Review
    clinician_certainty: Literal["HIGH", "MEDIUM", "LOW", "NOT_RECORDED"] = "NOT_RECORDED"
    uncertain: bool = False
    grading_protocol: ProtocolRef | None = None
    dr_grade: Annotated[int, Field(ge=0, le=4)] | None = None
    gradability: Literal["GRADABLE", "PARTIALLY_GRADABLE", "UNGRADABLE", "UNKNOWN"] = "UNKNOWN"
    laterality: Literal["OD", "OS", "UNKNOWN"] = "UNKNOWN"
    referable_by_protocol: bool | None = None
    referable_protocol_id: ID | None = None
    confidence_if_ai: Prob | None = None
    created_at: str
    updated_at: str
    adjudicator: ID | None = None
    adjudication_timestamp: str | None = None
    history: list[Event] = Field(min_length=1)

    @model_validator(mode="after")
    def provenance(self):
        if self.geometry.type not in POLICY[self.label]:
            raise ValueError("Geometry forbidden for label")
        if self.label == "dr_grade" and self.grading_protocol is None:
            raise ValueError("Grading protocol reference required")
        if self.label != "dr_grade" and self.dr_grade is not None:
            raise ValueError("Grade requires dr_grade label")
        if self.gradability == "UNGRADABLE" and self.dr_grade is not None:
            raise ValueError("Ungradable is not a grade")
        if self.referable_by_protocol is not None and not self.referable_protocol_id:
            raise ValueError("Referability requires protocol")
        if self.origin in ["CLINICIAN_CONFIRMED", "CLINICIAN_CORRECTED"] and (
            not self.parent_prediction_id or not self.parent_object_id
        ):
            raise ValueError("AI review requires parent IDs")
        if self.origin == "AI_SUGGESTED" and self.review_status in ["ADJUDICATED", "LOCKED"]:
            raise ValueError("AI cannot be adjudicated ground truth")
        if self.origin == "EXPERT_ADJUDICATED" and (not self.adjudicator or not self.adjudication_timestamp):
            raise ValueError("Adjudicator metadata required")
        if self.review_status in ["ADJUDICATED", "LOCKED"] and self.origin not in [
            "EXPERT_ADJUDICATED",
            "IMPORTED_PUBLIC_GT",
        ]:
            raise ValueError("Finalized review requires expert or imported public provenance")
        if self.origin == "EXPERT_ADJUDICATED" and not any(e.action == "ADJUDICATE" for e in self.history):
            raise ValueError("Adjudication event missing")
        last = self.history[-1]
        if last.origin != self.origin or last.review_status != self.review_status:
            raise ValueError("History and current state disagree")
        if len({e.event_id for e in self.history}) != len(self.history):
            raise ValueError("Duplicate event")
        return self


class BatchItem(Strict):
    image_id: ID
    priority: Prob
    reasons: list[ID] = Field(min_length=1)
    locked_sentinel: bool = False
    split: Split = "UNASSIGNED"


class Selection(Strict):
    strategy: ID
    model_manifest_id: ID


class AnnotationBatch(Strict):
    schema_version: Literal["annotation_batch.v0.1"] = "annotation_batch.v0.1"
    batch_id: ID
    dataset_id: ID
    selection: Selection
    requested_n: Annotated[int, Field(gt=0)]
    purpose: Literal["TRAINABLE", "SENTINEL_EVALUATION"] = "TRAINABLE"
    items: list[BatchItem] = Field(min_length=1)

    @model_validator(mode="after")
    def integrity(self):
        if len(self.items) != self.requested_n or len({x.image_id for x in self.items}) != len(self.items):
            raise ValueError("Batch count or duplicate IDs")
        if self.purpose == "TRAINABLE" and any(
            x.locked_sentinel or x.split in ["SENTINEL", "VAL", "TEST"] for x in self.items
        ):
            raise ValueError("Evaluation split in trainable batch")
        if self.purpose == "SENTINEL_EVALUATION" and any(
            x.split != "SENTINEL" or not x.locked_sentinel for x in self.items
        ):
            raise ValueError("Sentinel task must contain locked sentinel only")
        return self


class ExperimentRun(Strict):
    schema_version: Literal["experiment_run.v0.1"] = "experiment_run.v0.1"
    run_id: ID
    timestamp: str
    git_sha: str
    docker_image: str
    config_hash: SHA
    dataset_manifest_ids: list[ID]
    model_manifest_parent: ID | None
    random_seed: int
    gpu_name: str
    cuda_version: str | None
    framework_version: str
    metrics_path: str
    artifact_path: str
    status: Literal["RUNNING", "COMPLETED", "FAILED"]
    scientific_result_eligible: Literal[False] = False


class ModelManifest(Strict):
    schema_version: Literal["model_manifest.v0.1"] = "model_manifest.v0.1"
    model_manifest_id: ID
    name: str
    version: ID
    status: Literal["RESEARCH", "CANDIDATE", "LOCKED_VALIDATION"] = "RESEARCH"
    architecture: str
    encoder: str
    weight_hash: SHA
    training_run_id: ID
    training_dataset_ids: list[ID]
    known_limitations: list[str] = Field(min_length=1)
    intended_research_use: str
    calibration_version: str | None
    ood_method: str | None
    created_at: str


TYPES = {
    c.model_fields["schema_version"].default: c
    for c in [
        ImageManifest,
        DatasetManifest,
        Prediction,
        Annotation,
        AnnotationBatch,
        ExperimentRun,
        ModelManifest,
    ]
}
