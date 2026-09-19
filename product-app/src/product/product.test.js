import assert from "node:assert/strict";
import test from "node:test";
import { AI_STATUS, EXPORT_STATUS, REVIEW_STATUS, deriveQueueBadge } from "./constants.js";
import { hashJson, sha256Bytes } from "./crypto.js";
import { isDicomBytes, parseDicomBytes } from "./dicom.js";
import { buildIndexCsv, buildManifestRows, buildManifestCsv } from "./manifest.js";
import { createSyntheticDicomBytes } from "./syntheticDicom.js";
import { ingestFiles } from "./ingestion.js";

function fakeFile(name, bytes, type = "application/octet-stream") {
  return { name, type, arrayBuffer: async () => bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength) };
}

test("DICOM preserves bytes, identity fields, frame count and SHA-256", async () => {
  const bytes = createSyntheticDicomBytes({ frames: 2, seed: 11 });
  const parsed = await parseDicomBytes(bytes.buffer, "fixture.dcm");
  assert.equal(isDicomBytes(bytes), true);
  assert.equal(parsed.frameCount, 2);
  assert.equal(parsed.technical.study_instance_uid, "1.2.826.0.1.3680043.10.543.100.11");
  assert.equal(parsed.technical.series_instance_uid, "1.2.826.0.1.3680043.10.543.200.11");
  assert.equal(parsed.technical.sop_instance_uid, "1.2.826.0.1.3680043.10.543.300.11");
  assert.equal(parsed.technical.transfer_syntax_uid, "1.2.840.10008.1.2.1");
  assert.equal(parsed.technical.rows, 32);
  assert.equal(parsed.technical.columns, 32);
  assert.equal(parsed.technical.window_center[0], 128);
  assert.equal(parsed.sourceSha256, await sha256Bytes(bytes));
  assert.equal(parsed.technical.patient_name, undefined);
});

test("malformed DICOM is quarantined and retry is idempotent", async () => {
  const bytes = new TextEncoder().encode("not a DICOM object");
  const files = [fakeFile("bad.dcm", bytes, "application/dicom")];
  const objects = new Map();
  const repository = { putObject: async (key, value) => objects.set(key, value) };
  const config = { sourceReference: "fixture", outputPolicy: "REFERENCE_ONLY" };
  const first = await ingestFiles(files, config, repository, []);
  const second = await ingestFiles(files, config, repository, first.cases);
  assert.equal(first.quarantined, 1);
  assert.equal(first.cases[0].qcStatus, "QUARANTINED");
  assert.match(first.cases[0].quarantineReason, /DICOM/i);
  assert.equal(second.cases.length, 0);
  assert.equal(objects.size, 1);
});

test("multi-frame ingestion creates independent frame lineage", async () => {
  const bytes = createSyntheticDicomBytes({ frames: 2, seed: 12 });
  const repository = { putObject: async () => undefined };
  const result = await ingestFiles([fakeFile("multi.dcm", bytes, "application/dicom")], { sourceReference: "fixture", outputPolicy: "REFERENCE_ONLY" }, repository, []);
  assert.equal(result.cases.length, 2);
  assert.deepEqual(result.cases.map((item) => item.frame_number), [1, 2]);
  assert.equal(result.cases[0].sourceSha256, result.cases[1].sourceSha256);
  assert.notEqual(result.cases[0].id, result.cases[1].id);
});

test("queue badge keeps review durable when AI or export fails", () => {
  const reviewedExportFailed = { review_status: REVIEW_STATUS.HUMAN_REVIEWED, ai_status: AI_STATUS.PROCESSED, export_status: EXPORT_STATUS.FAILED };
  const reviewedAiFailed = { review_status: REVIEW_STATUS.HUMAN_REVIEWED, ai_status: AI_STATUS.FAILED, export_status: EXPORT_STATUS.NOT_EXPORTED };
  assert.equal(deriveQueueBadge(reviewedExportFailed), "HUMAN_REVIEWED_EXPORT_FAILED");
  assert.equal(deriveQueueBadge(reviewedAiFailed), "HUMAN_REVIEWED");
});

test("manifest contains exact annotation and training image lineage", async () => {
  const item = {
    id: "CASE-1", imageId: "IMG-1", sourceFolderId: "WARD", sourceFolder: "Ward", sourceReference: "local://case",
    sourceObjectKey: "source/hash", fileName: "a.dcm", sourceSha256: "hash", fileType: "DICOM", modality: "OP", laterality: "OD",
    frame_count: 2, frame_number: 1, qcStatus: "PASS", review_status: REVIEW_STATUS.HUMAN_REVIEWED, ai_status: AI_STATUS.PROCESSED,
    export_status: EXPORT_STATUS.FAILED, derived_queue_status: "HUMAN_REVIEWED_EXPORT_FAILED", systemGrade: 2, systemConfidence: .9,
    prediction_history: [{ prediction_id: "PRED-1", model_manifest: { model_manifest_id: "bundle" } }], humanGrade: 1,
    human_grading_protocol: "DR-v1", humanReviewStatus: "REVIEWED", humanReviewer: "reviewer", human_reviewed_at: "now",
    annotations: [{ id: "ANN-1", provenance: "USER" }], annotation_revisions: [{ revision_hash: "revision-sha", schema_version: "annotation.v0.1" }],
    displayDerivativeUri: "local://derivative.png", derivative_preprocessing_version: "dicom-display-v0.1", trainingEligibility: "HUMAN",
    output_policy: "REFERENCE_ONLY", export_uri: null, export_hash: null, created_at: "now", updated_at: "now", technical_metadata: {},
  };
  const rows = buildManifestRows([item]);
  assert.equal(rows[0].annotation_artifact_uri, "local://CASE-1/annotations.json");
  assert.equal(rows[0].annotation_revision_hash, "revision-sha");
  assert.equal(rows[0].annotation_schema_version, "annotation.v0.1");
  assert.equal(rows[0].training_image_uri, "local://derivative.png");
  assert.equal(rows[0].training_image_sha256, "hash");
  assert.equal(rows[0].human_grading_protocol, "DR-v1");
  assert.match(buildManifestCsv([item]), /annotation_revision_hash/);
  assert.match(buildIndexCsv([item]), /training_image_uri/);
  assert.equal((await hashJson(rows[0])).length, 64);
});
