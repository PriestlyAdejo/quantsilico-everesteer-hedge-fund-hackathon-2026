export const CHART = {
  amber: "#FFB000",
  cyan: "#38BDF8",
  blue: "#3B82F6",
  green: "#22C55E",
  red: "#EF4444",
  violet: "#A78BFA",
  neutral: "#4B5563",
} as const;

export const CHART_SERIES = [CHART.cyan, CHART.blue, CHART.green, CHART.violet, CHART.neutral];

export const STAGE_COLOR: Record<string, string> = {
  R0: "#4B5563",
  R1: "#38BDF8",
  R2: "#3B82F6",
  R3: "#A78BFA",
  frontier: "#FFB000",
};
