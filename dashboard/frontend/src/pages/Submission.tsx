import { useEffect, useState } from "react";
import { useDataSource } from "../data/useDataSource";
import type { SubmissionData, StepStatus } from "../data/types";
import { CHART } from "../data/chartTokens";
import { PAGE_META, fmtInt, fmtVal } from "../data/humanize";
import PageHeader from "../components/PageHeader";
import Panel, { Btn, MetricTile } from "../components/Panel";
import JobTiming from "../components/JobTiming";
import StatusPage from "../components/StatusPage";
import SubmissionModeBanner from "../components/SubmissionModeBanner";

const STEP_COLORS: Record<StepStatus, string> = {
  NOT_STARTED: "var(--border)",
  RUNNING: CHART.cyan,
  PASS: CHART.green,
  FAIL: CHART.red,
  BLOCKED: CHART.amber,
  RETRYABLE: CHART.amber,
};

const STEP_BG: Record<StepStatus, string> = {
  NOT_STARTED: "transparent",
  RUNNING: "rgba(56,189,248,0.08)",
  PASS: "rgba(34,197,94,0.08)",
  FAIL: "rgba(239,68,68,0.08)",
  BLOCKED: "rgba(255,176,0,0.08)",
  RETRYABLE: "rgba(255,176,0,0.08)",
};

const STEP_LABEL: Record<StepStatus, string> = {
  NOT_STARTED: "NOT STARTED",
  RUNNING: "RUNNING",
  PASS: "PASS",
  FAIL: "FAIL",
  BLOCKED: "BLOCKED",
  RETRYABLE: "RETRYABLE",
};

type Candidate = SubmissionData["candidates"][number];

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <div style={{ fontFamily: "'Montserrat', sans-serif", fontSize: 9, color: "var(--metadata)", letterSpacing: "0.08em", marginBottom: 3 }}>{label}</div>
      <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: "var(--body-primary)", wordBreak: "break-all" }}>{children}</div>
    </div>
  );
}

function Check({ ok }: { ok: boolean }) {
  return <span style={{ color: ok ? CHART.green : CHART.red }}>{ok ? "✓" : "✗"}</span>;
}

export default function Submission() {
  const ds = useDataSource();
  const [data, setData] = useState<SubmissionData | null>(null);
  const [source, setSource] = useState<string>("");
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [actionLog, setActionLog] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = () => {
    ds.getSubmission().then((e) => {
      setData(e.data);
      setSource(e.source);
      setUpdatedAt(e.generatedAt);
      setSelectedId((prev) => prev ?? e.data.selectedCandidate);
      setLoading(false);
    });
  };

  useEffect(() => { load(); }, [ds]);

  if (loading) return <StatusPage state="loading" />;
  if (!data) return <StatusPage state="backend-unavailable" />;

  const selected: Candidate | undefined =
    data.candidates.find((c) => c.id === selectedId) ?? data.candidates[0];

  const quotaRemaining =
    data.quotaTotal != null && data.quotaUsed != null ? data.quotaTotal - data.quotaUsed : null;

  // Enable submit only when every gate passes.
  const gateReasons: string[] = selected ? [...selected.blockingReasons] : ["No candidate selected"];
  if (selected) {
    if (!selected.laneAllowed) gateReasons.push("Submission lane not allowed for this candidate");
    if (!selected.quotaAllows) gateReasons.push("Upload budget exhausted for this lane");
    if (!selected.integrityOk) gateReasons.push("Integrity checks have not passed");
    if (selected.idCoverage !== 100) gateReasons.push("ID coverage is not 100% against the live split");
    if (!selected.pickleOk) gateReasons.push("Model artefact (pickle) is not verified");
  }
  const uniqueReasons = Array.from(new Set(gateReasons));
  const canSubmit = Boolean(selected) && uniqueReasons.length === 0;

  const run = async (fn: () => Promise<{ message: string }>) => {
    setBusy(true);
    try {
      const r = await fn();
      setActionLog(r.message);
      load(); // state advances from the backend, not manual stepping
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ padding: 16, display: "flex", flexDirection: "column", gap: 14 }}>
      <PageHeader
        title={PAGE_META["/submission"].title}
        intro={PAGE_META["/submission"].intro}
        source={source}
        updatedAt={updatedAt}
      />
      <SubmissionModeBanner mode={data.submissionMode} />

      {/* Upload budget (quota, not scoring) */}
      <Panel title="Upload budget">
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <MetricTile label="TOTAL BUDGET" value={fmtVal(data.quotaTotal)} />
          <MetricTile label="USED" value={fmtVal(data.quotaUsed)} warn={data.quotaTotal != null && data.quotaUsed != null && data.quotaUsed > data.quotaTotal * 0.8} />
          <MetricTile label="PRACTICE" value={fmtVal(data.quotaPractice)} />
          <MetricTile label="LIVE RESERVE" value={fmtVal(data.quotaLiveReserve)} />
          <MetricTile label="EMERGENCY" value={fmtVal(data.quotaEmergency)} />
          <MetricTile
            label="REMAINING"
            value={quotaRemaining == null ? "—" : quotaRemaining}
            accent={quotaRemaining != null && quotaRemaining > 3}
            critical={quotaRemaining != null && quotaRemaining <= 1}
          />
        </div>
      </Panel>

      {/* Candidate selection */}
      <Panel title="Submission candidates" noPad>
        <table className="qs-table">
          <thead>
            <tr>
              <th></th><th>MODEL</th><th>LANE</th><th>ID COVERAGE</th>
              <th>DUPES</th><th>BOUNDS</th><th>PICKLE</th><th>INTEGRITY</th>
            </tr>
          </thead>
          <tbody>
            {data.candidates.map((c) => (
              <tr
                key={c.id}
                onClick={() => setSelectedId(c.id)}
                style={{ cursor: "pointer", background: c.id === selected?.id ? "rgba(255,176,0,0.06)" : undefined }}
              >
                <td>
                  <span style={{ color: c.id === selected?.id ? "var(--accent)" : "var(--faint)" }}>
                    {c.id === selected?.id ? "◉" : "○"}
                  </span>
                </td>
                <td style={{ color: c.id === selected?.id ? "var(--accent)" : "var(--foreground)", fontWeight: 600 }}>{c.model}</td>
                <td>{c.lane}</td>
                <td style={{ color: c.idCoverage !== 100 ? CHART.red : "var(--body-primary)" }}>
                  {c.idCoverage == null ? "—" : `${c.idCoverage}%`}
                </td>
                <td style={{ color: (c.duplicates ?? 0) > 0 ? CHART.red : "var(--body-primary)" }}>{fmtVal(c.duplicates)}</td>
                <td><Check ok={c.boundsOk} /></td>
                <td><Check ok={c.pickleOk} /></td>
                <td><Check ok={c.integrityOk} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>

      {/* Selected candidate detail */}
      {selected && (
        <Panel title={`Candidate detail — ${selected.model}`}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 14 }}>
            <Field label="SPLIT FINGERPRINT">{fmtVal(selected.splitFingerprint)}</Field>
            <Field label="ID COVERAGE">{selected.idCoverage == null ? "—" : `${selected.idCoverage}%`}</Field>
            <Field label="DUPLICATES">{fmtVal(selected.duplicates)}</Field>
            <Field label="BOUNDS OK"><Check ok={selected.boundsOk} /></Field>
            <Field label="PICKLE OK"><Check ok={selected.pickleOk} /></Field>
            <Field label="PRED HASH">{fmtVal(selected.predHash)}</Field>
            <Field label="MODEL HASH">{fmtVal(selected.modelHash)}</Field>
            <Field label="LINEAGE">{fmtVal(selected.lineage)}</Field>
          </div>
        </Panel>
      )}

      {/* Pipeline stepper — reflects backend job state */}
      <Panel title="Submission pipeline">
        <div style={{ display: "flex", gap: 0, flexWrap: "wrap", alignItems: "stretch" }}>
          {data.stepperSteps.map((step, i) => {
            const color = STEP_COLORS[step.status];
            const bg = STEP_BG[step.status];
            return (
              <div key={step.label} style={{ display: "flex", alignItems: "center", gap: 0 }}>
                <div style={{
                  background: bg,
                  border: `1px solid ${color}`,
                  borderRadius: 2,
                  padding: "10px 14px",
                  minWidth: 96,
                  textAlign: "center",
                }}>
                  <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 9.5, color, fontWeight: 600, letterSpacing: "0.06em" }}>
                    {STEP_LABEL[step.status]}
                  </div>
                  <div style={{ fontFamily: "'Montserrat', sans-serif", fontSize: 11, color: "var(--foreground)", fontWeight: 600, marginTop: 4 }}>
                    {step.label}
                  </div>
                  {step.message && (
                    <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 9, color: "var(--metadata)", marginTop: 3 }}>
                      {step.message}
                    </div>
                  )}
                  {step.status === "RUNNING" && (step.startedAt || step.etaSeconds != null) && (
                    <div style={{ marginTop: 5 }}>
                      <JobTiming
                        compact
                        job={{
                          startedAt: step.startedAt ?? null,
                          etaSeconds: step.etaSeconds ?? null,
                          totalSeconds: null,
                          progress: null,
                          queuePosition: null,
                          status: "RUNNING",
                        }}
                      />
                    </div>
                  )}
                </div>
                {i < data.stepperSteps.length - 1 && (
                  <div style={{ color: "var(--faint)", fontSize: 12, padding: "0 4px" }}>→</div>
                )}
              </div>
            );
          })}
        </div>
      </Panel>

      {/* Submit actions */}
      <Panel title="Actions">
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
          <Btn variant="ghost" disabled={!selected || busy} onClick={() => selected && run(() => ds.validateSubmission(selected.id))}>
            Validate
          </Btn>
          <Btn variant="surface" disabled={!canSubmit || busy} onClick={() => selected && run(() => ds.submitPractice(selected.id))}>
            ↑ Submit practice
          </Btn>
          <Btn variant="accent" disabled={!canSubmit || busy} onClick={() => selected && run(() => ds.submitLive(selected.id))}>
            ↑ Submit live
          </Btn>
        </div>

        {!canSubmit && uniqueReasons.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <div style={{ fontFamily: "'Montserrat', sans-serif", fontSize: 9, color: "var(--metadata)", letterSpacing: "0.08em", marginBottom: 5 }}>
              SUBMISSION BLOCKED
            </div>
            <ul style={{ margin: 0, paddingLeft: 16, display: "flex", flexDirection: "column", gap: 3 }}>
              {uniqueReasons.map((r, i) => (
                <li key={i} style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: CHART.red }}>{r}</li>
              ))}
            </ul>
          </div>
        )}

        {actionLog && (
          <div style={{ marginTop: 12, fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: "var(--accent)" }}>
            {actionLog}
          </div>
        )}

        <div style={{ marginTop: 10, fontFamily: "'JetBrains Mono', monospace", fontSize: 10, color: "var(--faint)" }}>
          {fmtInt(data.candidates.length)} candidates · pipeline reflects live backend state
        </div>
      </Panel>
    </div>
  );
}
