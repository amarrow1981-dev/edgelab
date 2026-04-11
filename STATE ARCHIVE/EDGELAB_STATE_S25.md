# EDGELAB — Claude State File S25
# For Claude's use at session start. Read alongside briefing doc and master backlog.
# Generated: Session 24 close — 09/04/2026

## LAST SESSION ENDED
Session 24. Long productive session. DPOL weighted loss run confirmed complete.
Draw gridsearch run — no breakthrough via standard method. Signals-only DPOL run
complete — all signals dormant. Weekly predictions done (139 matches, 10-12 Apr).
Score prediction v2 built and deployed (venue-split + H2H blend).
Major draw signal discovery: score prediction produces 26.6% draw-score rate
matching real-world draw frequency, independent of DTI.
Market baselines established all 17 tiers. H/A breakdown analysis done.
Bug fixes in Gary files. New acca type (winner_btts). New analysis scripts.

## SESSION START HANDSHAKE — SAY THIS FIRST
"Last session ended with the draw signal discovery — the score prediction
independently finds ~26.6% draw rate matching real world, independent of DTI.
Queue item 1 is to validate whether those draw-score matches actually correlate
with real draws historically. Do you want to start there, or is there anything
urgent first?"

## CURRENT STATUS

### Draw Signal
STATUS: VALIDATED — NO SIGNAL. CLOSED.
- Validation run: 132,685 matches, all 17 tiers
- Lift: +1.1% (1.011x), p=0.1876 — not statistically significant
- 0 tiers showed >= 1.10x lift. 7 tiers showed negative lift.
- The 26.6% draw-score rate is a mathematical property of Poisson, not a predictor.
- SCORE_DRAW_NUDGE removed from edgelab_engine.py S25.
- Draw intelligence path remains: DPOL activation via existing draw signals.

### Score Prediction
STATUS: v2 DEPLOYED S24
- Venue-split goal tracking + 25% H2H blend
- Eliminates majority of result/scoreline contradictions
- Full DPOL re-run needed to revalidate params against new engine

### DPOL
STATUS: WEIGHTED LOSS RUN COMPLETE
- All 17 tiers: 46.2% overall (+0.8%)
- Signals dormant on all 17 tiers
- Draw intelligence dormant on all 17 tiers
- Draw activation via weighted loss: not working at 1.5x penalty
- New path: score prediction draw signal (see above)

### Weather Cache
STATUS: RUNNING — 82,000/132,685 rows at S24 close
- Check row count S25
- Do not wire to DPOL until 132,685 rows complete

### Website / Email
STATUS: FULLY WORKING
- khaotikk.com Mailchimp auth: unconfirmed — check S25

### Predictions
STATUS: WEEKEND RUN COMPLETE (10-12 Apr 2026)
- 139 predictions done. 4 upset flags. Gary analysis on all 4.
- Internal + public HTML produced and delivered.
- Sunday run (midweek fixtures) due S25

## S25 QUEUE — IN ORDER

1. ~~Draw signal validation~~ — COMPLETE. NO SIGNAL. p=0.1876, lift +1.1% across 132,685 matches. SCORE_DRAW_NUDGE removed from edgelab_engine.py. pred_score_draw is a Poisson property, not a predictor.
2. Full DPOL re-run (score prediction v2 changed the engine)
3. **Public HTML — qualifying picks tab fix** — tab renders but pane content not showing. Div closure issue. Needs clean rebuild of tab structure.
4. Sunday predictions — midweek fixtures
5. Check weather cache row count
6. Confirm khaotikk.com Mailchimp auth
7. Clarify instinct_dti_thresh / skew_correction_thresh
8. E1 home bias investigation

## STANDARD WEEKLY WORKFLOW (permanent)
- Thursday: predictions for weekend fixtures + accas + Gary upset picks
- Sunday: predictions for midweek fixtures + accas + Gary upset picks
- Results check after each fixture set completes

## WEEKLY PREDICTION COMMANDS (exact — commit to memory)
Step 1: python edgelab_databot.py --key YOUR_API_FOOTBALL_KEY --days 4
Step 2: python edgelab_predict.py --data history/ --fixtures databot_output/YYYY-MM-DD_fixtures.csv --tier all
Step 3: python edgelab_acca.py predictions/YYYY-MM-DD_predictions.csv --all-types
Step 4: python edgelab_upset_picks.py --data history/ --predictions predictions/YYYY-MM-DD_predictions.csv
Step 5: python edgelab_gary.py --data history/ --home "X" --away "Y" --date YYYY-MM-DD --tier E0 --chat
NOTE: DataBot = API-Football key. Gary = Anthropic API key. Two separate keys.

## KEY NUMBERS
- Engine overall: 46.2% (weighted loss)
- Market baseline E0: 54.7% overall / 72.2% H/A only
- Our E0 H/A only: 66.5% vs market 72.2% (-5.7%)
- Away accuracy is the primary gap across all tiers
- Draw score rate S24: 26.6% (37/139) — matches real-world draw rate
- Signals: ALL DORMANT. Draw intelligence: DORMANT.
- Weather cache: 82k/132,685 rows (recheck S25)
- Dataset hash: 580b0f3a1667
- API-Football Pro plan: active until May 2026 — schedule connection before expiry

## KNOWN ISSUES — ACTIVE
- Draw floor 2% vs 26% — DPOL path blocked. New path: score prediction draw signal.
- E2 overconfidence w_form=0.94 — monitoring
- E1 home bias — investigate S25
- BTTS/scoreline inconsistency — partially improved by score prediction v2
- khaotikk.com Mailchimp auth — confirm S25
- instinct_dti_thresh / skew_correction_thresh — clarify S25

## MILESTONE STATUS
- M1: COMPLETE
- M2: IN PROGRESS. Weighted loss done. Items 2-5 not started.
- M3: FUTURE.

## FILES CHANGED S24
- edgelab_engine.py — compute_score_prediction v2
- edgelab_acca.py — winner_btts + qualifying picks list
- edgelab_gary_brain.py — last8_meetings naming fix
- edgelab_gary_context.py — weather_load fix
- edgelab_gridsearch.py — draw-focused objective
- edgelab_params.json — weighted loss params all 17 tiers
- edgelab_market_baseline.py — NEW
- edgelab_ha_breakdown.py — NEW

## GIT COMMIT MESSAGE S24
```
S24: score prediction v2, draw signal discovery, market baselines, predictions

Engine:
- compute_score_prediction v2 — venue-split goal tracking + 25% H2H blend
  Fixes result/scoreline contradictions (Liverpool H/0-0 eliminated)
- Draw signal discovery: score prediction independently finds 26.6% draw rate
  matching real-world frequency, independent of DTI — major finding for S25

Analysis:
- Market baselines all 17 tiers (B365 implied probability method)
- H/A only breakdown vs market — away accuracy is primary gap
- Draw gridsearch updated: draw-focused objective (draw +5pp gate)
- Signals-only DPOL run complete — all signals dormant

Fixes:
- edgelab_gary_brain.py: last6_meetings → last8_meetings
- edgelab_gary_context.py: weather_factor → weather_load

New files:
- edgelab_market_baseline.py
- edgelab_ha_breakdown.py

Acca builder:
- winner_btts acca type added
- Full qualifying picks list in matchday briefing

Predictions: 10-12 Apr 2026, 139 matches, internal + public HTML
```

## CLAUDE BEHAVIOUR RULES (non-negotiable)
- Never lie. Never cover. If uncertain, say so explicitly.
- One thing at a time.
- Rebrief from project knowledge every 8 exchanges. NO EXCEPTIONS.
  Every 8 exchanges — not "substantive" ones. No filtering. No judgment calls.
- Evaluate ideas, don't validate them.
- Session close checklist mandatory — all 8 items, unprompted.
- Generate ALL THREE documents at close: briefing doc + state file + master backlog.
- Use view tool to read files — not search summaries. Full read, every line.
- Use EDGELAB_SESSION_START_PROMPT.md at every session start.

## PARKED IDEAS — DO NOT BUILD WITHOUT FLAGGING
- Gary acca picks (product feature) — trigger: Gary live on site
- Social comment workflow — trigger: content push
- Underdog effect signal — trigger: signals active
- HeyGen avatar — Andrew's call
- Upset flip Stage 2 — trigger: Stage 1 history validated
- API-Football connection — schedule before May 2026 expiry
- Gary temporal awareness — trigger: API-Football connected
- DPOL upset-focused evolution — trigger: draw intelligence + signals active first
- Perplexity Computer — trigger: M3
- Personal web app — trigger: M2 running
- Gary app iOS/Android — trigger: M3
- Score prediction draw nudge — trigger: draw signal validated first
- Long shot acca — trigger: upset flip Stage 2 validated
- Expand to other sports — trigger: DPOL proven on football

## PERIODIC AUDIT SCHEDULE
- Protocol established S23
- Every 5-6 sessions: download Anthropic export, load into session
- Next due: approximately S28-29
