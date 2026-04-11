# EdgeLab — Session 21 Briefing (Final)

## What We Are Building

Most sports analytics measures average. Average is what bookmakers price. Average is
what everyone else optimises for. We already beat average — E0 at 50.2%, N1 at 51.4%,
overall at 45.9% on a cold engine with signals dormant and draw intelligence inactive.

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

**This is not a betting tool. This is the best football brain ever built.**

**Owner:** Andrew Marrow
**Company:** Khaotikk Ltd — khaotikk.com
**Built in:** 11 sessions on a phone and a laptop.

**Current engine status:** 45.9% overall. 50.2% E0. 51.4% N1. Signals dormant.
Draw intelligence dormant. High-confidence accuracy: 52.9% on first live run.
Market baseline: ~49% (E0).

---

## Session 21 — What Got Done

### Engine
- **Signals-only run confirmed** — completed from S19. No Phase 1 or Phase 2 signals
  activated. All weights remain 0.0. Expected — weather cache incomplete, signals need
  full data to find correlation.
- **Weather cache** — confirmed running. 52,000 rows at session start (target 132,685).
  Left running overnight. Check cache size next session.
- **Draw intelligence investigation** — gridsearch re-run with fine-grained continuous
  search (0.01 threshold steps, 0.25–0.55 range, ~1,800 combos per tier).
  Zero improvement on E1/E2/E3/EC. Root cause confirmed: DPOL optimises flat accuracy,
  so calling more draws trades H/A correct calls for D correct calls at net loss.
  Draw floor and weighted loss function are the same problem. Fix loss function first,
  then re-run gridsearch.
- **Gridsearch upgraded** — now uses continuous fine-grained ranges. Finds optimal
  values itself rather than straddling the sweet spot between hand-picked steps.
- **Weighted loss function BUILT** ✅ — Milestone 2, item 1 complete.
  `_evaluate_params` in `edgelab_dpol.py` now scores per match:
    - Correct call → +1.0
    - Wrong, conf <50% → -0.5
    - Wrong, conf 50–79% → -1.0
    - Wrong, conf ≥80% → -3.0
  Normalised to 0–1 range. Compatible with existing min_improvement thresholds.
- **Confidence wiring** — `make_pred_fn` in `edgelab_engine.py` now writes confidence
  back into df_window so DPOL weighted loss can read it per match.
- **DPOL re-evolution run started** — `python edgelab_runner.py --tier all history/`
  running locally at session close under new weighted loss function. Status unknown.
- **E2 overconfidence diagnosed** — w_form=0.898 and w_gd=0.533 are 2x higher than
  E1. Engine trusts numbers too hard in a chaotic league. Weighted loss function should
  naturally suppress this during re-evolution. Monitor E2 params in new run output.

### Website & Marketing
- **Landing page form fixed** — `handleSubmit()` was completely fake since S19.
  Showed success message but never submitted to Mailchimp. Now wires via hidden
  iframe POST to Mailchimp action URL. This is on Claude — missed in S19 build.
- **FNAME field added** — "your name" input added above email. Maps to FNAME merge tag.
- **Welcome automation fixed** — was paused after S19 editing, never re-activated.
  Confirmed firing after fix. Trigger: Contact signs up to Gary Knows audience.
- **Favicon added** — GARY wordmark 64x64 PNG now shows in browser tab on garyknows.com.
- **garyknows.com redeployed** — index.html + favicon.png + preview.png. Live 8 April.
- **Lost signups** — unknown number of TikTok/Instagram viewers signed up before form
  fix. Site showed success, nothing reached Mailchimp. Unrecoverable.
  Post on socials: ask anyone who signed up before 8 April and heard nothing to
  sign up again at garyknows.com.
- **Sender email** — gary@garyknows.com blocked. Google Workspace setup incomplete —
  verification email sent to non-existent address during signup.
  Temporary fix: Gary@khaotikk.com. Resolve properly S22.

### Social
- TikTok: ~3,000 views across 3 posts (one boosted) as of session 21.
  No conversion data before form fix. Fresh start from 8 April 2026.

### Scalability Check — Session 21
- Nothing built this session creates a scaling problem.
- Weighted loss function adds minimal overhead per DPOL evaluation.
- Mailchimp free tier: headroom to ~400 contacts, then migrate to Brevo.
- Watch: DPOL run time will increase as signal candidate sets grow. Flag if runs
  exceed ~30 minutes.

---

## Ordered Work Queue

### Session 22 — priorities in order

1. **Check DPOL re-evolution run** — did it complete? Upload updated edgelab_params.json.
   Check E2 params: did w_form and w_gd drop? Did draw_margin widen?
   Re-run draw gridsearch on new params — does draw intelligence now activate?
2. **Check weather cache** — how many rows now? If complete (132,685), wire into DPOL
   for weather signal activation test.
3. **Fix gary@garyknows.com** — resolve Google Workspace verification or start fresh.
   Update Mailchimp sender address once resolved.
4. **Lost signups social post** — TikTok + Instagram. Ask anyone who signed up before
   8 April and heard nothing to sign up again at garyknows.com.
5. **Duplicate pick warning in acca builder** — flag if same match appears in more
   than one acca type.
6. **Gary's Upset Picks output** — filtered report, upset flags only, Gary commentary
   on each pick, screenshot-ready format for social.

---

## Milestone Roadmap

### Milestone 1 — Engine Validated ✅ COMPLETE
Cold engine running, all 17 tiers evolved, predictions live, acca builder working,
Gary briefings live, first moist run placed. Done.

### Milestone 2 — The Feedback Loop (IN PROGRESS)
The system must learn from every result, not just historical data.

Components in build order:
1. **Weighted loss function** ✅ BUILT S21 — DPOL punishes confident wrong calls 3x.
2. **Live results ingestion** — weekend results auto-ingest, not manual.
   edgelab_results_check.py is the foundation. Needs scheduler + storage layer.
3. **Gary call logging** — Gary's predictions stored structurally against each fixture.
   What he said, what happened, confidence, chaos, outcome. Persisted, not just printed.
4. **Gary post-match analysis** — explicit "why wrong" reasoning logged per miss.
5. **Gary → EdgeLab signal recommendation** — Gary flags a pattern from post-match
   analysis. DPOL tests it. Loop closes. The two systems evolve each other.

### Milestone 3 — Consumer Launch (Future)
Gary as a product. App, social, email. Paid tier. Public-facing track record.
Not until Milestone 2 feedback loop is running and accuracy trend is upward.

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

Key insight: high-confidence calls already beat the market. The drag is low-confidence
high-chaos calls and dormant draw intelligence. Weighted loss function now targets both.

---

## Known Issues / Active Bugs

- **Draw floor** — D=4 from 199 predictions (2%). Real-world ~26%.
  Gridsearch confirmed: draw weights won't activate under flat loss function.
  Weighted loss function now live — re-run gridsearch after DPOL re-evolution.
- **E2 overconfidence** — 5/8 notable misses are League One. w_form/w_gd too high.
  Weighted loss function should self-correct during re-evolution. Monitor.
- **E1 home bias** — high DTI matchdays default H. Investigate S22+.
- **Signal activation** — all Phase 1 + Phase 2 weights at 0.0.
  Re-evolution run started S21 under weighted loss. Check next session.
- **BTTS/scoreline inconsistency** — BTTS flag inconsistent with scoreline pred.
  Sevilla vs Atletico: engine predicted 0-1 but BTTS active. Logged S19.
- **Sender email** — Mailchimp sending from Gary@khaotikk.com. Fix S22.
- **Duplicate acca picks** — no warning when same match appears in multiple accas.

---

## DPOL Status

- --tier all run (flat loss): COMPLETE — all 17 tiers evolved, params saved
- --signals-only flag: BUILT S19
- Signal activation run: COMPLETE S21 — no signals activated, all weights 0.0
- Weighted loss function: BUILT S21 ✅
- --tier all run (weighted loss): STARTED S21 — running locally, status unknown

---

## Evolved Params — Last Known Good (flat loss function)

| Tier | Accuracy |
|------|---------|
| E0 | 50.2% |
| E1 | 44.7% |
| E2 | 44.5% |
| E3 | 42.2% |
| EC | 44.9% |
| B1 | 47.1% |
| D1 | 47.6% |
| D2 | 42.3% |
| I1 | 48.6% |
| I2 | 40.5% |
| N1 | 51.4% |
| SC0 | 49.6% |
| SC1 | 43.3% |
| SC2 | 47.1% |
| SC3 | 46.4% |
| SP1 | 47.9% |
| SP2 | 41.4% |
| OVERALL | 45.9% |

Signal weights: all 0.0. New weighted loss run in progress — update table S22.

---

## Acca Builder

Two-stage process. Standalone module. Takes predictions CSV as input.

Stage 1 — filters: conf ≥52%, LOW/MED chaos, no upset flag.
Stage 2 — best decorrelated combination. Penalises same-tier same-day pairs.

Five acca types: result, safety, value, upset, BTTS.
Safety acca — lowest combined odds, HIGH conviction gate (≥65%).
Known issue: no duplicate pick warning across acca types. Queue item S22.

```bash
python edgelab_acca.py predictions/2026-04-05_predictions.csv --all-types
```

---

## Weather Bot

Open-Meteo API. Free, no key required. Historical + forecast auto-detected.

```bash
python edgelab_weather.py --batch history/ --output weather_cache.csv
```

Weather load signal (0–1): rain 50% weight, wind 35%, temperature 15%.
Cache: ~52,000 rows of 132,685. Still running. Leave overnight.
Missing coords: Bristol Rvs, Oxford, AFC Wimbledon, Crawley, Carlisle — add later.

---

## Files

| File | Status | Notes |
|------|--------|-------|
| edgelab_engine.py | Updated S21 | pred_fn writes confidence back to df_window |
| edgelab_dpol.py | Updated S21 | Weighted loss function in _evaluate_params |
| edgelab_gridsearch.py | Updated S21 | Fine-grained continuous search ranges |
| edgelab_acca.py | Updated S19 | Safety acca fixed |
| edgelab_databot.py | Updated S17 | All 17 tiers in LEAGUE_MAP |
| edgelab_weather.py | Updated S17 | --batch CLI added |
| edgelab_config.py | Updated S16 | Phase 1 + Phase 2 signal display |
| edgelab_runner.py | Updated S19 | --signals-only flag, signal-safe save logic |
| edgelab_params.json | S21 in progress | Update when weighted loss run completes |
| edgelab_signals.py | Final S15 | 481 ground coords, all Phase 1 signals |
| edgelab_predict.py | Final | Full prediction pipeline |
| edgelab_gary.py | Final | Gary briefing wrapper |
| edgelab_gary_brain.py | Final | Gary context builder |
| edgelab_results_check.py | New S20 | Live results vs predictions accuracy checker |
| index.html (Gary-knows) | Updated S21 | Form wired to Mailchimp, FNAME field, favicon |
| favicon.png | New S21 | GARY wordmark 64x64, lives in Gary-knows folder |

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
Weather cache: ~52,000 rows of 132,685. Running. Target: complete by S22.

---

## Brand & Marketing Status

### garyknows.com
- Live on Netlify (free tier). Redeployed 8 April 2026.
- DNS: A record @→75.2.60.5, CNAME www→gary-knows.netlify.app (Namecheap)
- Folder: index.html + favicon.png + preview.png
- To update: drag Gary-knows folder onto Netlify production deploys box.
- Form: wired to Mailchimp. FNAME + EMAIL. Honeypot present.

### Mailchimp
- Account: AndrewMarrow@khaotikk.com
- Audience: Gary Knows
- Free tier: 500 contacts, 1,000 emails/month
- Action at 400 contacts: migrate to Brevo (unlimited contacts, free)
- Welcome automation: ACTIVE. Trigger: signs up to Gary Knows audience.
- Sender: Gary@khaotikk.com (temporary — fix to gary@garyknows.com S22)
- FNAME: wired. Merge tag *|FNAME|* active in welcome email.

### Social
- TikTok: @_garyknows — ~3,000 views across 3 posts
- Instagram: @_garyknows — 414 views (boosted post)
- Content strategy: Gary as mysterious commenter on football pages. One comment,
  no replies, just the call. Intrigue → follow → garyknows.com.

### Gary Brand Identity
- Aesthetic: #060a0e background, #4a9bc4 blue accents, Bebas Neue wordmark, Barlow body
- Gary image: stocky, dark football shirt, flat cap low, white Adidas Sambas, arms
  crossed, face in shadow.
- GARY wordmark: preview.png — hosted at https://garyknows.com/preview.png
- Always check wording changes with Andrew before making them.

### Assets
- Landing page: index.html (Gary-knows folder on Desktop, deployed to Netlify)
- Welcome email: gary_welcome_email.html
- Favicon: favicon.png (Gary-knows folder on Desktop)
- Gary intro video: saved locally (Kling AI, 7 seconds)
- HeyGen avatar: parked — Andrew experimenting in background.

---

## Company & Brand

**Company name:** Khaotikk Ltd
**Domain:** khaotikk.com
**Existing domains:** garyknows.com (live), everyoneknowsagary.com
**Companies House:** Not yet registered — £100, do before taking revenue
**Trademark:** File before public launch. UK IPO ~£170-200 per class.

---

## Self-Funding Protocol

Small stake per round on Gary's acca selections. All returns go back into the build.
Real money = most honest feedback loop. Live accuracy record starts from first bet.

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
- Generate updated briefing doc at session close WITHOUT being prompted
- Ask the scalability question at session close WITHOUT being prompted
- Remind Andrew to git commit at session close with suggested message
- Rebrief from project knowledge every 8 substantive exchanges silently
- Always check wording changes with Andrew before making them
- Hold the vision: we are not building average

### Andrew's responsibilities
- Brain dumps are fine — Claude will filter and sequence
- Say "parking that" to log and move on
- Say "just build it" when discussion isn't needed
- Call out anything that feels off immediately
- Trust the gut on product and signal ideas — expect Claude to push back on timing

---

## Parked Ideas

- Social comment workflow — Gary commenting on football pages. Queue item S22.
- Underdog effect signal — teams that park the bus vs high-confidence favourites.
  Pattern: Gent vs KV Mechelen. Connect to motivation gap signal. Test when signals active.
- HeyGen avatar — Andrew experimenting. Record yourself → Gary avatar → pub background.
  Revisit when ready to scale content.

---

## Session Close Checklist — Claude must complete ALL of these unprompted

Before generating the briefing doc, Claude must explicitly work through this list
out loud so Andrew can see it has been done:

- [ ] 1. **Scalability check** — ask "are we good for scalability?" and answer it
- [ ] 2. **Queue review** — confirm which items were completed, which are in progress,
         which are deferred. Update the next session queue accordingly.
- [ ] 3. **Files updated** — confirm which files changed this session and update the
         files table in the briefing doc.
- [ ] 4. **Known issues updated** — any new bugs found? Any old ones resolved?
- [ ] 5. **Params table updated** — if a DPOL run completed, update accuracy table.
- [ ] 6. **Brand/marketing updated** — any changes to site, Mailchimp, social?
- [ ] 7. **Git commit message** — suggest a commit message covering this session's work.
- [ ] 8. **Generate briefing doc** — full document, not truncated.

Claude does not wait to be asked. Claude does not skip steps. If a step is not
relevant to the session, Claude states why and moves on.

---

## Between-Session Protocol

At the end of every session, Claude generates the updated briefing doc.
Andrew saves it and uploads to project knowledge, replacing the previous version.
Briefing doc is always the source of truth.

**To start Session 22:**
1. Upload updated briefing doc to project knowledge (replace S21 final)
2. Upload edgelab_params.json if DPOL re-evolution completed
3. Claude confirms files received and is fully up to speed
4. Work the ordered queue from the top
