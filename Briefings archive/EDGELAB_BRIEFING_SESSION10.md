# EdgeLab — Session Briefing Document
*Paste this at the start of any new Claude session to restore full project context.*
*Last updated: Session 10 — 3 April 2026*

---

## What EdgeLab Is

A multi-layer football prediction engine designed to go beyond standard statistics.
The core insight: **uncertainty itself is information** — detecting when a match is
unpredictable and using that to make smarter calls, particularly on upsets and draws.

**Owner:** Andrew Marrow
**Current status:** Engine built and validated. DataBot live (API-Football Pro).
Full forward-prediction workflow operational. Live predictions logging started.
Draw intelligence tested on expanded dataset — no signal found at current data scale.
All params re-evolved on significantly expanded dataset (53,668 matches, 120 files).
Gary's brain architecture designed this session — schema v1.0 complete.

**Market baseline:** ~49% (E0). EdgeLab E0 currently at **49.8%** on 8,669 matches.

---

## Owner Context

- Andrew has ADHD (inattentive) — one thing at a time, clear outputs, no waffle
- Works on Windows laptop + VS Code + Claude Code extension
- Pattern recognition is a strength — spots signals quickly, generates ideas fast
- Approach: intuition for signal discovery, DPOL for rigorous validation
- Not expecting every feature to work — builds iteratively, keeps what sticks
- Previous AI (ChatGPT) fabricated results. All metrics here are real and verified.
- Big picture vision comes naturally and quickly — trust it
- Small connecting details are harder — that's what Claude is for
- When gut fires even half-formed — say it out loud anyway
- ADHD hyperfocus is the superpower — the engine was built in 9 sessions on a phone then a laptop

---

## Core Design Philosophy

**Every component must be built with scalability and future integration in mind.**
Every new stage of design or development needs to have scalability and future
integration with new systems baked in from day one. Not bolted on later. This has
been true of every component so far:

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
  |-- Draw Intelligence Layer [all weights=0 — no signal on full dataset]
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

**Upload at start of every session:** all 8 files above + edgelab_data.zip

---

## params.json Note

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

## Live Results Log

### Started: week of 2 April 2026

| Match | Pred | Actual | ~D Flag | Notes |
|-------|------|--------|---------|-------|
| Wigan 0-0 Leyton Orient | A (89%) MED | D | YES | Wigan 4th consecutive game without scoring vs Orient. Bogey bias confirmed. |
| Cambridge 1-1 Swindon | H (26%) HIGH | D | YES | Cambridge dominated (xG 2.08 vs 0.51, 20 shots vs 4). 90th min equaliser. |

**Key takeaway:** Both ~D flags fired correctly on day one. Draw confidence flag is
already meaningful even without official D predictions.
HIGH chaos + low confidence + ~D = treat as draw candidate regardless of official prediction.

---

## Bogey Team Watch List v1.0

To be validated statistically by Team Chaos Index:

- Wigan ⚠️ (already validated match 1)
- Leeds
- Cardiff
- Swansea
- TBC (more to be recalled)

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

## SESSION 10 — GARY'S BRAIN

### The Philosophy

Gary is not just a prediction tool. He is a trusted mate who happens to know more
about football than anyone. But before Gary gets a personality, Gary needs a brain.
The brain comes first. The mouth comes later.

**The approach:**
- Build basic Gary now using existing data — he can have intelligent opinions immediately
- Design him from day one so new capabilities plug straight in as additional data sources
- No rebuilding — only expanding
- DPOL does not need to be finished before touching Gary
- Gary just needs to know what he knows AND what he doesn't know yet

**The two layers:**
- **Basic Gary brain** — references raw historical stats, current form, H2H, basic context. Buildable now.
- **Learned Gary brain** — references Signal Performance Ledger, pattern memory, DPOL discoveries. Needs framework first.

### Gary's Brain — Knowledge Schema v1.0

```
MATCH_CONTEXT
├── home_team
├── away_team
├── date
├── tier
├── kickoff
├── home_position
├── away_position
├── home_points
├── away_points
├── home_gd
└── away_gd

FORM
├── home_last5_results
├── home_last5_goals_scored
├── home_last5_goals_conceded
├── home_last5_clean_sheets
├── home_current_streak
├── away_last5_results
├── away_last5_goals_scored
├── away_last5_goals_conceded
├── away_last5_clean_sheets
└── away_current_streak

H2H
├── last6_meetings (result, score, date)
├── h2h_home_win_rate
├── h2h_draw_rate
├── h2h_away_win_rate
├── bogey_flag
└── bogey_direction (which team suffers)

MATCH_FLAGS
├── post_international_break
├── dead_rubber
├── relegation_battle
├── promotion_chase
├── fixture_congestion
├── rest_days_home
├── rest_days_away
├── [injury_index — SLOT]
└── [weather_factor — SLOT]

WORLD_CONTEXT
├── world_event_flag
├── event_type
│   ├── pandemic
│   ├── conflict
│   ├── economic_shock
│   ├── national_event
│   └── other
├── severity_tier (LOW/MED/HIGH/CRITICAL)
├── crowd_context
│   ├── normal
│   ├── reduced_capacity
│   └── behind_closed_doors
├── event_description
├── [sentiment_index — SLOT, news API]
└── [social_mood_score — SLOT, future]

ENGINE_OUTPUT
├── prediction (H/D/A)
├── confidence
├── dti
├── chaos_tier
├── draw_score
├── approx_draw_flag
├── upset_score
├── upset_flag
├── pred_scoreline
├── btts_flag
├── [signal_ledger_context — SLOT]
├── [team_chaos_index — SLOT]
├── [bogey_team_alert — SLOT]
├── [weekly_scoring_index — SLOT]
└── [player_dpol_output — SLOT]

GARY_MEMORY
├── [signal_performance_ledger — SLOT]
├── [pattern_memory — SLOT]
├── [meta_learning_context — SLOT]
├── [param_resurrection_candidates — SLOT]
└── [sport_specific_context — SLOT, Cobey/Cooper/Rico]
```

### World Context Signal

A genuinely novel signal — macro mood at time of fixture, using general news data.
The hypothesis: collective world events affect players, crowds, home advantage,
and result patterns in statistically measurable ways.

Examples already in the historical data:
- **Covid** — behind closed doors, home advantage collapsed
- **Ukraine invasion early 2022** — collective European anxiety
- **Economic shocks** — away support drops, crowd intensity changes
- **National events** — mood affects everyone including players

Gary uses this not just for predictions but for intelligent commentary:
*"This was March 2020. Nobody knew what was happening. The data from this
period needs handling carefully."*

### Next Steps for Gary's Brain (Session 11)

1. **Build the data access layer** — populates the schema from existing CSVs
2. **Build the context builder** — assembles match facts into something Gary can reason about
3. **Build the knowledge schema as a live object** — structured dict/JSON Gary receives per match
4. **Wire to Claude API** — Gary receives context, responds in character
5. **Test on real matches** — feed Wigan vs Orient, Cambridge vs Swindon, see what he says

---

## Expanded Roadmap (Full)

### Brain / Learning Layer
- **Signal Performance Ledger** — every param gets running track record
- **Meta-Learning Layer** — DPOL builds memory across evolution runs
- **Pattern Memory** — logs conditions that preceded upsets, draws, chaos
- **Param Resurrection Trigger** — rejected params monitored, flagged for retest
- **Closed Learning Loop** — Signal ledger → Pattern memory → DPOL → Params → Predictions → Results → Signal ledger

### New Signals
- **Team Chaos Index** — Upset Causer score + Upset Victim score per team
- **Bogey Team Bias** — fixture-specific underperformance signal, separate from chaos index
- **Weekly Scoring Index** — total goals per gameweek, high/low scoring week detection
- **World Context Signal** — macro mood from news data at time of fixture
- **Confidence-Weighted Accuracy** — primary metric going forward, not overall accuracy

### Infrastructure
- **SQLite database layer** — stop reprocessing everything from scratch
- **Result auto-fetcher** — DataBot pulls results for logged predictions automatically
- **Scheduled automation** — Windows Task Scheduler, weekly workflow
- **Statistical data collection** — red cards, scorers, assists, clean sheets

### Product / Gary
- **Gary's personality layer** — Claude API, "trusted mate" archetype
- **Gary's data access layer** — queries schema in real time
- **Gary's TikTok / Instagram** — Friday predictions videos, AI-generated avatar
- **Design your own Gary** — user describes ideal football mate, personalised avatar generated
- **Freemium tier** — Free / Regular (£5-10) / Serious Punter (£15-20) / The Edge (£25-30)
- **Charity betting pot** — 2% of subscription revenue, scales with business

### Sports Expansion
- **Cobey** — Basketball (Chicago, snapback)
- **Cooper** — American Football (Texas, very serious)
- **Rico** — Baseball (New York, lifelong fan)
- Same DPOL brain, same uncertainty architecture, different data + personality

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
- Build historical databases in spare time — every major European league, player stats,
  manager records, financial market data, weather data
- Data collected now = months of evolution time saved later

---

## How to Run

```bash
# Pull fixtures and odds
python edgelab_databot.py --key YOUR_KEY --days 7

# Generate predictions
python edgelab_predict.py --data history/ --fixtures databot_output/YYYY-MM-DD_fixtures.csv

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
2. Upload: edgelab_engine.py, edgelab_dpol.py, edgelab_runner.py,
   edgelab_config.py, edgelab_params.json, edgelab_gridsearch.py,
   edgelab_databot.py, edgelab_predict.py
3. Claude will confirm files received and be fully up to speed
4. First jobs next session:
   a. Check E0 draw weights in params.json — should be 0, currently showing 0.05
   b. Build Gary's data access layer — populates schema v1.0 from existing CSVs
   c. Build context builder — assembles match facts into structured object
   d. Review any new live results and mark actuals on predictions CSV

---

## Between-Session Briefing Protocol

At the end of every between-session conversation, generate a briefing update summary.
Paste into session briefing doc before starting new session.
Keeps the single source of truth current without pasting entire raw chat logs.
