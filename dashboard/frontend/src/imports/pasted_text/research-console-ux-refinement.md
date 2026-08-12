QUANTSILICO × EVERESTEER 2026 RESEARCH CONSOLE — FINAL UX / OPERATING-SYSTEM REFINEMENT

The existing Research Console implementation is structurally good, but this pass is a serious UX, semantics, readability, live-operation and documentation refinement.

Do not redesign the product from scratch.

Preserve:

terminal-dark QuantSilico visual identity;
left grouped navigation;
top operating status bar;
existing route structure;
DataSource architecture;
current charts where still useful;
React Router;
allowlisted actions;
hard-integrity vs soft-evidence architecture;
competition-specific research-console purpose.

The objective is to make this interface something I can genuinely operate during a live five-hour quantitative ML competition.

1. REMOVE PROVENANCE / DEMO BADGE CLUTTER

The current application over-renders internal metadata.

Remove routine visual badges such as:

SYNTHETIC beside every page title;
OFFICIAL OBSERVATION repeated on every leaderboard row;
repetitive provenance chips;
unnecessary little documentation tags such as sdk, setup, baseline;
similar labels whose information is already obvious from context.

Do not delete provenance from the data model.

Keep:

provenance
sourceId
eventSnapshotId
generatedAt

internally.

Expose provenance only where it is genuinely useful:

raw-record/detail drawer;
source tooltip;
page-level source line;
debugging/developer inspection.

For a normal live page, prefer:

Source: Everesteer API
Updated 18:42:06

once near the page header.

Do not repeat the same source in every row.

Never display contradictory states such as:

SYNTHETIC
OFFICIAL OBSERVATION

on the same dataset.

If explicit demo mode is still required for development, use at most one subtle global preview-mode indication. It must disappear completely in API/production mode.

2. REMOVE FABRICATED RUNTIME FACTS

The current fixture contains realistic-looking but incorrect information such as:

SDK 0.9.4;
Apple M2 Pro;
GPU not detected;
hard-coded round R3 / 8;
hard-coded upload 12 / 20;
hard-coded competition phase;
fabricated scoring semantics;
fixed model/round counts.

These may exist internally as fixtures only to exercise layouts, but they must not appear as authoritative constants in the production-oriented implementation.

Production UI values come exclusively from DataSource/backend responses.

When disconnected, show:

NOT CONNECTED
WAITING FOR EVENT
UNKNOWN
NOT AVAILABLE
—

rather than invented numbers.

Zero is real data.

Unknown is state.

Never represent unknown as 0, 0.000, $0, rank 0, 0 GB, etc.

3. FIX EVENT-CONTROL SCORING SEMANTICS

The current Event Control implementation shows concepts such as:

Pearson R (annualised)
Practice 30%
Live 70%

under scoring.

Remove this.

The Figma console must not invent the competition scoring formula.

The scoring panel is a dynamic rendering contract for backend-provided event scoring.

Structure it approximately as:

Current scoring
Rank metric        <runtime value>
Primary target     <runtime value>

CORR20             <weight/value if available>
AIMC               <weight/value if available>
NCORR               <weight/value if available>

Scoring snapshot   <timestamp>

If an item is not exposed:

NOT PROVIDED BY EVENT

Practice/live submission allocation belongs to Submission, not scoring.

4. ADD A CLEAR OPERATING FLOW

The present pages are individually useful but the user cannot immediately understand the order in which they should be used.

Do not number the sidebar pages.

Instead, add a compact global operating flow to Overview:

CONNECT EVENT
    →
DATA READY
    →
BASELINE PROVEN
    →
RESEARCH
    →
VALIDATE
    →
ENSEMBLE
    →
SUBMIT
    →
LIVE ROUND
    →
STAKE / FINALISE

Each node supports states such as:

waiting
ready
active
complete
attention
blocked

Highlight the current stage.

Under it show:

Recommended next action

Example:

Train data verified. Reproduce the organiser baseline before starting the research race.

[Run baseline]   [Open Data Lab]

This recommendation is supplied by DataSource/backend state rather than guessed by the frontend.

The sidebar can optionally display one subtle amber indicator beside the contextually recommended page.

Do not clutter every nav item with statuses.

5. HUMANISE EVERY PAGE

Every page gets a short 1–2 sentence explanation directly beneath its title.

No generic AI marketing copy.

Use practical language.

Use approximately these meanings:

Overview

Start here. See where the event is, what the research loop is doing, what is currently winning, and what needs attention next.

Event Control

Connect to Everesteer and verify the live event rules before doing anything that depends on them. This is the source of truth for rounds, scoring, capabilities and submission limits.

Round Room

Use this during an open round. Track the current live dataset, inference jobs, submissions, leaderboard movement and the time remaining.

Data Lab

Check what data arrived, whether it is safe to model, and how train, practice and live splits differ.

Experiments

Everything we have tried, what changed between runs, and which research branches are still worth compute.

Validation

Decide whether a result can be trusted, how strong the evidence is, and whether the candidate deserves more budget.

Models

Registry of trained model artefacts: lineage, performance, latency, stability and submission readiness.

Feature Lab

Statistical diagnostics for anonymous features. Analyse behaviour and stability without inventing economic identities.

Ensembles

Combine models only when they contribute independent signal. Compare overlap, marginal improvement and robustness before promoting a blend.

Leaderboard

External evidence from Everesteer: current round, cumulative standing and how our submitted aliases have moved over time.

Submission

The controlled path from a research candidate to a valid practice or live upload. Every submission is checked before it leaves the machine.

Staking

Use only after the event explains the staking mechanism. Compare model evidence, uncertainty and concentration before allocating anything.

Compute & Jobs

See what is running, how much machine capacity is being used, when results are expected and what is queued next.

Repository

The exact code, environment and build state producing the current research results.

Documentation

Generated reference documentation plus human-written runbooks and end-to-end operating flows.

Do not display these as badges.

6. HUMANISE MACHINE DECISIONS

Keep internal enums.

Change visible language.

Instead of:

PROMOTE — DIVERSITY SLOT

show:

Advance to R2 — adds useful independent signal

Instead of:

RETIRED — DOMINATED

show:

Stop exploring — another candidate is better on the same trade-offs

Instead of:

RETIRED — SATURATED FAMILY

show:

Stop this branch — recent variants are no longer improving

Instead of:

INVALID — INTEGRITY FAILURE

show the actual reason:

Blocked — prediction IDs do not match the current split

The raw enum/code remains accessible in the detail drawer.

7. READABILITY PASS

The current interface is too small/dim in several places.

Preserve density but improve hierarchy.

Do not globally enlarge everything.

Target approximately:

page title              18–20px
primary metric value    17–22px
section heading         12–14px
body/table text         12–13px minimum
metadata                10.5–11.5px

Use sufficient line-height.

Increase contrast for meaningful secondary text.

Reduce excessive tiny all-caps labels.

Use uppercase selectively for instrumentation/status, not every heading.

At 1280×800 the application must remain genuinely usable.

8. TOP STATUS BAR RESPONSIVENESS

The current top bar contains too much information at once.

Always keep these visible where possible:

EVENT / CONNECTION
ROUND
UPLOADS
CHAMPION
AUTOPILOT
LIVE FEED

Secondary values such as:

SDK
AUTH SCOPE
GPU

may collapse into the system/status control at narrower desktop widths.

Add a live connection state:

LIVE · updated 4s ago
RECONNECTING
DISCONNECTED

Do not use another provenance chip for this.

9. GLOBAL LIVE-DATA BEHAVIOUR

The final UI must be designed around continuously changing backend data.

Create consistent behaviour for:

event state
current round
jobs
experiments
models
leaderboard
submission state
staking state
compute usage

Each domain defines:

updatedAt
staleAfter
refreshMode

Support:

SSE / WebSocket pushed updates
bounded polling fallback
manual refresh

The frontend should not refresh everything at the same frequency.

A slowly changing repository page does not need the same cadence as Round Room.

Show stale state only when meaningful.

10. DYNAMIC COLLECTIONS — NO FIXED MODEL/ROUND COUNTS

No production component may assume:

4 models
5 rounds
20 leaderboard rows
40 experiments

All tables, charts and heatmaps render arbitrary arrays.

The model × round score matrix uses dynamic:

models[]
rounds[]
scores

If there are many models:

vertical scroll;
search/filter;
optionally show selected/frontier/submitted models first.

If rounds grow:

horizontal scroll;
sticky row labels;
latest round kept visible.

The prediction-correlation matrix likewise grows with the currently selected candidate set.

Large experiment/feature tables use virtualisation or efficient pagination rather than rendering thousands of DOM rows.

11. PAGE-LEVEL CONTEXT SELECTORS

Use useful selectors rather than decorative tags.

Research pages may expose context controls such as:

Candidate
Model family
Race stage
Round
Split
Time/fold window
Status

Selections should update all applicable panels consistently.

Do not make a separate dashboard for each model/round.

12. RUNNING JOBS MUST SHOW TIME

For every asynchronous or long-running process support:

started at
elapsed
estimated remaining
expected finish
progress if measurable
queue position where relevant

Examples:

LightGBM R2
Running 3m 12s
~2m remaining
Expected 04:34

or:

Estimating runtime…

when there is not enough history.

Apply to:

training;
inference;
validation;
data pull;
scorer parity;
ensemble builds;
server compute;
submissions when asynchronous;
documentation generation;
autopilot stages.

ActivityStrip should display the most important active job and link to Compute & Jobs.

13. OVERVIEW IMPROVEMENTS

Keep the current page structure but improve it.

Top metrics should prioritise:

event phase
round
upload budget
champion
external rank
local best
practice score
live score
active jobs

Add a second compact research metrics strip:

CORR20 / primary IC
ICIR
positive expeds
recent-vs-history
worst fold
local→external gap

Only render metrics supported by actual data.

Experiment frontier chart

Fix current unreadable runtime axis.

Use human units:

10s
30s
1m
2m
5m

Encoding:

x = runtime/compute
y = local event-equivalent score
size = novelty/diversity
shape = family
outline = race stage/frontier state

Use good tooltips.

Upload quota

Show:

used
practice allocation
live reserve
emergency reserve
remaining

Do not call this scoring weight.

14. EVENT CONTROL IMPROVEMENTS

Show four primary areas:

Connection
API status
SDK version
scope
key fingerprint
last successful request
Event state
event
tournament
phase
current round
round opened
time remaining
Scoring

Runtime-provided:

target
rank metric
CORR20
AIMC
NCORR
other event-provided components
Capabilities

Human names:

Practice submissions
Live submissions
Leaderboard
Cumulative standings
Server compute
Event staking

Use:

Available
Unavailable
Unknown

not technical enum spam.

Controls remain allowlisted.

15. ROUND ROOM IMPROVEMENTS

This should be the strongest event-day page.

Top:

round
status
time remaining
dataset fingerprint
rows
submissions used / remaining for round/event
live feed status

Inference and submission queues show:

model
stage
started
elapsed
ETA
expected finish
status

Current leaderboard:

replace ambiguous Δ with a clear label such as:

Score change
Rank change

depending on what it actually represents.

Never use one symbol without an explanation.

Rank trajectory

Rank 1 is best.

Make this visually unambiguous.

If rank is charted vertically, use an inverted rank axis and label:

1 = best
Emergency panel

Show:

known-good champion
known-good ensemble
model hash
current split verified
submission readiness
16. DATA LAB IMPROVEMENTS

Cards remain:

Train
Practice/Validation
Live

Use the real event naming supplied by backend.

Show:

fingerprint
rows
columns
features
expeds
targets
target availability
duplicates
missingness
memory
updated

If exped is used, provide a tooltip explaining the event field.

Add:

schema drift
missingness drift
feature cardinality drift
target availability
ID overlap

Keep charts but improve labels/axes.

No fabricated feature-name semantics.

17. EXPERIMENTS IMPROVEMENTS

The current experiment table is too visually compressed.

Use:

sticky header;
sticky run/name column;
search;
sorting;
filters;
column visibility controls;
efficient large-table rendering.

Default important columns:

Run
Family
Change
Stage
Local score
Recent score
Stability
Runtime
Diversity
Practice
Live
Decision

Technical details belong in expandable/detail view.

When a row is selected, open a substantial detail drawer/panel showing:

hypothesis
parent
operator/config change
resolved parameters
all metric components
folds
OOF path
artefact
resources
decision rationale
children
logs

Add charts:

score vs runtime
score vs diversity
score improvement by operator
experiments over time
family saturation
18. VALIDATION IMPROVEMENTS

Keep the underlying three-part philosophy, but make it human.

Display headings:

Can this result be trusted?

Integrity checks.

How strong is the evidence?

Research metrics.

What happens next?

Race decision.

Under integrity:

Schema
Leakage
ID alignment
Submission lane
Scorer parity
Model artefact

Under evidence add:

Rank metric
CORR20
AIMC
NCORR
mean IC
median IC
IC standard deviation
ICIR
positive exped %
recent-window IC
lower quantile
worst fold
feature exposure
prediction diversity
runtime
local→practice gap
trial count

Only show metrics actually available.

Charts:

per-exped IC/CORR
cumulative IC
fold matrix
score distribution
early vs recent
component score by fold
19. MODELS IMPROVEMENTS

The current page leaves too much unused space when only a few models exist.

Keep the registry table but add a selected-model inspection region.

Summary metrics:

local score
recent score
practice
live
ICIR
worst fold
inference p50/p95
model size
prediction exposure

Selected-model charts:

fold performance
per-exped performance
score components
feature importance summary
correlation to champion
latency/resource history

Support compare mode for 2–5 models.

Model names and rows are fully dynamic.

20. FEATURE LAB IMPROVEMENTS

The current long table needs better navigation.

Use:

sticky header;
sticky feature name;
search;
sort;
filters;
virtualised rows.

Top summary:

feature count
high-missingness
unstable features
high exposure
selected-by-frontier models

Table concepts may include:

feature
missingness
cardinality
importance
importance stability
exposure
selection frequency
drift

On row selection open feature detail:

distribution
missingness through time
importance through folds
correlation neighborhood
model-selection history

Feature names come from actual data.

Do not invent economic names.

21. ENSEMBLES MUST ACTUALLY WORK

The current selectors cannot remain decorative tabs.

Strategies:

Rank average
Weighted
Greedy
Diversity-aware
Neutralised

must correspond to real DataSource/backend capabilities.

Selecting a strategy updates the relevant controls.

Examples:

Weighted

editable model weights with validation that they satisfy the backend contract.

Greedy

show candidate pool and selected order.

Diversity-aware

show diversity penalty/constraint if exposed.

Neutralised

show only when the active scorer/backend supports the operation.

Add candidate/member selectors.

Provide:

Build preview
Compare to champion
Save candidate
Promote blend

as allowlisted operations where backend supports them.

Metrics:

local uplift vs best member
recent uplift
worst-fold change
mean pairwise correlation
effective model count/concentration
feature-exposure change
practice uplift
live uplift

Keep:

prediction correlation heatmap;
marginal contribution;
score vs diversity;
fold score.

All dynamic.

22. LEADERBOARD IMPROVEMENTS

Remove the repeated provenance column.

Header contains:

Source: Everesteer
Updated <time>

Tabs remain:

Current round
Cumulative
Our models
History

Columns should use clear names:

Rank
Model
Score
Score change
Rank change

only where that data exists.

Add:

local-vs-practice gap
practice-vs-live gap

for our own submitted aliases where enough evidence exists.

Rank trajectory must make rank direction obvious.

Tables and charts adapt to arbitrary participants/rounds.

23. SUBMISSION PAGE MUST REFLECT REAL JOB STATE

The current manual ADVANCE / RESET demo behaviour is not appropriate for production.

Remove fake manual stage progression.

The pipeline remains:

SELECT
→ INFER
→ VALIDATE
→ PACKAGE
→ DRY RUN
→ SUBMIT
→ RECORD

but stages reflect real backend jobs/actions.

A user action begins an operation; backend state advances it.

Show:

started
elapsed
ETA
result
error/retry

Practice and Live submission buttons are enabled only when:

event capability permits lane
candidate IDs match
prediction artefact exists
model artefact exists
quota allows
hard integrity passes

Provide actual blocking reason beside a disabled action.

Candidate list is dynamic.

24. STAKING

Remove unnecessary status tags.

The page begins with plain language:

Staking is not yet available for this event.

or:

This event uses virtual competition balance.

or:

This action involves a real wallet and requires manual confirmation.

depending on backend classification.

Show evidence:

model/blend
local evidence
live evidence
uncertainty
correlation
proposed allocation
concentration

No real-wallet action becomes autonomous.

25. COMPUTE & JOBS MUST USE REAL HARDWARE

Remove Apple M2 fixture presentation from the production-oriented UI.

The backend supplies:

OS
CPU
RAM total/used
GPU
VRAM
CUDA
disk

If a device is absent:

Not detected

is fine.

Job table:

Job
Type
Candidate
Status
Started
Elapsed
ETA
Expected finish
CPU/GPU

Add:

queue length
experiments/hour
GPU utilisation
VRAM utilisation
RAM pressure

where supported.

Do not over-refresh expensive hardware probes.

26. REPOSITORY PAGE

Remain read-only.

Add useful operational context rather than empty space:

serving branch
serving SHA
dirty state
Python
everestapi
lockfile hash
frontend build SHA
backend build SHA
last tests
last rehearsal
last scorer-parity result
environment health

Latest commits remain.

No Git mutations.

27. REBUILD DOCUMENTATION PAGE

Replace the existing placeholder cards/tags.

Create internal documentation navigation:

Start Here
Competition Workflow
Research Loop
Data & Validation Flow
Model Lifecycle
Live Round Flow
Submission Flow
Staking Flow
CLI Reference
Python API
Backend API
Configuration Reference
Runbooks
Glossary

The page has:

search;
generated/manual source indicator only in document metadata, not badge spam;
table of contents;
previous/next document navigation;
copyable commands;
linked routes into the dashboard.
28. DOCUMENTATION GENERATION CONTRACT

The Figma frontend only designs this contract.

Cursor/backend later implements generation.

The production docs system should support:

docs/generated/
docs/flows/
docs/runbooks/

Generated reference should be derived from real code where possible:

Python modules/classes/functions → docstrings
Typer CLI → commands/options/help
FastAPI → OpenAPI routes/schemas
Pydantic/config models → configuration reference
build metadata → version/environment reference

A generated docs manifest should feed the frontend documentation search/index.

Do not hand-copy API signatures into React components.

29. CURATED MDX FLOW PAGES

Workflow explanations remain human-curated MDX.

Provide reusable components such as:

<PageIntro />
<FlowDiagram />
<FlowStep />
<Callout />
<Command />
<MetricDefinition />
<RelatedPage />

Design the renderer for MDX documents of this general form:

---
title: Live round workflow
description: What happens from round open to recorded result.
section: flows
order: 40
---

<PageIntro>
Use this flow when Everesteer opens a live round. The objective is to move from
a verified live split to a recorded submission without rebuilding the research
system.
</PageIntro>

<FlowDiagram
  nodes={[
    { id: "detect", label: "Detect round" },
    { id: "snapshot", label: "Snapshot event" },
    { id: "pull", label: "Pull live data" },
    { id: "verify", label: "Verify split and IDs" },
    { id: "infer", label: "Run inference" },
    { id: "guard", label: "Submission checks" },
    { id: "submit", label: "Submit" },
    { id: "observe", label: "Record score and standing" }
  ]}
/>

## What to watch

<MetricDefinition name="Time remaining">
How long the current round remains open.
</MetricDefinition>

<MetricDefinition name="Upload budget">
How many external submissions remain available.
</MetricDefinition>

## If something fails

<Callout tone="warning">
Do not retrain automatically because a submission failed. First check lane,
IDs, event state and the model artefact.
</Callout>

<RelatedPage href="/round">Open Round Room</RelatedPage>

Also support a research-flow document such as:

---
title: Research loop
description: How a hypothesis becomes a candidate, frontier member or retired branch.
section: flows
order: 20
---

<FlowDiagram
  nodes={[
    { id: "hypothesis", label: "Hypothesis" },
    { id: "r0", label: "Smoke test" },
    { id: "r1", label: "Fast race" },
    { id: "r2", label: "Standard evidence" },
    { id: "frontier", label: "Frontier" },
    { id: "ensemble", label: "Ensemble candidate" }
  ]}
/>

These MDX files are drop-in source documents, not manually recreated JSX pages.

30. DOCUMENTATION AUTO-REFRESH

The eventual integration should support a docs-build command conceptually like:

qseh docs build

which regenerates:

CLI reference
Python API reference
backend API reference
configuration reference
docs search manifest

Documentation page should show:

Generated from commit <SHA>
Generated <timestamp>

in subtle metadata.

Manual flow/runbook documents remain unchanged unless their source MDX changes.

31. TABLE DESIGN

All large tables should follow a consistent pattern:

clear title/purpose
search
filters
sorting
column visibility
sticky headers
row selection
detail drawer

Avoid displaying every low-level field in the main table.

Use progressive disclosure.

32. TOOLTIP / GLOSSARY

Technical abbreviations remain where they are useful, but provide definitions.

Examples:

CORR20
AIMC
NCORR
IC
ICIR
exped
OOF
frontier

Use:

hover tooltip;
documentation link;
Glossary page.

Do not replace domain terminology with vague generic wording.

33. EMPTY SPACE

Do not fill sparse pages with decorative cards merely to occupy space.

Instead:

selected-row detail panel;
context help;
useful historical plots;
recent activity;
system status.

Models and Repository currently have especially large unused areas.

Make them useful without turning them into visual clutter.

34. VISUAL QA

Test at:

1280×800
1440×900
1920×1080

At 1280×800 specifically verify:

readable text;
top bar;
sidebar;
tables;
no clipped charts;
usable Round Room;
usable Submission;
useful Experiment table.

Fix raw float axes.

Fix ambiguous symbols.

Fix tiny table typography.

Fix excessive muted text.

Fix unnecessary uppercase.

35. DO NOT EXPAND THE MAIN SIDEBAR

The existing page set is enough.

Documentation gets its own internal sub-navigation.

Do not create more top-level dashboard pages simply because new documentation flows exist.

36. FINAL PRODUCT TEST

Before finishing:

Navigate every route.
Confirm routine SYNTHETIC/OFFICIAL provenance badge clutter is gone.
Confirm fixture values are not hardcoded into domain components.
Confirm Event Control does not invent scoring semantics.
Confirm all large collections are array-driven and dynamic.
Confirm ensemble selectors perform actual DataSource actions in demo mode.
Confirm submission stages reflect state rather than blindly advancing.
Confirm job ETA/elapsed UI exists.
Confirm every page has useful human explanation.
Confirm Overview communicates the operating flow and next action.
Confirm documentation has flow/article navigation instead of placeholder cards.
Confirm MDX flow components render.
Confirm 1280×800 usability.
Confirm DataSource architecture remains intact.
Confirm final export notes document all new contracts.

Do not redesign the visual identity.

Make the existing console clearer, more human, more dynamic, more quant-research-oriented and genuinely operable during a live competition.