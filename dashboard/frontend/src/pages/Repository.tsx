import { useEffect, useState } from "react";
import { useDataSource } from "../data/useDataSource";
import type { RepoData } from "../data/types";
import { CHART } from "../data/chartTokens";
import Panel from "../components/Panel";
import PageHeader from "../components/PageHeader";
import StatusPage from "../components/StatusPage";
import { PAGE_META, fmtVal, fmtClock } from "../data/humanize";

const STATUS_COLOR: Record<string, string> = {
  passing: CHART.green, healthy: CHART.green,
  failing: CHART.red, degraded: CHART.amber,
  unknown: "var(--faint)",
};

function KV({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div>
      <div className="qs-kv-label" style={{ marginBottom: 3 }}>{label}</div>
      <div className="qs-kv-value" style={color ? { color } : undefined}>{value}</div>
    </div>
  );
}

function CheckCard({ label, status, at, detail }: { label: string; status: "passing" | "failing" | "unknown"; at: string | null; detail: string }) {
  const color = STATUS_COLOR[status];
  return (
    <div style={{ padding: "10px 12px", background: "var(--surface)", border: `1px solid ${color}44`, borderRadius: 2, borderLeft: `2px solid ${color}` }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 5 }}>
        <span style={{ fontFamily: "'Montserrat', sans-serif", fontSize: 11.5, color: "var(--body-secondary)" }}>{label}</span>
        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, fontWeight: 700, color }}>{status.toUpperCase()}</span>
      </div>
      <div style={{ fontFamily: "'Raleway', sans-serif", fontSize: 11.5, color: "var(--body-primary)", lineHeight: 1.4 }}>{detail}</div>
      <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 9.5, color: "var(--faint)", marginTop: 4 }}>{at ? fmtClock(at) : "never run"}</div>
    </div>
  );
}

export default function Repository() {
  const ds = useDataSource();
  const [data, setData] = useState<RepoData | null>(null);
  const [meta, setMeta] = useState<{ source: string; updatedAt: string } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    ds.getRepository().then((e) => { setData(e.data); setMeta({ source: e.source, updatedAt: e.generatedAt }); setLoading(false); });
  }, [ds]);

  if (loading) return <StatusPage state="loading" />;
  if (!data) return <StatusPage state="backend-unavailable" />;

  return (
    <div style={{ padding: 16, display: "flex", flexDirection: "column", gap: 14 }}>
      <PageHeader
        title={PAGE_META["/repository"].title}
        intro={PAGE_META["/repository"].intro}
        source={meta?.source}
        updatedAt={meta?.updatedAt}
        actions={<span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 9.5, color: "var(--faint)" }}>Read-only · no git mutations</span>}
      />

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        <Panel title="Serving build">
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <KV label="Branch" value={fmtVal(data.servingBranch)} />
            <KV label="Commit" value={fmtVal(data.servingSha)} />
            <KV label="Working tree" value={data.dirty ? "Uncommitted changes" : "Clean"} color={data.dirty ? CHART.amber : CHART.green} />
            <KV label="Environment health" value={data.envHealth} color={STATUS_COLOR[data.envHealth]} />
            <KV label="Frontend build" value={fmtVal(data.frontendBuildSha)} />
            <KV label="Backend build" value={fmtVal(data.backendBuildSha)} />
          </div>
        </Panel>

        <Panel title="Runtime pins">
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <KV label="Python" value={fmtVal(data.pythonVersion)} />
            <KV label="Everest API" value={fmtVal(data.everestApiPin)} />
            <KV label="Lockfile hash" value={fmtVal(data.lockfileHash)} />
          </div>
        </Panel>
      </div>

      <Panel title="Reproducibility checks">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 12 }}>
          <CheckCard label="Test suite" {...data.lastTests} />
          <CheckCard label="Submission rehearsal" {...data.lastRehearsal} />
          <CheckCard label="Scorer parity" {...data.lastScorerParity} />
        </div>
      </Panel>

      <Panel title="Latest commits">
        <table className="qs-table">
          <thead><tr><th>Commit</th><th>Message</th><th>Author</th><th>When</th></tr></thead>
          <tbody>
            {data.latestCommits.map((c) => (
              <tr key={c.sha}>
                <td style={{ color: CHART.cyan }}>{c.sha}</td>
                <td style={{ color: "var(--body-primary)", maxWidth: 340, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{c.msg}</td>
                <td>{c.author}</td>
                <td style={{ color: "var(--faint)" }}>{fmtClock(c.ts)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    </div>
  );
}
