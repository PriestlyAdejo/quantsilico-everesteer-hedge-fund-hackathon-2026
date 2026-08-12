# qseh CLI reference (generated)

Generated at `2026-08-12T05:11:44+00:00`.

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
| `qseh dashboard start` | Start FastAPI backend via uvicorn on 127.0.0.1:8766. |
| `qseh dashboard status` | Health / PID status for the local dashboard. |
| `qseh dashboard open` | Open the dashboard URL in the default browser. |
| `qseh dashboard stop` | Stop the dashboard process recorded in runs/state/dashboard.pid. |
| `qseh docs` | Generate docs stubs / frontend manifest. |
| `qseh docs build` | Write docs/generated/ and dashboard frontend docs-manifest.json. |
