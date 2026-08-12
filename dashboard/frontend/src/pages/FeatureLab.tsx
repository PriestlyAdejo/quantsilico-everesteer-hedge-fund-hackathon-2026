import { useEffect, useMemo, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { useDataSource } from "../data/useDataSource";
import type { FeatureLabData } from "../data/types";
import { CHART_SERIES } from "../data/chartTokens";
import { PAGE_META, fmtNum, fmtInt } from "../data/humanize";
import PageHeader from "../components/PageHeader";
import Panel from "../components/Panel";
import Heatmap from "../components/Heatmap";
import Drawer from "../components/Drawer";
import { MetricTile } from "../components/Panel";
import StatusPage from "../components/StatusPage";

const TT = { background: "var(--elevated)", border: "1px solid var(--border)", borderRadius: 2, fontSize: 11, fontFamily: "'JetBrains Mono', monospace" };
const AXIS = { fill: "var(--metadata)", fontSize: 10 } as const;

type Feature = FeatureLabData["features"][number];
type SortKey = "missingness" | "cardinality" | "importance" | "importanceStd" | "exposure" | "selectionFreq" | "drift";

export default function FeatureLab() {
  const ds = useDataSource();
  const [data, setData] = useState<FeatureLabData | null>(null);
  const [source, setSource] = useState<string>();
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("importance");
  const [sortDir, setSortDir] = useState<1 | -1>(-1);
  const [selected, setSelected] = useState<Feature | null>(null);

  useEffect(() => {
    ds.getFeatureLab().then((e) => {
      setData(e.data);
      setSource(e.source);
      setUpdatedAt(e.generatedAt);
      setLoading(false);
    });
  }, [ds]);

  const filtered = useMemo(() => {
    if (!data) return [];
    const q = query.trim().toLowerCase();
    return data.features
      .filter((f) => q === "" || f.id.toLowerCase().includes(q))
      .sort((a, b) => {
        const av = a[sortKey], bv = b[sortKey];
        return av < bv ? -sortDir : av > bv ? sortDir : 0;
      });
  }, [data, query, sortKey, sortDir]);

  // Top correlated neighbours for the selected feature id.
  const neighbours = useMemo(() => {
    if (!data || !selected) return [];
    return data.correlationMatrix
      .filter((c) => (c.a === selected.id || c.b === selected.id) && c.a !== c.b)
      .map((c) => ({ id: c.a === selected.id ? c.b : c.a, corr: c.corr }))
      .sort((x, y) => Math.abs(y.corr) - Math.abs(x.corr))
      .slice(0, 6);
  }, [data, selected]);

  if (loading) return <StatusPage state="loading" />;
  if (!data) return <StatusPage state="backend-unavailable" />;

  const setSort = (key: SortKey) => {
    if (sortKey === key) setSortDir((d) => (d === 1 ? -1 : 1));
    else { setSortKey(key); setSortDir(-1); }
  };

  const corrRows = Array.from(new Set(data.correlationMatrix.map((d) => d.a)));
  const corrCols = Array.from(new Set(data.correlationMatrix.map((d) => d.b)));
  const corrMap: Record<string, Record<string, number>> = {};
  data.correlationMatrix.forEach(({ a, b, corr }) => {
    (corrMap[a] ??= {})[b] = corr;
  });

  const cols: { key: SortKey; label: string }[] = [
    { key: "missingness", label: "Missing%" },
    { key: "cardinality", label: "Cardinality" },
    { key: "importance", label: "Importance" },
    { key: "importanceStd", label: "Imp std" },
    { key: "exposure", label: "Exposure" },
    { key: "selectionFreq", label: "Sel freq" },
    { key: "drift", label: "Drift" },
  ];

  const s = data.summary;

  return (
    <div style={{ padding: 16, display: "flex", flexDirection: "column", gap: 14 }}>
      <PageHeader
        title={PAGE_META["/features"].title}
        intro={PAGE_META["/features"].intro}
        source={source}
        updatedAt={updatedAt}
      />

      {/* Summary tiles */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
        <MetricTile label="Features" value={fmtInt(s.featureCount)} />
        <MetricTile label="High missingness" value={fmtInt(s.highMissingness)} warn={!!s.highMissingness} />
        <MetricTile label="Unstable" value={fmtInt(s.unstable)} warn={!!s.unstable} />
        <MetricTile label="High exposure" value={fmtInt(s.highExposure)} warn={!!s.highExposure} />
        <MetricTile label="Selected by frontier" value={fmtInt(s.selectedByFrontier)} accent />
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search feature id…"
          style={{
            background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius)",
            padding: "5px 10px", fontFamily: "'JetBrains Mono', monospace", fontSize: 12,
            color: "var(--foreground)", minWidth: 200,
          }}
        />
        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: "var(--metadata)", marginLeft: "auto" }}>
          Feature ids are anonymous — they do not correspond to real economic signals
        </span>
      </div>

      {/* Table */}
      <Panel noPad>
        <div style={{ overflow: "auto", maxHeight: 420 }}>
          <table className="qs-table">
            <thead>
              <tr>
                <th className="sticky-col">Feature</th>
                {cols.map((c) => (
                  <th key={c.key} className="sortable" onClick={() => setSort(c.key)}>
                    {c.label}{sortKey === c.key ? (sortDir === 1 ? " ↑" : " ↓") : ""}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((f) => (
                <tr
                  key={f.id}
                  className={selected?.id === f.id ? "selected" : undefined}
                  onClick={() => setSelected(f)}
                  style={{ cursor: "pointer" }}
                >
                  <td className="sticky-col" style={{ color: "var(--foreground)", fontWeight: 600 }}>{f.id}</td>
                  <td style={{ color: f.missingness > 5 ? "#FFB000" : "var(--body-primary)" }}>{fmtNum(f.missingness, 1)}%</td>
                  <td>{fmtInt(f.cardinality)}</td>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                      <div style={{ width: 50, height: 4, background: "var(--elevated)", borderRadius: 2 }}>
                        <div style={{ width: `${Math.min(100, f.importance * 100)}%`, height: "100%", background: CHART_SERIES[0], borderRadius: 2 }} />
                      </div>
                      {fmtNum(f.importance, 2)}
                    </div>
                  </td>
                  <td>±{fmtNum(f.importanceStd, 2)}</td>
                  <td>{fmtInt(f.exposure)}</td>
                  <td>{fmtInt(f.selectionFreq)}%</td>
                  <td style={{ color: f.drift > 0.2 ? "#FFB000" : "var(--body-primary)" }}>{fmtNum(f.drift, 2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        <Panel title="Feature importance">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={data.importanceSeries} layout="vertical" margin={{ top: 8, right: 12, bottom: 8, left: 0 }}>
              <XAxis type="number" tick={AXIS} />
              <YAxis type="category" dataKey="feature" tick={{ fill: "var(--metadata)", fontSize: 9 }} width={90} />
              <Tooltip contentStyle={TT} formatter={(v) => fmtNum(Number(v), 2)} />
              <Bar dataKey="importance" name="Importance">
                {data.importanceSeries.map((_, i) => (
                  <Cell key={i} fill={CHART_SERIES[i % CHART_SERIES.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Panel>
        <Panel title="Correlation matrix">
          <Heatmap
            rows={corrRows}
            cols={corrCols}
            data={corrMap}
            formatValue={(v) => v.toFixed(2)}
          />
        </Panel>
      </div>

      {/* Feature detail drawer */}
      <Drawer
        open={!!selected}
        title={selected?.id ?? ""}
        subtitle="Anonymous feature diagnostics"
        onClose={() => setSelected(null)}
      >
        {selected && (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              {([
                ["Missingness", `${fmtNum(selected.missingness, 1)}%`],
                ["Cardinality", fmtInt(selected.cardinality)],
                ["Importance", fmtNum(selected.importance, 2)],
                ["Importance std", `±${fmtNum(selected.importanceStd, 2)}`],
                ["Redundancy", fmtNum(selected.redundancy, 2)],
                ["Exposure", fmtInt(selected.exposure)],
                ["Selection freq", `${fmtInt(selected.selectionFreq)}%`],
                ["Drift", fmtNum(selected.drift, 2)],
              ] as [string, string][]).map(([k, v]) => (
                <div key={k}>
                  <div style={{ fontFamily: "'Montserrat', sans-serif", fontSize: 9, color: "var(--metadata)", letterSpacing: "0.06em" }}>{k}</div>
                  <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: "var(--body-primary)" }}>{v}</div>
                </div>
              ))}
            </div>

            <div>
              <div className="qs-section-label" style={{ marginBottom: 8 }}>Correlation neighbourhood</div>
              {neighbours.length === 0 ? (
                <div style={{ fontFamily: "'Raleway', sans-serif", fontSize: 12, color: "var(--body-secondary)" }}>
                  No correlation data available for this feature.
                </div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  {neighbours.map((n) => (
                    <div key={n.id} style={{ display: "flex", justifyContent: "space-between", fontFamily: "'JetBrains Mono', monospace", fontSize: 12 }}>
                      <span style={{ color: "var(--body-primary)" }}>{n.id}</span>
                      <span style={{ color: Math.abs(n.corr) > 0.7 ? "#FFB000" : "var(--body-secondary)" }}>{fmtNum(n.corr, 2)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </Drawer>
    </div>
  );
}
