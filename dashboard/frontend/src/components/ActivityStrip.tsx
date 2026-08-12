import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { useDataSource } from "../data/useDataSource";
import type { Job } from "../data/types";
import { fmtElapsed, fmtEta, elapsedSince } from "../data/humanize";

export default function ActivityStrip() {
  const ds = useDataSource();
  const nav = useNavigate();
  const [job, setJob] = useState<Job | null>(null);
  const [queueLen, setQueueLen] = useState<number | null>(null);
  const [, setTick] = useState(0);

  useEffect(() => {
    let alive = true;
    const load = () =>
      ds.getComputeJobs().then((e) => {
        if (!alive) return;
        const running = e.data.localQueue.find((j) => j.status === "RUNNING") ?? e.data.localQueue[0] ?? null;
        setJob(running);
        setQueueLen(e.data.utilisation.queueLength);
      });
    load();
    const poll = setInterval(load, 5000);
    const tick = setInterval(() => setTick((n) => n + 1), 1000);
    return () => { alive = false; clearInterval(poll); clearInterval(tick); };
  }, [ds]);

  const el = job ? elapsedSince(job.startedAt) : null;

  return (
    <div
      onClick={() => nav("/compute")}
      title="Open Compute & Jobs"
      style={{
        height: 24,
        background: "var(--surface-deep)",
        borderTop: "1px solid var(--border)",
        display: "flex",
        alignItems: "center",
        padding: "0 14px",
        gap: 14,
        flexShrink: 0,
        cursor: "pointer",
      }}
    >
      {job ? (
        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: "var(--body-secondary)", flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          <span style={{ color: "var(--accent)" }}>{job.name}</span>
          {job.status === "RUNNING" && el != null && <span> · running {fmtElapsed(el)}</span>}
          {job.status === "RUNNING" && <span> · {fmtEta(job.etaSeconds)}</span>}
          {job.status !== "RUNNING" && <span> · {job.status.toLowerCase()}</span>}
          {queueLen != null && queueLen > 1 && <span style={{ color: "var(--faint)" }}> · {queueLen - 1} more queued</span>}
        </span>
      ) : (
        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: "var(--faint)", flex: 1 }}>No active jobs</span>
      )}
      <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, color: "var(--faint)" }}>Compute &amp; Jobs →</span>
    </div>
  );
}
