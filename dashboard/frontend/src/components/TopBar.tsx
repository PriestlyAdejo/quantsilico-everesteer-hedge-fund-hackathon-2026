import { useState, useEffect } from "react";
import { useDataSource, isDemo } from "../data/useDataSource";
import type { EventStatus, ConnectionState } from "../data/types";
import { fmtVal, elapsedSince } from "../data/humanize";
import { connectLiveEvents } from "../data/liveEvents";

const CONN_COLOR: Record<ConnectionState, string> = {
  LIVE: "#22C55E",
  RECONNECTING: "#FFB000",
  DISCONNECTED: "#EF4444",
  NOT_CONNECTED: "var(--faint)",
};

function ConnPill({ status, lastUpdateAt }: { status: ConnectionState; lastUpdateAt: string | null }) {
  const [, setTick] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setTick((n) => n + 1), 1000);
    return () => clearInterval(t);
  }, []);
  const el = elapsedSince(lastUpdateAt);
  const color = CONN_COLOR[status];
  const text =
    status === "LIVE"
      ? el != null
        ? `LIVE · updated ${Math.max(0, Math.round(el))}s ago`
        : "LIVE"
      : status.replace("_", " ");
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 6, flexShrink: 0 }}>
      <span
        style={{
          width: 7,
          height: 7,
          borderRadius: "50%",
          background: color,
          boxShadow: status === "LIVE" ? `0 0 6px ${color}` : "none",
        }}
      />
      <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color, whiteSpace: "nowrap" }}>{text}</span>
    </span>
  );
}

function Item({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 5,
        padding: "0 11px",
        borderRight: "1px solid var(--border)",
        height: 38,
        flexShrink: 0,
      }}
    >
      <span style={{ fontFamily: "'Montserrat', sans-serif", fontSize: 10, letterSpacing: "0.04em", color: "var(--faint)" }}>
        {label}
      </span>
      <span
        style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 12,
          fontWeight: accent ? 600 : 400,
          color: accent ? "var(--accent)" : "var(--body-primary)",
        }}
      >
        {value}
      </span>
    </div>
  );
}

export default function TopBar() {
  const ds = useDataSource();
  const [st, setSt] = useState<EventStatus | null>(null);
  const [time, setTime] = useState(() => new Date().toLocaleTimeString("en-GB", { hour12: false }));

  useEffect(() => {
    let alive = true;
    const load = () => ds.getEventStatus().then((e) => { if (alive) setSt(e.data); });
    load();
    const poll = setInterval(load, 5000);
    const clk = setInterval(() => setTime(new Date().toLocaleTimeString("en-GB", { hour12: false })), 1000);
    const stopLive = isDemo()
      ? () => undefined
      : connectLiveEvents(() => {
          if (alive) load();
        }, { base: import.meta.env.VITE_API_BASE ?? "" });
    return () => {
      alive = false;
      clearInterval(poll);
      clearInterval(clk);
      stopLive();
    };
  }, [ds]);

  const round = st?.round.label ? `${st.round.label} / ${fmtVal(st.round.total)}` : "—";
  const uploads = st ? `${fmtVal(st.uploads.used)} / ${fmtVal(st.uploads.total)}` : "—";

  return (
    <div
      style={{
        height: 38,
        background: "var(--surface-deep)",
        borderBottom: "1px solid var(--border)",
        display: "flex",
        alignItems: "center",
        padding: "0 14px",
        flexShrink: 0,
        overflow: "hidden",
      }}
    >
      {/* Identity */}
      <div style={{ marginRight: 16, flexShrink: 0 }}>
        <span style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 700, fontSize: 12, letterSpacing: "0.06em", color: "var(--foreground)" }}>
          QUANTSILICO
        </span>
        <span style={{ color: "var(--accent)", margin: "0 4px", fontWeight: 700 }}>//</span>
        <span style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 600, fontSize: 12, letterSpacing: "0.04em", color: "var(--body-secondary)" }}>
          EVERESTEER 2026
        </span>
        <span style={{ fontFamily: "'Raleway', sans-serif", fontSize: 9.5, letterSpacing: "0.08em", color: "var(--faint)", marginLeft: 8, textTransform: "uppercase" }}>
          Research Console
        </span>
      </div>

      <div style={{ width: 1, height: 18, background: "var(--border)", marginRight: 12, flexShrink: 0 }} />

      {/* Primary competition-critical items — kept visible; overflow scrolls */}
      <div style={{ display: "flex", flex: 1, overflowX: "auto", alignItems: "center", minWidth: 0 }}>
        <Item label="EVENT" value={fmtVal(st?.eventId, "NOT CONNECTED")} />
        <Item label="ROUND" value={round} accent />
        <Item label="UPLOADS" value={uploads} />
        <Item label="CHAMPION" value={fmtVal(st?.champion)} accent />
        <Item label="RANK" value={fmtVal(st?.externalRank)} />
        <Item label="AUTOPILOT" value={st?.autopilot ? "ON" : "OFF"} accent={st?.autopilot} />
      </div>

      {/* System / status area (secondary values collapse here) + live + clock */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, flexShrink: 0, paddingLeft: 12 }}>
        <span
          title={`Auth scope: ${fmtVal(st?.scope)}`}
          style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: "var(--faint)", cursor: "default" }}
        >
          {isDemo() ? "preview" : "system"}
        </span>
        <ConnPill status={st?.connection ?? "NOT_CONNECTED"} lastUpdateAt={st?.lastUpdateAt ?? null} />
        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: "var(--metadata)" }}>{time}</span>
      </div>
    </div>
  );
}
