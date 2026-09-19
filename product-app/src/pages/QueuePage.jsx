import { useState } from "react";
import { Box, Button, Flex, HStack, Input, Text } from "@chakra-ui/react";
import { ArrowUpDown, ChevronRight, Filter, Play, Search, SlidersHorizontal } from "lucide-react";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { QUEUE_STATES } from "../data/demoData";

function Grade({ value, muted = false }) {
  return <span className={`grade-value ${muted ? "is-muted" : ""}`}>{value === null || value === undefined ? "-" : `Grade ${value}`}</span>;
}

export function QueuePage({ cases, onOpenReview }) {
  const [query, setQuery] = useState("");
  const [stateFilter, setStateFilter] = useState("ALL");
  const filtered = cases.filter((item) => {
    const matchesQuery = `${item.id} ${item.fileName} ${item.sourceFolder}`.toLowerCase().includes(query.toLowerCase());
    return matchesQuery && (stateFilter === "ALL" || item.status === stateFilter);
  });
  const counts = QUEUE_STATES.reduce((result, state) => ({ ...result, [state]: cases.filter((item) => item.status === state).length }), {});

  return (
    <Box>
      <PageHeader eyebrow="Workspace / Queue" title="Review queue" description="A durable worklist with system output and human review kept in separate columns.">
        <Button className="secondary-action"><Filter size={15} /> Saved view</Button>
        <Button className="primary-action" onClick={() => onOpenReview(cases.find((item) => item.status === "AI_PROCESSED")?.id || cases[0].id)}><Play size={15} /> Open next review</Button>
      </PageHeader>

      <Flex className="queue-metrics" gap="3" wrap="wrap">
        <Box className="metric-card metric-card-accent"><Text className="metric-label">Needs attention</Text><Text className="metric-value">{(counts.NOT_PROCESSED || 0) + (counts.AI_PROCESSED || 0) + (counts.IN_REVIEW || 0)}</Text><Text className="metric-detail">across the active worklist</Text></Box>
        <Box className="metric-card"><Text className="metric-label">Human reviewed</Text><Text className="metric-value">{(counts.HUMAN_REVIEWED || 0) + (counts.EXPORTED || 0)}</Text><Text className="metric-detail">system grade remains visible</Text></Box>
        <Box className="metric-card"><Text className="metric-label">Exported</Text><Text className="metric-value">{counts.EXPORTED || 0}</Text><Text className="metric-detail">verified at destination</Text></Box>
        <Box className="metric-card"><Text className="metric-label">Errors</Text><Text className="metric-value">{counts.ERROR || 0}</Text><Text className="metric-detail">retryable item-level issues</Text></Box>
      </Flex>

      <Box className="surface-panel queue-panel">
        <Flex className="queue-toolbar" align="center" justify="space-between" gap="3" wrap="wrap"><HStack className="search-box" gap="2"><Search size={17} /><Input aria-label="Search queue" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search ID, filename or folder" /></HStack><HStack gap="2"><select className="select-control" aria-label="Filter by queue state" value={stateFilter} onChange={(event) => setStateFilter(event.target.value)}><option value="ALL">All states ({cases.length})</option>{QUEUE_STATES.map((state) => <option key={state} value={state}>{state.replaceAll("_", " ")} ({counts[state] || 0})</option>)}</select><Button className="icon-button" variant="ghost" aria-label="Queue filters"><SlidersHorizontal size={17} /></Button></HStack></Flex>
        <Box className="table-scroll"><table className="data-table queue-table"><thead><tr><th>Case</th><th>Source folder</th><th>Modality</th><th>System DR grade</th><th>Human reviewed grade</th><th>Status</th><th>Eligibility</th><th /></tr></thead><tbody>{filtered.map((item) => <tr key={item.id} onClick={() => onOpenReview(item.id)} className="table-row-clickable"><td><Box><Text className="case-id">{item.id}</Text><Text className="file-name">{item.fileName}</Text></Box></td><td><Text className="folder-name">{item.sourceFolder}</Text><Text className="source-ref">{item.sourceSha256.slice(0, 18)}...</Text></td><td><HStack gap="2"><span className={`modality-dot ${item.modality === "DICOM" ? "is-dicom" : ""}`} />{item.modality} <span className="laterality">{item.laterality}</span></HStack></td><td><Grade value={item.systemGrade} muted={item.systemGrade === null} />{item.systemConfidence && <Text className="confidence-text">{Math.round(item.systemConfidence * 100)}% confidence</Text>}</td><td><Grade value={item.humanGrade} muted={item.humanGrade === null} />{item.humanReviewer && <Text className="confidence-text">{item.humanReviewer}</Text>}</td><td><StatusBadge status={item.status} /></td><td><span className={`eligibility-badge eligibility-${item.trainingEligibility.toLowerCase()}`}>{item.trainingEligibility}</span></td><td><ChevronRight size={17} className="row-chevron" /></td></tr>)}</tbody></table>{filtered.length === 0 && <Box className="empty-state"><Search size={22} /><Text>No queue items match this view.</Text></Box>}</Box>
        <Flex className="table-footer" align="center" justify="space-between"><Text>Showing {filtered.length} of {cases.length} images</Text><HStack gap="2"><ArrowUpDown size={14} /><Text>Sorted by review priority</Text></HStack></Flex>
      </Box>
    </Box>
  );
}
