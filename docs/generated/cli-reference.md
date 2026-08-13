---
title: CLI Reference
description: Generated from the current qseh Typer command tree.
source: generated
generatedFromSha: 0b0fe69f467df29751a6e316ad852083503d48b6
generatedAt: 2026-08-13T11:38:41+00:00
---

# CLI Reference

Generated from commit `0b0fe69f467df29751a6e316ad852083503d48b6`.

Authoritative source: the live Typer command tree (`qseh docs build`).

Do not maintain a handwritten second command inventory.

## `qseh autopilot`

Deterministic competition autopilot (no LLM).

```text
Usage: qseh autopilot [OPTIONS]
```

Subcommands: `run`, `status`, `stop`.

## `qseh autopilot run`

Advance the persisted autopilot workflow (never auto-arms submissions).

```text
Usage: qseh autopilot run [OPTIONS]
```

### Options

| Option | Required | Default | Meaning |
| --- | --- | --- | --- |
| --profile | no | competition-aggressive | Autopilot profile name. |
| --max-steps | no |  | Optional step cap (default: run until COMPLETE). |

## `qseh autopilot status`

Show autopilot stage / history from research state.

```text
Usage: qseh autopilot status [OPTIONS]
```

## `qseh autopilot stop`

Deactivate autopilot without erasing history.

```text
Usage: qseh autopilot stop [OPTIONS]
```

## `qseh baseline`

Baseline / scorer tooling.

```text
Usage: qseh baseline [OPTIONS]
```

Subcommands: `reproduce`, `scorer-parity`.

## `qseh baseline reproduce`

Fit the independent reference_lgbm baseline.

```text
Usage: qseh baseline reproduce [OPTIONS]
```

### Options

| Option | Required | Default | Meaning |
| --- | --- | --- | --- |
| --data | no |  | Training parquet (default: synthetic train). |

## `qseh baseline scorer-parity`

Compare expected vs observed predictions; list official scorer availability.

```text
Usage: qseh baseline scorer-parity [OPTIONS]
```

### Options

| Option | Required | Default | Meaning |
| --- | --- | --- | --- |
| --expected | no |  | Expected prediction column/file. |
| --observed | no |  | Observed prediction column/file. |
| --column | no | prediction |  |

## `qseh champion`

Show or set the research champion candidate.

```text
Usage: qseh champion [OPTIONS]
```

### Options

| Option | Required | Default | Meaning |
| --- | --- | --- | --- |
| --set | no |  | Promote a candidate id to champion (omit to show current). |

## `qseh compare`

Compare experiment run metrics under runs/experiments/.

```text
Usage: qseh compare [OPTIONS]
```

## `qseh dashboard`

Local dashboard on 127.0.0.1:8766.

```text
Usage: qseh dashboard [OPTIONS]
```

Subcommands: `build`, `diagnose`, `open`, `start`, `status`, `stop`.

## `qseh dashboard build`

Build the Figma frontend production bundle.

```text
Usage: qseh dashboard build [OPTIONS]
```

### Options

| Option | Required | Default | Meaning |
| --- | --- | --- | --- |
| --clean | no | False | Force pnpm install --frozen-lockfile before build. |

## `qseh dashboard diagnose`

Print venue-ready dashboard diagnostics (no secrets).

```text
Usage: qseh dashboard diagnose [OPTIONS]
```

## `qseh dashboard open`

Open the dashboard URL only when healthy.

```text
Usage: qseh dashboard open [OPTIONS]
```

### Options

| Option | Required | Default | Meaning |
| --- | --- | --- | --- |
| --start | no | False | Start the dashboard first if it is not healthy. |

## `qseh dashboard start`

Start FastAPI/Uvicorn; success requires live process + /api/health.

```text
Usage: qseh dashboard start [OPTIONS]
```

## `qseh dashboard status`

Authoritative dashboard lifecycle status (single source of truth).

```text
Usage: qseh dashboard status [OPTIONS]
```

## `qseh dashboard stop`

Stop the qseh-owned dashboard process; never kill foreign :8766 owners.

```text
Usage: qseh dashboard stop [OPTIONS]
```

## `qseh data`

Dataset pull, audit, and fingerprinting.

```text
Usage: qseh data [OPTIONS]
```

Subcommands: `audit`, `fingerprint`, `pull`.

## `qseh data audit`

Run structural integrity audit on a Parquet/CSV dataset.

```text
Usage: qseh data audit [OPTIONS]
```

### Options

| Option | Required | Default | Meaning |
| --- | --- | --- | --- |
| path | no |  | Dataset path (default: synthetic train.parquet). |

## `qseh data fingerprint`

Content + schema fingerprint for a dataset file.

```text
Usage: qseh data fingerprint [OPTIONS]
```

### Options

| Option | Required | Default | Meaning |
| --- | --- | --- | --- |
| path | no |  | Dataset path (default: synthetic train.parquet). |

## `qseh data pull`

Pull a split; uses synthetic fixtures when creds missing or QSEH_SYNTHETIC=1.

```text
Usage: qseh data pull [OPTIONS]
```

### Options

| Option | Required | Default | Meaning |
| --- | --- | --- | --- |
| --split | yes |  | Dataset split: train \| validation \| live |
| --dest | no |  | Destination file or directory (default: data/<split>.parquet). |

## `qseh docs`

Generate documentation from live code.

```text
Usage: qseh docs [OPTIONS]
```

Subcommands: `build`.

## `qseh docs build`

Write docs/generated/ and dashboard frontend docs-manifest.json.

```text
Usage: qseh docs build [OPTIONS]
```

## `qseh doctor`

Check Python, everestapi, disk, optional GPU, and repo paths.

```text
Usage: qseh doctor [OPTIONS]
```

## `qseh emergency`

Disarm submissions, stop autopilot, snapshot event.

```text
Usage: qseh emergency [OPTIONS]
```

### Options

| Option | Required | Default | Meaning |
| --- | --- | --- | --- |
| --send | no | False | Queue a local alert marker (no secrets). |

## `qseh ensemble`

Ensemble blending.

```text
Usage: qseh ensemble [OPTIONS]
```

Subcommands: `build`, `compare`.

## `qseh ensemble build`

Build a blend from available experiment OOF predictions.

```text
Usage: qseh ensemble build [OPTIONS]
```

### Options

| Option | Required | Default | Meaning |
| --- | --- | --- | --- |
| --strategy | no | rank_average | rank_average\|greedy_forward |
| --out | no |  | Blend manifest path. |

## `qseh ensemble compare`

List persisted blend manifests under artifacts/ensembles/.

```text
Usage: qseh ensemble compare [OPTIONS]
```

## `qseh event`

Event control and submission arming.

```text
Usage: qseh event [OPTIONS]
```

Subcommands: `arm-submissions`, `disarm-submissions`, `inspect`, `snapshot`, `submission-mode`, `watch`.

## `qseh event arm-submissions`

Explicitly arm real uploads (requires a current event snapshot id).

```text
Usage: qseh event arm-submissions [OPTIONS]
```

### Options

| Option | Required | Default | Meaning |
| --- | --- | --- | --- |
| --snapshot-id | no |  | Event snapshot id required to arm (defaults to latest / state). |

## `qseh event disarm-submissions`

Return to DRY_RUN (safe default).

```text
Usage: qseh event disarm-submissions [OPTIONS]
```

## `qseh event inspect`

Capability-detecting event inspection (never invents quotas/standings).

```text
Usage: qseh event inspect [OPTIONS]
```

## `qseh event snapshot`

Write an event capability snapshot under runs/event/.

```text
Usage: qseh event snapshot [OPTIONS]
```

## `qseh event submission-mode`

Show or set submission operating mode.

```text
Usage: qseh event submission-mode [OPTIONS]
```

### Options

| Option | Required | Default | Meaning |
| --- | --- | --- | --- |
| mode | no |  | Optional mode to set: DISABLED \| DRY_RUN \| ARMED. Omit to print current. |
| --snapshot-id | no |  | Required when setting ARMED. |

## `qseh event watch`

Poll current round / deadline using server-observed time when available.

```text
Usage: qseh event watch [OPTIONS]
```

### Options

| Option | Required | Default | Meaning |
| --- | --- | --- | --- |
| --interval / -i | no | 5.0 | Seconds between polls. |
| --once | no | False | Single poll then exit. |
| --tick-round | no | False | Advance one RoundController cycle (detect→pull→guard→submit path). |

## `qseh frontier`

Compute Pareto frontier (max score, min runtime).

```text
Usage: qseh frontier [OPTIONS]
```

### Options

| Option | Required | Default | Meaning |
| --- | --- | --- | --- |
| --score-key | no | score |  |
| --runtime-key | no | runtime_seconds |  |

## `qseh leaderboard`

Fetch official leaderboard when available (never invent ranks).

```text
Usage: qseh leaderboard [OPTIONS]
```

## `qseh race`

Successive-halving race over known experiment candidates.

```text
Usage: qseh race [OPTIONS]
```

### Options

| Option | Required | Default | Meaning |
| --- | --- | --- | --- |
| --profile | no | fast | Race profile: fast \| standard |
| --stage | no | R0 | Racing stage R0–R3. |

## `qseh rehearsal`

Synthetic end-to-end rehearsal (works without dashboard/LLM).

```text
Usage: qseh rehearsal [OPTIONS]
```

## `qseh run`

Run a persisted temporal experiment from a YAML config.

```text
Usage: qseh run [OPTIONS]
```

### Options

| Option | Required | Default | Meaning |
| --- | --- | --- | --- |
| config | yes |  | YAML experiment config path. |
| --sync | no | True | Run via in-process job worker (default) or enqueue only. |

## `qseh sdk`

everestapi SDK inspection.

```text
Usage: qseh sdk [OPTIONS]
```

Subcommands: `check`, `info`.

## `qseh sdk check`

Probe SDK client connectivity / capability discovery.

```text
Usage: qseh sdk check [OPTIONS]
```

## `qseh sdk info`

Show installed everestapi version and adapter fingerprint (never the key).

```text
Usage: qseh sdk info [OPTIONS]
```

## `qseh stake`

Stake classification (no real transfers).

```text
Usage: qseh stake [OPTIONS]
```

Subcommands: `recommend`, `status`.

## `qseh stake recommend`

Recommend allocations. Real-money modes always require human action.

```text
Usage: qseh stake recommend [OPTIONS]
```

### Options

| Option | Required | Default | Meaning |
| --- | --- | --- | --- |
| --profile | no | aggressive |  |

## `qseh stake status`

Classify current stake mode from event capabilities (never invent balances).

```text
Usage: qseh stake status [OPTIONS]
```

## `qseh standings`

Fetch diagnostics standings when available.

```text
Usage: qseh standings [OPTIONS]
```

## `qseh submissions`

List local submission artefacts / idempotency ledger entries.

```text
Usage: qseh submissions [OPTIONS]
```

## `qseh submit`

Submission guard and upload pipeline.

```text
Usage: qseh submit [OPTIONS]
```

Subcommands: `check`, `live`, `practice`.

## `qseh submit check`

Run SubmissionGuard without uploading.

```text
Usage: qseh submit check [OPTIONS]
```

### Options

| Option | Required | Default | Meaning |
| --- | --- | --- | --- |
| --predictions | no |  |  |
| --lane | no | practice |  |
| --candidate | no | champion |  |
| --round | no |  |  |

## `qseh submit live`

Live event submit respecting DISABLED/DRY_RUN/ARMED (+ guard).

```text
Usage: qseh submit live [OPTIONS]
```

### Options

| Option | Required | Default | Meaning |
| --- | --- | --- | --- |
| --predictions | no |  |  |
| --candidate | no | champion |  |
| --round | no |  |  |

## `qseh submit practice`

Practice/diagnostics submit respecting DISABLED/DRY_RUN/ARMED.

```text
Usage: qseh submit practice [OPTIONS]
```

### Options

| Option | Required | Default | Meaning |
| --- | --- | --- | --- |
| --predictions | no |  |  |
| --candidate | no | champion |  |
| --round | no |  |  |

