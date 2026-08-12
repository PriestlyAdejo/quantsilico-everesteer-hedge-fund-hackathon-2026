Yes — the overall structure is strong, but after looking through the screenshots closely, I would not export/integrate this exact version yet. The architecture is good; the presentation and some of the displayed semantics need one serious cleanup pass.

And yes: the Cursor integration prompt is designed to make this a real live console, not a static mockup. It explicitly maps every Figma DataSource method to a FastAPI route, implements ApiDataSource, wires the allowlisted actions, builds live event/round/leaderboard/submission endpoints, and verifies the production app. I would strengthen that prompt slightly so Cursor must prove every panel is backend-driven and dynamically handles arbitrary models/rounds rather than merely looking wired. I’ve given you that addendum below.

What is wrong in the screenshots right now

The biggest problem is that Figma has taken the provenance architecture too literally and turned it into UI chrome. SYNTHETIC beside nearly every page title, OFFICIAL OBSERVATION repeated down every leaderboard row, little documentation tags like sdk, setup, baseline, and similar labels are mostly noise. Provenance should remain in the underlying data and be inspectable when useful, but normal successful data should not repeatedly announce its provenance.

There is an even worse semantic contradiction on the Leaderboard page: it visibly says OFFICIAL OBSERVATION while the application simultaneously says SYNTHETIC. Those two ideas should never coexist on the same displayed dataset. In production, official Everesteer observations can have a single source line such as Source: Everesteer · Updated 18:42:06; in development, if you absolutely need fixture identification, use one global developer-only preview indicator—not dozens of badges.

There are also actual inaccuracies in the fixture content. Event Control shows SDK 0.9.4, while the project is currently built around the verified everestapi 0.3.22 pin. More importantly, it shows “Pearson R (annualised)” and a PRACTICE 30% / LIVE 70% panel under Scoring weights. That is conceptually wrong for what we've researched: the current competition scoring interface concerns CORR20/AIMC/NCORR and the actual rank metric/weights should come from event introspection. Practice/live allocation belongs to submission-budget policy, not scoring. The Figma UI should never invent the competition score formula; it should render whatever explain_scoring() gives the backend. Current Everesteer materials describe the scorer around CORR20/AIMC20/NCORR, so hard-coded “Pearson R annualised” should disappear.

And yes — it has fabricated an Apple M2 Pro on Compute & Jobs. You're not using Apple. Your actual bootstrap inspection found an i7-10750H, roughly 16 GB RAM and RTX 3070 8 GB. The production page must get this from Python's hardware detection. Same with GPU NOT DETECTED, R3/8, 12/20 uploads, event phase, model counts, row counts and every other runtime value. The Figma fixture can exist solely to exercise layout, but none of those values should survive as constants during integration.

Readability needs another pass

The design language is good and recognisably in the same family as the Generals console, but too much text is tiny and dim. Section labels, table headers, sidebar items and secondary values are all competing at approximately the same low visual weight. At a competition venue, on a laptop, while you're looking between Cursor, terminal, Discord and this console, that will become annoying very quickly.

I would keep the density but increase the practical hierarchy. Page headings and important values need to be larger; table body text should be comfortably legible; metadata can stay smaller. Stop putting almost every heading in tiny spaced uppercase. Some uppercase works for instrumentation; when everything is uppercase it stops carrying hierarchy.

The Overview frontier chart is a great example: the concept is useful but the runtime x-axis currently displays ugly raw decimal values. It should say things like:

15s · 30s · 1m · 2m · 4m

not a sequence of floating-point numbers.

The top bar is also very crowded. At full desktop width it survives, but at your target 1280×800 it needs responsive prioritisation. Keep the genuinely competition-critical fields always visible—event/round, upload budget, champion, autopilot/live connection—and let secondary system information like SDK scope/GPU collapse into the system status area when width is tight.

Official Grafana guidance actually lines up with your instinct here: dashboards should answer a question, follow a logical story, reduce cognitive load, and use directed browsing rather than forcing users to guess where to go next. It also recommends meaningful colour, normalized values and controlled refresh rather than refreshing everything unnecessarily. Carbon's table guidance similarly emphasises clear table purpose, concise column names, sorting/filtering and progressive disclosure instead of dumping everything into a flat grid.

The missing thing is the operating story

This is probably why you're looking at the pages thinking:

“Okay, they're all relevant, but what am I actually supposed to do?”

The groups OPERATE / RESEARCH / COMPETE / SYSTEM are useful categorisation, but they don't explain the research workflow.

I wouldn't number the pages. Instead, the console should understand the current stage and gently direct you:

Connect event → inspect data → prove baseline → run experiments → validate → ensemble → submit → operate live round → stake/finalise

Overview should show that entire flow, where you currently are, and the recommended next action.

Then each page gets a short human-written introduction. Not a tag. Not RACE DECISION. Something like:

Experiments

Everything we've tried, what changed between runs, and which research branches still deserve compute.

Validation

Decide whether a result can be trusted, how strong the evidence is, and whether the candidate deserves more budget.

Ensembles

Combine models only when they add independent signal. Compare prediction overlap, marginal improvement and robustness before promoting a blend.

Round Room

Use this during an open live round. It tracks the current dataset, inference jobs, submission state, leaderboard movement and the time remaining.

That's enough to orient you immediately.

The underlying enum can still be PROMOTE_DIVERSITY_SLOT; the UI does not need to scream:

PROMOTE — DIVERSITY SLOT

It can say:

Advance to R2 — adds useful independent signal

with the raw enum available in the detail drawer.

The model/round matrices absolutely should be dynamic

Yes. The current four-model/five-round matrices must not be hard-coded.

Cursor should receive:

models[]
rounds[]
scores[modelId][roundId]

and render however many actually exist.

If you end up with:

6 models × 3 rounds

it shows that.

If the autopilot creates:

47 models × 11 rounds

the heatmap becomes scrollable/virtualised/filterable rather than breaking.

Same for:

experiment table;
model registry;
leaderboard;
ensemble members;
feature table;
inference queue;
job queue;
round history.

This is going into the strengthened Cursor requirements below.

You are also right about time/ETA

Anything that can be left running should consistently expose:

Started · elapsed · estimated remaining · expected finish

For example:

LightGBM R2 · running 3m 12s · ~2m remaining · expected 04:34

rather than only:

RUNNING

That should apply to:

training;
inference;
validation;
ensemble build;
data download;
remote compute;
scorer parity;
autopilot research stage;
live submission where asynchronous;
documentation generation/build jobs.

For uncertain estimates, use ~4m or estimating…, not fake precision.

Quant metrics: yes, there should be more

At the moment some pages feel like an ML admin console rather than a quant research console.

I would add metrics that make sense for cross-sectional prediction without pretending this is already a PnL strategy:

Competition metrics: rank metric, CORR20, AIMC, NCORR, feature exposure, current/practice/live score, rank and rank change.

Research metrics: mean IC/CORR, median IC, IC standard deviation, ICIR, positive-exped rate, recent-window IC, lower-tail/5th percentile, worst fold, local→practice generalisation gap, practice→live gap, score drift, prediction correlation, marginal ensemble uplift.

Operational metrics: train time, inference latency, peak RAM/VRAM, experiments/hour, queue time, expected finish.

For ensembles specifically I'd add:

local uplift vs best member
recent-window uplift
worst-fold improvement
mean pairwise correlation
effective model count / concentration
feature-exposure change
live/practice uplift where observed

PBO/DSR-style multiplicity information can remain a subtle diagnostic rather than another giant blocking gate.

Documentation should be completely rebuilt

You're right: the current Documentation screenshot is basically filler.

The useful version should have an internal docs navigation containing something like:

Start Here → Competition Workflow → Research Loop → Data & Validation Flow → Model Lifecycle → Live Round Flow → Submission Flow → Staking Flow → CLI Reference → Python API → Backend API → Configuration Reference → Runbooks → Glossary.

And most reference material can be generated from code instead of hand-maintained. FastAPI already exposes an OpenAPI schema and automatically produces API documentation from typed routes/models. Typer uses command/function docstrings and option help for CLI help, which gives us a straightforward source for generated CLI reference. Python APIs can similarly be generated from docstrings using tooling such as mkdocstrings/mkdocstrings-python rather than manually copying signatures into MDX.

I would not auto-generate the workflow explanations from code, though. Those are conceptual documentation and should remain curated MDX. The code can generate reference; humans should define the meaning of the workflow.

That gives you both:

AUTO-GENERATED REFERENCE
Python / CLI / API / config

and:

CURATED MDX FLOWS
what to do and why