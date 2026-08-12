# Dashboard operations (Windows)

The Research Console does **not** require PowerShell activation.

Prefer explicit venv executables from the repository root:

```powershell
cd C:\Users\pries\Documents\Projects\quantsilico-everesteer-hedge-fund-hackathon-2026

.\.venv\Scripts\qseh.exe dashboard diagnose
.\.venv\Scripts\qseh.exe dashboard build
.\.venv\Scripts\qseh.exe dashboard start
.\.venv\Scripts\qseh.exe dashboard status
.\.venv\Scripts\qseh.exe dashboard open
.\.venv\Scripts\qseh.exe dashboard stop
```

Optional CMD wrappers (no activation):

```text
scripts\dashboard\start.cmd
scripts\dashboard\status.cmd
scripts\dashboard\stop.cmd
scripts\dashboard\open.cmd
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8766/api/health |
    ConvertTo-Json -Depth 10
```

## Notes

- PowerShell `Activate.ps1` may be blocked by local execution policy and is **not required**.
- Optional CMD activation only: `.\.venv\Scripts\activate.bat`
- Correct path is `...\2026\.venv\Scripts\...` (slash before `.venv`), never `...\2026.venv\...`
- Startup success means: process alive **and** port listening **and** `/api/health` returns `status=ok`
- State file: `runs/state/dashboard.json` (gitignored under `runs/`)
- Log: `runs/state/dashboard.log`
- `qseh dashboard build` runs `pnpm install --frozen-lockfile` only when `node_modules` is missing (or with `--clean`)
