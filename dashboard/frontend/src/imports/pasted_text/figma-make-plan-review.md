Yes — **this is a good Figma Make plan**. I’d put it around **8.5–9/10** as a frontend implementation plan. It understood the visual system, the page taxonomy, the provenance rule, the hard-integrity-vs-soft-evidence distinction, and—most importantly—it did **not** turn the thing into a generic purple SaaS dashboard.

I would let Figma Make proceed, **but I would amend several things first**, because a few choices could make the later Cursor/FastAPI integration unnecessarily awkward.

The biggest issue is this line:

> **Client-side routing via `useState` in Shell (no React Router — keeps the export clean).**

I wouldn't do that. For a 14-page application that will later become the actual local research console, proper URL routing is worth having. Otherwise `/validation`, `/round-room`, `/leaderboard`, etc. don't really exist as routes; refresh/deep-link behaviour gets ugly, browser history is poor, and Cursor will later have to restructure navigation during the exact-port integration. You already know from the Generals work that **the less structural reinterpretation Cursor has to do after Figma, the better**.

Use React Router if it's already available or reasonably installable. The shell still stays clean:

```text
/
 /event
 /round
 /data
 /experiments
 /validation
 /models
 /features
 /ensembles
 /leaderboard
 /submission
 /staking
 /compute
 /repository
 /docs
```

That is a much better handoff boundary.

The second issue is that the proposed `DataSource` only contains **reads**:

```ts
getOverview()
getEventControl()
...
```

but your interface contains quite a few real operations:

```text
refresh event
snapshot event
pull datasets
run scorer parity
run baseline
start autopilot
stop autopilot
build ensemble
validate submission
submit practice
submit live
stop job
```

If Figma Make doesn't model those now, Cursor will later have to modify a lot of component contracts.

I would make the Figma prototype's DataSource represent **both reads and allowlisted actions from day one**.

Third, I would tighten the provenance contract. Saying "every record has SYNTHETIC provenance" is good, but it should be impossible for a page to accidentally lose it. I'd make all major response envelopes carry something like:

```ts
interface DataEnvelope<T> {
  schemaVersion: number
  kind: string
  provenance: Provenance
  generatedAt: string
  stale: boolean
  data: T
}
```

Then the frontend can show:

```text
SYNTHETIC FIXTURE
OFFICIAL EVENT STATE
LOCAL EXPERIMENT
STALE
```

consistently rather than each page inventing provenance behaviour.

The fourth issue is **DemoDataSource fallback behaviour**. The plan says `ApiDataSource` returns `BACKEND_UNAVAILABLE`, which is correct, but I would explicitly forbid `useDataSource()` from doing something like:

```ts
try API
catch -> DemoDataSource
```

That particular fallback is dangerous for this product because a backend outage could suddenly make the console appear healthy with plausible-looking fake experiment results.

It should instead be:

```text
mode=demo
    -> DemoDataSource

mode=api
    -> ApiDataSource
       backend dies
       -> BACKEND UNAVAILABLE
```

No automatic fallback.

There are also several smaller but worthwhile corrections. Rather than asking for "steel-blue variants for model series", define a tiny stable chart palette now so Figma doesn't make every page subtly different. Make chart legends always identify model aliases. Add `asOf`/last-updated timestamps to live/event panels. Make the Round Room and Event Control explicitly show `UNKNOWN` rather than blank values. Require the submission stepper to have disabled/error/retry states rather than merely animate through seven demo states. And make the command palette aware of both routes and **allowlisted actions**, even if actions are demo callbacks for now.

The Validation page needs one additional visual concept because this is central to the changed architecture:

```text
HARD INTEGRITY
──────────────
PASS / FAIL / UNKNOWN

RESEARCH EVIDENCE
─────────────────
strong / mixed / weak / insufficient evidence

RACE DECISION
─────────────
PROMOTE R1 → R2
KEEP AS DIVERSITY CHALLENGER
RETEST
RETIRE
```

That third section matters. Otherwise the UI can still accidentally make the old mistake of equating "soft metric isn't great" with "model failed".

Similarly, the Experiments page should show **why** something advanced:

```text
PROMOTED — TOP LOCAL SCORE
PROMOTED — DIVERSITY SLOT
PROMOTED — EXPLORATION SLOT
RETAINED — ENSEMBLE VALUE
RETIRED — DOMINATED
RETIRED — SATURATED FAMILY
FAILED — OOM
INVALID — ID ALIGNMENT
```

That makes your new racing philosophy legible rather than hidden inside Python.

I would also change the Overview scatter description from just:

> marker size = diversity

to something a little more useful:

```text
x = runtime
y = event-equivalent local score
size = novelty/diversity
shape = model family
outline/status = R0/R1/R2/R3/frontier
```

That plot could become one of the genuinely useful day-of views.

One other technical detail: **Recharts doesn't give you a nice general-purpose heatmap component out of the box.** That's not a reason not to use it, but tell Figma Make it may implement heatmaps with a small custom SVG/grid component rather than forcing everything through Recharts. Otherwise it may generate something bizarre for the prediction-correlation matrix and round×model matrix.

And the verification section is currently a bit light. "Navigate every route" is good, but I'd also require actual screenshot review at desktop widths because this dashboard has dense tables. Check at least around `1440×900`, `1920×1080`, and a narrower laptop width like `1280×800`. The event will be run on your laptop, so the compact laptop breakpoint actually matters more than mobile.

### What I would add before telling Figma Make to execute

Paste this underneath its existing plan:

# REQUIRED AMENDMENTS BEFORE IMPLEMENTATION

The plan is approved subject to the following amendments. Apply these directly rather than treating them as optional suggestions.

## 1. Use real URL routing

Do not implement page navigation as a single `useState` page selector.

Use React Router or the lightest existing proper router available in the project.

Required route structure should approximately be:

```text
/
 /event
 /round
 /data
 /experiments
 /validation
 /models
 /features
 /ensembles
 /leaderboard
 /submission
 /staking
 /compute
 /repository
 /docs
```

Sidebar navigation and CommandPalette navigation must use the same route registry.

Browser back/forward, route refresh and direct deep links must work.

This is important because the exported Figma implementation will later be ported directly into the production FastAPI-backed repository. Cursor should not have to redesign navigation during integration.

---

## 2. Expand DataSource to cover reads AND allowlisted actions

The DataSource abstraction is not read-only.

It must represent the controls already present in the product.

Use a contract conceptually similar to:

```ts
export interface DataSource {
  // reads
  getOverview(): Promise<DataEnvelope<OverviewData>>
  getEventControl(): Promise<DataEnvelope<EventControlData>>
  getRoundRoom(): Promise<DataEnvelope<RoundRoomData>>
  getDataLab(): Promise<DataEnvelope<DataLabData>>
  getExperiments(): Promise<DataEnvelope<ExperimentRow[]>>
  getValidation(): Promise<DataEnvelope<ValidationData>>
  getModels(): Promise<DataEnvelope<ModelRow[]>>
  getFeatureLab(): Promise<DataEnvelope<FeatureLabData>>
  getEnsembles(): Promise<DataEnvelope<EnsembleData>>
  getLeaderboard(): Promise<DataEnvelope<LeaderboardData>>
  getSubmission(): Promise<DataEnvelope<SubmissionData>>
  getStaking(): Promise<DataEnvelope<StakingData>>
  getComputeJobs(): Promise<DataEnvelope<ComputeData>>
  getRepository(): Promise<DataEnvelope<RepoData>>
  getDocumentation(): Promise<DataEnvelope<DocumentationData>>

  // allowlisted actions
  refreshEvent(): Promise<ActionResult>
  snapshotEvent(): Promise<ActionResult>
  pullDatasets(): Promise<ActionResult>
  runScorerParity(): Promise<ActionResult>
  runOfficialBaseline(): Promise<ActionResult>
  startAutopilot(): Promise<ActionResult>
  stopAutopilot(): Promise<ActionResult>
  startRace(profile: string): Promise<ActionResult>
  buildEnsemble(): Promise<ActionResult>
  validateSubmission(candidateId: string): Promise<ActionResult>
  submitPractice(candidateId: string): Promise<ActionResult>
  submitLive(candidateId: string): Promise<ActionResult>
  stopJob(jobId: string): Promise<ActionResult>
}
```

The exact type names can differ, but preserve this architectural division.

There must be no arbitrary command execution method.

---

## 3. Standardise response provenance

Use an envelope for all major DataSource responses:

```ts
export interface DataEnvelope<T> {
  schemaVersion: number
  kind: string
  provenance: Provenance
  generatedAt: string
  stale: boolean
  data: T
}
```

Where useful also include:

```ts
sourceId?: string
eventSnapshotId?: string
```

The UI must display provenance consistently.

---

## 4. Never automatically fall back from API data to demo data

The application has explicit modes.

```text
DEMO MODE
→ DemoDataSource

API MODE
→ ApiDataSource
```

If the production/API backend becomes unavailable:

```text
BACKEND UNAVAILABLE
```

must be shown.

Do not automatically switch to DemoDataSource.

A backend outage must never produce plausible-looking synthetic event results.

---

## 5. Add race-decision semantics

The Validation and Experiments interfaces must make the competition-racing architecture visible.

Distinguish:

### HARD INTEGRITY

Possible states:

```text
PASS
FAIL
UNKNOWN
```

### SOFT RESEARCH EVIDENCE

Possible interpretations:

```text
STRONG
MIXED
WEAK
INSUFFICIENT
```

These do not automatically invalidate an experiment.

### RACE DECISION

Examples:

```text
PROMOTE R0 → R1
PROMOTE R1 → R2
PROMOTE R2 → R3
PROMOTE — TOP SCORE
PROMOTE — DIVERSITY SLOT
PROMOTE — EXPLORATION SLOT
KEEP — ENSEMBLE VALUE
RETEST
RETIRE — DOMINATED
RETIRE — SATURATED FAMILY
FAILED — TRAINING ERROR
INVALID — INTEGRITY FAILURE
```

Do not visually equate `WEAK` research evidence with `FAIL`.

Red is reserved primarily for genuine integrity/error conditions.

---

## 6. Improve the Experiment Frontier visualisation

The primary experiment-frontier scatter should encode approximately:

```text
x-axis = runtime / compute cost
y-axis = local event-equivalent score
marker size = prediction novelty/diversity
marker shape = model family
outline/status = race stage or frontier state
```

Hover should reveal:

* run;
* model family;
* operator;
* parent;
* local score;
* recent score;
* runtime;
* diversity;
* practice/live result;
* race decision.

---

## 7. Define a stable chart palette

Do not choose chart colours independently on every page.

Use one restrained categorical palette consistently.

For example:

```text
amber       #FFB000  interaction / selected / champion highlight
cyan        data-series colour
blue        data-series colour
green       positive/live-proven
red         negative/error
violet      optional data-series colour only
neutral     baseline/reference
```

The exact secondary hex values may be chosen to fit the canonical dark background, but they must be shared as chart tokens.

Amber remains the product accent and should not become every plotted series.

---

## 8. Add data freshness everywhere it matters

Current-event panels should visibly expose:

```text
UPDATED
STALE
UNKNOWN
```

with timestamps.

Particularly:

* Event Control;
* Round Room;
* Leaderboard;
* Staking;
* Compute & Jobs;
* TopBar.

Never use an empty cell when `UNKNOWN` communicates the state correctly.

---

## 9. Strengthen Submission states

The seven-stage submission workflow remains:

```text
SELECT
→ INFER
→ VALIDATE
→ PACKAGE
→ DRY RUN
→ SUBMIT
→ RECORD
```

Each stage must support:

```text
NOT_STARTED
RUNNING
PASS
FAIL
BLOCKED
RETRYABLE
```

A demo interaction should not simply advance through all stages regardless of validation.

Synthetic data may simulate both a successful and failed path.

---

## 10. Heatmaps

Recharts can be used for the standard charts, but do not force prediction-correlation and round×model heatmaps through an unsuitable chart primitive.

A lightweight custom SVG/CSS-grid heatmap component is acceptable and preferable if it produces a cleaner deterministic result.

Use the same heatmap component for:

* prediction correlations;
* model × round scores;
* validation fold matrices where appropriate.

---

## 11. Command palette

The CommandPalette should contain:

### Navigation

all application routes.

### Safe actions

such as:

```text
Refresh Event
Snapshot Event
Pull Data
Run Scorer Parity
Run Official Baseline
Start Fast Race
Build Ensemble
Start Autopilot
Stop Autopilot
```

Actions must call DataSource methods.

No text box that executes arbitrary shell commands.

---

## 12. Desktop verification

The console is desktop-first.

Explicitly test at least:

```text
1280×800
1440×900
1920×1080
```

Focus especially on 1280×800 because that is representative of a constrained competition laptop viewport.

Tables must remain usable.

Charts must not clip.

The top status bar must not wrap into an unreadable state.

The collapsed icon rail must remain functional.

Also perform responsive/mobile sanity checking, but do not sacrifice desktop information density to optimise mobile.

---

## 13. Preserve exact exportability

The final Figma Make result must remain suitable for direct porting.

Generate `FIGMA_EXPORT_NOTES.md` documenting:

* routes;
* component tree;
* DataSource methods;
* action methods;
* domain types;
* chart dependencies;
* font dependencies;
* localStorage keys;
* demo/API mode mechanism;
* known implementation limitations.

The exported implementation will later become the visual source of truth for Cursor.

Do not leave architectural decisions undocumented.

---

## 14. Final visual review

Before declaring completion:

1. Run every route.
2. Exercise both expanded and collapsed sidebar.
3. Exercise CommandPalette.
4. Exercise loading/error/empty/stale/demo/backend-unavailable states.
5. Exercise successful and failed submission paths.
6. Exercise all staking classifications.
7. Verify that synthetic provenance can never be mistaken for official event data.
8. Capture screenshots of all major routes at a desktop viewport.
9. Correct overflow, clipping, misalignment, inconsistent chart colours and excessive whitespace.
10. Ensure the finished product visually belongs to the same QuantSilico design family as the Generals Research Console.

Proceed after applying these amendments.

With those changes, I'd be happy to have Figma Make implement it.

The important thing is that **I would not expand the scope with another dozen pages**. The current page set is already comprehensive. The improvements should be about strengthening the handoff contracts and making the racing/autopilot philosophy visible, not making the dashboard bigger.

One minor naming preference: I'd probably have the top-left product identity read something like **`QUANTSILICO // EVERESTEER 2026`** with `RESEARCH CONSOLE` as smaller metadata rather than a huge "QuantSilico × Everesteer 2026 Research Console" logo. It will fit the terminal/research-instrument aesthetic much better.
