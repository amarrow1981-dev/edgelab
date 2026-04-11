# EdgeLab — Session 27 Briefing (Start)

## What We Are Building

Most sports analytics measures average. Average is what bookmakers price. Average is
what everyone else optimises for. We already beat average — E0 at 50.8%, N1 at 51.5%,
overall at 46.2% on weighted loss run with signals dormant and draw intelligence
now wired but pending full DPOL validation.

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

**This is not a betting tool. This is the best football brain ever built.**

**Owner:** Andrew Marrow
**Company:** Khaotikk Ltd — khaotikk.com

**Current engine status:** 46.2% overall (weighted loss S24). E0 updated to 50.8% (S26
single-tier DPOL run). Full re-run in progress overnight S26 — results pending S27.
Composite draw signal wired. Gridsearch seeded from draw_profile.json — 16/17 tiers
found draw signal. Draw intelligence activation pending full DPOL re-run.

---

## Session 27 — Start State

### Actions completed in Session 26

- **Composite draw signal wired into engine** — COMPLETE.
  `w_xg_draw` and `composite_draw_boost` added to `EngineParams` and `LeagueParams`.
  Composite gate: `odds_draw_prob > 0.288` AND supporting signal in draw-positive band
  → additive boost to `draw_score`. `expected_goals_total` wired as standalone draw
  signal (1.088x lift). Both start at 0.0 — inert until DPOL activates.
  `make_pred_fn` bridge updated to pass new params through.

- **Gridsearch rebuilt and run — all 17 tiers** — COMPLETE.
  Seeded from draw_profile.json per-tier suggested weights. New params included.
  16/17 tiers passed gate (draw +5pp, overall within -0.5%).
  N1 failed gate — best seen 22.6% draw acc but breached overall tolerance.
  Results saved to gridsearch_results.json.

- **Full DPOL re-run started** — IN PROGRESS. Running overnight.
  E0 single-tier validation: 50.8% (+1.5pp). Same home bias pattern visible —
  draw intelligence not yet active in this run. Full results pending S27.

- **Public HTML qualifying picks tab** — FIXED.
  Full tab system built from scratch: Gary's Picks / All Predictions / Qualifying Picks.
  Search scoped correctly to predictions tab. Qualifying picks populated from acca data.

- **Weather cache checked** — 105,388/132,685 rows (79.4%). Not ready to wire.

- **instinct_dti_thresh / skew_correction_thresh** — CLARIFIED.
  Confirmed unused stubs in LeagueParams and edgelab_params.json.
  Never wired to any logic. Review and decision at codebase refactor (S27-28).

- **E1 home bias** — INVESTIGATED and CONFIRMED.
  E1 predicting H 80.3% of time vs 43.8% actual home wins.
  Confusion matrix: 2,617 away wins misclassified as H (74.5% of all away wins).
  Root cause: home_adv=0.373 with w_form=0.30, w_gd=0.22 — DPOL over-relied on
  home advantage due to weak form/GD signal. Expected to rebalance after full
  DPOL re-run with draw intelligence and new params active.

### The three-pass strategy — S26 milestone

The draw evolution three-pass approach is now partially proven:
- Pass 3 combination signals up to 1.347x lift (confirmed S25)
- Composite signal wired into engine (S26)
- Gridsearch seeded from profile: 16/17 tiers found draw signal (S26)
- Full DPOL rolling window validation: in progress (overnight S26)

If draw accuracy holds under rolling window validation in S27, the case for extending
three-pass to ALL params is proven. That becomes the S27-28 priority.

**Retrospective param evolution philosophy (from S25-26):**
The same three-pass approach can be applied to every param in the engine. Pass 1
predicts pre-match only. Pass 2 identifies which individual params most reliably
preceded correct calls. Pass 3 finds which param combinations together improve
accuracy beyond any single param alone. Full param space ~30-40 candidates,
~10k+ triples — runnable overnight with sensible minimum sample gate.
Potentially the single biggest accuracy improvement available.
**Trigger: draw intelligence proven under DPOL rolling window validation.**

Also logged: previously discarded params should be retested using the three-pass
approach — params that showed no individual signal may behave differently when
their interactions with other params are mapped first.
**Trigger: three-pass proven on draws and validated through full DPOL.**

### Session continuity protocol — active
- Three documents in project knowledge: briefing doc + state file + master backlog
- Session start prompt: use EDGELAB_SESSION_START_PROMPT.md at every new session
- Context refresh: every 8 exchanges — not "substantive" ones — NO EXCEPTIONS
- Periodic full audit: every 5-6 sessions. Next due ~S28-29.

---

## Ordered Work Queue

### Session 27 — priorities in order

1. **Assess full DPOL re-run results**
   Review overnight output across all 17 tiers. Check:
   - Overall accuracy per tier vs S24 baseline
   - Draw intelligence activation (w_xg_draw, composite_draw_boost wired but
     DPOL needs to search these params — confirm they are in the search space)
   - E1 home bias — has home_adv rebalanced?
   - Any tiers that regressed
   Gate: overall accuracy must not drop below S24 baseline on any tier.

2. **Seed draw weights from gridsearch into DPOL**
   gridsearch_results.json has per-tier draw params that cleared the gate.
   Wire these as starting points for DPOL's draw param search.
   Then run targeted draw DPOL pass to validate under rolling window.
   Gate: draw accuracy +5pp AND overall accuracy -0.5% maximum — same as gridsearch.

3. **Confirm new params in DPOL search space**
   Verify edgelab_dpol.py actually searches w_xg_draw and composite_draw_boost
   during evolution. If not in candidate params list, add them.

4. **Public HTML qualifying picks — automate in edgelab_acca.py**
   Currently manually populated in HTML. Needs to be generated automatically.
   The qualifying picks section should write to the public HTML output.

5. **Confirm khaotikk.com Mailchimp auth**
   Still unconfirmed. Check in Mailchimp → Domains.

6. **Weather cache — check row count again**
   Was 105,388 at S26. Target 132,685. Wire to DPOL when complete.

7. **Three-pass full param evolution** — IF draw intelligence proven in items 1-2
   Design and build the full retrospective param evolution tool.
   Extends edgelab_draw_evolution.py philosophy to all ~30-40 engine params.
   Trigger: draw accuracy confirmed under rolling window DPOL validation.

8. **Codebase refactor** — rebuild all .py files cleanly.
   Trigger: after draw intelligence wired, validated, and params confirmed.
   Probably S27-28.

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
- HeyGen avatar — Andrew's call
- Upset flip Stage 2 — trigger: Stage 1 history validated
- API-Football connection — schedule before May 2026 expiry
- Gary temporal awareness — trigger: API-Football connected
- Perplexity Computer — trigger: M3
- DPOL upset-focused evolution — trigger: draw intelligence + signals active
- Score prediction draw nudge — ABANDONED. No signal validated.
- Long shot acca — trigger: upset flip Stage 2 validated
- Expand to other sports — trigger: DPOL proven on football
- Personal web app — trigger: M2 running
- Gary app iOS/Android — trigger: M3
- Three-pass full param evolution — trigger: draw intelligence proven under DPOL
- Retest discarded params via three-pass — trigger: three-pass proven on draws
- instinct_dti_thresh / skew_correction_thresh — review at codebase refactor

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

## Current Accuracy — Post S26 DPOL Run (partial)

| Tier | S24 Weighted Loss | S26 Update | Notes |
|------|------------------|------------|-------|
| E0 | 50.3% | **50.8%** | S26 single-tier run +1.5pp |
| E1 | 44.6% | pending | Full run overnight |
| E2 | 44.4% | pending | |
| E3 | 42.2% | pending | |
| EC | 45.2% | pending | |
| B1 | 47.3% | pending | |
| D1 | 47.6% | pending | |
| D2 | 43.9% | pending | |
| I1 | 48.5% | pending | |
| I2 | 40.9% | pending | |
| N1 | 51.5% | pending | |
| SC0 | 49.5% | pending | |
| SC1 | 44.0% | pending | |
| SC2 | 47.1% | pending | |
| SC3 | 46.6% | pending | |
| SP1 | 48.3% | pending | |
| SP2 | 43.0% | pending | |
| OVERALL | 46.2% | pending | |

Signal weights: all dormant. Draw intelligence: wired S26, activation pending DPOL.

---

## Signal weights — current (from edgelab_params.json post S26)

| Tier | w_form | w_gd | home_adv | draw_margin | w_draw_odds | w_h2h_draw | w_xg_draw | composite_boost |
|------|--------|------|----------|-------------|-------------|------------|-----------|-----------------|
| E0 | 0.4838 | 0.2959 | 0.4437 | 0.12 | 0.0 | 0.0 | 0.0 | 0.0 |
| E1 | 0.3001 | 0.2179 | 0.3733 | 0.145 | 0.0 | 0.0 | 0.0 | 0.0 |
| (others pending overnight run) | | | | | | | | |

Draw params all 0.0 — activation pending DPOL rolling window validation.

---

## Market Baselines — All 17 Tiers (established S24)

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

**Key insight:** Away accuracy is the primary gap. Draw calls are the ceiling problem.
E1 home bias confirmed S26 — engine calling H 80.3% vs 43.8% actual.

---

## Files

| File | Status | Notes |
|------|--------|-------|
| edgelab_engine.py | Updated S26 | w_xg_draw + composite_draw_boost added; composite gate wired; make_pred_fn bridge updated |
| edgelab_dpol.py | Updated S26 | w_xg_draw + composite_draw_boost added to LeagueParams |
| edgelab_gridsearch.py | Updated S26 | Full rebuild — all 17 tiers, seeded from draw_profile.json, new params, --tier flag |
| edgelab_dpol.py | Updated S22 | Weighted loss function |
| edgelab_acca.py | Updated S24 | winner_btts; qualifying picks list |
| edgelab_gary_brain.py | Updated S24 | last8_meetings fix |
| edgelab_gary_context.py | Updated S24 | weather_load fix |
| edgelab_upset_picks.py | Built S22 | |
| edgelab_databot.py | Updated S17 | All 17 tiers |
| edgelab_weather.py | Updated S17 | --batch CLI |
| edgelab_config.py | Updated S16 | Phase 1 + Phase 2 signal display |
| edgelab_runner.py | Updated S19 | --signals-only flag |
| edgelab_params.json | Updated S26 | E0 updated from single-tier run. Full update pending overnight |
| edgelab_signals.py | Final S15 | 481 ground coords, all Phase 1 signals |
| edgelab_predict.py | Final | Full prediction pipeline |
| edgelab_gary.py | Final | Gary briefing wrapper |
| edgelab_results_check.py | New S20 | Live results vs predictions |
| edgelab_market_baseline.py | New S24 | Market baseline calculator |
| edgelab_ha_breakdown.py | New S24 | H/A breakdown vs market |
| edgelab_draw_signal_validation.py | New S25 | Draw signal validator — confirmed NO SIGNAL |
| edgelab_draw_evolution.py | New S25 | Three-pass draw evolution tool |
| draw_profile.json | New S25 | Draw signal profile + per-tier suggested weights |
| edgelab_2026-04-09_predictions_public.html | Updated S26 | Tab system fixed, search fixed, qualifying picks tab added |

---

## Dataset

417 CSV files, 25 years, 17 tiers, 132,685 matches (373 files loaded — 48 skipped
due to encoding/format errors, consistent across all runs).
Hash: 580b0f3a1667
Weather cache: 105,388/132,685 rows (79.4%) — not ready to wire.

---

## Brand & Marketing Status

### garyknows.com
- Live on Netlify (free tier). Last deployed 8 April 2026.
- DNS: A record @→75.2.60.5, CNAME www→gary-knows.netlify.app (Namecheap)
- Form: wired to Mailchimp. FNAME + EMAIL. Honeypot present.
- Sender: gary@garyknows.com ✅ Welcome automation: active ✅

### Email
- Mailchimp: Gary Knows audience. Free tier limit 500 → migrate to Brevo at 400.
- khaotikk.com domain auth: unconfirmed — check S27.

### Social
- TikTok + Instagram: ~3,000 TikTok views. Fresh start 8 April 2026.
- Content strategy: Gary as oracle. No apologies. No explanations. Just calls.

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
- Evaluate ideas, don't just validate them
- Track parked ideas and reintroduce at the right moment
- Generate updated briefing doc + state file + master backlog at session close
  WITHOUT being prompted — AS FILES, not in chat
- Ask the scalability question at session close WITHOUT being prompted
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
- Next due: approximately S28-29

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

## To Start Session 27

1. Use EDGELAB_SESSION_START_PROMPT.md as the opening prompt
2. Upload EDGELAB_BRIEFING_SESSION27_START.md to project knowledge (replace S26)
3. Upload EDGELAB_STATE_S27.md to project knowledge (replace S26)
4. Upload EDGELAB_MASTER_BACKLOG.md to project knowledge (replace S26 version)
5. Claude confirms files received, states last action + next action
6. Work the ordered queue from the top
