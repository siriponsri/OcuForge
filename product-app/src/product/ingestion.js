import { arrayBufferToDataUrl, dataUrlToBytes, sha256Bytes } from "./crypto.js";
import { isDicomBytes, isLikelyDicom, parseDicomBytes } from "./dicom.js";

function now() {
  return new Date().toISOString();
}

function sourceFolderOf(file, sourceReference) {
  return file.webkitRelativePath?.split("/")[0] || sourceReference || "Local source";
}

function baseCase(fields) {
  return {
    id: fields.caseId,
    imageId: fields.imageId,
    fileName: fields.fileName,
    sourceFolder: fields.sourceFolder,
    sourceFolderId: fields.sourceFolder.toUpperCase().replace(/[^A-Z0-9]+/g, "-").replace(/^-|-$/g, "") || "LOCAL",
    modality: fields.modality,
    laterality: fields.laterality || null,
    dimensions: fields.dimensions || "-",
    qcStatus: fields.quarantine ? "QUARANTINED" : "PASS",
    review_status: "NOT_STARTED",
    ai_status: "NOT_RUN",
    export_status: "NOT_EXPORTED",
    derived_queue_status: fields.quarantine ? "QUARANTINED" : "NOT_PROCESSED",
    systemGrade: null,
    systemConfidence: null,
    humanGrade: null,
    humanReviewer: null,
    humanReviewStatus: "UNREVIEWED",
    remark: "",
    annotations: [],
    annotation_revisions: [],
    prediction_history: [],
    audit: [{ actor: "SYSTEM", actorLabel: "System", at: now(), event: fields.quarantine ? "QUARANTINED" : "INGESTED", detail: fields.detail }],
    sourceSha256: fields.sourceSha256,
    sourceReference: fields.sourceReference,
    sourceObjectKey: `source/${fields.sourceSha256}`,
    sourceBytesStored: true,
    fileType: fields.fileType,
    imageUrl: fields.imageUrl || null,
    displayDerivativeUri: fields.displayDerivativeUri || fields.imageUrl || null,
    derivative_provenance: fields.derivative_provenance || null,
    derivative_preprocessing_version: fields.derivative_preprocessing_version || null,
    training_image_uri: fields.training_image_uri || fields.displayDerivativeUri || fields.sourceReference,
    training_image_sha256: fields.training_image_sha256 || fields.sourceSha256,
    frame_count: fields.frame_count || 1,
    frame_number: fields.frame_number || 1,
    study_instance_uid: fields.study_instance_uid || null,
    series_instance_uid: fields.series_instance_uid || null,
    sop_instance_uid: fields.sop_instance_uid || null,
    transfer_syntax_uid: fields.transfer_syntax_uid || null,
    technical_metadata: fields.technical_metadata || {},
    quarantineReason: fields.quarantineReason || null,
    output_policy: fields.output_policy || "REFERENCE_ONLY",
    trainingEligibility: "UNREVIEWED_SYSTEM",
    created_at: now(),
    updated_at: now(),
  };
}

async function rasterCase(file, index, sourceConfig) {
  const supportedRaster = /\.(jpe?g|png|tiff?|webp)$/i.test(file.name) || file.type?.startsWith("image/");
  if (!supportedRaster) throw new Error("Unsupported raster format; object was quarantined.");
  const bytes = await file.arrayBuffer();
  const sourceSha256 = await sha256Bytes(new Uint8Array(bytes));
  const sourceFolder = sourceFolderOf(file, sourceConfig.sourceReference);
  const imageUrl = arrayBufferToDataUrl(bytes, file.type || "image/*");
  const caseId = `CASE-${sourceSha256.slice(0, 8).toUpperCase()}`;
  return baseCase({
    caseId,
    imageId: `IMG-${sourceSha256.slice(0, 10)}`,
    fileName: file.name,
    sourceFolder,
    modality: "CFP",
    laterality: index % 2 ? "OS" : "OD",
    dimensions: "Raster derivative",
    sourceSha256,
    sourceReference: `local://${sourceFolder}/${file.name}`,
    fileType: "RASTER",
    imageUrl,
    detail: "Raster source bytes preserved and hashed before display use.",
    output_policy: sourceConfig.outputPolicy,
  });
}

async function dicomCases(file, sourceConfig) {
  const bytes = await file.arrayBuffer();
  const sourceFolder = sourceFolderOf(file, sourceConfig.sourceReference);
  const parsed = await parseDicomBytes(bytes, file.name);
  const cases = [];
  for (let frameNumber = 1; frameNumber <= parsed.frameCount; frameNumber += 1) {
    let derivative = { dataUrl: null, provenance: { available: false } };
    try {
      derivative = await parsed.displayDerivative(frameNumber);
    } catch {
      derivative = { dataUrl: null, provenance: { available: false, reason: "DERIVATIVE_FAILED" } };
    }
    const frameKey = `${parsed.sourceSha256.slice(0, 8)}-F${String(frameNumber).padStart(3, "0")}`;
    const trainingImageSha256 = derivative.dataUrl ? await sha256Bytes(dataUrlToBytes(derivative.dataUrl)) : parsed.sourceSha256;
    cases.push(baseCase({
      caseId: `CASE-${frameKey.toUpperCase()}`,
      imageId: `IMG-${frameKey.toUpperCase()}`,
      fileName: file.name,
      sourceFolder,
      modality: parsed.technical.modality,
      laterality: parsed.technical.laterality,
      dimensions: `${parsed.technical.columns || "?"} x ${parsed.technical.rows || "?"}`,
      sourceSha256: parsed.sourceSha256,
      sourceReference: `local://${sourceFolder}/${file.name}#frame=${frameNumber}`,
      fileType: "DICOM",
      imageUrl: derivative.dataUrl,
      displayDerivativeUri: derivative.dataUrl,
      training_image_uri: derivative.dataUrl || `local://${sourceFolder}/${file.name}#frame=${frameNumber}`,
      training_image_sha256: trainingImageSha256,
      derivative_provenance: { ...derivative.provenance, source_sha256: parsed.sourceSha256 },
      derivative_preprocessing_version: "dicom-display-v0.1",
      frame_count: parsed.frameCount,
      frame_number: frameNumber,
      study_instance_uid: parsed.technical.study_instance_uid,
      series_instance_uid: parsed.technical.series_instance_uid,
      sop_instance_uid: parsed.technical.sop_instance_uid,
      transfer_syntax_uid: parsed.technical.transfer_syntax_uid,
      technical_metadata: parsed.technical,
      detail: "DICOM bytes preserved, SHA-256 recorded, and a reviewable display derivative created.",
      output_policy: sourceConfig.outputPolicy,
    }));
  }
  return { cases, sourceSha256: parsed.sourceSha256, bytes };
}

export async function ingestFiles(files, sourceConfig, repository, existingCases = []) {
  const cases = [];
  const quarantined = [];
  const seen = new Set(existingCases.map((item) => item.sourceSha256));
  let acceptedFiles = 0;
  let duplicateFiles = 0;
  for (const [index, file] of files.entries()) {
    const bytes = await file.arrayBuffer();
    const header = new Uint8Array(bytes.slice(0, 132));
    const dicom = isDicomBytes(header) || isLikelyDicom(file);
    try {
      const result = dicom
        ? await dicomCases(file, sourceConfig)
        : { cases: [await rasterCase(file, index, sourceConfig)], sourceSha256: await sha256Bytes(new Uint8Array(bytes)), bytes };
      if (seen.has(result.sourceSha256)) {
        duplicateFiles += 1;
        continue;
      }
      seen.add(result.sourceSha256);
      await repository.putObject(`source/${result.sourceSha256}`, new Blob([bytes], { type: file.type || "application/octet-stream" }));
      cases.push(...result.cases);
      acceptedFiles += 1;
    } catch (error) {
      const sourceSha256 = await sha256Bytes(new Uint8Array(bytes));
      if (seen.has(sourceSha256)) {
        duplicateFiles += 1;
        continue;
      }
      seen.add(sourceSha256);
      await repository.putObject(`source/${sourceSha256}`, new Blob([bytes], { type: file.type || "application/octet-stream" }));
      const sourceFolder = sourceFolderOf(file, sourceConfig.sourceReference);
      quarantined.push(baseCase({
        caseId: `CASE-Q-${sourceSha256.slice(0, 8).toUpperCase()}`,
        imageId: `IMG-Q-${sourceSha256.slice(0, 8).toUpperCase()}`,
        fileName: file.name,
        sourceFolder,
        modality: "DICOM",
        sourceSha256,
        sourceReference: `local://${sourceFolder}/${file.name}`,
        fileType: dicom ? "DICOM" : "RASTER",
        quarantine: true,
        quarantineReason: error.message,
        detail: "Source bytes were preserved, but the object was quarantined before review.",
        output_policy: sourceConfig.outputPolicy,
      }));
    }
  }
  return { cases: [...cases, ...quarantined], discovered: files.length, accepted: acceptedFiles, accepted_cases: cases.length, quarantined: quarantined.length, duplicates: duplicateFiles };
}
