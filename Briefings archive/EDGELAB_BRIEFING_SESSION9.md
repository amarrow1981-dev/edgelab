# EdgeLab — Session Briefing Document
*Paste this at the start of any new Claude session to restore full project context.*
*Last updated: Session 9 — 2 April 2026*

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

**Market baseline:** ~49% (E0). EdgeLab E0 currently at **49.8%** on 8,669 matches.
Note: previous 51.1% was on 7,140 matches. Larger dataset gives more honest baseline.

---

## Owner Context

- Andrew has ADHD (inattentive) — one thing at a time, clear outputs, no waffle
- Works on Windows laptop + VS Code + Claude Code extension
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
  |-- Draw Intelligence Layer [all weights=0 — no signal on full dataset]
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
DataBot (API-Football Pro — 7,500 calls/day)
  |-- Pulls upcoming fixtures for E0-EC
  |-- Pulls Bet365 odds per fixture
  |-- Outputs engine-ready CSV to databot_output/
        |
edgelab_predict.py
  |-- Loads historical CSVs for team form/GD/H2H context
  |-- Appends upcoming fixtures
  |-- Runs full feature pipeline
  |-- Outputs predictions table + acca candidates
  |-- Saves predictions CSV + PDF
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
| edgelab_databot.py | **NEW session 9** | Pulls fixtures + odds from API-Football |
| edgelab_predict.py | **NEW session 9** | Forward predictions on upcoming fixtures |

**Upload at start of every session:** all 8 files above + edgelab_data.zip

---

## API-Football (DataBot)

- **Account:** a.marrow1981@gmail.com
- **Plan:** Pro — 7,500 requests/day
- **Base URL:** v3.football.api-sports.io
- **Key:** stored locally — do not paste in chat unnecessarily

### Verified League IDs
| Tier | ID | League |
|------|----|--------|
| E0 | 39 | Premier League |
| E1 | 40 | Championship |
| E2 | 41 | League One |
| E3 | 42 | League Two |
| EC | **43** | National League — CONFIRMED via /leagues endpoint |

Note: ID 45 = FA Cup (not National League). ID 197 = Greek Super League. Always verify via /leagues endpoint if unsure.

### DataBot Usage
```bash
# Connection test (1 API call)
python edgelab_databot.py --key YOUR_KEY --test

# Fetch next 7 days fixtures + odds
python edgelab_databot.py --key YOUR_KEY --days 7

# Fetch without odds (faster, saves calls)
python edgelab_databot.py --key YOUR_KEY --days 7 --no-odds

# Specific date
python edgelab_databot.py --key YOUR_KEY --date 2026-04-05
```

Output: `databot_output/YYYY-MM-DD_fixtures.csv` + raw JSON

---

## Prediction Workflow (Session 9 — Operational)

```bash
# Step 1: Pull fixtures and odds (run Mon/Tue, re-run Wed/Thu when odds priced)
python edgelab_databot.py --key YOUR_KEY --days 7

# Step 2: Generate predictions
python edgelab_predict.py --data history/ --fixtures databot_output/YYYY-MM-DD_fixtures.csv

# Output: predictions/YYYY-MM-DD_predictions.csv
# PDF generated separately if needed
```

**Important:** Odds are often not priced until 2-3 days before the match.
Re-run DataBot mid-week to get real odds — draw intelligence fires properly then.

---

## Current Evolved Params (Session 9 — Expanded Dataset)

All tiers re-evolved on 53,668 matches across 106 files.
Draw intelligence weights all at 0 — no signal found on full dataset.

### E0 — Premier League
| Param | Value |
|-------|-------|
| w_form | 0.786 |
| w_gd | 0.354 |
| home_adv | 0.330 |
| dti_edge_scale | 0.400 |
| dti_ha_scale | 0.550 |
| draw_margin | 0.120 |
| coin_dti_thresh | 0.688 |
| w_draw_odds | 0.000 |
| w_h2h_draw | 0.000 |

### E1 — Championship
| Param | Value |
|-------|-------|
| w_form | 0.560 |
| w_gd | 0.362 |
| home_adv | 0.505 |
| draw_margin | 0.145 |
| coin_dti_thresh | 0.677 |

### E2 — League One
| Param | Value |
|-------|-------|
| w_form | 0.895 |
| w_gd | 0.489 |
| home_adv | 0.468 |
| draw_margin | 0.120 |
| coin_dti_thresh | 0.719 |

### E3 — League Two
| Param | Value |
|-------|-------|
| w_form | 0.503 |
| w_gd | 0.306 |
| home_adv | 0.199 |
| draw_margin | 0.120 |
| coin_dti_thresh | 0.726 |

### EC — National League
| Param | Value |
|-------|-------|
| w_form | 0.700 |
| w_gd | 0.316 |
| home_adv | 0.258 |
| draw_margin | 0.108 |
| coin_dti_thresh | 0.703 |

---

## Evolution Results History

| Session | Tier | Matches | Accuracy | Notes |
|---------|------|---------|----------|-------|
| Session 4 | E0 | 3,220 | 50.6% | First proper run |
| Session 5 | E0 | 7,140 | 50.6% | Validated on 2x data |
| Session 6 | E0 | 7,140 | 51.0% | Draw intelligence activated |
| Session 7 | E0 | 7,140 | 51.1% | B365H/A bug fixed |
| Session 7 | E1 | 9,575 | 44.6% | Draw intelligence +0.2% |
| Session 7 | E2-EC | varies | 42-45% | No draw signal |
| **Session 9** | **E0** | **8,669** | **49.8%** | **Expanded dataset, draw intel no signal** |
| **Session 9** | **E1** | **12,059** | **44.3%** | **Expanded dataset** |
| **Session 9** | **E2** | **11,906** | **44.4%** | **Expanded dataset** |
| **Session 9** | **E3** | **11,954** | **42.2%** | **Expanded dataset** |
| **Session 9** | **EC** | **9,080** | **44.8%** | **Expanded dataset, most improvement** |

**Note on E0 accuracy:** 49.8% on 8,669 matches is more honest than 51.1% on 7,140.
Larger dataset = less overfitting. Still above market baseline (~49%).
Draw intelligence previously showed +0.4% on smaller data — did not survive expansion.
This means current draw signals (odds implied prob + H2H rate) are not robust enough alone.
Better draw signals needed — live odds from DataBot may help as live data accumulates.

---

## Draw Intelligence — Current Status

Previous small-dataset signal did not survive expanded validation. All draw weights = 0.

**Why this matters:** The engine needs better draw signals. Candidates:
- Live pre-match odds (DataBot now provides these — need to accumulate)
- Team draw tendency over longer windows
- Referee draw tendency (future signal)
- Match importance / dead rubber context (future signal)

**Do not re-enable draw weights until a new signal source is validated.**

---

## Upset Layer — Design Notes

### Stage 1 (current): Flag only
upset_score computed every match. If >= 0.60 and prediction is H/A → upset_flag = 1.
Prediction does NOT change. Purpose: accumulate live track record.

### Validated results (historical — session 7):
| Tier | Flagged | Flag% | Flag Wrong | Unflag Wrong | Uplift |
|------|---------|-------|------------|--------------|--------|
| E0 | 293 | 4.1% | 65.2% | 47.7% | **+17.5%** |
| E1 | 402 | 4.2% | 65.7% | 55.0% | **+10.7%** |
| E2 | 338 | 6.1% | 63.3% | 53.9% | **+9.4%** |
| E3 | 169 | 3.0% | 60.4% | 58.0% | +2.4% |
| EC | 140 | 4.1% | 60.0% | 55.4% | +4.6% |

### External signal hooks (designed in, not yet built):
- `rest_days_gap` — fixture congestion
- `injury_index` — key player absence (API-Football ~2018+)
- `motivation_index` — dead rubbers, relegation battles
- `weather_factor` — heavy conditions favour underdogs
- `intl_break_flag` — post-international break elevated upset risk

---

## Live Prediction Logging

### Started: week of 2 April 2026
First live predictions generated session 9 — 94 matches across E1/E2/E3/EC.
E0 blank this week (international break — no Premier League fixtures).

### Weekly workflow:
1. Monday: `edgelab_databot.py --days 7` — pull fixtures
2. Tuesday/Wednesday: re-run DataBot when odds are priced
3. `edgelab_predict.py` — generate predictions
4. Log before matches, mark results after
5. Track: overall accuracy, upset flag hit rate, acca performance

### What to log per prediction:
- Date, HomeTeam, AwayTeam, Tier
- Prediction, Confidence, DTI, Chaos tier
- Draw score, Mkt D%, H2H D%
- Upset flag, Upset score
- Actual result (fill in after)
- Notes (post-break, injury, dead rubber etc.)

---

## Acca Selection Criteria (Current)

Filter: confidence >= 50%, chaos tier LOW or MED, upset_flag = 0, prediction H or A only.
Sort by confidence descending. Pick top 3 for 3-leg acca.

Session 9 produced 35 acca candidates meeting criteria across E1/E2/E3/EC.

---

## Skipped/Problem Files (Known)

14 files consistently skipped due to encoding or format issues:
- E0 (21).csv, E0 (22).csv — encoding/column issues
- E1 (20).csv, E1 (22).csv — encoding/column issues  
- E2 (21).csv — encoding issue
- (9 others)

These are older historical files with non-standard formats. Not worth fixing now —
106 files loaded successfully covering 53,668 matches. Sufficient for evolution.
Future: build a pre-processor to normalise older formats.

---

## Scalability Architecture (design target)

```
Raw CSVs / API feed (DataBot)
        |
Pre-processor
        |
edgelab.db (SQLite — not yet built)
        |
Engine reads pre-computed features
        |
DPOL / Pattern memory layer (future)
```

edgelab_params.json schema is SQLite-forward.

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
9. coin_dti_thresh optimised
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
23. E0 DPOL run — draw intelligence activated, 51.0%
24. Dataset hash safeguard added
25. E1-EC draw intelligence grid search — E1 +0.2%, E2/E3/EC no signal
26. B365H + B365A bug fixed
27. h2h_home_edge formula fixed
28. Upset layer built and validated
29. Git repository set up (private)
30. Windows laptop acquired — development moves off phone
31. VS Code + Claude Code extension set up
32. **DataBot built — API-Football Pro connected, fixtures + odds pulling live**
33. **edgelab_predict.py built — forward prediction on upcoming fixtures**
34. **EC league ID confirmed — ID 43 (was pulling FA Cup ID 45 / Greek league ID 197)**
35. **Full prediction workflow operational — 94 predictions generated session 9**
36. **Expanded dataset evolution — 53,668 matches across 106 files**
37. **Draw intelligence retested on full dataset — no signal, weights reset to 0**
38. **PDF prediction output built**
39. **gridsearch.py KeyError fix — skips _dataset metadata key**

---

## Next Steps — In Priority Order

### Immediate (session 10)
- **Review this week's results** — mark actual outcomes on session 9 predictions
- **Re-run DataBot mid-week** when odds are priced for better draw intelligence
- **Re-run predictions** with real odds — draw layer may find signal on live data
- **Build result logging script** — automate marking actual results on predictions CSV

### Soon
- **Expand gridsearch** — try wider odds/H2H weight ranges for draw intelligence
- **Investigate draw signal further** — team draw tendency over longer windows?
- **Fix skipped files** — pre-processor to normalise older CSV formats (more E0 data)
- **Upset layer live validation** — track flagged vs unflagged accuracy on live predictions

### Medium term
- **SQLite database layer** — stop reprocessing everything from scratch each run
- **Pattern memory layer** — DPOL logs what conditions preceded upsets, builds profile
- **Scheduled automation** — Windows Task Scheduler runs DataBot + predict weekly
- **Result auto-fetcher** — DataBot pulls results for logged predictions automatically

### Later (Phase 2)
- **Injury data** (~2018+ via API-Football)
- **Rest days / fixture congestion** parameter
- **Season context / motivation index** (dead rubbers, relegation battles)
- **International break flag** (automatic from fixture calendar)
- **Claude API integration** — natural language prediction summaries
- **Web app / front end** — mobile-friendly predictions interface

### Business Layer (when validated)
- Tier 1 — H/D/A picks + public accuracy stats (free, trust builder)
- Tier 2 — DTI, confidence, volatility flags, draw intelligence scores
- Tier 3 — Upset alerts (premium — this is the differentiator)
- Accumulator product — high confidence + low DTI + no upset flag
- Charity betting pot — validated picks, winnings to gambling harm charities
- Marketed as analysis tool, not gambling advice

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

# Draw intelligence grid search (E1-EC)
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
   a. Review this week's results — mark actuals on predictions CSV
   b. Re-run DataBot with odds (mid-week) and regenerate predictions
   c. Discuss next signal to investigate for draw intelligence
