const TRANSFER_SYNTAX = "1.2.840.10008.1.2.1";
const SOP_CLASS = "1.2.840.10008.5.1.4.1.1.7";
const IMPLEMENTATION = "1.2.826.0.1.3680043.10.543.1";

function evenBytes(text, pad = " ") {
  const value = `${text}${text.length % 2 ? pad : ""}`;
  return new TextEncoder().encode(value);
}

function uid(value) {
  return evenBytes(value, "\0");
}

function element(group, elementNumber, vr, valueBytes) {
  const header = new Uint8Array(8);
  const view = new DataView(header.buffer);
  view.setUint16(0, group, true);
  view.setUint16(2, elementNumber, true);
  header[4] = vr.charCodeAt(0);
  header[5] = vr.charCodeAt(1);
  view.setUint16(6, valueBytes.length, true);
  return concat(header, valueBytes);
}

function longElement(group, elementNumber, vr, valueBytes) {
  const header = new Uint8Array(12);
  const view = new DataView(header.buffer);
  view.setUint16(0, group, true);
  view.setUint16(2, elementNumber, true);
  header[4] = vr.charCodeAt(0);
  header[5] = vr.charCodeAt(1);
  view.setUint32(8, valueBytes.length, true);
  return concat(header, valueBytes);
}

function us(value) {
  const bytes = new Uint8Array(2);
  new DataView(bytes.buffer).setUint16(0, value, true);
  return bytes;
}

function concat(...parts) {
  const result = new Uint8Array(parts.reduce((total, part) => total + part.length, 0));
  let offset = 0;
  parts.forEach((part) => { result.set(part, offset); offset += part.length; });
  return result;
}

export function createSyntheticDicomBytes({ frames = 2, seed = 1 } = {}) {
  const studyUid = `1.2.826.0.1.3680043.10.543.100.${seed}`;
  const seriesUid = `1.2.826.0.1.3680043.10.543.200.${seed}`;
  const sopUid = `1.2.826.0.1.3680043.10.543.300.${seed}`;
  const metaWithoutLength = concat(
    longElement(0x0002, 0x0001, "OB", new Uint8Array([0, 1])),
    element(0x0002, 0x0002, "UI", uid(SOP_CLASS)),
    element(0x0002, 0x0003, "UI", uid(sopUid)),
    element(0x0002, 0x0010, "UI", uid(TRANSFER_SYNTAX)),
    element(0x0002, 0x0012, "UI", uid(IMPLEMENTATION)),
  );
  const meta = concat(element(0x0002, 0x0000, "UL", new Uint8Array(new Uint32Array([metaWithoutLength.length]).buffer)), metaWithoutLength);
  const rows = 32;
  const columns = 32;
  const pixels = new Uint8Array(rows * columns * frames);
  for (let frame = 0; frame < frames; frame += 1) {
    for (let index = 0; index < rows * columns; index += 1) {
      const x = index % columns;
      const y = Math.floor(index / columns);
      pixels[frame * rows * columns + index] = (x * 5 + y * 3 + frame * 40 + seed * 11) % 256;
    }
  }
  const dataset = concat(
    element(0x0008, 0x0060, "CS", evenBytes("OP")),
    element(0x0008, 0x0018, "UI", uid(sopUid)),
    element(0x0020, 0x000d, "UI", uid(studyUid)),
    element(0x0020, 0x000e, "UI", uid(seriesUid)),
    element(0x0020, 0x0062, "CS", evenBytes(seed % 2 ? "OD" : "OS")),
    element(0x0020, 0x0037, "DS", evenBytes("1\\0\\0\\0\\1\\0")),
    element(0x0028, 0x0002, "US", us(1)),
    element(0x0028, 0x0004, "CS", evenBytes("MONOCHROME2")),
    element(0x0028, 0x0008, "IS", evenBytes(String(frames), " ")),
    element(0x0028, 0x0010, "US", us(rows)),
    element(0x0028, 0x0011, "US", us(columns)),
    element(0x0028, 0x0030, "DS", evenBytes("0.01\\0.01")),
    element(0x0028, 0x0100, "US", us(8)),
    element(0x0028, 0x0101, "US", us(8)),
    element(0x0028, 0x0102, "US", us(7)),
    element(0x0028, 0x0103, "US", us(0)),
    element(0x0028, 0x1050, "DS", evenBytes("128")),
    element(0x0028, 0x1051, "DS", evenBytes("256")),
    longElement(0x7fe0, 0x0010, "OW", pixels),
  );
  const preamble = new Uint8Array(128);
  return concat(preamble, new TextEncoder().encode("DICM"), meta, dataset);
}

export function createSyntheticDicomFile(options = {}) {
  const bytes = createSyntheticDicomBytes(options);
  return new File([bytes], options.fileName || "synthetic-multiframe.dcm", { type: "application/dicom" });
}

export function createSyntheticFixtureFiles() {
  const rasterBytes = Uint8Array.from(atob("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="), (character) => character.charCodeAt(0));
  return [
    createSyntheticDicomFile({ seed: 1, frames: 2, fileName: "synthetic-multiframe.dcm" }),
    new File([rasterBytes], "synthetic-raster.png", { type: "image/png" }),
    new File([new TextEncoder().encode("not a DICOM object")], "malformed.dcm", { type: "application/dicom" }),
  ];
}
