# EdgeLab — Session Briefing Document
*Paste this at the start of any new Claude session to restore full project context.*
*Last updated: Session 7 — 30 March 2026*

---

## What EdgeLab Is

A multi-layer football prediction engine designed to go beyond standard statistics.
The core insight: **uncertainty itself is information** — detecting when a match is
unpredictable and using that to make smarter calls, particularly on upsets and draws.

**Owner:** Andrew Marrow
**Current status:** Engine built and validated. Upset layer added session 7 — confirmed
real signal across all tiers. Live prediction logging starting this week (English leagues,
post-international break). Draw intelligence active on E0+E1. E2/E3/EC draw weights at 0
(no signal found at those tiers).
**Market baseline:** ~49% (E0). EdgeLab E0 currently at **51.1%** on 7,140 matches.

---

## Owner Context

- Andrew has ADHD (inattentive) — one thing at a time, clear outputs, no waffle
- Works on phone only currently (Windows laptop too slow, saving for replacement)
- Pattern recognition is a strength — spots signals quickly, generates ideas fast
- Approach: intuition for signal discovery, DPOL for rigorous validation
- Not expecting every feature to work — builds iteratively, keeps what sticks
- Previous AI (ChatGPT) fabricated results. All metrics here are real and verified.

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
  |-- Draw Intelligence Layer [E0+E1 active, E2/E3/EC weights=0 no signal]
  |     |-- odds_draw_prob  (B365D -> fair implied draw probability)
  |     |-- home/away_draw_rate  (rolling team draw tendency)
  |     |-- h2h_draw_rate  (H2H draw history, sparse-data prior)
  |-- Score Prediction Layer [built, all weights=0 rejected by DPOL]
  |     |-- pred_home_goals / pred_away_goals (rolling goals scored/conceded)
  |     |-- pred_scoreline  (display string e.g. "2-1")
  |     |-- pred_margin     (signed float — signal for H/A reinforcement)
  |     |-- btts_prob / btts_flag (both-teams-to-score estimate)
  |-- Upset Layer [SESSION 7 — built, validated, Stage 1 flag-only]
  |     |-- sig_tension     (DTI × confidence — engine certain but match volatile)
  |     |-- sig_odds_gap    (engine confidence vs market implied prob for same outcome)
  |     |-- sig_h2h_upset   (H2H edge contradicts engine prediction direction)
  |     |-- upset_score     (weighted sum 0.0–1.0)
  |     |-- upset_flag      (1 if upset_score >= 0.60 and prediction is H/A)
        |
Prediction Engine (score differential -> H/D/A)
  |-- draw_margin
  |-- coin_dti_thresh
  |-- draw_score_thresh
  |-- w_score_margin (0 — rejected)
  |-- w_btts (0 — rejected)
        |
DPOL (Dynamic Pattern Override Layer)
  |-- Tests param candidates on rolling window
  |-- Global accuracy guard (rejects anything that hurts full-dataset accuracy)
  |-- min_improvement threshold (0.1%)
  |-- Auto-saves best params per tier to edgelab_params.json
        |
Output: H/D/A + confidence + DTI + chaos tier + draw score + scoreline + btts
        + upset_score + upset_flag
```

---

## Upset Layer — Design Notes

### Stage 1 (current): Flag only
upset_score computed every match. If >= 0.60 and prediction is H/A → upset_flag = 1.
Prediction does NOT change. Purpose: accumulate a live track record.

### Stage 2 (future, when validated on live data):
DPOL gets `upset_flip_thresh`. If upset_score exceeds it, prediction flips.
Earns the right to flip by proving predictive power on logged live predictions first.

### V1 signals (internal only — current data sources):
| Signal | Weight | Description |
|--------|--------|-------------|
| sig_tension | 0.45 | DTI × confidence. High DTI + high confidence = engine over-certain on volatile match |
| sig_odds_gap | 0.35 | Engine confidence minus market implied prob for predicted outcome. Market pricing in risk engine can't see |
| sig_h2h_upset | 0.20 | H2H edge contradicts prediction direction. Magnitude = historical gap size |

### External signal hooks (designed in, not yet built):
These are commented in `compute_upset_score()` ready to plug in:
- `rest_days_gap` — one team significantly less rested (fixture congestion)
- `travel_load` — midweek away Europa/Conference before this fixture
- `injury_index` — key player absence (API-Football ~2018+)
- `motivation_index` — season context: already safe/relegated/nothing to play for
- `weather_factor` — heavy conditions compress results, favour underdogs

### Validated results (historical — all 5 tiers):
| Tier | Flagged | Flag% | Flag Wrong | Unflag Wrong | Uplift |
|------|---------|-------|------------|--------------|--------|
| E0 | 293 | 4.1% | 65.2% | 47.7% | **+17.5%** |
| E1 | 402 | 4.2% | 65.7% | 55.0% | **+10.7%** |
| E2 | 338 | 6.1% | 63.3% | 53.9% | **+9.4%** |
| E3 | 169 | 3.0% | 60.4% | 58.0% | +2.4% |
| EC | 140 | 4.1% | 60.0% | 55.4% | +4.6% |

E3/EC uplift weaker — thinner H2H histories and noisier odds at those tiers. Expected.

---

## Live Prediction Logging

### Starting: week of 31 March 2026 (post-international break)
English league games this week. International break = no club football Tue/Wed.

### International break note (important for results interpretation):
Matches played immediately after an international break carry elevated upset risk:
- Players returning from different training environments, travel, time zones
- Squad disruption — some players not released, others return injured
- Form continuity broken — rolling form window reflects pre-break form
  which may not reflect current team state
- The engine does NOT currently model international break disruption
- Until this is built in, treat post-break predictions with added caution,
  especially for teams with many international players (top E0 clubs most affected)
- This is a future external signal hook candidate: `intl_break_flag`

### Live prediction workflow (manual, pre-DataBot):
1. Download latest season CSV from football-data.co.uk (updates weekly with results)
2. Drop into data folder, run engine
3. Log predictions for upcoming fixtures BEFORE matches are played
4. Mark actual results after
5. Track: overall accuracy, draw accuracy, upset flag hit rate

### What to log per prediction:
- Date, HomeTeam, AwayTeam, Tier
- Prediction (H/D/A), Confidence, DTI, Chaos tier
- Draw score, Mkt D%, H2H D%
- Upset flag (0/1), Upset score
- Actual result (fill in after)
- Notes (e.g. "post-international break", "known injury", "dead rubber")

---

## Scalability Architecture (design target)

Current: raw CSVs -> full recompute every run. Fine for development.
Future target:

```
Raw CSVs / API feed
        |
Pre-processor (runs once, or on new data only)
        |
edgelab.db (SQLite)
        |
Engine reads pre-computed features
        |
DPOL / Instinct layer
```

edgelab_params.json schema is SQLite-forward.

**Dataset hash safeguard (session 7):** config stores a fingerprint of the CSV data.
If data changes (new seasons added), hash changes, runner warns you that re-evolution
is recommended. Prevents silent use of stale params on expanded dataset.

---

## Files

| File | Status | Notes |
|------|--------|-------|
| edgelab_engine.py | Final | Upset layer added. B365H/B365A bug fixed. h2h_home_edge formula fixed. |
| edgelab_dpol.py | Final | Unchanged session 7. |
| edgelab_runner.py | Final | Dataset hash check on startup, hash save after run. |
| edgelab_config.py | Final | Hash safeguard functions added. show_config displays hash. |
| edgelab_params.json | Final | All tiers updated. Dataset hash stored. |
| edgelab_gridsearch.py | Final | Fast grid search alternative to DPOL (for when DPOL too slow). |
| edgelab_databot.py | Exists | Pulls live fixtures from API-Football. Needs API key resubscribed. |

**Upload at start of every session:** all 6 files above + edgelab_data.zip

---

## Data Sources

| Source | Cost | Notes |
|--------|------|-------|
| football-data.co.uk | Free | Historical CSVs. E0 back to 1993/94. Primary source. |
| api-sports.io | Paid | Live fixtures via DataBot. Needs API key to resubscribe. |

More E0 data needed: football-data.co.uk has E0 back to 1993/94.
More seasons = deeper H2H = stronger upset + draw signals.
**Priority: download more E0 seasons before next evolution run.**

Skipped files (encoding issues): Conf1617, Conf1819, Conf2021, Conf2122, League21718.

---

## Current Evolved Params

### E0 — Session 6 (DPOL)

| Param | Value |
|-------|-------|
| w_form | 0.873 |
| w_gd | 0.356 |
| home_adv | 0.299 |
| dti_edge_scale | 0.400 |
| dti_ha_scale | 0.550 |
| draw_margin | 0.120 |
| coin_dti_thresh | 0.690 |
| w_draw_odds | **0.100** |
| w_h2h_draw | **0.100** |
| draw_score_thresh | **0.450** |
| w_draw_tendency | 0.000 |
| w_score_margin | 0.000 |
| w_btts | 0.000 |

### E1 — Session 7 (grid search)

| Param | Value |
|-------|-------|
| w_form | 0.669 |
| w_gd | 0.452 |
| home_adv | 0.436 |
| dti_edge_scale | 0.360 |
| dti_ha_scale | 0.441 |
| draw_margin | 0.145 |
| coin_dti_thresh | 0.650 |
| w_draw_odds | **0.050** |
| w_h2h_draw | **0.050** |
| draw_score_thresh | **0.500** |
| w_draw_tendency | 0.000 |
| w_score_margin | 0.000 |
| w_btts | 0.000 |

### E2/E3/EC — Session 5 params, draw weights confirmed 0 (session 7)

| Param | E2 | E3 | EC |
|-------|----|----|-----|
| w_form | 0.762 | 0.778 | 0.786 |
| w_gd | 0.410 | 0.363 | 0.392 |
| home_adv | 0.390 | 0.246 | 0.272 |
| draw_margin | 0.120 | 0.120 | 0.108 |
| coin_dti_thresh | 0.737 | 0.759 | 0.744 |
| w_draw_odds | 0.000 | 0.000 | 0.000 |
| w_h2h_draw | 0.000 | 0.000 | 0.000 |

---

## Evolution Results History

| Session | Tier | Matches | Accuracy | Notes |
|---------|------|---------|----------|-------|
| Session 4 | E0 | 3,220 | 50.6% | First proper run |
| Session 4 | E1 | 9,575 | 44.4% | |
| Session 4 | E2 | 5,008 | 45.3% | |
| Session 4 | E3 | 1,104 | 43.2% | Small sample |
| Session 4 | EC | 2,345 | 45.2% | |
| Session 5 | E0 | 7,140 | 50.6% | Validated on 2x data |
| Session 5 | E1 | 9,575 | 44.4% | |
| Session 5 | E2 | 5,560 | 45.4% | |
| Session 5 | E3 | 5,612 | 42.0% | |
| Session 5 | EC | 3,449 | 44.4% | |
| Session 6 | E0 | 7,140 | 51.0% | Draw intelligence activated +0.4% |
| **Session 7** | **E1** | **9,575** | **44.6%** | **Draw intelligence activated +0.2%** |
| Session 7 | E2 | 5,560 | 45.4% | No draw signal — unchanged |
| Session 7 | E3 | 5,612 | 42.0% | No draw signal — unchanged |
| Session 7 | EC | 3,449 | 44.4% | No draw signal — unchanged |

E0 at 51.1% is 2.1% above market baseline (~49%).

---

## Prediction Output Format

| # | Home | Away | Pred | Score | Conf | DTI | Chaos | Mkt D% | H2H D% | Upset | Actual |
|---|------|------|------|-------|------|-----|-------|--------|--------|-------|--------|
| 1 | Arsenal | Palace | H | 2-0 | 100% | 0.698 | MED | 21% | 50% | — | H |
| 2 | Wolves | Burnley | H | 1-1 | 9.5% | 0.822 | HIGH | 30% | 26% | — | A |
| 3 | Everton | Spurs | A | 1-2 | 39.8% | 0.836 | HIGH | 29% | 0% | ⚠ | A |

Upset flag (⚠): upset_score >= 0.60 on an H/A prediction. History shows these
predictions are wrong ~65% of the time. Treat flagged calls with significant caution.
Stage 2: when validated on live data, flagged predictions may flip to the other outcome.

---

## What Has Been Built (Chronological)

1. ChatGPT history audited — fabricated results discarded, rebuilt from scratch
2. Honest baseline established
3. Draw over-correction fixed
4. DPOL wired to engine via make_pred_fn() bridge
5. Global accuracy guard added to DPOL
6. Engine vectorised
7. Multi-division loader
8. Deep evolution run — 68 seasons, 31,336 matches, 5 divisions
9. coin_dti_thresh 0.85->0.767 confirmed optimal
10. df_features bug fixed
11. fast_pred_fn implemented
12. --tier expanded to all tiers
13. draw_pull + dti_draw_lock tested and disabled
14. edgelab_config.py built — params persist to JSON
15. Runner wired to auto-load/save params per tier
16. gd_gap normalisation bug fixed
17. Draws diagnosed as unpredictable from DTI/form alone
18. Full re-evolution — E0 50.6% on 7,140 matches
19. B365D odds loaded
20. Draw intelligence layer built and validated
21. DPOL candidate space extended for draw intelligence
22. Score prediction layer built (w=0 rejected)
23. E0 DPOL run — draw intelligence activated, 51.0%, draws 48->318
24. Dataset hash safeguard added to config + runner
25. E1-EC draw intelligence grid search — E1 activated (+0.2%), E2/E3/EC no signal
26. **B365H + B365A bug fixed in load_csv (were being dropped)**
27. **h2h_home_edge formula fixed (was computing near-zero for all matches)**
28. **Upset layer built: sig_tension + sig_odds_gap + sig_h2h_upset**
29. **Upset flag validated: flagged matches wrong 60-66% vs 48-58% unflagged (+2-18% uplift)**
30. **External signal hooks commented into compute_upset_score() ready for future data**

---

## Next Steps — In Priority Order

### Immediate (next session — session 8)
- **Set up private git repository** (GitHub or GitLab — free private repo)
  - Commit all current files with message "Session 7 baseline"
  - Commit each session going forward — timestamped, immutable development trail
  - Briefing doc goes in too — readable record of the project evolving over time
  - This is the proof of ownership trail. Do this before anything else next session.
- **Download more E0 seasons** (football-data.co.uk back to 1993/94) and re-run
  evolution — deeper H2H history will sharpen both draw intelligence and upset signals
- **Live predictions: English leagues this week** (post-international break)
  - Run engine on current week's E0/E1/E2/E3/EC fixtures
  - Log predictions before matches, mark results after
  - Note international break context on all predictions this round
- **Start live prediction log** — simple CSV or table tracking each prediction

### International break context
- Matches after international breaks carry extra upset risk not modelled by the engine
- Engine's form window reflects pre-break form which may be stale
- Top-flight clubs most affected (more internationals)
- Flag all this week's predictions manually as "post-international break"
- Future: add `intl_break_flag` as an external signal hook in upset layer

### Soon
- Re-run DPOL on E0 with expanded dataset (more seasons = better params)
- Re-run grid search on E1-EC with expanded dataset
- Upset layer: consider lowering flag threshold from 0.60 → 0.55 on E0 to catch more
  (currently 4.1% flagged — reasonable but could be wider net)
- Feedback loop — results in, accuracy tracked per week

### Later (Phase 2)
- Fixture congestion / rest days parameter (first external signal to build)
- Injury/absence data (~2018+ via API-Football)
- Weather parameter
- Season context / motivation index (dead rubbers, relegation battles)
- International break flag (automatic — derivable from fixture calendar)
- Pre-match risk score
- Full automation: DataBot -> Engine -> DPOL -> Output

### Web App / Front End
- Not building yet — engine still evolving
- When stable: self-contained mobile-friendly web app
- v1 scope: paste fixture list -> predictions table -> log results -> track accuracy
- Start accumulating public accuracy record now (even manually)

### Business Layer
- Tier 1 — H/D/A picks + public accuracy stats (free, trust builder)
- Tier 2 — DTI, confidence, volatility flags, draw intelligence scores
- Tier 3 — Upset alerts (premium — this is the differentiator)
- Accumulator product — high confidence + low DTI + no upset flag

---

## How to Run

```bash
# Baseline only
python edgelab_engine.py /path/to/csvs/

# Full DPOL evolution — all tiers
python edgelab_runner.py /path/to/csvs/ --tier all --boldness medium

# Single tier
python edgelab_runner.py /path/to/csvs/ --tier E1

# Fast grid search (draw intelligence weights — use when DPOL too slow)
python edgelab_gridsearch.py /path/to/csvs/

# Show saved params + dataset hash
python edgelab_config.py show
```

---

## How to Resume

1. Paste this entire document into a new Claude session
2. Upload: edgelab_engine.py, edgelab_dpol.py, edgelab_runner.py,
   edgelab_config.py, edgelab_params.json, edgelab_gridsearch.py + edgelab_data.zip
3. Claude will confirm files received and be fully up to speed
4. First jobs next session:
   a. Live predictions for this week's English fixtures (log before matches)
   b. Download more E0 historical seasons, re-run evolution
