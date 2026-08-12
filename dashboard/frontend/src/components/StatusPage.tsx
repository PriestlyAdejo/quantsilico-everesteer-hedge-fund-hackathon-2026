type State = "loading" | "error" | "empty" | "stale" | "demo" | "backend-unavailable";

interface Props {
  state: State;
  message?: string;
  children?: React.ReactNode;
}

export default function StatusPage({ state, message, children }: Props) {
  if (state === "loading") {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", gap: 12 }}>
        <div style={{
          width: 6, height: 6, borderRadius: "50%", background: "var(--accent)",
          animation: "pulse 1.2s ease-in-out infinite",
        }} />
        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: "var(--metadata)" }}>
          LOADING…
        </span>
        <style>{`@keyframes pulse { 0%,100%{opacity:0.2} 50%{opacity:1} }`}</style>
      </div>
    );
  }

  const configs: Record<State, { label: string; color: string; icon: string }> = {
    loading: { label: "LOADING", color: "var(--accent)", icon: "◌" },
    error: { label: "ERROR", color: "#EF4444", icon: "⊗" },
    empty: { label: "NO DATA", color: "var(--metadata)", icon: "∅" },
    stale: { label: "STALE DATA", color: "#FFB000", icon: "⚠" },
    demo: { label: "DEMO MODE — SYNTHETIC FIXTURE", color: "#FFB000", icon: "◈" },
    "backend-unavailable": { label: "BACKEND UNAVAILABLE", color: "#EF4444", icon: "⊘" },
  };

  const cfg = configs[state];

  return (
    <div style={{
      display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
      height: "100%", gap: 10, padding: 40,
    }}>
      <span style={{ fontSize: 28, color: cfg.color, lineHeight: 1 }}>{cfg.icon}</span>
      <span style={{
        fontFamily: "'JetBrains Mono', monospace", fontSize: 11, letterSpacing: "0.1em",
        color: cfg.color, fontWeight: 600,
      }}>
        {cfg.label}
      </span>
      {message && (
        <span style={{ fontSize: 12, color: "var(--metadata)", textAlign: "center", maxWidth: 420 }}>
          {message}
        </span>
      )}
      {children}
    </div>
  );
}
