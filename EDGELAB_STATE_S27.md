# EDGELAB — Claude State File S27
# For Claude's use at session start. Read alongside briefing doc and master backlog.
# Generated: Session 26 close — 09/04/2026

## LAST SESSION ENDED
Session 26. Composite draw signal wired into engine. Gridsearch rebuilt and run
across all 17 tiers seeded from draw_profile.json — 16/17 passed gate. Full DPOL
re-run started overnight — E0 single-tier validated at 50.8% (+1.5pp). E1 home bias
confirmed and diagnosed. Public HTML tab system fixed. Weather cache at 79.4%.
instinct_dti_thresh/skew_correction_thresh confirmed as unused stubs.

## SESSION START HANDSHAKE — SAY THIS FIRST
"Last session ended with the composite draw signal wired and the gridsearch run —
16/17 tiers found draw signal. The full DPOL re-run was running overnight. First
priority is to assess those results. Do you have the output, or is it still running?"

## CURRENT STATUS

### Draw Intelligence
STATUS: WIRED — pending DPOL rolling window validation
- Composite gate: odds_draw_prob > 0.288 AND supporting signal in draw-positive band
- expected_goals_total wired as standalone draw signal (1.088x lift)
- w_xg_draw and composite_draw_boost in EngineParams + LeagueParams — both 0.0
- Gridsearch: 16/17 tiers found draw signal under gate conditions
- N1 failed gate — best seen 22.6% draw acc but breached overall tolerance
- Next: assess DPOL overnight results, then seed draw weights from gridsearch

### DPOL Re-run
STATUS: IN PROGRESS — running overnight S26
- E0 single-tier: 50.8% (+1.5pp vs S24 baseline of 50.3%)
- Full 17-tier results pending
- Draw params (w_xg_draw, composite_draw_boost) need confirming in DPOL search space

### Score Prediction
STATUS: v2 deployed S24. SCORE_DRAW_NUDGE removed S25.
Full DPOL re-run in progress — will revalidate.

### E1 Home Bias
STATUS: CONFIRMED S26
- Engine calling H 80.3% vs 43.8% actual home wins
- 2,617 away wins misclassified as H (74.5% of all away wins)
- Root cause: home_adv=0.373 with w_form=0.30, w_gd=0.22
- Expected to rebalance after full DPOL re-run with new signals active
- Monitor after overnight results

### Weather Cache
STATUS: 105,388/132,685 rows (79.4%) — not ready to wire

### Website / Email
STATUS: FULLY WORKING
- khaotikk.com Mailchimp auth: still unconfirmed — check S27

### Public HTML
STATUS: FIXED S26
- Tab system rebuilt: Gary's Picks / All Predictions / Qualifying Picks
- Search fixed and scoped to predictions tab
- Qualifying picks tab populated from acca data
- Note: qualifying picks still manually maintained — automate in edgelab_acca.py (queue item 4)

## S27 QUEUE — IN ORDER

1. Assess full DPOL overnight re-run results
   - Check accuracy per tier vs S24 baseline
   - Confirm w_xg_draw + composite_draw_boost in DPOL search space
   - Check E1 home bias rebalance
   - Gate: no tier should regress below S24 baseline
2. Seed draw weights from gridsearch_results.json into DPOL
   Run targeted draw DPOL pass — validate under rolling window
   Gate: draw accuracy +5pp AND overall -0.5% maximum
3. Confirm new params in DPOL search space (w_xg_draw, composite_draw_boost)
4. Automate qualifying picks in edgelab_acca.py → public HTML output
5. Confirm khaotikk.com Mailchimp auth
6. Weather cache row count check — target 132,685
7. Three-pass full param evolution — TRIGGER: draw intelligence proven in items 1-2
8. Codebase refactor — TRIGGER: draw intelligence wired, validated, params confirmed

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
- Engine overall: 46.2% (weighted loss, S24) — full update pending overnight run
- E0: 50.8% (S26 single-tier DPOL run, +1.5pp)
- Draw evolution best combination: 1.347x lift, 35.5% draw rate, 888 matches
- Gridsearch: 16/17 tiers found draw signal (gate: draw +5pp, overall within -0.5%)
- Market baseline E0: 54.7% overall / 72.2% H/A only
- Our E0 H/A only: 66.5% vs market 72.2% (-5.7%)
- E1 home bias: calling H 80.3% vs 43.8% actual — confirmed S26
- Dataset: 132,685 matches (373 files, 48 skipped — consistent)
- Dataset hash: 580b0f3a1667
- Weather cache: 105,388/132,685 (79.4%)
- API-Football Pro plan: active until May 2026 — schedule connection before expiry

## KNOWN ISSUES — ACTIVE
- Draw intelligence dormant — wired S26, activation pending DPOL rolling window validation
- E1 home bias — confirmed S26. Monitor after full DPOL re-run
- E2 overconfidence w_form=0.94 — monitoring
- BTTS/scoreline inconsistency — partially improved by score prediction v2
- khaotikk.com Mailchimp auth — unconfirmed, check S27
- instinct_dti_thresh / skew_correction_thresh — confirmed unused stubs, review at refactor
- Qualifying picks in public HTML — manually maintained, automate S27
- Public HTML mobile tab switching — unresponsive on mobile, web works fine. Parked S26, revisit S27.

## MILESTONE STATUS
- M1: COMPLETE
- M2: IN PROGRESS. Weighted loss done. Items 2-5 not started.
- M3: FUTURE.

## FILES CHANGED S26
- edgelab_engine.py — w_xg_draw + composite_draw_boost params; composite draw gate; make_pred_fn bridge updated
- edgelab_dpol.py — w_xg_draw + composite_draw_boost added to LeagueParams
- edgelab_gridsearch.py — full rebuild: all 17 tiers, seeded from draw_profile.json, new params, --tier flag
- edgelab_2026-04-09_predictions_public.html — tab system built, search fixed, qualifying picks tab added
- edgelab_params.json — E0 updated (50.8%). Full update pending overnight run.

## GIT COMMIT MESSAGE S26
```
S26: composite draw signal wired, gridsearch rebuilt, E1 bias confirmed

Engine changes:
- edgelab_engine.py: w_xg_draw + composite_draw_boost added to EngineParams
  Composite gate: odds_draw_prob > 0.288 AND supporting signal → additive draw_score boost
  expected_goals_total wired as standalone draw signal
  make_pred_fn bridge updated to pass new params through
- edgelab_dpol.py: w_xg_draw + composite_draw_boost added to LeagueParams

Gridsearch:
- edgelab_gridsearch.py: full rebuild — all 17 tiers, seeded from draw_profile.json
  16/17 tiers passed gate (draw +5pp, overall within -0.5%)
  New params (w_xg_draw, composite_draw_boost) included in search

Analysis:
- E1 home bias confirmed: 80.3% H predictions vs 43.8% actual
  Confusion matrix: 2,617 away wins misclassified as H
  Root cause: home_adv=0.373, w_form=0.30 — DPOL over-relied on home advantage
- Weather cache: 105,388/132,685 (79.4%) — not ready to wire
- instinct_dti_thresh / skew_correction_thresh: confirmed unused stubs

DPOL:
- E0 single-tier run: 50.8% (+1.5pp). Full 17-tier run running overnight.

HTML:
- edgelab_2026-04-09_predictions_public.html: tab system rebuilt from scratch
  Gary's Picks / All Predictions / Qualifying Picks tabs working
  Search fixed and scoped to predictions tab
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
- Three-pass full param evolution — trigger: draw intelligence proven under DPOL
- Retest previously discarded params via three-pass — trigger: three-pass proven on draws
- instinct_dti_thresh / skew_correction_thresh — review and decision at codebase refactor

## PERIODIC AUDIT SCHEDULE
- Protocol established S23
- Every 5-6 sessions: download Anthropic export, load into session
- Next due: approximately S28-29
