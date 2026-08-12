import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  ScatterChart, Scatter, ZAxis, BarChart, Bar, PieChart, Pie, Cell, Legend,
} from "recharts";
import { useDataSource } from "../data/useDataSource";
import type { OverviewData } from "../data/types";
import { CHART, STAGE_COLOR } from "../data/chartTokens";
import { PAGE_META, FLOW_STATE_COLOR, FLOW_STATE_LABEL, fmtDuration } from "../data/humanize";
import Panel, { Btn, MetricTile } from "../components/Panel";
import PageHeader from "../components/PageHeader";
import Tip from "../components/Tip";
import StatusPage from "../components/StatusPage";

const PAGE = { padding: 16, display: "flex", flexDirection: "column" as const, gap: 14, minHeight: "100%" };
const CHART_STYLE = { fontFamily: "'JetBrains Mono', monospace", fontSize: 10 };
const TT_STYLE = { background: "var(--elevated)", border: "1px solid var(--border)", borderRadius: 2, fontSize: 11, fontFamily: "'JetBrains Mono', monospace" };

export default function Overview() {
  const ds = useDataSource();
  const nav = useNavigate();
  const [data, setData] = useState<OverviewData | null>(null);
  const [meta, setMeta] = useState<{ source: string; updatedAt: string } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    ds.getOverview().then((e) => { setData(e.data); setMeta({ source: e.source, updatedAt: e.generatedAt }); setLoading(false); });
  }, [ds]);

  if (loading) return <StatusPage state="loading" />;
  if (!data) return <StatusPage state="backend-unavailable" />;

  return (
    <div style={PAGE}>
      <PageHeader title={PAGE_META["/"].title} intro={PAGE_META["/"].intro} source={meta?.source} updatedAt={meta?.updatedAt} />

      {/* Operating flow */}
      <Panel title="Operating flow">
        <div style={{ display: "flex", alignItems: "stretch", gap: 0, overflowX: "auto", paddingBottom: 4 }}>
          {data.flow.map((n, i) => {
            const active = n.id === data.currentStage;
            const color = FLOW_STATE_COLOR[n.state];
            return (
              <div key={n.id} style={{ display: "flex", alignItems: "center", flexShrink: 0 }}>
                <div style={{
                  display: "flex", flexDirection: "column", alignItems: "center", gap: 4,
                  padding: "6px 12px", borderRadius: 3,
                  border: `1px solid ${active ? "var(--accent)" : "var(--border)"}`,
                  background: active ? "rgba(255,176,0,0.08)" : "transparent",
                  minWidth: 96,
                }}>
                  <span style={{ width: 8, height: 8, borderRadius: "50%", background: color, boxShadow: active ? `0 0 6px ${color}` : "none" }} />
                  <span style={{ fontFamily: "'Montserrat', sans-serif", fontSize: 11, fontWeight: active ? 700 : 500, color: active ? "var(--foreground)" : "var(--body-secondary)", whiteSpace: "nowrap" }}>{n.label}</span>
                  <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 9, color }}>{FLOW_STATE_LABEL[n.state]}</span>
                </div>
                {i < data.flow.length - 1 && <span style={{ color: "var(--faint)", padding: "0 6px", fontSize: 12 }}>→</span>}
              </div>
            );
          })}
        </div>
        {/* Recommended next action */}
        <div style={{ marginTop: 12, padding: "10px 12px", background: "var(--surface-deep)", border: "1px solid var(--border)", borderLeft: "2px solid var(--accent)", borderRadius: 2 }}>
          <div style={{ fontFamily: "'Montserrat', sans-serif", fontSize: 11, color: "var(--metadata)", marginBottom: 4 }}>Recommended next action</div>
          <div style={{ fontFamily: "'Raleway', sans-serif", fontSize: 13, color: "var(--body-primary)", lineHeight: 1.5, marginBottom: 10 }}>{data.recommendation.text}</div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {data.recommendation.actions.map((a, i) => (
              <Btn key={a.to} variant={i === 0 ? "accent" : "surface"} onClick={() => nav(a.to)}>{a.label}</Btn>
            ))}
          </div>
        </div>
      </Panel>

      {/* Primary metrics */}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        {data.metrics.map((m, i) => (
          <MetricTile
            key={i}
            label={m.label}
            value={m.value ?? "—"}
            accent={m.label === "Round" || m.label === "Champion"}
            warn={m.value === null && m.label === "Live score"}
          />
        ))}
      </div>

      {/* Research metrics strip */}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        {data.researchMetrics.map((m, i) => (
          <MetricTile
            key={i}
            label={m.label}
            value={m.value ?? "—"}
            labelNode={m.term ? <Tip term={m.term}>{m.label}</Tip> : undefined}
          />
        ))}
      </div>

      {/* Charts row 1 */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        <Panel title="Score trajectory by round">
          <ResponsiveContainer width="100%" height={170}>
            <LineChart data={data.scoreHistory} style={CHART_STYLE}>
              <XAxis dataKey="round" tick={{ fill: "var(--metadata)", fontSize: 10 }} />
              <YAxis domain={["auto", "auto"]} tick={{ fill: "var(--metadata)", fontSize: 10 }} width={48} tickFormatter={(v) => v.toFixed(3)} />
              <Tooltip contentStyle={TT_STYLE} />
              <Line type="monotone" dataKey="score" stroke={CHART.cyan} strokeWidth={2} dot={false} name="Score" />
            </LineChart>
          </ResponsiveContainer>
        </Panel>

        <Panel title="Experiment frontier — runtime vs local score">
          <ResponsiveContainer width="100%" height={170}>
            <ScatterChart style={CHART_STYLE} margin={{ bottom: 8 }}>
              <XAxis
                dataKey="runtimeSeconds"
                type="number"
                name="Runtime"
                scale="log"
                domain={["auto", "auto"]}
                tick={{ fill: "var(--metadata)", fontSize: 10 }}
                tickFormatter={fmtDuration}
                label={{ value: "runtime", position: "insideBottom", offset: -4, fill: "var(--faint)", fontSize: 9 }}
              />
              <YAxis dataKey="score" name="Local score" tick={{ fill: "var(--metadata)", fontSize: 10 }} width={48} tickFormatter={(v) => v.toFixed(2)} />
              <ZAxis dataKey="diversity" range={[30, 150]} name="Diversity" />
              <Tooltip contentStyle={TT_STYLE} content={({ payload }) => {
                if (!payload?.length) return null;
                const d = payload[0]?.payload;
                return (
                  <div style={{ ...TT_STYLE, padding: "8px 10px" }}>
                    <div style={{ color: "var(--accent)", fontWeight: 600 }}>{d.name}</div>
                    <div>score: {d.score?.toFixed(4)}</div>
                    <div>runtime: {fmtDuration(d.runtimeSeconds)}</div>
                    <div>diversity: {d.diversity?.toFixed(2)}</div>
                    <div>family: {d.family}</div>
                    <div>stage: <span style={{ color: STAGE_COLOR[d.stage] || "var(--metadata)" }}>{d.stage}</span></div>
                  </div>
                );
              }} />
              {Object.entries(STAGE_COLOR).map(([stage, color]) => (
                <Scatter key={stage} name={stage} data={data.experiments.filter((e) => e.stage === stage)} fill={color} />
              ))}
            </ScatterChart>
          </ResponsiveContainer>
          <div style={{ display: "flex", gap: 12, marginTop: 4, flexWrap: "wrap" }}>
            {Object.entries(STAGE_COLOR).map(([s, c]) => (
              <span key={s} style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 9.5, color: c }}>● {s}</span>
            ))}
            <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 9.5, color: "var(--faint)" }}>size = diversity · shape colour = stage</span>
          </div>
        </Panel>
      </div>

      {/* Charts row 2 */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        <Panel title="Fold evidence — score by round">
          <ResponsiveContainer width="100%" height={170}>
            <BarChart data={data.foldEvidence} style={CHART_STYLE}>
              <XAxis dataKey="fold" tick={{ fill: "var(--metadata)", fontSize: 10 }} />
              <YAxis domain={["auto", "auto"]} tick={{ fill: "var(--metadata)", fontSize: 10 }} width={44} tickFormatter={(v) => v.toFixed(2)} />
              <Tooltip contentStyle={TT_STYLE} />
              <Bar dataKey="r0" fill={CHART.neutral} name="R0" />
              <Bar dataKey="r1" fill={CHART.cyan} name="R1" />
              <Bar dataKey="r2" fill={CHART.blue} name="R2" />
              <Bar dataKey="r3" fill={CHART.violet} name="R3" />
              <Legend wrapperStyle={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, color: "var(--metadata)" }} />
            </BarChart>
          </ResponsiveContainer>
        </Panel>

        <Panel title="Upload budget">
          <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
            <PieChart width={150} height={150}>
              <Pie data={data.uploadQuota} dataKey="value" innerRadius={42} outerRadius={64} paddingAngle={2}>
                {data.uploadQuota.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
              </Pie>
            </PieChart>
            <div style={{ display: "flex", flexDirection: "column", gap: 7, flex: 1 }}>
              {data.uploadQuota.map((q, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <div style={{ width: 8, height: 8, background: q.fill, borderRadius: 1, flexShrink: 0 }} />
                  <span style={{ fontFamily: "'Montserrat', sans-serif", fontSize: 11.5, color: "var(--body-secondary)" }}>{q.label}</span>
                  <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12.5, color: "var(--body-primary)", marginLeft: "auto" }}>{q.value}</span>
                </div>
              ))}
            </div>
          </div>
          <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, color: "var(--faint)", marginTop: 8 }}>Submission budget allocation — not scoring weight.</div>
        </Panel>
      </div>

      {/* Decisions & warnings */}
      <Panel title="Latest decisions & integrity warnings">
        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          {data.latestDecisions.map((d, i) => (
            <div key={i} style={{ display: "flex", gap: 10, alignItems: "flex-start", padding: "5px 0", borderBottom: "1px solid rgba(30,38,48,0.5)" }}>
              <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10.5, color: "var(--faint)", flexShrink: 0, whiteSpace: "nowrap" }}>
                {new Date(d.ts).toLocaleTimeString("en-GB", { hour12: false })}
              </span>
              <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11.5, color: d.level === "error" ? "#EF4444" : d.level === "warn" ? "#FFB000" : "var(--body-primary)" }}>
                {d.text}
              </span>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}
