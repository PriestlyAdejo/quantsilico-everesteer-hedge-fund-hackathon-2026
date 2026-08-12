import { useEffect, useState } from "react";
import { useDataSource } from "../data/useDataSource";
import type { StakingData } from "../data/types";
import { CHART } from "../data/chartTokens";
import { PAGE_META, fmtNum, fmtInt, fmtVal } from "../data/humanize";
import PageHeader from "../components/PageHeader";
import Panel, { MetricTile } from "../components/Panel";
import StatusPage from "../components/StatusPage";

type Classification = StakingData["classification"];

const TONE: Record<Classification, { color: string; bg: string; border: string; warning?: boolean }> = {
  VIRTUAL_EVENT_BALANCE: { color: CHART.cyan, bg: "rgba(56,189,248,0.06)", border: CHART.cyan },
  REAL_USDC: { color: CHART.red, bg: "rgba(239,68,68,0.08)", border: CHART.red, warning: true },
  NO_STAKING: { color: "var(--metadata)", bg: "rgba(133,147,161,0.05)", border: "var(--border)" },
  UNKNOWN: { color: CHART.amber, bg: "rgba(255,176,0,0.06)", border: CHART.amber, warning: true },
};

export default function Staking() {
  const ds = useDataSource();
  const [data, setData] = useState<StakingData | null>(null);
  const [source, setSource] = useState<string>("");
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    ds.getStaking().then((e) => {
      setData(e.data);
      setSource(e.source);
      setUpdatedAt(e.generatedAt);
      setLoading(false);
    });
  }, [ds]);

  if (loading) return <StatusPage state="loading" />;
  if (!data) return <StatusPage state="backend-unavailable" />;

  const tone = TONE[data.classification];
  const isReal = data.classification === "REAL_USDC";

  return (
    <div style={{ padding: 16, display: "flex", flexDirection: "column", gap: 14 }}>
      <PageHeader
        title={PAGE_META["/staking"].title}
        intro={PAGE_META["/staking"].intro}
        source={source}
        updatedAt={updatedAt}
      />

      {/* Plain-language banner driven by the classification */}
      <div style={{
        background: tone.bg,
        border: `1px solid ${tone.border}`,
        borderLeft: `3px solid ${tone.border}`,
        borderRadius: "var(--radius)",
        padding: "16px 20px",
        display: "flex",
        flexDirection: "column",
        gap: 8,
      }}>
        <div style={{ fontFamily: "'Raleway', sans-serif", fontSize: 15, lineHeight: 1.5, color: "var(--foreground)", fontWeight: 600 }}>
          {data.statement}
        </div>
        {data.virtualBalance != null && (
          <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 13, color: tone.color }}>
            Virtual balance: {fmtInt(data.virtualBalance)}
          </div>
        )}
        {isReal && data.requiresConfirmation && (
          <div style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 12,
            color: CHART.red,
            fontWeight: 600,
          }}>
            Real funds — any allocation requires manual confirmation. Nothing is ever submitted automatically.
          </div>
        )}
      </div>

      {/* Context */}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <MetricTile label="CONCENTRATION" value={fmtNum(data.concentration, 2)} />
        <MetricTile label="RISK PROFILE" value={fmtVal(data.riskProfile)} />
        <MetricTile
          label="CONFIRMATION"
          value={data.requiresConfirmation ? "MANUAL" : "NOT REQUIRED"}
          warn={data.requiresConfirmation}
        />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        <Panel title="Evidence">
          <div style={{ fontFamily: "'Raleway', sans-serif", fontSize: 12.5, lineHeight: 1.5, color: "var(--body-primary)" }}>
            {fmtVal(data.evidence)}
          </div>
        </Panel>
        <Panel title="Uncertainty">
          <div style={{ fontFamily: "'Raleway', sans-serif", fontSize: 12.5, lineHeight: 1.5, color: "var(--body-primary)" }}>
            {fmtVal(data.uncertainty)}
          </div>
        </Panel>
      </div>

      {/* Model evidence table */}
      <Panel title="Model evidence" noPad>
        <table className="qs-table">
          <thead>
            <tr>
              <th>MODEL</th><th>LOCAL EVIDENCE</th><th>LIVE EVIDENCE</th>
              <th>UNCERTAINTY</th><th>CORRELATION</th><th>PROPOSED ALLOCATION</th>
            </tr>
          </thead>
          <tbody>
            {data.candidates.map((c, i) => (
              <tr key={i}>
                <td style={{ color: "var(--foreground)", fontWeight: 600 }}>{c.model}</td>
                <td>{fmtNum(c.localEvidence, 4)}</td>
                <td style={{ color: c.liveEvidence == null ? "var(--faint)" : "var(--body-primary)" }}>{fmtNum(c.liveEvidence, 4)}</td>
                <td>{fmtNum(c.uncertainty, 2)}</td>
                <td>{fmtNum(c.correlation, 2)}</td>
                <td style={{ color: "var(--accent)" }}>
                  {c.proposedAllocationPct == null ? "—" : `${fmtNum(c.proposedAllocationPct, 0)}%`}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    </div>
  );
}
