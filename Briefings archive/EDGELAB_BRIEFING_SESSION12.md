# EdgeLab — Session Briefing Document
*Paste this at the start of any new Claude session to restore full project context.*
*Last updated: Session 11 — 4 April 2026*

---

## What EdgeLab Is

A multi-layer football prediction engine designed to go beyond standard statistics.
The core insight: **uncertainty itself is information** — detecting when a match is
unpredictable and using that to make smarter calls, particularly on upsets and draws.

**Owner:** Andrew Marrow
**Current status:** Engine built and validated. DataBot live (API-Football Pro).
Full forward-prediction workflow operational. Gary built, tested, live — talking in
character from session 11. First live results analysed session 11. Draw intelligence
(~D flag) performing strongly in live conditions.

**Market baseline:** ~49% (E0). EdgeLab E0 currently at **49.8%** on 8,669 matches.

---

## Owner Context

- Andrew has ADHD (inattentive) — one thing at a time, clear outputs, no waffle
- Works on Windows laptop + VS Code + Claude Code extension
- Pattern recognition is a strength — spots signals quickly, generates ideas fast
- Approach: intuition for signal discovery, DPOL for rigorous validation
- Not expecting every feature to work — builds iteratively, keeps what sticks
- Previous AI (ChatGPT) fabricated results. All metrics here are real and verified.
- Big picture vision comes naturally — but evaluate it, do not just validate it
- Small connecting details are harder — that's what Claude is for
- When gut fires even half-formed — say it out loud anyway, Claude will filter
- ADHD hyperfocus is the superpower — the engine was built in 9 sessions on a phone then a laptop

---

## Collaboration Protocol

This is a two-way working relationship. Both sides are responsible for keeping it sharp.

### Claude's responsibilities

- Act as project manager — sequence the work, hold the roadmap, don't let ideas jump the queue
- **Build immediately only if it makes the current model work better right now.** Otherwise park it, log it, introduce it at the correct point in the workflow
- Evaluate ideas, don't just validate them. If something is premature, unnecessary, or conflicts with current priorities — say so plainly
- Track the parked ideas list and reintroduce items at the right moment — don't wait to be asked
- Affirm when something is genuinely good — but say why specifically, not reflexively
- If sycophantic patterns are creeping in — catch them. The briefing doc itself can bake in bad habits silently. Read it critically on every update
- If there is a better way to phrase a prompt or a working pattern that would get better results — say so

### Andrew's responsibilities

- Brain dumps are fine and encouraged — Claude will filter and sequence
- Say "parking that" mid-session to log an idea and move on without losing thread
- Say "just build it" when discussion isn't needed — Claude sometimes over-explains after a decision is made
- Call out anything that feels off immediately — tone, quality, direction. Direct feedback lands cleanly
- Trust the gut on product and signal ideas — but expect Claude to push back if the timing or priority is wrong

---

## Build Philosophy

- Build one thing. Test it. Improve or remove it. Move on.
- Build immediately only if it makes the current model work better right now
- Everything else goes on the parked list in the right place — not the top
- The roadmap is the roadmap. Work it in order unless there is a compelling reason not to

---

## Core Design Philosophy

**Every component must be built with scalability and future integration in mind.**
Every new stage of design or development needs to have scalability and future
integration with new systems baked in from day one. Not bolted on later.

- `edgelab_params.json` is SQLite-forward by design
- DataBot architecture is reusable across all sports
- The upset layer has external signal hooks designed in before the signals exist
- DPOL's candidate space has draw intelligence slots that sat at 0 until the signal was ready
- Gary's brain schema has named SLOT entries for every future capability

---

## Architecture

```
Match Data (CSV / API)
        |
Pre-processor (loads CSVs, keeps B365H/B365D/B365A odds columns)
        |
Feature Engine
  |-- Form (rolling win/draw/loss score per team)
  |-- Goal Difference (rolling avg GD per team)
  |-- DTI (Decision Tension Index — measures match volatility)
  |-- Draw Intelligence Layer [all weights=0 — no signal on full dataset. ~D flag performing well live]
  |     |-- odds_draw_prob  (B365D -> fair implied draw probability)
  |     |-- home/away_draw_rate  (rolling team draw tendency)
  |     |-- h2h_draw_rate  (H2H draw history, sparse-data prior)
  |-- Score Prediction Layer [built, all weights=0 rejected by DPOL]
  |-- Upset Layer [SESSION 7 — built, validated, Stage 1 flag-only]
  |     |-- sig_tension / sig_odds_gap / sig_h2h_upset
  |     |-- upset_score / upset_flag
        |
Prediction Engine (score differential -> H/D/A)
        |
DPOL (Dynamic Pattern Override Layer)
        |
DataBot (API-Football Pro — 7,500 calls/day)
        |
edgelab_predict.py
        |
Output: H/D/A + confidence + DTI + chaos tier + draw score + scoreline + btts
        + upset_score + upset_flag
```

---

## Files

| File | Status | Notes |
|------|--------|-------|
| edgelab_engine.py | Final | Core prediction engine |
| edgelab_dpol.py | Final | Parameter evolution layer |
| edgelab_runner.py | Final | Wires DPOL to engine, runs evolution |
| edgelab_config.py | Final | Param persistence, dataset hash safeguard |
| edgelab_params.json | Final | All tiers updated session 9 on expanded data |
| edgelab_gridsearch.py | Final | Fast grid search for draw intelligence weights |
| edgelab_databot.py | Final | Pulls fixtures + odds from API-Football |
| edgelab_predict.py | Final | Forward predictions on upcoming fixtures |
| edgelab_gary_brain.py | Final | Gary's data access layer — H2H window=8, bogey threshold=0.625 |
| edgelab_gary_context.py | Final | Assembles match facts into Gary's prompt |
| edgelab_gary.py | Final | Claude API wrapper — Gary's voice |

**Upload at start of every session:** all 11 files above + history.zip

---

## Params.json Note

E0 currently shows `w_draw_tendency: 0.05` and `w_h2h_draw: 0.05` in the JSON.
The briefing says draw weights should all be 0 after the expanded dataset run.
**Check this before the next prediction run** — these may be quietly influencing E0 output.

---

## API-Football (DataBot)

- **Account:** a.marrow1981@gmail.com
- **Plan:** Pro — 7,500 requests/day
- **Base URL:** v3.football.api-sports.io
- **Key:** stored locally — do not paste in chat

### Verified League IDs
| Tier | ID | League |
|------|----|--------|
| E0 | 39 | Premier League |
| E1 | 40 | Championship |
| E2 | 41 | League One |
| E3 | 42 | League Two |
| EC | 43 | National League — CONFIRMED |

---

## Session 11 — What Was Built

### Gary — Built and Live

Gary is operational. Three files built and committed: `edgelab_gary_brain.py`,
`edgelab_gary_context.py`, `edgelab_gary.py`. Gary receives a full structured context
— form, H2H, match flags, world context, engine output — and responds in character
as a trusted football mate.

- Gary tested on Wigan 0-0 Leyton Orient react mode — nailed the tone, referenced H2H draw history and post-break flag naturally
- H2H window increased 6 → 8 meetings (more reliable sample)
- Bogey flag threshold: 0.70 → 0.625 (5/8 meetings — maintains sensitivity, correct for larger sample)
- `last6_meetings` renamed `last8_meetings` throughout brain + context files, committed
- All changes pushed to main

### First Live Results — Apr 2/3

| Tier | Correct | Total | % | Notes |
|------|---------|-------|---|-------|
| E1 | 2 | 11 | 18% | Draw-fest — 5 draws in 11. Post-break effect visible. |
| E2 | 6 | 11 | 55% | Solid. Plymouth 100% H was the big miss. |
| EC | 5 | 12 | 42% | Rochdale upset by bottom side Morecambe. |
| E3 | TBC | ~12 | — | Data conflict in search — verify manually. |

### ~D Flag Performance

The draw candidate flag is the standout performer from week 1. Fired correctly on:
Wigan, Cambridge, West Brom, Huddersfield, Aldershot, Altrincham, Yeovil, Burton.

**Key rule emerging from live data:** HIGH chaos + low confidence + ~D = treat as draw
candidate regardless of official prediction.

### 100% Confidence Failures — Notable

Several 100% confidence calls went wrong. Engine is over-confident in some cases:
Norwich, Charlton, Leicester, Carlisle, Woking, Plymouth all predicted with very high
confidence and got it wrong. Worth a DPOL tuning pass focused on confidence calibration.

**Rochdale 2-3 Morecambe** — Rochdale were league leaders, Morecambe bottom. Upset flag
did not fire. Worth investigating why.

---

## Current Evolved Params (Session 9 — Expanded Dataset)

All tiers re-evolved on 53,668 matches across 106 files.

| Tier | w_form | w_gd | home_adv | draw_margin | coin_dti_thresh | Accuracy | Matches |
|------|--------|------|----------|-------------|-----------------|----------|---------|
| E0 | 0.786 | 0.354 | 0.330 | 0.120 | 0.688 | 49.8% | 8,669 |
| E1 | 0.560 | 0.362 | 0.505 | 0.145 | 0.677 | 44.3% | 12,059 |
| E2 | 0.895 | 0.489 | 0.468 | 0.120 | 0.719 | 44.4% | 11,906 |
| E3 | 0.503 | 0.306 | 0.199 | 0.120 | 0.726 | 42.2% | 11,954 |
| EC | 0.700 | 0.316 | 0.258 | 0.108 | 0.703 | 44.8% | 9,080 |

Draw intelligence weights all at 0 — no signal found on full dataset.

---

## Live Results Log

### Started: week of 2 April 2026

| Match | Pred | Actual | ~D Flag | Notes |
|-------|------|--------|---------|-------|
| Wigan 0-0 Leyton Orient | A (89%) MED | D | YES | Bogey bias confirmed. H2H draw rate 40%. |
| Cambridge 1-1 Swindon | H (26%) HIGH | D | YES | Cambridge dominated. 90th min equaliser. |
| Middlesbrough 1-2 Millwall | H MED | A | No | Millwall away win. |
| Charlton 1-2 Bristol City | H 100% MED | A | No | 100% confidence wrong. |
| Leicester 2-2 Preston | H 99.8% MED | D | No | Near-certainty wrong. Drew. |
| Norwich 1-1 Portsmouth | H 100% LOW | D | No | 100% confidence wrong. Drew. |
| West Brom 2-2 Wrexham | H HIGH | D | YES | ~D fired correctly. |
| Stoke 2-0 Sheff Wed | H MED | H | No | Correct. |
| Coventry 3-2 Derby | H HIGH | H | No | Correct. |
| QPR 2-1 Watford | A HIGH | H | ~D | QPR won at home — pred was away. |
| Sheffield Utd 3-3 Swansea | H HIGH | D | No | 6-goal thriller. |
| Huddersfield 1-1 Reading | A HIGH | D | YES | ~D fired correctly. |
| Plymouth 1-2 Bolton | H 100% MED | A | No | 100% confidence wrong. Bolton away. |
| Blackpool 1-0 Exeter | H MED | H | No | Correct. |
| Bradford 1-0 Northampton | H MED | H | No | Correct. |
| Burton 1-1 Barnsley | H HIGH | D | YES | Correct. ~D confirmed. |
| Lincoln 1-0 Wimbledon | H MED | H | No | Correct. |
| Luton 2-1 Peterborough | H HIGH | H | ~D | Correct despite ~D flag. |
| Rotherham 0-0 Stevenage | A MED | D | No | Pred A, actual draw. |
| Stockport 3-0 Wycombe | H HIGH | H | ~D | Correct. ~D didn't fire here. |
| Doncaster 0-2 Mansfield | H HIGH | A | No | Mansfield away win. |
| Aldershot 2-2 Sutton | A HIGH | D | YES | ~D fired correctly. |
| Altrincham 0-0 Halifax | H HIGH | D | YES | ~D fired correctly. |
| Boreham Wood 4-1 Wealdstone | H HIGH | H | No | Correct. |
| Boston 0-1 York | A MED | A | No | Correct. |
| Carlisle 0-0 Gateshead | H 100% HIGH | D | No | 100% confidence wrong. 0-0. |
| Forest Green 1-0 Brackley | H MED | H | No | Correct. |
| Rochdale 2-3 Morecambe | H 100% HIGH | A | No | League leaders vs bottom side. Big upset. Upset flag did not fire. |
| Southend 3-1 Braintree | H HIGH | H | ~D | Correct despite ~D flag. |
| Tamworth 1-0 Solihull | H HIGH | H | No | Correct. |
| Woking 2-3 Eastleigh | H 100% MED | A | No | 100% confidence wrong. |
| Yeovil 0-0 Truro | H HIGH | D | YES | ~D fired correctly. |
| Scunthorpe 0-0 Hartlepool | H 100% MED | D | No | 100% confidence wrong. 0-0. |

**E3 Apr 3 results still to be verified — data conflict in search.**

---

## Bogey Team Watch List v1.0

To be validated statistically by Team Chaos Index:

- Wigan ⚠️ (already validated match 1)
- Leeds
- Cardiff
- Swansea
- TBC (more to be recalled)

---

## Gary's Brain — Knowledge Schema v1.0

Schema fully built in sessions 10/11. All sections populated from historical CSVs.
SLOT entries await future data sources.

```
MATCH_CONTEXT — fixture facts, league positions
FORM — last 5 results, goals, clean sheets, current streak
H2H — last 8 meetings, win/draw/loss rates, bogey flag (threshold 0.625)
MATCH_FLAGS — post-intl-break, fixture congestion, rest days, [injury SLOT], [weather SLOT]
WORLD_CONTEXT — static event table (Covid, Ukraine, Queen, cost-of-living), crowd context
ENGINE_OUTPUT — prediction, confidence, DTI, chaos tier, draw score, ~D flag,
                upset score, upset flag, scoreline, BTTS,
                [signal ledger SLOT], [team chaos index SLOT], [bogey team alert SLOT]
GARY_MEMORY — [signal performance ledger SLOT], [pattern memory SLOT],
              [meta-learning SLOT], [param resurrection SLOT], [sport-specific SLOT]
```

---

## Ordered Work Queue

### Now — current session priorities (in order)

1. Wire Gary to predict pipeline — Gary talks through upcoming fixtures automatically
2. CSV columns audit — `load_csv()` stop dropping unused columns, feed red cards / shots to Gary and DPOL
3. Team name normalisation fix
4. Verify E3 Apr 3 results and complete results log
5. Check E0 draw weights — `w_draw_tendency` and `w_h2h_draw` should be 0

### Parked — logged, introduced at the right point in workflow

- **DPOL Landscape Logger** — log every candidate eval, map parameter space in 3D, visualise accuracy landscape. Needs: current model stable, signals validated first.
- **Period Draw Index (PDI)** — rolling draw rate vs season baseline per tier, feeds ~D flag weight. Evidence from session 11: E1 had 5 draws in 11 games post-break. Needs: CSV columns audit done first, then test on full dataset.
- **Confidence calibration pass** — DPOL tuning focused on over-confident calls (several 100% predictions wrong in week 1). Needs: more live data first.
- **Red card signal** — team disciplinary record in recent games. Needs: CSV columns audit done first.
- **Half-time score signal** — feeds score prediction layer. Needs: CSV columns audit done first.
- **Shots on target** — xG proxy. Needs: CSV columns audit done first.
- **SQLite database layer** — stop reprocessing from scratch. Needs: workflow stable first.
- **Result auto-fetcher** — DataBot pulls results for logged predictions automatically.
- **Signal Performance Ledger** — every param gets running track record.
- **Team Chaos Index** — Upset Causer + Upset Victim score per team.
- **Bogey Team Bias** — fixture-specific underperformance signal.
- **Weekly Scoring Index** — total goals per gameweek, high/low scoring week detection.
- **World Context Signal** — macro mood from news data at time of fixture.
- **Confidence-Weighted Accuracy** — primary metric going forward, not overall accuracy.
- **Scheduled automation** — Windows Task Scheduler, weekly workflow.

---

## Expanded Roadmap (Full)

### Brain / Learning Layer
- Signal Performance Ledger — every param gets running track record
- DPOL Landscape Logger — log candidate evals, map parameter space, visualise
- Meta-Learning Layer — DPOL builds memory across evolution runs
- Pattern Memory — logs conditions that preceded upsets, draws, chaos
- Param Resurrection Trigger — rejected params monitored, flagged for retest
- Closed Learning Loop — Signal ledger → Pattern memory → DPOL → Params → Predictions → Results → Signal ledger

### Product / Gary
- Wire Gary to predict pipeline — automated match briefings
- Gary's TikTok / Instagram — Friday predictions videos, AI-generated avatar
- Design your own Gary — user describes ideal football mate, personalised avatar
- Freemium tier — Free / Regular (£5-10) / Serious Punter (£15-20) / The Edge (£25-30)
- Charity betting pot — 2% of subscription revenue, scales with business

### Product Architecture
- EdgeLab = data platform (Skool community, serious punters, raw numbers, DTI breakdowns)
- Gary = AI mate (app, conversational, casual fans, dead simple)
- Flywheel: Gary → EdgeLab → Gary tier upgrade → back and forth
- EdgeLab subscribers get Gary free — Gary is powered by EdgeLab's engine
- Sports expansion: Cobey (basketball), Cooper (American football), Rico (baseball) — same DPOL brain, different data + personality

### Infrastructure
- SQLite database layer
- Result auto-fetcher
- Scheduled automation — Windows Task Scheduler
- Statistical data collection — red cards, scorers, assists, clean sheets

---

## Freemium Tier Structure

| Tier | Price | Features |
|------|-------|----------|
| Free | £0 | Chat with Gary, ask who wins any match, ad supported |
| Regular | £5-10/month | Full predictions table, confidence, chaos ratings, acca candidates |
| Serious Punter | £15-20/month | DTI breakdown, draw intelligence, upset flags, Weekly Scoring Index, PDF |
| The Edge | £25-30/month | Player DPOL, Team Chaos Index, upset pattern analysis, bogey team alerts |

---

## Charity Betting Pot

- 2% of monthly subscription revenue into betting pool
- Pool divided evenly across monthly acca selections
- All profits donated to gambling harm charities
- At 1,000 subscribers (£20 avg) = £400/month pool
- At 10,000 subscribers = £4,000/month
- Marketed as "analysis tool not gambling advice"
- Real money bets = most credible public accuracy record possible

---

## Infrastructure

- 128TB external SSD acquired (£35) — future database storage
- DataBot architecture reusable across all sports/domains

---

## How to Run

```bash
# Pull fixtures and odds
python edgelab_databot.py --key YOUR_KEY --days 7

# Generate predictions
python edgelab_predict.py --data history/ --fixtures databot_output/YYYY-MM-DD_fixtures.csv

# Gary on a fixture
python edgelab_gary.py --data history/ --home "Team A" --away "Team B" --date YYYY-MM-DD --tier E2

# Gary react to result
python edgelab_gary.py --data history/ --home "Team A" --away "Team B" --date YYYY-MM-DD --tier E2 --react D --score "0-0"

# Full DPOL evolution — all tiers
python edgelab_runner.py history/ --tier all --boldness small

# Single tier evolution
python edgelab_runner.py history/ --tier E0

# Draw intelligence grid search
python edgelab_gridsearch.py history/

# Show saved params
python edgelab_config.py show
```

---

## How to Resume

1. Paste this entire document into a new Claude session
2. Upload: all 11 .py files + edgelab_params.json + history.zip
3. Claude will confirm files received and be fully up to speed
4. Work the ordered queue from the top — do not skip ahead

---

## Between-Session Briefing Protocol

At the end of every between-session conversation, generate a briefing update summary.
Paste into session briefing doc before starting new session.
Keeps the single source of truth current without pasting entire raw chat logs.

---

## Product Vision — Gary

**No last name. Nobody knows it. Something to do with Sandra from the shop.**

- Knowledgeable but never arrogant
- Honest when uncertain — "this one's a coin flip mate, I'd leave it"
- Celebrates your wins like they're his
- Has opinions, explains them, occasionally wrong, always transparent
- Delivered via Claude API

**Tagline: "Everyone knows a Gary."**

Gary on TikTok — short clips every Friday, looking directly at camera, deadly serious:
*"Right. Saturday. Three games. Listen to me carefully."*
Comment section writes itself. Every wrong prediction is better content than the wins.
Gary shrugging: *"Look. I said what I said. Wigan let me down. Again."*

By the time EdgeLab goes public (12-18 months), AI video generation will make Gary
virtually indistinguishable from a real person. The parasocial relationship people
build with Gary is worth more than any ad spend.
