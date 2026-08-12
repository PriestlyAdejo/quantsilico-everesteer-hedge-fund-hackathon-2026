import type { SubmissionMode } from "../data/types";

const STYLES: Record<
  SubmissionMode,
  { label: string; bg: string; border: string; color: string }
> = {
  DISABLED: {
    label: "SUBMISSIONS DISABLED",
    bg: "rgba(239,68,68,0.08)",
    border: "#EF4444",
    color: "#EF4444",
  },
  DRY_RUN: {
    label: "SUBMISSION MODE · DRY_RUN",
    bg: "rgba(56,189,248,0.08)",
    border: "#38BDF8",
    color: "#38BDF8",
  },
  ARMED: {
    label: "SUBMISSIONS ARMED",
    bg: "rgba(255,176,0,0.12)",
    border: "#FFB000",
    color: "#FFC53D",
  },
};

export default function SubmissionModeBanner({
  mode = "DRY_RUN",
}: {
  mode?: SubmissionMode | null;
}) {
  const m = mode ?? "DRY_RUN";
  const s = STYLES[m] ?? STYLES.DRY_RUN;
  return (
    <div
      role="status"
      style={{
        background: s.bg,
        border: `1px solid ${s.border}`,
        borderRadius: 2,
        padding: "8px 12px",
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: 11,
        fontWeight: 600,
        letterSpacing: "0.06em",
        color: s.color,
      }}
    >
      {s.label}
      {m === "ARMED"
        ? " — real practice/live uploads permitted after integrity guards"
        : m === "DRY_RUN"
          ? " — packaging and recording without external upload"
          : " — external upload blocked"}
    </div>
  );
}
