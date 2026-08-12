# qseh CLI reference (generated)

Generated at `2026-08-12T13:02:08+00:00`.
generatedFromSha: `6e8f61695c1d3e55cb5e4ac54133d73b00b858ae`.

Authoritative source: live Typer command tree (`qseh docs build`).

| Command | Help |
|---|---|
| `qseh doctor` | Check Python, everestapi, disk, optional GPU, and repo paths. |
| `qseh rehearsal` | Synthetic end-to-end rehearsal (works without dashboard/LLM). |
| `qseh emergency` | Disarm submissions, stop autopilot, snapshot event. |
| `qseh run` | Run a persisted temporal experiment from a YAML config. |
| `qseh race` | Successive-halving race over known experiment candidates. |
| `qseh compare` | Compare experiment run metrics under runs/experiments/. |
| `qseh frontier` | Compute Pareto frontier (max score, min runtime). |
| `qseh champion` | Show or set the research champion candidate. |
| `qseh submissions` | List local submission artefacts / idempotency ledger entries. |
| `qseh leaderboard` | Fetch official leaderboard when available (never invent ranks). |
| `qseh standings` | Fetch diagnostics standings when available. |
| `qseh sdk` | everestapi SDK inspection. |
| `qseh sdk info` | Show installed everestapi version and adapter fingerprint (never the key). |
| `qseh sdk check` | Probe SDK client connectivity / capability discovery. |
| `qseh event` | Event control and submission arming. |
| `qseh event inspect` | Capability-detecting event inspection (never invents quotas/standings). |
| `qseh event watch` | Poll current round / deadline using server-observed time when available. |
| `qseh event snapshot` | Write an event capability snapshot under runs/event/. |
| `qseh event arm-submissions` | Explicitly arm real uploads (requires a current event snapshot id). |
| `qseh event disarm-submissions` | Return to DRY_RUN (safe default). |
| `qseh event submission-mode` | Show or set submission operating mode. |
| `qseh data` | Dataset pull, audit, and fingerprinting. |
| `qseh data pull` | Pull a split; uses synthetic fixtures when creds missing or QSEH_SYNTHETIC=1. |
| `qseh data audit` | Run structural integrity audit on a Parquet/CSV dataset. |
| `qseh data fingerprint` | Content + schema fingerprint for a dataset file. |
| `qseh baseline` | Baseline / scorer tooling. |
| `qseh baseline scorer-parity` | Compare expected vs observed predictions; list official scorer availability. |
| `qseh baseline reproduce` | Fit the independent reference_lgbm baseline. |
| `qseh ensemble` | Ensemble blending. |
| `qseh ensemble build` | Build a blend from available experiment OOF predictions. |
| `qseh ensemble compare` | List persisted blend manifests under artifacts/ensembles/. |
| `qseh submit` | Submission guard and upload pipeline. |
| `qseh submit check` | Run SubmissionGuard without uploading. |
| `qseh submit practice` | Practice/diagnostics submit respecting DISABLED/DRY_RUN/ARMED. |
| `qseh submit live` | Live event submit respecting DISABLED/DRY_RUN/ARMED (+ guard). |
| `qseh stake` | Stake classification (no real transfers). |
| `qseh stake status` | Classify current stake mode from event capabilities (never invent balances). |
| `qseh stake recommend` | Recommend allocations. Real-money modes always require human action. |
| `qseh autopilot` | Deterministic competition autopilot (no LLM). |
| `qseh autopilot status` | Show autopilot stage / history from research state. |
| `qseh autopilot run` | Advance the persisted autopilot workflow (never auto-arms submissions). |
| `qseh autopilot stop` | Deactivate autopilot without erasing history. |
| `qseh dashboard` | Local dashboard on 127.0.0.1:8766. |
| `qseh dashboard start` | Start FastAPI/Uvicorn; success requires live process + /api/health. |
| `qseh dashboard status` | Authoritative dashboard lifecycle status (single source of truth). |
| `qseh dashboard stop` | Stop the qseh-owned dashboard process; never kill foreign :8766 owners. |
| `qseh dashboard open` | Open the dashboard URL only when healthy. |
| `qseh dashboard diagnose` | Print venue-ready dashboard diagnostics (no secrets). |
| `qseh dashboard build` | Build the Figma frontend production bundle. |
| `qseh docs` | Generate docs stubs / frontend manifest. |
| `qseh docs build` | Write docs/generated/ and dashboard frontend docs-manifest.json. |

## Options and arguments

### `qseh emergency`

| Name | Kind | Default | Help |
|---|---|---|---|
| `--send` | option | `False` | Queue a local alert marker (no secrets). |

### `qseh run`

| Name | Kind | Default | Help |
|---|---|---|---|
| `config` | argument | `` | YAML experiment config path. |
| `--sync/--async` | option | `True` | Run via in-process job worker (default) or enqueue only. |

### `qseh race`

| Name | Kind | Default | Help |
|---|---|---|---|
| `--profile` | option | `fast` | Race profile: fast \| standard |
| `--stage` | option | `R0` | Racing stage R0–R3. |

### `qseh frontier`

| Name | Kind | Default | Help |
|---|---|---|---|
| `--score-key` | option | `score` |  |
| `--runtime-key` | option | `runtime_seconds` |  |

### `qseh champion`

| Name | Kind | Default | Help |
|---|---|---|---|
| `--set` | option | `` | Promote a candidate id to champion (omit to show current). |

### `qseh event watch`

| Name | Kind | Default | Help |
|---|---|---|---|
| `--interval / -i` | option | `5.0` | Seconds between polls. |
| `--once` | option | `False` | Single poll then exit. |
| `--tick-round` | option | `False` | Advance one RoundController cycle (detect→pull→guard→submit path). |

### `qseh event arm-submissions`

| Name | Kind | Default | Help |
|---|---|---|---|
| `--snapshot-id` | option | `` | Event snapshot id required to arm (defaults to latest / state). |

### `qseh event submission-mode`

| Name | Kind | Default | Help |
|---|---|---|---|
| `mode` | argument | `` | Optional mode to set: DISABLED \| DRY_RUN \| ARMED. Omit to print current. |
| `--snapshot-id` | option | `` | Required when setting ARMED. |

### `qseh data pull`

| Name | Kind | Default | Help |
|---|---|---|---|
| `--split` | option | `` | Dataset split: train \| validation \| live |
| `--dest` | option | `` | Destination file or directory (default: data/<split>.parquet). |

### `qseh data audit`

| Name | Kind | Default | Help |
|---|---|---|---|
| `path` | argument | `` | Dataset path (default: synthetic train.parquet). |

### `qseh data fingerprint`

| Name | Kind | Default | Help |
|---|---|---|---|
| `path` | argument | `` | Dataset path (default: synthetic train.parquet). |

### `qseh baseline scorer-parity`

| Name | Kind | Default | Help |
|---|---|---|---|
| `--expected` | option | `` | Expected prediction column/file. |
| `--observed` | option | `` | Observed prediction column/file. |
| `--column` | option | `prediction` |  |

### `qseh baseline reproduce`

| Name | Kind | Default | Help |
|---|---|---|---|
| `--data` | option | `` | Training parquet (default: synthetic train). |

### `qseh ensemble build`

| Name | Kind | Default | Help |
|---|---|---|---|
| `--strategy` | option | `rank_average` | rank_average\|greedy_forward |
| `--out` | option | `` | Blend manifest path. |

### `qseh submit check`

| Name | Kind | Default | Help |
|---|---|---|---|
| `--predictions` | option | `` |  |
| `--lane` | option | `practice` |  |
| `--candidate` | option | `champion` |  |
| `--round` | option | `` |  |

### `qseh submit practice`

| Name | Kind | Default | Help |
|---|---|---|---|
| `--predictions` | option | `` |  |
| `--candidate` | option | `champion` |  |
| `--round` | option | `` |  |

### `qseh submit live`

| Name | Kind | Default | Help |
|---|---|---|---|
| `--predictions` | option | `` |  |
| `--candidate` | option | `champion` |  |
| `--round` | option | `` |  |

### `qseh stake recommend`

| Name | Kind | Default | Help |
|---|---|---|---|
| `--profile` | option | `aggressive` |  |

### `qseh autopilot run`

| Name | Kind | Default | Help |
|---|---|---|---|
| `--profile` | option | `competition-aggressive` | Autopilot profile name. |
| `--max-steps` | option | `` | Optional step cap (default: run until COMPLETE). |

### `qseh dashboard open`

| Name | Kind | Default | Help |
|---|---|---|---|
| `--start` | option | `False` | Start the dashboard first if it is not healthy. |

### `qseh dashboard build`

| Name | Kind | Default | Help |
|---|---|---|---|
| `--clean` | option | `False` | Force pnpm install --frozen-lockfile before build. |

