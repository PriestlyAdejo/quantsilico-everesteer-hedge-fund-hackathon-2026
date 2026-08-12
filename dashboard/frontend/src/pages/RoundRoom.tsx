import { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { useDataSource } from "../data/useDataSource";
import type { RoundRoomData, Job, ConnectionState } from "../data/types";
import { CHART, CHART_SERIES } from "../data/chartTokens";
import { PAGE_META, fmtInt, fmtNum, fmtVal, fmtClock } from "../data/humanize";
import PageHeader from "../components/PageHeader";
import Panel, { MetricTile } from "../components/Panel";
import JobTiming from "../components/JobTiming";
import Heatmap from "../components/Heatmap";
import StatusPage from "../components/StatusPage";
import SubmissionModeBanner from "../components/SubmissionModeBanner";

const TT = { background: "var(--elevated)", border: "1px solid var(--border)", borderRadius: 2, fontSize: 11, fontFamily: "'JetBrains Mono', monospace" };
const AXIS = { fill: "var(--metadata)", fontSize: 10, fontFamily: "'JetBrains Mono', monospace" };

const FEED_COLOR: Record<ConnectionState, string> = {
  LIVE: CHART.green,
  RECONNECTING: CHART.amber,
  DISCONNECTED: CHART.red,
  NOT_CONNECTED: "var(--faint)",
};

const STATUS_COLOR: Record<string, string> = {
  RUNNING: CHART.cyan,
  QUEUED: CHART.amber,
  PENDING: "var(--faint)",
  DONE: CHART.green,
  FAILED: CHART.red,
};

function JobTable({ jobs }: { jobs: Job[] }) {
  if (jobs.length === 0) {
    return <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: "var(--faint)", padding: "6px 2px" }}>Queue empty</div>;
  }
  return (
    <div style={{ overflowX: "auto" }}>
      <table className="qs-table">
        <thead>
          <tr>
            <th>Model</th>
            <th>Stage</th>
            <th>Status</th>
            <th>Timing</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((j) => (
            <tr key={j.id}>
              <td style={{ color: "var(--foreground)" }}>{fmtVal(j.candidate ?? j.name)}</td>
              <td style={{ color: "var(--metadata)" }}>{j.type}</td>
              <td>
                <span style={{ color: STATUS_COLOR[j.status] ?? "var(--metadata)", fontWeight: 600 }}>{j.status}</span>
              </td>
              <td><JobTiming job={j} compact /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function deltaColor(v: number | null): string {
  if (v == null || v === 0) return "var(--body-secondary)";
  return v > 0 ? CHART.green : CHART.red;
}

function signed(v: number | null, digits = 4): string {
  if (v == null) return "—";
  return `${v > 0 ? "+" : ""}${v.toFixed(digits)}`;
}

function Flag({ ok, okText, badText }: { ok: boolean; okText: string; badText: string }) {
  return (
    <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, fontWeight: 700, color: ok ? CHART.green : CHART.red }}>
      {ok ? okText : badText}
    </span>
  );
}

export default function RoundRoom() {
  const ds = useDataSource();
  const [data, setData] = useState<RoundRoomData | null>(null);
  const [env, setEnv] = useState<{ source: string; generatedAt: string } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    ds.getRoundRoom().then((e) => {
      setData(e.data);
      setEnv({ source: e.source, generatedAt: e.generatedAt });
      setLoading(false);
    });
  }, [ds]);

  if (loading) return <StatusPage state="loading" />;
  if (!data) return <StatusPage state="backend-unavailable" />;

  const statusColor =
    data.roundStatus === "open" ? CHART.green : data.roundStatus === "scoring" ? CHART.amber : "var(--metadata)";

  // Heatmap: rows = unique models, cols = unique rounds
  const heatRows = Array.from(new Set(data.heatmapData.map((d) => d.model)));
  const heatCols = Array.from(new Set(data.heatmapData.map((d) => d.round)));
  const heatMap: Record<string, Record<string, number | null>> = {};
  data.heatmapData.forEach(({ model, round, score }) => {
    (heatMap[model] ??= {})[round] = score;
  });

  return (
    <div style={{ padding: 16, display: "flex", flexDirection: "column", gap: 14 }}>
      <PageHeader
        title={PAGE_META["/round"].title}
        intro={PAGE_META["/round"].intro}
        source={env?.source}
        updatedAt={env?.generatedAt}
      />
      <SubmissionModeBanner mode={data.submissionMode} />

      {/* Top strip */}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <MetricTile label="Round" value={fmtVal(data.roundId)} accent />
        <MetricTile
          label="Status"
          value={data.roundStatus === "unknown" ? "UNKNOWN" : data.roundStatus.toUpperCase()}
          labelNode={<span style={{ color: statusColor }}>Status</span>}
        />
        <MetricTile label="Time remaining" value={fmtVal(data.countdown)} accent />
        <MetricTile label="Split fingerprint" value={fmtVal(data.splitFingerprint)} />
        <MetricTile label="Live rows" value={fmtInt(data.liveRows)} />
        <MetricTile
          label="Submissions (round)"
          value={fmtInt(data.submissionsUsedRound)}
          sub="used this round"
        />
        <MetricTile
          label="Submissions (event)"
          value={`${fmtInt(data.submissionsUsedEvent)} / ${fmtInt(data.submissionsTotalEvent)}`}
          sub="used / total"
        />
        <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius)", padding: "10px 14px", minWidth: 118, flex: "1 1 118px" }}>
          <div style={{ fontFamily: "'Montserrat', sans-serif", fontSize: 11, letterSpacing: "0.02em", color: "var(--metadata)", marginBottom: 7 }}>Live feed</div>
          <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 18, fontWeight: 600, color: FEED_COLOR[data.liveFeed], lineHeight: 1 }}>
            {data.liveFeed}
          </div>
        </div>
      </div>

      {/* Queues */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        <Panel title="Inference queue"><JobTable jobs={data.inferenceQueue} /></Panel>
        <Panel title="Submission queue"><JobTable jobs={data.submissionQueue} /></Panel>
      </div>

      {/* Current leaderboard */}
      <Panel title="Current leaderboard">
        <div style={{ overflowX: "auto" }}>
          <table className="qs-table">
            <thead>
              <tr>
                <th>Rank</th>
                <th>Model</th>
                <th>Score</th>
                <th>Score change</th>
                <th>Rank change</th>
              </tr>
            </thead>
            <tbody>
              {data.currentBoard.map((e) => (
                <tr key={e.alias} style={{ background: e.isOurs ? "rgba(255,176,0,0.06)" : undefined }}>
                  <td>{e.rank ?? "—"}</td>
                  <td style={{ color: e.isOurs ? "var(--accent)" : "var(--foreground)", fontWeight: e.isOurs ? 600 : 400 }}>
                    {e.alias}{e.isOurs ? " ◀ ours" : ""}
                  </td>
                  <td>{fmtNum(e.score)}</td>
                  <td style={{ color: deltaColor(e.scoreChange) }}>{signed(e.scoreChange)}</td>
                  <td style={{ color: e.rankChange == null || e.rankChange === 0 ? "var(--body-secondary)" : e.rankChange > 0 ? CHART.green : CHART.red }}>
                    {e.rankChange == null ? "—" : e.rankChange === 0 ? "0" : `${e.rankChange > 0 ? "+" : ""}${e.rankChange}`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      {/* Rank trajectory + heatmap */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        <Panel title="Rank trajectory" actions={
          <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10.5, color: "var(--faint)" }}>1 = best (top)</span>
        }>
          <ResponsiveContainer width="100%" height={170}>
            <LineChart data={data.rankByRound} margin={{ top: 8, right: 12, bottom: 4, left: -8 }}>
              <CartesianGrid stroke="var(--border)" strokeDasharray="2 4" />
              <XAxis dataKey="round" tick={AXIS} />
              <YAxis reversed allowDecimals={false} tick={AXIS} />
              <Tooltip contentStyle={TT} formatter={(v) => [v == null ? "—" : `rank ${v}`, "Rank"]} />
              <Line type="monotone" dataKey="rank" stroke={CHART_SERIES[0]} strokeWidth={2} dot={{ fill: CHART_SERIES[0], r: 3 }} connectNulls={false} />
            </LineChart>
          </ResponsiveContainer>
        </Panel>
        <Panel title="Model × round score heatmap">
          <Heatmap rows={heatRows} cols={heatCols} data={heatMap} colorLow="#0C1116" colorHigh={CHART.cyan} formatValue={(v) => v.toFixed(3)} />
        </Panel>
      </div>

      {/* Emergency */}
      <Panel title="Emergency — known-good fallback">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "10px 20px", fontFamily: "'JetBrains Mono', monospace", fontSize: 11.5 }}>
          <div>
            <div style={{ color: "var(--metadata)", fontSize: 10.5, marginBottom: 3 }}>Known-good champion</div>
            <div style={{ color: "var(--foreground)" }}>{fmtVal(data.emergency.champion)}</div>
          </div>
          <div>
            <div style={{ color: "var(--metadata)", fontSize: 10.5, marginBottom: 3 }}>Known-good ensemble</div>
            <div style={{ color: "var(--foreground)" }}>{fmtVal(data.emergency.ensemble)}</div>
          </div>
          <div>
            <div style={{ color: "var(--metadata)", fontSize: 10.5, marginBottom: 3 }}>Model hash</div>
            <div style={{ color: "var(--body-primary)" }}>{fmtVal(data.emergency.modelHash)}</div>
          </div>
          <div>
            <div style={{ color: "var(--metadata)", fontSize: 10.5, marginBottom: 3 }}>Current split verified</div>
            <Flag ok={data.emergency.splitVerified} okText="VERIFIED" badText="NOT VERIFIED" />
          </div>
          <div>
            <div style={{ color: "var(--metadata)", fontSize: 10.5, marginBottom: 3 }}>Submission ready</div>
            <Flag ok={data.emergency.submissionReady} okText="READY" badText="NOT READY" />
          </div>
        </div>
      </Panel>

      {/* Event log */}
      <Panel title="Event log">
        <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {data.eventLog.map((e, i) => (
            <div key={i} style={{ display: "flex", gap: 8 }}>
              <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10.5, color: "var(--faint)", flexShrink: 0 }}>
                {fmtClock(e.ts)}
              </span>
              <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10.5, color: e.level === "error" ? CHART.red : e.level === "warn" ? CHART.amber : "var(--body-primary)" }}>
                {e.msg}
              </span>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}
