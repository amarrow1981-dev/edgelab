# EdgeLab — Session 28 Briefing

## What We Are Building

Most sports analytics measures average. Average is what bookmakers price. Average is
what everyone else optimises for. We already beat average — E0 at 50.8%, N1 at 53.2%,
overall at 46.5% on weighted loss run with draw intelligence now seeded across 9 tiers
and a second full DPOL evolution running overnight S27.

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

**Current engine status:** 46.5% overall (S27 DPOL run). E0: 50.8%, N1: 53.2%.
Draw intelligence live on 9/16 tiers (draw_seed_s27). Second full DPOL run running
overnight S27 with seeded draw params as starting points — results pending S28.

---

## Session 28 — Start State

### Actions completed in Session 27

- **Full Anthropic export audit** — COMPLETE.
  All 29 conversations read (sessions 1–27). Backlog updated with every gap:
  Gary avatar design, addiction detection layer, team affiliation onboarding,
  regional accent/persona tiers, weekly longshot (charity edition), selection builder,
  Stage 2 draw rate strategy, social content pipeline, Kling subscription noted.
  Periodic audit count reset — next due ~S32-33.

- **Full DPOL re-run assessed** — COMPLETE.
  46.5% overall (+0.7pp vs S24 baseline of 45.8%). No regressions across 17 tiers.
  14 tiers improved, 3 held flat (E1, D1, SC3).
  Standouts: N1 +1.7pp (53.2%), I2 +1.5pp, SP2 +1.5pp, B1 +1.3pp.
  E1 home bias structurally improved: home_adv 0.373→0.272, w_form 0.30→0.25.
  w_score_margin activated on 13/17 tiers.

- **w_xg_draw + composite_draw_boost added to DPOL search space** — COMPLETE.
  Both params were missing from _generate_candidates in edgelab_dpol.py.
  Now added — DPOL will search them from S28 onwards.

- **Draw weights seeded from gridsearch — 9/16 tiers saved** — COMPLETE.
  edgelab_draw_dpol_seed.py built and run. Seeds gridsearch draw weights into
  current evolved params, gate-validates (draw +5pp AND overall within -0.5%).
  9 tiers passed: EC, B1, D1, D2, SC0, SC1, SC2, SP1, SP2.
  7 tiers failed gate at exactly -0.5% overall: E0, E1, E2, E3, I1, I2, SC3.
  Draw intelligence now live on 9 tiers for the first time.
  Failure pattern: signal is real (+13.5pp draw on E0) but cost to H/A just over limit.
  Second DPOL run should find the balance — it starts from seeded draw weights.

- **Second full DPOL run started overnight** — IN PROGRESS.
  Runs with seeded draw params as starting points. DPOL can now search
  w_xg_draw and composite_draw_boost. Should find balance for 7 failing tiers
  and improve further on 9 passing ones.

- **Stage 2 draw rate strategy discussed and parked** — LOGGED.
  Post-result analysis only. No dependency on predictions. Log draw_score per match.
  Use 25-27% band as sanity check not target. Feed misses back into signal weights.
  Trigger: three-pass proven on draws.

### The three-pass strategy — S27 milestone

Draw intelligence is now live on 9 tiers. Second DPOL run running overnight.
Trigger condition for three-pass full param evolution: draw intelligence confirmed
under rolling window validation (both the 9 seeded tiers AND resolution of the 7
failing tiers).

**Trigger check at S28 open: assess overnight DPOL results. If draw confirmed
across all/most tiers, three-pass is the immediate next build.**

### Session continuity protocol — active
- Three documents in project knowledge: briefing doc + state file + master backlog
- Session start prompt: use EDGELAB_SESSION_START_PROMPT.md at every new session
- Context refresh: every 8 exchanges — not "substantive" ones — NO EXCEPTIONS
- Periodic full audit: every 5-6 sessions. Last done S27. Next due ~S32-33.

---

## Ordered Work Queue

### Session 28 — priorities in order

1. **Assess second DPOL overnight run results**
   Upload new edgelab_params.json. Check:
   - Did the 7 failing tiers (E0, E1, E2, E3, I1, I2, SC3) find their draw balance?
   - Did the 9 seeded tiers improve further?
   - Overall accuracy — must not regress below S27 DPOL baseline on any tier
   - I1/I2 draw overcalling — were weights tuned to sensible levels?
   Gate: draw intelligence confirmed under rolling window = three-pass trigger met.

2. **Three-pass full param evolution** — IF draw confirmed in item 1
   Design and build the full retrospective param evolution tool.
   Extends edgelab_draw_evolution.py philosophy to all ~30-40 engine params.
   Pass 1: predict pre-match only. Pass 2: single-param retrospective.
   Pass 3: combination testing (~10k+ triples). Runnable overnight.
   Potentially the single biggest accuracy improvement available.
   Trigger: draw intelligence confirmed under rolling window DPOL validation.

3. **Public HTML qualifying picks — automate in edgelab_acca.py**
   Currently manually populated. Wire edgelab_acca.py output to public HTML.
   Qualifying picks section should write automatically on each prediction run.

4. **Confirm khaotikk.com Mailchimp auth**
   Check Mailchimp → Domains. Unconfirmed since S20.

5. **Weather cache — check row count**
   Was 105,388/132,685 (79.4%) at S26. Check if run has progressed.
   Wire to DPOL when complete (132,685 target).

6. **iOS Safari HTML fix**
   Tab switching and search unresponsive on iPhone. Android works.
   Fix: add onkeyup + onchange fallbacks alongside oninput on search input.

7. **Date labelling bug — investigate**
   Fixtures appearing a day early in HTML output. Root cause unconfirmed.
   Likely in acca.py date conversion or DataBot UTC handling.

8. **Market baseline refresh**
   Run edgelab_market_baseline.py. Update market baseline table.
   Currently S24 numbers. Add to standard post-DPOL checklist going forward.

9. **Codebase refactor** — trigger: draw intelligence wired, validated, params confirmed.

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
- Gary avatar / HeyGen — Kling subscription active, 7-sec intro clip exists. Trigger: M3
- Upset flip Stage 2 — trigger: enough logged Stage 1 history to validate first
- API-Football connection — schedule before May 2026 expiry
- Gary temporal awareness — trigger: API-Football connected
- Perplexity Computer — trigger: M3
- DPOL upset-focused evolution — trigger: draw intelligence + signals active
- Score prediction draw nudge — ABANDONED. No signal validated.
- Long shot acca — trigger: upset flip Stage 2 validated
- Gary's Weekly Longshot (charity edition) — trigger: upset flip Stage 2 validated
- Expand to other sports — trigger: DPOL proven on football
- Personal web app — trigger: M2 running
- Gary app iOS/Android — trigger: M3
- Three-pass full param evolution — trigger: draw confirmed under DPOL (check S28 item 1)
- Retest discarded params via three-pass — trigger: three-pass proven on draws
- instinct_dti_thresh / skew_correction_thresh — review at codebase refactor
- Stage 2 draw rate strategy (25-27% band, post-result only) — trigger: three-pass proven
- Gary onboarding — team affiliation — trigger: M3
- Gary accent / regional persona — trigger: M3
- Gary behavioural addiction detection — trigger: M3
- Selection builder (on-site) — trigger: M3
- Cryptocurrency payment options — trigger: M3 paid tier
- Countdown clock on landing page — trigger: launch date confirmed

---

## Milestone Roadmap

### Milestone 1 — Engine Validated ✅ COMPLETE

### Milestone 2 — The Feedback Loop (IN PROGRESS)
1. **Weighted loss function** ✅ BUILT S22
2. **Live results auto-ingestion** 🔲
3. **Gary call logging** 🔲
4. **Gary post-match analysis** 🔲
5. **Gary → EdgeLab signal recommendation** 🔲

### Milestone 3 — Consumer Launch (Future)

---

## Live Accuracy Record

| Date | Selections | Stake | Odds | Result |
|------|-----------|-------|------|--------|
| 05/04/2026 | 5-leg safety/result acca | £6.54 | ~16/1 | ✗ 4/5 — KV Mechelen drew 1-1 |

### First Live Run — 5–6 April 2026 (64 predictions matched)
| Metric | Value |
|--------|-------|
| Predictions matched to results | 64 |
| Correct | 33 |
| Accuracy | 51.6% |
| H correct | 26/41 (63.4%) |
| D correct | 1/9 (11.1%) |
| A correct | 6/14 (42.9%) |

---

## Current Accuracy — Post S27

| Tier | S24 Baseline | S27 DPOL | Draw Seed Status | Notes |
|------|-------------|----------|-----------------|-------|
| E0 | 50.3% | 50.8% | dormant — gate -0.5% | Draw signal real (+13.5pp) but cost marginal |
| E1 | 44.6% | 44.6% | dormant — gate -0.5% | Home bias improved structurally |
| E2 | 44.4% | 44.5% | dormant — gate -0.5% | |
| E3 | 42.2% | 42.9% | dormant — gate -0.5% | |
| EC | 45.2% | 45.5% | LIVE 44.7% draw_acc 7.2% | |
| B1 | 47.3% | 48.6% | LIVE 47.7% draw_acc 8.7% | |
| D1 | 47.6% | 47.6% | LIVE 47.2% draw_acc 9.6% | |
| D2 | 43.9% | 44.7% | LIVE 44.0% draw_acc 13.2% | |
| I1 | 48.5% | 49.6% | dormant — gate -0.6% | Overcalling draws 26.4% at these weights |
| I2 | 40.9% | 42.4% | dormant — gate -0.5% | Overcalling draws 38.7% at these weights |
| N1 | 51.5% | 53.2% | N/A excluded by design | |
| SC0 | 49.5% | 50.2% | LIVE 49.2% draw_acc 14.4% | |
| SC1 | 44.0% | 44.2% | LIVE 43.9% draw_acc 9.5% | |
| SC2 | 47.1% | 47.7% | LIVE 46.9% draw_acc 6.6% | |
| SC3 | 46.6% | 46.6% | dormant — gate -0.5% | |
| SP1 | 48.3% | 49.1% | LIVE 47.5% draw_acc 17.8% | |
| SP2 | 43.0% | 44.5% | LIVE 44.1% draw_acc 21.0% | |
| OVERALL | 45.8% | 46.5% | pending overnight run | |

Second DPOL run overnight will update all figures.

---

## Signal weights — current (post S27)

| Tier | w_form | w_gd | home_adv | draw_margin | w_draw_odds | w_draw_tend | w_h2h_draw | w_xg_draw | comp_boost |
|------|--------|------|----------|-------------|-------------|-------------|------------|-----------|------------|
| E0 | 0.457 | 0.267 | 0.422 | 0.120 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| E1 | 0.253 | 0.141 | 0.272 | 0.145 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| E2 | 0.796 | 0.506 | 0.483 | 0.120 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| E3 | 0.272 | 0.175 | 0.148 | 0.126 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| EC | 0.772 | 0.181 | 0.325 | 0.108 | 0.10 | 0.0 | 0.05 | 0.20 | 0.10 |
| B1 | 0.633 | 0.306 | 0.365 | 0.120 | 0.18 | 0.05 | 0.10 | 0.10 | 0.15 |
| D1 | 0.658 | 0.295 | 0.261 | 0.120 | 0.19 | 0.10 | 0.05 | 0.10 | 0.15 |
| D2 | 0.619 | 0.137 | 0.415 | 0.114 | 0.03 | 0.0 | 0.0 | 0.20 | 0.10 |
| I1 | 0.697 | 0.340 | 0.302 | 0.120 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| I2 | 0.526 | 0.197 | 0.248 | 0.114 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| N1 | 0.479 | 0.222 | 0.297 | 0.120 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| SC0 | 1.073 | 0.329 | 0.214 | 0.120 | 0.24 | 0.05 | 0.10 | 0.10 | 0.10 |
| SC1 | 0.535 | 0.297 | 0.304 | 0.120 | 0.10 | 0.05 | 0.0 | 0.15 | 0.15 |
| SC2 | 0.755 | 0.327 | 0.273 | 0.120 | 0.05 | 0.05 | 0.0 | 0.20 | 0.15 |
| SC3 | 0.847 | 0.310 | 0.275 | 0.120 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| SP1 | 0.459 | 0.218 | 0.320 | 0.120 | 0.26 | 0.0 | 0.01 | 0.15 | 0.10 |
| SP2 | 0.314 | 0.157 | 0.375 | 0.120 | 0.10 | 0.0 | 0.06 | 0.05 | 0.10 |

Draw params 0.0 = dormant. Non-zero = seeded draw_seed_s27, being tuned by overnight DPOL run.

---

## Market Baselines — All 17 Tiers (S24 — refresh due S28)

| Tier | Mkt Overall | Mkt H/A Only | EdgeLab Overall | EdgeLab H/A Only | Gap (H/A) |
|------|------------|--------------|-----------------|------------------|-----------|
| E0 | 54.7% | 72.2% | 50.3% | 66.5% | -5.7% |
| E1 | 46.6% | 64.0% | 44.6% | 61.1% | -2.9% |
| E2 | 47.7% | 64.7% | 44.4% | 60.2% | -4.5% |
| E3 | 45.2% | 62.0% | 42.2% | 57.6% | -4.4% |
| EC | 48.2% | 65.1% | 45.2% | 61.0% | -4.1% |
| B1 | 52.5% | 70.2% | 47.3% | 63.2% | -7.0% |
| D1 | 51.8% | 68.9% | 47.6% | 63.4% | -5.5% |
| D2 | 47.2% | 64.8% | 43.9% | 60.3% | -4.5% |
| I1 | 54.4% | 73.5% | 48.5% | 66.0% | -7.5% |
| I2 | 45.8% | 66.2% | 40.9% | 59.9% | -6.3% |
| N1 | 56.2% | 73.4% | 51.5% | 67.3% | -6.1% |
| SC0 | 52.9% | 70.0% | 49.5% | 65.4% | -4.6% |
| SC1 | 47.5% | 65.4% | 44.0% | 60.5% | -4.9% |
| SC2 | 50.4% | 65.0% | 47.1% | 61.0% | -4.0% |
| SC3 | 49.4% | 63.5% | 46.6% | 59.8% | -3.7% |
| SP1 | 53.6% | 71.5% | 48.3% | 64.5% | -7.0% |
| SP2 | 46.8% | 65.9% | 43.0% | 60.8% | -5.1% |

**NOTE: S24 numbers. Run edgelab_market_baseline.py at S28 and update this table.**
Away accuracy is the primary gap. Draw calls are the ceiling problem.

---

## Files

| File | Status | Notes |
|------|--------|-------|
| edgelab_engine.py | Updated S26 | w_xg_draw + composite_draw_boost added; composite gate wired; make_pred_fn bridge updated |
| edgelab_dpol.py | Updated S27 | w_xg_draw + composite_draw_boost added to _generate_candidates |
| edgelab_gridsearch.py | Updated S26 | Full rebuild — all 17 tiers, seeded from draw_profile.json, new params, --tier flag |
| edgelab_draw_dpol_seed.py | New S27 | Seeds gridsearch draw weights, gate-validates, saves passing tiers |
| edgelab_acca.py | Updated S24 | winner_btts; qualifying picks list |
| edgelab_gary_brain.py | Updated S24 | last8_meetings fix |
| edgelab_gary_context.py | Updated S24 | weather_load fix |
| edgelab_upset_picks.py | Built S22 | |
| edgelab_databot.py | Updated S17 | All 17 tiers |
| edgelab_weather.py | Updated S17 | --batch CLI |
| edgelab_config.py | Updated S16 | Phase 1 + Phase 2 signal display |
| edgelab_runner.py | Updated S19 | --signals-only flag |
| edgelab_params.json | Updated S27 | S27 DPOL run + draw seed 9 tiers. Full update pending overnight. |
| edgelab_signals.py | Final S15 | 481 ground coords, all Phase 1 signals |
| edgelab_predict.py | Final | Full prediction pipeline |
| edgelab_gary.py | Final | Gary briefing wrapper |
| edgelab_results_check.py | New S20 | Live results vs predictions |
| edgelab_market_baseline.py | New S24 | Market baseline calculator — REFRESH DUE S28 |
| edgelab_ha_breakdown.py | New S24 | H/A breakdown vs market |
| edgelab_draw_signal_validation.py | New S25 | Draw signal validator — confirmed NO SIGNAL |
| edgelab_draw_evolution.py | New S25 | Three-pass draw evolution tool |
| draw_profile.json | New S25 | Draw signal profile + per-tier suggested weights |
| gridsearch_results.json | New S26 | Per-tier draw params that cleared gate |
| edgelab_2026-04-09_predictions_public.html | Updated S26 | Tab system fixed, search fixed, qualifying picks tab added |

---

## Dataset

417 CSV files, 25 years, 17 tiers, 132,685 matches (373 files loaded — 48 skipped
due to encoding/format errors, consistent across all runs).
Hash: 580b0f3a1667
Weather cache: 105,388/132,685 rows (79.4%) — not ready to wire. Check S28.

---

## Brand & Marketing Status

### garyknows.com
- Live on Netlify (free tier). Last deployed 8 April 2026.
- DNS: A record @→75.2.60.5, CNAME www→gary-knows.netlify.app (Namecheap)
- Form: wired to Mailchimp. FNAME + EMAIL. Honeypot present.
- Sender: gary@garyknows.com ✅ Welcome automation: active ✅

### Email
- Mailchimp: Gary Knows audience. Free tier limit 500 → migrate to Brevo at 400.
- khaotikk.com domain auth: unconfirmed — check S28.

### Social
- TikTok + Instagram: ~3,000 TikTok views. Fresh start 8 April 2026.
- Content strategy: Gary as oracle. No apologies. No explanations. Just calls.
- Gary avatar: 7-second Kling intro clip exists. "Who the hell is Gary?" cut live.
- Kling subscription active for content creation.

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
- Rebrief from project knowledge every 8 exchanges silently — NO EXCEPTIONS
  (every 8 exchanges — not "substantive" ones — no filtering, no judgment calls)
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

## To Start Session 28

1. Use EDGELAB_SESSION_START_PROMPT.md as the opening prompt
2. Upload EDGELAB_BRIEFING_SESSION28_START.md to project knowledge (replace S27)
3. Upload EDGELAB_STATE_S28.md to project knowledge (replace S27)
4. Upload EDGELAB_MASTER_BACKLOG.md to project knowledge (replace S27 version)
5. Upload new edgelab_params.json (overnight DPOL run results)
6. Claude confirms files received, states last action + next action
7. Work the ordered queue from the top
