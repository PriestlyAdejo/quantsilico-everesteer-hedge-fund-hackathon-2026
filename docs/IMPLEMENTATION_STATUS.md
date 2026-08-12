# Implementation status

## P0

| Item | Status |
|---|---|
| Everesteer adapter + capability discovery | Complete |
| Event snapshots | Complete |
| Synthetic data + audit + fingerprint | Complete |
| Official scoring wrapper (`everestapi.scoring`) | Complete (fallback local IC labelled non-official) |
| Temporal validation R0–R3 | Complete |
| Models: Ridge, RF, ExtraTrees, XGBoost, reference_lgbm | Complete |
| Organiser exact baseline | **UNAVAILABLE** — see `docs/BASELINE_PROVENANCE.md`; `reference_lgbm` used |
| Experiment registry (filesystem) | Complete |
| Racing R0→R3 | Complete |
| Frontier / champion separation | Complete |
| Ensembles (rank/weighted/greedy/diversity) | Complete |
| Submission guard + pipeline + modes DISABLED/DRY_RUN/ARMED | Complete |
| Live round controller + idempotency | Complete |
| Stake classification | Complete |
| Deterministic autopilot | Complete |
| FastAPI `/api/*` + SSE | Complete |
| Exact Figma port | Complete |
| Live DataSource wiring | Complete |
| CLI `qseh` full surface | Complete |
| Emergency path | Complete |
| Docs build + curated MDX | Complete |

## P1

| Item | Status |
|---|---|
| Regularised / subspace / recency / bagging LGBM | Complete |
| Shallow MLP | Complete |
| Server compute adapter | Capability probe only; optional jobs if available |
| Neutralised ensemble | Exposed only when scoring/backend supports |

## P2 deferred

- Transformers / AutoML frameworks
- LLM research operator (optional; not required)
- Automatic public push of milestone commits

## Event / SDK / auth unknowns

| Unknown | Representation |
|---|---|
| Live Everesteer credentials | NOT YET AVAILABLE |
| Exact organiser starter hash | UNAVAILABLE |
| Live submission cap | runtime discovery / null until connected |
| Staking mode for live event | UNKNOWN until classified from event |
| Server compute | UNKNOWN/unavailable until probe succeeds |

Pinned SDK: `everestapi[scoring]==0.3.22` (installed verified).
