import type { CSSProperties, ReactNode } from "react";

interface PanelProps {
  title?: string;
  children: ReactNode;
  style?: CSSProperties;
  actions?: ReactNode;
  accent?: boolean;
  noPad?: boolean;
}

export default function Panel({ title, children, style, actions, noPad }: PanelProps) {
  return (
    <div style={{
      background: "var(--surface)",
      border: "1px solid var(--border)",
      borderRadius: "var(--radius)",
      display: "flex",
      flexDirection: "column",
      ...style,
    }}>
      {(title || actions) && (
        <div style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "8px 12px",
          borderBottom: "1px solid var(--border)",
          gap: 10,
          flexShrink: 0,
        }}>
          {title && (
            <span style={{
              fontFamily: "'Montserrat', sans-serif",
              fontSize: 12,
              fontWeight: 600,
              letterSpacing: "0.02em",
              color: "var(--body-secondary)",
            }}>
              {title}
            </span>
          )}
          {actions && <div style={{ display: "flex", gap: 6, alignItems: "center" }}>{actions}</div>}
        </div>
      )}
      <div style={{ flex: 1, padding: noPad ? 0 : 12, overflow: "auto" }}>
        {children}
      </div>
    </div>
  );
}

export function Btn({
  children,
  onClick,
  variant = "ghost",
  small,
  danger,
  disabled,
}: {
  children: ReactNode;
  onClick?: () => void;
  variant?: "ghost" | "accent" | "surface";
  small?: boolean;
  danger?: boolean;
  disabled?: boolean;
}) {
  const base: CSSProperties = {
    fontFamily: "'Montserrat', sans-serif",
    fontSize: small ? 10 : 11,
    fontWeight: 600,
    letterSpacing: "0.06em",
    border: "1px solid var(--border)",
    borderRadius: "2px",
    cursor: disabled ? "not-allowed" : "pointer",
    padding: small ? "3px 8px" : "5px 10px",
    opacity: disabled ? 0.5 : 1,
    transition: "background 0.1s, color 0.1s",
    textTransform: "uppercase",
  };
  const variants: Record<string, CSSProperties> = {
    ghost: { background: "none", color: "var(--metadata)", borderColor: "var(--border)" },
    accent: { background: "var(--accent)", color: "#090D11", borderColor: "var(--accent)" },
    surface: { background: "var(--elevated)", color: "var(--body-primary)", borderColor: "var(--border)" },
  };
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{ ...base, ...variants[variant], ...(danger ? { color: "#EF4444", borderColor: "#EF4444" } : {}) }}
    >
      {children}
    </button>
  );
}

export function MetricTile({ label, value, sub, accent, warn, critical, labelNode }: {
  label: string; value: string | number; sub?: string; accent?: boolean; warn?: boolean; critical?: boolean; labelNode?: ReactNode;
}) {
  const isUnknown = value === "—" || value === "UNKNOWN" || value === "NOT AVAILABLE";
  const color = critical ? "#EF4444" : warn ? "#FFB000" : isUnknown ? "var(--faint)" : accent ? "var(--accent)" : "var(--foreground)";
  return (
    <div style={{
      background: "var(--surface)",
      border: "1px solid var(--border)",
      borderRadius: "var(--radius)",
      padding: "10px 14px",
      minWidth: 118,
      flex: "1 1 118px",
    }}>
      <div style={{
        fontFamily: "'Montserrat', sans-serif",
        fontSize: 11,
        letterSpacing: "0.02em",
        color: "var(--metadata)",
        marginBottom: 7,
      }}>
        {labelNode ?? label}
      </div>
      <div style={{
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: 21,
        fontWeight: 600,
        color,
        lineHeight: 1,
      }}>
        {value}
      </div>
      {sub && (
        <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: "var(--metadata)", marginTop: 4 }}>
          {sub}
        </div>
      )}
    </div>
  );
}
