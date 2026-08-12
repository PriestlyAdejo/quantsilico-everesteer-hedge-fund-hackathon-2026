import { useEffect, useMemo, useState } from "react";
import { ScatterChart, Scatter, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from "recharts";
import { useDataSource } from "../data/useDataSource";
import type { ExperimentRow } from "../data/types";
import { CHART, CHART_SERIES, STAGE_COLOR } from "../data/chartTokens";
import { PAGE_META, humanizeDecision, TONE_COLOR, fmtNum, fmtDuration, fmtVal } from "../data/humanize";
import PageHeader from "../components/PageHeader";
import Panel, { Btn } from "../components/Panel";
import Drawer from "../components/Drawer";
import StatusPage from "../components/StatusPage";

const TT = { background: "var(--elevated)", border: "1px solid var(--border)", borderRadius: 2, fontSize: 11, fontFamily: "'JetBrains Mono', monospace" };

// Sortable numeric columns.
type SortKey = "localScore" | "recentScore" | "stability" | "runtimeSeconds" | "diversity" | "practiceScore" | "liveScore";

const AXIS = { fill: "var(--metadata)", fontSize: 10 } as const;

export default function Experiments() {
  const ds = useDataSource();
  const [rows, setRows] = useState<ExperimentRow[]>([]);
  const [source, setSource] = useState<string>();
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [sortKey, setSortKey] = useState<SortKey>("localScore");
  const [sortDir, setSortDir] = useState<1 | -1>(-1);
  const [selected, setSelected] = useState<ExperimentRow | null>(null);
  const [query, setQuery] = useState("");
  const [stageFilter, setStageFilter] = useState("ALL");

  useEffect(() => {
    ds.getExperiments().then((e) => {
      setRows(e.data);
      setSource(e.source);
      setUpdatedAt(e.generatedAt);
      setLoading(false);
    });
  }, [ds]);

  const stages = useMemo(() => ["ALL", ...Array.from(new Set(rows.map((r) => r.raceStage)))], [rows]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return rows
      .filter((r) => stageFilter === "ALL" || r.raceStage === stageFilter)
      .filter((r) => q === "" || r.run.toLowerCase().includes(q))
      .sort((a, b) => {
        const av = a[sortKey], bv = b[sortKey];
        if (av == null) return 1;
        if (bv == null) return -1;
        return av < bv ? -sortDir : av > bv ? sortDir : 0;
      });
  }, [rows, query, stageFilter, sortKey, sortDir]);

  // Aggregate mean local score by operator for the bar chart.
  const byOperator = useMemo(() => {
    const acc: Record<string, { sum: number; n: number }> = {};
    rows.forEach((r) => {
      if (r.localScore == null) return;
      (acc[r.operator] ??= { sum: 0, n: 0 });
      acc[r.operator].sum += r.localScore;
      acc[r.operator].n += 1;
    });
    return Object.entries(acc).map(([operator, { sum, n }]) => ({ operator, meanScore: sum / n }));
  }, [rows]);

  if (loading) return <StatusPage state="loading" />;

  const setSort = (key: SortKey) => {
    if (sortKey === key) setSortDir((d) => (d === 1 ? -1 : 1));
    else { setSortKey(key); setSortDir(-1); }
  };

  const cols: { key: SortKey; label: string }[] = [
    { key: "localScore", label: "Local" },
    { key: "recentScore", label: "Recent" },
    { key: "stability", label: "Stability" },
    { key: "runtimeSeconds", label: "Runtime" },
    { key: "diversity", label: "Diversity" },
    { key: "practiceScore", label: "Practice" },
    { key: "liveScore", label: "Live" },
  ];

  return (
    <div style={{ padding: 16, display: "flex", flexDirection: "column", gap: 14 }}>
      <PageHeader
        title={PAGE_META["/experiments"].title}
        intro={PAGE_META["/experiments"].intro}
        source={source}
        updatedAt={updatedAt}
      />

      {/* Filter bar */}
      <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search run…"
          style={{
            background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius)",
            padding: "5px 10px", fontFamily: "'JetBrains Mono', monospace", fontSize: 12,
            color: "var(--foreground)", minWidth: 200,
          }}
        />
        <div style={{ display: "flex", gap: 4, marginLeft: "auto", flexWrap: "wrap" }}>
          {stages.map((s) => (
            <Btn key={s} variant={stageFilter === s ? "accent" : "ghost"} small onClick={() => setStageFilter(s)}>{s}</Btn>
          ))}
        </div>
        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: "var(--metadata)" }}>
          {filtered.length} / {rows.length} runs
        </span>
      </div>

      {/* Table — render all demo rows; virtualization is future work for very large tables. */}
      <Panel noPad>
        <div style={{ overflow: "auto", maxHeight: 460 }}>
          <table className="qs-table">
            <thead>
              <tr>
                <th className="sticky-col">Run</th>
                <th>Family</th>
                <th>Change</th>
                <th>Stage</th>
                {cols.map((c) => (
                  <th key={c.key} className="sortable" onClick={() => setSort(c.key)}>
                    {c.label}{sortKey === c.key ? (sortDir === 1 ? " ↑" : " ↓") : ""}
                  </th>
                ))}
                <th>Decision</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => {
                const dec = humanizeDecision(r.raceDecision);
                return (
                  <tr
                    key={r.run}
                    className={selected?.run === r.run ? "selected" : undefined}
                    onClick={() => setSelected(r)}
                    style={{ cursor: "pointer" }}
                  >
                    <td className="sticky-col" style={{ color: "var(--foreground)", fontWeight: 600 }}>{r.run}</td>
                    <td>{fmtVal(r.family)}</td>
                    <td>{fmtVal(r.operator)}</td>
                    <td style={{ color: STAGE_COLOR[r.raceStage] ?? "var(--metadata)" }}>{r.raceStage}</td>
                    <td>{fmtNum(r.localScore)}</td>
                    <td>{fmtNum(r.recentScore)}</td>
                    <td>{fmtNum(r.stability, 2)}</td>
                    <td>{fmtDuration(r.runtimeSeconds)}</td>
                    <td>{fmtNum(r.diversity, 2)}</td>
                    <td>{fmtNum(r.practiceScore)}</td>
                    <td>{fmtNum(r.liveScore)}</td>
                    <td style={{ color: TONE_COLOR[dec.tone], fontSize: 11 }}>{dec.label}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Panel>

      {/* Charts */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        <Panel title="Score vs runtime">
          <ResponsiveContainer width="100%" height={200}>
            <ScatterChart margin={{ top: 8, right: 12, bottom: 8, left: 0 }}>
              <XAxis
                type="number"
                dataKey="runtimeSeconds"
                name="Runtime"
                tick={AXIS}
                tickFormatter={fmtDuration}
              />
              <YAxis type="number" dataKey="localScore" name="Local score" tick={AXIS} domain={["auto", "auto"]} tickFormatter={(v) => fmtNum(v, 3)} />
              <Tooltip
                contentStyle={TT}
                formatter={(v, n) => (n === "Runtime" ? fmtDuration(Number(v)) : fmtNum(Number(v)))}
              />
              <Scatter data={filtered} fill={CHART_SERIES[0]} />
            </ScatterChart>
          </ResponsiveContainer>
        </Panel>
        <Panel title="Mean local score by change (operator)">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={byOperator} margin={{ top: 8, right: 12, bottom: 8, left: 0 }}>
              <XAxis dataKey="operator" tick={AXIS} />
              <YAxis tick={AXIS} domain={["auto", "auto"]} tickFormatter={(v) => fmtNum(v, 3)} />
              <Tooltip contentStyle={TT} formatter={(v) => fmtNum(Number(v))} />
              <Bar dataKey="meanScore" name="Mean local score">
                {byOperator.map((_, i) => (
                  <Cell key={i} fill={CHART_SERIES[i % CHART_SERIES.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Panel>
      </div>

      {/* Detail drawer — raw enum lives here */}
      <Drawer
        open={!!selected}
        title={selected?.run ?? ""}
        subtitle={selected ? `${selected.family} · ${selected.operator} · ${selected.raceStage}` : undefined}
        onClose={() => setSelected(null)}
        rawCode={selected?.raceDecision}
      >
        {selected && (
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div>
              <div style={{ color: TONE_COLOR[humanizeDecision(selected.raceDecision).tone], fontFamily: "'JetBrains Mono', monospace", fontSize: 12, fontWeight: 600 }}>
                {humanizeDecision(selected.raceDecision).label}
              </div>
            </div>

            <Field label="Hypothesis" value={selected.hypothesis} />

            <Section title="Lineage">
              <Field label="Parent" value={fmtVal(selected.parent)} mono />
              <Field label="Children" value={selected.children.length ? selected.children.join(", ") : "—"} mono />
            </Section>

            <Section title="Resolved config">
              <Field label="Family" value={fmtVal(selected.family)} mono />
              <Field label="Operator / change" value={fmtVal(selected.operator)} mono />
            </Section>

            <Section title="Metric components">
              <Grid items={[
                ["Local", fmtNum(selected.localScore)],
                ["Recent", fmtNum(selected.recentScore)],
                ["Lower quantile", fmtNum(selected.lowerQuantile)],
                ["Stability", fmtNum(selected.stability, 2)],
                ["Diversity", fmtNum(selected.diversity, 2)],
                ["Practice", fmtNum(selected.practiceScore)],
                ["Live", fmtNum(selected.liveScore)],
                ["Runtime", fmtDuration(selected.runtimeSeconds)],
              ]} />
            </Section>

            <Section title="Artefacts">
              <Field label="OOF path" value={fmtVal(selected.oofPath)} mono />
              <Field label="Artefact" value={fmtVal(selected.artefact)} mono />
            </Section>

            <Section title="Logs">
              <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: "var(--body-secondary)", display: "flex", flexDirection: "column", gap: 3 }}>
                {selected.logs.map((l, i) => <div key={i}>· {l}</div>)}
              </div>
            </Section>
          </div>
        )}
      </Drawer>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="qs-section-label" style={{ marginBottom: 8 }}>{title}</div>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>{children}</div>
    </div>
  );
}

function Field({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <div style={{ fontFamily: "'Montserrat', sans-serif", fontSize: 9, color: "var(--metadata)", letterSpacing: "0.06em" }}>{label}</div>
      <div style={{ fontFamily: mono ? "'JetBrains Mono', monospace" : "'Raleway', sans-serif", fontSize: 12, color: "var(--body-primary)", wordBreak: "break-all" }}>{value}</div>
    </div>
  );
}

function Grid({ items }: { items: [string, string][] }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
      {items.map(([k, v]) => (
        <div key={k}>
          <div style={{ fontFamily: "'Montserrat', sans-serif", fontSize: 9, color: "var(--metadata)", letterSpacing: "0.06em" }}>{k}</div>
          <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: "var(--body-primary)" }}>{v}</div>
        </div>
      ))}
    </div>
  );
}
