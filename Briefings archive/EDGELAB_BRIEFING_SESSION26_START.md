# EdgeLab — Session 26 Briefing (Start)

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
Signals dormant. Draw intelligence dormant but NOW UNDERSTOOD — combination
signal path identified. Score prediction v2 active. SCORE_DRAW_NUDGE removed.

---

## Session 26 — Start State

### Actions completed in Session 25

- **Draw signal validation** — COMPLETE. pred_score_draw has NO SIGNAL.
  p=0.1876, lift +1.1% across 132,685 matches. The 26.6% draw-score rate is
  a mathematical property of Poisson, not a predictor.
- **SCORE_DRAW_NUDGE removed** — from edgelab_engine.py. Was built before
  validation. Not backed by evidence.
- **Draw evolution tool built** — edgelab_draw_evolution.py. Three-pass analysis.
  Pass 1: full pipeline on all 132,685 matches.
  Pass 2: universal signal analysis — odds_draw_prob 1.202x lift, expected_goals_total
  1.088x. All other signals 1.03-1.06x individually.
  Pass 3: combination testing — 120 pairs + 560 triples tested.
  BREAKTHROUGH: combinations up to 1.347x lift (35.5% draw rate vs 26.3% baseline).
  Best: home_draw_rate + odds_draw_prob + form_parity — 888 matches, p=0.0000.
- **draw_profile.json produced** — per-tier suggested draw weights, combination
  results, full signal analysis. Ready for gridsearch seeding.
- **Codebase refactor added to backlog** — all .py files need clean rebuild.
  Trigger: after draw intelligence and signals validated and wired.

### The draw signal discovery — S25 breakthrough

This is the most important finding since the engine was built.

**Individual signals:**
- odds_draw_prob: 1.202x lift — the market implied draw probability is the anchor signal
- expected_goals_total: 1.088x lift — low xG total independently predicts draws
- All other signals 1.03-1.06x — real but too weak to act on alone

**Combination signals (Pass 3):**
Every combination that cleared 1.15x contained odds_draw_prob. The supporting
signals that amplify it most:
- home_draw_rate + odds_draw_prob + form_parity: 1.347x, 888 matches, p=0.0000
- away_form + dti + odds_draw_prob: 1.344x, 1,000 matches, p=0.0000
- away_gd + away_draw_rate + odds_draw_prob: 1.342x, 1,030 matches, p=0.0000
- h2h_draw_rate + odds_draw_prob + expected_goals_diff: 1.306x, 2,825 matches

**Strategic implication:**
DPOL couldn't activate draw intelligence because it was searching for single-signal
weights starting from zero. The draw signal is composite — odds_draw_prob is the
anchor, and the supporting signals amplify it when they align simultaneously.
The fix is: wire expected_goals_total as a new draw signal input, add a composite
gate to draw_score, then seed the gridsearch from draw_profile.json weights
instead of from zero.

### Session continuity protocol — active
- Three documents in project knowledge: briefing doc + state file + master backlog
- Session start prompt: use EDGELAB_SESSION_START_PROMPT.md at every new session
- Context refresh: every 8 exchanges, silently — NO EXCEPTIONS
  (every 8 exchanges — not "substantive" ones — no filtering)
- Periodic full audit: every 5-6 sessions. Next due ~S28-29.

---

## Ordered Work Queue

### Session 26 — priorities in order

1. **Wire draw composite signal into engine**
   a. Add expected_goals_total as a new input to draw_score calculation
   b. Add composite gate: when odds_draw_prob > 0.288 AND any one of
      (form_parity / draw_tendency / h2h_draw_rate) is in draw-positive band,
      apply composite boost to draw_score
   c. Keep strictly pre-match — no post-match data in prediction path
   Spec before build — confirm with Andrew first.

2. **Seed draw gridsearch from draw_profile.json**
   Update edgelab_gridsearch.py to accept seeded starting params from
   draw_profile.json rather than always starting from zero.
   Then run targeted draw gridsearch per tier using the suggested weights.
   Gate: draw accuracy +5pp AND overall accuracy -0.5% maximum.

3. **Full DPOL re-run post score prediction v2 + draw changes**
   Score prediction v2 changed engine inputs. Draw composite changes engine
   further. Full evolution needed to revalidate all params.
   Command: python edgelab_runner.py history/ --tier all

4. **Public HTML qualifying picks tab fix**
   Tab renders but content not showing — div closure issue.
   Needs clean rebuild of tab structure from scratch.

5. **Check weather cache row count**
   Target: 132,685. Wire to DPOL if complete.

6. **Confirm khaotikk.com Mailchimp auth**

7. **Clarify instinct_dti_thresh / skew_correction_thresh**

8. **E1 home bias investigation**

9. **Codebase refactor** — rebuild all .py files cleanly.
   Trigger: after draw intelligence wired and validated. Probably S27-28.

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
| Overall accuracy | 21/64 (32.8%) |
| High conf ≥80% | 9/17 (52.9%) |

---

## Draw Evolution Results — S25 (full detail)

### Individual signals (132,685 matches, all tiers)
| Signal | Lift | p-value | Note |
|--------|------|---------|------|
| odds_draw_prob | 1.202x | 0.0000 | Best band: 0.288–0.712 → 31.6% draw rate |
| expected_goals_total | 1.088x | 0.0000 | Best band: <2.225 → 28.7% draw rate |
| pred_margin | 1.060x | 0.0000 | Weak — too small to act on alone |
| pred_home_goals | 1.056x | 0.0000 | Weak |
| home_gd / away_gd | 1.043–1.055x | 0.0000 | Weak |
| dti | 1.055x | 0.0000 | Weak |
| h2h_draw_rate | 1.053x | 0.0000 | Weak |
| form_parity / gd_parity | 1.046–1.050x | 0.0000 | Weak |
| home/away_draw_rate | 1.030–1.047x | 0.0001 | Weak |
| pred_away_goals | NOT SIGNIFICANT | 0.4040 | No signal |

### Top combination signals (Pass 3)
| Combination | N | Draw Rate | Lift | p |
|-------------|---|-----------|------|---|
| home_draw_rate + odds_draw_prob + form_parity | 888 | 35.5% | 1.347x | 0.0000 |
| away_form + dti + odds_draw_prob | 1,000 | 35.4% | 1.344x | 0.0000 |
| away_gd + away_draw_rate + odds_draw_prob | 1,030 | 35.3% | 1.342x | 0.0000 |
| home_gd + away_draw_rate + odds_draw_prob | 824 | 35.3% | 1.341x | 0.0000 |
| away_draw_rate + odds_draw_prob + pred_home_goals | 1,508 | 35.3% | 1.339x | 0.0000 |
| h2h_draw_rate + odds_draw_prob + expected_goals_diff | 2,825 | 34.4% | 1.306x | 0.0000 |
| dti + home_draw_rate + odds_draw_prob | 1,326 | 34.5% | 1.311x | 0.0000 |

### Per-tier suggested draw weights (from draw_profile.json)
| Tier | w_draw_odds | w_draw_tendency | w_h2h_draw |
|------|------------|-----------------|------------|
| B1 | 0.20 | 0.0 | 0.0 |
| D1 | 0.14 | 0.0 | 0.0 |
| D2 | 0.13 | 0.0 | 0.0 |
| E0 | 0.27 | 0.0 | 0.10 |
| E1 | 0.00 | 0.0 | 0.0 |
| E2 | 0.00 | 0.0 | 0.0 |
| E3 | 0.11 | 0.0 | 0.0 |
| EC | 0.09 | 0.0 | 0.0 |
| I1 | 0.20 | 0.0 | 0.0 |
| I2 | 0.13 | 0.0 | 0.0 |
| N1 | 0.13 | 0.12 | 0.0 |
| SC0 | 0.29 | 0.0 | 0.0 |
| SC1 | 0.08 | 0.0 | 0.0 |
| SC2 | 0.09 | 0.0 | 0.0 |
| SC3 | 0.00 | 0.0 | 0.0 |
| SP1 | 0.20 | 0.0 | 0.11 |
| SP2 | 0.09 | 0.0 | 0.16 |

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

**Key insight:** Away accuracy is the primary gap. Draw calls are the ceiling problem —
both market and EdgeLab rarely call draws, and ~26% of matches draw.

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

Signal weights: all dormant. Draw intelligence: dormant — activation path now clear.

---

## Files

| File | Status | Notes |
|------|--------|-------|
| edgelab_engine.py | Updated S25 | SCORE_DRAW_NUDGE removed |
| edgelab_dpol.py | Updated S22 | Weighted loss function |
| edgelab_gridsearch.py | Updated S24 | Draw-focused objective |
| edgelab_acca.py | Updated S24 | winner_btts; qualifying picks list |
| edgelab_gary_brain.py | Updated S24 | last8_meetings fix |
| edgelab_gary_context.py | Updated S24 | weather_load fix |
| edgelab_upset_picks.py | Built S22 | |
| edgelab_databot.py | Updated S17 | All 17 tiers |
| edgelab_weather.py | Updated S17 | --batch CLI |
| edgelab_config.py | Updated S16 | Phase 1 + Phase 2 signal display |
| edgelab_runner.py | Updated S19 | --signals-only flag |
| edgelab_params.json | Updated S24 | Weighted loss params all 17 tiers |
| edgelab_signals.py | Final S15 | 481 ground coords, all Phase 1 signals |
| edgelab_predict.py | Final | Full prediction pipeline |
| edgelab_gary.py | Final | Gary briefing wrapper |
| edgelab_results_check.py | New S20 | Live results vs predictions |
| edgelab_market_baseline.py | New S24 | Market baseline calculator |
| edgelab_ha_breakdown.py | New S24 | H/A breakdown vs market |
| edgelab_draw_signal_validation.py | New S25 | Draw signal validator — confirmed NO SIGNAL |
| edgelab_draw_evolution.py | New S25 | Three-pass draw evolution tool |
| draw_profile.json | New S25 | Draw signal profile + per-tier suggested weights |

---

## Dataset

417 CSV files, 25 years, 17 tiers, 132,685 matches (373 files loaded — 48 skipped
due to encoding/format errors, consistent across all runs).
Hash: 580b0f3a1667
Weather cache: running — check row count S26.

---

## Brand & Marketing Status

### garyknows.com
- Live on Netlify (free tier). Last deployed 8 April 2026.
- DNS: A record @→75.2.60.5, CNAME www→gary-knows.netlify.app (Namecheap)
- Form: wired to Mailchimp. FNAME + EMAIL. Honeypot present.
- Sender: gary@garyknows.com ✅ Welcome automation: active ✅

### Email
- Mailchimp: Gary Knows audience. Free tier limit 500 → migrate to Brevo at 400.
- khaotikk.com domain auth: unconfirmed — check S26.

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

## To Start Session 26

1. Use EDGELAB_SESSION_START_PROMPT.md as the opening prompt
2. Upload EDGELAB_BRIEFING_SESSION26_START.md to project knowledge (replace S25)
3. Upload EDGELAB_STATE_S26.md to project knowledge (replace S25)
4. Upload EDGELAB_MASTER_BACKLOG.md to project knowledge (replace S25 version)
5. Claude confirms files received, states last action + next action
6. Work the ordered queue from the top
