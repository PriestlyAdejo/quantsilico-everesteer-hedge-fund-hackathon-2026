# Bootstrap provenance

Recorded when the public-safe event repository was materialised from the preparation bundle.
Sibling repositories were inspected read-only and were not modified.

## Bootstrap

| Field | Value |
|---|---|
| Bootstrap timestamp (local) | 2026-08-12 ~04:00 BST |
| Parent Projects directory | `c:\Users\pries\Documents\Projects` |
| Preparation-bundle source | `c:\Users\pries\Documents\Projects\quantsilico-everesteer-hedge-fund-hackathon-2026-prep-bundle\quantsilico-everesteer-hackathon-2026-prep\quantsilico-everesteer-hedge-fund-hackathon-2026` |
| Target repository | `c:\Users\pries\Documents\Projects\quantsilico-everesteer-hedge-fund-hackathon-2026` |
| Initial working branch | `feature/pre-event-platform` |
| Public baseline branch | `main` (same commit as bootstrap) |

## Environment snapshot

| Field | Value |
|---|---|
| Python | 3.12.10 (`py -3.12`) |
| Package tooling | venv + pip (no `uv`; matches Generals/M2M practice) |
| Node | v22.22.0 |
| pnpm | 11.10.0 |
| CPU | Intel Core i7-10750H @ 2.60 GHz, 12 logical processors |
| RAM | ~16 GB |
| GPU | NVIDIA GeForce RTX 3070 Laptop GPU, 8192 MiB, driver 581.42 |
| Free disk (C:) | ~59 GB at inspection |

## Everesteer SDK

| Field | Value |
|---|---|
| Package | `everestapi` (Everesteer prediction tournament SDK; not unrelated EVEREST HPC) |
| Researched latest (PyPI) | `0.3.22` uploaded `2026-08-11T16:42:17Z` |
| Pinned in `pyproject.toml` | `everestapi[scoring]==0.3.22` |

## Sibling repositories inspected (read-only)

### Generals (primary dashboard/console lineage)

| Field | Value |
|---|---|
| Path | `c:\Users\pries\Documents\Projects\quantsilico-generals-competition` |
| Note | Plural folder `quantsilico-generals-competitions` was **not** present locally |
| Branch | `research/phase9g-competition-native-jax-preovernight-v1` |
| SHA | `bd028b438cf6750f5c20e5902d7cc63dec9f365d` (`bd028b4`) |
| Dirty | clean |

Reusable patterns noted for later Prompt 02/Figma work (not copied in bootstrap): terminal-amber console, Figma exact-port architecture, DataSource provider boundary, FastAPI local backend, filesystem-first evidence, rebuildable dashboard index, allowlisted job runner, provenance badges, `.cmd` launchers, production `build-info.json` SHA checks.

### Model-to-Market

| Field | Value |
|---|---|
| Path | `c:\Users\pries\Documents\Projects\quantsilico-model-to-market-competition` |
| Branch | `main` |
| SHA | `951721d534932615d32d35ff2613516e74252ff7` (`951721d`) |
| Dirty | clean |

### Other siblings inspected briefly

| Path | Branch | SHA (short) | Role |
|---|---|---|---|
| `quantsilico-model-to-market-competition-dev` | `dev` | `56783db` | research tip on same remote |
| `quantsilico-generals-dashboard-integration` | `feature/figma-console-integration` | `4be2a55` | earlier Figma port |
| `quantsilico-generals-noon-rescue-v3` | `research/noon-closed-loop-hybrid-salvage-v3` | `bdb28da` | Generals fork |
| `quantsilico-generals-perf-v1` | `perf/cloud-a100-forensic-v1` | `4ae1b05` | Generals fork |
| `quantsilico-generals-valid-learning-recovery` | `research/cloud-valid-learning-recovery-v1` | `c0b5353` | Generals fork |
| `quantsilico-forecasting-the-future-2026-competition` | `main` | `e4f2219` | archive shell |
| `quantsilico-onyx-future-of-energy-trading-competition` | `main` | `925913f` | provenance/archive shell |

## Public / local boundary at bootstrap

Published: engineering scaffold, generic architecture/contracts, synthetic tooling stubs, public source links, tests.

Kept local (gitignored): `PROMPTS/`, `private/`, `docs/private/` (implementation prompts, day-of playbook, aggressive autopilot profile, tactical research notes).
