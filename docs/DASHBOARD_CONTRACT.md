# Dashboard contract

Reuse the Generals **design language and integration architecture**, not its game domain.

## Tokens

```text
#090D11 canvas
#11161C surface
#0C1116 deep
#161C24 elevated
#1E2630 border
#FFB000 amber
#FFC53D amber-high
#B37A00 amber-dim
#EAF0F6 foreground
#CDD6DF body
#A3AFBA secondary
#8593A1 metadata
#6F7C89 faint
2px radius
15px base
Montserrat / Raleway / JetBrains Mono
```

No generic purple SaaS.

## Top status

`EVENT | SDK | SCOPE | ROUND | UPLOADS | CHAMPION | GPU | AUTOPILOT`

## Navigation

OPERATE:
- Overview
- Event Control
- Round Room
- Data Lab

RESEARCH:
- Experiments
- Validation
- Models
- Feature Lab
- Ensembles

COMPETE:
- Leaderboard
- Submission
- Staking

SYSTEM:
- Compute & Jobs
- Repository
- Documentation

## High-value charts

Overview:
- rank/score trajectory;
- experiment score vs runtime frontier;
- fold evidence;
- quota allocation.

Experiments:
- score/runtime/diversity scatter;
- improvement by operator;
- timeline.

Validation:
- fold heatmap;
- per-exped curve;
- recent vs early;
- score distribution;
- search multiplicity.

Models:
- lineage;
- metric breakdown;
- runtime.

Feature Lab:
- missingness;
- cardinality;
- feature importance/stability;
- redundancy;
- exposure.

Ensembles:
- prediction correlation heatmap;
- marginal contribution;
- weights.

Leaderboard:
- rank trajectory;
- round/model matrix.

Round Room:
- current round clock;
- live dataset fingerprint;
- inference/submission queue;
- round scores;
- cumulative standings.

## Hard/soft display rule

Do not show soft quality evidence as a red blocking gate.

There must be separate visual sections:
- HARD INTEGRITY
- RESEARCH EVIDENCE

## Backend failure

Show `BACKEND UNAVAILABLE`.

Never silently switch to realistic fixtures.

## Figma integration

The final exported Figma graph is visual authority.

Cursor must copy the reachable component graph and replace only data/action adapters instead of “redesigning” it.
