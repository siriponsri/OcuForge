import { useMemo, useState } from "react";
import { Box, Button, Flex, Grid, HStack, Text } from "@chakra-ui/react";
import { CheckCircle2, Download, FileSpreadsheet, RefreshCw, ShieldAlert } from "lucide-react";
import { PageHeader } from "../components/PageHeader";
import { EligibilityBadge } from "../components/StatusBadge";
import { ELIGIBILITY } from "../data/demoData";

const manifestFields = ["manifest_version", "row_id", "case_id", "image_id", "source_folder_id", "file_sha256", "modality", "laterality", "system_dr_grade", "system_prediction_id", "human_reviewed_dr_grade", "human_review_status", "annotation_count", "training_eligibility", "label_provenance", "export_status"];

function buildCsv(cases) {
  const headers = manifestFields.join(",");
  const rows = cases.map((item) => ["manifest.v0.1", `ROW-${item.id}`, item.id, item.imageId, item.sourceFolderId, item.sourceSha256, item.modality, item.laterality, item.systemGrade ?? "", item.systemPredictionId ?? "", item.humanGrade ?? "", item.humanReviewStatus, item.annotations.length, item.trainingEligibility, item.humanGrade === null ? "UNREVIEWED_SYSTEM" : "HUMAN", item.exportStatus].map((value) => `"${String(value).replaceAll('"', '""')}"`).join(","));
  return `${headers}\n${rows.join("\n")}`;
}

export function ManifestPage({ cases, onRebuild }) {
  const [filter, setFilter] = useState("ALL");
  const counts = Object.fromEntries(ELIGIBILITY.map((value) => [value, cases.filter((item) => item.trainingEligibility === value).length]));
  const filtered = useMemo(() => filter === "ALL" ? cases : cases.filter((item) => item.trainingEligibility === filter), [cases, filter]);
  const downloadCsv = () => { const blob = new Blob([buildCsv(cases)], { type: "text/csv;charset=utf-8" }); const url = URL.createObjectURL(blob); const anchor = document.createElement("a"); anchor.href = url; anchor.download = "manifest.csv"; anchor.click(); URL.revokeObjectURL(url); };

  return <Box><PageHeader eyebrow="Workspace / Dataset" title="Dataset / Manifest" description="Inspect provenance and eligibility before any downstream training selection."><Button className="secondary-action" onClick={onRebuild}><RefreshCw size={15} /> Rebuild manifest</Button><Button className="primary-action" onClick={downloadCsv}><Download size={15} /> Download CSV</Button></PageHeader>
    <Grid className="manifest-overview" templateColumns={{ base: "repeat(2, 1fr)", lg: "repeat(4, 1fr)" }} gap="3"><ManifestStat label="Manifest version" value="v0.1" detail="generated locally" /><ManifestStat label="Rows" value={cases.length} detail="hashes retained" /><ManifestStat label="Human eligible" value={counts.HUMAN || 0} detail="explicit review only" /><ManifestStat label="System only" value={counts.UNREVIEWED_SYSTEM || 0} detail="excluded by default" /></Grid>
    <Box className="manifest-callout"><ShieldAlert size={20} /><Box><Text className="callout-title">Eligibility is fail-closed</Text><Text>UNREVIEWED_SYSTEM rows are visible for audit but never count as human ground truth or training eligible data.</Text></Box></Box>
    <Box className="surface-panel manifest-panel"><Flex className="manifest-toolbar" align="center" justify="space-between" gap="3" wrap="wrap"><HStack gap="2"><FileSpreadsheet size={18} /><Text className="panel-title">Manifest rows</Text></HStack><HStack className="eligibility-filter" gap="1"><button type="button" className={filter === "ALL" ? "is-active" : ""} onClick={() => setFilter("ALL")}>All {cases.length}</button>{ELIGIBILITY.map((value) => <button type="button" key={value} className={filter === value ? "is-active" : ""} onClick={() => setFilter(value)}>{value} {counts[value] || 0}</button>)}</HStack></Flex><Box className="table-scroll"><table className="data-table manifest-table"><thead><tr><th>Case / image</th><th>Source hash</th><th>System grade</th><th>Human grade</th><th>Annotations</th><th>Eligibility</th><th>Export</th></tr></thead><tbody>{filtered.map((item) => <tr key={item.id}><td><Text className="case-id">{item.id}</Text><Text className="file-name">{item.imageId} / {item.modality}</Text></td><td><Text className="mono-cell">{item.sourceSha256.slice(0, 22)}...</Text></td><td>{item.systemGrade === null ? "-" : `Grade ${item.systemGrade}`}</td><td>{item.humanGrade === null ? <span className="is-muted">Not reviewed</span> : `Grade ${item.humanGrade}`}</td><td>{item.annotations.length}</td><td><EligibilityBadge value={item.trainingEligibility} /></td><td><span className={`export-state export-${item.exportStatus.toLowerCase()}`}>{item.exportStatus}</span></td></tr>)}</tbody></table></Box><Flex className="table-footer" justify="space-between"><Text>Schema columns: {manifestFields.length}</Text><HStack gap="2"><CheckCircle2 size={14} /><Text>Source references verified</Text></HStack></Flex></Box>
  </Box>;
}

function ManifestStat({ label, value, detail }) { return <Box className="manifest-stat"><Text>{label}</Text><strong>{value}</strong><small>{detail}</small></Box>; }
