# EDGELAB — Claude State File S26
# For Claude's use at session start. Read alongside briefing doc and master backlog.
# Generated: Session 25 close — 09/04/2026

## LAST SESSION ENDED
Session 25. Draw signal discovery validated and extended. pred_score_draw confirmed
NO SIGNAL (p=0.1876) — SCORE_DRAW_NUDGE removed from engine. Draw evolution tool
built and run across 132,685 matches. BREAKTHROUGH: combination signals up to
1.347x lift. odds_draw_prob is the anchor. Supporting signals (form_parity,
draw_rate, h2h_draw_rate, dti) amplify it significantly when combined.
draw_profile.json produced with per-tier suggested weights.
Codebase refactor added to backlog. Queue items 2-8 all deferred.

## SESSION START HANDSHAKE — SAY THIS FIRST
"Last session ended with the draw evolution breakthrough — combinations of
odds_draw_prob with supporting signals reach 1.347x lift (35.5% draw rate vs
26.3% baseline). Queue item 1 is to wire the composite draw signal into the
engine. Do you want to start there, or is there anything urgent first?"

## CURRENT STATUS

### Draw Intelligence
STATUS: BREAKTHROUGH — ready to wire
- Individual signals: odds_draw_prob 1.202x, expected_goals_total 1.088x
- Combination signals: up to 1.347x (home_draw_rate + odds_draw_prob + form_parity)
- All combinations that cleared 1.15x included odds_draw_prob as anchor
- Per-tier suggested weights in draw_profile.json
- Next: wire composite signal into engine, seed gridsearch from profile

### SCORE_DRAW_NUDGE
STATUS: REMOVED S25
- Validated: NO SIGNAL. p=0.1876 across 132,685 matches.
- Removed from edgelab_engine.py.

### Score Prediction
STATUS: v2 deployed S24. SCORE_DRAW_NUDGE removed S25.
Full DPOL re-run still needed (deferred from S25).

### DPOL
STATUS: WEIGHTED LOSS RUN COMPLETE (S24)
- All signals dormant. Draw intelligence dormant.
- Activation path now clear — composite draw signal + seeded gridsearch.

### Weather Cache
STATUS: RUNNING — check row count S26. Target 132,685.

### Website / Email
STATUS: FULLY WORKING
- khaotikk.com Mailchimp auth: unconfirmed — check S26.

### Predictions
STATUS: Weekend 10-12 Apr done S24. Midweek run deferred S25.
Check if midweek fixtures are still relevant or have passed.

## S26 QUEUE — IN ORDER

1. Wire draw composite signal into engine
   a. Add expected_goals_total as new draw_score input
   b. Add composite gate: odds_draw_prob > 0.288 AND supporting signal in
      draw-positive band → boost draw_score
   c. Spec before build — confirm with Andrew first
2. Seed draw gridsearch from draw_profile.json — run per tier
3. Full DPOL re-run (score prediction v2 + draw changes)
4. Public HTML qualifying picks tab fix — clean rebuild of tab structure
5. Check weather cache row count
6. Confirm khaotikk.com Mailchimp auth
7. Clarify instinct_dti_thresh / skew_correction_thresh
8. E1 home bias investigation
9. Codebase refactor — all .py files — trigger: after draw wired + validated

## STANDARD WEEKLY WORKFLOW (permanent)
- Thursday: predictions for weekend fixtures + accas + Gary upset picks
- Sunday: predictions for midweek fixtures + accas + Gary upset picks
- Results check after each fixture set completes

## WEEKLY PREDICTION COMMANDS (exact)
Step 1: python edgelab_databot.py --key YOUR_API_FOOTBALL_KEY --days 4
Step 2: python edgelab_predict.py --data history/ --fixtures databot_output/YYYY-MM-DD_fixtures.csv --tier all
Step 3: python edgelab_acca.py predictions/YYYY-MM-DD_predictions.csv --all-types
Step 4: python edgelab_upset_picks.py --data history/ --predictions predictions/YYYY-MM-DD_predictions.csv
Step 5: python edgelab_gary.py --data history/ --home "X" --away "Y" --date YYYY-MM-DD --tier E0 --chat
NOTE: DataBot = API-Football key. Gary = Anthropic API key. Two separate keys.

## KEY NUMBERS
- Engine overall: 46.2% (weighted loss, S24)
- Draw evolution best combination: 1.347x lift, 35.5% draw rate, 888 matches
- Market baseline E0: 54.7% overall / 72.2% H/A only
- Our E0 H/A only: 66.5% vs market 72.2% (-5.7%)
- Away accuracy is the primary H/A gap
- Dataset: 132,685 matches (373 files, 48 skipped — consistent)
- Dataset hash: 580b0f3a1667
- API-Football Pro plan: active until May 2026 — schedule connection before expiry

## KNOWN ISSUES — ACTIVE
- Draw intelligence dormant — activation path now clear (composite signal)
- E2 overconfidence w_form=0.94 — monitoring
- E1 home bias — investigate S26
- BTTS/scoreline inconsistency — partially improved by score prediction v2
- khaotikk.com Mailchimp auth — confirm S26
- instinct_dti_thresh / skew_correction_thresh — clarify S26
- Public HTML qualifying picks tab — div closure issue — fix S26

## MILESTONE STATUS
- M1: COMPLETE
- M2: IN PROGRESS. Weighted loss done. Items 2-5 not started.
- M3: FUTURE.

## FILES CHANGED S25
- edgelab_engine.py — SCORE_DRAW_NUDGE removed
- edgelab_draw_signal_validation.py — NEW
- edgelab_draw_evolution.py — NEW
- draw_profile.json — NEW (in EDGELAB folder, not project knowledge)

## GIT COMMIT MESSAGE S25
```
S25: draw signal validation, draw evolution breakthrough, nudge removed

Validation:
- pred_score_draw: NO SIGNAL. p=0.1876, lift +1.1% across 132,685 matches.
  The 26.6% draw-score rate is a Poisson property, not a predictor.
- SCORE_DRAW_NUDGE removed from edgelab_engine.py

Draw evolution (edgelab_draw_evolution.py — new):
- Three-pass analysis across 132,685 matches, 17 tiers
- Individual: odds_draw_prob 1.202x, expected_goals_total 1.088x
- Combinations: up to 1.347x (home_draw_rate + odds_draw_prob + form_parity)
- All 1.15x+ combinations include odds_draw_prob as anchor
- draw_profile.json: per-tier suggested weights, combination results

New files:
- edgelab_draw_signal_validation.py
- edgelab_draw_evolution.py
- draw_profile.json
```

## CLAUDE BEHAVIOUR RULES (non-negotiable)
- Never lie. Never cover. If uncertain, say so explicitly.
- One thing at a time.
- Rebrief from project knowledge every 8 exchanges. NO EXCEPTIONS.
  Every 8 exchanges — not "substantive" ones. No filtering. No judgment calls.
- Evaluate ideas, don't validate them.
- Session close checklist mandatory — all 8 items, unprompted.
- Generate ALL THREE documents at close AS FILES — not in chat.
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
- Long shot acca — trigger: upset flip Stage 2 validated
- Expand to other sports — trigger: DPOL proven on football
- Score prediction draw nudge — ABANDONED. No signal.
- Codebase refactor — trigger: after draw intelligence wired and validated

## PERIODIC AUDIT SCHEDULE
- Protocol established S23
- Every 5-6 sessions: download Anthropic export, load into session
- Next due: approximately S28-29
