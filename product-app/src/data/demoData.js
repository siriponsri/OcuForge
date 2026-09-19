import { AI_STATUS, EXPORT_STATUS, REVIEW_STATUS, withDerivedStatus } from "../product/constants";

export const IMAGE_URL = "/fundus-retinopathy-eda03.jpg";

function audit(event, detail, actor = "SYSTEM", actorLabel = "System", at = "2026-09-19T08:42:00Z") {
  return { actor, actorLabel, at, event, detail };
}

function prediction(id, grade, confidence, annotations = []) {
  return {
    prediction_id: id,
    system_dr_grade: grade,
    confidence,
    model_manifest: {
      model_manifest_id: "mock-bundle-v0.1.0",
      encoder_id: "mock-encoder",
      head_id: "mock-dr-head",
      preprocessing_version: "fundus-display-v0.1",
      calibration_version: "none-poc",
      adapter_contract_version: "model-adapter.v0.1",
    },
    annotations,
    created_at: "2026-09-19T08:42:00Z",
  };
}

function makeCase(overrides = {}) {
  const predictionRecord = overrides.prediction_history?.at(-1);
  return withDerivedStatus({
    id: "CASE-0000",
    imageId: "IMG-0000",
    fileName: "fundus-image.jpg",
    sourceFolder: "Ward A / Morning intake",
    sourceFolderId: "WARD-A-MORNING",
    modality: "CFP",
    laterality: "OD",
    dimensions: "4288 x 2848",
    qcStatus: "PASS",
    review_status: REVIEW_STATUS.NOT_STARTED,
    ai_status: AI_STATUS.NOT_RUN,
    export_status: EXPORT_STATUS.NOT_EXPORTED,
    systemGrade: null,
    systemConfidence: null,
    humanGrade: null,
    humanReviewer: null,
    humanReviewStatus: "UNREVIEWED",
    human_grading_protocol: null,
    human_reviewed_at: null,
    remark: "",
    annotations: [],
    annotation_revisions: [],
    prediction_history: [],
    audit: [audit("INGESTED", "Source bytes preserved; content hash recorded.")],
    sourceSha256: "3a7c4d9f1b2e8a3e7c1d4f0a9b6e5c2d8a4f1e7b3c0d6a9e2f5b8c1d4a7e0f3",
    sourceReference: "local://WARD-A-MORNING/fundus-image.jpg",
    sourceObjectKey: "source/3a7c4d9f1b2e8a3e7c1d4f0a9b6e5c2d8a4f1e7b3c0d6a9e2f5b8c1d4a7e0f3",
    sourceBytesStored: false,
    fileType: "RASTER",
    imageUrl: IMAGE_URL,
    displayDerivativeUri: IMAGE_URL,
    derivative_provenance: { available: true, source: "demo-fixture" },
    derivative_preprocessing_version: "fundus-display-v0.1",
    frame_count: 1,
    frame_number: 1,
    study_instance_uid: null,
    series_instance_uid: null,
    sop_instance_uid: null,
    transfer_syntax_uid: null,
    technical_metadata: {},
    quarantineReason: null,
    output_policy: "REFERENCE_ONLY",
    trainingEligibility: "UNREVIEWED_SYSTEM",
    export_uri: null,
    export_hash: null,
    annotation_artifact_uri: null,
    training_image_uri: IMAGE_URL,
    training_image_sha256: null,
    created_at: "2026-09-19T08:42:00Z",
    updated_at: "2026-09-19T08:42:00Z",
    ...overrides,
    ...(predictionRecord ? {
      systemGrade: predictionRecord.system_dr_grade,
      systemConfidence: predictionRecord.confidence,
      systemPredictionId: predictionRecord.prediction_id,
      systemModelManifestId: predictionRecord.model_manifest.model_manifest_id,
    } : {}),
  });
}

export const createDemoCases = () => [
  makeCase({
    id: "CASE-0042", imageId: "IMG-0042", fileName: "IMG_0042.dcm", modality: "DICOM", dimensions: "4288 x 2848",
    study_instance_uid: "1.2.826.0.1.3680043.10.543.100.42", series_instance_uid: "1.2.826.0.1.3680043.10.543.200.42",
    sop_instance_uid: "1.2.826.0.1.3680043.10.543.300.42", transfer_syntax_uid: "1.2.840.10008.1.2.1",
    fileType: "DICOM", sourceReference: "local://WARD-A-MORNING/IMG_0042.dcm#frame=1",
    prediction_history: [prediction("PRED-0042-01", 2, 0.91, [{ id: "ANN-S-0042", type: "ellipse", x: 0.55, y: 0.42, width: 0.16, height: 0.12, provenance: "SYSTEM", label: "System suggestion", source_prediction_id: "PRED-0042-01" }])],
    annotations: [{ id: "ANN-S-0042", type: "ellipse", x: 0.55, y: 0.42, width: 0.16, height: 0.12, provenance: "SYSTEM", label: "System suggestion", source_prediction_id: "PRED-0042-01" }],
    ai_status: AI_STATUS.PROCESSED,
    audit: [audit("INGESTED", "DICOM source preserved and hashed."), audit("AI_PROCESSED", "Mock bundle produced an immutable system prediction.")],
  }),
  makeCase({
    id: "CASE-0043", imageId: "IMG-0043", fileName: "fundus_0043.jpg", laterality: "OS",
    sourceFolder: "Ward A / Morning intake", sourceFolderId: "WARD-A-MORNING",
    prediction_history: [prediction("PRED-0043-01", 1, 0.78, [{ id: "ANN-S-0043", type: "rectangle", x: 0.55, y: 0.42, width: 0.16, height: 0.18, provenance: "SYSTEM", label: "Possible lesion", source_prediction_id: "PRED-0043-01" }])],
    annotations: [{ id: "ANN-S-0043", type: "rectangle", x: 0.55, y: 0.42, width: 0.16, height: 0.18, provenance: "SYSTEM", label: "Possible lesion", source_prediction_id: "PRED-0043-01" }],
    review_status: REVIEW_STATUS.IN_REVIEW, ai_status: AI_STATUS.PROCESSED,
    audit: [audit("INGESTED", "Source bytes preserved; content hash recorded."), audit("AI_PROCESSED", "Mock bundle produced an immutable system prediction."), audit("REVIEW_OPENED", "Review session materialized by reviewer.")],
  }),
  makeCase({
    id: "CASE-0044", imageId: "IMG-0044", fileName: "fundus_0044.png", sourceFolder: "Ward B / Afternoon intake", sourceFolderId: "WARD-B-AFTERNOON",
    systemGrade: 3, systemConfidence: 0.84,
    prediction_history: [prediction("PRED-0044-01", 3, 0.84, [{ id: "ANN-S-0044", type: "ellipse", x: 0.28, y: 0.37, width: 0.12, height: 0.1, provenance: "SYSTEM", label: "System area", source_prediction_id: "PRED-0044-01" }])],
    annotations: [{ id: "ANN-S-0044", type: "ellipse", x: 0.28, y: 0.37, width: 0.12, height: 0.1, provenance: "SYSTEM", label: "System area", source_prediction_id: "PRED-0044-01" }, { id: "ANN-U-0044", type: "point", x: 0.48, y: 0.56, provenance: "USER", label: "Microaneurysm", source_prediction_id: "PRED-0044-01" }],
    review_status: REVIEW_STATUS.HUMAN_REVIEWED, ai_status: AI_STATUS.PROCESSED, export_status: EXPORT_STATUS.FAILED,
    humanGrade: 2, humanReviewer: "reviewer-7f3a", humanReviewStatus: "REVIEWED", human_grading_protocol: "DR-GRADING-PROTOCOL-v0.1", human_reviewed_at: "2026-09-19T08:55:00Z",
    remark: "Human grade differs from system grade; review retained.", trainingEligibility: "HUMAN",
    annotation_revisions: [{ revision_id: "REV-0044-01", revision_hash: "revhash-0044-01", schema_version: "annotation.v0.1", provenance: "USER", base_prediction_id: "PRED-0044-01", created_at: "2026-09-19T08:55:00Z" }],
    audit: [audit("INGESTED", "Source bytes preserved; content hash recorded."), audit("AI_PROCESSED", "Mock bundle produced an immutable system prediction."), audit("HUMAN_REVIEWED", "Human grade 2 saved; system grade 3 preserved.", "reviewer-7f3a", "Reviewer", "2026-09-19T08:55:00Z"), audit("EXPORT_FAILED", "Destination was unavailable; review remains durable.", "SYSTEM", "Export")],
  }),
  makeCase({
    id: "CASE-0045", imageId: "IMG-0045", fileName: "fundus_0045.tif", sourceFolder: "Ward B / Afternoon intake", sourceFolderId: "WARD-B-AFTERNOON",
    systemGrade: 0, systemConfidence: 0.96, prediction_history: [prediction("PRED-0045-01", 0, 0.96)],
    review_status: REVIEW_STATUS.HUMAN_REVIEWED, ai_status: AI_STATUS.PROCESSED, export_status: EXPORT_STATUS.EXPORTED,
    humanGrade: 0, humanReviewer: "reviewer-7f3a", humanReviewStatus: "REVIEWED", human_grading_protocol: "DR-GRADING-PROTOCOL-v0.1", human_reviewed_at: "2026-09-19T08:28:00Z", trainingEligibility: "HUMAN",
    export_uri: "local-folder://WARD-B-AFTERNOON/CASE-0045", export_hash: "exporthash-0045",
    audit: [audit("INGESTED", "Source bytes preserved; content hash recorded."), audit("AI_PROCESSED", "Mock bundle produced an immutable system prediction."), audit("HUMAN_REVIEWED", "Human grade 0 saved.", "reviewer-7f3a", "Reviewer", "2026-09-19T08:28:00Z"), audit("EXPORTED", "Export artifacts verified at local destination.", "SYSTEM", "Export")],
  }),
  makeCase({
    id: "CASE-0046", imageId: "IMG-0046", fileName: "fundus_0046.jpg", sourceFolder: "Ward C / Review set", sourceFolderId: "WARD-C-REVIEW-SET", ai_status: AI_STATUS.FAILED,
    audit: [audit("INGESTED", "Source bytes preserved; content hash recorded."), audit("AI_FAILED", "Mock adapter failure is isolated from review state.")],
  }),
  makeCase({ id: "CASE-0047", imageId: "IMG-0047", fileName: "fundus_0047.jpeg", sourceFolder: "Ward C / Review set", sourceFolderId: "WARD-C-REVIEW-SET" }),
  makeCase({
    id: "CASE-0048", imageId: "IMG-0048", fileName: "fundus_0048.jpg", sourceFolder: "Ward A / Morning intake", sourceFolderId: "WARD-A-MORNING",
    prediction_history: [prediction("PRED-0048-01", 4, 0.73, [{ id: "ANN-S-0048", type: "area", x: 0.62, y: 0.31, width: 0.17, height: 0.16, provenance: "SYSTEM", label: "System area", source_prediction_id: "PRED-0048-01" }])],
    annotations: [{ id: "ANN-S-0048", type: "area", x: 0.62, y: 0.31, width: 0.17, height: 0.16, provenance: "SYSTEM", label: "System area", source_prediction_id: "PRED-0048-01" }], ai_status: AI_STATUS.PROCESSED,
    audit: [audit("INGESTED", "Source bytes preserved; content hash recorded."), audit("AI_PROCESSED", "Mock bundle produced an immutable system prediction.")],
  }),
];
