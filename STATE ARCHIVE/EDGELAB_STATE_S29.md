# EDGELAB — Claude State File S29
# For Claude's use at session start. Read alongside briefing doc and master backlog.
# Generated: Session 28 close — 10/04/2026

## LAST SESSION ENDED
Session 28. Second DPOL run assessed (46.8% overall, draw weights stripped by DPOL).
Three-pass full param evolution built and run — w_score_margin dominant signal across
15/17 tiers. draw_pull, dti_draw_lock, w_btts confirmed dead (zero signal).
Three-pass seed applied to 15 tiers. Third DPOL run started overnight.
HTML iOS fix applied, dates corrected, league names added to acca/qualifying picks.
Market baseline confirmed stable. Weather cache at 93.4%. Mailchimp auth confirmed.

## SESSION START HANDSHAKE — SAY THIS FIRST
"Last session ended with three-pass param evolution complete and a third DPOL run
seeded with w_score_margin across 15 tiers running overnight. First priority is to
assess those results. Do you have the new params.json?"

## CURRENT STATUS

### Three-Pass Param Evolution
STATUS: COMPLETE — S28
- edgelab_param_evolution.py built and run
- w_score_margin: dominant signal, fires on 15/17 tiers individually (+0.5pp to +1.8pp)
- 7 tiers with combination gains: SP1 +1.7pp, I2 +1.6pp, D1 +1.2pp, SC3 +1.1pp,
  SP2 +0.9pp, D2 +0.7pp, E3 +0.6pp
- draw_pull, dti_draw_lock, w_btts: confirmed zero signal — remove from candidate list
- param_profile.json saved

### Three-Pass Seed
STATUS: COMPLETE — S28
- edgelab_threepass_seed.py built and run
- 15 tiers seeded (source: threepass_seed_s28)
- E1 and SC1 unchanged — no movers found
- Key changes: w_score_margin activated across 15 tiers (0.1 to 0.3)
  I2: home_adv 0.248→0.45, w_gd 0.197→0.05
  SP1: w_form 0.394→0.1, w_gd 0.251→0.15
  SC3: home_adv 0.275→0.5
  D1: dti_edge_scale 0.4→0.5, dti_ha_scale 0.5→0.4

### DPOL
STATUS: THIRD RUN IN PROGRESS — running overnight S28
- Second run: 46.8% overall (+0.3pp vs S27). Draw weights zeroed by DPOL.
- Third run: seeded with threepass_seed_s28 values. w_score_margin active on 15 tiers.
- Expected completion: ~8 hours from start (~11pm 10/04 or early 11/04)

### Draw Intelligence
STATUS: DORMANT — DPOL keeps stripping draw weights
- Two DPOL runs now zeroed draw params on all/most tiers
- draw_pull, dti_draw_lock, w_btts: confirmed dead via three-pass
- w_score_margin may improve overall accuracy sufficiently that draw ceiling becomes
  the next bottleneck — reassess after third DPOL run
- Three-pass trigger was met by Andrew's decision — core param improvement first

### Weather Cache
STATUS: 123,926/132,685 (93.4%) — not ready to wire. Check S29.

### Website / Email
STATUS: FULLY WORKING
- garyknows.com live on Netlify
- khaotikk.com Mailchimp auth: CONFIRMED S28
- Mailchimp free trial: 8 days left — let expire, stay free tier
- 6 contacts (mostly Andrew) — Brevo migration not triggered yet
- Predictions HTML: MUST be deployed to Netlify as URL, not shared as file

### Public HTML
STATUS: iOS fix applied S28.
- Tab switching fix: touchend handler removed, inline onclick added to all 3 tab buttons
- Search fix: oninput + onkeyup + onchange inline on search input
- Dates: manually corrected +1 day (workaround for date labelling bug)
- League names: added to Gary's Picks acca cards and Qualifying Picks table
- CRITICAL: Fix only works when served from Netlify URL. Local file sharing does not work.
- Qualifying picks: still manually populated — automate S29 (queue item 2)
- Date labelling bug: fix at source still needed (queue item 3)

## S29 QUEUE — IN ORDER

1. Assess third DPOL overnight run results
   - Upload new edgelab_params.json
   - Check w_score_margin held on seeded tiers
   - Check overall accuracy improved above 46.8%
   - Check for any regressions
   - Update params table
2. Automate qualifying picks in edgelab_acca.py → public HTML output
   Include league name mapping (tier code → full name) in acca.py
3. Date labelling bug — fix at source in databot/acca.py
4. Weather cache row count check — wire if complete (target 132,685)
5. iOS HTML — confirm fix works via Netlify URL (deploy HTML, share URL)
6. Market baseline — add to standard post-DPOL checklist
7. Codebase refactor — trigger: draw wired, validated, params confirmed

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
- Engine overall: 46.8% (S28 second DPOL run, +0.3pp vs S27)
- E0: 50.7% | N1: 52.2% | I1: 49.8% | SC0: 50.2%
- Three-pass best individual gain: N1 +1.8pp (w_score_margin=0.3 → 53.1% projected)
- Three-pass best combo: SP1 +1.7pp (w_score_margin + w_form + w_gd)
- Draw intelligence: DORMANT — DPOL strips draw weights every run
- Dataset: 132,685 matches (373 files, 48 skipped — consistent)
- Dataset hash: 580b0f3a1667
- Weather cache: 123,926/132,685 (93.4%)
- API-Football Pro plan: active until May 2026 — schedule connection before expiry
- Mailchimp: 6 contacts, free trial 8 days left — let expire

## KNOWN ISSUES — ACTIVE
- Date labelling bug — fixtures appear a day early. Workaround: manual +1 day on HTML.
  Fix at source needed in databot or acca.py (queue item 3)
- Qualifying picks in public HTML — manually maintained. Automate S29 (queue item 2)
- Public HTML iOS — fix applied but only works via Netlify URL, not local file.
  Must deploy to Netlify and share URL.
- Draw intelligence dormant — DPOL strips weights. Core param improvement first.
- BTTS/scoreline inconsistency — partially improved by score prediction v2. Monitor.
- instinct_dti_thresh / skew_correction_thresh — confirmed unused stubs. Review at refactor.
- Market baseline table — now confirmed stable at S24 numbers. Permanent benchmark.
- SC3 home_adv large jump (0.275→0.5) — watch after third DPOL run
- SP1 w_form large drop (0.394→0.1) — watch after third DPOL run

## MILESTONE STATUS
- M1: COMPLETE
- M2: IN PROGRESS. Weighted loss done. Items 2-5 not started.
- M3: FUTURE.

## FILES CHANGED S28
- edgelab_param_evolution.py — NEW. Three-pass full param evolution tool.
- edgelab_threepass_seed.py — NEW. Seeds param_profile.json into edgelab_params.json.
- edgelab_params.json — Updated with threepass_seed_s28 values. Third DPOL pending.
- param_profile.json — NEW. Three-pass results for all 17 tiers.
- edgelab_2026-04-09_predictions_public.html — iOS tab fix, dates +1 day, league names.

## GIT COMMIT MESSAGE S28
```
S28: three-pass param evolution, threepass seed, HTML iOS fix, market baseline
```

## CLAUDE BEHAVIOUR RULES (non-negotiable)
- Never lie. Never cover. If uncertain, say so explicitly.
- One thing at a time.
- Rebrief from project knowledge every 8 prompts. NO EXCEPTIONS.
  Every 8 prompts — not "substantive" ones. No filtering. No judgment calls.
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
- draw_pull, dti_draw_lock, w_btts — CONFIRMED DEAD via three-pass S28. Zero signal.
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
