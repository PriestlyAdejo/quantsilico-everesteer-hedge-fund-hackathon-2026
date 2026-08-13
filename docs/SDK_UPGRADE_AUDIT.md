# EverestAPI 0.3.22 to 0.3.24 audit

Audit date: 13 August 2026.

The repository began this change pinned to `everestapi[scoring]==0.3.22`.
Release `0.3.24` was downloaded as a wheel into a temporary directory and
inspected without replacing the project environment. No API key or organiser
data was used.

## Observed compatibility

The public `EverestAPI.train` signature in 0.3.24 remains compatible with the
0.3.22 signature used by the repository, including built-in/custom models,
features, target, filters, transforms, GPU tier and `max_hours`.

The 0.3.24 client exposes the compute methods required for runtime capability
detection:

- `get_compute_credits`;
- `list_compute_jobs`;
- `get_job_status`, `get_job_log` and `get_job_output`;
- `get_job_predictions_url`;
- `wait_for_job`;
- `cancel_job`.

It also exposes event-mechanic methods including `get_event_staking`,
`get_final_selection` and `set_final_selection`.

Method presence is not proof that an account may use the operation. The adapter
therefore records presence separately from authenticated probe success, and no
live compute or external action is attempted by the compatibility test.

## Upgrade gate

The project may pin 0.3.24 only when:

1. the existing adapter, scoring and CLI contract tests pass;
2. official scoring orientation tests pass;
3. event capability probes fail closed without credentials;
4. submission remains disabled/dry-run by default;
5. synthetic rehearsal remains visibly synthetic.

Authenticated compute access, pricing, funding provenance, quota and event shape
remain runtime observations even after the dependency upgrade.
