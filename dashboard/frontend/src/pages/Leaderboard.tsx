import { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { useDataSource } from "../data/useDataSource";
import type { LeaderboardData, LeaderBoardEntry } from "../data/types";
import { CHART } from "../data/chartTokens";
import { PAGE_META, fmtNum, fmtInt, fmtVal } from "../data/humanize";
import PageHeader from "../components/PageHeader";
import Panel from "../components/Panel";
import Heatmap from "../components/Heatmap";
import StatusPage from "../components/StatusPage";

const TT = { background: "var(--elevated)", border: "1px solid var(--border)", borderRadius: 2, fontSize: 11, fontFamily: "'JetBrains Mono', monospace" };
const TABS = ["Current round", "Cumulative", "Our models", "History"] as const;
type Tab = typeof TABS[number];

type OurEntry = LeaderboardData["ourAliases"][number];

function ScoreChange({ v }: { v: number | null }) {
  if (v == null) return <span style={{ color: "var(--faint)" }}>—</span>;
  const color = v > 0 ? CHART.green : v < 0 ? CHART.red : "var(--metadata)";
  return <span style={{ color }}>{v > 0 ? "+" : ""}{fmtNum(v, 4)}</span>;
}

function RankChange({ v }: { v: number | null }) {
  if (v == null) return <span style={{ color: "var(--faint)" }}>—</span>;
  if (v === 0) return <span style={{ color: "var(--metadata)" }}>0</span>;
  // Positive rankChange => moved up (improvement).
  const up = v > 0;
  const color = up ? CHART.green : CHART.red;
  return <span style={{ color }}>{up ? "▲" : "▼"} {Math.abs(v)}</span>;
}

function BoardTable({ entries, isOur }: { entries: (LeaderBoardEntry | OurEntry)[]; isOur?: boolean }) {
  const hasScoreChange = entries.some((e) => e.scoreChange != null);
  const hasRankChange = entries.some((e) => e.rankChange != null);
  return (
    <table className="qs-table">
      <thead>
        <tr>
          <th>RANK</th>
          <th>MODEL</th>
          <th>SCORE</th>
          {hasScoreChange && <th>SCORE CHANGE</th>}
          {hasRankChange && <th>RANK CHANGE</th>}
          {isOur && <th>LOCAL → PRACTICE</th>}
          {isOur && <th>PRACTICE → LIVE</th>}
        </tr>
      </thead>
      <tbody>
        {entries.map((e, i) => (
          <tr key={i} style={{ background: e.isOurs ? "rgba(255,176,0,0.06)" : undefined }}>
            <td style={{ color: e.rank === 1 ? CHART.amber : "var(--body-primary)", fontWeight: e.rank === 1 ? 700 : 400 }}>
              {fmtVal(e.rank)}
            </td>
            <td style={{ color: e.isOurs ? "var(--accent)" : "var(--foreground)", fontWeight: e.isOurs ? 600 : 400 }}>
              {e.alias}{e.isOurs && " ◀"}
            </td>
            <td>{fmtNum(e.score, 4)}</td>
            {hasScoreChange && <td><ScoreChange v={e.scoreChange} /></td>}
            {hasRankChange && <td><RankChange v={e.rankChange} /></td>}
            {isOur && <td>{fmtNum((e as OurEntry).localVsPracticeGap, 4)}</td>}
            {isOur && <td>{fmtNum((e as OurEntry).practiceVsLiveGap, 4)}</td>}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function HistoryTable({ rows }: { rows: LeaderboardData["history"] }) {
  return (
    <table className="qs-table">
      <thead><tr><th>ROUND</th><th>RANK</th><th>SCORE</th></tr></thead>
      <tbody>
        {rows.map((h, i) => (
          <tr key={i}>
            <td style={{ color: "var(--foreground)" }}>{h.round}</td>
            <td style={{ color: h.rank === 1 ? CHART.amber : "var(--body-primary)" }}>{fmtVal(h.rank)}</td>
            <td>{fmtNum(h.score, 4)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function Leaderboard() {
  const ds = useDataSource();
  const [data, setData] = useState<LeaderboardData | null>(null);
  const [source, setSource] = useState<string>("");
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>("Current round");

  useEffect(() => {
    ds.getLeaderboard().then((e) => {
      setData(e.data);
      setSource(e.data.source || e.source);
      setUpdatedAt(e.generatedAt);
      setLoading(false);
    });
  }, [ds]);

  if (loading) return <StatusPage state="loading" />;
  if (!data) return <StatusPage state="backend-unavailable" />;

  // Build round×model heatmap (nulls skipped — never rendered as 0).
  const models = Array.from(new Set(data.roundModelMatrix.map((d) => d.model)));
  const rounds = Array.from(new Set(data.roundModelMatrix.map((d) => d.round)));
  const matMap: Record<string, Record<string, number>> = {};
  data.roundModelMatrix.forEach(({ model, round, score }) => {
    if (!matMap[model]) matMap[model] = {};
    if (score != null) matMap[model][round] = score;
  });
  const hasMatrix = models.length > 0 && rounds.length > 0;

  return (
    <div style={{ padding: 16, display: "flex", flexDirection: "column", gap: 14 }}>
      <PageHeader
        title={PAGE_META["/leaderboard"].title}
        intro={PAGE_META["/leaderboard"].intro}
        source={source}
        updatedAt={updatedAt}
      />

      {/* Tabs */}
      <div style={{ display: "flex", gap: 0, borderBottom: "1px solid var(--border)" }}>
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{
              background: "none",
              border: "none",
              borderBottom: tab === t ? "2px solid var(--accent)" : "2px solid transparent",
              color: tab === t ? "var(--foreground)" : "var(--metadata)",
              fontFamily: "'Montserrat', sans-serif",
              fontSize: 11,
              fontWeight: tab === t ? 600 : 400,
              padding: "8px 16px",
              cursor: "pointer",
              letterSpacing: "0.04em",
              marginBottom: -1,
            }}
          >
            {t}
          </button>
        ))}
      </div>

      <Panel noPad>
        {tab === "Current round" && <BoardTable entries={data.currentRound} />}
        {tab === "Cumulative" && <BoardTable entries={data.cumulative} />}
        {tab === "Our models" && <BoardTable entries={data.ourAliases} isOur />}
        {tab === "History" && <HistoryTable rows={data.history} />}
      </Panel>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        <Panel title="Rank trajectory">
          <ResponsiveContainer width="100%" height={150}>
            <LineChart data={data.rankTrajectory}>
              <XAxis dataKey="round" tick={{ fill: "var(--metadata)", fontSize: 10 }} />
              <YAxis reversed allowDecimals={false} tick={{ fill: "var(--metadata)", fontSize: 10 }} />
              <Tooltip contentStyle={TT} />
              <Line type="monotone" dataKey="rank" stroke={CHART.amber} strokeWidth={2} dot={{ fill: CHART.amber, r: 3 }} connectNulls={false} />
            </LineChart>
          </ResponsiveContainer>
          <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, color: "var(--faint)", marginTop: 4 }}>
            1 = best (axis reversed)
          </div>
        </Panel>
        <Panel title="Score trajectory">
          <ResponsiveContainer width="100%" height={150}>
            <LineChart data={data.scoreTrajectory}>
              <XAxis dataKey="round" tick={{ fill: "var(--metadata)", fontSize: 10 }} />
              <YAxis domain={["auto", "auto"]} tick={{ fill: "var(--metadata)", fontSize: 10 }} />
              <Tooltip contentStyle={TT} />
              <Line type="monotone" dataKey="score" stroke={CHART.cyan} strokeWidth={2} dot={false} connectNulls={false} />
            </LineChart>
          </ResponsiveContainer>
          <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, color: "var(--faint)", marginTop: 4 }}>
            {fmtInt(data.scoreTrajectory.length)} rounds
          </div>
        </Panel>
      </div>

      {hasMatrix && (
        <Panel title="Round × model score matrix">
          <Heatmap rows={models} cols={rounds} data={matMap} colorLow="#0C1116" colorHigh={CHART.cyan} formatValue={(v) => v.toFixed(3)} />
        </Panel>
      )}
    </div>
  );
}
