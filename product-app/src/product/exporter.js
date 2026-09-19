import { hashJson, sha256Blob } from "./crypto.js";

function jsonBlob(value) {
  return new Blob([JSON.stringify(value, null, 2)], { type: "application/json" });
}

function jsonlBlob(values) {
  return new Blob([values.map((value) => JSON.stringify(value)).join("\n") + "\n"], { type: "application/x-ndjson" });
}

function dataUrlBlob(dataUrl) {
  if (!dataUrl?.startsWith("data:")) return null;
  const [header, encoded] = dataUrl.split(",");
  const mimeType = header.match(/^data:([^;]+)/)?.[1] || "application/octet-stream";
  const binary = atob(encoded);
  const bytes = Uint8Array.from(binary, (character) => character.charCodeAt(0));
  return new Blob([bytes], { type: mimeType });
}

function exportPath(item) {
  return `${item.sourceFolderId || "LOCAL"}/${item.id}`;
}

export async function buildExportPackage(item) {
  const annotationRevision = item.annotation_revisions?.at(-1) || null;
  const packageValue = {
    export_schema_version: "export.v0.1",
    case_id: item.id,
    image_id: item.imageId,
    output_policy: item.output_policy,
    source_reference: { uri: item.sourceReference, sha256: item.sourceSha256, object_key: item.sourceObjectKey },
    image_metadata: {
      file_name: item.fileName,
      file_type: item.fileType,
      modality: item.modality,
      laterality: item.laterality,
      frame_number: item.frame_number,
      frame_count: item.frame_count,
      study_instance_uid: item.study_instance_uid,
      series_instance_uid: item.series_instance_uid,
      sop_instance_uid: item.sop_instance_uid,
      transfer_syntax_uid: item.transfer_syntax_uid,
      technical_metadata: item.technical_metadata,
    },
    system_predictions: item.prediction_history || [],
    annotations: item.annotations || [],
    annotation_revision: annotationRevision,
    review: {
      review_status: item.review_status,
      human_grade: item.humanGrade,
      human_grading_protocol: item.human_grading_protocol || null,
      remark: item.remark,
      training_eligibility: item.trainingEligibility,
    },
    artifact_policy: {
      original: item.output_policy === "COPY_ORIGINAL" || item.output_policy === "COPY_ORIGINAL_AND_DERIVED" ? "COPY" : "REFERENCE_ONLY",
      derived: item.output_policy === "DERIVED_IMAGE_ONLY" || item.output_policy === "COPY_ORIGINAL_AND_DERIVED" ? "EXPORT" : "REFERENCE_ONLY",
      annotations_are_never_burned_into_original: true,
    },
    audit_events: item.audit || [],
  };
  const exportHash = await hashJson(packageValue);
  return { packageValue, exportHash, path: exportPath(item) };
}

async function writeFile(directoryHandle, segments, blob) {
  let directory = directoryHandle;
  for (const segment of segments.slice(0, -1)) directory = await directory.getDirectoryHandle(segment, { create: true });
  const fileHandle = await directory.getFileHandle(segments.at(-1), { create: true });
  const writable = await fileHandle.createWritable();
  await writable.write(blob);
  await writable.close();
  const written = await fileHandle.getFile();
  const [expectedHash, writtenHash] = await Promise.all([sha256Blob(blob), sha256Blob(written)]);
  if (expectedHash !== writtenHash) throw new Error(`Export hash verification failed for ${segments.join("/")}.`);
  return writtenHash;
}

export async function writeExportPackage(item, directoryHandle, sourceBlob) {
  const { packageValue, exportHash, path } = await buildExportPackage(item);
  const copiesOriginal = packageValue.artifact_policy.original === "COPY";
  const exportsDerived = packageValue.artifact_policy.derived === "EXPORT";
  if ((copiesOriginal || exportsDerived) && !directoryHandle) {
    throw new Error("A connected local output folder is required for the selected copy/derived output policy.");
  }
  if (copiesOriginal && !sourceBlob) throw new Error("Original source bytes are unavailable for the selected copy policy.");
  const files = {
    "export_manifest.json": { ...packageValue, export_hash: exportHash },
    "image_metadata.json": packageValue.image_metadata,
    "source_reference.json": packageValue.source_reference,
    "system_predictions.json": packageValue.system_predictions,
    "annotations.json": packageValue.annotations,
    "review.json": packageValue.review,
    "audit_events.jsonl": jsonlBlob(packageValue.audit_events),
  };
  if (directoryHandle) {
    for (const [name, value] of Object.entries(files)) await writeFile(directoryHandle, [path, name], name.endsWith(".jsonl") ? value : jsonBlob(value));
    if (copiesOriginal) await writeFile(directoryHandle, [path, "source", `original.${item.fileName.split(".").pop() || "bin"}`], sourceBlob);
    if (exportsDerived) {
      const derivedBlob = dataUrlBlob(item.displayDerivativeUri);
      if (!derivedBlob) throw new Error("Display derivative is unavailable for the selected derived-image policy.");
      await writeFile(directoryHandle, [path, "preview", "display-derivative.png"], derivedBlob);
    }
  }
  return { exportHash, exportUri: directoryHandle ? `local-folder://${path}` : `browser-download://${path}`, packageValue, fileNames: Object.keys(files) };
}

export function triggerExportDownload(item, exportResult) {
  const blob = jsonBlob({ ...exportResult.packageValue, export_hash: exportResult.exportHash });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${item.id}-export.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}
