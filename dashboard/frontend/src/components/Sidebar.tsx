import { NavLink } from "react-router";
import { useState, useEffect } from "react";
import { useDataSource } from "../data/useDataSource";

const STORAGE_KEY = "qs_sidebar_collapsed";

interface NavItem {
  path: string;
  label: string;
  icon: string;
}

const GROUPS: { label: string; items: NavItem[] }[] = [
  {
    label: "OPERATE",
    items: [
      { path: "/", label: "Overview", icon: "◎" },
      { path: "/event", label: "Event Control", icon: "⌘" },
      { path: "/round", label: "Round Room", icon: "◈" },
      { path: "/data", label: "Data Lab", icon: "⊞" },
    ],
  },
  {
    label: "RESEARCH",
    items: [
      { path: "/experiments", label: "Experiments", icon: "⚗" },
      { path: "/validation", label: "Validation", icon: "✓" },
      { path: "/models", label: "Models", icon: "⬡" },
      { path: "/features", label: "Feature Lab", icon: "∿" },
      { path: "/ensembles", label: "Ensembles", icon: "⊕" },
    ],
  },
  {
    label: "COMPETE",
    items: [
      { path: "/leaderboard", label: "Leaderboard", icon: "▲" },
      { path: "/submission", label: "Submission", icon: "↑" },
      { path: "/staking", label: "Staking", icon: "◆" },
    ],
  },
  {
    label: "SYSTEM",
    items: [
      { path: "/compute", label: "Compute & Jobs", icon: "⚙" },
      { path: "/repository", label: "Repository", icon: "⊗" },
      { path: "/docs", label: "Documentation", icon: "?" },
    ],
  },
];

export default function Sidebar() {
  const ds = useDataSource();
  const [collapsed, setCollapsed] = useState<boolean>(() => {
    try { return localStorage.getItem(STORAGE_KEY) === "true"; } catch { return false; }
  });
  const [recommended, setRecommended] = useState<string | null>(null);

  useEffect(() => {
    try { localStorage.setItem(STORAGE_KEY, String(collapsed)); } catch {}
  }, [collapsed]);

  useEffect(() => {
    let alive = true;
    ds.getOverview().then((e) => { if (alive) setRecommended(e.data.recommendation.actions[0]?.to ?? null); });
    return () => { alive = false; };
  }, [ds]);

  const w = collapsed ? 44 : 192;

  return (
    <div style={{
      width: w,
      minWidth: w,
      background: "var(--surface)",
      borderRight: "1px solid var(--border)",
      display: "flex",
      flexDirection: "column",
      overflow: "hidden",
      transition: "width 0.18s ease, min-width 0.18s ease",
      flexShrink: 0,
    }}>
      <div style={{ flex: 1, overflowY: "auto", overflowX: "hidden", padding: collapsed ? "8px 0" : "8px 0" }}>
        {GROUPS.map((group) => (
          <div key={group.label} style={{ marginBottom: 4 }}>
            {!collapsed && (
              <div style={{
                fontFamily: "'Montserrat', sans-serif",
                fontSize: 9,
                letterSpacing: "0.12em",
                color: "var(--faint)",
                padding: "8px 12px 3px",
                textTransform: "uppercase",
              }}>
                {group.label}
              </div>
            )}
            {collapsed && <div style={{ height: 8 }} />}
            {group.items.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === "/"}
                style={({ isActive }) => ({
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  padding: collapsed ? "7px 0" : "6px 12px",
                  justifyContent: collapsed ? "center" : "flex-start",
                  textDecoration: "none",
                  background: isActive ? "rgba(255,176,0,0.08)" : "transparent",
                  borderLeft: isActive ? "2px solid var(--accent)" : "2px solid transparent",
                  transition: "background 0.1s",
                })}
              >
                {({ isActive }) => (
                  <>
                    <span style={{
                      fontSize: 14,
                      color: isActive ? "var(--accent)" : "var(--metadata)",
                      lineHeight: 1,
                      width: 18,
                      textAlign: "center",
                      flexShrink: 0,
                    }}>
                      {item.icon}
                    </span>
                    {!collapsed && (
                      <span style={{
                        fontFamily: "'Montserrat', sans-serif",
                        fontSize: 12.5,
                        fontWeight: isActive ? 600 : 400,
                        color: isActive ? "var(--foreground)" : "var(--body-secondary)",
                        whiteSpace: "nowrap",
                      }}>
                        {item.label}
                      </span>
                    )}
                    {recommended === item.path && !isActive && (
                      <span
                        title="Recommended next"
                        style={{
                          marginLeft: collapsed ? 0 : "auto",
                          width: 6,
                          height: 6,
                          borderRadius: "50%",
                          background: "var(--accent)",
                          boxShadow: "0 0 5px var(--accent)",
                          flexShrink: 0,
                        }}
                      />
                    )}
                  </>
                )}
              </NavLink>
            ))}
          </div>
        ))}
      </div>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed((c) => !c)}
        title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        style={{
          background: "none",
          border: "none",
          borderTop: "1px solid var(--border)",
          color: "var(--faint)",
          cursor: "pointer",
          padding: "8px",
          fontSize: 12,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          transition: "color 0.1s",
        }}
        onMouseOver={(e) => (e.currentTarget.style.color = "var(--accent)")}
        onMouseOut={(e) => (e.currentTarget.style.color = "var(--faint)")}
      >
        {collapsed ? "»" : "«"}
      </button>
    </div>
  );
}

export { GROUPS };
