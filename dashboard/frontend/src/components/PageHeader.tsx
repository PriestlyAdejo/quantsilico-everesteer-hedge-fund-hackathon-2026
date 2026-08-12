import type { ReactNode } from "react";
import { fmtClock } from "../data/humanize";

interface Props {
  title: string;
  intro: string;
  /** Human source line, e.g. "Everesteer API" or "Local research store". */
  source?: string;
  updatedAt?: string | null;
  /** Right-aligned controls: context selectors, actions. */
  actions?: ReactNode;
}

/**
 * Standard page header: title (readable, not tiny), a short human intro,
 * and a single quiet source line — instead of a provenance badge on every
 * title. Provenance stays in the data model and detail drawers.
 */
export default function PageHeader({ title, intro, source, updatedAt, actions }: Props) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 14, flexWrap: "wrap" }}>
        <h1
          style={{
            fontFamily: "'Raleway', sans-serif",
            fontSize: 19,
            fontWeight: 700,
            color: "var(--foreground)",
            margin: 0,
            letterSpacing: "0.01em",
          }}
        >
          {title}
        </h1>
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 10 }}>
          {actions}
          {(source || updatedAt) && (
            <span
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 11,
                color: "var(--metadata)",
                whiteSpace: "nowrap",
              }}
            >
              {source && <span>Source: {source}</span>}
              {source && updatedAt && <span style={{ color: "var(--border)" }}> · </span>}
              {updatedAt && <span style={{ color: "var(--faint)" }}>Updated {fmtClock(updatedAt)}</span>}
            </span>
          )}
        </div>
      </div>
      <p
        style={{
          fontFamily: "'Raleway', sans-serif",
          fontSize: 12.5,
          lineHeight: 1.5,
          color: "var(--body-secondary)",
          margin: 0,
          maxWidth: 820,
        }}
      >
        {intro}
      </p>
    </div>
  );
}
