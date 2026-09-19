import { Badge } from "@chakra-ui/react";
import { STATUS_META } from "../product/constants";

const toneMap = {
  neutral: "gray",
  blue: "blue",
  amber: "orange",
  green: "green",
  teal: "teal",
  red: "red",
};

export function StatusBadge({ status }) {
  const meta = STATUS_META[status] || { label: status, tone: "neutral" };
  return (
    <Badge className={`status-badge status-${meta.tone}`} colorPalette={toneMap[meta.tone]} variant="subtle">
      {meta.label}
    </Badge>
  );
}

export function ProvenanceBadge({ provenance }) {
  const isSystem = provenance === "SYSTEM";
  return (
    <Badge className={isSystem ? "provenance-badge provenance-system" : "provenance-badge provenance-user"}>
      {isSystem ? "SYSTEM" : "USER"}
    </Badge>
  );
}

export function EligibilityBadge({ value }) {
  return <span className={`eligibility-badge eligibility-${value.toLowerCase()}`}>{value}</span>;
}
