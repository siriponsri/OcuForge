window.DR_REVIEW_CONFIG = Object.freeze({
  mode: "mock",
  labelStudio: {
    baseUrl: "http://localhost:8080",
    projectId: null,
    openTaskPath: "/projects/{projectId}/data?task={taskId}",
  },
  apiBridge: {
    baseUrl: "http://localhost:8787",
    endpoints: {
      project: "/api/ui/project",
      tasks: "/api/ui/tasks",
      decisions: "/api/ui/decisions",
      labelStudioHealth: "/api/health/label-studio",
    },
  },
  modelApi: {
    baseUrl: "http://localhost:8000",
    endpoints: {
      global: "/v1/infer/global",
      lesionRoi: "/v1/infer/lesion-roi",
      models: "/v1/models",
      explainRoi: "/v1/explain/roi",
      modelDiff: "/v1/evaluate/model-diff",
    },
  },
  review: {
    decisions: ["CONFIRM", "CORRECT", "REJECT", "ESCALATE"],
    supportedRoiLabels: [
      "MICROANEURYSM",
      "INTRARETINAL_HEMORRHAGE",
      "HARD_EXUDATE",
      "SOFT_EXUDATE",
      "NO_SUPPORTED_LESION_IN_ROI",
    ],
  },
});
