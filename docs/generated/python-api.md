# Python API reference (generated)

Generated at `2026-08-12T13:02:09+00:00`.

Public entry points intended for event-day tooling. Private helpers are omitted.

## `qs_everesteer.hardware.probe.probe_hardware`

`probe_hardware() -> 'HardwareProbe'`

Probe local OS, CPU, and NVIDIA GPU (best-effort, never raises).

## `qs_everesteer.state.research.load_research_state`

`load_research_state(repo_root: 'str | Path | None' = None) -> 'dict[str, Any]'`

Load state under lock; create defaults if the file is missing.

## `qs_everesteer.state.research.update_research_state`

`update_research_state(mutator: 'Callable[[dict[str, Any]], None]', repo_root: 'str | Path | None' = None) -> 'dict[str, Any]'`

Load-modify-save under a single lock hold.

## `qs_everesteer.event.adapter.EveresteerAdapter`

`EveresteerAdapter(self, *, api_key: 'str | None' = None, base_url: 'str | None' = None, tournament: 'str' = 'futures', synthetic: 'bool | None' = None, client: 'Any | None' = None, feed: 'SimulatedEventFeed | None' = None) -> 'None'`

Capability-discovering Everesteer / everestapi adapter.

## `qs_everesteer.experiments.runner.ExperimentRunner`

`ExperimentRunner(self, repo_root: 'str | Path | None' = None) -> 'None'`

Config -> model -> OOF -> metrics -> artefacts -> immutable manifest.

## `qs_everesteer.experiments.racing.RacingScheduler`

`RacingScheduler(self, *, keep_fraction: 'float' = 0.5, min_survivors: 'int' = 1) -> 'None'`

## `qs_everesteer.docs_build.build_docs`

`build_docs(repo_root: 'str | Path | None' = None, *, app: 'Any | None' = None) -> 'dict[str, Path]'`

Write docs/generated/ artefacts and dashboard frontend docs-manifest.json.

## `qs_everesteer.dashboard.process.DashboardProcessManager`

`DashboardProcessManager(self, repo_root: 'str | Path | None' = None) -> 'None'`

Single authority for Research Console start/status/stop/open/diagnose.

## `qs_everesteer.ops_status.write_ops_status`

`write_ops_status(filename: 'str', *, status: 'StatusLiteral', detail: 'str', repo_root: 'str | Path | None' = None, extra: 'dict[str, Any] | None' = None) -> 'Path'`

Write a small JSON status file under runs/state/.

## `qs_everesteer.gitmeta.git_head_sha`

`git_head_sha(root: 'Path') -> 'str | None'`

