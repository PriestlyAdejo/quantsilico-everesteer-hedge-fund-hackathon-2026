import { useEffect, useState } from "react";
import { useDataSource } from "../data/useDataSource";
import type { EventControlData, CapabilityStatus } from "../data/types";
import Panel, { Btn } from "../components/Panel";
import PageHeader from "../components/PageHeader";
import Tip from "../components/Tip";
import StatusPage from "../components/StatusPage";
import SubmissionModeBanner from "../components/SubmissionModeBanner";
import { PAGE_META, fmtNum, fmtVal, fmtClock } from "../data/humanize";

const PAGE = { padding: 16, display: "flex", flexDirection: "column" as const, gap: 14 };

function KV({ label, value, term }: { label: string; value: string; term?: string }) {
  return (
    <div>
      <div className="qs-kv-label" style={{ marginBottom: 3 }}>{term ? <Tip term={term}>{label}</Tip> : label}</div>
      <div className="qs-kv-value">{value}</div>
    </div>
  );
}

const CAP_STYLE: Record<CapabilityStatus, { label: string; color: string }> = {
  available: { label: "Available", color: "#22C55E" },
  unavailable: { label: "Unavailable", color: "var(--faint)" },
  unknown: { label: "Unknown", color: "#FFB000" },
};

export default function EventControl() {
  const ds = useDataSource();
  const [data, setData] = useState<EventControlData | null>(null);
  const [meta, setMeta] = useState<{ source: string; updatedAt: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLog, setActionLog] = useState<string[]>([]);
  const [autopilot, setAutopilot] = useState(false);

  useEffect(() => {
    ds.getEventControl().then((e) => {
      setData(e.data);
      setMeta({ source: e.source, updatedAt: e.generatedAt });
      setAutopilot(e.data?.autopilotActive ?? false);
      setLoading(false);
    });
  }, [ds]);

  const runAction = async (fn: () => Promise<{ message: string }>, label: string) => {
    setActionLog((l) => [`[${new Date().toLocaleTimeString("en-GB", { hour12: false })}] ${label}…`, ...l]);
    const r = await fn();
    setActionLog((l) => [r.message, ...l.slice(0, 19)]);
  };

  if (loading) return <StatusPage state="loading" />;
  if (!data) return <StatusPage state="backend-unavailable" />;

  const conn = data.connection;
  const es = data.eventState;
  const sc = data.scoring;

  return (
    <div style={PAGE}>
      <PageHeader title={PAGE_META["/event"].title} intro={PAGE_META["/event"].intro} source={meta?.source} updatedAt={meta?.updatedAt} />
      <SubmissionModeBanner mode={data.submissionMode} />

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        {/* Connection */}
        <Panel title="Connection">
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <KV label="API status" value={conn.apiStatus.replace("_", " ")} />
            <KV label="SDK version" value={fmtVal(conn.sdkVersion)} />
            <KV label="Scope" value={fmtVal(conn.scope)} />
            <KV label="Key fingerprint" value={fmtVal(conn.keyFingerprint)} />
            <KV label="Last successful request" value={fmtClock(conn.lastRequestAt)} />
          </div>
        </Panel>

        {/* Event state */}
        <Panel title="Event state">
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <KV label="Event" value={fmtVal(es.eventId)} />
            <KV label="Tournament" value={fmtVal(es.tournament)} />
            <KV label="Phase" value={fmtVal(es.phase)} />
            <KV label="Current round" value={fmtVal(es.currentRound)} />
            <KV label="Round opened" value={fmtClock(es.roundOpenedAt)} />
            <KV label="Time remaining" value={fmtVal(es.timeRemaining)} />
          </div>
        </Panel>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 14 }}>
        {/* Scoring — dynamic rendering contract, never invented */}
        <Panel title="Current scoring">
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
            <KV label="Rank metric" value={fmtVal(sc.rankMetric)} term={sc.rankMetric ?? undefined} />
            <KV label="Primary target" value={fmtVal(sc.primaryTarget)} />
          </div>
          <table className="qs-table">
            <thead><tr><th>Component</th><th>Weight</th><th>Value</th></tr></thead>
            <tbody>
              {sc.components.map((c) => (
                <tr key={c.name}>
                  <td><Tip term={c.name}>{c.name}</Tip></td>
                  {c.provided ? (
                    <>
                      <td>{c.weight != null ? `${(c.weight * 100).toFixed(0)}%` : "—"}</td>
                      <td>{fmtNum(c.value)}</td>
                    </>
                  ) : (
                    <td colSpan={2} style={{ color: "var(--faint)" }}>Not provided by event</td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, color: "var(--faint)", marginTop: 10 }}>
            Scoring snapshot: {fmtClock(sc.snapshotAt)} · rendered from event introspection. Practice / live submission allocation lives in Submission.
          </div>
        </Panel>

        {/* Capabilities */}
        <Panel title="Capabilities">
          <table className="qs-table">
            <thead><tr><th>Capability</th><th>Status</th></tr></thead>
            <tbody>
              {data.capabilities.map((c) => {
                const cs = CAP_STYLE[c.status];
                return (
                  <tr key={c.name}>
                    <td style={{ fontFamily: "'Montserrat', sans-serif" }}>{c.name}</td>
                    <td style={{ color: cs.color }}>{cs.label}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Panel>
      </div>

      {/* Controls */}
      <Panel title="Allowlisted controls" actions={
        <Btn variant={autopilot ? "accent" : "ghost"} onClick={async () => {
          if (autopilot) { await runAction(ds.stopAutopilot.bind(ds), "Stop autopilot"); setAutopilot(false); }
          else { await runAction(ds.startAutopilot.bind(ds), "Start autopilot"); setAutopilot(true); }
        }}>
          {autopilot ? "⏹ Autopilot on" : "▶ Autopilot off"}
        </Btn>
      }>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 14 }}>
          <Btn onClick={() => runAction(ds.refreshEvent.bind(ds), "Refresh event")}>↻ Refresh event</Btn>
          <Btn onClick={() => runAction(ds.snapshotEvent.bind(ds), "Snapshot event")}>⬡ Snapshot</Btn>
          <Btn onClick={() => runAction(ds.pullDatasets.bind(ds), "Pull datasets")}>↓ Pull data</Btn>
          <Btn onClick={() => runAction(ds.runScorerParity.bind(ds), "Scorer parity")}>≈ Scorer parity</Btn>
          <Btn variant="surface" onClick={() => runAction(ds.runOfficialBaseline.bind(ds), "Official baseline")}>⊙ Run baseline</Btn>
        </div>
        <div style={{ background: "var(--surface-deep)", border: "1px solid var(--border)", borderRadius: 2, padding: "8px 10px", maxHeight: 130, overflowY: "auto" }}>
          {actionLog.length === 0 && <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10.5, color: "var(--faint)" }}>No actions yet.</span>}
          {actionLog.map((msg, i) => (
            <div key={i} style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10.5, color: "var(--body-primary)", padding: "1px 0" }}>{msg}</div>
          ))}
        </div>
        <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, color: "var(--faint)", marginTop: 8 }}>
          Latest snapshot: {fmtVal(data.latestSnapshot)}
        </div>
      </Panel>
    </div>
  );
}
