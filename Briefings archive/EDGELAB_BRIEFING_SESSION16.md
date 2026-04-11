# EdgeLab — Session Briefing Document
*Last updated: Session 16 — 5 April 2026*

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
External Signal Layer Phase 1 built, wired, extended to all 17 tiers.
Phase 2 weather bot built and wired (edgelab_weather.py).
European DPOL run complete — all 12 European tiers evolved.
--tier all DPOL run in progress (session 16 — pick up when complete).
Acca builder built (edgelab_acca.py) — first moist run today on current params.
First real backed acca pending stable --tier all params.

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
- Run the scalability check at session close without being prompted
- If sycophantic patterns are creeping in — catch them
- If there is a better way to phrase a prompt or a working pattern — say so

### Andrew's responsibilities

- Brain dumps are fine and encouraged — Claude will filter and sequence
- Say "parking that" mid-session to log an idea and move on without losing thread
- Say "just build it" when discussion isn't needed
- Call out anything that feels off immediately — tone, quality, direction
- Trust the gut on product and signal ideas — but expect Claude to push back if timing is wrong

---

## Build Philosophy

- Build one thing. Test it. Improve or remove it. Move on.
- Build immediately only if it makes the current model work better right now
- Everything else goes on the parked list in the right place — not the top
- The roadmap is the roadmap. Work it in order unless there is a compelling reason not to
- All Gary architecture decisions must remain gender-neutral at code level — personality lives in prompts only, never in logic

---

## Core Design Philosophy

**Every component must be built with scalability and future integration in mind.**

- `edgelab_params.json` is SQLite-forward by design
- DataBot architecture is reusable across all sports
- The upset layer has external signal hooks designed in before the signals exist
- DPOL's candidate space has draw intelligence slots that sat at 0 until the signal was ready
- Gary's brain schema has named SLOT entries for every future capability

---

## Session Closing Protocol

Before writing the briefing doc and closing every session, ask:
**Has today's work introduced any new scalability debt?**

Current known debt (not urgent — app layer handles most of this at launch):
- GaryBrain loads full dataset into memory per instantiation — needs caching before public launch
- No API wrapper around Gary — needed before app integration
- params.json write contention at scale — SQLite migration resolves this
- Gary's weather fetch in _build_match_flags makes a live API call per fixture —
  needs pre-fetch + cache per matchday before public launch (same pattern as Friday acca caching)

---

## Architecture

```
Match Data (CSV / API)         External Signal Sources
        |                               |
        |              ┌────────────────┤
        |              │  Weather       │ Open-Meteo (free, historical + forecast) [BUILT S16]
        |              │  Ground data   │ Coordinates, 481 entries, all 17 tiers [ACTIVE]
        |              │  Calendar      │ Bank holidays, fixture timing [ACTIVE]
        |              │  Referee       │ Already in CSVs [ACTIVE]
        |              │  Motivation    │ Derived from standings [ACTIVE]
        |              │  [Injury]      │ SLOT — future paid source
        |              │  [Sentiment]   │ SLOT — future news/social API
        |              └────────────────┤
        |
Pre-processor → Feature Engine → Prediction Engine → DPOL → DataBot
        |
Output: H/D/A + confidence + DTI + chaos tier + draw score + scoreline + btts
        + upset_score + upset_flag + external signal context
        |
Gary (optional) — full match briefing per fixture via --gary flag
        |
Acca Builder (edgelab_acca.py) — two-stage, five acca types [BUILT S16]
```

---

## Files

| File | Status | Notes |
|------|--------|-------|
| edgelab_engine.py | **Updated S16** | w_weather_signal added to EngineParams |
| edgelab_dpol.py | **Updated S16** | w_weather_signal added to LeagueParams |
| edgelab_runner.py | Updated S15 | All 17 tiers. --tier english / european / all |
| edgelab_config.py | **Updated S16** | Phase 1 + Phase 2 signal display. w_weather_signal in load_params |
| edgelab_params.json | **Updated S16** | All 17 tiers evolved. --tier all in progress |
| edgelab_signals.py | Final S15 | 481 ground coords, all Phase 1 signals |
| edgelab_weather.py | **NEW S16** | Phase 2 weather bot. Open-Meteo. Historical + forecast |
| edgelab_gary_brain.py | **Updated S16** | weather_factor SLOT promoted to live fields |
| edgelab_gary_context.py | Final S15 | Tier vocabulary, all 17 tiers |
| edgelab_gary.py | Final | Gary API wrapper |
| edgelab_databot.py | Final S15 | English IDs verified. European IDs partially verified |
| edgelab_predict.py | Final | Full prediction pipeline |
| edgelab_acca.py | **NEW S16** | Two-stage acca builder. Five acca types |
| edgelab_gridsearch.py | Final | Draw intelligence grid search |

---

## API-Football League IDs

### English — verified
| Tier | ID | League |
|------|----|--------|
| E0 | 39 | Premier League |
| E1 | 40 | Championship |
| E2 | 41 | League One |
| E3 | 42 | League Two |
| EC | 43 | National League |

### European — confirmed from public sources, verify live via DataBot
| Tier | ID | League |
|------|----|--------|
| SP1 | 140 | La Liga |
| SP2 | 141 | La Liga 2 |
| D1 | 78 | Bundesliga |
| D2 | 79 | 2. Bundesliga |
| I1 | 135 | Serie A |
| I2 | 136 | Serie B |
| N1 | 88 | Eredivisie |
| B1 | 144 | Belgian Pro League |
| SC0 | 179 | Scottish Premiership |
| SC1 | 180? | Scottish Championship — needs live verification |
| SC2 | 181? | Scottish League One — needs live verification |
| SC3 | 182? | Scottish League Two — needs live verification |

DataBot logs league name on first fetch — verify SC1/SC2/SC3 IDs by checking what
name comes back in the logs.

---

## Dataset

**417 CSV files, flat in history/ folder, 25 years, 17 tiers, 137,645 matches.**

| Tier | Matches | What it is |
|------|---------|------------|
| E0 | 8,360 | Premier League |
| E1 | 12,144 | Championship |
| E2 | 12,544 | League One |
| E3 | 12,584 | League Two |
| EC | 10,130 | National League |
| SP1 | 8,740 | La Liga |
| SP2 | 10,626 | La Liga 2 |
| D1 | 6,732 | Bundesliga |
| D2 | 6,732 | 2. Bundesliga |
| I1 | 8,518 | Serie A |
| I2 | 10,022 | Serie B |
| N1 | 6,964 | Eredivisie |
| B1 | 6,246 | Belgian First Division A |
| SC0 | 5,195 | Scottish Premiership |
| SC1 | 4,052 | Scottish Championship |
| SC2 | 4,029 | Scottish League One |
| SC3 | 4,027 | Scottish League Two |
| **TOTAL** | **137,645** | |

Dataset hash: 580b0f3a1667

---

## Evolved Params

### English tiers (session 14 — final)

| Tier | Accuracy | Matches | Notes |
|------|----------|---------|-------|
| E0 | 49.9% | 8,669 | w_form=0.774 home_adv=0.400 |
| E1 | 44.5% | 12,059 | w_form=0.460 home_adv=0.604 |
| E2 | 44.4% | 11,906 | w_form=0.797 home_adv=0.514 |
| E3 | 42.3% | 11,954 | w_form=0.401 home_adv=0.197 |
| EC | 45.1% | 9,080 | w_form=0.726 home_adv=0.326 |

### European tiers (session 16 — European run complete)

| Tier | Baseline | Evolved | Delta | Matches |
|------|----------|---------|-------|---------|
| B1 | 47.1% | 47.1% | +0.0% | — |
| D1 | 47.1% | 47.4% | +0.4% | — |
| D2 | 42.0% | 42.2% | +0.2% | — |
| I1 | 48.1% | 48.6% | +0.5% | — |
| I2 | 40.6% | 40.6% | +0.1% | — |
| N1 | 50.5% | 50.8% | +0.3% | — |
| SC0 | 49.4% | 49.5% | +0.1% | — |
| SC1 | 43.1% | 43.2% | +0.1% | — |
| SC2 | 46.9% | 47.2% | +0.2% | — |
| SC3 | 46.1% | 46.6% | +0.5% | — |
| SP1 | 46.5% | 47.5% | +1.0% | — |
| SP2 | 41.0% | 41.2% | +0.2% | — |
| **OVERALL** | **45.7%** | **46.0%** | **+0.3%** | — |

**Key observations:**
- SP1 best performer +1.0% — La Liga has clearest learnable patterns
- I1, SC3 both +0.5% — good signal
- Cold start across all 12 tiers — this is the floor not the ceiling
- Draw detection essentially off — 209 draws predicted from 3,083 actual (6.8% recall)
- --tier all run will be where draw intelligence and Phase 1 signals get proper activation shot

### Phase 1 signal weights — all tiers
w_ref_signal=0.0, w_travel_load=0.0, w_timing_signal=0.0, w_motivation_gap=0.0
All at zero pending --tier all activation test.

### Phase 2 signal weights — all tiers
w_weather_signal=0.0 — built and wired, pending DPOL activation.

---

## DPOL Status

- European run: **COMPLETE** — all 12 tiers, params saved
- --tier all run: **IN PROGRESS** (session 16) — all 17 tiers, warm start from European results
- After --tier all: check signal activation. If any signals activate, run again.
- SP2 final result: w_form=0.9500 w_gd=0.3000 home_adv=0.2500 coin_dti_thresh=0.8054

---

## Ordered Work Queue

### Session 17 — priorities in order

1. **Log --tier all results** — compare to European-only run. Did any Phase 1 signals activate?
2. **If signals activated** — run DPOL again to let it optimise around newly active weights
3. **Verify Scottish DataBot IDs** — SC1/SC2/SC3 need live verification via DataBot test fetch
4. **Wire European league IDs into DataBot** — add LEAGUE_MAP entries for all 12 European tiers
5. **First proper backed acca** — params stable, DataBot pulling European fixtures, acca builder live
6. **Weather batch run** — run get_weather_batch_chunked() on full 137k dataset overnight. Cache results for DPOL weather signal activation test

---

## Self-Funding Protocol

Small stake per round on Gary's acca selections. All returns go back into the build.
Real money = most honest feedback loop. Live accuracy record starts from first bet.
Track record logged alongside live results from day one.

First moist run: 5 April 2026. Baseline params, practice run. Token stake only.

---

## Acca Builder (edgelab_acca.py)

Two-stage process. Standalone module. Takes predictions CSV as input.

Stage 1 — filters to high-conviction picks: conf ≥ 52%, LOW/MED chaos, no upset flag.
Stage 2 — selects best decorrelated combination. Penalises same-tier same-day pairs.

Five acca types: result, safety, value (edge vs bookmaker), upset, BTTS.

```bash
# Gary's top 3 five-fold result accas
python edgelab_acca.py predictions/2026-04-05_predictions.csv

# Full matchday briefing — one of each type
python edgelab_acca.py predictions/2026-04-05_predictions.csv --all-types

# Bespoke — 4-fold, max 15/1, no lower Scottish
python edgelab_acca.py predictions/2026-04-05_predictions.csv --fold 4 --max-odds 15 --exclude SC2,SC3,EC

# Show all qualifying picks first
python edgelab_acca.py predictions/2026-04-05_predictions.csv --picks
```

**Note:** Acca builder is only as good as the params feeding it.
First real backed acca waits for stable --tier all params.

---

## Weather Bot (edgelab_weather.py)

Open-Meteo API. Free, no key required. Historical + forecast auto-detected.

- `get_weather_for_fixture()` — single match, for Gary briefing
- `get_weather_batch()` — full dataframe, for DPOL training
- `get_weather_batch_chunked()` — checkpoint saves every 1000 rows, safe for 137k run

Weather load signal (0–1): rain 50% weight, wind 35%, temperature 15%.
Gary gets plain English: "Heavy rain (6mm), strong wind (55km/h), 8°C"
Weather flag fires when load ≥ 0.25.

**Scalability note:** Gary's weather fetch is live per fixture call. Needs pre-fetch
+ cache per matchday before public launch.

```bash
# Test on single fixture
python edgelab_weather.py "Wigan Athletic" "2026-04-12" 15 E2
```

---

## External Signal Layer

### Phase 1 — Static / derivable (built, wired, all weights at 0.0)

| Signal | Status |
|--------|--------|
| Referee stats | Active — no Referee col in EC |
| Travel load | Active — 481 grounds, all 17 tiers |
| Fixture timing | Active — bank holidays, festive, midweek |
| Motivation index | Active — dead rubber, six-pointer, survival |

### Phase 2 — Free API (built, wired, pending activation)

| Signal | Status |
|--------|--------|
| Weather (Open-Meteo) | Built S16 — w_weather_signal=0.0 |

### Phase 3 — Richer signals (future)

| Signal | Status |
|--------|--------|
| Injury / availability | SLOT |
| News sentiment | SLOT |
| Fan sentiment | SLOT |
| Manager sacking effect | SLOT — could be Phase 1 |

---

## Gary — Product Vision

**No last name. Nobody knows it. Something to do with Sandra from the shop.**

Tagline: **"Everyone knows a Gary."**

- Knowledgeable but never arrogant
- Honest when uncertain — "this one's a coin flip mate, I'd leave it"
- Celebrates your wins like they're his
- Has opinions, explains them, occasionally wrong, always transparent
- Delivered via Claude API

### Interface Stack (parked — future build)

- **WhatsApp-style UI** — Gary texts tips and accas as push notifications, looks like messages from a mate
- **Proactive personalised texts** — Gary checks in about fixtures he knows you care about. News, updates, casual chat. Bespoke per user.
- **Incoming call notification** — renders as incoming call on screen. One tap answers. Gary rings you.
- **Proactive video calls** — Gary initiates video calls with the big tips
- **On-demand FaceTime** — you ring Gary when you want his read
- **Launch moment** — text product launches first. When video arrives, Gary rings to announce it. In character. The upgrade is a plot point.

### Gary Modes

- **Standard Gary** — knowledgeable mate, honest, warm, plain English
- **Gary Unfiltered** — pub version. Swears a bit, calls you a nobhead for bad bets. Banter, never mean. User opt-in setting.

### Gary Features (parked — future build)

- **Gary remembers you** — logs what he recommended, whether you backed it, result. References it. "You didn't listen last week." Core retention mechanic.
- **Confidence calibration display** — running track of whether Gary's stated confidence bands actually hit. "Gary's 65%+ picks landing at 71% over 6 weeks." Trust builder.
- **Gary spots bookmaker edge** — flags when engine confidence significantly exceeds implied bookmaker probability. Value betting framing. Premium tier.
- **Devil's Gary** — shadow Gary who always takes the opposite position. "Gary says Arsenal. Devil's Gary says Fulham." Richer content, more honest, great TikTok material.
- **Printable acca slip** — Gary generates printable bet slip. Take to bookies, hand over.
- **Direct bookmaker integration** — Gary loads bet into user's account, they approve. Betfair/Bet365/Sky Bet APIs. Needs track record first.
- **Bookmaker advertising** — sponsored placements in free tier. Contextual, relevant.

### Gaby

Female football analyst. Same engine, same DPOL, same brain schema as Gary.
Not a reskin — genuinely distinct voice and personality.
Women's football specialism. Crossover appeal in both directions.
Architecture already supports it — system prompt is the only thing that makes it Gary.
Build when Gary is stable. Estimated one week of work.
All Gary architecture decisions remain gender-neutral at code level.

---

## Product Architecture

- **EdgeLab** = data platform (Skool community, serious punters, raw numbers, DTI breakdowns)
- **Gary** = AI mate (app, conversational, casual fans, dead simple)
- **Gaby** = female analyst, same engine, second product
- Flywheel: Gary → EdgeLab → Gary tier upgrade → back and forth

### Sports Expansion (parked)
- Cobey (basketball), Cooper (American football), Rico (baseball)
- Same DPOL brain, different data + personality
- Football is the proof of concept

### Freemium Tier Structure

| Tier | Price | Features |
|------|-------|----------|
| Free | £0 | Chat with Gary, ask who wins any match, ad supported, bookmaker ads |
| Regular | £5-10/month | Full predictions table, confidence, chaos ratings, pre-generated accas |
| Serious Punter | £15-20/month | DTI breakdown, draw intelligence, upset flags, Weekly Scoring Index |
| The Edge | £25-30/month | Player DPOL, Team Chaos Index, upset patterns, bogey team alerts, bespoke live acca builder |

### Charity Betting Pot
2% of monthly subscription revenue into betting pool.
All profits donated to gambling harm charities.
Real money bets = most credible public accuracy record.

---

## Known Issues

### E1 Home Bias Problem
At high DTI across a whole matchday, engine calls H on nearly every match.
Fix direction: DTI-weighted randomisation or draw/away floor at high chaos.
Investigate during confidence calibration pass.

### Draw Detection — European Tiers
209 draws predicted from 3,083 actual in European DPOL run (6.8% recall).
Draw intelligence weights all at 0.0 on cold European data.
--tier all run expected to improve this significantly.

---

## Bogey Team Watch List v1.0

- Wigan ⚠️ (validated match 1)
- Leeds
- Cardiff
- Swansea
- TBC

---

## Gary's Brain — Knowledge Schema v1.0

```
MATCH_CONTEXT — fixture facts, league positions
FORM — last 5 results, goals, clean sheets, current streak
H2H — last 8 meetings, win/draw/loss rates, bogey flag (threshold 0.625)
MATCH_FLAGS — post-intl-break, fixture congestion, rest days, weather [LIVE S16], [injury SLOT]
WORLD_CONTEXT — static event table (Covid, Ukraine, Queen, cost-of-living), crowd context
ENGINE_OUTPUT — prediction, confidence, DTI, chaos tier, draw score, ~D flag,
                upset score, upset flag, scoreline, BTTS,
                [signal ledger SLOT], [team chaos index SLOT], [bogey team alert SLOT]
GARY_MEMORY — [signal performance ledger SLOT], [pattern memory SLOT],
              [meta-learning SLOT], [param resurrection SLOT], [sport-specific SLOT]
```

---

## Live Results Log

### Week of 2–3 April 2026

#### E1 — Apr 3: 2/11 = 18%
Engine called H on all 11. Avg DTI 0.847, 9/11 HIGH chaos. Home bias problem.

#### E2 — Apr 3: 6/11 = 55%
Draw intelligence (~D flag) performing well.

---

## Infrastructure

- 128TB external SSD acquired (£35)
- DataBot architecture reusable across all sports
- Domains: garyknows.com, everyoneknowsagary.com (both £8.37)
- SQLite migration: future — resolves params.json write contention at scale

---

## How to Run

```bash
# Pull fixtures and odds
python edgelab_databot.py --key YOUR_KEY --days 7

# Generate predictions
python edgelab_predict.py --data history/ --fixtures databot_output/YYYY-MM-DD_fixtures.csv

# Predictions + Gary
python edgelab_predict.py --data history/ --fixtures databot_output/YYYY-MM-DD_fixtures.csv --gary

# Gary on single fixture
python edgelab_gary.py --data history/ --home "Team A" --away "Team B" --date YYYY-MM-DD --tier E2

# Acca builder
python edgelab_acca.py predictions/YYYY-MM-DD_predictions.csv --all-types

# DPOL — all 17 tiers
python edgelab_runner.py history/ --tier all --boldness small

# DPOL — European only
python edgelab_runner.py history/ --tier european --boldness small

# Show saved params (now shows Phase 1 + Phase 2 signals)
python edgelab_config.py show

# Weather test
python edgelab_weather.py "Wigan Athletic" "2026-04-12" 15 E2
```

---

## How to Resume

1. Upload updated briefing doc to project knowledge (replace old version)
2. Upload all .py files + edgelab_params.json
3. Claude confirms files received and is fully up to speed
4. Work the ordered queue from the top

---

## Between-Session Protocol

At the end of every session, Claude generates the updated briefing doc.
Andrew saves it and uploads to project knowledge, replacing the previous version.
Briefing doc is always the source of truth.
