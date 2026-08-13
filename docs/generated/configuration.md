---
title: Configuration
description: Generated from experiment YAML keys, fold profiles, and project configs.
source: generated
generatedFromSha: 65828f1669f73fa7428a854ca927ef05e038cb3e
generatedAt: 2026-08-13T14:19:01+00:00
---

# Configuration

Generated from commit `65828f1669f73fa7428a854ca927ef05e038cb3e`.

Fields below are taken from code that actually reads them, dataclasses, enums, and checked-in YAML. Undocumented keys are not inferred.

## Race / experiment configuration

Consumed by `ExperimentRunner.run` from a YAML mapping or dict.

| Field | Type | Required | Default | Meaning |
| --- | --- | --- | --- | --- |
| data_path | path | yes |  | Training parquet path read by ExperimentRunner |
| model | str \| {name, params} | no | ridge | Model factory name or mapping with name/params |
| params | dict | no | {} | Hyperparameters when model is a string |
| profile | R0/R1/R2/R3 | no | R1 | Temporal fold profile passed to temporal_cv |
| target | str | no | target_everest_20 | Target column |
| exped_col | str | no | exped | Time-group / exped column |
| features | list[str] | no | feature_* columns | Feature list; otherwise columns starting with feature_ |
| run_id | str | no | run-<uuid12> | Persisted experiment id |
| data_hash | str | no |  | Optional training data fingerprint stored on the model artefact |

## Fold profiles

From `FoldProfile` / `FOLD_PROFILES` in `qs_everesteer.validation.temporal`.

| Key | name | n_splits | min_train_expeds | test_expeds | embargo | rolling_window |
| --- | --- | --- | --- | --- | --- | --- |
| R0 | R0 | 1 | 2 | 1 | 0 |  |
| R1 | R1 | 2 | 3 | 1 | 0 |  |
| R2 | R2 | 3 | 4 | 2 | 1 |  |
| R3 | R3 | 4 | 5 | 2 | 1 |  |

## Model factories

Names accepted by `qs_everesteer.models.create_model`.

| Name | Factory |
| --- | --- |
| catboost | qs_everesteer.models.catboost_model.catboost_model |
| extra_trees | qs_everesteer.models.forest.extra_trees |
| feature_bin | qs_everesteer.models.advanced.feature_bin_model |
| lgbm | qs_everesteer.models.lgbm.lgbm_model |
| organiser_lgbm | qs_everesteer.models.baseline.organiser_lgbm |
| random_forest | qs_everesteer.models.forest.random_forest |
| realmlp_style | qs_everesteer.models.advanced.realmlp_style |
| reference_lgbm | qs_everesteer.models.baseline.reference_lgbm |
| ridge | qs_everesteer.models.ridge.ridge_model |
| shallow_mlp | qs_everesteer.models.p1.shallow_mlp |
| tabular_hist | qs_everesteer.models.advanced.tabular_hist_challenger |
| xgboost | qs_everesteer.models.xgboost_model.xgboost_model |

## Model YAML examples

Checked-in files under `configs/models/`.

### `C:/Users/pries/Documents/Projects/quantsilico-everesteer-hedge-fund-hackathon-2026/configs/models/extra_trees.yaml`

| Field | Type | Example |
| --- | --- | --- |
| experiment.name | str | extra_trees |
| experiment.family | str | extra_trees |
| experiment.stage | str | auto |
| features.selector | str | all |
| validation.profile | str | fast_then_race |
| prediction.postprocess | str | auto |
| model.parameters | dict | {} |

### `C:/Users/pries/Documents/Projects/quantsilico-everesteer-hedge-fund-hackathon-2026/configs/models/lgbm_regularised.yaml`

| Field | Type | Example |
| --- | --- | --- |
| experiment.name | str | lgbm_regularised |
| experiment.family | str | lightgbm |
| experiment.stage | str | auto |
| features.selector | str | all |
| validation.profile | str | fast_then_race |
| prediction.postprocess | str | auto |
| model.parameters | dict | {} |

### `C:/Users/pries/Documents/Projects/quantsilico-everesteer-hedge-fund-hackathon-2026/configs/models/organiser_lgbm.yaml`

| Field | Type | Example |
| --- | --- | --- |
| experiment.name | str | organiser_lgbm |
| experiment.family | str | lightgbm |
| experiment.stage | str | auto |
| features.selector | str | all |
| validation.profile | str | fast_then_race |
| prediction.postprocess | str | auto |
| model.parameters | dict | {} |

### `C:/Users/pries/Documents/Projects/quantsilico-everesteer-hedge-fund-hackathon-2026/configs/models/random_forest.yaml`

| Field | Type | Example |
| --- | --- | --- |
| experiment.name | str | random_forest |
| experiment.family | str | random_forest |
| experiment.stage | str | auto |
| features.selector | str | all |
| validation.profile | str | fast_then_race |
| prediction.postprocess | str | auto |
| model.parameters | dict | {} |

### `C:/Users/pries/Documents/Projects/quantsilico-everesteer-hedge-fund-hackathon-2026/configs/models/ridge.yaml`

| Field | Type | Example |
| --- | --- | --- |
| experiment.name | str | ridge |
| experiment.family | str | ridge |
| experiment.stage | str | auto |
| features.selector | str | all |
| validation.profile | str | fast_then_race |
| prediction.postprocess | str | auto |
| model.parameters | dict | {} |

### `C:/Users/pries/Documents/Projects/quantsilico-everesteer-hedge-fund-hackathon-2026/configs/models/xgboost.yaml`

| Field | Type | Example |
| --- | --- | --- |
| experiment.name | str | xgboost |
| experiment.family | str | xgboost |
| experiment.stage | str | auto |
| features.selector | str | all |
| validation.profile | str | fast_then_race |
| prediction.postprocess | str | auto |
| model.parameters | dict | {} |


## Event configuration

From `C:/Users/pries/Documents/Projects/quantsilico-everesteer-hedge-fund-hackathon-2026/configs/event/everesteer_london_2026.yaml`.

| Field | Type | Example |
| --- | --- | --- |
| event.name | str | Everesteer Hedge Fund Hackathon London 2026 |
| event.date | date | 2026-08-13 |
| event.timezone | str | Europe/London |
| event.tournament | str | futures |
| event.universe | str | futures |
| event.target | str | auto |
| sdk.pinned_version | str | 0.3.22 |
| sdk.snapshot_runtime_version | bool | True |
| sdk.update_only_after_contract_tests | bool | True |
| capability_discovery.whoami | bool | True |
| capability_discovery.get_started | bool | True |
| capability_discovery.explain_scoring | bool | True |
| capability_discovery.event_staking | bool | True |
| capability_discovery.dataset_info | bool | True |
| capability_discovery.standings | bool | True |
| capability_discovery.server_compute | str | probe |
| submission.dry_run_default | bool | True |
| submission.public_model_names | str | opaque |
| submission.reserve_for_live_fraction | float | 0.6 |
| submission.emergency_reserve_slots | int | 1 |
| submission.account_cap | str | auto |
| staking.mode | str | auto |
| staking.virtual_event_autopilot | bool | True |
| staking.real_money_requires_human | bool | True |
| staking.risk_profile | str | aggressive |


## Submission configuration

Persisted as `submission_mode` in research state. `ARMED` requires an explicit snapshot id.

| Value | Type | Default | Meaning |
| --- | --- | --- | --- |
| DISABLED | enum | no | External uploads cannot be performed |
| DRY_RUN | enum | yes | Validate/package/record without uploading |
| ARMED | enum | no | Real uploads permitted after explicit arm |

## Autopilot configuration

`CompetitionAutopilot.step` / `run` take `profile` (default `competition_aggressive`).

Autopilot never transitions submission mode to ARMED.

| Stage | Order |
| --- | --- |
| DISCOVER | 0 |
| PULL | 1 |
| SCORER_PARITY | 2 |
| BASELINE | 3 |
| FAST_RACE | 4 |
| STANDARD_RACE | 5 |
| PROMOTION_RACE | 6 |
| FRONTIER | 7 |
| ENSEMBLE | 8 |
| PRACTICE_SUBMIT | 9 |
| LIVE_SUBMIT | 10 |
| OBSERVE | 11 |
| ADAPT | 12 |
| COMPLETE | 13 |

