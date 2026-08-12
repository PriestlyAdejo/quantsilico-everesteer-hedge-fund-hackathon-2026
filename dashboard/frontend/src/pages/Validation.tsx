import { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, CartesianGrid } from "recharts";
import { useDataSource } from "../data/useDataSource";
import type { ValidationData } from "../data/types";
import { CHART, CHART_SERIES } from "../data/chartTokens";
import { PAGE_META, humanizeDecision, TONE_COLOR, fmtClock } from "../data/humanize";
import Panel from "../components/Panel";
import Heatmap from "../components/Heatmap";
import PageHeader from "../components/PageHeader";
import Tip from "../components/Tip";
import StatusPage from "../components/StatusPage";

const TT = { background: "var(--elevated)", border: "1px solid var(--border)", borderRadius: 2, fontSize: 11, fontFamily: "'JetBrains Mono', monospace" };

const INTEGRITY_COLOR: Record<string, string> = {
  PASS: CHART.green,
  FAIL: CHART.red,
  UNKNOWN: "var(--faint)",
};

const EVIDENCE_COLOR: Record<string, string> = {
  STRONG: CHART.green,
  MIXED: CHART.amber,
  WEAK: "#A3AFBA",
  INSUFFICIENT: "var(--faint)",
};

const SECTION_TITLE: React.CSSProperties = {
  fontFamily: "'Raleway', sans-serif",
  fontSize: 14,
  fontWeight: 700,
  color: "var(--foreground)",
  margin: 0,
};

const SECTION_SUB: React.CSSProperties = {
  fontFamily: "'Raleway', sans-serif",
  fontSize: 12,
  color: "var(--body-secondary)",
  margin: "2px 0 0",
  lineHeight: 1.45,
};

export default function Validation() {
  const ds = useDataSource();
  const [data, setData] = useState<ValidationData | null>(null);
  const [source, setSource] = useState<string | undefined>(undefined);
  const [generatedAt, setGeneratedAt] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    ds.getValidation().then((e) => {
      setData(e.data);
      setSource(e.source);
      setGeneratedAt(e.generatedAt);
      setLoading(false);
    });
  }, [ds]);

  if (loading) return <StatusPage state="loading" />;
  if (!data) return <StatusPage state="backend-unavailable" />;

  const meta = PAGE_META["/validation"];

  // Fold heatmap structure (rows = folds, cols = rounds)
  const folds = Array.from(new Set(data.foldHeatmap.map((d) => d.fold)));
  const rounds = Array.from(new Set(data.foldHeatmap.map((d) => d.round)));
  const foldMap: Record<string, Record<string, number>> = {};
  data.foldHeatmap.forEach(({ fold, round, score }) => {
    if (!foldMap[fold]) foldMap[fold] = {};
    foldMap[fold][round] = score;
  });

  const decision = humanizeDecision(data.raceDecision.decision);
  const decColor = TONE_COLOR[decision.tone];
  const hasFail = data.hardIntegrity.some((c) => c.status === "FAIL");

  return (
    <div style={{ padding: 16, display: "flex", flexDirection: "column", gap: 16 }}>
      <PageHeader title={meta.title} intro={meta.intro} source={source} updatedAt={generatedAt} />

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 14, alignItems: "start" }}>
        {/* Section 1: Can this result be trusted? */}
        <Panel style={{ borderColor: hasFail ? CHART.red : "var(--border)" }}>
          <h2 style={SECTION_TITLE}>Can this result be trusted?</h2>
          <p style={SECTION_SUB}>Integrity checks. A single failure blocks promotion.</p>
          <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 12 }}>
            {data.hardIntegrity.map((c) => (
              <div key={c.check} style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                <span style={{
                  fontFamily: "'JetBrains Mono', monospace", fontSize: 11, fontWeight: 600, width: 60, flexShrink: 0,
                  color: INTEGRITY_COLOR[c.status] ?? "var(--metadata)",
                }}>
                  {c.status}
                </span>
                <div>
                  <div style={{ fontFamily: "'Montserrat', sans-serif", fontSize: 11, color: "var(--foreground)" }}>{c.check}</div>
                  <div style={{ fontFamily: "'Raleway', sans-serif", fontSize: 11, color: "var(--metadata)", lineHeight: 1.4 }}>{c.detail}</div>
                </div>
              </div>
            ))}
          </div>
        </Panel>

        {/* Section 2: How strong is the evidence? */}
        <Panel>
          <h2 style={SECTION_TITLE}>How strong is the evidence?</h2>
          <p style={SECTION_SUB}>Research metrics. Weak evidence is not a failure — it means less confidence.</p>
          <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 12 }}>
            {data.softResearch.map((m) => (
              <div key={m.metric} style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                <span style={{
                  fontFamily: "'JetBrains Mono', monospace", fontSize: 10, fontWeight: 600, width: 84, flexShrink: 0,
                  color: EVIDENCE_COLOR[m.interpretation] ?? "var(--metadata)",
                }}>
                  {m.interpretation}
                </span>
                <div>
                  <div style={{ fontFamily: "'Montserrat', sans-serif", fontSize: 11, color: "var(--foreground)" }}>
                    {m.term ? <Tip term={m.term}>{m.metric}</Tip> : m.metric}
                  </div>
                  <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10.5, color: "var(--metadata)", lineHeight: 1.4 }}>
                    {m.value} — {m.detail}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Panel>

        {/* Section 3: What happens next? */}
        <Panel style={{ borderColor: decColor + "55" }}>
          <h2 style={SECTION_TITLE}>What happens next?</h2>
          <p style={SECTION_SUB}>The race decision for this candidate.</p>
          <div style={{ marginTop: 14 }}>
            <div style={{ fontFamily: "'Raleway', sans-serif", fontSize: 16, fontWeight: 700, color: decColor, lineHeight: 1.3 }}>
              {decision.label}
            </div>
            <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: CHART.amber, marginTop: 8 }}>
              Stage: {data.raceDecision.stage}
            </div>
          </div>
          <div style={{ fontFamily: "'Raleway', sans-serif", fontSize: 12, color: "var(--body-secondary)", lineHeight: 1.5, marginTop: 12 }}>
            {data.raceDecision.rationale}
          </div>
          <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, color: "var(--faint)", marginTop: 14 }}>
            code: {decision.code}
          </div>
        </Panel>
      </div>

      {/* Charts */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        <Panel title="Evidence timeline — score over time (early → recent)">
          <ResponsiveContainer width="100%" height={170}>
            <LineChart data={data.timeline}>
              <CartesianGrid stroke="var(--border)" strokeDasharray="2 4" vertical={false} />
              <XAxis dataKey="ts" tickFormatter={fmtClock} tick={{ fill: "var(--metadata)", fontSize: 9 }} minTickGap={40} />
              <YAxis domain={["auto", "auto"]} tick={{ fill: "var(--metadata)", fontSize: 10 }} width={48} tickFormatter={(v) => v.toFixed(3)} />
              <Tooltip contentStyle={TT} labelFormatter={(l) => fmtClock(String(l))} formatter={((v: any) => [Number(v).toFixed(4), "Score"]) as any} />
              <Line type="monotone" dataKey="score" stroke={CHART_SERIES[0]} strokeWidth={2} dot={false} name="Score" />
            </LineChart>
          </ResponsiveContainer>
        </Panel>
        <Panel title="Score distribution across folds and rounds">
          <ResponsiveContainer width="100%" height={170}>
            <BarChart data={data.scoreDist}>
              <CartesianGrid stroke="var(--border)" strokeDasharray="2 4" vertical={false} />
              <XAxis dataKey="bucket" tick={{ fill: "var(--metadata)", fontSize: 9 }} />
              <YAxis tick={{ fill: "var(--metadata)", fontSize: 10 }} width={30} allowDecimals={false} />
              <Tooltip contentStyle={TT} formatter={((v: any) => [v, "Count"]) as any} />
              <Bar dataKey="count" fill={CHART_SERIES[1]} name="Count" />
            </BarChart>
          </ResponsiveContainer>
        </Panel>
      </div>

      <Panel title="Fold evidence — score by fold (rows) × round (columns)">
        <Heatmap rows={folds} cols={rounds} data={foldMap} colorLow="#0C1116" colorHigh={CHART.cyan} formatValue={(v) => v.toFixed(3)} />
      </Panel>
    </div>
  );
}
