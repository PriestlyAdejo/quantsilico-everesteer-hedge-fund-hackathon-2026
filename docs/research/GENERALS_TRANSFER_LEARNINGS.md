# Generals performance-engineering transfer

This document records public-safe engineering lessons transferred from the
QuantSilico Generals competition project. It deliberately does not include
private chat transcripts, credentials, organiser data, predictions, or
Generals-specific reinforcement-learning code.

`LOCAL_AGENT_HISTORY = AVAILABLE_PARTIAL`

Local Cursor history was available for a read-only audit. Older Codex history
was incomplete beyond exported notes, so the public repository reports,
manifests, source, and Git history remain the reproducible authorities.

## What transfers

The useful abstraction is an evidence-driven compute programme, not PPO or the
game environment:

- keep the timed hot path device-resident and batch complete units of useful
  work;
- reuse prepared data and device-side state instead of rebuilding it in every
  update;
- keep static shapes where compilation benefits from them;
- separate compilation and warm-up from steady-state timing;
- compare identical immutable inputs and restore the same parent artefact for
  every benchmark rung;
- autotune execution geometry rather than assuming that a larger GPU or batch
  is faster;
- measure valid end-to-end output, not isolated kernel throughput;
- sample CPU, RAM, GPU and VRAM continuously rather than using one post-run
  snapshot;
- hash source, dependencies, data, configuration, checkpoints and returned
  artefacts;
- checkpoint atomically and mark a run complete only after reload/hash
  verification;
- preserve failed trials and revert a speed optimisation when parity or signal
  health fails.

Everesteer applies these ideas to folds, model trials, scoring, OOF artefacts,
ensembles and inference packages. JAX is an optional implementation detail for
shape-stable neural or vectorised workloads; native tree libraries retain their
own acceleration paths.

## Evidence and cautions

The Generals reports under `experiments/reports/` show why staged profiling is
necessary. The project moved from a host-bound path to fused JAX execution, then
improved throughput again by reusing a reset pool, batching rollout/policy work,
and moving GAE and updates onto the device. Relevant public-safe sources include:

- `competition_native_jax_hot_path_profile.md`;
- `competition_native_jax_v4_2_profile.md`;
- `competition_native_jax_v4_2_matched_benchmarks.md`;
- `competition_native_jax_v4_2_terminal.md`;
- `gpu_training_benchmark.md`.

The strongest warning is in
`experiments/manifests/cloud_gpu_last_push_v1_final_programme_state.json`.
The paid A100 programme reconstructed rollout state across updates and
invalidated 33,849,344 transitions. After continuity was fixed, all-draw and
zero-reward behaviour still showed that compute cannot repair a broken learning
signal. Everesteer therefore requires data/scoring parity, valid OOF evidence,
and meaningful-score canaries before promoting an expensive backend.

The A100 geometry ladder in
`experiments/manifests/cloud_training_geometry_gate.json` is useful as proof
that geometry matters, but its fastest figures pre-date the continuity repair.
They are systems hints, not valid-learning evidence and are never copied as
Everesteer acceptance targets.

Operational patterns worth retaining are documented in:

- `scripts/cloud_gpu_last_push.py` for immutable-parent warm benchmark rungs;
- `scripts/cloud_orchestrator.py` for checkpoint and watchdog discipline;
- `scripts/cloud_restore_environment.sh` for checksummed environment recovery;
- `configs/training/device_policy.yaml` for fail-fast device selection;
- `experiments/manifests/cloud_parent_compatibility.json` for the distinction
  between compatibility and exact reproduction.

## What does not transfer

- PPO, GAE, actor/opponent logic, the Generals environment, and reward design;
- fixed environment/rollout geometry such as `512 x 32`;
- memory preallocation designed for an 80 GB A100;
- one-point GPU-utilisation gates;
- the assumption that GPU beats CPU for small workloads;
- compatibility tests presented as exact source reproduction;
- any cloud price, credit balance, SSH endpoint or provider configuration from
  the Generals project.

## Everesteer promotion gates

Before a workload can move from local proof to remote or expensive compute it
must satisfy:

1. dataset identity and egress policy;
2. deterministic configuration and source lineage;
3. CPU/reference parity within declared tolerances;
4. official-score orientation and OOF alignment checks;
5. successful small canary with non-degenerate predictions;
6. matched end-to-end benchmark including startup and transfer overhead;
7. known and authorised funding plus a deadline-safe wall-time bound;
8. verified checkpoint, cancellation, artifact recovery and teardown paths.

Failure at an integrity gate blocks promotion. Weak but valid model quality is
retained as graded evidence rather than erased.
