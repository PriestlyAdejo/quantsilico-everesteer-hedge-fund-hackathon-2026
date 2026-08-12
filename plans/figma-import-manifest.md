# Figma import manifest

## Source

| Field | Value |
|---|---|
| Source ZIP | `c:\Users\pries\Documents\Projects\figma export eversteer console.zip` |
| Immutable copy | `artifacts/figma-import/figma-export-eversteer-console.zip` (gitignored) |
| SHA-256 | `36F9B08FAF8A31B862E33CCC6671E0FDEC27F2D09858056848D2AC8B03B6F76A` |
| Size | 157623 bytes |
| Recovery tag | `recovery/pre-engine-figma-211f2c4` @ `211f2c45b0b41b4701a982b4285500dfcf478eff` |
| Frozen contracts | `contracts/figma/` |

## Package

| Field | Value |
|---|---|
| Package manager | pnpm (`pnpm-lock.yaml` lockfileVersion 9) |
| React | `^19.2.8` |
| Vite | `^8.0.0` |
| Tailwind | `^4.0.0` (`@tailwindcss/vite`) |
| Router | `react-router` `^8.3.0` |
| Charts | `recharts` `^3.10.1` |
| DataEnvelope schemaVersion | **2** (from DemoDataSource) |

## Routes (15)

`/`, `/event`, `/round`, `/data`, `/experiments`, `/validation`, `/models`, `/features`, `/ensembles`, `/leaderboard`, `/submission`, `/staking`, `/compute`, `/repository`, `/docs`

## DataSource

- Interface: `contracts/figma/data/types.ts` → `DataSource`
- Demo: `DemoDataSource`
- API: `ApiDataSource` → all paths under `/api/*`
- Mode: `VITE_DATA_MODE` (`demo` \| `api`); no silent demo fallback

## Styles / fonts

- Terminal-amber design tokens in `src/index.css`
- Google Fonts import in export (Montserrat, Raleway, JetBrains Mono) — must self-host in production
