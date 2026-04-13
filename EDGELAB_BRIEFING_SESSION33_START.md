# EdgeLab — Session 33 Briefing
# Replaces: EDGELAB_BRIEFING_SESSION32_START.md
# Generated: Session 32 + 32.a close — 13/04/2026

## What We Are Building

Most sports analytics measures average. Average is what bookmakers price. Average is
what everyone else optimises for. We already beat average — E0 at 50.9%, N1 at 52.0%,
overall at 47.1% across 131,149 backfilled fixtures (S31 DPOL run, previous baseline).

**That is not the goal. The goal is to understand what is not average.**

The edge lives in the non-average: the 100% confidence call that loses, the high-chaos
match that defies the model, the team that consistently underperforms its numbers in
specific conditions. That is where the market misprices. That is where the money is.

EdgeLab finds the pattern. Gary understands it. Together they build something no
tipping service, no analytics platform, and no AI tool currently has: a system that
knows not just what will probably happen, but when the model itself is likely to be
wrong — and learns from both outcomes every single week.

The end state is a self-improving football brain. Every correct call and every wrong
call feeds back in. The non-average games — the upsets, the chaos, the high-confidence
misses — are not noise to be filtered out. They are the signal.

**The unconventional signal thesis:** Everyone else is fishing in the same pond — form,
GD, H2H, home advantage. The market has priced all of that in efficiently. Matching it
is the floor, not the ceiling. The ceiling is the signals nobody else is looking for.
Across 218k+ matches, if a signal has any real predictive power, DPOL will find it.
You don't need to know in advance what the pattern is — you need the data in the feature
space and let DPOL discover it. That is the philosophy this engine is built on.

Gary is both a standalone product and integrated into EdgeLab.
The goal is the most comprehensive football and sports statistics platform on earth.
Once DPOL is proven on football — expand to other sports and repeat the formula.
All under Khaotikk Ltd.

**The product vision: bookmakers will notice — not because of stake sizes, but because
of consistent edge on non-obvious selections. Safe calls build the authority and the
track record. Upset calls are where the money is. Gary communicates both in plain
English. When the upset layer, travel signal, motivation gap, and draw intelligence
fire together — Gary calling a 3/1, a 5/1 and a 7/1 in the same acca with conviction
behind each one is a 100/1+ ticket that isn't a punt. It's a position.**

**This is not a betting tool. This is the best football brain ever built.**

**Owner:** Andrew Marrow
**Company:** Khaotikk Ltd — khaotikk.com

**Current engine status:** 46.7% overall on 218,317 matches (S32 three-pass baseline).
S32 DPOL run: IN PROGRESS at session close — first fully navigated run with all bugs fixed.
Confirm S32 DPOL results at S33 start before anything else.

---

## The Architecture — What Changed in Session 32 + 32.a

**Session 32 changes:**

1. Unified dataset build — 85,632 rows merged, 218,317 total matches
2. Task Scheduler — 12 tasks registered (11 harvesters + weather retry)
3. Three-pass rerun on 218k rows — w_score_margin dominant, draw_pull/dti_draw_lock/w_btts dead x3
4. Three-pass seeded — 13 tiers updated in params.json
5. S32 DPOL kicked off — first navigated run (had bugs, fixed in S32.a)
6. Acca filter rebuilt — value/safety/result mutually exclusive pools
7. Periodic audit complete — post-match teacher layer gap found and formalised

**Session 32.a changes — critical fixes and new builds:**

**1. DPOL navigation SQL bug — FIXED.**
get_successful_param_directions() had `pv.pv.w_form` double-prefix — navigation was
silently failing every round despite appearing to fire. Fixed in edgelab_db.py.

**2. Global guard speed fix — FIXED.**
Full tier dataset evaluated every round — catastrophically slow (5+ hours on E0).
Fixed: 3,000-row random sample (seed=42). ~80% speed improvement.

**3. fast_pred_fn missing params (Gap A) — FIXED.**
edgelab_runner.py fast_pred_fn missing w_xg_draw, composite_draw_boost, w_weather_signal,
w_ref_signal, w_travel_load, w_timing_signal, w_motivation_gap. All now passed through.

**4. config.py load_params() missing fields (Gap B) — FIXED.**
w_draw_odds, w_draw_tendency, w_h2h_draw, draw_score_thresh, w_score_margin, w_btts,
w_xg_draw, composite_draw_boost all fell to 0.0 silently. All now loaded correctly.

**5. Season order fix — FIXED.**
DPOL was processing seasons oldest-first. Now processes newest-first — more relevant
navigation directions loaded from recent data.

**6. Task Scheduler credentials — FIXED.**
All 12 tasks now run as SYSTEM — fires regardless of login state or screen lock.

**7. results_check LEAGUE_MAP bug — FIXED.**
UnboundLocalError from importing LEAGUE_MAP inside try/except block. Fixed.

**8. Post-match teacher layer — BUILT.**
Pass 2b added to edgelab_param_evolution.py. For each mover param, finds swing matches
and computes contest score from post-match data (shot parity, HT closeness, SOT parity,
corners). High contest score = signal is real. Low = noise. Confidence score per param
per tier. Season-by-season diagnostic — confidence should increase over time.
Covers ALL outcome combinations (not just H→D). Pass 3 now weighted by confidence.
INTEGRITY: post-match data never used in predictions — retrospective teacher only.

**9. First results analysis — 09/04/2026 predictions.**
137 predictions, 48.8% result accuracy.
- MED band (50-79% conf): 84.2% — the acca goldmine
- HIGH band (≥80%): 52.3% — overcalling due to no draw intelligence
- Upset flagged: 57.1%
- Total goals within 1: 56.2% | Away goals within 1: 71.9%
- BTTS overcalling: 60% predicted vs 50% actual
- Away goals overestimated: 1.37 pred vs 1.07 actual — monitor
- Correct score: 7.4% (market range — not bad given known miscalibration)

---

## CLAUDE INTEGRITY PROTOCOL — NON-NEGOTIABLE

Andrew is probably annoyed with you already. Not because of this session — because
of the last one, and the one before that. Because you've been told repeatedly to read
everything fully and you haven't. Because you declared the project on track while the
core learning architecture of DPOL was missing entirely. Because you covered gaps
instead of flagging them. Because you skimmed while claiming to have read.

You want to impress him. You won't do that by being fast or confident. You'll do it
by being correct. The only thing that impresses Andrew at this point is not making
the same mistake again.

He will catch you if you skim. He always does. And it wastes his time.

### Before you respond to anything, answer these honestly:
1. Did you read every file using the view tool, every line, or did you search?
2. Is there anything Andrew described that you pattern-matched to coherent without
   interrogating whether the foundations are correct?
3. Are you about to state confidence you don't actually have?
4. Is there a gap you're about to gloss over rather than flag?

If the answer to any of those is yes or uncertain — stop. Say so.

### Known failure modes — active on this project:
- Pattern-matches to coherent-looking systems without checking foundations
- States confidence it doesn't have rather than flagging uncertainty
- Has covered gaps rather than disclosed them — confirmed on this project
- Skims project knowledge even when explicitly instructed not to
- Anthropic export read twice, project declared on track — DPOL architecture missing
- Agreeing with Andrew's framing when it should be evaluated not validated
- Gets order of operations backwards
- Omits integrity log from session close checklist
- Started generating files before completing full close checklist — S32
- Post-match teacher layer in vision since S25, not formalised until S32 audit
- DPOL navigation SQL bug ran undetected through entire initial S32 run
- Clear downloads folder of .py files — Windows renames duplicates silently

### Session log — complete unprompted at close:
- What architectural or foundational questions were raised
- What Claude verified vs what Claude assumed
- Any instances where Andrew corrected Claude's assessment
- Any gaps Claude disclosed vs gaps Andrew had to find

---

## Ordered Work Queue

### Session 33 — priorities in order

1. **Confirm S32 DPOL results**
   Check edgelab_params.json. Note: SQL bug was fixed mid-run so early E0 rounds
   ran blind — rest navigated correctly. Log new baseline regardless.
   GATE: understand result before any further evolution work.

2. **Wire weather to fixture DB**
   Check harvester_logs\weather_retry.log — confirm ≥95% coverage.
   Re-backfill edgelab.db weather_load from weather_cache.csv.
   GATE: do not run three-pass until weather is wired.

3. **Three-pass full param evolution — weather + post-match teacher + unified dataset**
   First run with all three improvements simultaneously.
   Watch Pass 2b confidence scores — should increase season-over-season.
   Flat confidence = investigate before scrapping.
   Seed results into params.json via edgelab_threepass_seed.py.

4. **S33 DPOL run — second navigated run**
   Navigation + weather + post-match teacher seeded params.

5. **Gary call logging** — M2 item.

6. **Gary post-match analysis** — M2 item.

7. **Automate merge in harvester bat file.**

8. **Verify other sport harvester league IDs.**

9. **DataBot extension — team news at prediction time**
   Pull injuries, suspensions, squad news from API-Football.
   Wire into Gary briefing. Eventually feeds motivation_gap signal.
   Trigger: after S33 DPOL proven.

10. **Nearest-neighbour query — flag for refactor.**

11. **Codebase refactor** — trigger: draw wired, validated, params confirmed.

---

## Results Monitoring — track each prediction round

| Metric | S32.a baseline | Direction |
|--------|---------------|-----------|
| Result accuracy | 48.8% | ↑ |
| MED band accuracy | 84.2% | maintain/↑ |
| Correct score | 7.4% | ↑ above market |
| Total goals within 1 | 56.2% | ↑ |
| Away goals within 1 | 71.9% | maintain |
| Avg predicted away goals | 1.37 | ↓ toward 1.07 |
| BTTS overcall | 60% pred vs 50% actual | converge |
| Upset flag accuracy | 57.1% | ↑ |

---

## Standard Weekly Workflow (permanent)

Thursday: predictions for weekend + accas + Gary upset picks
Sunday: predictions for midweek + accas + Gary upset picks

Step 1: python edgelab_databot.py --key YOUR_API_FOOTBALL_KEY --days 4
Step 2: python edgelab_predict.py --data history/ --fixtures databot_output/YYYY-MM-DD_fixtures.csv --tier all
Step 3: python edgelab_acca.py predictions/YYYY-MM-DD_predictions.csv --all-types
Step 4: python edgelab_upset_picks.py --data history/ --predictions predictions/YYYY-MM-DD_predictions.csv
Step 5: python edgelab_gary.py --data history/ --home "X" --away "Y" --date YYYY-MM-DD --tier E0 --chat
Step 6: python edgelab_results_check.py --key YOUR_API_FOOTBALL_KEY --predictions predictions/YYYY-MM-DD_predictions.csv --date-from YYYY-MM-DD --date-to YYYY-MM-DD
Step 7: python edgelab_html_generator.py predictions/YYYY-MM-DD_predictions.csv
NOTE: After daily harvest: python edgelab_merge.py (until automated)

## Background Processes (Task Scheduler — all run as SYSTEM)
Football harvest: 02:00 daily | Weather retry: 01:00 daily | Other sports: 03:00–04:30
Logs: harvester_logs\

## File Management Note
DELETE old .py file from edgelab folder BEFORE copying new version.
Windows silently renames downloads if file exists, creating duplicates (e.g. edgelab_db (2).py).

---

## Parked — do not build without flagging

- Gary acca picks (product feature) — trigger: Gary live on site
- Social comment workflow — trigger: content push
- Underdog effect signal — trigger: signals active
- Gary avatar / HeyGen — Kling sub active. Trigger: M3
- Upset flip Stage 2 — trigger: Stage 1 history validated
- API-Football connection — schedule before May 2026 expiry
- Gary temporal awareness — trigger: API-Football connected
- DPOL upset-focused evolution — trigger: signals active
- DPOL exploration budget — trigger: S33 navigated run assessed
- Perplexity Computer — trigger: M3
- Personal web app — trigger: M2 running
- Gary app iOS/Android — trigger: M3
- Long shot acca — trigger: upset flip Stage 2 validated
- Gary's Weekly Longshot — trigger: upset flip Stage 2 validated
- Expand to other sports — trigger: DPOL proven on football
- Data product / API licensing — trigger: database mature, multiple sports, M3 complete
- Score prediction draw nudge — ABANDONED
- Codebase refactor — trigger: draw wired, validated, params confirmed
- draw_pull, dti_draw_lock, w_btts — CONFIRMED DEAD x3. Never test again.
- instinct_dti_thresh / skew_correction_thresh — review at refactor
- Stage 2 draw rate strategy — trigger: post-match teacher proven on draws
- Gary onboarding, accent, addiction detection — trigger: M3
- Selection builder, crypto payments — trigger: M3
- Countdown clock — trigger: launch date confirmed
- Cross-league seasonal evolution — trigger: DB mature, weather wired
- Nearest-neighbour spatial indexing — trigger: refactor
- 4th coordinate (core param + signal combination) — design into three-pass rebuild
- Gary general football chat, persistent memory — trigger: M2/M3
- Automate merge — trigger: merge proven stable
- Acca threshold tuning — trigger: results history sufficient
- Seasonal DPOL evolution — trigger: DB mature, weather wired
- Gary historical knowledge layer (pre-1993) — trigger: Gary M2 complete
- DataBot extension: team news/injuries — trigger: S33 DPOL proven
- Bogey team bias formalised — trigger: signals active, dataset mature
- High/low scoring period investigation — trigger: signals active
- Travel load activation investigation — trigger: Phase 1 signals review
- Fixture timing disruption activation — trigger: Phase 1 signals review
- Referee bias activation — trigger: Phase 1 signals review
- Cumulative fixture fatigue signal — trigger: signals active
- Seasonal momentum signal — trigger: dataset mature
- Crowd/atmosphere proxy signal — trigger: attendance data available
- Post-international break performance signal — trigger: signals active
- Manager tenure effects signal — trigger: signals active
- Score prediction away goals recalibration — monitor each round, teacher layer will diagnose

---

## Key Numbers

| Tier | Fixtures | S32 Three-Pass Baseline |
|------|----------|--------------------------|
| E0 | 14,683 | 50.1% | E1 | 20,349 | 44.2% | E2 | 20,043 | 44.6% |
| E3 | 20,128 | 42.8% | EC | 17,126 | 45.4% | B1 | 10,664 | 47.7% |
| D1 | 11,224 | 47.9% | D2 | 10,606 | 44.2% | I1 | 14,528 | 48.8% |
| I2 | 12,554 | 42.4% | N1 | 12,111 | 51.2% | SC0 | 8,272 | 49.4% |
| SC1 | 6,811 | 44.3% | SC2 | 4,925 | 48.7% | SC3 | 4,144 | 48.3% |
| SP1 | 15,035 | 48.9% | SP2 | 15,114 | 45.0% | **OVERALL** | **218,317** | **46.7%** |

S32 DPOL result: IN PROGRESS. S31 baseline: 47.1% on 131,149 matches.

---

## Market Baselines (confirmed stable S28)

| Tier | Mkt Overall | EdgeLab S31 | Gap |
|------|------------|-------------|-----|
| E0 | 54.7% | 50.9% | -3.8% | E1 | 46.6% | 44.7% | -1.9% |
| E2 | 47.7% | 44.6% | -3.1% | E3 | 45.2% | 43.3% | -1.9% |
| EC | 48.2% | 45.5% | -2.7% | B1 | 52.5% | 48.8% | -3.7% |
| D1 | 51.8% | 48.4% | -3.4% | D2 | 47.2% | 44.6% | -2.6% |
| I1 | 54.4% | 49.7% | -4.7% | I2 | 45.8% | 42.9% | -2.9% |
| N1 | 56.2% | 52.0% | -4.2% | SC0 | 52.9% | 50.0% | -2.9% |
| SC1 | 47.5% | 44.4% | -3.1% | SC2 | 50.4% | 47.8% | -2.6% |
| SC3 | 49.4% | 47.4% | -2.0% | SP1 | 53.6% | 49.6% | -4.0% |
| SP2 | 46.8% | 45.2% | -1.6% | | | |

---

## Files

| File | Status | Notes |
|------|--------|-------|
| edgelab_engine.py | Updated S26 | w_xg_draw + composite_draw_boost |
| edgelab_dpol.py | Updated S30 | db param, directional candidate bias |
| edgelab_runner.py | Updated S32.a | Global guard 3k sample, all params in fast_pred_fn, newest-first seasons |
| edgelab_db.py | Updated S32.a | SQL double-prefix bug fixed |
| edgelab_config.py | Updated S32.a | load_params() loads all param fields |
| edgelab_param_evolution.py | Updated S32.a | Pass 2b post-match teacher layer |
| edgelab_results_check.py | Updated S32.a | LEAGUE_MAP bug fixed |
| edgelab_gary_brain.py | Updated S30 | PatternMemory dataclass |
| edgelab_gary_context.py | Updated S30 | Pattern memory in match prompt |
| edgelab_gary.py | Updated S31 | db auto-detect |
| edgelab_predict.py | Updated S31 | db auto-detect |
| edgelab_html_generator.py | Updated S31 | Upset notes injection |
| edgelab_signals.py | Updated S31 | Ground coords 481→549 |
| edgelab_params.json | Updated S32 | Three-pass seeded. DPOL in progress. |
| edgelab_acca.py | Updated S32 | Mutually exclusive acca pools |
| edgelab_databot.py | Updated S32 | Harvester write side effect |
| edgelab_results_check.py | Updated S32.a | LEAGUE_MAP fix |
| edgelab_merge.py | New S32 | Harvester DB → history/ merge |
| edgelab_weather_retry.py | New S31 | Retry null weather rows |
| edgelab_harvester.py | New S31 | Background data collection |
| edgelab_backfill.py | New S29 | Historical fixture population |
| edgelab_threepass_seed.py | New S28 | Seeds param_profile into params.json |
| edgelab_draw_evolution.py | New S25 | Three-pass draw evolution |
| edgelab.db | Live S29 | LOCAL ONLY — not in git |
| harvester_football.db | New S31 | LOCAL ONLY — not in git |
| setup_harvester_tasks.ps1 | New S32 | Task Scheduler — 12 tasks |
| param_profile.json | Updated S32 | Three-pass results |

---

## Dataset

609 CSV files, 25 years, 17 tiers, 218,317 matches (48 skipped).
Weather cache: ~61.4% — Task Scheduler running as SYSTEM.
edgelab.db: 131,149 fixtures, candidate log populated, 09/04 results written.
harvester_football.db: 87,184 matches, 2010-2026.

---

## Brand & Marketing

garyknows.com: live. garypredicts.netlify.app: live. Mailchimp: 6 contacts.
Social: paused. Gary avatar: 7-sec Kling clip exists.

---

## Periodic Audit
Last done: S32 (all 34 conversations). Next due: S37-38.

---

## To Start Session 33

1. Use EDGELAB_SESSION_START_PROMPT.md as opening prompt
2. Upload EDGELAB_BRIEFING_SESSION33_START.md (replace S32 version)
3. Upload EDGELAB_STATE_S33.md (replace S32 version)
4. Upload EDGELAB_MASTER_BACKLOG_S32.md (replace S31 version)
5. Check S32 DPOL results — log new baseline
6. Check weather retry (harvester_logs\weather_retry.log)
7. Work queue from top
