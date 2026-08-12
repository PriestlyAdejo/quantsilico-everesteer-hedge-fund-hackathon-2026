import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { useDataSource } from "../data/useDataSource";
import type { ComputeData, Job } from "../data/types";
import { CHART } from "../data/chartTokens";
import Panel, { Btn, MetricTile } from "../components/Panel";
import PageHeader from "../components/PageHeader";
import JobTiming from "../components/JobTiming";
import StatusPage from "../components/StatusPage";
import { PAGE_META, fmtNum, fmtInt, fmtVal, fmtClock } from "../data/humanize";

const TT = { background: "var(--elevated)", border: "1px solid var(--border)", borderRadius: 2, fontSize: 11, fontFamily: "'JetBrains Mono', monospace" };

function GaugeBar({ label, used, total, unit }: { label: string; used: number | null; total: number | null; unit: string }) {
  const known = used != null && total != null && total > 0;
  const pct = known ? (used! / total!) * 100 : 0;
  const color = pct > 85 ? CHART.red : pct > 65 ? CHART.amber : CHART.cyan;
  return (
    <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 2, padding: "10px 14px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
        <span className="qs-kv-label">{label}</span>
        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11.5, color: known ? color : "var(--faint)" }}>
          {known ? `${fmtNum(used, unit === "%" ? 0 : 1)}${unit} / ${fmtNum(total, 0)}${unit}` : "—"}
        </span>
      </div>
      <div style={{ height: 4, background: "var(--elevated)", borderRadius: 2 }}>
        <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: 2, transition: "width 0.3s" }} />
      </div>
    </div>
  );
}

function JobTable({ jobs, onStop }: { jobs: Job[]; onStop?: (id: string) => void }) {
  return (
    <div style={{ overflowX: "auto" }}>
      <table className="qs-table">
        <thead>
          <tr><th>Job</th><th>Type</th><th>Candidate</th><th>Status</th><th>Timing</th><th>Device</th>{onStop && <th></th>}</tr>
        </thead>
        <tbody>
          {jobs.length === 0 ? (
            <tr><td colSpan={onStop ? 7 : 6} style={{ color: "var(--faint)" }}>No jobs</td></tr>
          ) : jobs.map((j) => (
            <tr key={j.id}>
              <td style={{ color: "var(--body-primary)" }}>{j.name}</td>
              <td>{j.type}</td>
              <td>{fmtVal(j.candidate)}</td>
              <td><span style={{ color: j.status === "RUNNING" ? CHART.cyan : j.status === "QUEUED" ? CHART.amber : j.status === "FAILED" ? CHART.red : "var(--metadata)" }}>{j.status}</span></td>
              <td><JobTiming job={j} compact /></td>
              <td>{j.device}</td>
              {onStop && (
                <td>{(j.status === "RUNNING" || j.status === "QUEUED") && <Btn small danger onClick={() => onStop(j.id)}>Stop</Btn>}</td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function ComputeJobs() {
  const ds = useDataSource();
  const [data, setData] = useState<ComputeData | null>(null);
  const [meta, setMeta] = useState<{ source: string; updatedAt: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLog, setActionLog] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    const load = () => ds.getComputeJobs().then((e) => { if (!alive) return; setData(e.data); setMeta({ source: e.source, updatedAt: e.generatedAt }); setLoading(false); });
    load();
    const poll = setInterval(load, 8000);
    return () => { alive = false; clearInterval(poll); };
  }, [ds]);

  if (loading) return <StatusPage state="loading" />;
  if (!data) return <StatusPage state="backend-unavailable" />;

  const hw = data.hardware;
  const u = data.utilisation;
  const stopJob = async (id: string) => { const r = await ds.stopJob(id); setActionLog(r.message); };

  return (
    <div style={{ padding: 16, display: "flex", flexDirection: "column", gap: 14 }}>
      <PageHeader title={PAGE_META["/compute"].title} intro={PAGE_META["/compute"].intro} source={meta?.source} updatedAt={meta?.updatedAt} />

      {/* Hardware — real machine, from backend detection */}
      <Panel title="Hardware">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: 12 }}>
          <div><div className="qs-kv-label">OS</div><div className="qs-kv-value">{fmtVal(hw.os)}</div></div>
          <div><div className="qs-kv-label">CPU</div><div className="qs-kv-value">{fmtVal(hw.cpu.model)}{hw.cpu.cores != null ? ` · ${hw.cpu.cores} cores` : ""}</div></div>
          <div><div className="qs-kv-label">GPU</div><div className="qs-kv-value" style={{ color: hw.gpu.name ? undefined : "var(--faint)" }}>{hw.gpu.name ?? "Not detected"}</div></div>
          <div><div className="qs-kv-label">VRAM</div><div className="qs-kv-value">{hw.gpu.vramTotalGb != null ? `${fmtNum(hw.gpu.vramUsedGb, 1)} / ${fmtNum(hw.gpu.vramTotalGb, 0)} GB` : "—"}</div></div>
          <div><div className="qs-kv-label">CUDA</div><div className="qs-kv-value">{hw.gpu.cuda ?? "Not detected"}</div></div>
          <div><div className="qs-kv-label">Disk</div><div className="qs-kv-value">{hw.disk.totalGb != null ? `${fmtInt(hw.disk.usedGb)} / ${fmtInt(hw.disk.totalGb)} GB` : "—"}</div></div>
        </div>
      </Panel>

      {/* Utilisation gauges */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 10 }}>
        <GaugeBar label="CPU" used={hw.cpu.usedPct} total={100} unit="%" />
        <GaugeBar label="RAM pressure" used={hw.ram.usedGb} total={hw.ram.totalGb} unit="GB" />
        <GaugeBar label="GPU utilisation" used={u.gpuUtilPct} total={100} unit="%" />
        <GaugeBar label="VRAM utilisation" used={u.vramUtilPct} total={100} unit="%" />
      </div>

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <MetricTile label="Experiments / hour" value={fmtVal(u.experimentsPerHour)} />
        <MetricTile label="Queue length" value={fmtVal(u.queueLength)} />
        <MetricTile label="Event watcher" value={data.eventWatcher.active ? "Active" : "Inactive"} accent={data.eventWatcher.active} sub={`ping ${fmtClock(data.eventWatcher.lastPing)} · ${data.eventWatcher.interval}`} />
      </div>

      {/* Queues with timing */}
      <Panel title="Local job queue" actions={actionLog ? <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10.5, color: "var(--accent)" }}>{actionLog}</span> : undefined}>
        <JobTable jobs={data.localQueue} onStop={stopJob} />
      </Panel>

      <Panel title="Server compute queue">
        {data.serverQueue.length === 0
          ? <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: "var(--faint)" }}>Server compute is not available for this event.</div>
          : <JobTable jobs={data.serverQueue} />}
      </Panel>

      <Panel title="Runtime history">
        <ResponsiveContainer width="100%" height={150}>
          <BarChart data={data.runtimeHistory}>
            <XAxis dataKey="ts" tick={false} />
            <YAxis tick={{ fill: "var(--metadata)", fontSize: 10 }} unit="m" width={40} />
            <Tooltip contentStyle={TT} labelFormatter={(v) => fmtClock(String(v))} />
            <Bar dataKey="durationMin" name="Duration (min)" fill={CHART.blue} />
          </BarChart>
        </ResponsiveContainer>
      </Panel>
    </div>
  );
}
