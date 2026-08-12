import type { ReactNode } from "react";

interface Props {
  open: boolean;
  title: string;
  subtitle?: string;
  onClose: () => void;
  children: ReactNode;
  /** Raw code / enum shown quietly at the footer for inspection. */
  rawCode?: string;
  width?: number;
}

/**
 * Right-side detail drawer for progressive disclosure — the place where
 * low-level fields, raw enums and provenance live instead of the main table.
 */
export default function Drawer({ open, title, subtitle, onClose, children, rawCode, width = 460 }: Props) {
  if (!open) return null;
  return (
    <>
      <div
        onClick={onClose}
        style={{ position: "fixed", inset: 0, background: "rgba(4,7,10,0.55)", zIndex: 90 }}
      />
      <div
        style={{
          position: "fixed",
          top: 0,
          right: 0,
          bottom: 0,
          width,
          maxWidth: "92vw",
          background: "var(--surface)",
          borderLeft: "1px solid var(--border)",
          boxShadow: "-12px 0 32px rgba(0,0,0,0.5)",
          zIndex: 91,
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "space-between",
            padding: "14px 16px",
            borderBottom: "1px solid var(--border)",
            gap: 12,
          }}
        >
          <div>
            <div style={{ fontFamily: "'Raleway', sans-serif", fontSize: 15, fontWeight: 700, color: "var(--foreground)" }}>
              {title}
            </div>
            {subtitle && (
              <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: "var(--metadata)", marginTop: 3 }}>
                {subtitle}
              </div>
            )}
          </div>
          <button
            onClick={onClose}
            style={{
              background: "none",
              border: "1px solid var(--border)",
              color: "var(--metadata)",
              borderRadius: "var(--radius)",
              cursor: "pointer",
              width: 24,
              height: 24,
              fontSize: 14,
              flexShrink: 0,
            }}
          >
            ✕
          </button>
        </div>
        <div style={{ flex: 1, overflowY: "auto", padding: "14px 16px" }}>{children}</div>
        {rawCode && (
          <div
            style={{
              borderTop: "1px solid var(--border)",
              padding: "8px 16px",
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 10,
              color: "var(--faint)",
            }}
          >
            raw: {rawCode}
          </div>
        )}
      </div>
    </>
  );
}
