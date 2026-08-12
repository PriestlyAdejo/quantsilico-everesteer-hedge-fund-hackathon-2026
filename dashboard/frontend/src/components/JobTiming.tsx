import { useEffect, useState } from "react";
import { fmtElapsed, fmtEta, fmtClock, elapsedSince } from "../data/humanize";

export interface JobTimingData {
  startedAt: string | null;
  /** Estimated remaining seconds; null => not enough history. */
  etaSeconds: number | null;
  /** Total estimated seconds for expected-finish; null if unknown. */
  totalSeconds?: number | null;
  progress?: number | null; // 0..1
  queuePosition?: number | null;
  status: string; // RUNNING / QUEUED / DONE / FAILED …
}

/**
 * Consistent "started · elapsed · ~remaining · expected finish" line for any
 * long-running job. Live-ticks elapsed while running. Uses honest imprecision
 * (~2m, estimating…) rather than fake precision.
 */
export default function JobTiming({ job, compact }: { job: JobTimingData; compact?: boolean }) {
  const running = job.status.toUpperCase() === "RUNNING";
  const [, setTick] = useState(0);
  useEffect(() => {
    if (!running) return;
    const t = setInterval(() => setTick((n) => n + 1), 1000);
    return () => clearInterval(t);
  }, [running]);

  const el = elapsedSince(job.startedAt);
  const mono: React.CSSProperties = {
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: compact ? 10.5 : 11,
    color: "var(--body-secondary)",
  };

  if (job.status.toUpperCase() === "QUEUED") {
    return (
      <span style={mono}>
        Queued{job.queuePosition != null ? ` · position ${job.queuePosition}` : ""}
        {job.etaSeconds != null && ` · starts in ${fmtEta(job.etaSeconds).replace("~", "~")}`}
      </span>
    );
  }

  const finish =
    job.startedAt && job.totalSeconds != null
      ? fmtClock(new Date(new Date(job.startedAt).getTime() + job.totalSeconds * 1000).toISOString())
      : null;

  return (
    <span style={{ display: "inline-flex", gap: 8, flexWrap: "wrap", ...mono }}>
      {job.startedAt && <span style={{ color: "var(--faint)" }}>started {fmtClock(job.startedAt)}</span>}
      {running && el != null && <span>running {fmtElapsed(el)}</span>}
      {running && <span style={{ color: "var(--accent)" }}>{fmtEta(job.etaSeconds)}</span>}
      {running && finish && <span style={{ color: "var(--faint)" }}>expected {finish}</span>}
      {job.progress != null && running && (
        <span style={{ color: "var(--faint)" }}>{Math.round(job.progress * 100)}%</span>
      )}
    </span>
  );
}
