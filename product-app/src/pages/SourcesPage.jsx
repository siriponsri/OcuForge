import { Box, Button, Flex, Grid, HStack, Input, Text } from "@chakra-ui/react";
import { ArrowRight, CheckCircle2, Cloud, FileInput, FolderOpen, HardDrive, Link2, LockKeyhole, Play, ShieldCheck, UploadCloud } from "lucide-react";
import { PageHeader } from "../components/PageHeader";
import { OUTPUT_POLICIES } from "../product/constants";

function SourceMode({ selected, icon: Icon, label, description, onClick }) {
  return <button type="button" className={`source-mode ${selected ? "is-selected" : ""}`} onClick={onClick}>
    <span className="source-mode-icon"><Icon size={18} /></span>
    <span><strong>{label}</strong><small>{description}</small></span>
    {selected && <CheckCircle2 size={17} className="source-selected" />}
  </button>;
}

function ReadinessItem({ icon: Icon, label, value, tone = "ready" }) {
  return <Flex className="readiness-item" align="center" justify="space-between" gap="3"><HStack gap="3"><Icon size={17} /><Text>{label}</Text></HStack><span className={`readiness-state ${tone}`}>{value}</span></Flex>;
}

const policyCopy = {
  REFERENCE_ONLY: "Keep original bytes local and export an immutable source reference/hash.",
  COPY_ORIGINAL: "Copy original bytes into the governed output folder; never modify them.",
  DERIVED_IMAGE_ONLY: "Export reviewable display derivatives and metadata, not the original.",
  COPY_ORIGINAL_AND_DERIVED: "Export both original bytes and display derivatives with lineage.",
};

export function SourcesPage({ sourceConfig, setSourceConfig, onFilesSelected, onSyntheticFixtures, onChooseOutput, onIngest, ingestion }) {
  const onFolderChange = (event) => onFilesSelected([...event.target.files || []]);
  return <Box>
    <PageHeader eyebrow="Workspace / Sources" title="Set up your image flow" description="Ingest local retinal images through a governed, byte-preserving boundary before they enter Queue.">
      <Box className="local-only-chip"><LockKeyhole size={14} /> Local authority</Box>
    </PageHeader>

    <Grid className="source-layout" templateColumns={{ base: "1fr", xl: "minmax(0, 1.32fr) minmax(19rem, .68fr)" }} gap="5">
      <Box className="surface-panel source-panel">
        <Flex className="panel-title-row" align="center" justify="space-between" gap="3"><Box><Text className="panel-kicker">01 / Input source</Text><Text className="panel-title">Bring in the next review set</Text></Box><span className="step-dot">01</span></Flex>
        <Grid className="source-mode-grid" templateColumns={{ base: "1fr", sm: "1fr 1fr" }} gap="3">
          <SourceMode selected={sourceConfig.sourceType === "LOCAL_FOLDER"} icon={FolderOpen} label="Local folder" description="Browser bridge / mounted share" onClick={() => setSourceConfig((current) => ({ ...current, sourceType: "LOCAL_FOLDER" }))} />
          <SourceMode selected={sourceConfig.sourceType === "GOOGLE_DRIVE_FOLDER"} icon={Cloud} label="Google Drive" description="Optional governed adapter" onClick={() => setSourceConfig((current) => ({ ...current, sourceType: "GOOGLE_DRIVE_FOLDER" }))} />
        </Grid>
        <Box className="form-field"><Text as="label" htmlFor="source-reference">Source reference</Text><Input id="source-reference" value={sourceConfig.sourceReference} onChange={(event) => setSourceConfig((current) => ({ ...current, sourceReference: event.target.value }))} placeholder="Local path, bridge reference or Drive URL" /><Text className="field-helper">UI code consumes a SourceAdapter reference; it never assumes unrestricted browser filesystem access.</Text></Box>
        {sourceConfig.sourceType === "LOCAL_FOLDER" && <Box className="drop-zone"><UploadCloud size={22} /><Text>Choose local files or a folder</Text><Text className="drop-zone-copy">DICOM is first-class. Supported raster files remain available through the RasterAdapter.</Text><Flex gap="2" wrap="wrap"><label className="secondary-action">Browse folder<input type="file" webkitdirectory="true" directory="true" multiple onChange={onFolderChange} /></label><Button className="secondary-action" onClick={onSyntheticFixtures}><FileInput size={15} /> Use synthetic POC fixtures</Button></Flex><span className="file-count">{sourceConfig.selectedFileCount ? `${sourceConfig.selectedFileCount} files staged: ${sourceConfig.selectedInputLabel}` : "No files staged yet"}</span></Box>}
        <Flex className="ingestion-note" align="flex-start" gap="3"><FileInput size={17} /><Box><Text><strong>Preserve originals.</strong> Every item is SHA-256 hashed before persistence; DICOM bytes stay separate from display derivatives.</Text><Text className="field-helper">Malformed or unsupported DICOM is quarantined with its original bytes and reason.</Text></Box></Flex>
      </Box>

      <Box className="surface-panel source-panel">
        <Flex className="panel-title-row" align="center" justify="space-between" gap="3"><Box><Text className="panel-kicker">02 / Output destination</Text><Text className="panel-title">Keep review artifacts close</Text></Box><span className="step-dot">02</span></Flex>
        <Grid className="source-mode-grid" templateColumns={{ base: "1fr", sm: "1fr 1fr" }} gap="3">
          <SourceMode selected={sourceConfig.destinationType === "LOCAL_FOLDER"} icon={HardDrive} label="Local folder" description="Recommended for private data" onClick={() => setSourceConfig((current) => ({ ...current, destinationType: "LOCAL_FOLDER" }))} />
          <SourceMode selected={sourceConfig.destinationType === "GOOGLE_DRIVE_FOLDER"} icon={Cloud} label="Google Drive" description="Optional output adapter" onClick={() => setSourceConfig((current) => ({ ...current, destinationType: "GOOGLE_DRIVE_FOLDER" }))} />
        </Grid>
        <Box className="form-field"><Text as="label" htmlFor="destination-reference">Destination reference</Text><Input id="destination-reference" value={sourceConfig.destinationReference} onChange={(event) => setSourceConfig((current) => ({ ...current, destinationReference: event.target.value }))} /><Text className="field-helper">LocalPathAdapter / governed Drive adapter owns the write; no raw bytes go to public telemetry.</Text></Box>
        <Button className="secondary-action full-action" onClick={onChooseOutput}><FolderOpen size={15} /> Connect local output folder</Button>
        <Box className="form-field"><Text as="label" htmlFor="output-policy">Output policy</Text><select id="output-policy" className="select-control full-select" value={sourceConfig.outputPolicy} onChange={(event) => setSourceConfig((current) => ({ ...current, outputPolicy: event.target.value }))}>{OUTPUT_POLICIES.map((policy) => <option key={policy} value={policy}>{policy}</option>)}</select><Text className="field-helper">{policyCopy[sourceConfig.outputPolicy]} Default for large DICOM workflows is REFERENCE_ONLY.</Text></Box>
        <Box className="destination-preview"><HStack gap="3"><Link2 size={17} /><Box><Text className="destination-label">Export contract</Text><Text className="destination-path">{sourceConfig.destinationReference}/source-folder/case-id/</Text></Box></HStack><ArrowRight size={16} /></Box>
        <label className="recovery-toggle"><input type="checkbox" checked={sourceConfig.simulateExportFailure} onChange={(event) => setSourceConfig((current) => ({ ...current, simulateExportFailure: event.target.checked }))} /> Simulate next export failure for recovery testing</label>
        <Button className="primary-action full-action" onClick={onIngest} isLoading={ingestion.status === "SCANNING"}><Play size={16} /> {ingestion.status === "SCANNED" ? "Ingest again" : "Start ingestion"}</Button>
      </Box>
    </Grid>

    <Box className="surface-panel readiness-panel">
      <Flex className="panel-title-row" align="center" justify="space-between"><Box><Text className="panel-kicker">Readiness check</Text><Text className="panel-title">Adapters and privacy boundary</Text></Box><span className="ready-label"><CheckCircle2 size={15} /> Local POC ready</span></Flex>
      <Grid className="readiness-grid" templateColumns={{ base: "1fr", md: "repeat(3, 1fr)" }} gap="0"><ReadinessItem icon={HardDrive} label="Local source bridge" value="READY" /><ReadinessItem icon={FolderOpen} label="Local output adapter" value="READY" /><ReadinessItem icon={ShieldCheck} label="Private data boundary" value="ON" /></Grid>
      {ingestion.status === "SCANNED" && <Box className="ingestion-result"><HStack gap="3"><CheckCircle2 size={18} /><Box><Text className="result-title">Ingestion scan complete</Text><Text>{ingestion.discovered} discovered / {ingestion.accepted} accepted / {ingestion.quarantined || 0} quarantined / {ingestion.duplicates || 0} duplicate. {ingestion.accepted_cases || 0} Queue frames created.</Text></Box></HStack><span className="result-time">Just now</span></Box>}
      {ingestion.status === "FAILED" && <Box className="ingestion-result ingestion-error"><Text className="result-title">Ingestion failed</Text><Text>{ingestion.error}</Text></Box>}
    </Box>
  </Box>;
}
