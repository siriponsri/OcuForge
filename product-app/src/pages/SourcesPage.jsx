import { Box, Button, Flex, Grid, HStack, Input, Text } from "@chakra-ui/react";
import { ArrowRight, CheckCircle2, Cloud, FileInput, FolderOpen, HardDrive, Link2, LockKeyhole, Play, UploadCloud } from "lucide-react";
import { PageHeader } from "../components/PageHeader";

function SourceMode({ selected, icon: Icon, label, description, onClick }) {
  return (
    <button type="button" className={`source-mode ${selected ? "is-selected" : ""}`} onClick={onClick}>
      <span className="source-mode-icon"><Icon size={18} /></span>
      <span><strong>{label}</strong><small>{description}</small></span>
      {selected && <CheckCircle2 size={17} className="source-selected" />}
    </button>
  );
}

function ReadinessItem({ icon: Icon, label, value, tone = "ready" }) {
  return <Flex className="readiness-item" align="center" justify="space-between" gap="3"><HStack gap="3"><Icon size={17} /><Text>{label}</Text></HStack><span className={`readiness-state ${tone}`}>{value}</span></Flex>;
}

export function SourcesPage({ sourceConfig, setSourceConfig, onIngest, ingestion }) {
  const onFolderChange = (event) => {
    const count = event.target.files?.length || 0;
    setSourceConfig((current) => ({ ...current, selectedFileCount: count }));
  };

  return (
    <Box>
      <PageHeader eyebrow="Workspace / Sources" title="Set up your image flow" description="Choose where images come from and where verified review artifacts should land.">
        <Box className="local-only-chip"><LockKeyhole size={14} /> Local authority</Box>
      </PageHeader>

      <Grid className="source-layout" templateColumns={{ base: "1fr", xl: "minmax(0, 1.32fr) minmax(19rem, .68fr)" }} gap="5">
        <Box className="surface-panel source-panel">
          <Flex className="panel-title-row" align="center" justify="space-between" gap="3"><Box><Text className="panel-kicker">01 / Input source</Text><Text className="panel-title">Bring in the next review set</Text></Box><span className="step-dot">01</span></Flex>
          <Grid className="source-mode-grid" templateColumns={{ base: "1fr", sm: "1fr 1fr" }} gap="3">
            <SourceMode selected={sourceConfig.sourceType === "LOCAL_FOLDER"} icon={FolderOpen} label="Local folder" description="On-prem path or mounted share" onClick={() => setSourceConfig((current) => ({ ...current, sourceType: "LOCAL_FOLDER" }))} />
            <SourceMode selected={sourceConfig.sourceType === "GOOGLE_DRIVE_FOLDER"} icon={Cloud} label="Google Drive" description="Optional governed adapter" onClick={() => setSourceConfig((current) => ({ ...current, sourceType: "GOOGLE_DRIVE_FOLDER" }))} />
          </Grid>
          <Box className="form-field">
            <Text as="label" htmlFor="source-reference">Source reference</Text>
            {sourceConfig.sourceType === "LOCAL_FOLDER" ? <Input id="source-reference" value={sourceConfig.sourceReference} onChange={(event) => setSourceConfig((current) => ({ ...current, sourceReference: event.target.value }))} placeholder="C:\\hospital-data\\fundus" /> : <Input id="source-reference" value={sourceConfig.sourceReference} onChange={(event) => setSourceConfig((current) => ({ ...current, sourceReference: event.target.value }))} placeholder="https://drive.google.com/drive/folders/..." />}
            <Text className="field-helper">The browser never receives provider credentials or uploads raw source bytes.</Text>
          </Box>
          {sourceConfig.sourceType === "LOCAL_FOLDER" && <Box className="drop-zone"><UploadCloud size={22} /><Text>Choose a local folder fixture</Text><Text className="drop-zone-copy">Folder selection is browser-local in this POC.</Text><label className="secondary-action">Browse folder<input type="file" webkitdirectory="true" directory="true" multiple onChange={onFolderChange} /></label>{sourceConfig.selectedFileCount > 0 && <span className="file-count">{sourceConfig.selectedFileCount} files selected</span>}</Box>}
          <Flex className="ingestion-note" align="flex-start" gap="3"><FileInput size={17} /><Box><Text><strong>Preserve originals.</strong> Every item is hashed before persistence; DICOM is kept separate from display derivatives.</Text><Text className="field-helper">Synthetic fixture mode is active. No hospital bytes are included in this browser demo.</Text></Box></Flex>
        </Box>

        <Box className="surface-panel source-panel">
          <Flex className="panel-title-row" align="center" justify="space-between" gap="3"><Box><Text className="panel-kicker">02 / Output destination</Text><Text className="panel-title">Keep review artifacts close</Text></Box><span className="step-dot">02</span></Flex>
          <Grid className="source-mode-grid" templateColumns={{ base: "1fr", sm: "1fr 1fr" }} gap="3">
            <SourceMode selected={sourceConfig.destinationType === "LOCAL_FOLDER"} icon={HardDrive} label="Local folder" description="Recommended for private data" onClick={() => setSourceConfig((current) => ({ ...current, destinationType: "LOCAL_FOLDER" }))} />
            <SourceMode selected={sourceConfig.destinationType === "GOOGLE_DRIVE_FOLDER"} icon={Cloud} label="Google Drive" description="Optional output adapter" onClick={() => setSourceConfig((current) => ({ ...current, destinationType: "GOOGLE_DRIVE_FOLDER" }))} />
          </Grid>
          <Box className="form-field"><Text as="label" htmlFor="destination-reference">Destination reference</Text><Input id="destination-reference" value={sourceConfig.destinationReference} onChange={(event) => setSourceConfig((current) => ({ ...current, destinationReference: event.target.value }))} /><Text className="field-helper">Outputs reference source hashes by default. Large originals are not duplicated.</Text></Box>
          <Box className="destination-preview"><HStack gap="3"><Link2 size={17} /><Box><Text className="destination-label">Export contract</Text><Text className="destination-path">{sourceConfig.destinationReference}/WARD-A-MORNING/CASE-0042/</Text></Box></HStack><ArrowRight size={16} /></Box>
          <Button className="primary-action full-action" onClick={onIngest}><Play size={16} /> {ingestion.status === "SCANNED" ? "Scan again" : "Start ingestion"}</Button>
        </Box>
      </Grid>

      <Box className="surface-panel readiness-panel">
        <Flex className="panel-title-row" align="center" justify="space-between"><Box><Text className="panel-kicker">Readiness check</Text><Text className="panel-title">Adapters and privacy boundary</Text></Box><span className="ready-label"><CheckCircle2 size={15} /> Ready for local fixtures</span></Flex>
        <Grid className="readiness-grid" templateColumns={{ base: "1fr", md: "repeat(3, 1fr)" }} gap="0"><ReadinessItem icon={HardDrive} label="Local source adapter" value="READY" /><ReadinessItem icon={FolderOpen} label="Local output adapter" value="READY" /><ReadinessItem icon={ShieldCheckIcon} label="Private data boundary" value="ON" /></Grid>
        {ingestion.status === "SCANNED" && <Box className="ingestion-result"><HStack gap="3"><CheckCircle2 size={18} /><Box><Text className="result-title">Ingestion scan complete</Text><Text>{ingestion.discovered} discovered / {ingestion.accepted} accepted / {ingestion.duplicates} duplicate / {ingestion.errors} error. Queue is ready.</Text></Box></HStack><span className="result-time">Just now</span></Box>}
      </Box>
    </Box>
  );
}

function ShieldCheckIcon(props) {
  return <LockKeyhole {...props} />;
}
