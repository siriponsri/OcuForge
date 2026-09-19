import { MANIFEST_FIELDS } from "./constants.js";

function csvValue(value) {
  return `"${String(value ?? "").replaceAll('"', '""')}"`;
}

export function buildManifestRows(cases) {
  return cases.map((item) => {
    const latestRevision = item.annotation_revisions?.at(-1);
    const hasHumanGrade = item.humanGrade !== null && item.humanGrade !== undefined;
    const trainingEligibility = item.trainingEligibility === "HUMAN" && !hasHumanGrade
      ? "UNREVIEWED_SYSTEM"
      : item.trainingEligibility || "UNREVIEWED_SYSTEM";
    return {
      manifest_version: "manifest.v0.1",
      manifest_snapshot_id: "local-live-snapshot",
      row_id: `ROW-${item.id}`,
      case_id: item.id,
      image_id: item.imageId,
      source_folder_id: item.sourceFolderId,
      source_folder_name: item.sourceFolder,
      source_provider: "LOCAL",
      source_reference: item.sourceReference,
      local_object_uri: item.sourceObjectKey,
      file_name: item.fileName,
      file_extension: item.fileName.includes(".") ? item.fileName.split(".").pop().toLowerCase() : "",
      file_sha256: item.sourceSha256,
      file_type: item.fileType,
      modality: item.modality,
      laterality: item.laterality,
      width_px: item.technical_metadata?.columns || "",
      height_px: item.technical_metadata?.rows || "",
      frame_count: item.frame_count,
      study_instance_uid_reference: item.study_instance_uid,
      series_instance_uid_reference: item.series_instance_uid,
      sop_instance_uid_reference: item.sop_instance_uid,
      frame_number: item.frame_number,
      transfer_syntax_uid: item.transfer_syntax_uid,
      patient_pseudo_id: item.patient_pseudo_id || "",
      eye_id: item.laterality || "",
      visit_id: item.visit_id || "",
      qc_status: item.qcStatus,
      review_status: item.review_status,
      ai_status: item.ai_status,
      export_status: item.export_status,
      derived_queue_status: item.derived_queue_status,
      system_dr_grade: item.systemGrade,
      system_dr_confidence: item.systemConfidence,
      system_prediction_id: item.prediction_history?.at(-1)?.prediction_id,
      system_model_manifest_id: item.prediction_history?.at(-1)?.model_manifest?.model_manifest_id,
      human_reviewed_dr_grade: item.humanGrade,
      human_grading_protocol: item.human_grading_protocol || "DR-GRADING-PROTOCOL-UNSET",
      human_review_status: item.humanReviewStatus,
      human_reviewer_id_hash: item.humanReviewer,
      human_reviewed_at: item.human_reviewed_at,
      annotation_count: item.annotations?.length || 0,
      human_annotation_count: item.annotations?.filter((annotation) => annotation.provenance === "USER").length || 0,
      annotation_artifact_uri: item.annotation_artifact_uri || `local://${item.id}/annotations.json`,
      annotation_revision_hash: latestRevision?.revision_hash || "",
      annotation_schema_version: latestRevision?.schema_version || "annotation.v0.1",
      training_image_uri: item.training_image_uri || item.displayDerivativeUri || item.sourceReference,
      training_image_sha256: item.training_image_sha256 || item.sourceSha256,
      derivative_preprocessing_version: item.derivative_preprocessing_version,
      training_eligibility: trainingEligibility,
      label_provenance: trainingEligibility === "HUMAN" && hasHumanGrade ? "HUMAN" : trainingEligibility,
      output_policy: item.output_policy,
      export_uri: item.export_uri,
      export_hash: item.export_hash,
      created_at: item.created_at,
      updated_at: item.updated_at,
    };
  });
}

export function rowsToCsv(rows) {
  return `${MANIFEST_FIELDS.join(",")}\n${rows.map((row) => MANIFEST_FIELDS.map((field) => csvValue(row[field])).join(",")).join("\n")}`;
}

export function buildManifestCsv(cases) {
  return rowsToCsv(buildManifestRows(cases));
}

export function buildIndexCsv(cases) {
  const rows = buildManifestRows(cases);
  const fields = ["case_id", "image_id", "file_sha256", "training_image_uri", "training_image_sha256", "annotation_artifact_uri", "annotation_revision_hash", "annotation_schema_version", "training_eligibility", "review_status", "ai_status", "export_status"];
  return `${fields.join(",")}\n${rows.map((row) => fields.map((field) => csvValue(row[field])).join(",")).join("\n")}`;
}
