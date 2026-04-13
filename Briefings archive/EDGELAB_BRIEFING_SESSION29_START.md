# EdgeLab — Session 29 Briefing

## What We Are Building

Most sports analytics measures average. Average is what bookmakers price. Average is
what everyone else optimises for. We already beat average — E0 at 50.7%, N1 at 53.2%,
overall at 46.8% on second DPOL run S28. Three-pass param evolution now seeded across
15 tiers. Third full DPOL run running overnight S28.

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

**Current engine status:** 46.8% overall (S28 second DPOL run). E0: 50.7%, N1: 52.2%.
Three-pass seed applied to 15 tiers. Third DPOL run running overnight S28.

---

## Session 29 — Start State

### Actions completed in Session 28

- **Second DPOL run assessed** — COMPLETE.
  46.8% overall (+0.3pp vs S27). No regressions on 15/17 tiers.
  N1 slipped -1.0pp (52.2%), I2 slipped -0.5pp. All other tiers held or improved.
  Draw intelligence: DPOL stripped draw weights off all seeded tiers.
  Only EC retained w_draw_odds=0.05. Draw params zeroed across 16/17 tiers.
  Conclusion: DPOL can't hold draw params against sequential optimisation.
  Three-pass is the correct next step.

- **Three-pass full param evolution — BUILT AND RUN** — COMPLETE.
  edgelab_param_evolution.py built. Full run across all 17 tiers.
  w_score_margin dominant signal: fires on 15/17 tiers individually.
  7 tiers with combination gains: SP1 +1.7pp, I2 +1.6pp, D1 +1.2pp,
  SC3 +1.1pp, SP2 +0.9pp, D2 +0.7pp, E3 +0.6pp.
  draw_pull, dti_draw_lock, w_btts all tested — zero signal individually or in combination.
  Core finding: w_score_margin is the unlock. Draw signals need core params right first.
  param_profile.json saved.

- **Three-pass seed — BUILT AND RUN** — COMPLETE.
  edgelab_threepass_seed.py built. 15 tiers seeded into edgelab_params.json.
  E1 and SC1 unchanged (no movers found).
  Source: threepass_seed_s28.
  Third DPOL run started overnight with these as starting points.

- **Market baseline refreshed** — COMPLETE.
  edgelab_market_baseline.py run. S24 numbers confirmed stable — no change.
  Now confirmed as permanent benchmark. Add to standard post-DPOL checklist.

- **Weather cache checked** — COMPLETE.
  123,926/132,685 rows (93.4%). Up from 79.4% at S26. Not yet complete.

- **khaotikk.com Mailchimp auth confirmed** — COMPLETE.
  Both garyknows.com and khaotikk.com show Authenticated in Mailchimp Domains.
  Mailchimp free trial has 8 days left — decision: let it expire, stay on free tier.
  6 real contacts (mostly Andrew). Brevo migration trigger (400 contacts) not near.

- **Public HTML iOS fix — COMPLETE.**
  Tab switching broken on iPhone Chrome/Safari when opening file from email.
  Root cause: touchend + click double-firing. Fixed by removing touchend handler,
  adding inline onclick on all three tab buttons. onkeyup + onchange added to search.
  user-select:none added to tab button CSS.
  Additional fix: all match dates rolled forward +1 day (date labelling bug workaround).
  League names and dates added to all acca picks (Gary's Picks tab).
  League names replacing tier codes in Qualifying Picks tab.
  NOTE: File was being shared via email and opened locally — tabs will never work
  reliably in that context. File should be deployed to Netlify and shared as URL.

- **Mailchimp Brevo migration** — no action needed yet. Under 400 contacts.

### The three-pass result — S28 milestone

Three-pass proved: w_score_margin is the dominant untapped signal, currently at 0.0
on most tiers. DPOL has been ignoring it because it wasn't activated in starting params.
Draw signals are not the unlock — core param recalibration is. Third DPOL run starting
from threepass_seed_s28 values is the most promising run yet.

**Trigger check at S29 open: assess third DPOL overnight run results. If w_score_margin
holds across tiers and overall accuracy improves, update params table and move to
automating HTML output.**

### Session continuity protocol — active
- Three documents in project knowledge: briefing doc + state file + master backlog
- Session start prompt: use EDGELAB_SESSION_START_PROMPT.md at every new session
- Context refresh: every 8 exchanges — NO EXCEPTIONS (every 8 prompts regardless of size)
- Periodic full audit: every 5-6 sessions. Last done S27. Next due ~S32-33.

---

## Ordered Work Queue

### Session 29 — priorities in order

1. **Assess third DPOL overnight run results**
   Upload new edgelab_params.json. Check:
   - Did w_score_margin hold on the seeded tiers?
   - Overall accuracy — target above 46.8% (S28 baseline)
   - Any regressions vs S28?
   - Did DPOL find further improvements on top of the seed?
   Gate: improvement confirms three-pass seed worked. Update params table.

2. **Public HTML qualifying picks — automate in edgelab_acca.py**
   Currently manually populated. Wire edgelab_acca.py output to public HTML.
   Qualifying picks section should write automatically on each prediction run.
   Also: league names + dates should be auto-populated from acca picks.
   Tier code → league name mapping needed in acca.py.

3. **Date labelling bug — fix at source**
   Root cause: DataBot UTC offset or acca.py date conversion.
   Currently working around it manually (+1 day). Fix properly.

4. **Weather cache — check row count and wire if complete**
   At 93.4% (123,926/132,685) at S28. Check if complete.
   If complete: wire weather signal to DPOL.

5. **iOS HTML — confirm fix works via Netlify URL**
   Deploy HTML to Netlify. Share URL not file. Confirm tabs work on iPhone.

6. **Market baseline refresh — add to post-DPOL checklist**
   Already refreshed S28. Confirmed stable. Add formally to workflow.

7. **Codebase refactor** — trigger: draw intelligence wired, validated, params confirmed.

### Standard weekly workflow (permanent)
- Thursday: predictions for weekend fixtures + accas + Gary upset picks
- Sunday: predictions for midweek fixtures + accas + Gary upset picks
- Results check after each fixture set completes

### Weekly prediction commands (exact)
Step 1: python edgelab_databot.py --key YOUR_API_FOOTBALL_KEY --days 4
Step 2: python edgelab_predict.py --data history/ --fixtures databot_output/YYYY-MM-DD_fixtures.csv --tier all
Step 3: python edgelab_acca.py predictions/YYYY-MM-DD_predictions.csv --all-types
Step 4: python edgelab_upset_picks.py --data history/ --predictions predictions/YYYY-MM-DD_predictions.csv
Step 5: python edgelab_gary.py --data history/ --home "X" --away "Y" --date YYYY-MM-DD --tier E0 --chat
NOTE: DataBot = API-Football key. Gary = Anthropic API key. Two separate keys.

### Parked — reintroduce at right moment
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
- Codebase refactor — trigger: draw intelligence wired, validated, params confirmed
- Retest previously discarded params — DONE via three-pass S28. draw_pull, dti_draw_lock,
  w_btts all tested — zero signal. Confirmed dead. Remove from candidate list.
- instinct_dti_thresh / skew_correction_thresh — review at codebase refactor
- Stage 2 draw rate strategy (25-27% band) — trigger: three-pass proven on draws
- Gary onboarding — team affiliation — trigger: M3
- Gary accent / regional persona — trigger: M3
- Gary behavioural addiction detection — trigger: M3
- Selection builder (on-site, not bet builder) — trigger: M3
- Cryptocurrency payment options — trigger: M3 paid tier
- Countdown clock on landing page — trigger: launch date confirmed

---

## Signal weights — current (post threepass_seed_s28)

| Tier | w_form | w_gd | home_adv | w_score_margin | Source |
|------|--------|------|----------|----------------|--------|
| E0 | 0.480 | 0.278 | 0.420 | 0.300 | threepass_seed_s28 |
| E1 | 0.253 | 0.141 | 0.272 | 0.000 | dpol_run (unchanged) |
| E2 | 0.796 | 0.506 | 0.483 | 0.300 | threepass_seed_s28 |
| E3 | 0.272 | 0.175 | 0.148 | 0.100 | threepass_seed_s28 |
| EC | 0.772 | 0.181 | 0.325 | 0.200 | threepass_seed_s28 |
| B1 | 0.633 | 0.306 | 0.365 | 0.300 | threepass_seed_s28 |
| D1 | 0.658 | 0.295 | 0.261 | 0.300 | threepass_seed_s28 |
| D2 | 0.619 | 0.137 | 0.415 | 0.100 | threepass_seed_s28 |
| I1 | 0.697 | 0.340 | 0.302 | 0.300 | threepass_seed_s28 |
| I2 | 0.526 | 0.197 | 0.248 | 0.200 | threepass_seed_s28 |
| N1 | 0.479 | 0.222 | 0.297 | 0.300 | threepass_seed_s28 |
| SC0 | 1.073 | 0.329 | 0.214 | 0.300 | threepass_seed_s28 |
| SC1 | 0.535 | 0.297 | 0.304 | 0.000 | dpol_run (unchanged) |
| SC2 | 0.755 | 0.327 | 0.273 | 0.200 | threepass_seed_s28 |
| SC3 | 0.847 | 0.310 | 0.275 | 0.300 | threepass_seed_s28 |
| SP1 | 0.459 | 0.218 | 0.320 | 0.250 | threepass_seed_s28 |
| SP2 | 0.314 | 0.157 | 0.375 | 0.200 | threepass_seed_s28 |

NOTE: Full param changes per tier in param_profile.json and edgelab_params.json.
Key combination changes: I2 home_adv 0.248→0.45, w_gd 0.197→0.05.
SP1 w_form 0.394→0.1, w_gd 0.251→0.15. SC3 home_adv 0.275→0.5.
D1 dti_edge_scale 0.4→0.5, dti_ha_scale 0.5→0.4.

---

## Market Baselines — All 17 Tiers (confirmed stable S28)

| Tier | Mkt Overall | Mkt H/A Only | EdgeLab Overall | Gap (Overall) |
|------|------------|--------------|-----------------|---------------|
| E0 | 54.7% | 72.2% | 50.7% | -4.0% |
| E1 | 46.6% | 64.0% | 44.6% | -2.0% |
| E2 | 47.7% | 64.7% | 44.5% | -3.2% |
| E3 | 45.2% | 62.0% | 43.1% | -2.1% |
| EC | 48.2% | 65.1% | 45.2% | -3.0% |
| B1 | 52.5% | 70.2% | 48.5% | -4.0% |
| D1 | 51.8% | 68.9% | 47.9% | -3.9% |
| D2 | 47.2% | 64.8% | 44.8% | -2.4% |
| I1 | 54.4% | 73.5% | 49.8% | -4.6% |
| I2 | 45.8% | 66.2% | 41.9% | -3.9% |
| N1 | 56.2% | 73.4% | 52.2% | -4.0% |
| SC0 | 52.9% | 70.0% | 50.2% | -2.7% |
| SC1 | 47.5% | 65.4% | 44.4% | -3.1% |
| SC2 | 50.4% | 65.0% | 47.4% | -3.0% |
| SC3 | 49.4% | 63.5% | 46.6% | -2.8% |
| SP1 | 53.6% | 71.5% | 48.9% | -4.7% |
| SP2 | 46.8% | 65.9% | 44.5% | -2.3% |

Market numbers confirmed stable vs S24. Safe to use as permanent benchmark.

---

## Files

| File | Status | Notes |
|------|--------|-------|
| edgelab_engine.py | Updated S26 | w_xg_draw + composite_draw_boost added |
| edgelab_dpol.py | Updated S27 | w_xg_draw + composite_draw_boost in _generate_candidates |
| edgelab_gridsearch.py | Updated S26 | Full rebuild — all 17 tiers |
| edgelab_draw_dpol_seed.py | New S27 | Seeds gridsearch draw weights |
| edgelab_param_evolution.py | New S28 | Three-pass full param evolution tool |
| edgelab_threepass_seed.py | New S28 | Seeds param_profile.json into edgelab_params.json |
| edgelab_acca.py | Updated S24 | winner_btts; qualifying picks list |
| edgelab_gary_brain.py | Updated S24 | last8_meetings fix |
| edgelab_gary_context.py | Updated S24 | weather_load fix |
| edgelab_upset_picks.py | Built S22 | |
| edgelab_databot.py | Updated S17 | All 17 tiers |
| edgelab_weather.py | Updated S17 | --batch CLI |
| edgelab_config.py | Updated S16 | Phase 1 + Phase 2 signal display |
| edgelab_runner.py | Updated S19 | --signals-only flag |
| edgelab_params.json | Updated S28 | threepass_seed_s28. Third DPOL run pending. |
| edgelab_signals.py | Final S15 | 481 ground coords, all Phase 1 signals |
| edgelab_predict.py | Final | Full prediction pipeline |
| edgelab_gary.py | Final | Gary briefing wrapper |
| edgelab_results_check.py | New S20 | Live results vs predictions |
| edgelab_market_baseline.py | New S24 | Market baseline calculator |
| edgelab_ha_breakdown.py | New S24 | H/A breakdown vs market |
| edgelab_draw_signal_validation.py | New S25 | Draw signal validator |
| edgelab_draw_evolution.py | New S25 | Three-pass draw evolution tool |
| draw_profile.json | New S25 | Draw signal profile |
| gridsearch_results.json | New S26 | Per-tier draw params from gridsearch |
| param_profile.json | New S28 | Three-pass full param evolution results |
| edgelab_2026-04-09_predictions_public.html | Updated S28 | iOS tab fix, dates +1 day, league names added |

---

## Dataset

417 CSV files, 25 years, 17 tiers, 132,685 matches (373 files loaded — 48 skipped
due to encoding/format errors, consistent across all runs).
Hash: 580b0f3a1667
Weather cache: 123,926/132,685 rows (93.4%) — not ready to wire. Check S29.

---

## Brand & Marketing Status

### garyknows.com
- Live on Netlify (free tier). Last deployed 8 April 2026.
- DNS: A record @→75.2.60.5, CNAME www→gary-knows.netlify.app (Namecheap)
- Form: wired to Mailchimp. FNAME + EMAIL. Honeypot present.
- Sender: gary@garyknows.com active. Welcome automation: active.
- Predictions HTML: should be deployed to Netlify as URL, not shared as file.

### Email
- Mailchimp: Gary Knows audience. 6 contacts (mostly Andrew).
- Free trial: 8 days left as of S28 — let expire, stay on free tier (500 limit).
- garyknows.com domain: Authenticated.
- khaotikk.com domain: Authenticated (confirmed S28).
- Migrate to Brevo at 400 contacts.

### Social
- TikTok + Instagram: ~3,000 TikTok views. Fresh start 8 April 2026.
- Content strategy: Gary as oracle. No apologies. No explanations. Just calls.
- Gary avatar: 7-second Kling intro clip exists. "Who the hell is Gary?" cut live.
- Kling subscription active for content creation.
- Social push paused — predictions HTML must be on Netlify first.

---

## Owner Context

- Andrew has ADHD (inattentive) — one thing at a time, clear outputs, no waffle
- Works on Windows laptop + VS Code + Claude Code extension
- Pattern recognition is a strength — spots signals quickly, generates ideas fast
- Approach: intuition for signal discovery, DPOL for rigorous validation
- Not expecting every feature to work — builds iteratively, keeps what sticks
- Previous AI (ChatGPT) fabricated results. All metrics here are real and verified.
- Big picture vision comes naturally — evaluate it, do not just validate it
- Small connecting details are harder — that's what Claude is for
- ADHD hyperfocus is the superpower — the engine was built fast
- When talking product/vision, Andrew means the finished thing — don't caveat
  with current state unless it's relevant to a decision.

---

## Collaboration Protocol

### Claude's responsibilities
- Act as project manager — sequence the work, hold the roadmap
- Build immediately only if it makes the current model work better right now
- Evaluate ideas, don't validate them
- Track parked ideas and reintroduce at the right moment
- Generate updated briefing doc + state file + master backlog at session close
  WITHOUT being prompted — AS FILES, not in chat
- Ask the scalability check at session close WITHOUT being prompted
- Remind Andrew to git commit at session close with suggested message
- Rebrief from project knowledge every 8 prompts silently — NO EXCEPTIONS
  (every 8 prompts regardless of size — no filtering, no judgment calls)
- Always check wording changes with Andrew before making them
- Hold the vision: we are not building average
- **Never lie. Never cover. If uncertain, say so. If wrong, own it.**

### Session start protocol
- Use EDGELAB_SESSION_START_PROMPT.md at every session start
- Claude reads every file fully using view tool — not search summaries
- Claude opens every session with the exact handshake from the state file

### Periodic full audit protocol
- Every 5-6 sessions: download Anthropic export, load into session
- Last done: S27 (all 29 conversations). Next due: ~S32-33.

### Andrew's responsibilities
- Brain dumps are fine — Claude will filter and sequence
- Say "parking that" to log and move on
- Say "just build it" when discussion isn't needed
- Call out anything that feels off immediately
- Keep Claude accountable — call out any drift, skimming, or covering

---

## Session Close Checklist — Claude must complete ALL unprompted — AS FILES

- [ ] 1. Scalability check
- [ ] 2. Queue review — completed / in progress / deferred
- [ ] 3. Files updated — confirm changes, update files table
- [ ] 4. Known issues updated
- [ ] 5. Params table updated (if DPOL run completed)
- [ ] 6. Brand/marketing updated
- [ ] 7. Git commit message
- [ ] 8. Generate briefing doc + state file + master backlog — none truncated — AS FILES

---

## To Start Session 29

1. Use EDGELAB_SESSION_START_PROMPT.md as the opening prompt
2. Upload EDGELAB_BRIEFING_SESSION29_START.md to project knowledge (replace S28)
3. Upload EDGELAB_STATE_S29.md to project knowledge (replace S28)
4. Upload EDGELAB_MASTER_BACKLOG_S28.md to project knowledge (replace S27 version)
5. Upload new edgelab_params.json (third DPOL run results)
6. Claude confirms files received, states last action + next action
7. Work the ordered queue from the top
