import { useEffect, useMemo, useState } from "react";
import { Box, Text } from "@chakra-ui/react";
import { AppShell } from "./components/AppShell";
import { createDemoCases } from "./data/demoData";
import { ManifestPage } from "./pages/ManifestPage";
import { QueuePage } from "./pages/QueuePage";
import { ReviewPage } from "./pages/ReviewPage";
import { SourcesPage } from "./pages/SourcesPage";
import { SummaryPage } from "./pages/SummaryPage";

const STORAGE_KEY = "ocuforge-product-poc-v1";

const defaultSourceConfig = {
  sourceType: "LOCAL_FOLDER",
  sourceReference: "C:\\hospital-data\\fundus",
  destinationType: "LOCAL_FOLDER",
  destinationReference: "C:\\ocuforge\\exports",
  selectedFileCount: 0,
};

function loadState() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
    if (saved?.cases?.length) return saved;
  } catch {
    // Browser storage is optional for the POC.
  }
  return { cases: createDemoCases(), sourceConfig: defaultSourceConfig, ingestion: { status: "IDLE" } };
}

export default function App() {
  const [state, setState] = useState(loadState);
  const [page, setPage] = useState("queue");
  const [selectedCaseId, setSelectedCaseId] = useState("CASE-0042");
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [toast, setToast] = useState(null);

  useEffect(() => { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); }, [state]);
  useEffect(() => { if (!toast) return undefined; const timeout = window.setTimeout(() => setToast(null), 3600); return () => window.clearTimeout(timeout); }, [toast]);

  const selectedCase = state.cases.find((item) => item.id === selectedCaseId) || state.cases[0];
  const sourceReady = Boolean(state.sourceConfig.sourceReference && state.sourceConfig.destinationReference);

  const showToast = (message, tone = "success") => setToast({ message, tone });
  const updateCase = (caseId, updater) => setState((current) => ({ ...current, cases: current.cases.map((item) => item.id === caseId ? updater(item) : item) }));

  const runAi = (caseId) => {
    updateCase(caseId, (item) => {
      if (item.systemPredictionId) return item;
      return {
        ...item,
        status: "AI_PROCESSED",
        systemGrade: [1, 2, 3, 0][item.id.charCodeAt(item.id.length - 1) % 4],
        systemConfidence: 0.89,
        systemPredictionId: `PRED-${item.id.slice(-4)}-01`,
        systemModelManifestId: "mock-encoder-head-0.1.0",
        trainingEligibility: "UNREVIEWED_SYSTEM",
        audit: [...item.audit, { actor: "SYSTEM", actorLabel: "System", at: new Date().toISOString(), event: "AI_PROCESSED", detail: "Mock bundle produced a versioned system prediction." }],
      };
    });
    showToast("System prediction saved. It remains separate from human review.");
  };

  const saveDraft = (caseId, changes = {}) => {
    updateCase(caseId, (item) => ({ ...item, ...changes, annotations: changes.annotation ? [...item.annotations, changes.annotation] : item.annotations, status: item.status === "AI_PROCESSED" ? "IN_REVIEW" : item.status, audit: changes.annotation ? [...item.audit, { actor: "reviewer-7f3a", actorLabel: "Reviewer", at: new Date().toISOString(), event: "ANNOTATION_DRAFTED", detail: `${changes.annotation.type} annotation added as USER provenance.` }] : item.audit }));
    showToast("Draft persisted locally.", "info");
  };

  const saveReview = (caseId, changes) => {
    updateCase(caseId, (item) => ({ ...item, ...changes, status: "EXPORTED", exportStatus: "VERIFIED", humanReviewStatus: "REVIEWED", humanReviewer: "reviewer-7f3a", trainingEligibility: "HUMAN", audit: [...item.audit, { actor: "reviewer-7f3a", actorLabel: "Reviewer", at: new Date().toISOString(), event: "HUMAN_REVIEWED", detail: `Human grade ${changes.humanGrade ?? "not set"} saved; system grade preserved.` }, { actor: "SYSTEM", actorLabel: "Export", at: new Date().toISOString(), event: "EXPORTED", detail: "POC export receipt verified at local destination." }] }));
    setPage("queue");
    showToast("Review saved, then export receipt verified.");
  };

  const openReview = (caseId) => {
    setSelectedCaseId(caseId);
    const item = state.cases.find((entry) => entry.id === caseId);
    if (item?.status === "AI_PROCESSED") updateCase(caseId, (current) => ({ ...current, status: "IN_REVIEW", audit: [...current.audit, { actor: "reviewer-7f3a", actorLabel: "Reviewer", at: new Date().toISOString(), event: "REVIEW_OPENED", detail: "Review session materialized by reviewer." }] }));
    setPage("review");
  };

  const startIngestion = () => {
    setState((current) => ({ ...current, ingestion: { status: "SCANNED", discovered: 8, accepted: 7, duplicates: 1, errors: 0 } }));
    showToast("Ingestion scan complete. Queue is ready.");
  };

  const resetDemo = () => { setState({ cases: createDemoCases(), sourceConfig: defaultSourceConfig, ingestion: { status: "IDLE" } }); setPage("queue"); setSelectedCaseId("CASE-0042"); showToast("Demo state reset.", "info"); };
  const rebuildManifest = () => showToast("Manifest rebuilt from persisted local review state.");

  const content = useMemo(() => {
    if (page === "sources") return <SourcesPage sourceConfig={state.sourceConfig} setSourceConfig={(value) => setState((current) => ({ ...current, sourceConfig: typeof value === "function" ? value(current.sourceConfig) : value }))} onIngest={startIngestion} ingestion={state.ingestion} />;
    if (page === "review") return <ReviewPage cases={state.cases} selectedCaseId={selectedCaseId} setSelectedCaseId={setSelectedCaseId} onRunAi={runAi} onSaveReview={saveReview} onSaveDraft={saveDraft} onBackToQueue={() => setPage("queue")} />;
    if (page === "summary") return <SummaryPage cases={state.cases} />;
    if (page === "manifest") return <ManifestPage cases={state.cases} onRebuild={rebuildManifest} />;
    return <QueuePage cases={state.cases} onOpenReview={openReview} />;
  }, [page, selectedCaseId, state]);

  return <AppShell page={page} onNavigate={setPage} onReset={resetDemo} sourceReady={sourceReady} queueCount={state.cases.length} mobileNavOpen={mobileNavOpen} setMobileNavOpen={setMobileNavOpen}>{content}{toast && <Box className={`toast-message toast-${toast.tone}`} role="status"><Text>{toast.message}</Text></Box>}</AppShell>;
}
