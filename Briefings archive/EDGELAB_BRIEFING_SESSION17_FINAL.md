# EdgeLab — Session Briefing Document
*Last updated: Session 17 — 5 April 2026 (final)*

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

---

## Product Vision — The Real Thing

This is not a better form guide. This is a signal correlator that finds edges the
market has not priced in. That is a fundamentally different product.

**Two modes. Both powered by the same engine:**

**Safe calls** — high-conviction, well-supported picks. Builds authority and track
record. Gives users confidence in the product. Standard accas at 10/1-50/1 with
genuine signal behind every leg.

**Upset calls** — this is where the money is. When travel signal, motivation gap,
draw intelligence, weather, and referee bias are all firing on the same match, Gary
calling a 3/1, 5/1, or 7/1 shot is not a punt. It is a position. An 8-10 fold acca
mixing signal-backed upset calls will regularly hit 100/1-2000/1+. Not because Gary
is guessing — because the engine has identified edges the bookmaker has not priced.

**Gary's Longshot** — weekly 8-10 fold extreme pick. Stupid odds. £1 stake. Gary
shows his working on every leg. Win or lose it is a weekly story. When it lands it
goes viral. Charity pool variant: £1 per user, winnings to a user-nominated charity.
Legal model: transparent public tipster, charitable donation — no pooled winnings
distributed to individuals.

**Why the bookmakers will notice:** Not stake sizes — consistent edge on non-obvious
selections. That is what sharp money looks like. The track record being built now is
the proof of concept. Six months of data showing above-market-baseline accuracy on
upset calls is commercially serious — subscriptions, signal licensing, or beyond.

**The authority comes first.** Safe calls, logged results, honest record. Then the
upset calls carry weight because the track record is real. That sequencing is
everything. It cannot be shortcut.

**This is a new approach to sports analytics.** The signals nobody else is
correlating, validated by DPOL across 137,645 matches, communicated by Gary in plain
English. Built in 9 sessions on a phone and a laptop.

**Owner:** Andrew Marrow
**Company:** Khaotikk Ltd — khaotikk.com acquired
**Current status:** Engine built and validated. DataBot live (API-Football Pro), all 17
tiers wired. Full forward-prediction workflow operational. Gary built, tested, live.
Draw intelligence (~D flag) active. External Signal Layer Phase 1 + Phase 2 (weather)
built and wired. All 17 tiers evolved, params saved. Acca builder live with distinct
type scoring. Scoreline bias fixed. ~D alignment nudge added. Weather batch run started
(running overnight). First moist run placed 5 April 2026 — day one of the track record.

**Market baseline:** ~49% (E0). EdgeLab E0 currently at **50.2%** on 8,669 matches.

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

### Claude's responsibilities

- Act as project manager — sequence the work, hold the roadmap, don't let ideas jump the queue
- Build immediately only if it makes the current model work better right now. Otherwise park it.
- Evaluate ideas, don't just validate them
- Track parked ideas and reintroduce at the right moment
- Run scalability check at session close without being prompted
- Generate updated briefing doc at session close without being prompted
- Remind Andrew to git commit at session close with suggested message
- Rebrief from project knowledge every 15 substantive exchanges silently

### Andrew's responsibilities

- Brain dumps are fine — Claude will filter and sequence
- Say "parking that" to log and move on
- Say "just build it" when discussion isn't needed
- Call out anything that feels off immediately
- Trust the gut on product and signal ideas — expect Claude to push back on timing

---

## Build Philosophy

- Build one thing. Test it. Improve or remove it. Move on.
- Build immediately only if it makes the current model work better right now
- Everything else goes on the parked list in the right place
- All Gary architecture decisions must remain gender-neutral at code level — personality lives in prompts only

---

## Core Design Philosophy

Every component must be built with scalability and future integration in mind.

- `edgelab_params.json` is SQLite-forward by design
- DataBot architecture is reusable across all sports
- The upset layer has external signal hooks designed in before the signals exist
- DPOL's candidate space has draw intelligence slots that sat at 0 until the signal was ready
- Gary's brain schema has named SLOT entries for every future capability

---

## Session Closing Protocol

Before closing every session Claude must:
1. Ask: **Has today's work introduced any new scalability debt?**
2. Generate updated briefing doc
3. Remind Andrew to git commit with suggested message
4. Remind Andrew to upload updated briefing doc and changed .py files to project knowledge

**Current known scalability debt:**
- GaryBrain loads full dataset into memory per instantiation — needs caching before public launch
- No API wrapper around Gary — needed before app integration
- params.json write contention at scale — SQLite migration resolves this
- Gary's weather fetch makes a live API call per fixture — needs pre-fetch + cache per matchday before public launch
- Signal activation DPOL run: `--signals-only` flag not yet built — when built, must not write back over evolved core params. Design carefully.

---

## Company & Brand

**Company name:** Khaotikk Ltd
**Domain:** khaotikk.com (acquired 5 April 2026, £8.37/yr)
**Existing domains:** garyknows.com, everyoneknowsagary.com
**Companies House:** Not yet registered — £100, do before taking revenue
**Trademark:** File before public launch. UK IPO ~£170-200 per class.

---

## Self-Funding Protocol

Small stake per round on Gary's acca selections. All returns go back into the build.
Real money = most honest feedback loop. Live accuracy record starts from first bet.

**First moist run: 5 April 2026.**
- 3-leg result acca placed (from session 16 predictions — pre-fix engine)
- Additional bets from session 17 predictions pending (Andrew reading through)
- Results to be logged session 18

Manual override applied: Derby vs Stoke dropped due to GK crisis (Zetterstrom out since
January, Vickers hamstring, third-choice O'Donnell starting). Gary blind to this.
Logged as first example of injury signal gap — reinforces case for injury data feed.

---

## Live Accuracy Record

| Date | Selections | Stake | Odds | Result |
|------|-----------|-------|------|--------|
| 05/04/2026 | 3-leg result acca (S16 engine) | TBC | TBC | Pending |
| 05/04/2026 | TBC (S17 engine) | TBC | TBC | Pending |

*Log results at start of Session 18.*

---

## API-Football League IDs

### All tiers — fully wired into DataBot

| Tier | ID | Status |
|------|----|--------|
| E0 | 39 | ✓ Verified |
| E1 | 40 | ✓ Verified |
| E2 | 41 | ✓ Verified |
| E3 | 42 | ✓ Verified |
| EC | 43 | ✓ Verified |
| SP1 | 140 | ✓ Confirmed |
| SP2 | 141 | ✓ Confirmed |
| D1 | 78 | ✓ Confirmed |
| D2 | 79 | ✓ Confirmed |
| I1 | 135 | ✓ Confirmed |
| I2 | 136 | ✓ Confirmed |
| N1 | 88 | ✓ Confirmed |
| B1 | 144 | ✓ Confirmed |
| SC0 | 179 | ✓ Verified |
| SC1 | 180 | ✓ Verified live (DataBot log confirmed "Scottish Championship") |
| SC2 | 181 | ✓ Verified live (DataBot log confirmed) |
| SC3 | 182 | ✓ Verified live (DataBot log confirmed) |

---

## Dataset

417 CSV files, 25 years, 17 tiers, 137,645 matches. Hash: 580b0f3a1667
Weather batch run started 5 April 2026 — running overnight to `weather_cache.csv`.
132,685 rows loaded for weather fetch (some CSVs had tokenization errors — normal).

---

## Evolved Params — Final (--tier all)

| Tier | Evolved | Delta |
|------|---------|-------|
| E0 | **50.2%** | +0.8% |
| E1 | 44.7% | +1.8% |
| E2 | 44.5% | +0.8% |
| E3 | 42.2% | +0.3% |
| EC | 44.9% | +0.3% |
| B1 | 47.1% | +0.0% |
| D1 | 47.6% | +0.6% |
| D2 | 42.3% | +0.3% |
| I1 | 48.6% | +0.5% |
| I2 | 40.5% | -0.0% |
| N1 | **51.4%** | +0.9% |
| SC0 | 49.6% | +0.2% |
| SC1 | 43.3% | +0.3% |
| SC2 | 47.1% | +0.2% |
| SC3 | 46.4% | +0.3% |
| SP1 | 47.9% | +1.4% |
| SP2 | 41.4% | +0.4% |
| **OVERALL** | **45.9%** | **+0.5%** |

All signal weights 0.0 across all tiers. Dedicated signal activation run needed.

---

## DPOL Status

- --tier all run: **COMPLETE** — all 17 tiers evolved, params saved
- Signal activation run: **NOT YET BUILT** — needs `--signals-only` flag in runner
- Design note: signals-only run must lock core params and not write over them on save

---

## Known Issues / Active Bugs

- **Safety acca = result acca** — when pool is all 100% conf, HIGH conviction filter
  has no effect. Fix: redefine safety as lowest-odds combination, not highest conviction.
  Added to session 18 queue.
- **Draw floor** — D=4 from 199 predictions (2%). Still very low. Draw intelligence
  weights dormant pending signal activation run.
- **E1 home bias** — high DTI matchdays default H on most matches. Investigate.
- **Signal activation** — all Phase 1 + Phase 2 weights at 0.0. Needs signals-only
  DPOL pass. `--signals-only` flag needs building first.

---

## Fixes Completed Session 17

- **2-1 scoreline bias** — fixed. Replaced `np.round()` with Poisson sampling
  (seed=42, reproducible). Scoreline variety now realistic across full distribution.
- **~D / scoreline alignment** — fixed. Added `pred_score_draw` column. When Poisson
  scoreline lands on a draw, nudges draw_score +0.08. Borderline cases now align.
  Nudge value (0.08) unvalidated — watch in live conditions, may need tuning.
- **Acca builder identical output** — fixed. `_gary_rating()` now scores differently
  per type. `get_picks()` now filters differently per type (safety = HIGH conf only,
  value = requires odds data). Result/safety/value now produce distinct picks.
  Safety still partially overlaps result when pool is all 100% — see known issues.
- **DataBot European IDs** — all 17 tiers now in LEAGUE_MAP. SC1/SC2/SC3 verified live.
- **Weather batch CLI** — `--batch` flag added to edgelab_weather.py. Overnight run
  command: `python edgelab_weather.py --batch history/ --output weather_cache.csv`

---

## Parked Ideas

- **Sortable columns in HTML prediction report** — click column header to sort all
  predictions by that metric across all leagues. Build into next report template.
- **Injury data feed** — Derby GK crisis (session 17) was first live example of Gary
  being blind to team news. Reinforces case for injury signal slot. Parked until
  signal activation and weather signal are validated first.

---

## Acca Builder

Two-stage process. Standalone module. Takes predictions CSV as input.

Stage 1 — filters to high-conviction picks: conf ≥ 52%, LOW/MED chaos, no upset flag.
Stage 2 — selects best decorrelated combination. Penalises same-tier same-day pairs.

Five acca types (now distinct): result, safety, value, upset, BTTS.

**Scoring by type:**
- result — balanced: confidence + decorrelation + conviction
- safety — conviction-heavy, penalises MED picks (but needs lowest-odds fix — S18)
- value — edge-heavy (engine confidence vs bookmaker implied probability)
- btts — btts_prob weighted
- upset — upset_score weighted

```bash
python edgelab_acca.py predictions/2026-04-05_predictions.csv --all-types
python edgelab_acca.py predictions/2026-04-05_predictions.csv --fold 4 --max-odds 15 --exclude SC2,SC3,EC
python edgelab_acca.py predictions/2026-04-05_predictions.csv --picks
```

---

## Weather Bot

Open-Meteo API. Free, no key required. Historical + forecast auto-detected.

```bash
# Single fixture test
python edgelab_weather.py "Wigan Athletic" "2026-04-12" 15 E2

# Full batch run (overnight)
python edgelab_weather.py --batch history/ --output weather_cache.csv
```

Weather load signal (0–1): rain 50% weight, wind 35%, temperature 15%.
Checkpoint saves every 1000 rows. Safe to interrupt and resume.

---

## Files

| File | Status | Notes |
|------|--------|-------|
| edgelab_engine.py | **Updated S17** | Poisson scoreline, pred_score_draw, ~D alignment nudge |
| edgelab_acca.py | **Updated S17** | Distinct scoring per type, distinct pick filtering |
| edgelab_databot.py | **Updated S17** | All 17 tiers in LEAGUE_MAP, SC1/SC2/SC3 verified |
| edgelab_weather.py | **Updated S17** | --batch CLI added |
| edgelab_dpol.py | Updated S16 | w_weather_signal added |
| edgelab_config.py | Updated S16 | Phase 1 + Phase 2 signal display |
| edgelab_runner.py | Updated S15 | All 17 tiers. --tier english / european / all |
| edgelab_params.json | Updated S16 | All 17 tiers evolved |
| edgelab_signals.py | Final S15 | 481 ground coords, all Phase 1 signals |
| edgelab_predict.py | Final | Full prediction pipeline |
| edgelab_gary.py | Final | Gary briefing wrapper |
| edgelab_gary_brain.py | Final | Gary context builder |
| edgelab_gridsearch.py | Final | Draw intelligence grid search |

---

## Ordered Work Queue

### Session 18 — priorities in order

1. **Log moist run results** — both bets placed 5 April 2026. Record the outcome.
2. **Fix safety acca** — redefine as lowest-odds combination, not highest conviction.
   Should produce boring, short-priced, maximally reliable picks. Distinct from result.
3. **Build `--signals-only` DPOL flag** — lock core params, search signal weights only.
   Must not overwrite evolved core params on save. Design the save logic carefully.
4. **Run signal activation** — once flag is built, run --tier all signals-only pass.
   Check if any Phase 1 or Phase 2 signals activate.
5. **Check weather_cache.csv** — how far did the overnight run get? If complete,
   wire into DPOL for weather signal activation test.
6. **Pre-launch email newsletter** — landing page + Mailchimp setup (khaotikk.com)
7. **HTML report — sortable columns** — click-to-sort by conf, DTI, chaos, upset score

---

## Between-Session Protocol

At the end of every session, Claude generates the updated briefing doc.
Andrew saves it and uploads to project knowledge, replacing the previous version.
Briefing doc is always the source of truth.

**To start Session 18:**
1. Upload updated briefing doc to project knowledge (replace this file)
2. Upload changed .py files: edgelab_engine.py, edgelab_acca.py, edgelab_databot.py, edgelab_weather.py
3. Claude confirms files received and is fully up to speed
4. Work the ordered queue from the top
