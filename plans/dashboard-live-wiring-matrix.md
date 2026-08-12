# Dashboard live wiring matrix (Phase 4)

Evidence that each of the 15 Research Console pages is live-wired through
`ApiDataSource` → FastAPI read/action routes → `ConsoleService` (filesystem /
research state). Demo fixtures are preview-only and are not the production path.

**Production status key:** `LIVE-WIRED` = backend `ConsoleService` method +
frontend page/`ApiDataSource` method exist and share the contract envelope.

**SubmissionModeBanner:** rendered on Event Control, Round Room, and Submission
(not other pages).

| Page | Panel/component | DataSource method | ApiDataSource call | Backend endpoint | Authoritative source | Update mode | Expected latency | Action endpoint | Production status | Integration test |
|---|---|---|---|---|---|---|---|---|---|---|
| Overview `/` | Operating flow, metrics, score history, frontier scatter, fold evidence, upload quota, decisions | `getOverview` | `GET /api/overview` | `/api/overview` → `ConsoleService.overview` | `runs/state/research_state.json` (local research) | poll / on mount | <200 ms local | — | LIVE-WIRED | `tests/integration/test_api_reads.py` |
| Event Control `/event` | Connection, Event state, Scoring, Capabilities, Autopilot; **SubmissionModeBanner** | `getEventControl` | `GET /api/event-control` | `/api/event-control` → `event_control` | Research state + event adapter observations | poll / on mount | <200 ms; refresh enqueues job | `POST /api/actions/refresh-event`, `snapshot-event`, `pull-datasets`, `scorer-parity`, `official-baseline`, `autopilot/start\|stop` | LIVE-WIRED | `test_api_reads.py`, `test_live_event_rehearsal.py` |
| Round Room `/round` | Metric strip, inference/submission queues, board, event log, emergency, heatmap; **SubmissionModeBanner** | `getRoundRoom` | `GET /api/round-room` | `/api/round-room` → `round_room` | Official round snapshot + job queue + research state | poll (open-round) | <300 ms; live path via round controller | (submit/infer via Submission / jobs) | LIVE-WIRED | `test_live_event_rehearsal.py`, `test_dynamic_cardinality.py` |
| Data Lab `/data` | Dataset cards, missingness, cardinality, target dist, schema diff, drift | `getDataLab` | `GET /api/data-lab` | `/api/data-lab` → `data_lab` | Local `data/**/*audit*.json` (synthetic flagged) | manual / after pull | <500 ms (audit scan) | `POST /api/actions/pull-datasets` | LIVE-WIRED | `test_live_event_rehearsal.py` |
| Experiments `/experiments` | Experiment table, race decisions, drawer | `getExperiments` | `GET /api/experiments` | `/api/experiments` → `experiments` | `runs/experiments/*/run.json` + metrics | poll after race | <300 ms | `POST /api/actions/race/start?profile=` | LIVE-WIRED | `test_live_event_rehearsal.py`, `test_api_actions_enqueue.py` |
| Validation `/validation` | Hard integrity, soft research, race decision, fold heatmap | `getValidation` | `GET /api/validation` | `/api/validation` → `validation` | Local validation evidence | on mount | <200 ms | — | LIVE-WIRED | `test_api_reads.py` |
| Models `/models` | Registry table, fold/importance drawers | `getModels` | `GET /api/models` | `/api/models` → `models` | Research state model/frontier fixtures + local registry | on mount | <200 ms | — | LIVE-WIRED | `test_dynamic_cardinality.py` |
| Feature Lab `/features` | Feature table, importance, correlation matrix | `getFeatureLab` | `GET /api/feature-lab` | `/api/feature-lab` → `feature_lab` | Local feature evidence (empty until audited) | on mount | <200 ms | — | LIVE-WIRED | `test_api_reads.py` |
| Ensembles `/ensembles` | Blend members, strategies, correlation, marginal contrib | `getEnsembles` | `GET /api/ensembles` | `/api/ensembles` → `ensembles` | `research_state.ensemble` | on mount / after build | <300 ms | `POST /api/actions/build-ensemble`, `save-ensemble`, `promote-ensemble` | LIVE-WIRED | `test_live_event_rehearsal.py` |
| Leaderboard `/leaderboard` | Current/cumulative tabs, aliases, trajectories, round×model matrix | `getLeaderboard` | `GET /api/leaderboard` | `/api/leaderboard` → `leaderboard` | Official platform observation when connected; matrix from state fixtures | poll when LIVE | <300 ms | — | LIVE-WIRED | `test_live_event_rehearsal.py`, `test_dynamic_cardinality.py` |
| Submission `/submission` | Upload budget, candidates, stepper; **SubmissionModeBanner** | `getSubmission` | `GET /api/submission` | `/api/submission` → `submission` | Research state submission mode + quota | on mount / after action | <200 ms; submit enqueues | `POST /api/actions/validate/{id}`, `submit-practice/{id}`, `submit-live/{id}` | LIVE-WIRED | `test_live_event_rehearsal.py`, `test_rehearsal_failure_drills.py` |
| Staking `/staking` | Classification banner, candidates, concentration | `getStaking` | `GET /api/staking` | `/api/staking` → `staking` | Explicit event staking signals only (no wallet tx) | on mount | <200 ms | — (human-only real money) | LIVE-WIRED | `test_api_reads.py` |
| Compute & Jobs `/compute` | Hardware gauges, local/server queues, watcher | `getComputeJobs` | `GET /api/compute` | `/api/compute` → `compute` | Host metrics + `runs/jobs/*.json` | poll ~8s | <200 ms (+ psutil) | `POST /api/actions/jobs/{id}/stop` | LIVE-WIRED | `test_rehearsal_failure_drills.py` |
| Repository `/repository` | Branch/SHA, env pins, last tests/rehearsal | `getRepository` | `GET /api/repository` | `/api/repository` → `repository` | Local metadata (git not invoked by default) | on mount | <200 ms | — | LIVE-WIRED | `test_api_reads.py` |
| Documentation `/docs` | Searchable curated flows + generated reference | `getDocumentation` | `GET /api/docs` | `/api/docs` → `documentation` | `docs/flows`, `docs/runbooks` MDX + `docs/generated` manifest | manual (`qseh docs build`) | <300 ms | — | LIVE-WIRED | `test_api_reads.py` (docs envelope) |

## Cross-cutting

| Surface | DataSource method | Endpoint | Notes |
|---|---|---|---|
| TopBar event strip | `getEventStatus` | `GET /api/event-status` | Poll ~5s; connection LIVE/RECONNECTING/DISCONNECTED |
| ActivityStrip jobs | `getComputeJobs` | `GET /api/compute` | Poll ~5s |
| SSE / poll fallback | — | `GET /api/events` (hub) | Bounded live events; poll tick if SSE unavailable |

## Provenance rule

Live wiring must never silently swap to `DemoDataSource` fixtures. Disconnect /
reconnect updates connection state on the live path; envelopes keep
`OFFICIAL_*` / `LOCAL_EXPERIMENT` / `MANUALLY_RECORDED` provenance from
`ConsoleService`, not demo `SYNTHETIC_FIXTURE` preview content.
