# Target repository tree

```text
quantsilico-everesteer-hedge-fund-hackathon-2026/
├── README.md
├── AGENTS.md
├── pyproject.toml
├── .env.example
├── .gitignore
│
├── configs/
│   ├── event/
│   │   └── everesteer_london_2026.yaml
│   ├── autopilot/
│   │   └── competition_aggressive.yaml
│   ├── models/
│   │   ├── organiser_lgbm.yaml
│   │   ├── lgbm_regularised.yaml
│   │   ├── ridge.yaml
│   │   ├── random_forest.yaml
│   │   ├── extra_trees.yaml
│   │   └── xgboost.yaml
│   ├── validation/              # Cursor adds smoke/fast/standard/promotion
│   └── ensembles/               # Cursor adds rank/greedy/diverse configs
│
├── src/
│   └── qs_everesteer/
│       ├── cli.py
│       ├── contracts.py
│       ├── event/
│       │   ├── adapter.py
│       │   ├── capabilities.py  # target
│       │   ├── snapshot.py      # target
│       │   └── watcher.py       # target
│       ├── data/
│       │   ├── audit.py
│       │   ├── synthetic.py
│       │   ├── fingerprint.py   # target
│       │   └── ingest.py        # target
│       ├── validation/
│       │   ├── scoring.py
│       │   ├── splits.py        # target
│       │   └── evidence.py      # target
│       ├── models/              # target
│       │   ├── base.py
│       │   ├── registry.py
│       │   ├── linear.py
│       │   └── trees.py
│       ├── experiments/
│       │   ├── runner.py
│       │   ├── racing.py
│       │   ├── ledger.py        # target
│       │   └── research_state.py# target
│       ├── selection/
│       │   └── frontier.py
│       ├── ensemble/
│       │   └── blend.py
│       ├── submission/
│       │   ├── guard.py
│       │   └── budget.py        # target
│       ├── live/
│       │   └── rounds.py
│       ├── staking/             # target
│       ├── compute/             # target
│       ├── autopilot/
│       │   └── orchestrator.py
│       └── reports/             # target
│
├── dashboard/
│   ├── backend/
│   │   └── app/main.py
│   └── frontend/
│       └── README.md            # replaced by exact Figma export integration
│
├── scripts/
│   └── dashboard/
│       ├── start.cmd
│       ├── stop.cmd
│       ├── status.cmd
│       └── open.cmd
│
├── docs/
│   ├── RESEARCH_DOSSIER.md
│   ├── KNOWN_UNKNOWN_RUNTIME_DETECTION.md
│   ├── VALIDATION_AND_PROMOTION.md
│   ├── ARCHITECTURE.md
│   ├── AUTOPILOT.md
│   ├── DAY_OF_PLAYBOOK.md
│   ├── WORKFLOW_DEMO.md
│   ├── MONITORING_LINKS.md
│   ├── DASHBOARD_CONTRACT.md
│   ├── FAILURE_RECOVERY.md
│   ├── BUILD_PRIORITY.md
│   ├── QUANTSILICO_REUSE_MAP.md
│   └── prompts...
│
├── tests/
│   ├── test_contracts.py
│   ├── unit/                    # target
│   ├── integration/             # target
│   └── regression/              # target
│
├── data/
│   ├── synthetic/               # generated locally
│   ├── official/                # gitignored
│   └── cache/                   # gitignored
│
├── runs/
│   ├── experiments/             # manifests
│   ├── state/
│   ├── event/                   # gitignored
│   └── leaderboard/             # gitignored
│
└── artifacts/
    ├── models/                  # gitignored
    ├── predictions/             # gitignored
    └── submissions/             # gitignored
```

The tree is intentionally smaller than a full QuantSilico platform. Cursor should add modules when they implement a real event requirement, not create empty abstraction layers for appearance.
