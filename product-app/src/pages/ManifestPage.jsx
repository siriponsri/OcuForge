import { useMemo, useState } from "react";
import { Box, Button, Flex, Grid, HStack, Text } from "@chakra-ui/react";
import { CheckCircle2, Download, FileSpreadsheet, FileText, RefreshCw, ShieldAlert } from "lucide-react";
import { PageHeader } from "../components/PageHeader";
import { EligibilityBadge } from "../components/StatusBadge";
import { ELIGIBILITY } from "../product/constants";
import { buildIndexCsv, buildManifestCsv, buildManifestRows } from "../product/manifest";

function downloadText(name, text) {
  const blob = new Blob([text], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function ManifestPage({ cases, onRebuild }) {
  const [filter, setFilter] = useState("ALL");
  const rows = useMemo(() => buildManifestRows(cases), [cases]);
  const counts = Object.fromEntries(ELIGIBILITY.map((value) => [value, cases.filter((item) => item.trainingEligibility === value).length]));
  const filtered = useMemo(() => filter === "ALL" ? cases : cases.filter((item) => item.trainingEligibility === filter), [cases, filter]);
  return <Box><PageHeader eyebrow="Workspace / Dataset" title="Dataset / Manifest" description="Inspect provenance and eligibility before any downstream model-factory selection. No training runs here."><Button className="secondary-action" onClick={onRebuild}><RefreshCw size={15} /> Rebuild manifest</Button><Button className="secondary-action" onClick={() => downloadText("index.csv", buildIndexCsv(cases))}><FileText size={15} /> Download index.csv</Button><Button className="primary-action" onClick={() => downloadText("manifest.csv", buildManifestCsv(cases))}><Download size={15} /> Download manifest.csv</Button></PageHeader>
    <Grid className="manifest-overview" templateColumns={{ base: "repeat(2, 1fr)", lg: "repeat(4, 1fr)" }} gap="3"><ManifestStat label="Manifest version" value="v0.1" detail="generated locally" /><ManifestStat label="Rows" value={rows.length} detail="lineage retained" /><ManifestStat label="Human eligible" value={counts.HUMAN || 0} detail="explicit review only" /><ManifestStat label="System only" value={counts.UNREVIEWED_SYSTEM || 0} detail="excluded by default" /></Grid>
    <Box className="manifest-callout"><ShieldAlert size={20} /><Box><Text className="callout-title">Eligibility is fail-closed</Text><Text>SYSTEM AUTO LABEL is never HUMAN GROUND TRUTH. UNREVIEWED_SYSTEM rows remain visible for audit but are not silently promoted into training data.</Text></Box></Box>
    <Box className="surface-panel manifest-panel"><Flex className="manifest-toolbar" align="center" justify="space-between" gap="3" wrap="wrap"><HStack gap="2"><FileSpreadsheet size={18} /><Text className="panel-title">Manifest rows</Text></HStack><HStack className="eligibility-filter" gap="1"><button type="button" className={filter === "ALL" ? "is-active" : ""} onClick={() => setFilter("ALL")}>All {cases.length}</button>{ELIGIBILITY.map((value) => <button type="button" key={value} className={filter === value ? "is-active" : ""} onClick={() => setFilter(value)}>{value} {counts[value] || 0}</button>)}</HStack></Flex><Box className="table-scroll"><table className="data-table manifest-table"><thead><tr><th>Case / frame</th><th>Source identity</th><th>System / human</th><th>Review / AI / export</th><th>Annotation lineage</th><th>Training image</th><th>Eligibility</th></tr></thead><tbody>{filtered.map((item) => { const row = rows.find((entry) => entry.case_id === item.id); return <tr key={item.id}><td><Text className="case-id">{item.id}</Text><Text className="file-name">{item.imageId} · {item.fileName}{item.frame_count > 1 ? ` · F${item.frame_number}/${item.frame_count}` : ""}</Text></td><td><Text className="mono-cell">{item.sourceSha256?.slice(0, 18)}...</Text><Text className="file-name">{item.study_instance_uid ? `SOP ${item.sop_instance_uid.slice(-10)}` : item.sourceFolder}</Text></td><td><Text>{item.systemGrade === null ? "System -" : `System ${item.systemGrade}`}</Text><Text className={item.humanGrade === null ? "is-muted" : "confidence-text"}>{item.humanGrade === null ? "Human -" : `Human ${item.humanGrade}`}</Text></td><td><Text className="manifest-state-line">{item.review_status}</Text><Text className="manifest-state-line">{item.ai_status} · {item.export_status}</Text></td><td><Text className="mono-cell">{row.annotation_revision_hash ? row.annotation_revision_hash.slice(0, 18) : "No revision"}</Text><Text className="file-name">{row.annotation_artifact_uri}</Text></td><td><Text className="mono-cell">{row.training_image_sha256?.slice(0, 18)}...</Text><Text className="file-name">{row.derivative_preprocessing_version || "source"}</Text></td><td><EligibilityBadge value={item.trainingEligibility} /></td></tr>; })}</tbody></table></Box><Flex className="table-footer" justify="space-between"><Text>Schema columns: {Object.keys(rows[0] || {}).length} · exact annotation revision and training image lineage retained</Text><HStack gap="2"><CheckCircle2 size={14} /><Text>Source references verified</Text></HStack></Flex></Box>
  </Box>;
}

function ManifestStat({ label, value, detail }) { return <Box className="manifest-stat"><Text>{label}</Text><strong>{value}</strong><small>{detail}</small></Box>; }
