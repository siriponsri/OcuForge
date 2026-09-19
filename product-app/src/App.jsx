import { useEffect, useMemo, useRef, useState } from "react";
import { Box, Text } from "@chakra-ui/react";
import { AppShell } from "./components/AppShell";
import { createDemoCases } from "./data/demoData";
import { ManifestPage } from "./pages/ManifestPage";
import { QueuePage } from "./pages/QueuePage";
import { ReviewPage } from "./pages/ReviewPage";
import { SourcesPage } from "./pages/SourcesPage";
import { SummaryPage } from "./pages/SummaryPage";
import { AI_STATUS, EXPORT_STATUS, REVIEW_STATUS, withDerivedStatus } from "./product/constants";
import { hashJson } from "./product/crypto";
import { ingestFiles } from "./product/ingestion";
import { localFileSystemBridge } from "./product/localFileSystem";
import { MockModelAdapter } from "./product/modelAdapter";
import { createSyntheticFixtureFiles } from "./product/syntheticDicom";
import { caseRepository } from "./product/repository";
import { triggerExportDownload, writeExportPackage } from "./product/exporter";

const defaultSourceConfig = {
  sourceType: "LOCAL_FOLDER",
  sourceReference: "Local browser folder / synthetic fixture",
  destinationType: "LOCAL_FOLDER",
  destinationReference: "Local output folder / browser download fallback",
  outputPolicy: "REFERENCE_ONLY",
  selectedFileCount: 0,
  selectedInputLabel: "No folder selected",
  simulateExportFailure: false,
};

function initialState() {
  return { cases: createDemoCases(), sourceConfig: defaultSourceConfig, ingestion: { status: "IDLE" } };
}

function now() {
  return new Date().toISOString();
}

export default function App() {
  const [state, setState] = useState(initialState);
  const [hydrated, setHydrated] = useState(false);
  const [page, setPage] = useState("queue");
  const [selectedCaseId, setSelectedCaseId] = useState("CASE-0042");
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [toast, setToast] = useState(null);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const outputDirectoryHandle = useRef(null);

  useEffect(() => {
    caseRepository.loadState(initialState()).then((saved) => {
      setState(saved);
      setSelectedCaseId(saved.cases?.[0]?.id || "");
      setHydrated(true);
    });
  }, []);

  useEffect(() => {
    if (hydrated) caseRepository.saveState(state).catch(() => undefined);
  }, [state, hydrated]);

  useEffect(() => {
    if (!toast) return undefined;
    const timeout = window.setTimeout(() => setToast(null), 4200);
    return () => window.clearTimeout(timeout);
  }, [toast]);

  const selectedCase = state.cases.find((item) => item.id === selectedCaseId) || state.cases[0];
  const sourceReady = Boolean(state.sourceConfig.sourceReference && state.sourceConfig.destinationReference);
  const showToast = (message, tone = "success") => setToast({ message, tone });

  const updateCase = (caseId, updater) => {
    setState((current) => ({
      ...current,
      cases: current.cases.map((item) => item.id === caseId ? withDerivedStatus({ ...updater(item), updated_at: now() }) : item),
    }));
  };

  const updateSourceConfig = (value) => setState((current) => ({
    ...current,
    sourceConfig: typeof value === "function" ? value(current.sourceConfig) : value,
  }));

  const runAi = async (caseId) => {
    const item = state.cases.find((entry) => entry.id === caseId);
    if (!item || item.qcStatus === "QUARANTINED" || item.prediction_history?.length) return;
    updateCase(caseId, (current) => ({
      ...current,
      ai_status: AI_STATUS.RUNNING,
      audit: [...current.audit, { actor: "SYSTEM", actorLabel: "System", at: now(), event: "AI_RUNNING", detail: "Explicit Run AI requested; no inference occurs on open." }],
    }));
    try {
      const prediction = await MockModelAdapter.run({ imageId: item.imageId, sourceSha256: item.sourceSha256 });
      updateCase(caseId, (current) => ({
        ...current,
        ai_status: AI_STATUS.PROCESSED,
        prediction_history: [...current.prediction_history, prediction],
        annotations: [...current.annotations, ...prediction.annotations],
        systemGrade: prediction.system_dr_grade,
        systemConfidence: prediction.confidence,
        systemPredictionId: prediction.prediction_id,
        systemModelManifestId: prediction.model_manifest.model_manifest_id,
        audit: [...current.audit, { actor: "SYSTEM", actorLabel: "System", at: now(), event: "AI_PROCESSED", detail: "Deterministic mock bundle produced an immutable system prediction." }],
      }));
      showToast("System prediction saved. It remains separate from human review.");
    } catch (error) {
      updateCase(caseId, (current) => ({
        ...current,
        ai_status: AI_STATUS.FAILED,
        audit: [...current.audit, { actor: "SYSTEM", actorLabel: "System", at: now(), event: "AI_FAILED", detail: error.message }],
      }));
      showToast("AI failed; existing review state was preserved.", "error");
    }
  };

  const saveDraft = async (caseId, changes = {}) => {
    const current = state.cases.find((item) => item.id === caseId);
    if (!current) return;
    let nextAnnotations = current.annotations;
    let revision = null;
    const { annotation, annotationUpdate, ...reviewChanges } = changes;
    if (annotation) {
      nextAnnotations = [...current.annotations, annotation];
      revision = {
        revision_id: `REV-${caseId}-${Date.now()}`,
        revision_hash: await hashJson(nextAnnotations),
        schema_version: "annotation.v0.1",
        provenance: "USER",
        base_prediction_id: annotation.source_prediction_id || current.systemPredictionId || null,
        annotation_ids: nextAnnotations.map((annotation) => annotation.id),
        created_at: now(),
      };
    }
    if (annotationUpdate) {
      const target = current.annotations.find((entry) => entry.id === annotationUpdate.annotationId);
      if (target && annotationUpdate.label?.trim()) {
        const corrected = {
          ...target,
          id: `ANN-U-CORRECTION-${caseId}-${Date.now()}`,
          provenance: "USER",
          label: annotationUpdate.label.trim(),
          corrects_annotation_id: target.id,
          source_prediction_id: target.source_prediction_id || current.systemPredictionId || null,
        };
        nextAnnotations = [...current.annotations, corrected];
        revision = {
          revision_id: `REV-${caseId}-${Date.now()}`,
          revision_hash: await hashJson(nextAnnotations),
          schema_version: "annotation.v0.1",
          provenance: "USER",
          base_prediction_id: corrected.source_prediction_id,
          corrected_annotation_id: target.id,
          annotation_ids: nextAnnotations.map((entry) => entry.id),
          created_at: now(),
        };
      }
    }
    updateCase(caseId, (item) => ({
      ...item,
      ...reviewChanges,
      annotations: nextAnnotations,
      annotation_revisions: revision ? [...item.annotation_revisions, revision] : item.annotation_revisions,
      review_status: item.review_status === REVIEW_STATUS.HUMAN_REVIEWED ? item.review_status : REVIEW_STATUS.IN_REVIEW,
      audit: annotation ? [...item.audit, { actor: "reviewer-7f3a", actorLabel: "Reviewer", at: now(), event: "ANNOTATION_DRAFTED", detail: `${annotation.type} annotation added as USER provenance.` }] : annotationUpdate ? [...item.audit, { actor: "reviewer-7f3a", actorLabel: "Reviewer", at: now(), event: "ANNOTATION_CORRECTED", detail: "A new USER annotation revision was created; the previous geometry remains immutable." }] : item.audit,
    }));
    showToast("Draft persisted locally.", "info");
  };

  const exportCase = async (caseToExport) => {
    if (state.sourceConfig.simulateExportFailure) throw new Error("Simulated destination failure for recovery testing.");
    const sourceBlob = await caseRepository.getObject(caseToExport.sourceObjectKey);
    return writeExportPackage(caseToExport, outputDirectoryHandle.current, sourceBlob);
  };

  const saveReview = async (caseId, changes) => {
    const current = state.cases.find((item) => item.id === caseId);
    if (!current) return;
    const reviewed = withDerivedStatus({
      ...current,
      ...changes,
      review_status: REVIEW_STATUS.HUMAN_REVIEWED,
      humanReviewStatus: "REVIEWED",
      humanReviewer: "reviewer-7f3a",
      human_grading_protocol: "DR-GRADING-PROTOCOL-v0.1",
      human_reviewed_at: now(),
      trainingEligibility: changes.humanGrade === null ? "UNREVIEWED_SYSTEM" : "HUMAN",
      audit: [...current.audit, { actor: "reviewer-7f3a", actorLabel: "Reviewer", at: now(), event: "HUMAN_REVIEWED", detail: `Human grade ${changes.humanGrade ?? "not set"} saved; system grade preserved.` }],
    });
    const persisted = { ...state, cases: state.cases.map((item) => item.id === caseId ? reviewed : item) };
    setState(persisted);
    await caseRepository.saveState(persisted);
    await finishExport(caseId, reviewed);
    setPage("queue");
  };

  const finishExport = async (caseId, reviewedItem) => {
    updateCase(caseId, (item) => ({ ...item, export_status: EXPORT_STATUS.EXPORTING, audit: [...item.audit, { actor: "SYSTEM", actorLabel: "Export", at: now(), event: "EXPORTING", detail: "Review persisted; export started idempotently." }] }));
    try {
      const exportResult = await exportCase(reviewedItem);
      if (!outputDirectoryHandle.current) triggerExportDownload(reviewedItem, exportResult);
      updateCase(caseId, (item) => ({
        ...item,
        export_status: EXPORT_STATUS.EXPORTED,
        export_uri: exportResult.exportUri,
        export_hash: exportResult.exportHash,
        annotation_artifact_uri: `${exportResult.exportUri}/annotations.json`,
        audit: [...item.audit, { actor: "SYSTEM", actorLabel: "Export", at: now(), event: "EXPORTED", detail: `Export receipt verified; ${exportResult.fileNames.length} logical artifacts prepared.` }],
      }));
      showToast(outputDirectoryHandle.current ? "Review saved and artifacts written to the local folder." : "Review saved; export package downloaded for local storage.");
    } catch (error) {
      updateCase(caseId, (item) => ({
        ...item,
        export_status: EXPORT_STATUS.FAILED,
        audit: [...item.audit, { actor: "SYSTEM", actorLabel: "Export", at: now(), event: "EXPORT_FAILED", detail: error.message }],
      }));
      showToast("Review saved. Export failed and can be retried without losing the review.", "error");
    }
  };

  const retryExport = async (caseId) => {
    const item = state.cases.find((entry) => entry.id === caseId);
    if (item) await finishExport(caseId, item);
  };

  const openReview = (caseId) => {
    setSelectedCaseId(caseId);
    const item = state.cases.find((entry) => entry.id === caseId);
    if (item && item.qcStatus !== "QUARANTINED") {
      updateCase(caseId, (current) => ({ ...current, review_status: REVIEW_STATUS.IN_REVIEW, audit: [...current.audit, { actor: "reviewer-7f3a", actorLabel: "Reviewer", at: now(), event: "REVIEW_OPENED", detail: current.review_status === REVIEW_STATUS.HUMAN_REVIEWED ? "Correction session opened; prior human review remains in immutable history." : "Review session opened; AI remains explicit." }] }));
    }
    setPage("review");
  };

  const handleFilesSelected = (files) => {
    setSelectedFiles(files);
    updateSourceConfig((current) => ({ ...current, selectedFileCount: files.length, selectedInputLabel: localFileSystemBridge.describeInput(files) }));
    showToast(`${files.length} local file${files.length === 1 ? "" : "s"} staged for ingestion.`, "info");
  };

  const stageSyntheticFixtures = () => {
    const files = createSyntheticFixtureFiles();
    handleFilesSelected(files);
  };

  const chooseOutputDirectory = async () => {
    try {
      const handle = await localFileSystemBridge.chooseOutputDirectory();
      if (!handle) {
        showToast("This browser does not expose a directory picker; exports use the download fallback.", "info");
        return;
      }
      outputDirectoryHandle.current = handle;
      updateSourceConfig((current) => ({ ...current, destinationReference: `Local folder handle / ${handle.name}` }));
      showToast("Local output folder connected.");
    } catch (error) {
      if (error.name !== "AbortError") showToast(`Output folder unavailable: ${error.message}`, "error");
    }
  };

  const startIngestion = async () => {
    const files = selectedFiles.length ? selectedFiles : createSyntheticFixtureFiles();
    setState((current) => ({ ...current, ingestion: { status: "SCANNING", discovered: files.length } }));
    try {
      const result = await ingestFiles(files, state.sourceConfig, caseRepository, state.cases);
      setState((current) => ({ ...current, cases: [...current.cases, ...result.cases], ingestion: { status: "SCANNED", ...result } }));
      showToast(`Ingestion complete: ${result.accepted} accepted, ${result.quarantined} quarantined, ${result.duplicates} duplicate.`);
    } catch (error) {
      setState((current) => ({ ...current, ingestion: { status: "FAILED", error: error.message } }));
      showToast(`Ingestion failed: ${error.message}`, "error");
    }
  };

  const resetDemo = async () => {
    await caseRepository.clear();
    setState(initialState());
    setSelectedFiles([]);
    setPage("queue");
    setSelectedCaseId("CASE-0042");
    showToast("Demo state reset.", "info");
  };

  const content = useMemo(() => {
    if (!selectedCase && page !== "sources") return <Box className="empty-state"><Text>No cases are available yet. Start with Sources.</Text></Box>;
    if (page === "sources") return <SourcesPage sourceConfig={state.sourceConfig} setSourceConfig={updateSourceConfig} onFilesSelected={handleFilesSelected} onSyntheticFixtures={stageSyntheticFixtures} onChooseOutput={chooseOutputDirectory} onIngest={startIngestion} ingestion={state.ingestion} />;
    if (page === "review") return <ReviewPage cases={state.cases} selectedCaseId={selectedCaseId} setSelectedCaseId={setSelectedCaseId} onRunAi={runAi} onSaveReview={saveReview} onSaveDraft={saveDraft} onRetryExport={retryExport} onBackToQueue={() => setPage("queue")} />;
    if (page === "summary") return <SummaryPage cases={state.cases} />;
    if (page === "manifest") return <ManifestPage cases={state.cases} onRebuild={() => showToast("Manifest rebuilt from persisted local review state.", "info")} />;
    return <QueuePage cases={state.cases} onOpenReview={openReview} onRetryExport={retryExport} />;
  }, [page, selectedCaseId, selectedCase, state]);

  return <AppShell page={page} onNavigate={setPage} onReset={resetDemo} sourceReady={sourceReady} queueCount={state.cases.length} mobileNavOpen={mobileNavOpen} setMobileNavOpen={setMobileNavOpen}>
    {content}
    {toast && <Box className={`toast-message toast-${toast.tone}`} role="status"><Text>{toast.message}</Text></Box>}
  </AppShell>;
}
