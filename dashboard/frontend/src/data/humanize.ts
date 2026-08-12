import type { RaceDecision } from "./types";

// ─── Page metadata ────────────────────────────────────────────
// Short, human, practical one/two-sentence explanations shown under each
// page title. Not badges. Keyed by route path.

export interface PageMeta {
  title: string;
  intro: string;
}

export const PAGE_META: Record<string, PageMeta> = {
  "/": {
    title: "Overview",
    intro:
      "Start here. See where the event is, what the research loop is doing, what is currently winning, and what needs attention next.",
  },
  "/event": {
    title: "Event Control",
    intro:
      "Connect to Everesteer and verify the live event rules before doing anything that depends on them. This is the source of truth for rounds, scoring, capabilities and submission limits.",
  },
  "/round": {
    title: "Round Room",
    intro:
      "Use this during an open round. Track the current live dataset, inference jobs, submissions, leaderboard movement and the time remaining.",
  },
  "/data": {
    title: "Data Lab",
    intro:
      "Check what data arrived, whether it is safe to model, and how the train, practice and live splits differ.",
  },
  "/experiments": {
    title: "Experiments",
    intro:
      "Everything we have tried, what changed between runs, and which research branches are still worth compute.",
  },
  "/validation": {
    title: "Validation",
    intro:
      "Decide whether a result can be trusted, how strong the evidence is, and whether the candidate deserves more budget.",
  },
  "/models": {
    title: "Models",
    intro:
      "Registry of trained model artefacts: lineage, performance, latency, stability and submission readiness.",
  },
  "/features": {
    title: "Feature Lab",
    intro:
      "Statistical diagnostics for anonymous features. Analyse behaviour and stability without inventing economic identities.",
  },
  "/ensembles": {
    title: "Ensembles",
    intro:
      "Combine models only when they contribute independent signal. Compare overlap, marginal improvement and robustness before promoting a blend.",
  },
  "/leaderboard": {
    title: "Leaderboard",
    intro:
      "External evidence from Everesteer: current round, cumulative standing and how our submitted aliases have moved over time.",
  },
  "/submission": {
    title: "Submission",
    intro:
      "The controlled path from a research candidate to a valid practice or live upload. Every submission is checked before it leaves the machine.",
  },
  "/staking": {
    title: "Staking",
    intro:
      "Use only after the event explains the staking mechanism. Compare model evidence, uncertainty and concentration before allocating anything.",
  },
  "/compute": {
    title: "Compute & Jobs",
    intro:
      "See what is running, how much machine capacity is being used, when results are expected and what is queued next.",
  },
  "/repository": {
    title: "Repository",
    intro:
      "The exact code, environment and build state producing the current research results.",
  },
  "/docs": {
    title: "Documentation",
    intro:
      "Generated reference documentation plus human-written runbooks and end-to-end operating flows.",
  },
};

// ─── Race decision humanisation ────────────────────────────────
// Keep the raw enum internally; show human language. Raw code stays
// accessible via the detail drawer / `.code`.

export type DecisionTone = "good" | "warn" | "muted" | "error" | "neutral";

export interface HumanDecision {
  label: string;
  tone: DecisionTone;
  code: RaceDecision;
}

const DECISION_MAP: Record<RaceDecision, { label: string; tone: DecisionTone }> = {
  PROMOTE_TOP_SCORE: { label: "Advance — best local score so far", tone: "good" },
  PROMOTE_DIVERSITY: { label: "Advance to next round — adds useful independent signal", tone: "good" },
  PROMOTE_EXPLORATION: { label: "Advance — this branch is worth more exploration", tone: "good" },
  KEEP_ENSEMBLE: { label: "Keep in the blend — contributes independent signal", tone: "good" },
  RETEST: { label: "Retest — evidence is not yet conclusive", tone: "warn" },
  RETIRE_DOMINATED: { label: "Stop exploring — another candidate is better on the same trade-offs", tone: "muted" },
  RETIRE_SATURATED: { label: "Stop this branch — recent variants are no longer improving", tone: "muted" },
  FAILED_OOM: { label: "Failed — ran out of memory", tone: "error" },
  FAILED_TRAINING: { label: "Failed — training error", tone: "error" },
  INVALID_INTEGRITY: { label: "Blocked — an integrity check failed", tone: "error" },
  INVALID_ID_ALIGNMENT: { label: "Blocked — prediction IDs do not match the current split", tone: "error" },
  PENDING: { label: "Pending — awaiting evidence", tone: "neutral" },
};

export function humanizeDecision(code: RaceDecision): HumanDecision {
  const m = DECISION_MAP[code] ?? { label: code, tone: "neutral" as DecisionTone };
  return { ...m, code };
}

export const TONE_COLOR: Record<DecisionTone, string> = {
  good: "#22C55E",
  warn: "#FFB000",
  muted: "var(--faint)",
  error: "#EF4444",
  neutral: "var(--body-secondary)",
};

// ─── Formatting: zero ≠ unknown ────────────────────────────────
// null / undefined => explicit unknown marker. 0 is real data.

export function fmtNum(v: number | null | undefined, digits = 4, unknown = "—"): string {
  if (v === null || v === undefined || Number.isNaN(v)) return unknown;
  return v.toFixed(digits);
}

export function fmtInt(v: number | null | undefined, unknown = "—"): string {
  if (v === null || v === undefined || Number.isNaN(v)) return unknown;
  return v.toLocaleString("en-US");
}

export function fmtVal(v: string | number | null | undefined, unknown = "—"): string {
  if (v === null || v === undefined) return unknown;
  if (typeof v === "number") return Number.isNaN(v) ? unknown : String(v);
  return v === "" ? unknown : v;
}

// ─── Human runtime / duration axes ─────────────────────────────
// Turns raw seconds into "15s · 30s · 1m · 2m · 5m" style labels.

export function fmtDuration(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined || Number.isNaN(seconds)) return "—";
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const m = seconds / 60;
  if (m < 60) return m < 10 ? `${m.toFixed(m % 1 === 0 ? 0 : 1)}m` : `${Math.round(m)}m`;
  const h = m / 60;
  return `${h.toFixed(h % 1 === 0 ? 0 : 1)}h`;
}

// elapsed like "3m 12s"
export function fmtElapsed(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined || Number.isNaN(seconds)) return "—";
  const s = Math.max(0, Math.round(seconds));
  const m = Math.floor(s / 60);
  const rem = s % 60;
  if (m === 0) return `${rem}s`;
  const h = Math.floor(m / 60);
  if (h === 0) return `${m}m ${rem}s`;
  return `${h}h ${m % 60}m`;
}

// ETA phrasing with honest imprecision
export function fmtEta(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined || Number.isNaN(seconds)) return "estimating…";
  if (seconds <= 0) return "finishing…";
  return `~${fmtDuration(seconds)} remaining`;
}

export function fmtClock(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleTimeString("en-GB", { hour12: false });
}

// Given a start ISO and total estimated seconds, expected finish clock.
export function expectedFinish(startIso: string | null | undefined, totalSeconds: number | null | undefined): string {
  if (!startIso || totalSeconds === null || totalSeconds === undefined) return "—";
  const start = new Date(startIso).getTime();
  if (Number.isNaN(start)) return "—";
  return fmtClock(new Date(start + totalSeconds * 1000).toISOString());
}

export function elapsedSince(startIso: string | null | undefined): number | null {
  if (!startIso) return null;
  const t = new Date(startIso).getTime();
  if (Number.isNaN(t)) return null;
  return (Date.now() - t) / 1000;
}

// ─── Glossary of domain terms ──────────────────────────────────
// Definitions surfaced through hover tooltips and the Documentation
// glossary. Domain terminology is kept — never replaced with vague words.

export const GLOSSARY: Record<string, string> = {
  CORR20:
    "Rank correlation of predictions against the target over a 20-period window — a core competition scoring component.",
  AIMC:
    "Adjusted information-metric component reported by the event scorer. Weight and value come from event introspection.",
  NCORR:
    "Neutralised correlation — correlation after feature exposure has been removed. Reported by the scorer when supported.",
  IC:
    "Information coefficient: correlation between predictions and realised targets per expedition.",
  ICIR:
    "Information ratio: mean IC divided by its standard deviation — how consistent the signal is across expeditions.",
  exped:
    "Expedition — the event's cross-sectional grouping unit (one scored slice of the data). Field naming comes from the event.",
  OOF:
    "Out-of-fold predictions: validation predictions produced on data the model did not train on.",
  frontier:
    "The set of candidates that are not dominated on the score / diversity / runtime trade-off — the current research front.",
  diversity:
    "How independent a candidate's predictions are from the current champion. High diversity can add ensemble signal.",
  "worst fold":
    "The lowest score across cross-validation folds — a robustness floor rather than an average.",
};

// ─── Operating flow ───────────────────────────────────────────
// The global research workflow shown on Overview. Backend supplies the
// state; the frontend never guesses ordering.

export type FlowState = "waiting" | "ready" | "active" | "complete" | "attention" | "blocked";

export const FLOW_STATE_COLOR: Record<FlowState, string> = {
  waiting: "var(--faint)",
  ready: "#38BDF8",
  active: "#FFB000",
  complete: "#22C55E",
  attention: "#FFB000",
  blocked: "#EF4444",
};

export const FLOW_STATE_LABEL: Record<FlowState, string> = {
  waiting: "Waiting",
  ready: "Ready",
  active: "Active",
  complete: "Complete",
  attention: "Attention",
  blocked: "Blocked",
};
