import { useState } from "react";
import { Box, Button, Flex, HStack, Input, Text } from "@chakra-ui/react";
import { ChevronRight, Filter, Play, RefreshCw, Search, SlidersHorizontal } from "lucide-react";
import { PageHeader } from "../components/PageHeader";
import { EligibilityBadge, StatusBadge } from "../components/StatusBadge";
import { QUEUE_FILTERS, deriveQueueBadge } from "../product/constants";

function Grade({ value, muted = false }) {
  return <span className={`grade-value ${muted ? "is-muted" : ""}`}>{value === null || value === undefined ? "-" : `Grade ${value}`}</span>;
}

function StatusCell({ item }) {
  return <Box className="status-stack"><StatusBadge status={deriveQueueBadge(item)} /><Text className="status-subline">{item.review_status} · {item.ai_status} · {item.export_status}</Text></Box>;
}

export function QueuePage({ cases, onOpenReview, onRetryExport }) {
  const [query, setQuery] = useState("");
  const [stateFilter, setStateFilter] = useState("ALL");
  const filtered = cases.filter((item) => {
    const matchesQuery = `${item.id} ${item.fileName} ${item.sourceFolder}`.toLowerCase().includes(query.toLowerCase());
    return matchesQuery && (stateFilter === "ALL" || deriveQueueBadge(item) === stateFilter);
  });
  const counts = Object.fromEntries(QUEUE_FILTERS.map((status) => [status, cases.filter((item) => deriveQueueBadge(item) === status).length]));
  const needsAttention = cases.filter((item) => !["EXPORTED", "QUARANTINED"].includes(deriveQueueBadge(item))).length;
  const nextCase = cases.find((item) => ["AI_PROCESSED", "NOT_PROCESSED", "IN_REVIEW"].includes(deriveQueueBadge(item)));

  return <Box>
    <PageHeader eyebrow="Workspace / Queue" title="Review queue" description="A durable worklist where review, AI execution, and export recovery remain independent dimensions.">
      <Button className="secondary-action"><Filter size={15} /> Saved view</Button>
      <Button className="primary-action" onClick={() => nextCase && onOpenReview(nextCase.id)} disabled={!nextCase}><Play size={15} /> Open next review</Button>
    </PageHeader>

    <Flex className="queue-metrics" gap="3" wrap="wrap">
      <Box className="metric-card metric-card-accent"><Text className="metric-label">Needs attention</Text><Text className="metric-value">{needsAttention}</Text><Text className="metric-detail">AI, review or export action</Text></Box>
      <Box className="metric-card"><Text className="metric-label">Human reviewed</Text><Text className="metric-value">{cases.filter((item) => item.review_status === "HUMAN_REVIEWED").length}</Text><Text className="metric-detail">system grade remains visible</Text></Box>
      <Box className="metric-card"><Text className="metric-label">Exported</Text><Text className="metric-value">{counts.EXPORTED || 0}</Text><Text className="metric-detail">receipt verified</Text></Box>
      <Box className="metric-card"><Text className="metric-label">Recovery</Text><Text className="metric-value">{(counts.AI_FAILED || 0) + (cases.filter((item) => item.export_status === "FAILED").length)}</Text><Text className="metric-detail">retryable item-level issues</Text></Box>
    </Flex>

    <Box className="surface-panel queue-panel">
      <Flex className="queue-toolbar" align="center" justify="space-between" gap="3" wrap="wrap"><HStack className="search-box" gap="2"><Search size={17} /><Input aria-label="Search queue" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search ID, filename or folder" /></HStack><HStack gap="2"><select className="select-control" aria-label="Filter by queue state" value={stateFilter} onChange={(event) => setStateFilter(event.target.value)}><option value="ALL">All states ({cases.length})</option>{QUEUE_FILTERS.map((status) => <option key={status} value={status}>{status.replaceAll("_", " ")} ({counts[status] || 0})</option>)}</select><Button className="icon-button" variant="ghost" aria-label="Queue filters"><SlidersHorizontal size={17} /></Button></HStack></Flex>
      <Box className="queue-status-note"><strong>Canonical state:</strong> review status, AI status and export status are stored separately. The badge is a derived view only.</Box>
      <Box className="table-scroll"><table className="data-table queue-table"><thead><tr><th>Case</th><th>Source folder</th><th>Modality / frame</th><th>System DR grade</th><th>Human reviewed grade</th><th>Operational states</th><th>Eligibility</th><th /></tr></thead><tbody>{filtered.map((item) => <tr key={item.id} onClick={() => onOpenReview(item.id)} className="table-row-clickable"><td><Box><Text className="case-id">{item.id}</Text><Text className="file-name">{item.fileName}</Text></Box></td><td><Text className="folder-name">{item.sourceFolder}</Text><Text className="source-ref">{item.sourceSha256?.slice(0, 18)}...</Text></td><td><HStack gap="2"><span className={`modality-dot ${item.modality === "DICOM" ? "is-dicom" : ""}`} />{item.modality}<span className="laterality">{item.laterality || "-"}</span>{item.frame_count > 1 && <span className="laterality">F{item.frame_number}/{item.frame_count}</span>}</HStack></td><td><Grade value={item.systemGrade} muted={item.systemGrade === null} />{item.systemConfidence && <Text className="confidence-text">{Math.round(item.systemConfidence * 100)}% confidence</Text>}</td><td><Grade value={item.humanGrade} muted={item.humanGrade === null} />{item.humanReviewer && <Text className="confidence-text">{item.humanReviewer}</Text>}</td><td><StatusCell item={item} />{item.export_status === "FAILED" && <Button className="text-action retry-action" variant="ghost" onClick={(event) => { event.stopPropagation(); onRetryExport(item.id); }}><RefreshCw size={12} /> Retry export</Button>}</td><td><EligibilityBadge value={item.trainingEligibility} /></td><td><ChevronRight size={17} className="row-chevron" /></td></tr>)}</tbody></table>{filtered.length === 0 && <Box className="empty-state"><Search size={22} /><Text>No queue items match this view.</Text></Box>}</Box>
      <Flex className="table-footer" justify="space-between"><Text>{filtered.length} of {cases.length} cases</Text><Text>Original source bytes remain immutable</Text></Flex>
    </Box>
  </Box>;
}
