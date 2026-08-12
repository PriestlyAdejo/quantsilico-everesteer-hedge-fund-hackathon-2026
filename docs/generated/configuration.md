# Configuration reference (generated)

Generated at `2026-08-12T13:06:24+00:00`.

Experiment YAML fields consumed by `ExperimentRunner` / `qseh` research commands:

| Field | Default / notes |
|---|---|
| `model` | string model name (e.g. `ridge`, `reference_lgbm`) or `{name, params}` |
| `params` | model hyperparameters (dict) |
| `data_path` | path to training parquet |
| `profile` | temporal profile `R0`–`R3` |
| `target` | default `target_everest_20` |
| `exped_col` | default `exped` |
| `features` | optional list; otherwise `feature_*` columns |
| `run_id` | optional; auto-generated when omitted |
| `data_hash` | optional training data fingerprint |

Submission modes: `DISABLED`, `DRY_RUN`, `ARMED` (persisted in research state).

Hardware probe is live host detection — not YAML-configured.
