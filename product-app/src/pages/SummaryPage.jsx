import { useMemo, useState } from "react";
import { Box, Flex, Grid, HStack, Text } from "@chakra-ui/react";
import { ChevronDown, FolderKanban, Layers3, ShieldCheck, TrendingUp } from "lucide-react";
import { PageHeader } from "../components/PageHeader";

function BarRow({ label, value, total, color = "brick" }) {
  return <Box className="bar-row"><Flex justify="space-between" gap="3"><Text>{label}</Text><strong>{value}</strong></Flex><Box className="bar-track"><span className={`bar-fill bar-${color}`} style={{ width: `${total ? Math.max(6, value / total * 100) : 0}%` }} /></Box></Box>;
}

export function SummaryPage({ cases }) {
  const [dimension, setDimension] = useState("source");
  const groups = useMemo(() => {
    const map = new Map();
    cases.forEach((item) => {
      const key = dimension === "source" ? item.sourceFolder : item.systemGrade === null ? "Not predicted" : `System Grade ${item.systemGrade}`;
      map.set(key, (map.get(key) || 0) + 1);
    });
    return [...map.entries()].sort((a, b) => b[1] - a[1]);
  }, [cases, dimension]);
  const humanReviewed = cases.filter((item) => item.review_status === "HUMAN_REVIEWED");
  const reviewedGroups = [...new Set(humanReviewed.filter((item) => item.humanGrade !== null).map((item) => item.humanGrade))].sort();
  const reviewCount = (status) => cases.filter((item) => item.review_status === status).length;
  const aiCount = (status) => cases.filter((item) => item.ai_status === status).length;
  const exportCount = (status) => cases.filter((item) => item.export_status === status).length;

  return <Box><PageHeader eyebrow="Workspace / Summary" title="Throughput at a glance" description="Group work by source folder and SYSTEM DR grade while keeping human review, AI execution, and export recovery distinct."><Box className="dimension-select"><Layers3 size={15} /><select aria-label="Summary dimension" value={dimension} onChange={(event) => setDimension(event.target.value)}><option value="source">Group by source folder</option><option value="system">Group by system DR grade</option></select><ChevronDown size={14} /></Box></PageHeader>
    <Grid className="summary-hero-grid" templateColumns={{ base: "1fr", lg: "1.35fr .65fr" }} gap="5"><Box className="summary-hero"><Box className="summary-orbit orbit-one" /><Box className="summary-orbit orbit-two" /><Text className="panel-kicker">Human review coverage</Text><Text className="summary-big-number">{Math.round(humanReviewed.length / Math.max(1, cases.length) * 100)}<span>%</span></Text><Text className="summary-hero-copy">of the current worklist has an explicit review state. System predictions and human grades remain separate sources of evidence.</Text><Flex className="summary-progress" align="center" gap="3"><Box className="progress-track"><span style={{ width: `${humanReviewed.length / Math.max(1, cases.length) * 100}%` }} /></Box><Text>{humanReviewed.length} / {cases.length} cases</Text></Flex></Box><Box className="surface-panel state-panel"><Flex className="panel-title-row"><Box><Text className="panel-kicker">Review dimension</Text><Text className="panel-title">Where human work sits</Text></Box></Flex><StateRow label="NOT_STARTED" value={reviewCount("NOT_STARTED")} /><StateRow label="IN_REVIEW" value={reviewCount("IN_REVIEW")} /><StateRow label="HUMAN_REVIEWED" value={reviewCount("HUMAN_REVIEWED")} /><Text className="panel-kicker state-section-label">AI dimension</Text><StateRow label="NOT_RUN" value={aiCount("NOT_RUN")} /><StateRow label="PROCESSED" value={aiCount("PROCESSED")} /><StateRow label="FAILED" value={aiCount("FAILED")} /><Text className="panel-kicker state-section-label">Export dimension</Text><StateRow label="EXPORTED" value={exportCount("EXPORTED")} /><StateRow label="FAILED" value={exportCount("FAILED")} /></Box></Grid>

    <Grid className="summary-content-grid" templateColumns={{ base: "1fr", lg: "1.2fr .8fr" }} gap="5"><Box className="surface-panel"><Flex className="panel-title-row" align="center" justify="space-between"><Box><Text className="panel-kicker">Primary grouping</Text><Text className="panel-title">{dimension === "source" ? "Source folders" : "System DR grades"}</Text></Box><FolderKanban size={18} /></Flex><Box className="bars-list">{groups.map(([label, value], index) => <BarRow key={label} label={label} value={value} total={cases.length} color={index === 0 ? "brick" : index === 1 ? "gold" : "blue"} />)}</Box></Box><Box className="surface-panel"><Flex className="panel-title-row" align="center" justify="space-between"><Box><Text className="panel-kicker">Human dimension</Text><Text className="panel-title">Reviewed grades</Text></Box><ShieldCheck size={18} /></Flex>{reviewedGroups.length === 0 ? <Box className="empty-state compact"><ShieldCheck size={21} /><Text>No human grades recorded yet.</Text></Box> : <Box className="bars-list">{reviewedGroups.map((grade) => <BarRow key={grade} label={`Human Grade ${grade}`} value={humanReviewed.filter((item) => item.humanGrade === grade).length} total={humanReviewed.length} color="green" />)}</Box>}<Box className="summary-note"><TrendingUp size={15} /><Text>Export failures do not erase HUMAN_REVIEWED state.</Text></Box></Box></Grid>
  </Box>;
}

function StateRow({ label, value }) {
  return <Flex className="state-row" justify="space-between" align="center"><HStack gap="2"><span className={`state-dot state-dot-${label.toLowerCase()}`} /><Text>{label.replaceAll("_", " ")}</Text></HStack><strong>{value}</strong></Flex>;
}
