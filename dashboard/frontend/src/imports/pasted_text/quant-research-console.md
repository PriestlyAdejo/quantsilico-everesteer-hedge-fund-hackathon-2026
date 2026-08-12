DROP-IN FIGMA MAKE PROMPT — QUANTSILICO × EVERESTEER 2026 RESEARCH CONSOLE

Build a desktop-first quantitative research/competition console for:

QuantSilico — Everesteer Hedge Fund Hackathon 2026

It will be exported and wired into an existing FastAPI/Python event repository.

This is event-specific, not the full QuantSilico platform.

Canonical visual system

Use the same family as my QuantSilico Generals Research Console:

--background: #090D11;
--surface: #11161C;
--surface-deep: #0C1116;
--elevated: #161C24;
--border: #1E2630;

--accent: #FFB000;
--accent-hi: #FFC53D;
--accent-dim: #B37A00;

--foreground: #EAF0F6;
--body-primary: #CDD6DF;
--body-secondary: #A3AFBA;
--metadata: #8593A1;
--faint: #6F7C89;

--radius: 2px;
--font-size: 15px;

Fonts:Montserrat / Raleway / JetBrains Mono.

No global violet accent.No glassmorphism.No huge rounded cards.No generic SaaS aesthetic.

Amber is interaction/brand, not every chart series.

Data architecture

All pages:useDataSource().

Implement interface plus:

DemoDataSource;

ApiDataSource skeleton.

No page imports fixtures.

Provenance:

OFFICIAL_EVENT_STATE

OFFICIAL_EVENT_DATA

OFFICIAL_PLATFORM_OBSERVATION

LOCAL_EXPERIMENT

SYNTHETIC_FIXTURE

MANUALLY_RECORDED

Demo values visibly say SYNTHETIC.Backend failure = BACKEND UNAVAILABLE.Never silently fake current event data.

Shell

Top bar:EVENT | SDK | AUTH SCOPE | ROUND | UPLOADS | CHAMPION | GPU | AUTOPILOT

Left groups:

OPERATE:

Overview

Event Control

Round Room

Data Lab

RESEARCH:

Experiments

Validation

Models

Feature Lab

Ensembles

COMPETE:

Leaderboard

Submission

Staking

SYSTEM:

Compute & Jobs

Repository

Documentation

Collapse sidebar to icon rail.Persist collapse.Ctrl+K / Cmd+K command palette.Persistent activity strip.

Overview

Metrics:

event clock/phase;

round;

upload budget;

champion;

cumulative rank;

local best;

practice/live scores;

frontier count;

jobs.

Charts:

score/rank trajectory;

experiment frontier scatter (runtime vs score, size/diversity);

fold evidence;

upload quota segmentation.

Latest decisions and integrity warnings below.

Event Control

Panels:

SDK version/scope/key fingerprint;

event ID/tournament;

capability matrix;

current scoring/rank metric/weights;

staking state;

latest event snapshot.

Controls:

refresh;

snapshot;

pull;

scorer parity;

baseline;

autopilot start/stop.

No arbitrary command input.

Round Room

Live cockpit:

round status/countdown;

live split fingerprint/rows;

inference queue;

submission queue;

current board;

cumulative standings;

event log;

emergency known-good panel.

Charts:

score by model;

rank by round;

model × round heatmap.

Data Lab

Train/validation/live cards/table:

hash;

rows;

cols;

expeds;

features;

targets;

duplicates;

memory;

updated.

Charts:

rows/exped;

missingness;

feature cardinality;

target distribution train only;

schema diff.

Hard integrity failures red.Warnings amber.Blank target ≠ zero.

Experiments

Dense sortable/filterable table:

run;

family;

operator;

parent;

race stage;

local;

recent;

lower quantile;

runtime;

diversity;

practice;

live;

status.

Comparison detail + config/lineage/raw drawer.

Charts:

score vs runtime;

score vs diversity;

timeline;

operator improvement.

Validation

Visually separate:

HARD INTEGRITY

schema

leakage

IDs

lane

scorer parity

artefact load

from:

SOFT RESEARCH EVIDENCE

mean

recent

dispersion

lower quantile

exposure

diversity

runtime

trial multiplicity.

Never make soft quality look like an absolute red veto.

Charts:

fold heatmap;

per-exped/cumulative score;

early vs recent;

distribution;

multiplicity timeline.

Show R0/R1/R2/R3.

Models

Table:

private local name;

opaque public alias;

family;

params;

parent;

data hash;

pickle hash/status;

inference latency;

lifecycle;

practice/live.

Detail:lineage, metrics, correlations, artefact checks.

Feature Lab

Features are anonymous/obfuscated.

Never invent economics.

Show:

missingness;

cardinality;

importance;

importance stability;

redundancy/correlation;

exposure;

selection frequency.

Ensembles

Show:

current blend;

members/weights;

local/practice/live.

Charts:

prediction-correlation heatmap;

marginal contribution bars;

score/diversity scatter;

weights;

fold score.

Controls:rank average / weighted / greedy / diversity-aware / optional neutralisation.

Leaderboard

Tabs:

current round;

cumulative;

our aliases;

history.

Charts:

rank trajectory;

score trajectory;

round/model matrix.

Official observations carry official provenance.

Submission

Quota:

total;

used;

practice;

live reserve;

emergency.

Validator:

lane;

split fingerprint;

ID coverage;

duplicates;

bounds;

pickle;

prediction/model hashes;

lineage.

Stepper:SELECT → INFER → VALIDATE → PACKAGE → DRY RUN → SUBMIT → RECORD.

Staking

Huge classification banner:

VIRTUAL EVENT BALANCE

REAL USDC / WALLET

NO STAKING

UNKNOWN

REAL = MANUAL CONFIRMATION REQUIRED.

VIRTUAL demo can show fake credits, clearly synthetic.

Show evidence/uncertainty/allocation/risk profile.

Compute & Jobs

CPU/RAM/GPU/VRAM.Local queue.Server-compute queue.Event watcher.Runtime history.Experiments/hour.

Allowlisted controls only.

Repository

Read-only:branch, SHA, dirty, SDK pin, Python, locks, latest commits, build, rehearsal.

No Git mutation.

Documentation

Search local docs.

UX states

Every page:loading/error/empty/stale/demo/backend-unavailable.

Raw record drawers.Accessible focus.Responsive.Dense scientific tables.Useful tooltips.

Synthetic fixtures

Never invent:

real rank;

real cap;

real staking balance;

real key.

Use:DEMO / SYNTHETIC / UNKNOWN / NOT CONNECTED.

Model demo names can include organiser-lgbm, ridge-01, extra-trees-01, blend-01 but must be labelled synthetic.

Export readiness

React + TypeScript + Vite.Keep clean DataSource boundary.Do not build a fake Python backend.Document dependencies and DataSource method coverage.Preserve pnpm lock.Create FIGMA_EXPORT_NOTES.md.

Visual verification

Run every route.Automated screenshots if possible under ignored:artifacts/ui-review/figma-final/.

Do not ask me for screenshots.Fix clipping/overflow/charts/navigation.

The finished prototype should clearly share the Generals console's design DNA but be purpose-built for futures ML research, experimentation, live rounds and submission/staking control.

Proceed. Do not ask another palette question.