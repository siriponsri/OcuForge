import { hashJson } from "./crypto.js";

export const MOCK_MODEL_BUNDLE = {
  model_manifest_id: "mock-bundle-v0.1.0",
  encoder_id: "mock-encoder",
  head_id: "mock-dr-head",
  preprocessing_version: "fundus-display-v0.1",
  calibration_version: "none-poc",
  adapter_contract_version: "model-adapter.v0.1",
  runtime: "browser-local-deterministic",
};

export const MockModelAdapter = {
  async run({ imageId, sourceSha256 }) {
    const digest = await hashJson({ imageId, sourceSha256 });
    const grade = parseInt(digest.slice(0, 2), 16) % 5;
    const confidence = 0.7 + (parseInt(digest.slice(2, 4), 16) / 255) * 0.25;
    const x = 0.22 + (parseInt(digest.slice(4, 6), 16) / 255) * 0.45;
    const y = 0.24 + (parseInt(digest.slice(6, 8), 16) / 255) * 0.42;
    const predictionId = `PRED-${imageId}-${digest.slice(0, 8)}`;
    return {
      prediction_id: predictionId,
      model_manifest: MOCK_MODEL_BUNDLE,
      system_dr_grade: grade,
      confidence: Number(confidence.toFixed(4)),
      probabilities: Array.from({ length: 5 }, (_, index) => Number((index === grade ? confidence : (1 - confidence) / 4).toFixed(4))),
      annotations: [{
        id: `${predictionId}-ANN-01`,
        type: grade > 0 ? "ellipse" : "point",
        x,
        y,
        width: grade > 0 ? 0.16 : undefined,
        height: grade > 0 ? 0.12 : undefined,
        provenance: "SYSTEM",
        label: grade > 0 ? "System suggestion" : "System point",
        source_prediction_id: predictionId,
      }],
      created_at: "1970-01-01T00:00:00.000Z",
    };
  },
};
