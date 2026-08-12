import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { useDataSource } from "../data/useDataSource";
import type { DataLabData, DataSetCard } from "../data/types";
import { CHART, CHART_SERIES } from "../data/chartTokens";
import { PAGE_META, fmtInt, fmtNum, fmtVal, fmtClock } from "../data/humanize";
import PageHeader from "../components/PageHeader";
import Panel from "../components/Panel";
import Tip from "../components/Tip";
import StatusPage from "../components/StatusPage";

const TT = { background: "var(--elevated)", border: "1px solid var(--border)", borderRadius: 2, fontSize: 11, fontFamily: "'JetBrains Mono', monospace" };
const AXIS = { fill: "var(--metadata)", fontSize: 10, fontFamily: "'JetBrains Mono', monospace" };

function statusColor(s: DataSetCard["integrityStatus"]): string {
  return s === "fail" ? CHART.red : s === "warn" ? CHART.amber : CHART.green;
}

function Field({ label, value, node }: { label: React.ReactNode; value?: React.ReactNode; node?: React.ReactNode }) {
  return (
    <div style={{ display: "flex", gap: 6 }}>
      <span style={{ color: "var(--metadata)", fontSize: 9.5, fontFamily: "'Montserrat', sans-serif", letterSpacing: "0.05em", width: 74, flexShrink: 0, textTransform: "uppercase" }}>{label}</span>
      <span style={{ color: "var(--body-primary)" }}>{node ?? value}</span>
    </div>
  );
}

function DataCard({ d }: { d: DataSetCard }) {
  const border = d.integrityStatus === "fail" ? CHART.red : d.integrityStatus === "warn" ? CHART.amber : "var(--border)";
  return (
    <div style={{ background: "var(--surface)", border: `1px solid ${border}`, borderRadius: "var(--radius)", padding: "12px 14px" }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginBottom: 8 }}>
        <span style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 700, fontSize: 12, color: "var(--foreground)" }}>{d.label}</span>
        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, color: "var(--faint)" }}>{d.split}</span>
        <span style={{ marginLeft: "auto", color: statusColor(d.integrityStatus), fontSize: 10, fontWeight: 700, fontFamily: "'JetBrains Mono', monospace" }}>
          {d.integrityStatus.toUpperCase()}
        </span>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "4px 12px", fontFamily: "'JetBrains Mono', monospace", fontSize: 11 }}>
        <Field label="Fingerprint" value={fmtVal(d.hash)} />
        <Field label="Rows" value={fmtInt(d.rows)} />
        <Field label="Cols" value={fmtInt(d.cols)} />
        <Field label="Features" value={fmtInt(d.features)} />
        <Field label={<Tip term="exped">expeds</Tip>} value={fmtInt(d.expeds)} />
        <Field label="Targets" value={fmtInt(d.targets)} />
        <Field label="Target" node={
          <span style={{ color: d.targetAvailable ? CHART.green : "var(--faint)" }}>
            {d.targetAvailable ? "Available" : "Not available"}
          </span>
        } />
        <Field label="Duplicates" value={fmtInt(d.duplicates)} />
        <Field label="Missingness" value={d.missingnessPct == null ? "—" : `${fmtNum(d.missingnessPct, 1)}%`} />
        <Field label="Memory" value={d.memoryMb == null ? "—" : `${fmtNum(d.memoryMb, 0)} MB`} />
        <Field label="Updated" value={fmtClock(d.updatedAt)} />
      </div>
      {d.integrityMessages.length > 0 && (
        <div style={{ marginTop: 8, display: "flex", flexDirection: "column", gap: 2 }}>
          {d.integrityMessages.map((m, i) => (
            <div key={i} style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, color: m.level === "error" ? CHART.red : CHART.amber }}>
              ⚠ {m.text}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function DriftStat({ label, value, help }: { label: string; value: React.ReactNode; help?: string }) {
  return (
    <div style={{ background: "var(--elevated)", border: "1px solid var(--border)", borderRadius: "var(--radius)", padding: "9px 12px", flex: "1 1 150px", minWidth: 150 }}>
      <div style={{ fontFamily: "'Montserrat', sans-serif", fontSize: 10.5, color: "var(--metadata)", letterSpacing: "0.03em", marginBottom: 5 }}>{label}</div>
      <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 15, fontWeight: 600, color: "var(--foreground)" }}>{value}</div>
      {help && <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, color: "var(--faint)", marginTop: 4 }}>{help}</div>}
    </div>
  );
}

export default function DataLab() {
  const ds = useDataSource();
  const [data, setData] = useState<DataLabData | null>(null);
  const [env, setEnv] = useState<{ source: string; generatedAt: string } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    ds.getDataLab().then((e) => {
      setData(e.data);
      setEnv({ source: e.source, generatedAt: e.generatedAt });
      setLoading(false);
    });
  }, [ds]);

  if (loading) return <StatusPage state="loading" />;
  if (!data) return <StatusPage state="backend-unavailable" />;

  const drift = data.drift;

  return (
    <div style={{ padding: 16, display: "flex", flexDirection: "column", gap: 14 }}>
      <PageHeader
        title={PAGE_META["/data"].title}
        intro={PAGE_META["/data"].intro}
        source={env?.source}
        updatedAt={env?.generatedAt}
      />

      {/* Dataset cards */}
      <div style={{ display: "grid", gridTemplateColumns: `repeat(${Math.min(data.datasets.length, 3)}, 1fr)`, gap: 14 }}>
        {data.datasets.map((d) => <DataCard key={d.split} d={d} />)}
      </div>

      {/* Drift & alignment */}
      <Panel title="Drift & alignment — train vs live">
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <DriftStat label="Schema drift" value={drift.schemaDrift == null ? "—" : `${fmtInt(drift.schemaDrift)} fields`} help="fields changed type/shape" />
          <DriftStat label="Missingness drift" value={drift.missingnessDrift == null ? "—" : fmtNum(drift.missingnessDrift, 3)} help="mean shift in missing rate" />
          <DriftStat label="Cardinality drift" value={drift.cardinalityDrift == null ? "—" : fmtNum(drift.cardinalityDrift, 3)} help="mean shift in unique counts" />
          <DriftStat
            label="ID overlap"
            value={drift.idOverlapPct == null ? "—" : `${fmtNum(drift.idOverlapPct, 1)}%`}
            help="% of live IDs already seen"
          />
          <DriftStat
            label="Live target"
            value={
              <span style={{ color: data.datasets.find((d) => d.split === "live")?.targetAvailable ? CHART.green : "var(--faint)" }}>
                {data.datasets.find((d) => d.split === "live")?.targetAvailable ? "Available" : "Not available"}
              </span>
            }
            help="live is scored blind"
          />
        </div>
      </Panel>

      {/* Charts */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        <Panel title="Rows per expedition">
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={data.rowsPerExped} margin={{ top: 8, right: 8, bottom: 4, left: -6 }}>
              <CartesianGrid stroke="var(--border)" strokeDasharray="2 4" vertical={false} />
              <XAxis dataKey="exped" tick={AXIS} />
              <YAxis tick={AXIS} tickFormatter={(v: number) => fmtInt(v)} />
              <Tooltip contentStyle={TT} formatter={(v) => [fmtInt(Number(v)), "Rows"]} />
              <Bar dataKey="rows" fill={CHART_SERIES[0]} name="Rows" />
            </BarChart>
          </ResponsiveContainer>
        </Panel>
        <Panel title="Missingness by feature (%)">
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={data.missingness} layout="vertical" margin={{ top: 4, right: 12, bottom: 4, left: 8 }}>
              <CartesianGrid stroke="var(--border)" strokeDasharray="2 4" horizontal={false} />
              <XAxis type="number" tick={AXIS} tickFormatter={(v: number) => `${v.toFixed(0)}%`} />
              <YAxis type="category" dataKey="feature" tick={AXIS} width={86} />
              <Tooltip contentStyle={TT} formatter={(v) => [`${fmtNum(Number(v), 2)}%`, "Missing"]} />
              <Bar dataKey="pct" fill={CHART_SERIES[1]} name="Missing %" />
            </BarChart>
          </ResponsiveContainer>
        </Panel>
        <Panel title="Feature cardinality (unique values)">
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={data.cardinality} margin={{ top: 8, right: 8, bottom: 4, left: -6 }}>
              <CartesianGrid stroke="var(--border)" strokeDasharray="2 4" vertical={false} />
              <XAxis dataKey="feature" tick={AXIS} />
              <YAxis tick={AXIS} tickFormatter={(v: number) => fmtInt(v)} />
              <Tooltip contentStyle={TT} formatter={(v) => [fmtInt(Number(v)), "Unique"]} />
              <Bar dataKey="unique" fill={CHART_SERIES[2]} name="Unique values" />
            </BarChart>
          </ResponsiveContainer>
        </Panel>
        <Panel title="Target distribution (train)">
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={data.targetDist} margin={{ top: 8, right: 8, bottom: 4, left: -6 }}>
              <CartesianGrid stroke="var(--border)" strokeDasharray="2 4" vertical={false} />
              <XAxis dataKey="bucket" tick={AXIS} />
              <YAxis tick={AXIS} tickFormatter={(v: number) => fmtInt(v)} />
              <Tooltip contentStyle={TT} formatter={(v) => [fmtInt(Number(v)), "Count"]} />
              <Bar dataKey="count" fill={CHART_SERIES[3]} name="Count" />
            </BarChart>
          </ResponsiveContainer>
        </Panel>
      </div>

      {/* Schema diff */}
      <Panel title="Schema diff — train vs validation">
        <div style={{ overflowX: "auto" }}>
          <table className="qs-table">
            <thead><tr><th>Field</th><th>Train type</th><th>Validation type</th><th>Match</th></tr></thead>
            <tbody>
              {data.schemaDiff.map((r) => (
                <tr key={r.field}>
                  <td>{r.field}</td>
                  <td>{r.trainType}</td>
                  <td>{r.valType}</td>
                  <td style={{ color: r.match ? CHART.green : CHART.red, fontWeight: 600 }}>
                    {r.match ? "match" : "type mismatch"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}
