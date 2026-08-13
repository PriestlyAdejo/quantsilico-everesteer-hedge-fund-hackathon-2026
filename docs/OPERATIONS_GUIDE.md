# Everesteer operations guide

This guide explains the end-to-end research and event workflow. The CLI is the
critical path; the dashboard is an optional view and controlled launcher over
the same queue and state.

All examples assume PowerShell at the repository root. Do not activate the
virtual environment; invoke its executables directly.

## Safety model

- Real data never silently becomes synthetic data.
- Synthetic fixtures require `--synthetic` or `QSEH_SYNTHETIC=1` and remain
  visibly labelled.
- Runpod is synthetic/public-data only until authoritative event terms permit
  third-party processing.
- Existing included or explicitly authorised pre-funded credits may be used
  within the configured budget. Unknown funding and cash billing are blocked.
- Live submission is disabled by default and requires a deliberate human arm.
- Final selection, staking, wallet transfers, top-ups and purchases are never
  inferred from general automation authority.
- Public model names remain opaque and do not reveal the model family.

## 1. Preflight

```powershell
.\.venv\Scripts\qseh.exe doctor
.\.venv\Scripts\qseh.exe sdk info
.\.venv\Scripts\qseh.exe sdk check
```

`doctor` reports local CPU/RAM/GPU facts. `sdk info` reports the installed SDK,
while `sdk check` checks the repository adapter without making a submission.
Missing authenticated capabilities remain `UNKNOWN` rather than guessed.

## 2. Capture current event mechanics

```powershell
.\.venv\Scripts\qseh.exe event inspect
.\.venv\Scripts\qseh.exe event snapshot
```

The snapshot records current round shape, splits, score weights, upload limits,
staking/final-selection applicability and server-compute capabilities. Every
external action references the snapshot that authorised it.

## 3. Inspect compute, funding and data policy

```powershell
.\.venv\Scripts\qseh.exe compute probe
.\.venv\Scripts\qseh.exe compute policy show
.\.venv\Scripts\qseh.exe compute jobs
```

The probe distinguishes method presence from a usable backend. Local CPU is the
fallback. Native GPU, Linux/WSL JAX, Everesteer and Runpod are admitted only
after their required capabilities pass. A backend can be available but still
be rejected by deadline, budget, VRAM or egress policy.

No Runpod resource is provisioned merely by `compute probe`. Configure
credentials outside Git and never print them. A Runpod training allocation must
have a wall-time bound, worker cap, spend cap, idle/teardown policy and verified
artifact-recovery route.

## 4. Pull and verify data

Real event data:

```powershell
Remove-Item Env:QSEH_SYNTHETIC -ErrorAction SilentlyContinue
.\.venv\Scripts\qseh.exe data pull --split train
.\.venv\Scripts\qseh.exe data audit .\data\train.parquet
.\.venv\Scripts\qseh.exe data fingerprint .\data\train.parquet
```

The command must fail nonzero if the authenticated download fails. Confirm that
the output says `synthetic: false` before training.

Synthetic rehearsal:

```powershell
$env:QSEH_SYNTHETIC = '1'
.\.venv\Scripts\qseh.exe data pull --split train
.\.venv\Scripts\qseh.exe data audit .\data\synthetic\train.parquet
```

Synthetic artefacts are fixtures only and must never be described as live event
evidence.

## 5. Verify organiser parity

```powershell
.\.venv\Scripts\qseh.exe baseline reproduce --official --data .\data\train.parquet
.\.venv\Scripts\qseh.exe baseline scorer-parity
```

Baseline reproduction stores the starter URL/hash, target, missing-value
handling and validation settings. Scoring verification checks prediction/target
orientation, alignment and the official component implementation. For
`target_everest_20`, serious validation uses an embargo of at least 20 expeds.

## 6. Benchmark execution choices

```powershell
.\.venv\Scripts\qseh.exe compute benchmark --profile matched
.\.venv\Scripts\qseh.exe compute autotune
```

Matched benchmarks restore identical immutable inputs and report compilation,
warm-up, steady-state and complete scored-trial time separately. Autotuning may
choose CPU for a tiny trial, native GPU for a tree model, JAX/Torch for a neural
model, or an authorised remote backend when startup and transfer overhead still
meet the deadline.

## 7. Start the durable worker

```powershell
.\.venv\Scripts\qseh.exe worker start
.\.venv\Scripts\qseh.exe worker status
```

The queue is priority/deadline aware. Live packaging and recovery outrank
practice research; equal-priority jobs retain FIFO order. Workers use leases,
heartbeats, bounded attempts and resource semaphores. Cancellation stops the
actual subprocess or provider job rather than only changing a JSON field.

## 8. Broad cheap discovery through R1

```powershell
.\.venv\Scripts\qseh.exe search family --profile R0 --data .\data\train.parquet
.\.venv\Scripts\qseh.exe race --through R1
```

This stage compares cheap, similarly budgeted LightGBM, XGBoost, CatBoost,
ExtraTrees, Ridge and shallow-neural candidates. R0 and R1 produce real child
trials; they are not labels applied to old metrics.

## 9. Tune survivors and add diverse challengers

```powershell
.\.venv\Scripts\qseh.exe search tune --survivors --profile R2 --data .\data\train.parquet
.\.venv\Scripts\qseh.exe search advanced --profile R1 --bounded --data .\data\train.parquet
```

Tuning spends deeper budgets only on promising families. Advanced search adds
bounded neural or structurally different challengers. Diversity is useful only
with correctly aligned OOF predictions.

## 10. Final promotion

```powershell
.\.venv\Scripts\qseh.exe race --through R3
```

Tuned leaders and useful diverse challengers are retrained through the remaining
temporal profiles. Integrity failures stop promotion; weaker valid results stay
available as evidence or reserve candidates.

## 11. Ensemble and select champion

```powershell
.\.venv\Scripts\qseh.exe ensemble build --method greedy
.\.venv\Scripts\qseh.exe ensemble stack --method ridge-oof
.\.venv\Scripts\qseh.exe champion-select
```

Stackers train on OOF predictions only, aligned by event identity fields rather
than array length. Champion selection retains reserve and diversity candidates.

## 12. Run the orchestrated research sequence

```powershell
.\.venv\Scripts\qseh.exe autopilot run --profile competition-aggressive
.\.venv\Scripts\qseh.exe autopilot status
```

Autopilot follows the same broad-search, early-promotion, tuning, challenger,
final-promotion and stacking order. Missing mandatory handlers produce
`BLOCKED_NOT_IMPLEMENTED`; they never count as successful completion.

## 13. Generate and check a live package without uploading

```powershell
.\.venv\Scripts\qseh.exe candidate infer --candidate champion --data .\data\live.parquet
.\.venv\Scripts\qseh.exe candidate package --candidate champion --predictions .\artifacts\predictions\<candidate-id>.parquet
.\.venv\Scripts\qseh.exe event submission-mode DRY_RUN
.\.venv\Scripts\qseh.exe submit live --candidate champion --predictions .\artifacts\predictions\<candidate-id>.parquet
```

The package binds source/model/data/split/event lineage, predictions and the
required model artefact. Dry-run performs every local guard without contacting
the submission endpoint.

## 14. Human-authorised live submission

Use the established command so previous event-day notes remain valid:

```powershell
.\.venv\Scripts\qseh.exe event arm-submissions
.\.venv\Scripts\qseh.exe submit live --candidate champion --predictions .\artifacts\predictions\<candidate-id>.parquet
```

Arming is narrow and reversible. It does not authorise staking, funding,
top-ups, wallet operations or data egress. Re-run the event snapshot immediately
before the live action.

## 15. Recover and verify evidence

```powershell
.\.venv\Scripts\qseh.exe jobs list
.\.venv\Scripts\qseh.exe jobs retry <job-id>
.\.venv\Scripts\qseh.exe jobs cancel <job-id>
.\.venv\Scripts\qseh.exe evidence verify
```

Retry creates a new attempt linked to the failed attempt. Evidence verification
checks hashes and completion markers before a result can be promoted.

## Existing command compatibility

Established safe commands remain supported. Cleaner grouped commands may be
aliases, but event-day scripts are not broken for aesthetics. An old form is
removed only when its behavior is unsafe or semantically false, and the CLI then
prints the safe replacement.

## Emergency behavior

```powershell
.\.venv\Scripts\qseh.exe emergency
```

Emergency mode disarms submissions, stops new research dispatch, preserves
running/failure evidence and snapshots event state. It does not transfer money,
delete persistent cloud data or invent a successful result.
