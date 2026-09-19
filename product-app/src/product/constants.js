export const PRODUCT_SCHEMA_VERSION = "product.v0.1";

export const REVIEW_STATUS = {
  NOT_STARTED: "NOT_STARTED",
  IN_REVIEW: "IN_REVIEW",
  HUMAN_REVIEWED: "HUMAN_REVIEWED",
};

export const AI_STATUS = {
  NOT_RUN: "NOT_RUN",
  RUNNING: "RUNNING",
  PROCESSED: "PROCESSED",
  FAILED: "FAILED",
};

export const EXPORT_STATUS = {
  NOT_EXPORTED: "NOT_EXPORTED",
  EXPORTING: "EXPORTING",
  EXPORTED: "EXPORTED",
  FAILED: "FAILED",
};

export const OUTPUT_POLICIES = [
  "REFERENCE_ONLY",
  "COPY_ORIGINAL",
  "DERIVED_IMAGE_ONLY",
  "COPY_ORIGINAL_AND_DERIVED",
];

export const ELIGIBILITY = ["HUMAN", "PSEUDO_LABEL", "WEAK_LABEL", "UNREVIEWED_SYSTEM"];

export const TOOLS = [
  { id: "select", label: "Select", shortLabel: "Select" },
  { id: "rectangle", label: "Rectangle", shortLabel: "Box" },
  { id: "point", label: "Point", shortLabel: "Point" },
  { id: "ellipse", label: "Circle / ellipse", shortLabel: "Ellipse" },
  { id: "polygon", label: "Polygon", shortLabel: "Polygon" },
  { id: "area", label: "Translucent area", shortLabel: "Area" },
];

export const MANIFEST_FIELDS = [
  "manifest_version", "manifest_snapshot_id", "row_id", "case_id", "image_id",
  "source_folder_id", "source_folder_name", "source_provider", "source_reference",
  "local_object_uri", "file_name", "file_extension", "file_sha256", "file_type", "modality",
  "laterality", "width_px", "height_px", "frame_count", "study_instance_uid_reference",
  "series_instance_uid_reference", "sop_instance_uid_reference", "frame_number", "transfer_syntax_uid",
  "patient_pseudo_id", "eye_id", "visit_id", "qc_status", "review_status", "ai_status",
  "export_status", "derived_queue_status", "system_dr_grade", "system_dr_confidence",
  "system_prediction_id", "system_model_manifest_id", "human_reviewed_dr_grade", "human_grading_protocol",
  "human_review_status", "human_reviewer_id_hash", "human_reviewed_at", "annotation_count",
  "human_annotation_count", "annotation_artifact_uri", "annotation_revision_hash",
  "annotation_schema_version", "training_image_uri", "training_image_sha256",
  "derivative_preprocessing_version", "training_eligibility", "label_provenance", "output_policy",
  "export_uri", "export_hash", "created_at", "updated_at",
];

export const STATUS_META = {
  NOT_PROCESSED: { label: "Not processed", tone: "neutral" },
  AI_RUNNING: { label: "AI running", tone: "blue" },
  AI_PROCESSED: { label: "AI processed", tone: "blue" },
  IN_REVIEW: { label: "In review", tone: "amber" },
  HUMAN_REVIEWED: { label: "Human reviewed", tone: "green" },
  HUMAN_REVIEWED_EXPORT_FAILED: { label: "Review saved / export failed", tone: "red" },
  EXPORTED: { label: "Exported", tone: "teal" },
  AI_FAILED: { label: "AI failed", tone: "red" },
  QUARANTINED: { label: "Quarantined", tone: "red" },
};

export const QUEUE_FILTERS = [
  "NOT_PROCESSED",
  "AI_PROCESSED",
  "IN_REVIEW",
  "HUMAN_REVIEWED",
  "EXPORTED",
  "AI_FAILED",
  "QUARANTINED",
];

export function deriveQueueBadge(item) {
  if (item.qcStatus === "QUARANTINED") return "QUARANTINED";
  if (item.export_status === EXPORT_STATUS.EXPORTED) return "EXPORTED";
  if (item.review_status === REVIEW_STATUS.HUMAN_REVIEWED && item.export_status === EXPORT_STATUS.FAILED) {
    return "HUMAN_REVIEWED_EXPORT_FAILED";
  }
  if (item.ai_status === AI_STATUS.FAILED) {
    return item.review_status === REVIEW_STATUS.HUMAN_REVIEWED ? "HUMAN_REVIEWED" : "AI_FAILED";
  }
  if (item.ai_status === AI_STATUS.RUNNING) return "AI_RUNNING";
  if (item.review_status === REVIEW_STATUS.IN_REVIEW) return "IN_REVIEW";
  if (item.review_status === REVIEW_STATUS.HUMAN_REVIEWED) return "HUMAN_REVIEWED";
  if (item.ai_status === AI_STATUS.PROCESSED) return "AI_PROCESSED";
  return "NOT_PROCESSED";
}

export function statusMeta(itemOrStatus) {
  const status = typeof itemOrStatus === "string" ? itemOrStatus : deriveQueueBadge(itemOrStatus);
  return STATUS_META[status] || STATUS_META.NOT_PROCESSED;
}

export function withDerivedStatus(item) {
  return { ...item, derived_queue_status: deriveQueueBadge(item) };
}
