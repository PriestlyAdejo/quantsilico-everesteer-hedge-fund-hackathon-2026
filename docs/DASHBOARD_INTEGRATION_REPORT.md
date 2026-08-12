# Dashboard integration report

| Page | Status | Backend sources | Actions | Refresh | Remaining fixtures | Known limitations | Tests |
|---|---|---|---|---|---|---|---|
| Overview | LIVE-WIRED | `ConsoleService.overview` ← research_state, experiments | — | poll / SSE tick | none in API mode | Flow stages derived from state | `test_api_reads` |
| Event Control | LIVE-WIRED | adapter inspect + research_state | refresh/snapshot/pull/parity/baseline/autopilot | poll | none | Organiser baseline = reference_lgbm until exact starter | `test_api_reads`, actions enqueue |
| Round Room | LIVE-WIRED | live controller + jobs + board | — | push/poll | empty board when disconnected | Countdown from backend timestamps | rehearsal |
| Data Lab | LIVE-WIRED | dataset audits/fingerprints | — | on data change | synthetic when QSEH_SYNTHETIC | Official data NOT YET AVAILABLE without creds | audit tests |
| Experiments | LIVE-WIRED | `runs/experiments/*` manifests | — | event-driven | none | Large tables rely on browser scroll | cardinality |
| Validation | LIVE-WIRED | integrity + soft metrics from runs | — | event-driven | none | Only available metrics rendered | research loop |
| Models | LIVE-WIRED | model registry metadata | — | event-driven | none | Public aliases opaque | models_fit |
| Feature Lab | LIVE-WIRED | audit / importance summaries | — | on data change | none | No economic identities | audit |
| Ensembles | LIVE-WIRED | ensemble blend records | build/save/promote | event-driven | Neutralised only if supported | — | ensemble tests |
| Leaderboard | LIVE-WIRED | adapter observations | — | push/poll | empty when not connected | Never fakes ranks | rehearsal |
| Submission | LIVE-WIRED | quota + pipeline + mode | validate/practice/live | job-driven | none | Default DRY_RUN; ARMED operator-only | submission tests |
| Staking | LIVE-WIRED | stake classifier | recommend only | manual/moderate | none | Real money never auto | stake_classify |
| Compute & Jobs | LIVE-WIRED | jobs queue + hardware probe | stopJob | push/frequent | none | Soft ETA only | job_queue |
| Repository | LIVE-WIRED | git/python/sdk read-only | — | manual | none | No git writes | api_reads |
| Documentation | LIVE-WIRED | docs_build + curated MDX | — | build-triggered | none | `/docs` SPA vs `/api/docs` JSON | docs build |

**Submission mode banner:** Event Control, Round Room, Submission show DISABLED / DRY_RUN / **SUBMISSIONS ARMED**.

**Visual authority:** Figma ZIP SHA-256 `36F9B08F…B6F76A`. Self-hosted fonts (no Google Fonts at runtime).

**Docs collision:** Swagger at `/api/dev/docs`; SPA Documentation at `/docs`; JSON at `/api/docs`.
