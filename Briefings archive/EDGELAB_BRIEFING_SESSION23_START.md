# EdgeLab — Session 23 Briefing (Start)

## What We Are Building

Most sports analytics measures average. Average is what bookmakers price. Average is
what everyone else optimises for. We already beat average — E0 at 50.2%, N1 at 51.6%,
overall at 46.1% on weighted loss run with signals dormant and draw intelligence inactive.

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
**Built in:** 22 sessions.

**Current engine status:** 46.1% overall (weighted loss). 50.2% E0. 51.6% N1.
Signals dormant. Draw intelligence dormant. High-confidence accuracy: 52.9% on first live run.
Market baseline: ~49% (E0).

---

## Session 23 — Start State

### Actions completed in Session 22
- **Weighted loss function** — built and deployed. edgelab_dpol.py updated.
- **Full DPOL re-run (weighted loss)** — started end of S22, still running at close.
- **Weather cache** — 51,000 rows. Bot restarted. Still running.
- **gary@garyknows.com** — Google Workspace user created, signed in, working.
- **Mailchimp sender** — updated to gary@garyknows.com. Automation unpaused.
- **khaotikk.com Mailchimp auth** — DNS records in place, validating (up to 48hrs).
- **Duplicate pick warning** — built into edgelab_acca.py.
- **Gary Upset Picks** — new file edgelab_upset_picks.py built.
- **Master backlog** — EDGELAB_MASTER_BACKLOG.md built from full codebase + all 24 conversations.

### Session continuity protocol — active
- Three documents in project knowledge: briefing doc + state file + master backlog
- Master backlog updated at every session close alongside briefing doc
- Session start handshake: "Last session ended at X. Next action is Y. Anything changed?"
- Context refresh: every 8 substantive exchanges, silently
- Honesty protocol: never cover, never soften, never fabricate

---

## Ordered Work Queue

### Session 23 — priorities in order

1. **Check DPOL weighted loss run results**
   Upload updated edgelab_params.json when run completes.
   Key questions:
   - Did draw intelligence activate on any tier? (draw_pull, w_draw_odds, w_draw_tendency)
   - Did E2 w_form self-correct? (was 0.94 — should drop)
   - Did draw calls increase from 2%?
   - Update accuracy table with new params.

2. **Re-run draw gridsearch**
   Run edgelab_gridsearch.py after weighted loss params confirmed.
   Does draw intelligence now activate?

3. **Signals-only DPOL run**
   After weighted loss params confirmed good.
   Command: `python edgelab_runner.py history/ --tier all --signals-only`
   Do Phase 1 signals activate this time?

4. **Check weather cache row count**
   `python3 -c "import pandas as pd; print(len(pd.read_csv('weather_cache.csv')))"`
   If 132,685: wire into DPOL. If still running: leave it.

5. **Check khaotikk.com Mailchimp authentication**
   Should have resolved within 48hrs of S22. Confirm green.

6. **Clarify instinct_dti_thresh / skew_correction_thresh**
   Built as DPOL hooks but never used. Determine intent or remove.

7. **E1 home bias investigation**
   High DTI matchdays default H. Pattern spotted S21. Investigate.

### Parked — reintroduce at right moment

- **Gary acca picks (product feature)** — Gary builds accas, full pick list shown,
  site-wide selection builder. Not a bet builder. Trigger: Gary live on site.
- **Social comment workflow** — Gary commenting on football pages. One comment, no replies.
  Screenshots of correct calls = content.
- **Underdog effect signal** — park the bus vs high-confidence favourites.
  Pattern: Gent vs KV Mechelen. Trigger: signals active.
- **HeyGen avatar** — Andrew experimenting. Andrew's call.
- **Upset flip Stage 2** — prediction changes on high upset score.
  Trigger: enough Stage 1 logged history to validate.
- **API-Football connection** — needed for injury index, live standings, live odds.
  Pro plan active until May 2026. Schedule before it expires.

---

## Milestone Roadmap

### Milestone 1 — Engine Validated ✅ COMPLETE
Cold engine running, all 17 tiers evolved, predictions live, acca builder working,
Gary briefings live, first live run placed. Done.

### Milestone 2 — The Feedback Loop (IN PROGRESS)
The system must learn from every result, not just historical data.

Components in build order:
1. **Weighted loss function** ✅ BUILT S22 — draw misses penalised 1.5x.
2. **Live results ingestion** — weekend results auto-ingest, not manual.
   edgelab_results_check.py is the foundation. Needs scheduler + storage layer.
3. **Gary call logging** — Gary's predictions stored structurally against each fixture.
4. **Gary post-match analysis** — explicit "why wrong" reasoning logged per miss.
5. **Gary → EdgeLab signal recommendation** — Gary flags a pattern, DPOL tests it.
   Loop closes. The two systems evolve each other.

### Milestone 3 — Consumer Launch (Future)
Gary as a product. App, social, email. Paid tier. Public-facing track record.
Not until Milestone 2 feedback loop is running and accuracy trend is upward.

### Future — Beyond Football
Gary as standalone product + integrated into EdgeLab.
Most comprehensive football/sports statistics platform on earth.
Expand to other sports once DPOL proven. Repeat the formula.
New projects under Khaotikk Ltd.

---

## Live Accuracy Record

| Date | Selections | Stake | Odds | Result |
|------|-----------|-------|------|--------|
| 05/04/2026 | 5-leg safety/result acca | £6.54 | ~16/1 | ✗ 4/5 — KV Mechelen drew 1-1 |

### First Live Run — 5–6 April 2026 (64 predictions matched)

| Metric | Value |
|--------|-------|
| Overall accuracy | 21/64 (32.8%) |
| Weighted accuracy | 43/111 (38.7%) |
| High conf ≥80% | 9/17 (52.9%) |
| Med conf 50–79% | 4/13 (30.8%) |
| Low conf <50% | 8/34 (23.5%) |
| High chaos games | 13/47 (27.7%) |

---

## Known Issues / Active Bugs

- **Draw floor** — D=2% vs real-world ~26%. Weighted loss DPOL run in progress — should fix.
- **E2 overconfidence** — w_form=0.94. Monitor after weighted loss run.
- **E1 home bias** — high DTI matchdays default H. Queue item S23.
- **BTTS/scoreline inconsistency** — Sevilla vs Atletico. BTTS active, engine predicted 0-1. Not fixed.
- **khaotikk.com Mailchimp auth** — validating. Check S23.
- **instinct_dti_thresh / skew_correction_thresh** — built but never used. Clarify S23.

---

## DPOL Status

- --tier all run (flat loss): COMPLETE — 46.1% overall
- --signals-only flag: BUILT S19
- Signal activation run: COMPLETE S21 — no signals activated, all weights 0.0
- Weighted loss function: BUILT S22 ✅
- --tier all run (weighted loss): IN PROGRESS — started end of S22

---

## Evolved Params — Weighted Loss Run (flat loss baseline for comparison)

| Tier | Flat Loss | Weighted Loss |
|------|-----------|---------------|
| E0 | 50.2% | pending |
| E1 | 44.6% | pending |
| E2 | 44.4% | pending |
| E3 | 42.2% | pending |
| EC | 45.1% | pending |
| B1 | 47.3% | pending |
| D1 | 47.6% | pending |
| D2 | 43.6% | pending |
| I1 | 48.5% | pending |
| I2 | 40.6% | pending |
| N1 | 51.6% | pending |
| SC0 | 49.7% | pending |
| SC1 | 44.0% | pending |
| SC2 | 47.1% | pending |
| SC3 | 46.8% | pending |
| SP1 | 48.2% | pending |
| SP2 | 42.6% | pending |
| OVERALL | 46.1% | pending |

**Update weighted loss column when run completes.**

---

## Files

| File | Status | Notes |
|------|--------|-------|
| edgelab_engine.py | Updated S21 | pred_fn writes confidence back to df_window |
| edgelab_dpol.py | **Updated S22** | Weighted loss function in _evaluate_params (draw misses 1.5x) |
| edgelab_gridsearch.py | Updated S21 | Fine-grained continuous search ranges |
| edgelab_acca.py | **Updated S22** | Duplicate pick warning across acca types |
| edgelab_upset_picks.py | **New S22** | Gary upset picks, screenshot-ready output |
| edgelab_databot.py | Updated S17 | All 17 tiers in LEAGUE_MAP |
| edgelab_weather.py | Updated S17 | --batch CLI added |
| edgelab_config.py | Updated S16 | Phase 1 + Phase 2 signal display |
| edgelab_runner.py | Updated S19 | --signals-only flag, signal-safe save logic |
| edgelab_params.json | Updating S23 | Weighted loss run in progress. Upload when complete. |
| edgelab_signals.py | Final S15 | 481 ground coords, all Phase 1 signals |
| edgelab_predict.py | Final | Full prediction pipeline |
| edgelab_gary.py | Final | Gary briefing wrapper |
| edgelab_gary_brain.py | Final | Gary context builder |
| edgelab_gary_context.py | Final | Gary prompt assembler |
| edgelab_results_check.py | New S20 | Live results vs predictions accuracy checker |
| index.html (Gary-knows) | Updated S21 | Form wired to Mailchimp, FNAME field, favicon |
| favicon.png | New S21 | GARY wordmark 64x64 |
| EDGELAB_MASTER_BACKLOG.md | **New S22** | Full project backlog — every idea, signal, feature, bug |

---

## API-Football League IDs

| Tier | ID | Status |
|------|----|--------|
| E0 | 39 | ✓ Verified |
| E1 | 40 | ✓ Verified |
| E2 | 41 | ✓ Verified |
| E3 | 42 | ✓ Verified |
| EC | 43 | ✓ Verified |
| SP1 | 140 | ✓ Confirmed |
| SP2 | 141 | ✓ Confirmed |
| D1 | 78 | ✓ Confirmed |
| D2 | 79 | ✓ Confirmed |
| I1 | 135 | ✓ Confirmed |
| I2 | 136 | ✓ Confirmed |
| N1 | 88 | ✓ Confirmed |
| B1 | 144 | ✓ Confirmed |
| SC0 | 179 | ✓ Verified |
| SC1 | 180 | ✓ Verified live |
| SC2 | 181 | ✓ Verified live |
| SC3 | 182 | ✓ Verified live |

---

## Dataset

417 CSV files, 25 years, 17 tiers, 137,645 matches. Hash: 580b0f3a1667
Weather cache: ~51,000 rows of 132,685. Running.

---

## Brand & Marketing Status

### garyknows.com
- Live on Netlify (free tier). Redeployed 8 April 2026.
- DNS: A record @→75.2.60.5, CNAME www→gary-knows.netlify.app (Namecheap)
- Folder: index.html + favicon.png + preview.png
- To update: drag Gary-knows folder onto Netlify production deploys box.
- Form: wired to Mailchimp. FNAME + EMAIL. Honeypot present.
- Sender: gary@garyknows.com ✅ (fixed S22)
- Welcome automation: active ✅ (unpaused S22)

### Email
- Mailchimp: Gary Knows audience. Free tier limit 500 contacts → migrate to Brevo at 400.
- khaotikk.com domain auth: validating (DNS records added S22, up to 48hrs)

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
- ADHD hyperfocus is the superpower — the engine was built in 10 sessions on phone + laptop
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
- Rebrief from project knowledge every 8 substantive exchanges silently — no exceptions
- Always check wording changes with Andrew before making them
- Hold the vision: we are not building average
- **Never lie. Never cover. If uncertain, say so. If wrong, own it.**

### Session start protocol
- Claude reads briefing doc + state file + master backlog before responding
- Claude opens every session with: "Last session ended at [X]. Next action is [Y]. Anything changed?"

### Andrew's responsibilities
- Brain dumps are fine — Claude will filter and sequence
- Say "parking that" to log and move on
- Say "just build it" when discussion isn't needed
- Call out anything that feels off immediately
- Trust the gut on product and signal ideas — expect Claude to push back on timing
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

## To Start Session 23

1. Upload EDGELAB_BRIEFING_SESSION23_START.md to project knowledge (replace S22)
2. Upload EDGELAB_STATE_S23.md to project knowledge (replace S22)
3. Upload EDGELAB_MASTER_BACKLOG.md to project knowledge (replace S22 version)
4. Upload edgelab_params.json once weighted loss DPOL run completes
5. Claude confirms files received, states last action + next action
6. Work the ordered queue from the top
