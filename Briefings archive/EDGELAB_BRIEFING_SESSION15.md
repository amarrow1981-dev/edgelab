# EdgeLab — Session Briefing Document
*Paste this at the start of any new Claude session to restore full project context.*
*Last updated: Session 15 — 5 April 2026*

---

## What EdgeLab Is

A multi-layer football prediction engine designed to go beyond standard statistics.
The core insight: **uncertainty itself is information** — detecting when a match is
unpredictable and using that to make smarter calls, particularly on upsets and draws.

**The edge is in the signals nobody else is correlating.** Anyone can build a form +
home advantage model. EdgeLab's advantage comes from unconventional external signals —
weather, world mood, public holidays, fixture timing, travel load, motivation, referee
patterns — correlated against outcomes across thousands of matches. DPOL validates
which signals actually matter. Gary communicates them in plain English.

**Owner:** Andrew Marrow
**Current status:** Engine built and validated. DataBot live (API-Football Pro).
Full forward-prediction workflow operational. Gary built, tested, live — wired to
predict pipeline. Draw intelligence (~D flag) performing strongly in live conditions.
External Signal Layer Phase 1 built, wired, and extended to all European tiers.
European data expansion complete — 17 tiers, 137,645 matches, 25 years.
DPOL running across all 12 European tiers (session 15 — in progress, pick up in session 16).
Gary's tier vocabulary and European ground coordinates fully updated.

**Market baseline:** ~49% (E0). EdgeLab E0 currently at **49.9%** on 8,669 matches.

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
Match Data (CSV / API)         External Signal Sources
        |                               |
        |              ┌────────────────┤
        |              │  Weather       │ Open-Meteo (free, historical + forecast)
        |              │  Ground data   │ Coordinates, capacity (static)
        |              │  Calendar      │ Bank holidays, fixture timing (static)
        |              │  Referee       │ Already in CSVs (retained session 12)
        |              │  Motivation    │ Derived from standings (dead rubbers, etc.)
        |              │  Travel load   │ Ground coordinates → distance calculation
        |              │  World events  │ Static table (Gary already has this)
        |              │  [Injury]      │ SLOT — future paid source
        |              │  [Sentiment]   │ SLOT — future news/social API
        |              └────────────────┤
        |                               |
Pre-processor (loads CSVs, retains all stat columns — see CSV Column Map)
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
  |-- External Signal Layer [Phase 1 BUILT session 14 — all weights at 0.0 pending activation]
  |     |-- referee_stats [ACTIVE — no Referee col in EC, present in E0-E3]
  |     |-- travel_load [ACTIVE — 481 grounds mapped incl. all 17 tiers, haversine distance]
  |     |-- fixture_timing [ACTIVE — bank holidays, festive, midweek flags]
  |     |-- motivation_index [ACTIVE — dead rubber, six-pointer, survival detection]
  |     |-- [weather_factor SLOT — Phase 2, Open-Meteo]
  |     |-- [injury_index SLOT] [sentiment_index SLOT] [Phase 3]
        |
Prediction Engine (score differential -> H/D/A)
        |
DPOL (Dynamic Pattern Override Layer)
        |
DataBot (API-Football Pro — 7,500 calls/day) [name normalisation applied at source]
        |
edgelab_predict.py [--gary flag wires Gary to every fixture]
        |
Output: H/D/A + confidence + DTI + chaos tier + draw score + scoreline + btts
        + upset_score + upset_flag + [external signal context]
        |
Gary (optional) — full match briefing per fixture via --gary flag
        [Gary receives ALL external signals — weather, motivation, world context etc.]
```

---

## Files

| File | Status | Notes |
|------|--------|-------|
| edgelab_engine.py | Final | Core prediction engine. Phase 1 signal params added session 14 |
| edgelab_dpol.py | Final | Parameter evolution layer. Phase 1 signal slots added session 14 |
| edgelab_runner.py | **Updated S15** | All 17 tiers. --tier english / european / all |
| edgelab_config.py | Final | Param persistence. Phase 1 param loading added session 14 |
| edgelab_params.json | **Partial S15** | E0–EC evolved. B1/D1/D2/I1/I2/N1/SC0–SC3/SP1/SP2 — DPOL running, pick up S16 |
| edgelab_signals.py | **Updated S15** | 481 grounds mapped — all 17 tiers including full European coverage |
| edgelab_gridsearch.py | Final | Fast grid search for draw intelligence weights |
| edgelab_databot.py | Final | Pulls fixtures + odds from API-Football. Name normalisation map added session 12 |
| edgelab_predict.py | Final | Forward predictions. --gary flag wired session 12 |
| edgelab_gary_brain.py | Final | Gary's data access layer. MatchFlagsBlock extended session 14 |
| edgelab_gary_context.py | **Updated S15** | All 17 tiers with country + tier level context. TIER_COUNTRY + TIER_LEVEL dicts added |
| edgelab_gary.py | Final | Claude API wrapper — Gary's voice |

**Upload at start of every session:** all 12 files above + edgelab_params.json + history.zip

---

## CSV Column Map (Session 12 Audit)

All columns now retained in `load_csv()`. Classification baked into the code comments.

| Column(s) | Category | Status | Purpose |
|-----------|----------|--------|---------|
| B365H/D/A | Pre-match | ACTIVE | Draw intel, upset signal |
| B365>2.5 / B365<2.5 | Pre-match | PARKED | Over/under goals — 31% coverage |
| HY / AY | Pre-match | PARKED | Yellow cards rolling signal |
| HTHG / HTAG / HTR | Post-match | PARKED | Half-time score — pattern memory, Gary post-match |
| HS / AS | Post-match | PARKED | Total shots |
| HST / AST | Post-match | PARKED | Shots on target — xG proxy |
| HF / AF | Post-match | PARKED | Fouls |
| HC / AC | Post-match | PARKED | Corners |
| HR / AR | Post-match | PARKED | Red cards — discipline signal |
| All other bookmaker cols | — | DROPPED | Redundant odds sources (BW, BF, PS, WH, Max, Avg etc.) |

**Pre-match columns** may feed prediction features.
**Post-match columns** are analysis/DPOL/Gary only — never used for prediction.

---

## Team Name Normalisation (Session 12)

`TEAM_NAME_MAP` in `edgelab_databot.py` — 115 entries.
Applied at source in `build_dataframe()` before CSV is written.
API-Football official names → football-data.co.uk abbreviations.
Unknown clubs pass through unchanged (neutral priors, no crash).

Key mappings: Manchester City → Man City, Nottingham Forest → Nott'm Forest,
Wolverhampton Wanderers → Wolves, Sheffield Wednesday → Sheffield Weds, etc.

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

## Dataset — Session 15

**417 CSV files, flat in history/ folder, 25 years, 17 tiers, 137,645 matches.**

4 duplicates removed (N1 x2, SP2 x2 — content-identical files).

| Tier | Files | Matches | What it is |
|------|-------|---------|------------|
| E0 | 22 | 8,360 | Premier League |
| E1 | 22 | 12,144 | Championship |
| E2 | 23 | 12,544 | League One |
| E3 | 23 | 12,584 | League Two |
| EC | 19 | 10,130 | National League |
| SP1 | 23 | 8,740 | La Liga |
| SP2 | 23 | 10,626 | La Liga 2 |
| D1 | 22 | 6,732 | Bundesliga |
| D2 | 22 | 6,732 | 2. Bundesliga |
| I1 | 23 | 8,518 | Serie A |
| I2 | 23 | 10,022 | Serie B |
| N1 | 23 | 6,964 | Eredivisie |
| B1 | 23 | 6,246 | Belgian First Division A |
| SC0 | 23 | 5,195 | Scottish Premiership |
| SC1 | 23 | 4,052 | Scottish Championship |
| SC2 | 23 | 4,029 | Scottish League One |
| SC3 | 23 | 4,027 | Scottish League Two |
| **TOTAL** | **383** | **137,645** | |

---

## Current Evolved Params

### English tiers (session 14 — final)

| Tier | w_form | w_gd | home_adv | draw_margin | coin_dti_thresh | Accuracy | Matches |
|------|--------|------|----------|-------------|-----------------|----------|---------|
| E0 | 0.774 | 0.351 | 0.400 | 0.120 | 0.687 | 49.9% | 8,669 |
| E1 | 0.460 | 0.324 | 0.604 | 0.145 | 0.546 | 44.5% | 12,059 |
| E2 | 0.797 | 0.487 | 0.514 | 0.120 | 0.747 | 44.4% | 11,906 |
| E3 | 0.401 | 0.343 | 0.197 | 0.120 | 0.677 | 42.3% | 11,954 |
| EC | 0.726 | 0.268 | 0.326 | 0.108 | 0.663 | 45.1% | 9,080 |

### European tiers — DPOL in progress (session 15, complete in session 16)

B1, D1, D2, I1, I2, N1, SC0, SC1, SC2, SC3, SP1, SP2 — evolution running.
Results and evolved params to be logged in session 16.

Phase 1 signal weights (all tiers): w_ref_signal=0.0, w_travel_load=0.0,
w_timing_signal=0.0, w_motivation_gap=0.0 — all at zero, none yet activated.
Broader dataset may activate signals that didn't fire on English-only data.

---

## Session 15 — What Was Built

### 1. European data audit + dedup

417 clean CSVs confirmed. 4 content-identical duplicates removed before DPOL run:
- `N1 (9).csv` == `N1 (11).csv`
- `N1 (12).csv` == `N1 (10).csv`
- `SP2 (5).csv` == `SP2 (4).csv`
- `SP2 (13).csv` == `SP2 (12).csv`

Dedup method: MD5 content hash. Not filename-based — catches identical files
regardless of name. Clean history.zip delivered as output.

### 2. edgelab_runner.py — European tier expansion

`--tier` argument now accepts all 17 tiers plus three group shortcuts:
- `--tier english` → E0, E1, E2, E3, EC
- `--tier european` → B1, D1, D2, I1, I2, N1, SC0, SC1, SC2, SC3, SP1, SP2
- `--tier all` → all 17

Session 15 DPOL command:
```bash
python edgelab_runner.py history/ --tier european --boldness small
```

### 3. edgelab_gary_context.py — tier vocabulary

Three new dicts added:
- `TIER_NAMES` — all 17 tiers with proper competition names
- `TIER_COUNTRY` — every tier mapped to its country
- `TIER_LEVEL` — 1 = top flight, 2 = second tier etc.

Gary's match briefing header now includes country and tier level:
```
La Liga (Spain)  |  Spain  |  Top flight  |  2025-03-15
```
Gary knows the difference between a Bundesliga fixture and a Belgian second division game.

### 4. edgelab_signals.py — European ground coordinates

481 total ground entries — up from 119 (English only).

European coverage added:
- Belgium (B1): 37 clubs
- Germany (D1 + D2): 62 clubs — including Canary Islands awareness via Spanish data
- Italy (I1 + I2): 79 clubs
- Netherlands (N1): 33 clubs
- Scotland (SC0–SC3): 54 clubs
- Spain (SP1 + SP2): 127 clubs — Las Palmas and Tenerife at 28°N correctly placed

**100% coverage** — every team name in the dataset has a coordinate entry.
Travel signal now computes correctly for all European fixtures.
Notable: Las Palmas/Tenerife trips from mainland Spain = 2,000+km. Gary will flag these.

---

## Session 14 — What Was Built

### 1. External Signal Layer — Phase 1 (`edgelab_signals.py` — new file)

Complete Phase 1 signal layer. No external APIs required. All signals pre-match.

**Signals built:**
- **Referee stats** — rolling home win rate, card rate, foul rate per referee. No lookahead. Falls back to global average when < 10 matches. EC CSVs don't carry Referee column — handled gracefully.
- **Ground coordinates** — 119 English grounds mapped (E0–EC) with lat/lon. Haversine distance calculation. Extended to 481 entries session 15.
- **Travel load** — away team journey distance → normalised 0–1 signal. 0=local derby (<30km), 1=marathon trip (>400km). Plymouth to Newcastle = 537km. Chelsea to Arsenal = 10km.
- **Fixture timing** — day of week, midweek flag, bank holiday detection, festive period (Dec 20–Jan 3). Combined timing_signal 0–1.
- **Public holidays** — English bank holiday calendar 2018–2026 baked in.
- **Motivation index** — derived from standings. Dead rubbers (0.2), relegation six-pointers (1.0), title races (0.8), survival vs nothing gaps (0.8 differential). Fires correctly on all test cases.

**Wired into:**
- `edgelab_engine.py` — `prepare_dataframe()` calls `compute_phase1_signals()`. 4 new EngineParams slots (all 0.0).
- `edgelab_dpol.py` — 4 new LeagueParams slots. `_generate_candidates()` nudges all 4 from zero every evolution cycle.
- `edgelab_runner.py` — param conversion functions updated both directions.
- `edgelab_config.py` — `load_params()` handles new fields, defaults to 0.0 for backward compatibility.
- `edgelab_gary_brain.py` — `MatchFlagsBlock` fully extended. `_build_match_flags()` populates all signal fields via `get_signal_context()`.
- `edgelab_gary_context.py` — `_build_flags_section()` renders travel description, timing, bank holiday, motivation, dead rubber, six-pointer, referee bias for Gary.

**DPOL result:** All 4 signal weights tested, all remain at 0.0. Not enough signal in the English-only dataset to activate. Signals correctly built and waiting — retesting with full European dataset in session 16.

### 2. Full DPOL re-evolution (session 14)

- Pre-signals run: E0 49.8%, E1 44.7%, E2 44.5%, E3 42.2%, EC 44.8%
- Signals run: E0 49.9%, E1 44.5%, E2 44.4%, E3 42.3%, EC 45.1%
- EC gained +0.3% — largest single-run gain this session

### 3. Dataset audit

120 CSV files confirmed, 2001–2026, 60,931 total matches. Already 25 seasons deep.

### 4. Known issues logged for session 15 (now session 16)

- `show_config()` and `print_params()` don't display Phase 1 signal weights — fix needed
- DPOL near-miss ledger + guided combination search — parked for after Signal Performance Ledger

---

## Live Results Log

### Week of 2–3 April 2026

#### E1 — Apr 3: 2/11 = 18%

| Match | Pred | Actual | Notes |
|-------|------|--------|-------|
| Leicester 2-2 Preston | H 100% | D | Near-certainty wrong |
| Birmingham 0-0 Blackburn | H 29% | D | |
| West Brom 2-2 Wrexham | H HIGH | D | ~D fired correctly |
| Sheffield Utd 3-3 Swansea | H 100% | D | 6-goal thriller |
| Norwich 1-1 Portsmouth | H 100% | D | 100% confidence wrong |
| QPR 2-1 Watford | H 22% | H | ✓ |
| Stoke 2-0 Sheff Wed | H 42% | H | ✓ |
| Charlton 1-2 Bristol City | H 100% | A | 100% confidence wrong |
| Oxford Utd 1-1 Hull | H 42% | D | |
| Middlesbrough 1-2 Millwall | H 47% | A | |
| Coventry 3-2 Derby | H 91% | H | ✓ |

**Note:** E1 18% is NOT an international break effect. Real issue: engine called H on all 11 fixtures. Average DTI 0.847, 9/11 HIGH chaos. Engine defaults to home advantage when form is unreadable. See E1 Home Bias Problem.

#### E2 — Apr 3: 6/11 = 55%

| Match | Pred | Actual | Notes |
|-------|------|--------|-------|
| Wigan 0-0 Leyton Orient | A 89% MED | D | ~D fired. Bogey H2H confirmed |
| Stockport 3-0 Wycombe | H HIGH | H | ✓ |
| Doncaster 0-2 Mansfield | H HIGH | A | Mansfield away |
| Luton 2-1 Peterborough | H HIGH | H | ✓ ~D flag but H won |
| Plymouth 1-2 Bolton | H 100% MED | A | 100% wrong |
| Blackpool 1-0 Exeter | H MED | H | ✓ |
| Lincoln 1-0 Wimbledon | H MED | H | ✓ |
| Burton 1-1 Barnsley | H HIGH | D | ✓ ~D confirmed |
| Rotherham 0-0 Stevenage | A MED | D | |
| Huddersfield 1-1 Reading | A HIGH | D | ✓ ~D confirmed |
| Bradford 1-0 Northampton | H MED | H | ✓ |

#### E3 — Apr 3: 5/11 = 45.5%

| Match | Pred | Actual | Score | Notes |
|-------|------|--------|-------|-------|
| Milton Keynes Dons v Barrow | H | D | 0-0 | ✗ |
| Shrewsbury v Tranmere | H | H | 1-0 | ✓ |
| Accrington v Crewe | H | H | 2-0 | ✓ Upset — Accrington were big underdogs |
| Colchester v Oldham | A | A | 1-3 | ✓ |
| Grimsby v Harrogate | H | A | 1-3 | ✗ Harrogate upset |
| Newport County v Crawley | H | A | 0-2 | ✗ |
| Barnet v Bromley | A | D | 2-2 | ✗ |
| Chesterfield v Cheltenham | H | H | 1-0 | ✓ |
| Walsall v Gillingham | H | D | 2-2 | ✗ |
| Salford v Notts County | A | H | 2-1 | ✗ Salford upset |
| Bristol Rovers v Fleetwood | H | H | 1-0 | ✓ |

#### EC — Apr 3: 5/12 = 42%

Rochdale 2-3 Morecambe — Rochdale were league leaders, Morecambe bottom.
Upset flag did not fire. Still flagged for investigation.

#### Apr 2 (E3)
Cambridge 1-1 Swindon — H (26%) HIGH → D. ~D fired correctly.

---

## ~D Flag Performance (cumulative)

Fired correctly: Wigan, Cambridge, West Brom, Huddersfield, Aldershot, Altrincham,
Yeovil, Burton, Birmingham (approx ~D).

**Key rule confirmed by live data:** HIGH chaos + low confidence + ~D = treat as draw
candidate regardless of official prediction.

---

## 100% Confidence Failures

Norwich, Charlton, Leicester, Carlisle, Woking, Plymouth, Sheffield Utd, Scunthorpe,
Southend (near). Engine is over-confident in some cases. Confidence calibration pass
is parked and waiting for more live data — now has enough cases to act on.

---

## E1 Home Bias Problem (Session 12)

When DTI is high across a whole matchday, the engine calls H on nearly every match.
Apr 3 E1: 11/11 H predictions, avg DTI 0.847, 9/11 HIGH chaos, 2/11 correct.

Root cause: at high DTI, form/GD signals are dampened and home advantage dominates
as the default. The engine needs a mechanism to recognise "this entire slate is
unreadable" rather than defaulting to home on every call.

Fix direction: DTI-weighted randomisation or a draw/away floor at high chaos tiers.
Investigate during confidence calibration pass — this result adds urgency to that item.

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

## Acca Builder — Architecture (Session 15)

**First-class feature. Two-stage process. Premium product layer.**

### Stage 1 — Gary identifies high-conviction individual picks

Not "top N by statistical score." Gary selects matches where multiple signals agree:
- Engine confidence above threshold
- DTI is LOW or MED (readable match — not coin-flip territory)
- No upset flag undermining the prediction
- H2H supports it
- Form is clean and recent
- No confounding flags (dead rubber, post-intl-break chaos, congested schedule)

Each qualifying pick gets a Gary conviction rating. Picks that don't clear the bar are
left on the table. Gary is selective by design.

### Stage 2 — Gary evaluates combinations

**Not just "best 5 picks." Best 5 picks that are decorrelated from each other.**

Two mid-table home wins from the same division on the same Saturday are correlated —
if there's a systemic factor that day (weather pattern, refereeing trend, fixture
congestion) they could fail together. Gary prefers picks that are:
- Different tiers / different countries
- Different result types (mix of H, A, BTTS)
- Independent underlying reasons for conviction

### Acca types Gary builds

- **Result accas** — H/D/A combinations, most common
- **BTTS accas** — dedicated BTTS selections from the engine's btts_flag
- **Mixed accas** — result + BTTS on same or different matches
- **Safety accas** — lower odds, very high conviction only, for cautious users
- **Value accas** — longer shots where Gary sees genuine edge vs bookmaker implied probability
- **Upset accas** — this is the one. When upset flags fire independently on multiple
  matches in the same matchday, Gary builds the upset combination. Not a punt — a
  reasoned position. Double upset at 28/1 landing is the screenshot that goes viral.

### The maths (session 15 discussion)

With 150-200 European matches per weekend across 17 tiers, Gary has a large enough
pool to be genuinely selective. He picks the clearest 15-20 from 200 available.

At 60% accuracy on cherry-picked high-conviction picks:
- Single 4-fold: 0.6⁴ = 13%
- 8 picks available → 70 possible 4-folds → strong probability at least one lands

The upset version: Gary's upset flag was built to find conditions the market has
mispriced. When two independent upset flags fire on the same day, combining them
isn't reckless. It's systematic edge stacking. The bookmaker equivalent of a trading
desk running 1,000 bets/week at 52% accuracy — doesn't need to win most of the time,
just needs to be right slightly more than the market expects, consistently.

**Key insight:** It doesn't matter if Gary is the best predictor ever. What matters
is that accuracy on his highest-conviction picks is meaningfully above 50%, and
the dataset is large enough to find those picks consistently every week.

### Implementation plan

- `gary.build_acca(ctx_list, constraints)` — standalone acca builder function
- Matchday briefing can call it as an output section (batch use)
- User-bespoke mode: user specifies constraints live ("4-fold, max 15/1, no Scottish,
  BTTS preferred") — Gary builds it around them. Premium feature.
- Pre-generated weekly accas cached Friday morning — one API call per fixture per week
  regardless of user volume (caching strategy, session 14)

**Introduce:** after DPOL European evolution is complete and params are stable.
Gary can't build credible accas without evolved params for all 17 tiers.

---

## External Signal Layer — Workstream Definition

This is a first-class workstream, not a collection of parked items. It is the primary
source of EdgeLab's long-term edge. The signals below are things no standard football
model looks at. DPOL validates which ones actually correlate with outcomes. Gary
communicates the ones that do in plain English.

**All Phase 1 and 2 signals are pre-match** — available before kickoff, usable for
prediction. This is what makes them valuable.

### Phase 1 — Static / derivable signals (no external API needed)

| Signal | Source | What it detects |
|--------|--------|-----------------|
| Referee assignment | Already in CSVs (Referee col, retained session 12) | Referee-specific home bias, card rates, foul tendencies |
| Ground coordinates | One-time static table — 481 entries, all 17 tiers | Enables travel distance calculation |
| Travel distance / load | Ground coordinates → calculation | Away teams travelling 300+ miles on 3 days' rest |
| Fixture timing | Date + day of week | Tuesday nights, bank holiday games, festive congestion |
| Public holidays | Static English calendar | Bank holiday fixtures behave differently |
| Motivation index | Derived from standings | Dead rubbers, must-wins, relegation six-pointers, title deciders |

### Phase 2 — Free API signals (Open-Meteo)

| Signal | Source | What it detects |
|--------|--------|-----------------|
| Weather at kickoff | Open-Meteo (free, historical + forecast) | Rain, wind speed, temperature |
| Historical weather | Open-Meteo historical endpoint | Retrospective training — DPOL learns weather correlations going back years |

### Phase 3 — Richer signals (longer term)

| Signal | Source | Status |
|--------|--------|--------|
| Injury / availability index | Paid source or scraping | SLOT — future |
| News sentiment per club | News API | SLOT — future |
| Fan sentiment / social mood | Social API | SLOT — future |
| Manager sacking effect | Derivable from public records | SLOT — could be Phase 1 actually |

---

## Ordered Work Queue

### Session 16 — priorities in order

1. **Review European DPOL results** — log evolved params for all 12 new tiers.
   Check which tiers gained most from 25 years of data.
2. **Re-test Phase 1 signal weights** on full 137,645-match dataset — run DPOL
   `--tier all` to see if travel/timing/motivation signals now earn activation.
3. **Fix display gap** — update `show_config()` and `print_params()` to show
   Phase 1 signal weights. Currently blind to whether signals activate.
4. **European DataBot league IDs** — verify API-Football IDs for SP1, D1, I1 etc.
   so DataBot can pull European fixtures for forward prediction.
5. **External Signal Layer — Phase 2** — weather via Open-Meteo.

### Parked — logged, introduced at the right point in workflow

- **DPOL near-miss ledger + guided combination search** — when a signal nearly clears the threshold, log it. Introduce after Signal Performance Ledger.
- **E1 Home Bias** — Engine defaults to H on every match when DTI is high across the slate. Fix: DTI-weighted draw/away floor at HIGH chaos. Introduce during confidence calibration pass.
- **Acca Builder** — Stage 1 + Stage 2 as described above. Introduce after European DPOL complete and all 17 tiers have stable params.
- **Period Draw Index (PDI)** — Rolling draw rate vs season baseline per tier. Introduce after Phase 1 external signals.
- **Live Result & News DataBot** — Post-match Gary reactions. Slots in when result-logging workflow is in place.
- **DPOL Landscape Logger** — log every candidate eval, map parameter space, visualise accuracy landscape.
- **SQLite database layer** — stop reprocessing from scratch. Required before public launch.
- **Signal Performance Ledger** — every param gets running track record.
- **Team Chaos Index** — Upset Causer + Upset Victim score per team.
- **Bogey Team Bias** — fixture-specific underperformance signal.
- **Weekly Scoring Index** — total goals per gameweek, high/low scoring week detection.
- **Confidence-Weighted Accuracy** — primary metric going forward, not overall accuracy.
- **Confidence calibration pass** — do once, do properly. Enough 100% failure cases logged now.
- **Scheduled automation** — Windows Task Scheduler, weekly workflow.
- **Gary as Standalone Analyst** — Gary reads predictions CSV, params JSON, evolution history. Introduce when Signal Performance Ledger is built.
- **External Signal Layer Phase 3** — injury index, news sentiment. Longer term, paid sources.
- **Result auto-logging** — script that takes results CSV and scores predictions.
- **CSV stat signal pipeline** — shots, red cards, HT score, corners as DPOL signals.

---

## Expanded Roadmap (Full)

### External Signal Layer (next major workstream)
- Phase 1 — Referee, travel, fixture timing, public holidays, motivation index (no API) ✅
- Phase 2 — Weather via Open-Meteo (free, historical + forecast)
- Phase 3 — Injury index, news sentiment, fan sentiment (longer term, paid sources)
- Every signal: param slot added to DPOL at 0, DPOL validates which stick
- Every signal: fed to Gary so he can reason about context, not just statistics

### Brain / Learning Layer
- Signal Performance Ledger — every param gets running track record
- DPOL Landscape Logger — log candidate evals, map parameter space, visualise
- Meta-Learning Layer — DPOL builds memory across evolution runs
- Pattern Memory — logs conditions that preceded upsets, draws, chaos
- Param Resurrection Trigger — rejected params monitored, flagged for retest
- Closed Learning Loop — Signal ledger → Pattern memory → DPOL → Params → Predictions → Results → Signal ledger

### Product / Gary
- **Acca Builder** — Gary's two-stage combination engine. Stage 1: high-conviction picks. Stage 2: decorrelated combinations. Upset acca as premium flagship. Pre-generated Friday for free/regular tiers, bespoke live for premium.
- Gary App — standalone AI football companion. Free tier: Premier League chat and general football. Paid tiers: other leagues, accas, draw intel, upset flags. Gary naturally references EdgeLab as his "source." Funnel into Skool community.
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

### Data
- 17 tiers live. European evolution in progress.
- Phase 1 signals to be retested on full 137,645-match dataset.
- Future: all major world leagues, then eventually every league with structured data.

### Session-Closing Scalability Check

At the end of every session, ask: has today's work introduced any new scalability debt?

Current known debt (not urgent — app layer handles most of this at launch):
- GaryBrain loads full dataset into memory per instantiation — needs caching before public launch
- No API wrapper around Gary — needed before app integration
- params.json write contention at scale — SQLite migration resolves this
- All of this is app-layer infrastructure, not EdgeLab's problem to solve today

---

## Between-Session Notes (Session 14 → 15)

- Domains registered: **garyknows.com** (£8.37) and **everyoneknowsagary.com** (£8.37)
- garyknows.ai — available but £68/yr, left for now. edgelab.ai — taken/squatted.
- Brand structure confirmed: EdgeLab = engine/data platform, Gary = public face
- **Sports Intelligence Platform vision parked** — architecture is sport-agnostic by design. Football is the proof of concept. Cobey (basketball), Cooper (American football), Rico (baseball) — same DPOL brain, different data and voice.
- **Gary avatar** — fully interactive speaking avatar is achievable within build timeline. ElevenLabs for voice, HeyGen/D-ID for lip-sync. Audio-first with animated loop is production-ready now. Real-time fully interactive video is close.
- **App/website build** — Claude can build full backend, frontend, Gary chat interface, admin dashboard. Deployment is a human job (Railway/Render/VPS). App store submission needs developer accounts. ElevenLabs/HeyGen integration: code written by Claude, accounts/keys by Andrew.
- **Anthropic API at scale** — self-serve up to serious volume. Enterprise agreement when traction justifies it. Caching strategy (pre-generate Gary's Friday predictions, serve cached to all users, one API call per fixture per week) solves 90% of cost problem regardless of user count.
- **Player data** — API-Football Pro has lineups, goalscorers, assists. Future Gary workstream — injury_index SLOT already waiting for it.

---

## Freemium Tier Structure

| Tier | Price | Features |
|------|-------|----------|
| Free | £0 | Chat with Gary, ask who wins any match, ad supported |
| Regular | £5-10/month | Full predictions table, confidence, chaos ratings, pre-generated accas |
| Serious Punter | £15-20/month | DTI breakdown, draw intelligence, upset flags, Weekly Scoring Index, PDF |
| The Edge | £25-30/month | Player DPOL, Team Chaos Index, upset pattern analysis, bogey team alerts, bespoke live acca builder |

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

# Generate predictions + Gary's take on every fixture
python edgelab_predict.py --data history/ --fixtures databot_output/YYYY-MM-DD_fixtures.csv --gary

# Gary on a single fixture
python edgelab_gary.py --data history/ --home "Team A" --away "Team B" --date YYYY-MM-DD --tier E2

# Gary react to result
python edgelab_gary.py --data history/ --home "Team A" --away "Team B" --date YYYY-MM-DD --tier E2 --react D --score "0-0"

# Full DPOL evolution — all 17 tiers
python edgelab_runner.py history/ --tier all --boldness small

# English tiers only
python edgelab_runner.py history/ --tier english --boldness small

# European tiers only
python edgelab_runner.py history/ --tier european --boldness small

# Single tier
python edgelab_runner.py history/ --tier E0

# Draw intelligence grid search
python edgelab_gridsearch.py history/

# Show saved params
python edgelab_config.py show
```

---

## How to Resume

1. Paste this entire document into a new Claude session
2. Upload: all 12 .py files + edgelab_params.json + history.zip
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
