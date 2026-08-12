# Architecture

Repository:
`quantsilico-everesteer-hedge-fund-hackathon-2026`

This is event-specific.

## Critical path

```text
qseh CLI / autopilot
        |
        +-- Everesteer adapter
        |     +-- capability discovery
        |     +-- event snapshots
        |     +-- split pull
        |     +-- leaderboard/standings
        |
        +-- data audit/fingerprint
        |
        +-- organiser scorer
        |
        +-- experiment runner
        |     +-- OOF
        |     +-- manifests
        |     +-- models
        |
        +-- racing scheduler
        |
        +-- Pareto frontier
        |
        +-- ensemble
        |
        +-- submission quota + integrity guard
        |
        +-- live-round controller
        |
        `-- stake-mode classifier/recommender
```

Filesystem manifests are authoritative.
DuckDB/SQLite is only a rebuildable dashboard index.

## Provenance

Every record:
- OFFICIAL_EVENT_STATE
- OFFICIAL_EVENT_DATA
- OFFICIAL_PLATFORM_OBSERVATION
- LOCAL_EXPERIMENT
- SYNTHETIC_FIXTURE
- MANUALLY_RECORDED

## Dashboard

Reuse the Generals pattern:

```text
Figma Make frontend
   -> DataSource interface
      -> ApiDataSource
         -> FastAPI 127.0.0.1
            -> manifests / registry / allowlisted jobs / event adapter
```

CLI remains usable when dashboard dies.

No arbitrary shell strings.
No arbitrary file paths.
No Git mutations.
No secrets.
No real-wallet transaction API.

## Local concurrency

Default:
- 1 main local experiment worker;
- event watcher;
- dashboard;
- optional remote/server compute.

This keeps laptop memory/GPU predictable.

## Research state

`runs/state/research_state.json`

Contains:
- current event snapshot;
- time remaining;
- upload budget;
- frontier;
- champion;
- ensemble;
- correlations;
- live evidence;
- saturated branches;
- pending operators.

External AI can reason from this compact state.

## Windows

Primary launch UX should include `.cmd` wrappers:
- `start.cmd`
- `stop.cmd`
- `status.cmd`
- `open.cmd`

They may invoke PowerShell with process-local bypass, never global execution-policy changes.

## Public/private

Public:
- source;
- docs;
- synthetic fixture generator;
- generic configs;
- tests;
- design.

Ignored/private:
- keys;
- organiser data;
- live predictions;
- model pickles;
- private configs;
- event/leaderboard snapshots if strategically sensitive;
- wallet/staking secrets.
