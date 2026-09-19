import { useEffect, useMemo, useState } from "react";
import { Box, Button, Flex, Grid, HStack, Input, Text, Textarea, VStack } from "@chakra-ui/react";
import { AlertTriangle, ArrowLeft, Check, ChevronDown, Clock3, ExternalLink, History, Play, Save, Sparkles, UserRound } from "lucide-react";
import { PageHeader } from "../components/PageHeader";
import { ReviewCanvas } from "../components/ReviewCanvas";
import { EligibilityBadge, ProvenanceBadge, StatusBadge } from "../components/StatusBadge";
import { deriveQueueBadge } from "../product/constants";

const gradeOptions = [0, 1, 2, 3, 4];

function GradeSelect({ value, onChange, label }) {
  return <Box className="grade-select-wrap"><Text className="select-label">{label}</Text><select className="grade-select" value={value ?? ""} onChange={(event) => onChange(event.target.value === "" ? null : Number(event.target.value))}><option value="">Not set</option>{gradeOptions.map((grade) => <option key={grade} value={grade}>Grade {grade}</option>)}</select></Box>;
}

function SystemPanel({ item, onRunAi }) {
  const prediction = item.prediction_history?.at(-1);
  return <Box className="surface-panel detail-panel system-panel"><Flex className="panel-title-row" align="center" justify="space-between"><HStack gap="2"><span className="panel-icon system-icon"><Sparkles size={16} /></span><Box><Text className="panel-kicker">System output</Text><Text className="panel-title">Auto label & DR grade</Text></Box></HStack><ProvenanceBadge provenance="SYSTEM" /></Flex>{item.qcStatus === "QUARANTINED" ? <Box className="run-ai-prompt"><AlertTriangle size={22} /><Text>This source is quarantined and cannot run AI.</Text><Text className="field-helper">{item.quarantineReason}</Text></Box> : !prediction ? <Box className="run-ai-prompt"><Sparkles size={22} /><Text>{item.ai_status === "RUNNING" ? "AI is running locally..." : "AI is waiting for your explicit action."}</Text><Button className="primary-action" onClick={onRunAi} disabled={item.ai_status === "RUNNING"}><Play size={15} /> {item.ai_status === "FAILED" ? "Retry AI" : "Run AI"}</Button></Box> : <><Flex className="system-grade-block" align="flex-end" justify="space-between"><Box><Text className="system-grade-label">System DR grade</Text><Text className="system-grade-value">{item.systemGrade}<span>/4</span></Text></Box><Box className="confidence-ring"><Text>{Math.round(item.systemConfidence * 100)}%</Text><small>confidence</small></Box></Flex><Box className="system-summary"><Text>Versioned adapter output. It is not human ground truth and remains immutable after correction.</Text><Text className="mono-line">{prediction.model_manifest.model_manifest_id} <span>/</span> {prediction.prediction_id}</Text></Box><Flex className="system-meta-row" justify="space-between"><span>Preprocess <strong>{prediction.model_manifest.preprocessing_version}</strong></span><span>Calibration <strong>{prediction.model_manifest.calibration_version}</strong></span></Flex></>}</Box>;
}

function HumanPanel({ item, annotationLabel, setAnnotationLabel, selectedAnnotation, setHumanGrade, setRemark, onSave, onSaveDraft, onSaveAnnotationLabel }) {
  const eligibility = item.humanGrade === null ? "UNREVIEWED_SYSTEM" : "HUMAN";
  return <Box className="surface-panel detail-panel human-panel"><Flex className="panel-title-row" align="center" justify="space-between"><HStack gap="2"><span className="panel-icon human-icon"><UserRound size={16} /></span><Box><Text className="panel-kicker">Human review</Text><Text className="panel-title">Record your decision</Text></Box></HStack><ProvenanceBadge provenance="USER" /></Flex><VStack align="stretch" gap="4"><GradeSelect label="Human reviewed DR grade" value={item.humanGrade} onChange={setHumanGrade} /><Box className="form-field compact-field"><Text as="label" htmlFor="annotation-label">Annotation label</Text><HStack gap="2"><Input id="annotation-label" value={annotationLabel} onChange={(event) => setAnnotationLabel(event.target.value)} placeholder="Select an annotation or add a label" /><Button className="secondary-action" onClick={onSaveAnnotationLabel} disabled={!selectedAnnotation || !annotationLabel.trim()}>Apply</Button></HStack><Text className="field-helper">{selectedAnnotation ? `${selectedAnnotation.provenance} annotation selected; applying creates a new USER revision.` : "Select a system or user annotation on the canvas to correct its label."}</Text></Box><Box className="form-field compact-field"><Text as="label" htmlFor="review-remark">Remark</Text><Textarea id="review-remark" value={item.remark} onChange={(event) => setRemark(event.target.value)} placeholder="Add context for the next reviewer..." /></Box><Box className="training-callout"><Check size={16} /><Text><strong>Training eligibility:</strong> {eligibility}<small>{eligibility === "HUMAN" ? "Explicit human review makes this row eligible for downstream selection." : "System output stays excluded until a human grade is saved."}</small></Text><EligibilityBadge value={eligibility} /></Box><Flex className="human-actions" gap="2"><Button className="secondary-action" onClick={onSaveDraft}><Save size={15} /> Save draft</Button><Button className="primary-action" onClick={onSave}><Check size={15} /> Save & Return</Button></Flex></VStack></Box>;
}

function AuditPanel({ item }) {
  return <Box className="surface-panel detail-panel audit-panel"><Flex className="panel-title-row" align="center" justify="space-between"><HStack gap="2"><History size={17} /><Text className="panel-title">Immutable history</Text></HStack><Button className="text-action" variant="ghost"><ExternalLink size={14} /> Full audit</Button></Flex><VStack className="audit-list" align="stretch" gap="0">{item.audit.slice().reverse().map((event, index) => <Flex className="audit-event" key={`${event.event}-${index}`} gap="3"><span className={`audit-dot audit-${event.event.toLowerCase()}`} /><Box><Flex align="center" gap="2"><Text className="audit-event-name">{event.event.replaceAll("_", " ")}</Text><Text className="audit-actor">{event.actorLabel}</Text></Flex><Text className="audit-detail">{event.detail}</Text><Text className="audit-time"><Clock3 size={12} /> {new Date(event.at).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}</Text></Box></Flex>)}</VStack></Box>;
}

function Tile({ item, selected, onSelect }) {
  return <button type="button" className={`review-tile ${selected ? "is-selected" : ""}`} onClick={onSelect}><Box className="tile-image">{item.imageUrl ? <img src={item.imageUrl} alt="" /> : <span className="tile-empty">No display derivative</span>}{item.annotations.slice(0, 2).map((annotation) => <span key={annotation.id} className={`tile-mark ${annotation.provenance.toLowerCase()}`} style={{ left: `${annotation.x * 100}%`, top: `${annotation.y * 100}%` }} />)}</Box><Flex className="tile-footer" justify="space-between" align="center"><Box><Text className="tile-id">{item.id}</Text><Text className="tile-file">{item.fileName}{item.frame_count > 1 ? ` · frame ${item.frame_number}` : ""}</Text></Box><StatusBadge status={deriveQueueBadge(item)} /></Flex></button>;
}

export function ReviewPage({ cases, selectedCaseId, setSelectedCaseId, onRunAi, onSaveReview, onSaveDraft, onRetryExport, onBackToQueue }) {
  const [layout, setLayout] = useState(1);
  const [tool, setTool] = useState("select");
  const [humanGrade, setHumanGrade] = useState(null);
  const [remark, setRemark] = useState("");
  const [annotationLabel, setAnnotationLabel] = useState("User annotation");
  const [selectedAnnotationId, setSelectedAnnotationId] = useState(null);
  const active = cases.find((item) => item.id === selectedCaseId) || cases[0];
  const activeId = active.id;

  useEffect(() => {
    setHumanGrade(active.humanGrade);
    setRemark(active.remark || "");
    setAnnotationLabel("User annotation");
    setSelectedAnnotationId(null);
  }, [activeId, active.humanGrade, active.remark]);

  const visibleItems = useMemo(() => cases.filter((item) => item.qcStatus !== "QUARANTINED").slice(0, layout), [cases, layout]);
  const selectCase = (id) => setSelectedCaseId(id);
  const selectedAnnotation = active.annotations.find((annotation) => annotation.id === selectedAnnotationId) || null;
  const selectAnnotation = (annotation) => {
    setSelectedAnnotationId(annotation.id);
    setAnnotationLabel(annotation.label || "User annotation");
  };
  const addAnnotation = (event) => {
    if (tool === "select") return;
    const imageFrame = event.currentTarget.querySelector(".image-frame");
    if (!imageFrame) return;
    const rect = imageFrame.getBoundingClientRect();
    const x = Math.max(0.02, Math.min(0.92, (event.clientX - rect.left) / rect.width));
    const y = Math.max(0.02, Math.min(0.92, (event.clientY - rect.top) / rect.height));
    const shapes = { rectangle: { width: 0.18, height: 0.14 }, ellipse: { width: 0.16, height: 0.12 }, polygon: { width: 0.2, height: 0.16 }, area: { width: 0.22, height: 0.18 }, point: {} };
    onSaveDraft(activeId, { annotation: { id: `ANN-U-${activeId}-${Date.now()}`, type: tool, x, y, provenance: "USER", label: annotationLabel.trim() || `User ${tool}`, ...(shapes[tool] || shapes.point), source_prediction_id: active.systemPredictionId || null } });
    setTool("select");
  };
  const saveAnnotationLabel = () => {
    if (selectedAnnotation) onSaveDraft(activeId, { annotationUpdate: { annotationId: selectedAnnotation.id, label: annotationLabel.trim() } });
  };
  const commitReview = (mode) => {
    const updated = { humanGrade, remark };
    if (mode === "draft") onSaveDraft(activeId, updated);
    else onSaveReview(activeId, updated);
  };

  return <Box>
    <PageHeader eyebrow="Workspace / Review & Label" title="Review & Label" description="Keep system evidence visible while building a human-reviewed record.">
      <HStack className="review-breadcrumb" gap="2"><Button className="text-action" variant="ghost" onClick={onBackToQueue}><ArrowLeft size={15} /> Back to queue</Button><span>/</span><Text>{active.id}</Text></HStack>
    </PageHeader>

    <Flex className="review-case-strip" align="center" justify="space-between" gap="4" wrap="wrap"><HStack gap="3"><Box className="case-avatar"><ScanIcon /></Box><Box><Text className="case-strip-id">{active.id} <span>/</span> {active.laterality || "-"}</Text><Text className="case-strip-source">{active.sourceFolder} <span>/</span> {active.fileName}</Text></Box></HStack><HStack gap="4"><Box className="case-strip-meta"><Text>Modality</Text><strong>{active.modality}</strong></Box><Box className="case-strip-meta"><Text>QC</Text><strong className={active.qcStatus === "PASS" ? "qc-pass" : "qc-fail"}>{active.qcStatus}</strong></Box><StatusBadge status={deriveQueueBadge(active)} /></HStack></Flex>

    <Box className="surface-panel layout-toolbar"><HStack gap="3"><Text className="toolbar-label">Review layout</Text><HStack className="layout-switcher" gap="1">{[1, 2, 4, 8].map((value) => <button type="button" key={value} className={layout === value ? "is-active" : ""} onClick={() => setLayout(value)}>{value}</button>)}</HStack><Text className="toolbar-helper">Each image keeps independent review state.</Text></HStack><HStack gap="2"><span className="layout-note"><span className="live-dot" /> Live local state</span></HStack></Box>

    <Grid className="review-workspace-grid" templateColumns={{ base: "1fr", xl: "minmax(0, 1.32fr) minmax(21rem, .68fr)" }} gap="5">
      <Box><Box className={`review-tile-grid layout-${layout}`}>{visibleItems.map((item) => <Tile key={item.id} item={item} selected={item.id === activeId} onSelect={() => selectCase(item.id)} />)}</Box><ReviewCanvas item={active} tool={tool} selectedAnnotationId={selectedAnnotationId} onSelectTool={setTool} onCanvasClick={addAnnotation} onSelectAnnotation={selectAnnotation} /><Text className="review-disclaimer">POC workflow only. System predictions are preliminary model outputs, not diagnoses or clinical decisions. Original DICOM is never overwritten.</Text></Box>
      <VStack className="review-sidebar" align="stretch" gap="4"><SystemPanel item={active} onRunAi={() => onRunAi(activeId)} /><HumanPanel item={{ ...active, humanGrade, remark }} annotationLabel={annotationLabel} setAnnotationLabel={setAnnotationLabel} selectedAnnotation={selectedAnnotation} setHumanGrade={setHumanGrade} setRemark={setRemark} onSaveAnnotationLabel={saveAnnotationLabel} onSave={() => commitReview("save")} onSaveDraft={() => commitReview("draft")} /><>{active.export_status === "FAILED" && <Box className="surface-panel export-recovery"><Flex align="center" justify="space-between" gap="3"><Box><Text className="panel-kicker">Export recovery</Text><Text className="panel-title">Review is safe; retry export</Text></Box><Button className="secondary-action" onClick={() => onRetryExport(active.id)}><RefreshIcon /> Retry</Button></Flex><Text className="field-helper">Export failure does not revert HUMAN_REVIEWED or alter the immutable prediction.</Text></Box>}</><AuditPanel item={active} /></VStack>
    </Grid>
  </Box>;
}

function ScanIcon() { return <span className="scan-icon"><span /></span>; }
function RefreshIcon() { return <span aria-hidden="true">↻</span>; }
