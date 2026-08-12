import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, ScatterChart, Scatter, CartesianGrid } from "recharts";
import { useDataSource } from "../data/useDataSource";
import type { EnsembleData, EnsembleStrategy } from "../data/types";
import { CHART, CHART_SERIES } from "../data/chartTokens";
import { PAGE_META, fmtNum, fmtClock } from "../data/humanize";
import Panel, { Btn, MetricTile } from "../components/Panel";
import Heatmap from "../components/Heatmap";
import PageHeader from "../components/PageHeader";
import StatusPage from "../components/StatusPage";

const TT = { background: "var(--elevated)", border: "1px solid var(--border)", borderRadius: 2, fontSize: 11, fontFamily: "'JetBrains Mono', monospace" };

const ALL_STRATEGIES: EnsembleStrategy[] = ["rank_average", "weighted", "greedy", "diversity_aware", "neutralised"];

const STRATEGY_LABEL: Record<EnsembleStrategy, string> = {
  rank_average: "Rank average",
  weighted: "Weighted",
  greedy: "Greedy",
  diversity_aware: "Diversity-aware",
  neutralised: "Neutralised",
};

const inputStyle: React.CSSProperties = {
  width: 68,
  background: "var(--surface-deep)",
  border: "1px solid var(--border)",
  borderRadius: 2,
  color: "var(--foreground)",
  fontFamily: "'JetBrains Mono', monospace",
  fontSize: 11,
  padding: "3px 6px",
};

export default function Ensembles() {
  const ds = useDataSource();
  const [data, setData] = useState<EnsembleData | null>(null);
  const [source, setSource] = useState<string | undefined>(undefined);
  const [generatedAt, setGeneratedAt] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [strategy, setStrategy] = useState<EnsembleStrategy>("weighted");
  const [weights, setWeights] = useState<Record<string, number>>({});
  const [selectedMembers, setSelectedMembers] = useState<string[]>([]);
  const [greedyOrder, setGreedyOrder] = useState<string[]>([]);
  const [diversityPenalty, setDiversityPenalty] = useState(0.3);
  const [compareToChampion, setCompareToChampion] = useState(false);
  const [log, setLog] = useState<{ ts: string; msg: string; ok: boolean }[]>([]);

  useEffect(() => {
    ds.getEnsembles().then((e) => {
      const d = e.data;
      setData(d);
      setSource(e.source);
      setGeneratedAt(e.generatedAt);
      setStrategy(d.activeStrategy);
      setWeights(Object.fromEntries(d.members.map((m) => [m.model, m.weight])));
      setSelectedMembers(d.members.map((m) => m.model));
      setGreedyOrder(d.members.map((m) => m.model));
      setLoading(false);
    });
  }, [ds]);

  if (loading) return <StatusPage state="loading" />;
  if (!data) return <StatusPage state="backend-unavailable" />;

  const meta = PAGE_META["/ensembles"];
  const available = new Set(data.availableStrategies);

  const pushLog = (msg: string, ok: boolean) =>
    setLog((prev) => [{ ts: new Date().toISOString(), msg, ok }, ...prev].slice(0, 6));

  const runAction = async (fn: () => Promise<{ ok: boolean; message: string }>) => {
    const r = await fn();
    pushLog(r.message, r.ok);
  };

  const toggleMember = (model: string) =>
    setSelectedMembers((prev) => (prev.includes(model) ? prev.filter((m) => m !== model) : [...prev, model]));

  const weightSum = selectedMembers.reduce((s, m) => s + (weights[m] ?? 0), 0);
  const weightsOff = Math.abs(weightSum - 1) > 0.02;

  // Prediction correlation heatmap over unique models
  const corrRows = Array.from(new Set(data.predCorrelation.map((d) => d.a)));
  const corrCols = Array.from(new Set(data.predCorrelation.map((d) => d.b)));
  const corrMap: Record<string, Record<string, number>> = {};
  data.predCorrelation.forEach(({ a, b, corr }) => {
    if (!corrMap[a]) corrMap[a] = {};
    corrMap[a][b] = corr;
  });

  const metrics = data.metrics;
  const activeModels = data.members.filter((m) => selectedMembers.includes(m.model));

  return (
    <div style={{ padding: 16, display: "flex", flexDirection: "column", gap: 16 }}>
      <PageHeader
        title={meta.title}
        intro={meta.intro}
        source={source}
        updatedAt={generatedAt}
        actions={
          <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: "var(--accent)", fontWeight: 600 }}>
            {data.currentBlend}
          </span>
        }
      />

      {/* Strategy selector + controls */}
      <Panel title="Blend strategy" actions={
        <div style={{ display: "flex", gap: 6 }}>
          <Btn variant="surface" small onClick={() => runAction(() => ds.buildEnsemble(strategy))}>Build preview</Btn>
          <Btn variant="surface" small onClick={() => runAction(() => ds.saveEnsembleCandidate(strategy))}>Save candidate</Btn>
          <Btn variant="accent" small onClick={() => runAction(() => ds.promoteEnsemble())}>Promote blend</Btn>
          <Btn variant={compareToChampion ? "accent" : "ghost"} small onClick={() => setCompareToChampion((v) => !v)}>
            Compare to champion
          </Btn>
        </div>
      }>
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 14 }}>
          {ALL_STRATEGIES.map((s) => {
            const supported = available.has(s);
            const isActive = strategy === s;
            return (
              <Btn
                key={s}
                variant={isActive ? "accent" : "ghost"}
                small
                disabled={!supported}
                onClick={() => supported && setStrategy(s)}
              >
                {STRATEGY_LABEL[s]}
              </Btn>
            );
          })}
        </div>

        {/* Strategy-specific controls */}
        {strategy === "weighted" && (
          <div>
            <div style={{ fontFamily: "'Raleway', sans-serif", fontSize: 12, color: "var(--body-secondary)", marginBottom: 8 }}>
              Set a weight for each member. Weights should sum to about 1.
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {activeModels.map((m) => (
                <div key={m.model} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: "var(--foreground)", width: 140 }}>{m.model}</span>
                  <input
                    type="number"
                    step={0.05}
                    min={0}
                    max={1}
                    value={weights[m.model] ?? 0}
                    onChange={(e) => setWeights((prev) => ({ ...prev, [m.model]: Number(e.target.value) }))}
                    style={inputStyle}
                  />
                </div>
              ))}
            </div>
            <div style={{
              marginTop: 10, fontFamily: "'JetBrains Mono', monospace", fontSize: 11,
              color: weightsOff ? CHART.amber : CHART.green,
            }}>
              Sum: {weightSum.toFixed(2)} {weightsOff ? "— adjust so weights sum to ~1.00" : "— looks balanced"}
            </div>
          </div>
        )}

        {strategy === "rank_average" && (
          <div>
            <div style={{ fontFamily: "'Raleway', sans-serif", fontSize: 12, color: "var(--body-secondary)", marginBottom: 8 }}>
              Predictions are rank-averaged equally across selected members — no weights needed.
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {activeModels.map((m) => (
                <span key={m.model} style={{
                  fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: "var(--foreground)",
                  border: "1px solid var(--border)", borderRadius: 2, padding: "3px 8px",
                }}>{m.model}</span>
              ))}
            </div>
          </div>
        )}

        {strategy === "greedy" && (
          <div>
            <div style={{ fontFamily: "'Raleway', sans-serif", fontSize: 12, color: "var(--body-secondary)", marginBottom: 8 }}>
              Add models from the pool in the order they should be greedily included.
            </div>
            <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
              <div>
                <div style={{ fontFamily: "'Montserrat', sans-serif", fontSize: 10, color: "var(--faint)", letterSpacing: "0.06em", marginBottom: 6 }}>CANDIDATE POOL</div>
                <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  {data.candidatePool.map((p) => (
                    <div key={p.model} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <Btn
                        small
                        disabled={greedyOrder.includes(p.model)}
                        onClick={() => setGreedyOrder((prev) => [...prev, p.model])}
                      >
                        + Add
                      </Btn>
                      <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: "var(--foreground)" }}>
                        {p.model} <span style={{ color: "var(--metadata)" }}>({fmtNum(p.localScore)})</span>
                      </span>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <div style={{ fontFamily: "'Montserrat', sans-serif", fontSize: 10, color: "var(--faint)", letterSpacing: "0.06em", marginBottom: 6 }}>SELECTED ORDER</div>
                <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  {greedyOrder.length === 0 && <span style={{ fontSize: 11, color: "var(--faint)" }}>None selected</span>}
                  {greedyOrder.map((model, i) => (
                    <div key={model} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: "var(--accent)", width: 20 }}>{i + 1}.</span>
                      <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: "var(--foreground)", width: 140 }}>{model}</span>
                      <Btn small danger onClick={() => setGreedyOrder((prev) => prev.filter((m) => m !== model))}>Remove</Btn>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {strategy === "diversity_aware" && (
          <div>
            <div style={{ fontFamily: "'Raleway', sans-serif", fontSize: 12, color: "var(--body-secondary)", marginBottom: 8 }}>
              Higher penalty pushes the blend toward more independent members. Applied by the backend at build time.
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <input
                type="range"
                min={0}
                max={1}
                step={0.05}
                value={diversityPenalty}
                onChange={(e) => setDiversityPenalty(Number(e.target.value))}
                style={{ width: 240, accentColor: CHART.amber }}
              />
              <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: "var(--accent)" }}>
                penalty = {diversityPenalty.toFixed(2)}
              </span>
            </div>
          </div>
        )}

        {strategy === "neutralised" && (
          available.has("neutralised") ? (
            <div style={{ fontFamily: "'Raleway', sans-serif", fontSize: 12, color: "var(--body-secondary)" }}>
              Predictions are neutralised against feature exposure before blending.
            </div>
          ) : (
            <div style={{ fontFamily: "'Raleway', sans-serif", fontSize: 12, color: CHART.amber }}>
              Not supported by the active scorer.
            </div>
          )
        )}

        {/* Action log */}
        {log.length > 0 && (
          <div style={{ marginTop: 14, borderTop: "1px solid var(--border)", paddingTop: 10, display: "flex", flexDirection: "column", gap: 4 }}>
            {log.map((l, i) => (
              <div key={i} style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10.5, color: l.ok ? "var(--body-secondary)" : CHART.red }}>
                <span style={{ color: "var(--faint)" }}>{fmtClock(l.ts)}</span> {l.msg}
              </div>
            ))}
          </div>
        )}
      </Panel>

      {/* Member / candidate selector */}
      <Panel title="Members — choose which pool models are in the blend">
        <table className="qs-table">
          <thead><tr><th>IN BLEND</th><th>MODEL</th><th>LOCAL</th><th>DIVERSITY</th></tr></thead>
          <tbody>
            {data.candidatePool.map((p) => {
              const member = data.members.find((m) => m.model === p.model);
              const checked = selectedMembers.includes(p.model);
              return (
                <tr key={p.model}>
                  <td>
                    <input type="checkbox" checked={checked} onChange={() => toggleMember(p.model)} style={{ accentColor: CHART.amber, cursor: "pointer" }} />
                  </td>
                  <td style={{ color: "var(--foreground)", fontWeight: 600 }}>{p.model}</td>
                  <td>{fmtNum(member?.localScore ?? p.localScore)}</td>
                  <td>{fmtNum(p.diversity, 2)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </Panel>

      {/* Metrics */}
      <Panel title={compareToChampion ? "Blend metrics vs current champion" : "Blend metrics"}>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
          <MetricTile label="Local uplift vs best" value={fmtNum(metrics.localUpliftVsBest)} accent />
          <MetricTile label="Recent uplift" value={fmtNum(metrics.recentUplift)} />
          <MetricTile label="Worst-fold change" value={fmtNum(metrics.worstFoldChange)} />
          <MetricTile label="Mean pairwise corr" value={fmtNum(metrics.meanPairwiseCorr, 2)} />
          <MetricTile label="Effective models" value={fmtNum(metrics.effectiveModels, 1)} />
          <MetricTile label="Exposure change" value={fmtNum(metrics.exposureChange, 2)} />
          <MetricTile label="Practice uplift" value={fmtNum(metrics.practiceUplift)} />
          <MetricTile label="Live uplift" value={fmtNum(metrics.liveUplift)} />
        </div>
      </Panel>

      {/* Charts */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        <Panel title="Prediction correlation — model × model">
          <Heatmap rows={corrRows} cols={corrCols} data={corrMap} colorLow="#0C1116" colorHigh={CHART.blue} formatValue={(v) => v.toFixed(2)} />
        </Panel>
        <Panel title="Marginal contribution to the blend">
          <ResponsiveContainer width="100%" height={170}>
            <BarChart data={data.marginalContrib}>
              <CartesianGrid stroke="var(--border)" strokeDasharray="2 4" vertical={false} />
              <XAxis dataKey="model" tick={{ fill: "var(--metadata)", fontSize: 9 }} />
              <YAxis tick={{ fill: "var(--metadata)", fontSize: 10 }} width={48} tickFormatter={(v) => v.toFixed(3)} />
              <Tooltip contentStyle={TT} formatter={((v: any) => [Number(v).toFixed(4), "Contribution"]) as any} />
              <Bar dataKey="contribution" fill={CHART_SERIES[0]} name="Contribution" />
            </BarChart>
          </ResponsiveContainer>
        </Panel>
        <Panel title="Score vs diversity">
          <ResponsiveContainer width="100%" height={170}>
            <ScatterChart>
              <CartesianGrid stroke="var(--border)" strokeDasharray="2 4" />
              <XAxis dataKey="diversity" name="Diversity" tick={{ fill: "var(--metadata)", fontSize: 10 }} tickFormatter={(v) => v.toFixed(2)} />
              <YAxis dataKey="score" name="Score" domain={["auto", "auto"]} tick={{ fill: "var(--metadata)", fontSize: 10 }} width={48} tickFormatter={(v) => v.toFixed(2)} />
              <Tooltip contentStyle={TT} content={({ payload }) => {
                if (!payload?.length) return null;
                const d = payload[0]?.payload;
                return <div style={{ ...TT, padding: "8px 10px" }}><div style={{ color: "var(--accent)" }}>{d.model}</div><div>score: {fmtNum(d.score)}</div><div>diversity: {fmtNum(d.diversity, 2)}</div></div>;
              }} />
              <Scatter data={data.scoreDiversityScatter} fill={CHART_SERIES[3]} />
            </ScatterChart>
          </ResponsiveContainer>
        </Panel>
        <Panel title="Fold score by model">
          <ResponsiveContainer width="100%" height={170}>
            <BarChart data={
              (() => {
                const byFold: Record<string, Record<string, number>> = {};
                data.foldScore.forEach(({ fold, model, score }) => {
                  if (!byFold[fold]) byFold[fold] = {};
                  byFold[fold][model] = score;
                });
                return Object.entries(byFold).map(([fold, scores]) => ({ fold, ...scores }));
              })()
            }>
              <CartesianGrid stroke="var(--border)" strokeDasharray="2 4" vertical={false} />
              <XAxis dataKey="fold" tick={{ fill: "var(--metadata)", fontSize: 10 }} />
              <YAxis domain={["auto", "auto"]} tick={{ fill: "var(--metadata)", fontSize: 10 }} width={48} tickFormatter={(v) => v.toFixed(2)} />
              <Tooltip contentStyle={TT} />
              {Array.from(new Set(data.foldScore.map((d) => d.model))).map((model, i) => (
                <Bar key={model} dataKey={model} name={model} fill={CHART_SERIES[i % CHART_SERIES.length]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </Panel>
      </div>
    </div>
  );
}
