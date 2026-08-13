import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router";
import { useDataSource } from "../data/useDataSource";
import type { DocumentationData, DocArticle, DocBlock } from "../data/types";
import PageHeader from "../components/PageHeader";
import StatusPage from "../components/StatusPage";
import { PAGE_META, fmtClock } from "../data/humanize";
import { articleMatchesQuery } from "../data/docSearch";

const MONO = "'JetBrains Mono', monospace";
const CALLOUT_COLOR = { info: "var(--metadata)", warning: "#FFB000", danger: "#EF4444" } as const;

function CommandBlock({ command }: { command: string }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard?.writeText(command).then(() => { setCopied(true); setTimeout(() => setCopied(false), 1200); });
  };
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, background: "var(--surface-deep)", border: "1px solid var(--border)", borderRadius: 2, padding: "8px 10px", margin: "8px 0" }}>
      <span style={{ color: "var(--faint)", fontFamily: MONO, fontSize: 12 }}>$</span>
      <code style={{ flex: 1, fontFamily: MONO, fontSize: 12, color: "var(--body-primary)", overflowX: "auto" }}>{command}</code>
      <button onClick={copy} style={{ background: "none", border: "1px solid var(--border)", borderRadius: 2, color: copied ? "var(--accent)" : "var(--faint)", cursor: "pointer", fontFamily: MONO, fontSize: 9.5, padding: "2px 6px" }}>
        {copied ? "copied" : "copy"}
      </button>
    </div>
  );
}

function Block({ block, onNav }: { block: DocBlock; onNav: (href: string) => void }) {
  switch (block.kind) {
    case "intro":
      return <p style={{ fontFamily: "'Raleway', sans-serif", fontSize: 14, color: "var(--body-primary)", lineHeight: 1.6, margin: "0 0 14px" }}>{block.text}</p>;
    case "heading":
      return <h3 style={{ fontFamily: "'Raleway', sans-serif", fontSize: 14.5, fontWeight: 700, color: "var(--foreground)", margin: "18px 0 6px" }}>{block.text}</h3>;
    case "paragraph":
      return <p style={{ fontFamily: "'Raleway', sans-serif", fontSize: 13, color: "var(--body-secondary)", lineHeight: 1.7, margin: "0 0 10px" }}>{block.text}</p>;
    case "flow":
      return (
        <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 0, margin: "10px 0" }}>
          {block.nodes.map((n, i) => (
            <div key={n.id} style={{ display: "flex", alignItems: "center" }}>
              <span style={{ fontFamily: "'Montserrat', sans-serif", fontSize: 11, color: "var(--body-secondary)", background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 3, padding: "4px 10px" }}>{n.label}</span>
              {i < block.nodes.length - 1 && <span style={{ color: "var(--faint)", padding: "0 6px" }}>→</span>}
            </div>
          ))}
        </div>
      );
    case "callout":
      return (
        <div style={{ margin: "10px 0", padding: "9px 12px", background: "var(--surface)", borderLeft: `2px solid ${CALLOUT_COLOR[block.tone]}`, borderRadius: 2 }}>
          <span style={{ fontFamily: "'Raleway', sans-serif", fontSize: 12.5, color: "var(--body-primary)", lineHeight: 1.5 }}>{block.text}</span>
        </div>
      );
    case "command":
      return <CommandBlock command={block.command} />;
    case "metric":
      return (
        <div style={{ margin: "8px 0", padding: "8px 12px", background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 2 }}>
          <span style={{ fontFamily: MONO, fontSize: 11.5, color: "var(--accent)" }}>{block.name}</span>
          <span style={{ fontFamily: "'Raleway', sans-serif", fontSize: 12.5, color: "var(--body-secondary)", marginLeft: 8 }}>{block.text}</span>
        </div>
      );
    case "related":
      return (
        <button onClick={() => onNav(block.href)} style={{ display: "inline-flex", alignItems: "center", gap: 6, background: "none", border: "1px solid var(--border)", borderRadius: 2, color: "var(--accent)", cursor: "pointer", fontFamily: "'Montserrat', sans-serif", fontSize: 11.5, padding: "4px 9px", margin: "4px 6px 4px 0" }}>
          {block.label} <span style={{ fontSize: 10 }}>↗</span>
        </button>
      );
    case "table":
      return (
        <div style={{ overflowX: "auto", margin: "10px 0 14px", border: "1px solid var(--border)", borderRadius: 2 }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: MONO, fontSize: 11 }}>
            <thead>
              <tr>
                {block.headers.map((h) => (
                  <th key={h} style={{ textAlign: "left", padding: "6px 8px", borderBottom: "1px solid var(--border)", color: "var(--metadata)", fontWeight: 600, whiteSpace: "nowrap" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {block.rows.map((row, ri) => (
                <tr key={ri}>
                  {row.map((cell, ci) => (
                    <td key={ci} style={{ padding: "5px 8px", borderBottom: "1px solid var(--border)", color: "var(--body-secondary)", verticalAlign: "top" }}>{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
  }
}

export default function Documentation() {
  const ds = useDataSource();
  const nav = useNavigate();
  const [data, setData] = useState<DocumentationData | null>(null);
  const [meta, setMeta] = useState<{ source: string; updatedAt: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [activeId, setActiveId] = useState<string | null>(null);

  useEffect(() => {
    ds.getDocumentation().then((e) => {
      setData(e.data);
      setMeta({ source: e.source, updatedAt: e.generatedAt });
      setActiveId(e.data?.articles[0]?.id ?? null);
      setLoading(false);
    });
  }, [ds]);

  const matches = (a: DocArticle, q: string) => articleMatchesQuery(a, q);

  const ordered = useMemo(() => data ? [...data.articles].sort((a, b) => a.order - b.order) : [], [data]);
  const filtered = useMemo(() => ordered.filter((a) => matches(a, query)), [ordered, query]);
  const active = ordered.find((a) => a.id === activeId) ?? filtered[0] ?? null;
  const activeIdx = active ? ordered.findIndex((a) => a.id === active.id) : -1;
  const prev = activeIdx > 0 ? ordered[activeIdx - 1] : null;
  const next = activeIdx >= 0 && activeIdx < ordered.length - 1 ? ordered[activeIdx + 1] : null;

  if (loading) return <StatusPage state="loading" />;
  if (!data) return <StatusPage state="backend-unavailable" />;

  return (
    <div style={{ padding: 16, display: "flex", flexDirection: "column", gap: 14, height: "100%" }}>
      <PageHeader title={PAGE_META["/docs"].title} intro={PAGE_META["/docs"].intro} source={meta?.source} updatedAt={meta?.updatedAt} />

      <div style={{ display: "grid", gridTemplateColumns: "220px 1fr", gap: 14, flex: 1, minHeight: 0 }}>
        {/* Internal nav */}
        <div style={{ display: "flex", flexDirection: "column", gap: 8, overflowY: "auto" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 2, padding: "0 10px" }}>
            <span style={{ color: "var(--faint)", fontSize: 12 }}>⌕</span>
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search docs…"
              style={{ flex: 1, background: "none", border: "none", outline: "none", color: "var(--foreground)", fontFamily: MONO, fontSize: 12, padding: "8px 0" }} />
          </div>
          {data.sections.map((sec) => {
            const arts = filtered.filter((a) => a.section === sec.id);
            if (arts.length === 0) return null;
            return (
              <div key={sec.id}>
                <div style={{ fontFamily: "'Montserrat', sans-serif", fontSize: 9, letterSpacing: "0.12em", textTransform: "uppercase", color: "var(--faint)", padding: "6px 6px 3px" }}>{sec.label}</div>
                {arts.map((a) => (
                  <button key={a.id} onClick={() => setActiveId(a.id)}
                    style={{
                      display: "block", width: "100%", textAlign: "left", cursor: "pointer",
                      background: a.id === active?.id ? "rgba(255,176,0,0.08)" : "none",
                      border: "none", borderLeft: a.id === active?.id ? "2px solid var(--accent)" : "2px solid transparent",
                      color: a.id === active?.id ? "var(--foreground)" : "var(--body-secondary)",
                      fontFamily: "'Montserrat', sans-serif", fontSize: 12, padding: "5px 10px",
                    }}>
                    {a.title}
                  </button>
                ))}
              </div>
            );
          })}
          {filtered.length === 0 && <div style={{ fontFamily: MONO, fontSize: 11, color: "var(--faint)", padding: 8 }}>No matches</div>}
        </div>

        {/* Article */}
        <div style={{ overflowY: "auto", background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 2, padding: "18px 22px" }}>
          {active ? (
            <>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
                <h2 style={{ fontFamily: "'Raleway', sans-serif", fontSize: 18, fontWeight: 700, color: "var(--foreground)", margin: 0 }}>{active.title}</h2>
              </div>
              <p style={{ fontFamily: "'Raleway', sans-serif", fontSize: 12.5, color: "var(--metadata)", margin: "0 0 16px" }}>{active.description}</p>
              {active.blocks.map((b, i) => <Block key={i} block={b} onNav={nav} />)}

              {/* Prev / next */}
              <div style={{ display: "flex", justifyContent: "space-between", gap: 10, marginTop: 24, paddingTop: 14, borderTop: "1px solid var(--border)" }}>
                {prev ? (
                  <button onClick={() => setActiveId(prev.id)} style={navBtn}>← {prev.title}</button>
                ) : <span />}
                {next ? (
                  <button onClick={() => setActiveId(next.id)} style={{ ...navBtn, textAlign: "right" }}>{next.title} →</button>
                ) : <span />}
              </div>
            </>
          ) : <div style={{ fontFamily: MONO, fontSize: 12, color: "var(--faint)" }}>Select an article.</div>}
        </div>
      </div>

      <div style={{ fontFamily: MONO, fontSize: 9.5, color: "var(--faint)" }}>
        {active?.source === "generated"
          ? `Generated from commit ${data.generatedFromSha ?? "—"}`
          : "Curated runbook"}
        {data.generatedAt ? ` · ${fmtClock(data.generatedAt)}` : ""}
      </div>
    </div>
  );
}

const navBtn = {
  background: "none", border: "1px solid var(--border)", borderRadius: 2,
  color: "var(--body-secondary)", cursor: "pointer",
  fontFamily: "'Montserrat', sans-serif", fontSize: 11.5, padding: "6px 10px", maxWidth: "48%",
} as const;
