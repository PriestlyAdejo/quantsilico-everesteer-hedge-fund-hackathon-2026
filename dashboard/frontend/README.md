# Research Console frontend

Exact Figma Make export of the QuantSilico × Everesteer 2026 Research Console.

- Visual authority: Figma ZIP (see `plans/figma-import-manifest.md`)
- Data: `useDataSource()` → `ApiDataSource` (`VITE_DATA_MODE=api`) or `DemoDataSource`
- Never fall back demo on API failure — show `BACKEND UNAVAILABLE`
- Production served by FastAPI from `dist/` on `127.0.0.1:8766`

```bash
pnpm install --frozen-lockfile
pnpm run build
```
