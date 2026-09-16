(function createAdapter(global) {
  "use strict";

  const config = global.DR_REVIEW_CONFIG;
  const mock = global.DR_REVIEW_MOCK_DATA;

  async function request(path, options) {
    const response = await fetch(`${config.modelApi.baseUrl}${path}`, {
      ...options,
      headers: { "Content-Type": "application/json", ...(options && options.headers) },
    });

    if (!response.ok) {
      throw new Error(`Model API returned ${response.status}.`);
    }

    return response.json();
  }

  const mockAdapter = {
    async getProject() {
      return structuredClone(mock.project);
    },
    async getTask() {
      return structuredClone(mock.task);
    },
    async inferGlobal(imageId) {
      return {
        image_id: imageId,
        status: "MOCK_RESPONSE",
        gradability: "GRADABLE",
        model: { name: "global-model", version: "not-connected" },
      };
    },
    async inferLesionRoi(payload) {
      return {
        model: { name: "roi-lesion-model", version: "0.1.0-mock" },
        roi_id: payload.roi.id || "ROI-01",
        predictions: structuredClone(mock.task.predictions),
      };
    },
    async getExplanation(payload) {
      return {
        status: "MOCK_RESPONSE",
        task_id: payload.task_id,
        method: "MIL_ATTENTION_ILLUSTRATIVE",
        not_lesion_localization: true,
        evidence_regions: [
          { rank: 1, region: "CENTRAL_TEMPORAL", relative_contribution: 0.42 },
          { rank: 2, region: "INFERIOR_TEMPORAL", relative_contribution: 0.27 },
          { rank: 3, region: "SUPERIOR_CENTRAL", relative_contribution: 0.16 },
        ],
      };
    },
    async compareModels(payload) {
      return { status: "MOCK_RESPONSE", comparison: payload, counts: { total: 160, improved: 9, regressed: 6, changed: 13, unchanged: 132 } };
    },
    async submitDecision(payload) {
      return { status: "RECORDED_IN_MOCK_SESSION", payload };
    },
    openLabelStudio(taskId) {
      const projectId = config.labelStudio.projectId || "{projectId}";
      const path = config.labelStudio.openTaskPath
        .replace("{projectId}", projectId)
        .replace("{taskId}", taskId);
      return `${config.labelStudio.baseUrl}${path}`;
    },
    async testConnection(kind) {
      await new Promise((resolve) => setTimeout(resolve, 450));
      return { kind, status: "MOCK_ONLY", message: "Configure a local endpoint to run a live test." };
    },
  };

  const liveAdapter = {
    async getProject() {
      const response = await fetch(`${config.apiBridge.baseUrl}${config.apiBridge.endpoints.project}`);
      if (!response.ok) throw new Error(`API bridge returned ${response.status}.`);
      return response.json();
    },
    async getTask(taskId) {
      const response = await fetch(`${config.apiBridge.baseUrl}${config.apiBridge.endpoints.tasks}/${taskId}`);
      if (!response.ok) throw new Error(`API bridge returned ${response.status}.`);
      return response.json();
    },
    async inferGlobal(imageId) {
      return request(config.modelApi.endpoints.global, {
        method: "POST",
        body: JSON.stringify({ image_id: imageId }),
      });
    },
    async inferLesionRoi(payload) {
      return request(config.modelApi.endpoints.lesionRoi, {
        method: "POST",
        body: JSON.stringify(payload),
      });
    },
    async getExplanation(payload) {
      return request(config.modelApi.endpoints.explainRoi, {
        method: "POST",
        body: JSON.stringify(payload),
      });
    },
    async compareModels(payload) {
      return request(config.modelApi.endpoints.modelDiff, {
        method: "POST",
        body: JSON.stringify(payload),
      });
    },
    async submitDecision(payload) {
      const response = await fetch(`${config.apiBridge.baseUrl}${config.apiBridge.endpoints.decisions}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) throw new Error(`API bridge returned ${response.status}.`);
      return response.json();
    },
    openLabelStudio: mockAdapter.openLabelStudio,
    async testConnection(kind) {
      const url = kind === "label-studio"
        ? `${config.apiBridge.baseUrl}${config.apiBridge.endpoints.labelStudioHealth}`
        : `${config.modelApi.baseUrl}${config.modelApi.endpoints.models}`;
      const response = await fetch(url, { method: "GET" });
      if (!response.ok) throw new Error(`${kind} returned ${response.status}.`);
      return { kind, status: "CONNECTED" };
    },
  };

  global.DRReviewAdapter = config.mode === "live" ? liveAdapter : mockAdapter;
})(window);
