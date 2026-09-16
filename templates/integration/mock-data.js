window.DR_REVIEW_MOCK_DATA = Object.freeze({
  project: {
    id: "DR-ROI-PILOT-01",
    name: "ROI Lesion Review Pilot",
    protocol: "ROI lesion taxonomy v0.1",
    source: "Synthetic / public demo only",
    completed: 38,
    total: 60,
  },
  task: {
    id: "TASK-0042",
    imageId: "DEMO-IMG-0042",
    laterality: "OD",
    modality: "CFP",
    reviewStatus: "IN_REVIEW",
    model: "roi-lesion-model 0.1.0-mock",
    roi: { id: "ROI-01", type: "rectangle", x: 0.53, y: 0.43, width: 0.18, height: 0.17 },
    predictions: [
      { label: "MICROANEURYSM", display: "Microaneurysm", score: 0.87 },
      { label: "INTRARETINAL_HEMORRHAGE", display: "Intraretinal hemorrhage", score: 0.08 },
      { label: "NO_SUPPORTED_LESION_IN_ROI", display: "No lesion detected", score: 0.03 },
      { label: "HARD_EXUDATE", display: "Hard exudate", score: 0.02 },
    ],
  },
  queue: [
    { id: "TASK-0042", status: "Ready", reason: "AI suggestion available" },
    { id: "TASK-0043", status: "Review", reason: "Low confidence" },
    { id: "TASK-0044", status: "Review", reason: "Reviewer disagreement" },
    { id: "TASK-0045", status: "Queued", reason: "No prediction" },
  ],
  recent: [
    { id: "TASK-0038", eye: "OD", label: "Hard exudate", decision: "Confirmed", reviewer: "Reviewer A" },
    { id: "TASK-0039", eye: "OS", label: "Microaneurysm", decision: "Corrected", reviewer: "Reviewer B" },
    { id: "TASK-0040", eye: "OD", label: "No lesion detected", decision: "Escalated", reviewer: "Reviewer A" },
  ],
});
