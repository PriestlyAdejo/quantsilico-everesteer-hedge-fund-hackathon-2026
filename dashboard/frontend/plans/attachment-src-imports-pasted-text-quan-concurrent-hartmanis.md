# Plan: QuantSilico × Everesteer 2026 Research Console

## Context

The user has attached a detailed product brief for a desktop-first quantitative research / competition console. The app replaces the current placeholder App.tsx with a full multi-page shell wired to a clean DataSource abstraction for later FastAPI/Cursor integration. A detailed peer review of the initial plan (figma-make-plan-review.md) identified 14 required amendments — all incorporated here.

---

## Stance & Visual System

**Stance:** data-dense (Bloomberg Terminal DNA) — maximum information density, functional color coding, small tabular fonts, minimal whitespace.

**Top-left identity:** `QUANTSILICO // EVERESTEER 2026` with `RESEARCH CONSOLE` as smaller metadata.

**Fonts (all Google Fonts, wired via CSS @import at top of src/index.css):**
- `Montserrat` — nav labels, top-bar items, headings
- `Raleway` — section titles, panel labels
- `JetBrains Mono` — all data values, hashes, numbers, status codes

**Prescribed palette:**
```
--background:     #090D11
--surface:        #11161C
--surface-deep:   #0C1116
--elevated:       #161C24
--border:         #1E2630
--accent:         #FFB000   (amber — brand/interaction only)
--accent-hi:      #FFC53D
--accent-dim:     #B37A00
--foreground:     #EAF0F6
--body-primary:   #CDD6DF
--body-secondary: #A3AFBA
--metadata:       #8593A1
--faint:          #6F7C89
--radius:         2px
--font-size:      15px
```

**Stable chart palette (shared tokens, used on every chart page):**
```
amber   #FFB000  — interaction / selected / champion highlight only
cyan    #38BDF8  — primary data series
blue    #3B82F6  — secondary data series
green   #22C55E  — positive / live-proven
red     #EF4444  — negative / error / integrity failure
violet  #A78BFA  — optional 5th series only
neutral #4B5563  — baseline / reference
```
Amber is never used as the only/default series color. Red is reserved for genuine failures.

No glassmorphism. No large rounded cards. No generic SaaS aesthetic.

---

## Architecture

### Files to create / modify

| File | Action | 
|---|---|
| `src/index.css` | Google Font @imports first, then CSS custom properties |
| `src/App.tsx` | Mount Shell inside React Router BrowserRouter |
| `src/data/types.ts` | DataEnvelope, Provenance, DataSource interface, ActionResult, all domain types |
| `src/data/demo.ts` | DemoDataSource — SYNTHETIC_FIXTURE provenance on every envelope |
| `src/data/api.ts` | ApiDataSource — BACKEND_UNAVAILABLE stubs, no auto-fallback to demo |
| `src/data/useDataSource.ts` | Hook: reads mode from env/config, returns DataSource; never silently falls back |
| `src/components/Shell.tsx` | React Router outlet + TopBar + Sidebar + ActivityStrip |
| `src/components/TopBar.tsx` | EVENT / SDK / AUTH SCOPE / ROUND / UPLOADS / CHAMPION / GPU / AUTOPILOT with timestamps |
| `src/components/Sidebar.tsx` | Grouped nav with React Router NavLink; icon-rail collapse via localStorage |
| `src/components/CommandPalette.tsx` | Ctrl+K/Cmd+K; navigation registry + allowlisted actions calling DataSource |
| `src/components/ActivityStrip.tsx` | Persistent bottom strip |
| `src/components/ProvenanceBadge.tsx` | Color-coded badge for all 6 provenance values + STALE/UNKNOWN |
| `src/components/StatusPage.tsx` | loading / error / empty / stale / demo / backend-unavailable states |
| `src/components/Heatmap.tsx` | Shared lightweight SVG/CSS-grid heatmap (used for correlation, round×model, fold matrices) |
| `src/pages/Overview.tsx` | Metrics row + score/rank trajectory + frontier scatter + fold evidence + quota charts |
| `src/pages/EventControl.tsx` | SDK/event panels + allowlisted controls (refresh/snapshot/pull/scorer parity/baseline/autopilot) |
| `src/pages/RoundRoom.tsx` | Live cockpit + score by model + rank by round + Heatmap |
| `src/pages/DataLab.tsx` | Train/val/live cards + 5 charts + integrity flags (red=hard fail, amber=warning) |
| `src/pages/Experiments.tsx` | Dense sortable table + race decision labels + charts + drawer |
| `src/pages/Validation.tsx` | HARD INTEGRITY / SOFT RESEARCH EVIDENCE / RACE DECISION sections |
| `src/pages/Models.tsx` | Model table + detail drawer |
| `src/pages/FeatureLab.tsx` | Anonymous feature table + charts |
| `src/pages/Ensembles.tsx` | Blend table + 5 charts + blend controls |
| `src/pages/Leaderboard.tsx` | 4 tabs + 3 charts, official provenance, timestamps |
| `src/pages/Submission.tsx` | Quota + validator + 7-stage stepper with NOT_STARTED/RUNNING/PASS/FAIL/BLOCKED/RETRYABLE |
| `src/pages/Staking.tsx` | Huge classification banner (VIRTUAL/REAL USDC/NO STAKING/UNKNOWN) + evidence/allocation |
| `src/pages/ComputeJobs.tsx` | CPU/RAM/GPU/VRAM + queues + allowlisted controls only |
| `src/pages/Repository.tsx` | Read-only git/SDK/Python info — no mutation controls |
| `src/pages/Documentation.tsx` | Local doc search |
| `FIGMA_EXPORT_NOTES.md` | Routes, component tree, DataSource methods + actions, domain types, chart deps, font deps, localStorage keys, demo/API mode mechanism, known limitations |

---

## Amendment 1: Real URL Routing

Use `react-router-dom` (install if absent). All pages are proper routes. Sidebar NavLinks and CommandPalette both use the same route registry. Browser back/forward, refresh, and deep links all work.

```
/           → Overview
/event      → Event Control
/round      → Round Room
/data       → Data Lab
/experiments → Experiments
/validation → Validation
/models     → Models
/features   → Feature Lab
/ensembles  → Ensembles
/leaderboard → Leaderboard
/submission → Submission
/staking    → Staking
/compute    → Compute & Jobs
/repository → Repository
/docs       → Documentation
```

---

## Amendment 2: DataSource covers reads AND allowlisted actions

```ts
export interface DataSource {
  // reads — all return DataEnvelope<T>
  getOverview(): Promise<DataEnvelope<OverviewData>>
  getEventControl(): Promise<DataEnvelope<EventControlData>>
  getRoundRoom(): Promise<DataEnvelope<RoundRoomData>>
  getDataLab(): Promise<DataEnvelope<DataLabData>>
  getExperiments(): Promise<DataEnvelope<ExperimentRow[]>>
  getValidation(): Promise<DataEnvelope<ValidationData>>
  getModels(): Promise<DataEnvelope<ModelRow[]>>
  getFeatureLab(): Promise<DataEnvelope<FeatureLabData>>
  getEnsembles(): Promise<DataEnvelope<EnsembleData>>
  getLeaderboard(): Promise<DataEnvelope<LeaderboardData>>
  getSubmission(): Promise<DataEnvelope<SubmissionData>>
  getStaking(): Promise<DataEnvelope<StakingData>>
  getComputeJobs(): Promise<DataEnvelope<ComputeData>>
  getRepository(): Promise<DataEnvelope<RepoData>>
  getDocumentation(): Promise<DataEnvelope<DocumentationData>>

  // allowlisted actions
  refreshEvent(): Promise<ActionResult>
  snapshotEvent(): Promise<ActionResult>
  pullDatasets(): Promise<ActionResult>
  runScorerParity(): Promise<ActionResult>
  runOfficialBaseline(): Promise<ActionResult>
  startAutopilot(): Promise<ActionResult>
  stopAutopilot(): Promise<ActionResult>
  startRace(profile: string): Promise<ActionResult>
  buildEnsemble(): Promise<ActionResult>
  validateSubmission(candidateId: string): Promise<ActionResult>
  submitPractice(candidateId: string): Promise<ActionResult>
  submitLive(candidateId: string): Promise<ActionResult>
  stopJob(jobId: string): Promise<ActionResult>
}
```

No arbitrary command execution method. DemoDataSource returns synthetic ActionResult. ApiDataSource stubs return BACKEND_UNAVAILABLE.

---

## Amendment 3: Standardised DataEnvelope

```ts
export type Provenance =
  | 'OFFICIAL_EVENT_STATE'
  | 'OFFICIAL_EVENT_DATA'
  | 'OFFICIAL_PLATFORM_OBSERVATION'
  | 'LOCAL_EXPERIMENT'
  | 'SYNTHETIC_FIXTURE'
  | 'MANUALLY_RECORDED'

export interface DataEnvelope<T> {
  schemaVersion: number
  kind: string
  provenance: Provenance
  generatedAt: string
  stale: boolean
  sourceId?: string
  eventSnapshotId?: string
  data: T
}
```

Every read response is wrapped. ProvenanceBadge renders provenance + stale consistently across all pages.

---

## Amendment 4: No automatic API → Demo fallback

```
DEMO MODE  → DemoDataSource (explicit, never automatic)
API MODE   → ApiDataSource
             backend unavailable → BACKEND UNAVAILABLE state
```

`useDataSource()` reads `VITE_DATA_MODE` env var (or a runtime config). It never silently falls back to demo on API failure.

---

## Amendment 5: Race-decision semantics on Validation & Experiments

**Validation page — three visually distinct sections:**

```
HARD INTEGRITY          → PASS / FAIL / UNKNOWN
SOFT RESEARCH EVIDENCE  → STRONG / MIXED / WEAK / INSUFFICIENT
RACE DECISION           → PROMOTE R0→R1 / PROMOTE — TOP SCORE /
                          PROMOTE — DIVERSITY SLOT / KEEP — ENSEMBLE VALUE /
                          RETEST / RETIRE — DOMINATED / RETIRE — SATURATED FAMILY /
                          FAILED — TRAINING ERROR / INVALID — INTEGRITY FAILURE
```

Red = only genuine integrity/error. WEAK evidence ≠ red. Amber = warnings.

**Experiments page** — each row has a visible race-decision label:
`PROMOTED — TOP LOCAL SCORE`, `PROMOTED — DIVERSITY SLOT`, `RETAINED — ENSEMBLE VALUE`, `RETIRED — DOMINATED`, `RETIRED — SATURATED FAMILY`, `FAILED — OOM`, `INVALID — ID ALIGNMENT`, etc.

---

## Amendment 6: Improved frontier scatter

```
x-axis  = runtime / compute cost
y-axis  = local event-equivalent score
size    = prediction novelty/diversity
shape   = model family
outline = race stage (R0/R1/R2/R3/frontier)
```

Hover tooltip: run, model family, operator, parent, local score, recent score, runtime, diversity, practice/live result, race decision.

---

## Amendment 7: Stable chart palette

Already defined above. All chart files import from `src/data/chartTokens.ts` — no per-page color invention.

---

## Amendment 8: Data freshness everywhere

Event Control, Round Room, Leaderboard, Staking, Compute & Jobs, and TopBar all show `UPDATED / STALE / UNKNOWN` with ISO timestamp from `envelope.generatedAt`. Empty cells replaced with `UNKNOWN` where state is genuinely unknown.

---

## Amendment 9: Submission stepper states

7-stage stepper (SELECT → INFER → VALIDATE → PACKAGE → DRY RUN → SUBMIT → RECORD). Each stage supports: `NOT_STARTED / RUNNING / PASS / FAIL / BLOCKED / RETRYABLE`. Demo simulates both a successful path and a FAIL at VALIDATE with RETRYABLE recovery.

---

## Amendment 10: Heatmaps via shared component

`src/components/Heatmap.tsx` — lightweight SVG or CSS-grid heatmap. Used for:
- Prediction-correlation matrix (Ensembles)
- Model × round scores (Round Room)
- Validation fold matrices

Not forced through Recharts.

---

## Amendment 11: Command palette with actions

CommandPalette (Ctrl+K / Cmd+K) contains:
1. All 15 navigation routes
2. Allowlisted actions: Refresh Event, Snapshot Event, Pull Data, Run Scorer Parity, Run Official Baseline, Start Fast Race, Build Ensemble, Start Autopilot, Stop Autopilot

Actions call DataSource methods. No free-text shell input.

---

## Amendment 12: Desktop verification targets

Verify at: **1280×800** (primary — competition laptop), **1440×900**, **1920×1080**.
- Tables remain usable
- Charts do not clip
- TopBar does not wrap
- Collapsed icon rail stays functional

Mobile sanity check only — do not sacrifice desktop density.

---

## Amendment 13: FIGMA_EXPORT_NOTES.md

Document: routes, component tree, DataSource reads + actions, domain types, chart dependencies (recharts + custom Heatmap), font dependencies, localStorage keys (sidebar collapse, data mode), demo/API mode mechanism (VITE_DATA_MODE), known implementation limitations.

---

## Amendment 14: Final visual review checklist

Before marking complete:
1. Run every route
2. Expand and collapse sidebar
3. Open CommandPalette; exercise nav + action items
4. Exercise loading/error/empty/stale/demo/backend-unavailable on at least 3 pages
5. Exercise successful and failed submission paths
6. Exercise all 4 staking classifications
7. Verify SYNTHETIC provenance can never be mistaken for official data
8. Confirm chart palette is consistent across pages
9. Correct overflow, clipping, misalignment, inconsistent chart colours, excessive whitespace

---

## Final Implementation Notes (from second review)

### Offline-safe production fonts
Google Font `@import` is acceptable for Figma Make development. `FIGMA_EXPORT_NOTES.md` must explicitly flag that the Cursor integration should self-host Montserrat, Raleway, and JetBrains Mono so the event-day console has no runtime Google Fonts dependency. Visual appearance must remain identical.

### Mixed provenance on composite pages
`DataEnvelope` remains the top-level response wrapper. Individual domain records on mixed-source pages (e.g. Overview combines OFFICIAL_EVENT_STATE, OFFICIAL_PLATFORM_OBSERVATION, LOCAL_EXPERIMENT) must also carry:

```ts
interface ProvenanceMeta {
  provenance: Provenance
  generatedAt: string
  sourceId?: string
  eventSnapshotId?: string
}
```

Domain types like `MetricCardData` should extend `ProvenanceMeta` where evidence sources differ within a single page. Never assign one page-wide provenance to heterogeneous evidence.

### BrowserRouter SPA fallback (FIGMA_EXPORT_NOTES.md)
Add: *Production integration using BrowserRouter requires SPA history fallback when served by FastAPI/static hosting. Cursor must verify that directly loading or refreshing every application route (`/validation`, `/experiments`, `/round`, etc.) returns the React app, not a 404.*

### Unknown is not zero — global rule
Never convert unavailable, unknown, disconnected, or not-yet-observed numeric values into `0`. Use instead:

```text
UNKNOWN        NOT CONNECTED      NOT AVAILABLE
NOT DETECTED   —
```

A displayed `0`, `0.0000`, `$0`, `0 GB`, or rank `0` must always mean the underlying evidence genuinely contains zero. This applies to all metric cards, TopBar indicators, leaderboard ranks, GPU readouts, staking balances, and quota values.

---

## Verification (end-to-end)

1. `pnpm install` — confirm react-router-dom installed
2. Dev server already running on $PORT — navigate all 15 routes
3. Sidebar collapse → localStorage persisted on reload
4. Ctrl+K → CommandPalette → navigate to /staking → confirm VIRTUAL classification banner
5. /submission → advance through stepper → simulate FAIL at VALIDATE
6. /validation → confirm three sections render (HARD INTEGRITY / SOFT RESEARCH EVIDENCE / RACE DECISION)
7. /ensembles → confirm Heatmap renders for prediction correlations
8. Check viewport at 1280×800 — tables usable, charts unclipped, TopBar intact
