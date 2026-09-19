import dicomParser from "dicom-parser";
import { arrayBufferToDataUrl, sha256Bytes } from "./crypto.js";

const TAGS = {
  study: "x0020000d",
  series: "x0020000e",
  sop: "x00080018",
  transferSyntax: "x00020010",
  modality: "x00080060",
  laterality: "x00200062",
  rows: "x00280010",
  columns: "x00280011",
  samplesPerPixel: "x00280002",
  photometric: "x00280004",
  frames: "x00280008",
  bitsAllocated: "x00280100",
  bitsStored: "x00280101",
  highBit: "x00280102",
  pixelRepresentation: "x00280103",
  orientation: "x00200037",
  pixelSpacing: "x00280030",
  windowCenter: "x00281050",
  windowWidth: "x00281051",
  pixelData: "x7fe00010",
};

function value(dataSet, tag, index = 0) {
  const element = dataSet.elements[tag];
  if (!element) return null;
  try {
    return dataSet.string(tag, index) ?? null;
  } catch {
    return null;
  }
}

function numberValue(dataSet, tag, index = 0) {
  const element = dataSet.elements[tag];
  if (!element) return null;
  try {
    return dataSet.uint16(tag, index);
  } catch {
    const parsed = Number(value(dataSet, tag, index));
    return Number.isFinite(parsed) ? parsed : null;
  }
}

function decimalValues(dataSet, tag) {
  const text = value(dataSet, tag);
  if (!text) return null;
  const values = text.split("\\").map(Number).filter(Number.isFinite);
  return values.length ? values : null;
}

export function isDicomBytes(bytes) {
  return bytes.length >= 132 && String.fromCharCode(...bytes.slice(128, 132)) === "DICM";
}

export function isLikelyDicom(file) {
  return file.name.toLowerCase().endsWith(".dcm") || file.name.toLowerCase().endsWith(".dicom");
}

function privacySafeMetadata(dataSet) {
  return {
    modality: value(dataSet, TAGS.modality) || "OT",
    laterality: value(dataSet, TAGS.laterality) || null,
    rows: numberValue(dataSet, TAGS.rows),
    columns: numberValue(dataSet, TAGS.columns),
    samples_per_pixel: numberValue(dataSet, TAGS.samplesPerPixel),
    photometric_interpretation: value(dataSet, TAGS.photometric),
    number_of_frames: Math.max(1, Number(value(dataSet, TAGS.frames)) || 1),
    bits_allocated: numberValue(dataSet, TAGS.bitsAllocated),
    bits_stored: numberValue(dataSet, TAGS.bitsStored),
    high_bit: numberValue(dataSet, TAGS.highBit),
    pixel_representation: numberValue(dataSet, TAGS.pixelRepresentation),
    orientation_patient: decimalValues(dataSet, TAGS.orientation),
    pixel_spacing: decimalValues(dataSet, TAGS.pixelSpacing),
    window_center: decimalValues(dataSet, TAGS.windowCenter),
    window_width: decimalValues(dataSet, TAGS.windowWidth),
  };
}

function parseDataSet(buffer) {
  const bytes = new Uint8Array(buffer);
  if (!isDicomBytes(bytes)) throw new Error("Not a DICOM Part 10 object.");
  try {
    return dicomParser.parseDicom(bytes);
  } catch (error) {
    throw new Error(`Malformed or unsupported DICOM: ${error.message}`);
  }
}

function displayWindow(metadata) {
  const center = metadata.window_center?.[0];
  const width = metadata.window_width?.[0];
  if (Number.isFinite(center) && Number.isFinite(width) && width > 0) {
    return { center, width, source: "DICOM_WINDOW" };
  }
  return { center: null, width: null, source: "AUTO_MIN_MAX" };
}

function pixelFrame(dataSet, metadata, frameNumber) {
  const element = dataSet.elements[TAGS.pixelData];
  if (!element || !metadata.rows || !metadata.columns) return null;
  const samples = metadata.samples_per_pixel || 1;
  const bytesPerSample = Math.max(1, (metadata.bits_allocated || 8) / 8);
  const frameSize = metadata.rows * metadata.columns * samples * bytesPerSample;
  const offset = element.dataOffset + (frameNumber - 1) * frameSize;
  return { offset, length: frameSize, bytesPerSample, samples };
}

export function extractDicomTechnicalMetadata(dataSet) {
  const metadata = privacySafeMetadata(dataSet);
  return {
    ...metadata,
    study_instance_uid: value(dataSet, TAGS.study),
    series_instance_uid: value(dataSet, TAGS.series),
    sop_instance_uid: value(dataSet, TAGS.sop),
    transfer_syntax_uid: value(dataSet, TAGS.transferSyntax),
    orientation_windowing: {
      orientation_patient: metadata.orientation_patient,
      window: displayWindow(metadata),
      color: metadata.photometric_interpretation || "UNKNOWN",
    },
  };
}

export async function parseDicomBytes(buffer, fileName = "unknown.dcm") {
  const bytes = new Uint8Array(buffer);
  const sourceSha256 = await sha256Bytes(bytes);
  const dataSet = parseDataSet(buffer);
  const technical = extractDicomTechnicalMetadata(dataSet);
  const frameCount = technical.number_of_frames || 1;
  return {
    fileName,
    sourceSha256,
    dataSet,
    technical,
    frameCount,
    sourceBytes: bytes,
    displayDerivative: async (frameNumber = 1) => generateDisplayDerivative(buffer, dataSet, technical, frameNumber),
  };
}

function scaleSample(valueToScale, min, max) {
  if (max <= min) return 0;
  return Math.max(0, Math.min(255, Math.round(((valueToScale - min) / (max - min)) * 255)));
}

function readPixels(buffer, frame, metadata) {
  const bytes = new Uint8Array(buffer);
  const view = new DataView(buffer);
  const count = metadata.rows * metadata.columns;
  const samples = metadata.samples_per_pixel || 1;
  const values = new Array(count);
  const colors = metadata.samples_per_pixel >= 3 ? new Array(count) : null;
  const signed = metadata.pixel_representation === 1;
  const bits = metadata.bits_allocated || 8;
  for (let index = 0; index < count; index += 1) {
    const offset = frame.offset + index * samples * frame.bytesPerSample;
    const readSample = (channel) => {
      const channelOffset = offset + channel * frame.bytesPerSample;
      if (bits <= 8) return bytes[channelOffset];
      if (signed) return view.getInt16(channelOffset, true);
      return view.getUint16(channelOffset, true);
    };
    values[index] = readSample(0);
    if (colors) {
      let [red, green, blue] = [readSample(0), readSample(1), readSample(2)];
      if (metadata.photometric_interpretation === "YBR_FULL") {
        const [y, cb, cr] = [red, green, blue];
        red = y + 1.402 * (cr - 128);
        green = y - 0.344136 * (cb - 128) - 0.714136 * (cr - 128);
        blue = y + 1.772 * (cb - 128);
      }
      colors[index] = [red, green, blue];
    }
  }
  return { values, colors };
}

export async function generateDisplayDerivative(buffer, dataSet, metadata, frameNumber = 1) {
  const frame = pixelFrame(dataSet, metadata, frameNumber);
  if (!frame) return { dataUrl: null, provenance: { available: false } };
  const { values, colors } = readPixels(buffer, frame, metadata);
  const isColor = Boolean(colors && ["RGB", "YBR_FULL"].includes(metadata.photometric_interpretation));
  const window = displayWindow(metadata);
  const min = window.center === null ? Math.min(...values) : window.center - window.width / 2;
  const max = window.center === null ? Math.max(...values) : window.center + window.width / 2;
  const canvas = globalThis.OffscreenCanvas
    ? new OffscreenCanvas(metadata.columns, metadata.rows)
    : globalThis.document?.createElement("canvas");
  if (!canvas) {
    return { dataUrl: null, provenance: { available: false, reason: "CANVAS_UNAVAILABLE", window } };
  }
  canvas.width = metadata.columns;
  canvas.height = metadata.rows;
  const context = canvas.getContext("2d");
  const image = context.createImageData(metadata.columns, metadata.rows);
  values.forEach((sample, index) => {
    const pixelIndex = index * 4;
    if (isColor) {
      image.data[pixelIndex] = Math.max(0, Math.min(255, Math.round(colors[index][0])));
      image.data[pixelIndex + 1] = Math.max(0, Math.min(255, Math.round(colors[index][1])));
      image.data[pixelIndex + 2] = Math.max(0, Math.min(255, Math.round(colors[index][2])));
    } else {
      const output = scaleSample(sample, min, max);
      image.data[pixelIndex] = output;
      image.data[pixelIndex + 1] = output;
      image.data[pixelIndex + 2] = output;
    }
    image.data[pixelIndex + 3] = 255;
  });
  context.putImageData(image, 0, 0);
  const dataUrl = canvas.convertToBlob
    ? await canvas.convertToBlob({ type: "image/png" }).then((blob) => blob.arrayBuffer()).then((result) => arrayBufferToDataUrl(result, "image/png"))
    : canvas.toDataURL("image/png");
  return {
    dataUrl,
    provenance: {
      available: true,
      frame_number: frameNumber,
      orientation_patient: metadata.orientation_patient,
      window: isColor ? { center: null, width: null, source: "COLOR_PRESERVED" } : window,
      color: metadata.photometric_interpretation || "UNKNOWN",
      preprocessing_version: "dicom-display-v0.1",
    },
  };
}
