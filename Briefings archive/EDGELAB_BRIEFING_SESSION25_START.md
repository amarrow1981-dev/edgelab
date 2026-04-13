# EdgeLab — Session 25 Briefing (Start)

## What We Are Building

Most sports analytics measures average. Average is what bookmakers price. Average is
what everyone else optimises for. We already beat average — E0 at 50.3%, N1 at 51.5%,
overall at 46.2% on weighted loss run with signals dormant and draw intelligence inactive.

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

**Current engine status:** 46.2% overall (weighted loss). 50.3% E0. 51.5% N1.
Signals dormant. Draw intelligence dormant. Score prediction v2 active (venue-split
+ H2H blend). Market baselines established all 17 tiers.

---

## Session 25 — Start State

### Actions completed in Session 24

- **DPOL weighted loss run** — COMPLETE. All 17 tiers evolved. Overall 46.2% (+0.8%).
  No regressions. Signal weights dormant on all 17 tiers.
- **Draw gridsearch** — Run with draw-focused objective (draw +5pp gate, -0.5%
  overall tolerance). E2 minor improvement only. No breakthrough on draw activation.
- **Signals-only DPOL run** — COMPLETE. All signals dormant across all 17 tiers.
  Weighted loss at 1.5x insufficient to activate signals via evolution.
- **Market baselines** — Established for all 17 tiers using B365 implied probability.
  We are behind market on all 17 tiers. H/A only gap is 3-7%.
- **H/A breakdown analysis** — Away accuracy is the primary gap vs market.
  Home accuracy is competitive. Away calls need signals to close the gap.
- **Score prediction v2** — Built and deployed. Venue-split goal tracking + 25% H2H
  blend. Eliminates majority of result/scoreline contradictions.
- **Draw signal discovery** — Score prediction independently produces 26.6% draw-score
  rate matching real-world draw frequency (~26%), independent of DTI. Major finding.
- **Weekly predictions** — Weekend 10-12 April 2026. 139 predictions. 4 upset flags.
  Gary analysis on all 4. Internal + public HTML produced.
- **Bug fixes** — last8_meetings naming (gary_brain.py), weather_load naming (gary_context.py).
- **New acca type** — winner_btts added. Full qualifying picks list in matchday briefing.
- **New scripts** — edgelab_market_baseline.py, edgelab_ha_breakdown.py.

### Session continuity protocol — active
- Three documents in project knowledge: briefing doc + state file + master backlog
- Session start prompt: use EDGELAB_SESSION_START_PROMPT.md at every new session
- Context refresh: every 8 exchanges, silently — NO EXCEPTIONS (every 8, not "substantive")
- Periodic full audit: every 5-6 sessions. Next due ~S28-29.

---

## Ordered Work Queue

### Session 25 — priorities in order

1. **Draw signal validation — score prediction draw rate**
   The score prediction independently produces 26.6% draw-score rate matching
   real-world frequency, independent of DTI. Validate against full 25-year dataset:
   do draw-score matches historically end in draws more often than non-draw-score matches?
   If validated: wire pred_score_draw as a weighted input to draw_score in the engine.

2. **Full DPOL re-run post score prediction v2**
   Score prediction v2 changes expected goals inputs. Revalidate all params.
   Command: `python edgelab_runner.py history/ --tier all`

3. **Sunday predictions — midweek fixtures**
   Standard weekly workflow. See exact commands below.

4. **Check weather cache row count**
   `python3 -c "import pandas as pd; print(len(pd.read_csv('weather_cache.csv')))"`
   Target: 132,685. Wire to DPOL if complete.

5. **Confirm khaotikk.com Mailchimp authentication**
   Should be resolved. Confirm green.

6. **Clarify instinct_dti_thresh / skew_correction_thresh**
   Built as DPOL hooks. Never used. Determine intent or remove.

7. **E1 home bias investigation**
   High DTI matchdays default H. Pattern spotted S21. Investigate.

### Standard weekly workflow (permanent)
- Thursday: predictions for weekend fixtures + accas + Gary upset picks
- Sunday: predictions for midweek fixtures + accas + Gary upset picks
- Results check after each fixture set completes

### Weekly prediction workflow — exact commands

**Step 1 — fetch fixtures (API-Football key required):**
```
python edgelab_databot.py --key YOUR_API_FOOTBALL_KEY --days 4
```
**Step 2 — run predictions:**
```
python edgelab_predict.py --data history/ --fixtures databot_output/YYYY-MM-DD_fixtures.csv --tier all
```
**Step 3 — accas:**
```
python edgelab_acca.py predictions/YYYY-MM-DD_predictions.csv --all-types
```
**Step 4 — upset picks with Gary (Anthropic key required):**
```
python edgelab_upset_picks.py --data history/ --predictions predictions/YYYY-MM-DD_predictions.csv
```
**Step 5 — Gary on specific match:**
```
python edgelab_gary.py --data history/ --home "Team Name" --away "Team Name" --date YYYY-MM-DD --tier E0 --chat
```
Note: DataBot uses API-Football key. Gary uses Anthropic API key. Two separate keys.

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
- Score prediction draw nudge (post-processing) — trigger: draw signal validated first
- Long shot acca — trigger: upset flip Stage 2 validated
- Expand to other sports — trigger: DPOL proven on football

---

## Milestone Roadmap

### Milestone 1 — Engine Validated ✅ COMPLETE
Cold engine running, all 17 tiers evolved, predictions live, acca builder working,
Gary briefings live, first live run placed. Done.

### Milestone 2 — The Feedback Loop (IN PROGRESS)
1. **Weighted loss function** ✅ BUILT S22
2. **Live results auto-ingestion** 🔲
3. **Gary call logging** 🔲
4. **Gary post-match analysis** 🔲
5. **Gary → EdgeLab signal recommendation** 🔲

### Milestone 3 — Consumer Launch (Future)
Not until Milestone 2 feedback loop running and accuracy trend upward.

---

## Live Accuracy Record

| Date | Selections | Stake | Odds | Result |
|------|-----------|-------|------|--------|
| 05/04/2026 | 5-leg safety/result acca | £6.54 | ~16/1 | ✗ 4/5 — KV Mechelen drew 1-1 |

### First Live Run — 5–6 April 2026 (64 predictions matched)

| Metric | Value |
|--------|-------|
| Overall accuracy | 21/64 (32.8%) |
| High conf ≥80% | 9/17 (52.9%) |
| Med conf 50–79% | 4/13 (30.8%) |
| Low conf <50% | 8/34 (23.5%) |

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

**Key insight:** Away accuracy is the primary gap. Home accuracy is competitive.
Signals (travel, motivation, injury) are the fix. Market almost never calls draws either.

---

## Evolved Params — Weighted Loss Run (complete S24)

| Tier | Flat Loss | Weighted Loss |
|------|-----------|---------------|
| E0 | 50.2% | 50.3% |
| E1 | 44.6% | 44.6% |
| E2 | 44.4% | 44.4% |
| E3 | 42.2% | 42.2% |
| EC | 45.1% | 45.2% |
| B1 | 47.3% | 47.3% |
| D1 | 47.1% | 47.6% |
| D2 | 42.0% | 43.9% |
| I1 | 48.1% | 48.5% |
| I2 | 40.6% | 40.9% |
| N1 | 50.5% | 51.5% |
| SC0 | 49.4% | 49.5% |
| SC1 | 43.1% | 44.0% |
| SC2 | 46.9% | 47.1% |
| SC3 | 46.1% | 46.6% |
| SP1 | 46.5% | 48.3% |
| SP2 | 41.0% | 43.0% |
| OVERALL | 45.3% | 46.2% |

Signal weights: all dormant across all 17 tiers.

---

## Weekly Prediction Windows

| Run | Day | Covers | Notes |
|-----|-----|--------|-------|
| Weekend run | Thursday | Fri–Sun fixtures | Larger — most fixtures |
| Midweek run | Sunday | Mon–Wed fixtures | Usually lighter |

---

## Files

| File | Status | Notes |
|------|--------|-------|
| edgelab_engine.py | Updated S24 | compute_score_prediction v2 — venue-split + H2H blend |
| edgelab_dpol.py | Updated S22 | Weighted loss function in _evaluate_params |
| edgelab_gridsearch.py | Updated S24 | Draw-focused objective |
| edgelab_acca.py | Updated S24 | winner_btts type; qualifying picks list |
| edgelab_gary_brain.py | Updated S24 | last8_meetings naming fix |
| edgelab_gary_context.py | Updated S24 | weather_load fix |
| edgelab_upset_picks.py | Built S22 | Gary upset picks, screenshot-ready |
| edgelab_databot.py | Updated S17 | All 17 tiers in LEAGUE_MAP |
| edgelab_weather.py | Updated S17 | --batch CLI |
| edgelab_config.py | Updated S16 | Phase 1 + Phase 2 signal display |
| edgelab_runner.py | Updated S19 | --signals-only flag |
| edgelab_params.json | Updated S24 | Weighted loss params all 17 tiers |
| edgelab_signals.py | Final S15 | 481 ground coords, all Phase 1 signals |
| edgelab_predict.py | Final | Full prediction pipeline |
| edgelab_gary.py | Final | Gary briefing wrapper |
| edgelab_results_check.py | New S20 | Live results vs predictions |
| edgelab_market_baseline.py | New S24 | Market baseline calculator — B365 method |
| edgelab_ha_breakdown.py | New S24 | H/A breakdown vs market per tier |

---

## Dataset

417 CSV files, 25 years, 17 tiers, 137,645 matches. Hash: 580b0f3a1667
Weather cache: running — 82,000/132,685 rows at S24 close.

---

## Brand & Marketing Status

### garyknows.com
- Live on Netlify (free tier). Redeployed 8 April 2026.
- DNS: A record @→75.2.60.5, CNAME www→gary-knows.netlify.app (Namecheap)
- Folder: index.html + favicon.png + preview.png
- To update: drag Gary-knows folder onto Netlify production deploys box.
- Form: wired to Mailchimp. FNAME + EMAIL. Honeypot present.
- Sender: gary@garyknows.com ✅ Welcome automation: active ✅

### Email
- Mailchimp: Gary Knows audience. Free tier limit 500 → migrate to Brevo at 400.
- khaotikk.com domain auth: unconfirmed — check S25.

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
- When talking product/vision, Andrew means the finished thing — don't caveat with
  current state unless it's relevant to a decision.

---

## Collaboration Protocol

### Claude's responsibilities
- Act as project manager — sequence the work, hold the roadmap
- Build immediately only if it makes the current model work better right now
- Evaluate ideas, don't just validate them
- Track parked ideas and reintroduce at the right moment
- Generate updated briefing doc + state file + master backlog at session close WITHOUT being prompted
- Ask the scalability question at session close WITHOUT being prompted
- Remind Andrew to git commit at session close with suggested message
- Rebrief from project knowledge every 8 exchanges silently — NO EXCEPTIONS
  (every 8 exchanges, not "substantive" ones — no filtering, no judgment calls)
- Always check wording changes with Andrew before making them
- Hold the vision: we are not building average
- **Never lie. Never cover. If uncertain, say so. If wrong, own it.**

### Session start protocol
- Use EDGELAB_SESSION_START_PROMPT.md at every session start
- Claude reads every file fully before responding — use view tool, not search summaries
- Claude opens every session with the exact handshake from the state file

### Periodic full audit protocol
- Every 5-6 sessions: download Anthropic export, load into session
- Full review of every idea, decision, workflow
- Next due: approximately S28-29

### Andrew's responsibilities
- Brain dumps are fine — Claude will filter and sequence
- Say "parking that" to log and move on
- Say "just build it" when discussion isn't needed
- Call out anything that feels off immediately
- Keep Claude accountable — call out any drift, skimming, or covering

---

## Session Close Checklist — Claude must complete ALL unprompted

- [ ] 1. Scalability check
- [ ] 2. Queue review — completed / in progress / deferred
- [ ] 3. Files updated — confirm changes, update files table
- [ ] 4. Known issues updated
- [ ] 5. Params table updated (if DPOL run completed)
- [ ] 6. Brand/marketing updated
- [ ] 7. Git commit message
- [ ] 8. Generate briefing doc + state file + master backlog — none truncated

---

## To Start Session 25

1. Use EDGELAB_SESSION_START_PROMPT.md as the opening prompt
2. Upload EDGELAB_BRIEFING_SESSION25_START.md to project knowledge (replace S24)
3. Upload EDGELAB_STATE_S25.md to project knowledge (replace S24)
4. Upload EDGELAB_MASTER_BACKLOG.md to project knowledge (replace S24 version)
5. Claude confirms files received, states last action + next action
6. Work the ordered queue from the top
