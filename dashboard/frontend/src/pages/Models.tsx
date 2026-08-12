import { useEffect, useMemo, useState } from "react";
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, Cell,
} from "recharts";
import { useDataSource } from "../data/useDataSource";
import type { ModelRow } from "../data/types";
import { CHART_SERIES } from "../data/chartTokens";
import { PAGE_META, fmtNum, fmtInt, fmtVal, fmtDuration } from "../data/humanize";
import PageHeader from "../components/PageHeader";
import Panel, { Btn, MetricTile } from "../components/Panel";
import Tip from "../components/Tip";
import StatusPage from "../components/StatusPage";

const TT = { background: "var(--elevated)", border: "1px solid var(--border)", borderRadius: 2, fontSize: 11, fontFamily: "'JetBrains Mono', monospace" };
const AXIS = { fill: "var(--metadata)", fontSize: 10 } as const;

type SortKey = "localScore" | "recentScore" | "practiceScore" | "liveScore" | "icir" | "worstFold" | "inferenceP50Ms" | "inferenceP95Ms" | "modelSizeMb";

const MAX_SELECT = 5;

export default function Models() {
  const ds = useDataSource();
  const [rows, setRows] = useState<ModelRow[]>([]);
  const [source, setSource] = useState<string>();
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("localScore");
  const [sortDir, setSortDir] = useState<1 | -1>(-1);
  const [selected, setSelected] = useState<string[]>([]);

  useEffect(() => {
    ds.getModels().then((e) => {
      setRows(e.data);
      setSource(e.source);
      setUpdatedAt(e.generatedAt);
      setSelected(e.data.length ? [e.data[0].privateAlias] : []);
      setLoading(false);
    });
  }, [ds]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return rows
      .filter((r) => q === "" || r.privateAlias.toLowerCase().includes(q))
      .sort((a, b) => {
        const av = a[sortKey], bv = b[sortKey];
        if (av == null) return 1;
        if (bv == null) return -1;
        return av < bv ? -sortDir : av > bv ? sortDir : 0;
      });
  }, [rows, query, sortKey, sortDir]);

  const selectedRows = useMemo(
    () => selected.map((a) => rows.find((r) => r.privateAlias === a)).filter((r): r is ModelRow => !!r),
    [selected, rows]
  );

  if (loading) return <StatusPage state="loading" />;

  const setSort = (key: SortKey) => {
    if (sortKey === key) setSortDir((d) => (d === 1 ? -1 : 1));
    else { setSortKey(key); setSortDir(-1); }
  };

  const toggle = (alias: string, additive: boolean) => {
    setSelected((prev) => {
      if (additive) {
        if (prev.includes(alias)) return prev.filter((a) => a !== alias);
        if (prev.length >= MAX_SELECT) return prev;
        return [...prev, alias];
      }
      return [alias];
    });
  };

  const cols: { key: SortKey; label: string; term?: string }[] = [
    { key: "localScore", label: "Local" },
    { key: "recentScore", label: "Recent" },
    { key: "practiceScore", label: "Practice" },
    { key: "liveScore", label: "Live" },
    { key: "icir", label: "ICIR", term: "ICIR" },
    { key: "worstFold", label: "Worst fold", term: "worst fold" },
    { key: "inferenceP50Ms", label: "p50" },
    { key: "inferenceP95Ms", label: "p95" },
    { key: "modelSizeMb", label: "Size (MB)" },
  ];

  return (
    <div style={{ padding: 16, display: "flex", flexDirection: "column", gap: 14 }}>
      <PageHeader
        title={PAGE_META["/models"].title}
        intro={PAGE_META["/models"].intro}
        source={source}
        updatedAt={updatedAt}
      />

      <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search model…"
          style={{
            background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius)",
            padding: "5px 10px", fontFamily: "'JetBrains Mono', monospace", fontSize: 12,
            color: "var(--foreground)", minWidth: 200,
          }}
        />
        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: "var(--metadata)" }}>
          Click to select · Ctrl/Cmd-click to compare up to {MAX_SELECT}
        </span>
      </div>

      {/* Registry table */}
      <Panel noPad>
        <div style={{ overflow: "auto", maxHeight: 360 }}>
          <table className="qs-table">
            <thead>
              <tr>
                <th className="sticky-col">Model</th>
                <th>Family</th>
                <th>Lifecycle</th>
                {cols.map((c) => (
                  <th key={c.key} className="sortable" onClick={() => setSort(c.key)}>
                    {c.term ? <Tip term={c.term}>{c.label}</Tip> : c.label}
                    {sortKey === c.key ? (sortDir === 1 ? " ↑" : " ↓") : ""}
                  </th>
                ))}
                <th>Pickle</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => (
                <tr
                  key={r.privateAlias}
                  className={selected.includes(r.privateAlias) ? "selected" : undefined}
                  onClick={(e) => toggle(r.privateAlias, e.metaKey || e.ctrlKey)}
                  style={{ cursor: "pointer" }}
                >
                  <td className="sticky-col" style={{ color: "var(--foreground)", fontWeight: 600 }}>{r.privateAlias}</td>
                  <td>{fmtVal(r.family)}</td>
                  <td>
                    <span style={{ color: r.lifecycle === "active" ? CHART_SERIES[2] : r.lifecycle === "frozen" ? "#FFB000" : "var(--faint)" }}>
                      {r.lifecycle.toUpperCase()}
                    </span>
                  </td>
                  <td>{fmtNum(r.localScore)}</td>
                  <td>{fmtNum(r.recentScore)}</td>
                  <td>{fmtNum(r.practiceScore)}</td>
                  <td>{fmtNum(r.liveScore)}</td>
                  <td>{fmtNum(r.icir, 2)}</td>
                  <td>{fmtNum(r.worstFold)}</td>
                  <td>{fmtDuration(r.inferenceP50Ms != null ? r.inferenceP50Ms / 1000 : null)}</td>
                  <td>{fmtDuration(r.inferenceP95Ms != null ? r.inferenceP95Ms / 1000 : null)}</td>
                  <td>{fmtNum(r.modelSizeMb, 0)}</td>
                  <td>
                    <span style={{ color: r.pickleStatus === "verified" ? CHART_SERIES[2] : r.pickleStatus === "stale" ? "#FFB000" : "#EF4444" }}>
                      {r.pickleStatus.toUpperCase()}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      {/* Selected-model inspection region */}
      {selectedRows.length === 0 ? (
        <Panel title="Selected model">
          <div style={{ fontFamily: "'Raleway', sans-serif", fontSize: 12.5, color: "var(--body-secondary)" }}>
            Select a model in the registry to inspect fold performance, feature importance, score components and latency.
          </div>
        </Panel>
      ) : (
        <Inspection rows={selectedRows} onClear={() => setSelected([])} />
      )}
    </div>
  );
}

function Inspection({ rows, onClear }: { rows: ModelRow[]; onClear: () => void }) {
  const compare = rows.length > 1;

  // Overlay fold performance across selected models: one row per fold, one key per model.
  const foldData = useMemo(() => {
    const folds = Array.from(new Set(rows.flatMap((r) => r.foldPerformance.map((f) => f.fold))));
    return folds.map((fold) => {
      const point: Record<string, number | string | null> = { fold };
      rows.forEach((r) => {
        point[r.privateAlias] = r.foldPerformance.find((f) => f.fold === fold)?.score ?? null;
      });
      return point;
    });
  }, [rows]);

  const primary = rows[0];
  const topImportance = useMemo(
    () => [...primary.featureImportance].sort((a, b) => b.importance - a.importance).slice(0, 10),
    [primary]
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <Panel
        title={compare ? `Compare — ${rows.length} models` : `Selected model — ${primary.privateAlias}`}
        actions={<Btn small onClick={onClear}>Clear</Btn>}
      >
        <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
          <MetricTile label="Local score" value={fmtNum(primary.localScore)} accent />
          <MetricTile label="Recent score" value={fmtNum(primary.recentScore)} />
          <MetricTile label="Practice" value={fmtNum(primary.practiceScore)} />
          <MetricTile label="Live" value={fmtNum(primary.liveScore)} />
          <MetricTile label="ICIR" value={fmtNum(primary.icir, 2)} labelNode={<Tip term="ICIR">ICIR</Tip>} />
          <MetricTile label="Worst fold" value={fmtNum(primary.worstFold)} labelNode={<Tip term="worst fold">Worst fold</Tip>} />
          <MetricTile label="Corr to champion" value={fmtNum(primary.corrToChampion, 2)} />
          <MetricTile label="Inference p50 / p95" value={`${fmtInt(primary.inferenceP50Ms)} / ${fmtInt(primary.inferenceP95Ms)} ms`} />
          <MetricTile label="Model size" value={`${fmtNum(primary.modelSizeMb, 0)} MB`} />
          <MetricTile label="Exposure" value={fmtNum(primary.exposure, 2)} />
        </div>
        {!compare && (
          <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 4, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, color: "var(--faint)" }}>
            <div>data hash: {fmtVal(primary.dataHash)}</div>
            <div>pickle hash: {fmtVal(primary.pickleHash)}</div>
            <div>parent: {fmtVal(primary.parent)} · params: {fmtVal(primary.params)}</div>
          </div>
        )}
      </Panel>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        <Panel title={compare ? "Fold performance (overlay)" : "Fold performance"}>
          <ResponsiveContainer width="100%" height={220}>
            {compare ? (
              <LineChart data={foldData} margin={{ top: 8, right: 12, bottom: 8, left: 0 }}>
                <XAxis dataKey="fold" tick={AXIS} />
                <YAxis tick={AXIS} domain={["auto", "auto"]} tickFormatter={(v) => fmtNum(v, 3)} />
                <Tooltip contentStyle={TT} formatter={(v) => fmtNum(Number(v))} />
                <Legend wrapperStyle={{ fontSize: 10, fontFamily: "'JetBrains Mono', monospace" }} />
                {rows.map((r, i) => (
                  <Line key={r.privateAlias} type="monotone" dataKey={r.privateAlias} stroke={CHART_SERIES[i % CHART_SERIES.length]} dot={false} strokeWidth={2} />
                ))}
              </LineChart>
            ) : (
              <BarChart data={foldData} margin={{ top: 8, right: 12, bottom: 8, left: 0 }}>
                <XAxis dataKey="fold" tick={AXIS} />
                <YAxis tick={AXIS} domain={["auto", "auto"]} tickFormatter={(v) => fmtNum(v, 3)} />
                <Tooltip contentStyle={TT} formatter={(v) => fmtNum(Number(v))} />
                <Bar dataKey={primary.privateAlias} fill={CHART_SERIES[0]} />
              </BarChart>
            )}
          </ResponsiveContainer>
        </Panel>

        <Panel title={`Feature importance — top 10 (${primary.privateAlias})`}>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={topImportance} layout="vertical" margin={{ top: 8, right: 12, bottom: 8, left: 0 }}>
              <XAxis type="number" tick={AXIS} />
              <YAxis type="category" dataKey="feature" tick={{ fill: "var(--metadata)", fontSize: 9 }} width={90} />
              <Tooltip contentStyle={TT} formatter={(v) => fmtNum(Number(v), 2)} />
              <Bar dataKey="importance">
                {topImportance.map((_, i) => (
                  <Cell key={i} fill={CHART_SERIES[i % CHART_SERIES.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Panel>
      </div>
    </div>
  );
}
