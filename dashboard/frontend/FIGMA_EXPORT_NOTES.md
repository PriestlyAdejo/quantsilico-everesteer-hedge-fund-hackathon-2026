# FIGMA_EXPORT_NOTES

QuantSilico × Everesteer 2026 Research Console — export handoff document for Cursor integration.

---

## Routes

| Path | Component | Description |
|---|---|---|
| `/` | Overview | Event metrics, score trajectory, frontier scatter, fold evidence, quota |
| `/event` | EventControl | SDK/auth info, event config, capability matrix, allowlisted controls |
| `/round` | RoundRoom | Live round cockpit, queues, board, heatmap |
| `/data` | DataLab | Train/val/live dataset cards, integrity flags, 5 charts |
| `/experiments` | Experiments | Sortable experiment table with race decisions, drawer, charts |
| `/validation` | Validation | Hard Integrity / Soft Research Evidence / Race Decision + charts |
| `/models` | Models | Model registry table + detail drawer |
| `/features` | FeatureLab | Anonymous feature table + importance/correlation charts |
| `/ensembles` | Ensembles | Blend members, correlation heatmap, marginal contribution charts |
| `/leaderboard` | Leaderboard | 4-tab leaderboard + trajectory charts + round×model matrix |
| `/submission` | Submission | Quota, validator, 7-stage stepper |
| `/staking` | Staking | Classification banner (VIRTUAL/REAL USDC/NO STAKING/UNKNOWN) |
| `/compute` | ComputeJobs | CPU/RAM/GPU gauges, queues, runtime history |
| `/repository` | Repository | Read-only git/SDK/Python info |
| `/docs` | Documentation | Searchable local documentation |

**Router:** `react-router` v8 with `createBrowserRouter`.

**Production requirement:** FastAPI/static hosting must implement SPA history fallback so all frontend routes return `index.html`. Direct reload of `/validation`, `/round`, etc. must not return 404.

---

## Component Tree

```
App
└── RouterProvider (router)
    └── Shell (layout)
        ├── TopBar (event status bar)
        ├── Sidebar (grouped nav, icon-rail collapse)
        │   └── NavLink × 15
        ├── <Outlet> (page content)
        └── ActivityStrip (bottom strip)
        └── CommandPalette (Ctrl+K overlay, portal)
```

**Shared components:**
- `Panel` — surface panel with optional title/actions
- `Btn` — ghost/accent/surface button variants
- `MetricTile` — single metric card
- `ProvenanceBadge` — color-coded provenance label
- `StatusPage` — loading/error/empty/stale/demo/backend-unavailable
- `Heatmap` — custom SVG/CSS-grid heatmap (not Recharts)

---

## DataSource Interface

### Reads (all return `DataEnvelope<T>`)
| Method | Return type |
|---|---|
| `getOverview()` | `OverviewData` |
| `getEventControl()` | `EventControlData` |
| `getRoundRoom()` | `RoundRoomData` |
| `getDataLab()` | `DataLabData` |
| `getExperiments()` | `ExperimentRow[]` |
| `getValidation()` | `ValidationData` |
| `getModels()` | `ModelRow[]` |
| `getFeatureLab()` | `FeatureLabData` |
| `getEnsembles()` | `EnsembleData` |
| `getLeaderboard()` | `LeaderboardData` |
| `getSubmission()` | `SubmissionData` |
| `getStaking()` | `StakingData` |
| `getComputeJobs()` | `ComputeData` |
| `getRepository()` | `RepoData` |
| `getDocumentation()` | `DocumentationData` |

### Actions (all return `ActionResult`)
| Method | Notes |
|---|---|
| `refreshEvent()` | Pull latest event state |
| `snapshotEvent()` | Save snapshot |
| `pullDatasets()` | Pull datasets |
| `runScorerParity()` | Verify scorer |
| `runOfficialBaseline()` | Score official baseline |
| `startAutopilot()` | Engage autopilot |
| `stopAutopilot()` | Disengage autopilot |
| `startRace(profile)` | Start race with profile |
| `buildEnsemble()` | Build current ensemble |
| `validateSubmission(id)` | Run pre-submission validation |
| `submitPractice(id)` | Submit to practice lane |
| `submitLive(id)` | Submit to live lane |
| `stopJob(id)` | Kill a job |

---

## DataEnvelope

```ts
interface DataEnvelope<T> {
  schemaVersion: number;
  kind: string;
  provenance: Provenance;
  generatedAt: string;        // ISO 8601
  stale: boolean;
  sourceId?: string;
  eventSnapshotId?: string;
  data: T;
}
```

Individual records on mixed-provenance pages (Overview, Leaderboard) also carry `ProvenanceMeta`:

```ts
interface ProvenanceMeta {
  provenance: Provenance;
  generatedAt: string;
  sourceId?: string;
  eventSnapshotId?: string;
}
```

---

## Domain Types

See `src/data/types.ts` for full type definitions. Key types:

- `Provenance` — 6 values (OFFICIAL_EVENT_STATE | OFFICIAL_EVENT_DATA | OFFICIAL_PLATFORM_OBSERVATION | LOCAL_EXPERIMENT | SYNTHETIC_FIXTURE | MANUALLY_RECORDED)
- `RaceDecision` — 12 values covering promotion, retention, retirement, failure, invalidity
- `StepStatus` — NOT_STARTED | RUNNING | PASS | FAIL | BLOCKED | RETRYABLE
- `StakingData.classification` — VIRTUAL_EVENT_BALANCE | REAL_USDC | NO_STAKING | UNKNOWN

---

## Chart Dependencies

- **`recharts`** — LineChart, BarChart, ScatterChart, PieChart (standard charts)
- **`src/components/Heatmap.tsx`** — custom SVG/CSS-grid heatmap (prediction correlations, round×model matrix, fold matrices)
- **`src/data/chartTokens.ts`** — shared chart palette (`CHART`, `CHART_SERIES`, `STAGE_COLOR`)

---

## Font Dependencies

Google Fonts loaded via CSS `@import` in `src/index.css`:

| Family | Weights | Usage |
|---|---|---|
| Montserrat | 400, 500, 600, 700 | Nav labels, headings, table headers |
| Raleway | 400, 500, 600, 700 | Section titles, page headers |
| JetBrains Mono | 400, 500, 600 | All data values, hashes, status codes |

**Production packaging note:** The Cursor integration should self-host these fonts (download and serve as static assets or bundle via font tooling) so the event-day console has no runtime Google Fonts dependency. The visual appearance must remain equivalent to this export.

---

## localStorage Keys

| Key | Value | Purpose |
|---|---|---|
| `qs_sidebar_collapsed` | `"true"` / `"false"` | Sidebar collapse state |

---

## Demo / API Mode

Controlled by `VITE_DATA_MODE` environment variable:

- `VITE_DATA_MODE=demo` (default) → `DemoDataSource` — all data is `SYNTHETIC_FIXTURE`, clearly labelled
- `VITE_DATA_MODE=api` → `ApiDataSource` — connects to `VITE_API_BASE` URL

**Critical:** There is no automatic fallback from API to demo. Backend failure shows `BACKEND UNAVAILABLE`. A backend outage must never silently produce plausible-looking synthetic event data.

---

## CommandPalette

Opened with `Ctrl+K` / `Cmd+K`. Contains:
- Navigation to all 15 routes
- 9 allowlisted action commands calling `DataSource` methods
- No free-text shell execution

---

## Known Implementation Limitations

1. **Submission stepper demo:** The stepper advances sequentially through all PASS states. A real implementation should wire each step to actual SDK calls.
2. **Autopilot state:** Stored locally in `EventControl` component state. Production should sync with backend.
3. **Activity strip:** Shows static rotating messages. Production should poll `getComputeJobs()` and `getRoundRoom()`.
4. **TopBar:** Shows static synthetic values. Production should call `getEventControl()` and `getRoundRoom()` on mount and refresh.
5. **CommandPalette action results:** Shown inline. Production may want a global toast/notification system.
6. **Experiment drawer lineage:** Shows flat field values. Production could render a lineage tree.
7. **Heatmap max size:** Currently unbounded — very large matrices may need virtualization.
