Yes — **this version is good enough to implement.** The amendments have fixed essentially all the structural issues I had with the previous plan. I’d rate it about **9.5/10 for the Figma Make stage**. It now preserves the exact things we care about for the later Cursor integration: real routing, explicit demo/API modes, provenance, typed actions, racing semantics, reusable heatmaps, stable chart tokens, and proper failure states. 

There are only **four final things I would change before you tell Figma Make to execute**, and none requires redesigning the plan.

### 1. Google Fonts must not become an event-day internet dependency

This is the most important remaining issue.

The plan currently says:

> Google Fonts, wired via CSS `@import`

That is fine for Figma Make development, but **not ideal for the production console you're taking to the event**. If venue Wi-Fi is flaky, fonts shouldn't suddenly disappear or block rendering.

I would add:

> During Figma Make development, Google Font imports are acceptable. In `FIGMA_EXPORT_NOTES.md`, explicitly flag fonts for production packaging/self-hosting during Cursor integration so the final event dashboard has no runtime Google Fonts dependency. The Figma visual result must remain identical.

You don't need Figma Make to solve packaging right now. Just make the handoff explicit.

---

### 2. `DataEnvelope` provenance is slightly too coarse for mixed pages

This:

```ts
interface DataEnvelope<T> {
  provenance: Provenance
}
```

works perfectly for things like a single leaderboard response.

But **Overview is deliberately mixing different evidence sources**:

```text
event state             OFFICIAL_EVENT_STATE
leaderboard             OFFICIAL_PLATFORM_OBSERVATION
local experiments       LOCAL_EXPERIMENT
synthetic preview       SYNTHETIC_FIXTURE
```

You don't want the entire Overview page to inherit one provenance label.

I'd leave the envelope as-is but add provenance to individual important objects too:

```ts
interface ProvenanceMeta {
  provenance: Provenance
  generatedAt: string
  sourceId?: string
  eventSnapshotId?: string
}
```

Then something like:

```ts
interface MetricCardData extends ProvenanceMeta {
  label: string
  value: string | number | null
}
```

The envelope describes the response source; individual records can preserve their true evidence source.

That will help enormously when Cursor wires the mixed dashboard later.

---

### 3. BrowserRouter needs a production SPA-fallback requirement

I agree with the switch to real routing.

But BrowserRouter only gives you nice deep links if your eventual FastAPI server knows that:

```text
/validation
/experiments
/round
```

should all fall back to the React `index.html`.

Otherwise:

```text
navigate to /validation  ✅
refresh browser          ❌ 404
```

So add one small sentence to `FIGMA_EXPORT_NOTES.md` requirements:

> Production integration using BrowserRouter requires FastAPI/static serving to implement SPA history fallback for non-API frontend routes. Cursor integration must verify direct reload of every application route.

You've already included deep-link testing, so this simply documents **why**.

---

### 4. Add a global `UNKNOWN / NOT CONNECTED / SYNTHETIC` rule for numeric metrics

You've correctly done this for freshness and target blanks, but I would make the rule global:

> Never represent unavailable numeric values as `0`.

This matters enormously for a quant console.

For example:

```text
UPLOAD CAP    UNKNOWN
LIVE SCORE    NOT AVAILABLE
GPU VRAM      NOT DETECTED
STAKE BALANCE NOT CONNECTED
RANK          —
```

rather than:

```text
UPLOAD CAP    0
LIVE SCORE    0.0000
GPU VRAM      0 GB
STAKE BALANCE $0
RANK          0
```

Zero is data. Unknown is state.

That's worth explicitly putting into the UI rules.

---

## Other than those, I would stop modifying it

I **wouldn't add more pages**.

I **wouldn't add TanStack Query** right now.

I **wouldn't add Redux/Zustand**.

I **wouldn't make Figma Make simulate the actual Everesteer SDK**.

I **wouldn't add a full notification framework**.

I **wouldn't introduce authentication UI**.

The architecture has reached the point where additional sophistication is more likely to make Figma Make produce a bloated app than make the eventual competition console better.

The current split is good:

```text
FIGMA MAKE
──────────
visual system
routes
components
domain types
DataSource contract
synthetic interaction behaviour
error states
charts
UX

         ↓ exact export

CURSOR
──────
real FastAPI integration
real manifests
real Everesteer state
real jobs
real scoring
real submissions
real local fonts/build
real filesystem provenance
```

That's exactly the separation you want.

---

## One thing it got particularly right now

I'm very happy with this:

```text
HARD INTEGRITY
SOFT RESEARCH EVIDENCE
RACE DECISION
```

That fixes a subtle but important problem.

Instead of:

```text
Recent fold poor
       ↓
FAIL
       ↓
candidate killed
```

you can now have:

```text
INTEGRITY
PASS

RESEARCH EVIDENCE
MIXED

RACE DECISION
KEEP — DIVERSITY SLOT
```

or:

```text
INTEGRITY
PASS

RESEARCH EVIDENCE
WEAK

RACE DECISION
RETEST R1
```

or:

```text
INTEGRITY
PASS

RESEARCH EVIDENCE
STRONG

RACE DECISION
PROMOTE R2 → R3
```

while actual broken experiments look completely different:

```text
INTEGRITY
FAIL — LIVE ID ALIGNMENT

RACE DECISION
INVALID
```

That's exactly the philosophy we wanted after your complaint about some of the previous QuantSilico/Generals gates becoming too conservative.

---

## The frontend tree also looks sensible now

The file list is substantial, but it is **not fake architecture bloat**. 

Things like:

```text
Heatmap.tsx
ProvenanceBadge.tsx
StatusPage.tsx
CommandPalette.tsx
ActivityStrip.tsx
```

are genuinely shared components.

And the page boundaries correspond to genuine distinct operating questions:

```text
What's happening?          Overview
What does the event say?   Event Control
What round am I in?        Round Room
What data do I have?       Data Lab
What have I tried?         Experiments
Do I trust it?             Validation
What models exist?         Models
What do features show?     Feature Lab
What should I blend?       Ensembles
How am I doing externally? Leaderboard
Can I submit safely?       Submission
What should I stake?       Staking
What's running?            Compute
What code is serving?      Repository
How do I operate it?       Documentation
```

So I don't see any obvious page that should be deleted.

---

## I'd append only this tiny final amendment

# FINAL IMPLEMENTATION NOTES

The plan is approved. Apply the following final implementation notes without otherwise changing scope or architecture.

### Offline-safe production fonts

Google Font `@import` is acceptable for the Figma Make development prototype.

However, `FIGMA_EXPORT_NOTES.md` must state that the production Cursor integration should package/self-host the required Montserrat, Raleway and JetBrains Mono font resources so the event-day console does not depend on Google Fonts being reachable at runtime.

The final production appearance must remain visually equivalent to the Figma export.

### Mixed provenance

`DataEnvelope` remains the top-level response wrapper, but important individual domain records/metric cards may also carry:

```ts
interface ProvenanceMeta {
  provenance: Provenance
  generatedAt: string
  sourceId?: string
  eventSnapshotId?: string
}
```

This is required where a single page combines multiple evidence sources, such as official event state, official leaderboard observations and local experiment results.

Do not incorrectly assign one page-wide provenance to heterogeneous evidence.

### BrowserRouter production requirement

Add to `FIGMA_EXPORT_NOTES.md`:

> Production integration using BrowserRouter requires SPA history fallback when the frontend is served by FastAPI/static hosting. Cursor must verify that directly loading or refreshing `/validation`, `/experiments`, `/round`, `/leaderboard` and every other application route returns the React application rather than a server 404.

### Unknown is not zero

Apply globally:

> Never convert unavailable, unknown, disconnected or not-yet-observed numeric values into zero.

Examples:

```text
UNKNOWN
NOT CONNECTED
NOT AVAILABLE
NOT DETECTED
—
```

must be used where appropriate.

A displayed `0`, `0.0000`, `$0`, `0 GB` or rank `0` must always mean the underlying evidence genuinely contains zero.

Proceed with implementation after applying these notes. Do not expand the page set or introduce additional application-wide state-management/framework dependencies unless the existing project requires them.

After that, **yes: tell Figma Make to execute the plan**.

At this point I'd rather see the actual generated interface and review screenshots/UI behaviour than spend another cycle changing the architecture on paper. The plan has crossed the threshold where implementation will teach us more than another round of planning.
