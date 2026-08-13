# QuantSilico — Everesteer Hedge Fund Hackathon 2026

Independent event-specific research tooling for the Everesteer Hedge Fund Hackathon, London, 13 August 2026.

Not affiliated with or endorsed by Everesteer or EverestQuant.

## Research loop

`discover -> ingest -> verify -> baseline -> race -> validate -> ensemble -> submit -> observe -> adapt`

## Design choices

- current event/API state beats stale assumptions;
- hard-stop integrity failures only;
- quality evidence is graded;
- baseline first;
- broad cheap experimentation before deep work;
- every serious trial retained;
- CLI is critical path;
- local research console is a viewer/controlled launcher;
- no organiser data/secrets committed.

## Official references

SDK:
https://pypi.org/project/everestapi/

Docs:
https://docs.everesteer.ai/

Examples:
https://github.com/everestquant/example-scripts

Platform:
https://everesteer.ai/

See `docs/`.

## Quick start (local / synthetic)

```text
python -m venv .venv
.venv\Scripts\pip install -e ".[dashboard,dev]"
set QSEH_SYNTHETIC=1
qseh doctor
qseh data pull --split train
qseh race --profile fast
qseh dashboard start
```

Do not run `Activate.ps1`. Use `.\.venv\Scripts\qseh.exe` and `.\.venv\Scripts\python.exe` from the repo root.

Operator guide (also in the Research Console Documentation page): `docs/runbooks/event-day.mdx`

Safe local check before the venue:

```text
scripts\preflight.cmd
```

Dashboard: http://127.0.0.1:8766/

Submission default mode is `DRY_RUN`. Real uploads require an explicit:

```text
qseh event arm-submissions
```

Status reports: `docs/IMPLEMENTATION_STATUS.md`, `docs/DASHBOARD_INTEGRATION_REPORT.md`, `docs/REHEARSAL_REPORT.md`.

Dashboard ops (no PowerShell activation required): see `docs/DASHBOARD_OPERATIONS.md`.
