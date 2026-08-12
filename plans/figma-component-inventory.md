# Figma component inventory

Reachable graph from `src/main.tsx` → `App.tsx` → `createBrowserRouter` → `Shell`.

## Shell

| Component | Role |
|---|---|
| `Shell` | Layout: TopBar + Sidebar + Outlet + ActivityStrip + CommandPalette |
| `TopBar` | Event status (poll `getEventStatus`) |
| `Sidebar` | Grouped nav OPERATE / RESEARCH / COMPETE / SYSTEM |
| `ActivityStrip` | Job activity (poll `getComputeJobs`) |
| `CommandPalette` | Ctrl/Cmd+K allowlisted actions |

## Shared UI

`Panel`, `PageHeader`, `Drawer`, `Heatmap`, `JobTiming`, `ProvenanceBadge`, `StatusPage`, `Tip`

## Pages → DataSource

| Route | Page | Reads | Actions |
|---|---|---|---|
| `/` | Overview | `getOverview` | — |
| `/event` | EventControl | `getEventControl` | refresh/snapshot/pull/parity/baseline/autopilot |
| `/round` | RoundRoom | `getRoundRoom` | — |
| `/data` | DataLab | `getDataLab` | — |
| `/experiments` | Experiments | `getExperiments` | — |
| `/validation` | Validation | `getValidation` | — |
| `/models` | Models | `getModels` | — |
| `/features` | FeatureLab | `getFeatureLab` | — |
| `/ensembles` | Ensembles | `getEnsembles` | build/save/promote |
| `/leaderboard` | Leaderboard | `getLeaderboard` | — |
| `/submission` | Submission | `getSubmission` | validate/practice/live |
| `/staking` | Staking | `getStaking` | — |
| `/compute` | ComputeJobs | `getComputeJobs` | `stopJob` |
| `/repository` | Repository | `getRepository` | — |
| `/docs` | Documentation | `getDocumentation` | — |

## Contract freeze

Authoritative TypeScript: `contracts/figma/data/types.ts`  
Authoritative HTTP map: `contracts/figma/data/api.ts`  
Python mirrors: `src/qs_everesteer/api_schemas/`
