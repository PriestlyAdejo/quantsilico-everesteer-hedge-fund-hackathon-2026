import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router";
import { useDataSource } from "../data/useDataSource";
import { GROUPS } from "./Sidebar";

interface PaletteItem {
  label: string;
  description: string;
  type: "nav" | "action";
  path?: string;
  action?: () => Promise<void>;
}

export default function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const navigate = useNavigate();
  const ds = useDataSource();

  const navItems: PaletteItem[] = GROUPS.flatMap((g) =>
    g.items.map((item) => ({
      label: item.label,
      description: `Navigate → ${g.label}`,
      type: "nav" as const,
      path: item.path,
    }))
  );

  const actionItems: PaletteItem[] = [
    { label: "Refresh Event", description: "Pull latest event state", type: "action", action: async () => { const r = await ds.refreshEvent(); setStatus(r.message); } },
    { label: "Snapshot Event", description: "Save current event snapshot", type: "action", action: async () => { const r = await ds.snapshotEvent(); setStatus(r.message); } },
    { label: "Pull Data", description: "Pull latest datasets", type: "action", action: async () => { const r = await ds.pullDatasets(); setStatus(r.message); } },
    { label: "Run Scorer Parity", description: "Verify local scorer matches official", type: "action", action: async () => { const r = await ds.runScorerParity(); setStatus(r.message); } },
    { label: "Run Official Baseline", description: "Score the official baseline model", type: "action", action: async () => { const r = await ds.runOfficialBaseline(); setStatus(r.message); } },
    { label: "Start Fast Race", description: "Begin fast race profile", type: "action", action: async () => { const r = await ds.startRace("fast"); setStatus(r.message); } },
    { label: "Build Ensemble", description: "Build best current ensemble", type: "action", action: async () => { const r = await ds.buildEnsemble("weighted"); setStatus(r.message); } },
    { label: "Start Autopilot", description: "Engage autopilot", type: "action", action: async () => { const r = await ds.startAutopilot(); setStatus(r.message); } },
    { label: "Stop Autopilot", description: "Disengage autopilot", type: "action", action: async () => { const r = await ds.stopAutopilot(); setStatus(r.message); } },
  ];

  const allItems = [...navItems, ...actionItems];

  const filtered = query
    ? allItems.filter((i) => i.label.toLowerCase().includes(query.toLowerCase()) || i.description.toLowerCase().includes(query.toLowerCase()))
    : allItems;

  const handleKey = useCallback((e: KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "k") {
      e.preventDefault();
      setOpen((o) => !o);
      setQuery("");
      setStatus(null);
    }
    if (e.key === "Escape") setOpen(false);
  }, []);

  useEffect(() => {
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [handleKey]);

  const run = async (item: PaletteItem) => {
    setOpen(false);
    if (item.type === "nav" && item.path) {
      navigate(item.path);
    } else if (item.action) {
      setStatus("Running…");
      await item.action();
    }
  };

  if (!open) return null;

  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 1000,
      background: "rgba(9,13,17,0.7)",
      display: "flex", alignItems: "flex-start", justifyContent: "center",
      paddingTop: 80,
    }} onClick={() => setOpen(false)}>
      <div
        style={{
          background: "var(--elevated)",
          border: "1px solid var(--border)",
          borderRadius: 2,
          width: 540,
          maxHeight: 440,
          display: "flex",
          flexDirection: "column",
          boxShadow: "0 24px 60px rgba(0,0,0,0.8)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Input */}
        <div style={{ display: "flex", alignItems: "center", padding: "0 14px", borderBottom: "1px solid var(--border)", gap: 10 }}>
          <span style={{ color: "var(--metadata)", fontSize: 13 }}>⌘</span>
          <input
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search routes and actions…"
            style={{
              flex: 1,
              background: "none",
              border: "none",
              outline: "none",
              color: "var(--foreground)",
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 13,
              padding: "12px 0",
            }}
          />
          <kbd style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 10,
            color: "var(--faint)",
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 2,
            padding: "2px 5px",
          }}>ESC</kbd>
        </div>

        {/* Results */}
        <div style={{ overflowY: "auto", maxHeight: 340 }}>
          {status && (
            <div style={{
              padding: "8px 14px",
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 11,
              color: "var(--accent)",
              borderBottom: "1px solid var(--border)",
            }}>
              {status}
            </div>
          )}
          {filtered.length === 0 && (
            <div style={{ padding: "20px 14px", color: "var(--metadata)", fontSize: 12, textAlign: "center" }}>
              No results
            </div>
          )}
          {filtered.map((item, i) => (
            <button
              key={i}
              onClick={() => run(item)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                width: "100%",
                background: "none",
                border: "none",
                borderBottom: "1px solid rgba(30,38,48,0.5)",
                cursor: "pointer",
                padding: "9px 14px",
                textAlign: "left",
              }}
              onMouseOver={(e) => (e.currentTarget.style.background = "rgba(255,176,0,0.06)")}
              onMouseOut={(e) => (e.currentTarget.style.background = "none")}
            >
              <span style={{ fontSize: 10, color: item.type === "action" ? "var(--accent)" : "var(--metadata)", width: 50, flexShrink: 0, fontFamily: "'JetBrains Mono', monospace" }}>
                {item.type === "action" ? "ACTION" : "ROUTE"}
              </span>
              <span style={{ fontFamily: "'Montserrat', sans-serif", fontSize: 12, color: "var(--foreground)", fontWeight: 500 }}>{item.label}</span>
              <span style={{ fontFamily: "'Montserrat', sans-serif", fontSize: 11, color: "var(--metadata)", marginLeft: "auto" }}>{item.description}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
