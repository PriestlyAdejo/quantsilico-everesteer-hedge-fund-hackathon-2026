# Rehearsal report

| Field | Value |
|---|---|
| Timestamp | 2026-08-12 (local implementation) |
| Branch | `feature/pre-event-platform` |
| Starting SHA | `211f2c45b0b41b4701a982b4285500dfcf478eff` |
| Recovery tag | `recovery/pre-engine-figma-211f2c4` |
| SDK | `everestapi 0.3.22` |
| Synthetic fixture | `qs_everesteer.data.synthetic` Everesteer-like Parquet |
| Frontend | Exact Figma port; `VITE_DATA_MODE=api`; self-hosted fonts |
| Figma ZIP SHA-256 | `36F9B08FAF8A31B862E33CCC6671E0FDEC27F2D09858056848D2AC8B03B6F76A` |

## Tests

```text
70 passed (unit + contracts + integration)
```

Including:

- golden DataEnvelope contract tests (`schemaVersion` 2)
- synthetic research loop
- API reads + action enqueue
- live-event rehearsal happy path
- failure drills: backend kill / autopilot idempotency / disconnect→LIVE
- dynamic cardinality (1/4/50 models × 1/5/20 rounds)
- secret scan

## Stages exercised

```text
event disconnected → connected → data → audit → baseline/race jobs
→ frontier/champion → ensemble → practice DRY_RUN
→ round open → live infer → live DRY_RUN submit
→ leaderboard/standings → round close
```

Failure drills:

1. Dashboard stop while job continues — research state survives  
2. Autopilot/round restart — no duplicate submissions (idempotency ledger)  
3. Simulated feed disconnect/reconnect — DISCONNECTED → RECONNECTING → LIVE without Demo fixtures

## Frontend routes exercised (API)

All 15 SPA routes served via history fallback (`/validation` returns `index.html`).  
Swagger isolated at `/api/dev/docs` (no collision with SPA `/docs`).

## Remaining risks

- Live Everesteer credentials / organiser data: NOT YET AVAILABLE  
- Exact organiser LightGBM starter: UNAVAILABLE (`reference_lgbm` used)  
- Real ARMED submissions require explicit `qseh event arm-submissions`  
- Visual screenshot automation at 1280×800 not stored (build verified; browser automation optional)

## First venue commands

```text
qseh doctor
qseh event inspect
qseh data pull
qseh baseline reproduce
qseh event arm-submissions   # only when operator enables real uploads
qseh autopilot run --profile competition-aggressive
qseh dashboard start
```
