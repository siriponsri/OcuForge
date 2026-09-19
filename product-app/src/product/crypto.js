export async function sha256Bytes(input) {
  const bytes = input instanceof Uint8Array ? input : new Uint8Array(input);
  if (!globalThis.crypto?.subtle) {
    throw new Error("Web Crypto SHA-256 is required for the local POC.");
  }
  const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

export async function sha256Blob(blob) {
  return sha256Bytes(await blob.arrayBuffer());
}

export function arrayBufferToDataUrl(buffer, mimeType = "application/octet-stream") {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  const chunkSize = 0x8000;
  for (let offset = 0; offset < bytes.length; offset += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(offset, offset + chunkSize));
  }
  return `data:${mimeType};base64,${btoa(binary)}`;
}

export function dataUrlToBytes(dataUrl) {
  const encoded = dataUrl.split(",")[1] || "";
  const binary = atob(encoded);
  return Uint8Array.from(binary, (character) => character.charCodeAt(0));
}

export function shortHash(value, length = 16) {
  return value ? value.slice(0, length) : "";
}

export function stableJson(value) {
  if (Array.isArray(value)) return value.map(stableJson);
  if (!value || typeof value !== "object") return value;
  return Object.keys(value).sort().reduce((result, key) => {
    result[key] = stableJson(value[key]);
    return result;
  }, {});
}

export async function hashJson(value) {
  return sha256Bytes(new TextEncoder().encode(JSON.stringify(stableJson(value))));
}
