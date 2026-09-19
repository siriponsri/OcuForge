import { useMemo, useState } from "react";
import { Box, Button, Flex, Grid, HStack, Input, Text, Textarea, VStack } from "@chakra-ui/react";
import { ArrowLeft, Check, ChevronDown, Clock3, ExternalLink, History, Play, Save, Sparkles, Undo2, UserRound } from "lucide-react";
import { PageHeader } from "../components/PageHeader";
import { ReviewCanvas } from "../components/ReviewCanvas";
import { EligibilityBadge, ProvenanceBadge, StatusBadge } from "../components/StatusBadge";

const gradeOptions = [0, 1, 2, 3, 4];

function GradeSelect({ value, onChange, label }) {
  return <Box className="grade-select-wrap"><Text className="select-label">{label}</Text><select className="grade-select" value={value ?? ""} onChange={(event) => onChange(event.target.value === "" ? null : Number(event.target.value))}><option value="">Not set</option>{gradeOptions.map((grade) => <option key={grade} value={grade}>Grade {grade}</option>)}</select></Box>;
}

function SystemPanel({ item, onRunAi }) {
  return <Box className="surface-panel detail-panel system-panel"><Flex className="panel-title-row" align="center" justify="space-between"><HStack gap="2"><span className="panel-icon system-icon"><Sparkles size={16} /></span><Box><Text className="panel-kicker">System output</Text><Text className="panel-title">Auto label & DR grade</Text></Box></HStack><ProvenanceBadge provenance="SYSTEM" /></Flex>{item.systemGrade === null ? <Box className="run-ai-prompt"><Sparkles size={22} /><Text>AI is waiting for your explicit action.</Text><Button className="primary-action" onClick={onRunAi}><Play size={15} /> Run AI</Button></Box> : <><Flex className="system-grade-block" align="flex-end" justify="space-between"><Box><Text className="system-grade-label">System DR grade</Text><Text className="system-grade-value">{item.systemGrade}<span>/4</span></Text></Box><Box className="confidence-ring"><Text>{Math.round(item.systemConfidence * 100)}%</Text><small>confidence</small></Box></Flex><Box className="system-summary"><Text>Versioned mock bundle returned this prediction. It is not human ground truth.</Text><Text className="mono-line">{item.systemModelManifestId} <span>/</span> {item.systemPredictionId}</Text></Box><Flex className="system-meta-row" justify="space-between"><span>Preprocess <strong>fundus-display-v0.1</strong></span><span>Calibration <strong>none / POC</strong></span></Flex></>}</Box>;
}

function HumanPanel({ item, setHumanGrade, setRemark, onSave, onSaveDraft }) {
  return <Box className="surface-panel detail-panel human-panel"><Flex className="panel-title-row" align="center" justify="space-between"><HStack gap="2"><span className="panel-icon human-icon"><UserRound size={16} /></span><Box><Text className="panel-kicker">Human review</Text><Text className="panel-title">Record your decision</Text></Box></HStack><ProvenanceBadge provenance="USER" /></Flex><VStack align="stretch" gap="4"><GradeSelect label="Human reviewed DR grade" value={item.humanGrade} onChange={setHumanGrade} /><Box className="form-field compact-field"><Text as="label" htmlFor="review-remark">Remark</Text><Textarea id="review-remark" value={item.remark} onChange={(event) => setRemark(event.target.value)} placeholder="Add context for the next reviewer..." /></Box><Box className="training-callout"><Check size={16} /><Text><strong>Training eligibility:</strong> {item.humanGrade === null ? "UNREVIEWED_SYSTEM" : "HUMAN"}<small>{item.humanGrade === null ? "System output stays excluded until a human grade is saved." : "Explicit human review makes this row eligible for downstream selection."}</small></Text></Box><Flex className="human-actions" gap="2"><Button className="secondary-action" onClick={onSaveDraft}><Save size={15} /> Save draft</Button><Button className="primary-action" onClick={onSave}><Check size={15} /> Save & Return</Button></Flex></VStack></Box>;
}

function AuditPanel({ item }) {
  return <Box className="surface-panel detail-panel audit-panel"><Flex className="panel-title-row" align="center" justify="space-between"><HStack gap="2"><History size={17} /><Text className="panel-title">Immutable history</Text></HStack><Button className="text-action" variant="ghost"><ExternalLink size={14} /> Full audit</Button></Flex><VStack className="audit-list" align="stretch" gap="0">{item.audit.slice().reverse().map((event, index) => <Flex className="audit-event" key={`${event.event}-${index}`} gap="3"><span className={`audit-dot audit-${event.event.toLowerCase()}`} /><Box><Flex align="center" gap="2"><Text className="audit-event-name">{event.event.replaceAll("_", " ")}</Text><Text className="audit-actor">{event.actorLabel}</Text></Flex><Text className="audit-detail">{event.detail}</Text><Text className="audit-time"><Clock3 size={12} /> {new Date(event.at).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}</Text></Box></Flex>)}</VStack></Box>;
}

function Tile({ item, selected, onSelect }) {
  return <button type="button" className={`review-tile ${selected ? "is-selected" : ""}`} onClick={onSelect}><Box className="tile-image"><img src={item.imageUrl} alt="" />{item.annotations.slice(0, 2).map((annotation) => <span key={annotation.id} className={`tile-mark ${annotation.provenance.toLowerCase()}`} style={{ left: `${annotation.x * 100}%`, top: `${annotation.y * 100}%` }} />)}</Box><Flex className="tile-footer" justify="space-between" align="center"><Box><Text className="tile-id">{item.id}</Text><Text className="tile-file">{item.fileName}</Text></Box><StatusBadge status={item.status} /></Flex></button>;
}

export function ReviewPage({ cases, selectedCaseId, setSelectedCaseId, onRunAi, onSaveReview, onSaveDraft, onBackToQueue }) {
  const [layout, setLayout] = useState(1);
  const [tool, setTool] = useState("select");
  const [zoom, setZoom] = useState(1);
  const active = cases.find((item) => item.id === selectedCaseId) || cases[0];
  const [humanGrade, setHumanGrade] = useState(active.humanGrade);
  const [remark, setRemark] = useState(active.remark);

  const activeId = active.id;
  const visibleItems = useMemo(() => cases.filter((item) => item.status !== "ERROR").slice(0, layout), [cases, layout]);

  const selectCase = (id) => {
    setSelectedCaseId(id);
    const next = cases.find((item) => item.id === id);
    setHumanGrade(next?.humanGrade ?? null);
    setRemark(next?.remark ?? "");
  };

  const addAnnotation = (event) => {
    if (tool === "select") return;
    const rect = event.currentTarget.getBoundingClientRect();
    const x = Math.max(0.02, Math.min(0.8, (event.clientX - rect.left) / rect.width - 0.07));
    const y = Math.max(0.02, Math.min(0.78, (event.clientY - rect.top) / rect.height - 0.07));
    const shapes = { rectangle: { width: 0.18, height: 0.14, label: "User box" }, ellipse: { width: 0.16, height: 0.12, label: "User ellipse" }, polygon: { width: 0.2, height: 0.16, label: "User polygon" }, area: { width: 0.22, height: 0.18, label: "User area" }, point: { label: "User point" } };
    onSaveDraft(activeId, { annotation: { id: `ANN-U-${activeId}-${Date.now()}`, type: tool, x, y, provenance: "USER", ...(shapes[tool] || shapes.point) } });
    setTool("select");
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

    <Flex className="review-case-strip" align="center" justify="space-between" gap="4" wrap="wrap"><HStack gap="3"><Box className="case-avatar"><ScanIcon /></Box><Box><Text className="case-strip-id">{active.id} <span>·</span> {active.laterality}</Text><Text className="case-strip-source">{active.sourceFolder} <span>/</span> {active.fileName}</Text></Box></HStack><HStack gap="4"><Box className="case-strip-meta"><Text>Modality</Text><strong>{active.modality}</strong></Box><Box className="case-strip-meta"><Text>QC</Text><strong className="qc-pass">{active.qcStatus}</strong></Box><StatusBadge status={active.status} /></HStack></Flex>

    <Box className="surface-panel layout-toolbar"><HStack gap="3"><Text className="toolbar-label">Review layout</Text><HStack className="layout-switcher" gap="1">{[1, 2, 4, 8].map((value) => <button type="button" key={value} className={layout === value ? "is-active" : ""} onClick={() => setLayout(value)}>{value}</button>)}</HStack><Text className="toolbar-helper">Each image keeps independent review state.</Text></HStack><HStack gap="2"><span className="layout-note"><span className="live-dot" /> Live local state</span></HStack></Box>

    <Grid className="review-workspace-grid" templateColumns={{ base: "1fr", xl: "minmax(0, 1.32fr) minmax(21rem, .68fr)" }} gap="5">
      <Box><Box className={`review-tile-grid layout-${layout}`}>{visibleItems.map((item) => <Tile key={item.id} item={item} selected={item.id === activeId} onSelect={() => selectCase(item.id)} />)}</Box><ReviewCanvas item={active} tool={tool} onSelectTool={setTool} onCanvasClick={addAnnotation} onZoom={(amount) => setZoom((current) => Math.min(1.4, Math.max(.8, current + amount)))} /><Text className="review-disclaimer">POC workflow only. System predictions are preliminary model outputs, not diagnoses or clinical decisions.</Text></Box>
      <VStack className="review-sidebar" align="stretch" gap="4"><SystemPanel item={active} onRunAi={() => onRunAi(activeId)} /><HumanPanel item={{ ...active, humanGrade, remark }} setHumanGrade={setHumanGrade} setRemark={setRemark} onSave={() => commitReview("save")} onSaveDraft={() => commitReview("draft")} /><AuditPanel item={active} /></VStack>
    </Grid>
  </Box>;
}

function ScanIcon() {
  return <span className="scan-icon"><span /></span>;
}
