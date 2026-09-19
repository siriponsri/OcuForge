import { Box, Flex, HStack, Text } from "@chakra-ui/react";
import { Crosshair, MousePointer2, Minus, Plus, RotateCcw, ScanSearch } from "lucide-react";
import { ProvenanceBadge, StatusBadge } from "./StatusBadge";
import { TOOLS } from "../data/demoData";

function AnnotationShape({ annotation }) {
  const isSystem = annotation.provenance === "SYSTEM";
  const className = `annotation-shape ${isSystem ? "annotation-system" : "annotation-user"}`;
  const style = { left: `${annotation.x * 100}%`, top: `${annotation.y * 100}%` };

  if (annotation.type === "point") {
    return <span className={`${className} annotation-point`} style={style} aria-label={`${annotation.label} ${annotation.provenance}`} />;
  }

  if (annotation.type === "polygon") {
    return <span className={`${className} annotation-polygon`} style={{ ...style, width: `${annotation.width * 100}%`, height: `${annotation.height * 100}%` }} aria-label={`${annotation.label} ${annotation.provenance}`} />;
  }

  return (
    <span
      className={`${className} annotation-${annotation.type}`}
      style={{ ...style, width: `${annotation.width * 100}%`, height: `${annotation.height * 100}%` }}
      aria-label={`${annotation.label} ${annotation.provenance}`}
    >
      <span className="annotation-label"><ProvenanceBadge provenance={annotation.provenance} /> {annotation.label}</span>
    </span>
  );
}

export function ReviewCanvas({ item, tool, onSelectTool, onCanvasClick, onZoom }) {
  return (
    <Box className="review-stage-panel">
      <Flex className="review-stage-toolbar" align="center" justify="space-between" gap="3" wrap="wrap">
        <HStack className="annotation-tools" gap="1">
          {TOOLS.map(({ id, label, shortLabel }) => {
            const Icon = id === "select" ? MousePointer2 : id === "point" ? Crosshair : id === "polygon" ? ScanSearch : id === "ellipse" ? RotateCcw : id === "area" ? ScanSearch : ScanSearch;
            return (
              <button key={id} className={`tool-button ${tool === id ? "is-active" : ""}`} type="button" onClick={() => onSelectTool(id)} title={label} aria-label={label}>
                <Icon size={15} />
                <span>{shortLabel}</span>
              </button>
            );
          })}
        </HStack>
        <HStack className="zoom-controls" gap="1">
          <button type="button" className="icon-tool" aria-label="Zoom out" onClick={() => onZoom(-0.1)}><Minus size={14} /></button>
          <Text className="zoom-value">Fit</Text>
          <button type="button" className="icon-tool" aria-label="Zoom in" onClick={() => onZoom(0.1)}><Plus size={14} /></button>
        </HStack>
      </Flex>
      <Box className="review-canvas" onClick={onCanvasClick} role="application" aria-label="Retinal image annotation canvas">
        <Box className="image-frame">
          <img src={item.imageUrl} alt={`Synthetic retinal image for ${item.id}`} />
          {item.annotations.map((annotation) => <AnnotationShape key={annotation.id} annotation={annotation} />)}
        </Box>
        <HStack className="canvas-meta" gap="2">
          <span className="canvas-chip">{item.modality}</span>
          <span className="canvas-chip">{item.laterality}</span>
          <span className="canvas-chip">{item.dimensions}</span>
        </HStack>
        <Box className="canvas-instruction">{tool === "select" ? "Select an annotation to inspect" : `Click to place ${TOOLS.find((entry) => entry.id === tool)?.label.toLowerCase()}`}</Box>
      </Box>
      <Flex className="provenance-legend" align="center" justify="space-between" gap="3" wrap="wrap">
        <HStack gap="3">
          <HStack gap="2"><span className="legend-swatch system-swatch" /><Text>SYSTEM prediction</Text></HStack>
          <HStack gap="2"><span className="legend-swatch user-swatch" /><Text>USER annotation</Text></HStack>
        </HStack>
        <HStack gap="2"><StatusBadge status={item.status} /><Text className="legend-note">Original source unchanged</Text></HStack>
      </Flex>
    </Box>
  );
}
