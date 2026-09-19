import { useMemo, useState } from "react";
import { Box, Flex, Grid, HStack, Text } from "@chakra-ui/react";
import { BarChart3, ChevronDown, FolderKanban, Layers3, ShieldCheck, TrendingUp } from "lucide-react";
import { PageHeader } from "../components/PageHeader";

function BarRow({ label, value, total, color = "brick" }) {
  return <Box className="bar-row"><Flex justify="space-between" gap="3"><Text>{label}</Text><strong>{value}</strong></Flex><Box className="bar-track"><span className={`bar-fill bar-${color}`} style={{ width: `${total ? Math.max(6, value / total * 100) : 0}%` }} /></Box></Box>;
}

export function SummaryPage({ cases }) {
  const [dimension, setDimension] = useState("source");
  const stateCount = (state) => cases.filter((item) => item.status === state).length;
  const groups = useMemo(() => {
    const map = new Map();
    cases.forEach((item) => {
      const key = dimension === "source" ? item.sourceFolder : item.systemGrade === null ? "Not predicted" : `System Grade ${item.systemGrade}`;
      map.set(key, (map.get(key) || 0) + 1);
    });
    return [...map.entries()].sort((a, b) => b[1] - a[1]);
  }, [cases, dimension]);
  const humanReviewed = cases.filter((item) => item.humanGrade !== null);
  const reviewedGroups = [...new Set(humanReviewed.map((item) => item.humanGrade))].sort();

  return <Box><PageHeader eyebrow="Workspace / Summary" title="Throughput at a glance" description="Group work by source and system evidence without collapsing human review into model output."><Box className="dimension-select"><Layers3 size={15} /><select aria-label="Summary dimension" value={dimension} onChange={(event) => setDimension(event.target.value)}><option value="source">Group by source folder</option><option value="system">Group by system DR grade</option></select><ChevronDown size={14} /></Box></PageHeader>
    <Grid className="summary-hero-grid" templateColumns={{ base: "1fr", lg: "1.35fr .65fr" }} gap="5"><Box className="summary-hero"><Box className="summary-orbit orbit-one" /><Box className="summary-orbit orbit-two" /><Text className="panel-kicker">Review coverage</Text><Text className="summary-big-number">{Math.round(humanReviewed.length / cases.length * 100)}<span>%</span></Text><Text className="summary-hero-copy">of the current worklist has an explicit human grade. The system grade remains a separate source of evidence.</Text><Flex className="summary-progress" align="center" gap="3"><Box className="progress-track"><span style={{ width: `${humanReviewed.length / cases.length * 100}%` }} /></Box><Text>{humanReviewed.length} / {cases.length} cases</Text></Flex></Box><Box className="surface-panel state-panel"><Flex className="panel-title-row"><Box><Text className="panel-kicker">Queue state</Text><Text className="panel-title">Where work sits now</Text></Box></Flex><VStackSummary state="NOT_PROCESSED" value={stateCount("NOT_PROCESSED")} /><VStackSummary state="AI_PROCESSED" value={stateCount("AI_PROCESSED")} /><VStackSummary state="IN_REVIEW" value={stateCount("IN_REVIEW")} /><VStackSummary state="HUMAN_REVIEWED" value={stateCount("HUMAN_REVIEWED")} /><VStackSummary state="EXPORTED" value={stateCount("EXPORTED")} /><VStackSummary state="ERROR" value={stateCount("ERROR")} /></Box></Grid>

    <Grid className="summary-content-grid" templateColumns={{ base: "1fr", lg: "1.2fr .8fr" }} gap="5"><Box className="surface-panel"><Flex className="panel-title-row" align="center" justify="space-between"><Box><Text className="panel-kicker">Primary grouping</Text><Text className="panel-title">{dimension === "source" ? "Source folders" : "System DR grades"}</Text></Box><FolderKanban size={18} /></Flex><Box className="bars-list">{groups.map(([label, value], index) => <BarRow key={label} label={label} value={value} total={cases.length} color={index === 0 ? "brick" : index === 1 ? "gold" : "blue"} />)}</Box></Box><Box className="surface-panel"><Flex className="panel-title-row" align="center" justify="space-between"><Box><Text className="panel-kicker">Human dimension</Text><Text className="panel-title">Reviewed grades</Text></Box><ShieldCheck size={18} /></Flex>{reviewedGroups.length === 0 ? <Box className="empty-state compact"><ShieldCheck size={21} /><Text>No human grades recorded yet.</Text></Box> : <Box className="bars-list">{reviewedGroups.map((grade) => <BarRow key={grade} label={`Human Grade ${grade}`} value={humanReviewed.filter((item) => item.humanGrade === grade).length} total={humanReviewed.length} color="green" />)}</Box>}<Box className="summary-note"><TrendingUp size={15} /><Text>System and human grades stay distinct in every export.</Text></Box></Box></Grid>
  </Box>;
}

function VStackSummary({ state, value }) {
  return <Flex className="state-row" justify="space-between" align="center"><HStack gap="2"><span className={`state-dot state-dot-${state.toLowerCase()}`} /><Text>{state.replaceAll("_", " ")}</Text></HStack><strong>{value}</strong></Flex>;
}
