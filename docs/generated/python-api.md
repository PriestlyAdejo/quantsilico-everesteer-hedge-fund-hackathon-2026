---
title: Python API
description: Generated from public project signatures and docstrings.
source: generated
generatedFromSha: 65828f1669f73fa7428a854ca927ef05e038cb3e
generatedAt: 2026-08-13T14:19:03+00:00
---

# Python API

Generated from commit `65828f1669f73fa7428a854ca927ef05e038cb3e`.

Intended public interfaces only. Private helpers (`_name`) are omitted.

Missing docstrings are reported as `MISSING DOCSTRING` rather than invented.

## `qs_everesteer.event.adapter.EveresteerAdapter`

`EveresteerAdapter(self, *, api_key: 'str | None' = None, base_url: 'str | None' = None, tournament: 'str' = 'futures', synthetic: 'bool | None' = None, client: 'Any | None' = None, feed: 'SimulatedEventFeed | None' = None) -> 'None'`

Capability-discovering Everesteer / everestapi adapter.

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| api_key | no | None | str \| None |
| base_url | no | None | str \| None |
| tournament | no | 'futures' | str |
| synthetic | no | None | bool \| None |
| client | no | None | Any \| None |
| feed | no | None | SimulatedEventFeed \| None |

Returns: `None`

## `qs_everesteer.event.adapter.EveresteerAdapter.inspect`

`inspect(self) -> 'dict[str, Any]'`

Return EventCapabilities-like dict plus connection status.

Missing methods / failed probes become structured UNAVAILABLE / null —
never fabricated zeros for quotas or standings.

Returns: `dict[str, Any]`

## `qs_everesteer.event.adapter.EveresteerAdapter.pull_split`

`pull_split(self, split: 'str', dest: 'str | Path', *, repo_root: 'str | Path | None' = None) -> 'Path'`

Download a dataset split to *dest*.

When credentials / SDK are unavailable and ``QSEH_SYNTHETIC=1`` (or
``synthetic=True``), copies/generates a synthetic fixture instead.

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| split | yes |  | str |
| dest | yes |  | str \| Path |
| repo_root | no | None | str \| Path \| None |

Returns: `Path`

## `qs_everesteer.event.adapter.EveresteerAdapter.safe_key_fingerprint`

`safe_key_fingerprint(self) -> 'str | None'`

MISSING DOCSTRING

Returns: `str | None`

## `qs_everesteer.event.adapter.EveresteerAdapter.sdk_version`

`sdk_version(self) -> 'str'`

MISSING DOCSTRING

Returns: `str`

## `qs_everesteer.event.adapter.EveresteerAdapter.snapshot`

`snapshot(self, repo_root: 'str | Path | None' = None) -> 'dict[str, Any]'`

Inspect capabilities and write ``runs/event/event_snapshot_<ts>.json``.

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| repo_root | no | None | str \| Path \| None |

Returns: `dict[str, Any]`

## `qs_everesteer.event.adapter.EveresteerAdapter.submit_predictions`

`submit_predictions(self, *, model_id: 'str', predictions_path: 'str | Path', lane: 'str' = 'practice', model_pkl: 'str | Path | None' = None, target: 'str' = 'target_everest_20', **kwargs: 'Any') -> 'dict[str, Any]'`

Real upload path (practice diagnostics or live event).

Callers must gate this behind ARMED mode + SubmissionGuard. This method
never auto-arms and never runs in synthetic mode.

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| model_id | yes |  | str |
| predictions_path | yes |  | str \| Path |
| lane | no | 'practice' | str |
| model_pkl | no | None | str \| Path \| None |
| target | no | 'target_everest_20' | str |
| kwargs | yes |  | Any |

Returns: `dict[str, Any]`

## `qs_everesteer.event.adapter.sdk_version`

`sdk_version() -> 'str'`

Return installed everestapi version string, or UNKNOWN.

Returns: `str`

## `qs_everesteer.data.audit.audit_dataset`

`audit_dataset(path: 'str | Path') -> 'DatasetAudit'`

Run structural integrity checks on a Parquet/CSV dataset.

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| path | yes |  | str \| Path |

Returns: `DatasetAudit`

## `qs_everesteer.data.fingerprint.fingerprint_dataset`

`fingerprint_dataset(path: 'str | Path') -> 'dict[str, Any]'`

Return content hash + schema fingerprint (+ column inventory).

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| path | yes |  | str \| Path |

Returns: `dict[str, Any]`

## `qs_everesteer.validation.scoring.official_scorers`

`official_scorers() -> 'dict[str, Callable[..., Any]]'`

MISSING DOCSTRING

Returns: `dict[str, Callable[..., Any]]`

## `qs_everesteer.validation.temporal.temporal_cv`

`temporal_cv(frame: 'pd.DataFrame', model_factory: 'Callable[[], Any]', *, features: 'list[str]', target: 'str', exped_col: 'str' = 'exped', profile: 'str | FoldProfile' = 'R1', sample_weight_fn: 'Callable[[Any], Any] | None' = None, enforce_target_horizon: 'bool' = True) -> 'tuple[pd.DataFrame, dict[str, Any]]'`

MISSING DOCSTRING

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| frame | yes |  | pd.DataFrame |
| model_factory | yes |  | Callable[[], Any] |
| features | yes |  | list[str] |
| target | yes |  | str |
| exped_col | no | 'exped' | str |
| profile | no | 'R1' | str \| FoldProfile |
| sample_weight_fn | no | None | Callable[[Any], Any] \| None |
| enforce_target_horizon | no | True | bool |

Returns: `tuple[pd.DataFrame, dict[str, Any]]`

## `qs_everesteer.validation.temporal.TemporalSplitter`

`TemporalSplitter(self, profile: 'str | FoldProfile' = 'R1') -> 'None'`

MISSING DOCSTRING

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| profile | no | 'R1' | str \| FoldProfile |

Returns: `None`

## `qs_everesteer.validation.temporal.TemporalSplitter.get_n_splits`

`get_n_splits(self, data=None, groups=None) -> 'int'`

MISSING DOCSTRING

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| data | no | None |  |
| groups | no | None |  |

Returns: `int`

## `qs_everesteer.validation.temporal.TemporalSplitter.split`

`split(self, data, groups=None) -> 'Iterator[tuple[np.ndarray, np.ndarray]]'`

MISSING DOCSTRING

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| data | yes |  |  |
| groups | no | None |  |

Returns: `Iterator[tuple[np.ndarray, np.ndarray]]`

## `qs_everesteer.experiments.runner.ExperimentRunner`

`ExperimentRunner(self, repo_root: 'str | Path | None' = None) -> 'None'`

Config -> model -> OOF -> metrics -> artefacts -> immutable manifest.

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| repo_root | no | None | str \| Path \| None |

Returns: `None`

## `qs_everesteer.experiments.runner.ExperimentRunner.run`

`run(self, config_path: 'str | Path | dict[str, Any]') -> 'dict[str, Any]'`

MISSING DOCSTRING

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| config_path | yes |  | str \| Path \| dict[str, Any] |

Returns: `dict[str, Any]`

## `qs_everesteer.experiments.runner.ExperimentRunner.run_promoted_child`

`run_promoted_child(self, parent_run_id: 'str', next_stage: 'str') -> 'dict[str, Any]'`

Retrain a promoted parent at the next evidence stage with lineage.

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| parent_run_id | yes |  | str |
| next_stage | yes |  | str |

Returns: `dict[str, Any]`

## `qs_everesteer.experiments.racing.RacingScheduler`

`RacingScheduler(self, *, keep_fraction: 'float' = 0.5, min_survivors: 'int' = 1) -> 'None'`

MISSING DOCSTRING

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| keep_fraction | no | 0.5 | float |
| min_survivors | no | 1 | int |

Returns: `None`

## `qs_everesteer.experiments.racing.RacingScheduler.child_configs`

`child_configs(outcomes: 'list[RaceOutcome]', *, repo_root: 'str | Path', target_stage: 'str') -> 'list[dict[str, Any]]'`

Build real retraining configs for promoted parents, preserving lineage.

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| outcomes | yes |  | list[RaceOutcome] |
| repo_root | yes |  | str \| Path |
| target_stage | yes |  | str |

Returns: `list[dict[str, Any]]`

## `qs_everesteer.experiments.racing.RacingScheduler.evaluate`

`evaluate(self, records: 'list[dict[str, Any]]', stage: 'str') -> 'list[RaceOutcome]'`

MISSING DOCSTRING

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| records | yes |  | list[dict[str, Any]] |
| stage | yes |  | str |

Returns: `list[RaceOutcome]`

## `qs_everesteer.experiments.racing.RacingScheduler.next_actions`

`next_actions(self, research_state: 'dict') -> 'list[dict]'`

MISSING DOCSTRING

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| research_state | yes |  | dict |

Returns: `list[dict]`

## `qs_everesteer.selection.frontier.pareto_frontier`

`pareto_frontier(records: 'list[dict]', objectives: 'list[tuple[str, str]]') -> 'list[dict]'`

MISSING DOCSTRING

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| records | yes |  | list[dict] |
| objectives | yes |  | list[tuple[str, str]] |

Returns: `list[dict]`

## `qs_everesteer.ensemble.blend.rank_average`

`rank_average(predictions)`

MISSING DOCSTRING

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| predictions | yes |  |  |

## `qs_everesteer.ensemble.blend.weighted`

`weighted(predictions, weights=None)`

MISSING DOCSTRING

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| predictions | yes |  |  |
| weights | no | None |  |

## `qs_everesteer.ensemble.blend.greedy_forward`

`greedy_forward(predictions, y_true, scorer: 'Callable[[Any, Any], Any]', *, max_members: 'int | None' = None) -> 'dict[str, Any]'`

MISSING DOCSTRING

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| predictions | yes |  |  |
| y_true | yes |  |  |
| scorer | yes |  | Callable[[Any, Any], Any] |
| max_members | no | None | int \| None |

Returns: `dict[str, Any]`

## `qs_everesteer.ensemble.blend.diversity_aware`

`diversity_aware(predictions, y_true, scorer: 'Callable[[Any, Any], Any]', *, diversity_weight: 'float' = 0.05, max_members: 'int | None' = None) -> 'dict[str, Any]'`

MISSING DOCSTRING

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| predictions | yes |  |  |
| y_true | yes |  |  |
| scorer | yes |  | Callable[[Any, Any], Any] |
| diversity_weight | no | 0.05 | float |
| max_members | no | None | int \| None |

Returns: `dict[str, Any]`

## `qs_everesteer.submission.guard.SubmissionGuard`

`SubmissionGuard(self, /, *args, **kwargs)`

Hard integrity checks: event, round, lane, fingerprint, IDs, quota, mode.

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| args | yes |  |  |
| kwargs | yes |  |  |

## `qs_everesteer.submission.guard.SubmissionGuard.validate`

`validate(self, ctx: 'SubmissionContext | None' = None, **kwargs: 'Any') -> 'GuardResult'`

MISSING DOCSTRING

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| ctx | no | None | SubmissionContext \| None |
| kwargs | yes |  | Any |

Returns: `GuardResult`

## `qs_everesteer.submission.guard.SubmissionGuard.validate_from_research_state`

`validate_from_research_state(self, ctx: 'SubmissionContext', repo_root: 'str | Path | None' = None) -> 'GuardResult'`

Fill mode / snapshot defaults from research state then validate.

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| ctx | yes |  | SubmissionContext |
| repo_root | no | None | str \| Path \| None |

Returns: `GuardResult`

## `qs_everesteer.submission.mode.get_mode`

`get_mode(repo_root: 'str | Path | None' = None) -> 'SubmissionMode'`

Return the current submission mode (default DRY_RUN).

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| repo_root | no | None | str \| Path \| None |

Returns: `SubmissionMode`

## `qs_everesteer.submission.mode.arm_submissions`

`arm_submissions(event_snapshot_id: 'str', repo_root: 'str | Path | None' = None) -> 'SubmissionMode'`

Explicitly enable real uploads. Requires a current event snapshot id.

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| event_snapshot_id | yes |  | str |
| repo_root | no | None | str \| Path \| None |

Returns: `SubmissionMode`

## `qs_everesteer.live.rounds.RoundController`

`RoundController(self, *, repo_root: 'str | Path | None' = None, adapter: 'EveresteerAdapter | None' = None, feed: 'SimulatedEventFeed | None' = None, pipeline: 'SubmissionPipeline | None' = None, infer_fn: 'InferChampionFn | None' = None, ensemble_fn: 'EnsembleFn | None' = None, audit_fn: 'Callable[[Path], dict[str, Any]] | None' = None) -> 'None'`

Restartable / idempotent live-round loop.

detect round → snapshot → pull live → fingerprint → audit →
infer champion/challengers → ensemble → guard → submit (mode+idempotency) →
observe → update state.

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| repo_root | no | None | str \| Path \| None |
| adapter | no | None | EveresteerAdapter \| None |
| feed | no | None | SimulatedEventFeed \| None |
| pipeline | no | None | SubmissionPipeline \| None |
| infer_fn | no | None | InferChampionFn \| None |
| ensemble_fn | no | None | EnsembleFn \| None |
| audit_fn | no | None | Callable[[Path], dict[str, Any]] \| None |

Returns: `None`

## `qs_everesteer.live.rounds.RoundController.tick`

`tick(self, **kwargs: 'Any') -> 'RoundTickResult'`

Run one restartable cycle. Extra kwargs override detect/submit fields.

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| kwargs | yes |  | Any |

Returns: `RoundTickResult`

## `qs_everesteer.jobs.queue.enqueue`

`enqueue(kind: 'str | JobKind', payload: 'dict[str, Any] | None' = None, *, repo_root: 'str | Path | None' = None, name: 'str | None' = None, candidate: 'str | None' = None, device: 'str' = 'CPU', job_id: 'str | None' = None, priority: 'int | JobPriority' = <JobPriority.AUTOML: 4>, deadline: 'str | None' = None, dependencies: 'list[str] | None' = None, maximum_attempts: 'int' = 2) -> 'str'`

Write a QUEUED job JSON under ``runs/jobs/`` and return its id.

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| kind | yes |  | str \| JobKind |
| payload | no | None | dict[str, Any] \| None |
| repo_root | no | None | str \| Path \| None |
| name | no | None | str \| None |
| candidate | no | None | str \| None |
| device | no | 'CPU' | str |
| job_id | no | None | str \| None |
| priority | no | <JobPriority.AUTOML: 4> | int \| JobPriority |
| deadline | no | None | str \| None |
| dependencies | no | None | list[str] \| None |
| maximum_attempts | no | 2 | int |

Returns: `str`

## `qs_everesteer.jobs.worker.run_job_sync`

`run_job_sync(job_id: 'str', repo_root: 'str | Path | None' = None, *, handlers: 'dict[str, Handler] | None' = None) -> 'Job'`

Execute a single job in-process (unit-test path).

Updates status/progress/timing with ``time.perf_counter`` for monotonic elapsed.

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| job_id | yes |  | str |
| repo_root | no | None | str \| Path \| None |
| handlers | no | None | dict[str, Handler] \| None |

Returns: `Job`

## `qs_everesteer.autopilot.orchestrator.CompetitionAutopilot`

`CompetitionAutopilot(self, repo_root: 'str | Path | None' = None, handlers: 'dict[str | AutopilotStage, Callable[[dict[str, Any]], Any]] | None' = None) -> 'None'`

Advance one persisted state at a time; handlers are plain callables.

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| repo_root | no | None | str \| Path \| None |
| handlers | no | None | dict[str \| AutopilotStage, Callable[[dict[str, Any]], Any]] \| None |

Returns: `None`

## `qs_everesteer.autopilot.orchestrator.CompetitionAutopilot.run`

`run(self, profile: 'str' = 'competition_aggressive', *, max_steps: 'int | None' = None) -> 'dict[str, Any]'`

MISSING DOCSTRING

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| profile | no | 'competition_aggressive' | str |
| max_steps | no | None | int \| None |

Returns: `dict[str, Any]`

## `qs_everesteer.autopilot.orchestrator.CompetitionAutopilot.step`

`step(self, profile: 'str' = 'competition_aggressive') -> 'dict[str, Any]'`

MISSING DOCSTRING

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| profile | no | 'competition_aggressive' | str |

Returns: `dict[str, Any]`

## `qs_everesteer.dashboard.process.DashboardProcessManager`

`DashboardProcessManager(self, repo_root: 'str | Path | None' = None) -> 'None'`

Single authority for Research Console start/status/stop/open/diagnose.

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| repo_root | no | None | str \| Path \| None |

Returns: `None`

## `qs_everesteer.dashboard.process.DashboardProcessManager.build_command`

`build_command(self) -> 'list[str]'`

MISSING DOCSTRING

Returns: `list[str]`

## `qs_everesteer.dashboard.process.DashboardProcessManager.build_frontend`

`build_frontend(self, *, clean: 'bool' = False) -> 'dict[str, Any]'`

MISSING DOCSTRING

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| clean | no | False | bool |

Returns: `dict[str, Any]`

## `qs_everesteer.dashboard.process.DashboardProcessManager.classify`

`classify(self) -> 'dict[str, Any]'`

MISSING DOCSTRING

Returns: `dict[str, Any]`

## `qs_everesteer.dashboard.process.DashboardProcessManager.diagnose`

`diagnose(self) -> 'dict[str, Any]'`

MISSING DOCSTRING

Returns: `dict[str, Any]`

## `qs_everesteer.dashboard.process.DashboardProcessManager.open_browser`

`open_browser(self, *, start_if_needed: 'bool' = False) -> 'dict[str, Any]'`

MISSING DOCSTRING

### Parameters

| Name | Required | Default | Type |
| --- | --- | --- | --- |
| start_if_needed | no | False | bool |

Returns: `dict[str, Any]`

## `qs_everesteer.dashboard.process.DashboardProcessManager.start`

`start(self) -> 'dict[str, Any]'`

MISSING DOCSTRING

Returns: `dict[str, Any]`

## `qs_everesteer.dashboard.process.DashboardProcessManager.stop`

`stop(self) -> 'dict[str, Any]'`

MISSING DOCSTRING

Returns: `dict[str, Any]`

