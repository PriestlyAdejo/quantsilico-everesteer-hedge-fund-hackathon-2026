interface HeatmapProps {
  rows: string[];
  cols: string[];
  data: Record<string, Record<string, number | null>>;
  colorLow?: string;
  colorHigh?: string;
  label?: string;
  formatValue?: (v: number) => string;
}

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

function hexToRgb(hex: string): [number, number, number] {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

function blendColor(low: string, high: string, t: number): string {
  const [lr, lg, lb] = hexToRgb(low);
  const [hr, hg, hb] = hexToRgb(high);
  return `rgb(${Math.round(lerp(lr, hr, t))},${Math.round(lerp(lg, hg, t))},${Math.round(lerp(lb, hb, t))})`;
}

export default function Heatmap({
  rows,
  cols,
  data,
  colorLow = "#0C1116",
  colorHigh = "#FFB000",
  label,
  formatValue = (v) => v.toFixed(2),
}: HeatmapProps) {
  const allVals: number[] = [];
  rows.forEach((r) => cols.forEach((c) => {
    const v = data[r]?.[c];
    if (v != null) allVals.push(v);
  }));
  const min = Math.min(...allVals);
  const max = Math.max(...allVals);
  const range = max - min || 1;

  const cellW = Math.max(44, Math.floor(380 / cols.length));
  const cellH = 26;

  return (
    <div style={{ overflowX: "auto" }}>
      {label && (
        <div style={{
          fontFamily: "'Montserrat', sans-serif", fontSize: 10, letterSpacing: "0.08em",
          color: "var(--metadata)", textTransform: "uppercase", marginBottom: 8,
        }}>
          {label}
        </div>
      )}
      <table style={{ borderCollapse: "collapse", fontSize: 11, fontFamily: "'JetBrains Mono', monospace" }}>
        <thead>
          <tr>
            <th style={{ width: 90, color: "var(--faint)", fontWeight: 400, textAlign: "left", padding: "0 6px 4px 0" }} />
            {cols.map((c) => (
              <th key={c} style={{
                color: "var(--metadata)", fontWeight: 500, fontSize: 10,
                padding: "0 2px 4px", textAlign: "center", whiteSpace: "nowrap",
              }}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r}>
              <td style={{
                color: "var(--body-secondary)", fontSize: 10, padding: "1px 8px 1px 0",
                whiteSpace: "nowrap", maxWidth: 90, overflow: "hidden", textOverflow: "ellipsis",
              }}>{r}</td>
              {cols.map((c) => {
                const v = data[r]?.[c];
                const t = v != null ? (v - min) / range : 0;
                const bg = v != null ? blendColor(colorLow, colorHigh, t) : "#1E2630";
                const fgLight = t > 0.6;
                return (
                  <td key={c} title={v != null ? formatValue(v) : "—"} style={{
                    background: bg,
                    color: fgLight ? "#090D11" : "var(--body-primary)",
                    textAlign: "center",
                    padding: "0 2px",
                    height: cellH,
                    width: cellW,
                    fontSize: 10,
                    cursor: "default",
                    transition: "opacity 0.1s",
                  }}>
                    {v != null ? formatValue(v) : "—"}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
