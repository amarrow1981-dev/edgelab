# EDGELAB — Claude State File S28
# For Claude's use at session start. Read alongside briefing doc and master backlog.
# Generated: Session 27 close — 10/04/2026

## LAST SESSION ENDED
Session 27. Full Anthropic export audit completed (all 29 conversations). Backlog
fully updated. Full DPOL re-run assessed: 46.5% overall, no regressions, 14 tiers
improved. E1 home bias structurally improved. w_xg_draw and composite_draw_boost
added to DPOL search space (were missing). Draw weights seeded from gridsearch:
9/16 tiers passed gate and saved — draw intelligence live for first time on EC, B1,
D1, D2, SC0, SC1, SC2, SP1, SP2. Second full DPOL run started overnight with seeded
draw params as starting points.

## SESSION START HANDSHAKE — SAY THIS FIRST
"Last session ended with draw intelligence seeded on 9 tiers and a second full DPOL
run running overnight. First priority is to assess those results. Do you have the
new params.json, or is it still running?"

## CURRENT STATUS

### Draw Intelligence
STATUS: PARTIALLY LIVE — 9/16 tiers active, 7 dormant, second DPOL run overnight
- 9 tiers with draw params seeded (source: draw_seed_s27): EC, B1, D1, D2, SC0, SC1, SC2, SP1, SP2
- 7 tiers dormant (failed gate at exactly -0.5% overall): E0, E1, E2, E3, I1, I2, SC3
- Signal is real — E0 gained +13.5pp draw accuracy but cost just over gate limit
- N1 excluded by design — failed gridsearch gate
- Second DPOL run: starts from seeded draw weights, can now search w_xg_draw + composite_draw_boost
- Three-pass trigger: draw confirmed under rolling window validation

### DPOL
STATUS: SECOND RUN IN PROGRESS — running overnight S27
- First S27 run: 46.5% overall (+0.7pp vs S24). No regressions.
- Second run: seeded draw params as starting points. Results pending S28.
- w_xg_draw + composite_draw_boost now in _generate_candidates (fixed S27)

### E1 Home Bias
STATUS: STRUCTURALLY IMPROVED S27
- home_adv dropped 0.373→0.272, w_form dropped 0.30→0.25
- E1 accuracy held at 44.6% — bias reduction without accuracy cost
- Monitor after second DPOL run

### Weather Cache
STATUS: 105,388/132,685 rows (79.4%) — not ready to wire. Check S28.

### Website / Email
STATUS: FULLY WORKING
- khaotikk.com Mailchimp auth: still unconfirmed — check S28

### Public HTML
STATUS: Working. Qualifying picks manually maintained — automate S28 (queue item 3).
iOS Safari tab/search bug confirmed — fix queued S28.

## S28 QUEUE — IN ORDER

1. Assess second DPOL overnight run results
   - Upload new edgelab_params.json
   - Check 7 failing tiers found draw balance
   - Check 9 seeded tiers improved further
   - Gate: no regression below S27 DPOL baseline
   - Gate met = three-pass trigger confirmed
2. Three-pass full param evolution — TRIGGER: draw confirmed in item 1
3. Automate qualifying picks in edgelab_acca.py → public HTML output
4. Confirm khaotikk.com Mailchimp auth
5. Weather cache row count check — target 132,685
6. iOS Safari HTML fix — onkeyup + onchange fallbacks on search input
7. Date labelling bug — investigate root cause
8. Market baseline refresh — run edgelab_market_baseline.py, update table
9. Codebase refactor — trigger: draw wired, validated, params confirmed

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
- Engine overall: 46.5% (S27 DPOL run, +0.7pp vs S24)
- E0: 50.8% | N1: 53.2% | I1: 49.6% | SC0: 50.2%
- Draw intelligence: 9/16 tiers live (draw_seed_s27). 7 dormant pending second DPOL run.
- Draw evolution best combination: 1.347x lift, 35.5% draw rate, 888 matches
- Gridsearch: 16/17 tiers found draw signal (gate: draw +5pp, overall within -0.5%)
- Market baseline E0: 54.7% overall / 72.2% H/A only — REFRESH DUE S28
- Our E0 H/A only: 66.5% vs market 72.2% (-5.7%)
- E1 home bias: home_adv 0.373→0.272 after S27 run — structurally improved
- Dataset: 132,685 matches (373 files, 48 skipped — consistent)
- Dataset hash: 580b0f3a1667
- Weather cache: 105,388/132,685 (79.4%)
- API-Football Pro plan: active until May 2026 — schedule connection before expiry

## KNOWN ISSUES — ACTIVE
- Draw intelligence dormant on 7 tiers — second DPOL run overnight should resolve
- I1/I2 overcalling draws (26.4% and 38.7%) at seeded weights — DPOL tuning overnight
- E2 overconfidence w_form=0.796 — monitoring
- BTTS/scoreline inconsistency — partially improved by score prediction v2
- khaotikk.com Mailchimp auth — unconfirmed, check S28
- instinct_dti_thresh / skew_correction_thresh — confirmed unused stubs, review at refactor
- Qualifying picks in public HTML — manually maintained, automate S28
- Public HTML iOS Safari — tab/search unresponsive on iPhone. Android works. Fix queued S28.
- Date labelling bug — fixtures appear a day early in HTML. Root cause unconfirmed.
- Market baseline table — S24 numbers, refresh due S28

## MILESTONE STATUS
- M1: COMPLETE
- M2: IN PROGRESS. Weighted loss done. Items 2-5 not started.
- M3: FUTURE.

## FILES CHANGED S27
- edgelab_dpol.py — w_xg_draw + composite_draw_boost added to _generate_candidates
- edgelab_draw_dpol_seed.py — NEW. Seeds gridsearch draw weights, gate-validates, saves.
- edgelab_params.json — S27 DPOL full run + draw seed 9 tiers. Overnight update pending.
- EDGELAB_MASTER_BACKLOG.md — full audit update from Anthropic export (all 29 conversations)

## GIT COMMIT MESSAGE S27
```
S27: full audit, DPOL assessed, draw intelligence seeded 9 tiers, dpol search space fixed

- Full Anthropic export audit (29 conversations) — backlog updated with all gaps
  Gary avatar, addiction layer, team affiliation, weekly longshot, selection builder,
  Stage 2 draw rate strategy all captured
- S27 DPOL full run: 46.5% overall (+0.7pp vs S24 baseline), no regressions
  N1 +1.7pp (53.2%), I2 +1.5pp, SP2 +1.5pp, B1 +1.3pp
  E1 home bias improved: home_adv 0.373→0.272
- edgelab_dpol.py: w_xg_draw + composite_draw_boost added to _generate_candidates
- edgelab_draw_dpol_seed.py: new tool — seeds gridsearch draw weights, gate-validates
  9/16 tiers passed draw gate — draw intelligence live for first time
- edgelab_params.json: S27 DPOL results + draw seed for 9 tiers
- Second full DPOL run started overnight with seeded draw params
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
- Gary avatar / HeyGen — Kling sub active, 7-sec clip exists. Trigger: M3
- Upset flip Stage 2 — trigger: Stage 1 history validated
- API-Football connection — schedule before May 2026 expiry
- Gary temporal awareness — trigger: API-Football connected
- DPOL upset-focused evolution — trigger: draw intelligence + signals active first
- Perplexity Computer — trigger: M3
- Personal web app — trigger: M2 running
- Gary app iOS/Android — trigger: M3
- Long shot acca — trigger: upset flip Stage 2 validated
- Gary's Weekly Longshot (charity edition) — trigger: upset flip Stage 2 validated
- Expand to other sports — trigger: DPOL proven on football
- Score prediction draw nudge — ABANDONED. No signal.
- Codebase refactor — trigger: draw wired, validated, params confirmed
- Three-pass full param evolution — trigger: draw confirmed under DPOL (check S28 item 1)
- Retest previously discarded params — trigger: three-pass proven on draws
- instinct_dti_thresh / skew_correction_thresh — review at codebase refactor
- Stage 2 draw rate strategy (25-27% band) — trigger: three-pass proven on draws
- Gary onboarding — team affiliation — trigger: M3
- Gary accent / regional persona — trigger: M3
- Gary behavioural addiction detection — trigger: M3
- Selection builder (on-site, not bet builder) — trigger: M3
- Cryptocurrency payment options — trigger: M3 paid tier
- Countdown clock on landing page — trigger: launch date confirmed

## PERIODIC AUDIT SCHEDULE
- Protocol established S23
- Every 5-6 sessions: download Anthropic export, load into session
- Last done: S27 — all 29 conversations read
- Next due: approximately S32-33
