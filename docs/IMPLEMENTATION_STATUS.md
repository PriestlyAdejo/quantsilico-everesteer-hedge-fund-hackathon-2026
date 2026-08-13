# Implementation status

## Implemented

- Everesteer adapter, event snapshots and capability discovery.
- Explicit synthetic data, fail-closed real pulls, audits and fingerprints.
- Official named scoring adapter with honestly labelled local fallback.
- Target-aware temporal validation; real `target_everest_20` evidence uses a
  minimum 20-exped embargo while explicit synthetic fixtures use compact test
  profiles.
- Attributable official starter recipe and hash; numeric parity remains
  data-dependent.
- Ridge, forests, LightGBM, XGBoost, optional CatBoost, shallow MLP and bounded
  advanced challengers.
- Real R0-R3 retraining child trials with parent lineage and preserved failures.
- Bounded family search, survivor tuning and advanced/diversity stages.
- Rank, weighted, greedy, diversity, OOF ridge and non-negative ensembles.
- Promotion-grade champion/reserve selection and local inference/package
  manifests.
- Submission guard and DISABLED/DRY_RUN/ARMED modes; only integrity failures are
  universal hard stops.
- Live-round controller, idempotency and runtime classification of optional
  final-selection/staking mechanics.
- Mandatory-handler autopilot blocking.
- Durable priority/deadline jobs with FIFO among peers, dependencies, leases,
  heartbeats, bounded attempts, stale recovery and cancellation.
- Versioned experiment/task/backend/budget/egress/artifact contracts.
- Policy-first compute broker across CPU, native GPU, Linux JAX, Everesteer and
  optional Runpod lanes.
- Matched public-synthetic CPU/GPU benchmark and evidence-based autotuning.
- Dashboard local/server queue and runtime history using the same job records.
- CLI critical path, emergency path, generated docs and operator guide.

## Runtime-gated or optional

- JAX/Torch acceleration requires a verified Linux/WSL or remote runtime.
- Runpod real-data execution requires authoritative organiser egress permission.
- Authenticated Everesteer compute requires usable account capabilities and an
  allowed funding source.
- The Runpod policy and CUDA worker are implemented but no remote resource is
  provisioned automatically.
- Exact paper reproductions of TabM/RealMLP are not claimed; current versions are
  explicitly style/challenger implementations.

## Current runtime observations

- SDK: `everestapi[scoring]==0.3.24`, installed and test-verified.
- Official starter provenance: `docs/BASELINE_PROVENANCE.md`.
- RTX 3070 Laptop GPU: detected; native XGBoost synthetic canary passed.
- WSL JAX GPU: not verified.
- Everesteer credentials/compute: unavailable in this shell; represented as
  `UNKNOWN`/unavailable.
- Runpod tooling/auth/funding provenance: unavailable in this shell; represented
  as `UNKNOWN` and blocked.
- Live submission cap and active event mechanics remain runtime observations.
