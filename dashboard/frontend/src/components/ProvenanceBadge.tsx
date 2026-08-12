import type { Provenance } from "../data/types";

const CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  OFFICIAL_EVENT_STATE: { label: "OFFICIAL EVENT STATE", color: "#22C55E", bg: "rgba(34,197,94,0.12)" },
  OFFICIAL_EVENT_DATA: { label: "OFFICIAL EVENT DATA", color: "#22C55E", bg: "rgba(34,197,94,0.12)" },
  OFFICIAL_PLATFORM_OBSERVATION: { label: "OFFICIAL OBSERVATION", color: "#38BDF8", bg: "rgba(56,189,248,0.12)" },
  LOCAL_EXPERIMENT: { label: "LOCAL EXPERIMENT", color: "#A78BFA", bg: "rgba(167,139,250,0.12)" },
  SYNTHETIC_FIXTURE: { label: "SYNTHETIC", color: "#FFB000", bg: "rgba(255,176,0,0.12)" },
  MANUALLY_RECORDED: { label: "MANUALLY RECORDED", color: "#8593A1", bg: "rgba(133,147,161,0.12)" },
  STALE: { label: "STALE", color: "#FFB000", bg: "rgba(255,176,0,0.10)" },
  UNKNOWN: { label: "UNKNOWN", color: "#6F7C89", bg: "rgba(111,124,137,0.10)" },
  BACKEND_UNAVAILABLE: { label: "BACKEND UNAVAILABLE", color: "#EF4444", bg: "rgba(239,68,68,0.12)" },
};

interface Props {
  provenance: Provenance | "STALE" | "UNKNOWN" | "BACKEND_UNAVAILABLE";
  stale?: boolean;
  small?: boolean;
}

export default function ProvenanceBadge({ provenance, stale, small }: Props) {
  const key = stale ? "STALE" : provenance;
  const cfg = CONFIG[key] ?? CONFIG["UNKNOWN"];
  const sz = small ? "9px" : "10px";
  return (
    <span
      style={{
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: sz,
        fontWeight: 600,
        letterSpacing: "0.06em",
        color: cfg.color,
        background: cfg.bg,
        border: `1px solid ${cfg.color}33`,
        borderRadius: "2px",
        padding: "1px 5px",
        whiteSpace: "nowrap",
      }}
    >
      {cfg.label}
    </span>
  );
}
