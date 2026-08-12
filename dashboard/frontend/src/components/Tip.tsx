import { useState, type ReactNode } from "react";
import { GLOSSARY } from "../data/humanize";

interface Props {
  /** Term to look up in the glossary, or pass an explicit `text`. */
  term?: string;
  text?: string;
  children: ReactNode;
}

/**
 * Dotted-underline term with a hover definition. Domain terminology
 * (CORR20, ICIR, exped…) is kept and explained, never dumbed down.
 */
export default function Tip({ term, text, children }: Props) {
  const [show, setShow] = useState(false);
  const def = text ?? (term ? GLOSSARY[term] : undefined);
  if (!def) return <>{children}</>;

  return (
    <span
      style={{ position: "relative", borderBottom: "1px dotted var(--faint)", cursor: "help" }}
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      {children}
      {show && (
        <span
          style={{
            position: "absolute",
            bottom: "calc(100% + 6px)",
            left: 0,
            zIndex: 50,
            width: 240,
            background: "var(--elevated)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius)",
            padding: "8px 10px",
            fontFamily: "'Raleway', sans-serif",
            fontSize: 11.5,
            lineHeight: 1.45,
            color: "var(--body-primary)",
            boxShadow: "0 6px 18px rgba(0,0,0,0.5)",
            whiteSpace: "normal",
            textTransform: "none",
            letterSpacing: 0,
          }}
        >
          {term && (
            <span style={{ display: "block", color: "var(--accent)", fontFamily: "'JetBrains Mono', monospace", fontSize: 10, marginBottom: 3 }}>
              {term}
            </span>
          )}
          {def}
        </span>
      )}
    </span>
  );
}
