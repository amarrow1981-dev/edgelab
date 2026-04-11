# EdgeLab — Session 22 Briefing (Start)

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
**Built in:** 12 sessions on a phone and a laptop.

**Current engine status:** 45.9% overall. 50.2% E0. 51.4% N1. Signals dormant.
Draw intelligence dormant. High-confidence accuracy: 52.9% on first live run.
Market baseline: ~49% (E0).

---

## Session 22 — Start State

### Pre-session actions completed (between S21 and S22)
- **DPOL weighted loss run** — STILL RUNNING as of 08:31 on 08/04/2026.
  Confirmed active: processing Tier I1, Round 100+. params.json last modified 08:21.
  Do NOT interrupt. Wait for completion before uploading params.json.
- **Weather cache** — 51,000 rows visible in project files. Target: 132,685.
  Still short. Do not wire into DPOL yet.
- **New social posts planned** — Andrew posting today to generate leads.
  Lost signups post still needed (ask anyone who signed up before 8 April to re-sign-up).

### Session continuity additions (agreed between S21 and S22)
- **Claude state file** — this document now accompanied by EDGELAB_STATE_S22.md.
  Both must be uploaded to project knowledge at session start.
- **Session start handshake** — Claude states: "Last session ended at X. Next action
  is Y. Anything changed?" before touching the queue.
- **Two-document close** — briefing doc (human-readable) + state file (Claude-optimised)
  generated at every session close.
- **Honesty protocol** — Claude never covers itself. If uncertain, Claude says so.
  If wrong, Claude owns it. No softening. No fabrication.

---

## Ordered Work Queue

### Session 22 — priorities in order

1. **DPOL weighted loss run — await completion**
   Check if run has finished. Upload updated edgelab_params.json when done.
   Key questions:
   - Did E2 w_form and w_gd drop? (were 2x too high under flat loss)
   - Did draw_margin widen on any tier?
   - Re-run draw gridsearch — does draw intelligence now activate?
   - Update accuracy table with new weighted loss params.

2. **Check weather cache row count**
   Run: `import pandas as pd; df = pd.read_csv('weather_cache.csv'); print(len(df))`
   If complete (132,685 rows): wire into DPOL for weather signal activation test.
   If still running: leave it, move on.

3. **Fix gary@garyknows.com**
   Google Workspace verification incomplete — email sent to non-existent address.
   Options: fix verification, or start fresh with a new Google Workspace setup.
   Update Mailchimp sender address once resolved.
   Current temp sender: Gary@khaotikk.com.

4. **Lost signups social post**
   TikTok + Instagram. Simple message: anyone who signed up before 8 April and
   heard nothing — sign up again at garyknows.com. Form is now working.

5. **Duplicate pick warning in acca builder**
   Flag if same match appears in more than one acca type. Quick build.

6. **Gary's Upset Picks output**
   Filtered report, upset flags only. Gary commentary on each pick.
   Screenshot-ready format for social.

### Parked — reintroduce at right moment

- **Gary acca picks (product feature)** — Gary builds accas in standard formats
  plus custom types (long shot, underdog, "it IS over before it's over").
  Full pick list always shown so users can self-build. Site-wide selection builder —
  not a bet builder. Reintroduce when Gary output is live on site.
- **Social comment workflow** — Gary commenting on football pages as a character.
  One comment, no replies, just the call. Queue for S22/S23 content push.
- **Underdog effect signal** — teams that park the bus vs high-confidence favourites.
  Pattern: Gent vs KV Mechelen. Connect to motivation gap signal.
  Test when weather cache complete and signals active.
- **HeyGen avatar** — Andrew experimenting. Record yourself → Gary avatar → pub
  background. Revisit when ready to scale content.
- **E1 home bias** — high DTI matchdays default H. Investigate S22+.

---

## Milestone Roadmap

### Milestone 1 — Engine Validated ✅ COMPLETE
Cold engine running, all 17 tiers evolved, predictions live, acca builder working,
Gary briefings live, first live run placed. Done.

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
  Weighted loss function now live — re-run gridsearch after DPOL re-evolution completes.
- **E2 overconfidence** — w_form=0.898, w_gd=0.533 (2x E1 values). Too high.
  Weighted loss function should self-correct during re-evolution. Monitor new params.
- **E1 home bias** — high DTI matchdays default H. Investigate S22+.
- **Signal activation** — all Phase 1 + Phase 2 weights at 0.0.
  Weighted loss re-evolution in progress. Check after run completes.
- **BTTS/scoreline inconsistency** — BTTS flag inconsistent with scoreline pred.
  Sevilla vs Atletico: engine predicted 0-1 but BTTS active. Logged S19. Not yet fixed.
- **Sender email** — Mailchimp sending from Gary@khaotikk.com. Fix S22.
- **Duplicate acca picks** — no warning when same match appears in multiple accas.
- **Weather cache incomplete** — 51,000 of 132,685 rows. Still running.

---

## DPOL Status

- --tier all run (flat loss): COMPLETE — all 17 tiers evolved, params saved
- --signals-only flag: BUILT S19
- Signal activation run: COMPLETE S21 — no signals activated, all weights 0.0
- Weighted loss function: BUILT S21 ✅
- --tier all run (weighted loss): IN PROGRESS — running locally as of 08:31 08/04/2026.
  Processing Tier I1 at last observation. params.json partially updated (08:21).

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

**Update this table when weighted loss run completes.**

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
Cache: ~51,000 rows of 132,685. Still running.
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
| edgelab_params.json | Updating S22 | Weighted loss run in progress. Upload when complete. |
| edgelab_signals.py | Final S15 | 481 ground coords, all Phase 1 signals |
| edgelab_predict.py | Final | Full prediction pipeline |
| edgelab_gary.py | Final | Gary briefing wrapper |
| edgelab_gary_brain.py | Final | Gary context builder |
| edgelab_gary_context.py | Final | Gary prompt assembler |
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
Weather cache: ~51,000 rows of 132,685. Running.

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
- New posts planned today (8 April) to generate leads.

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
- Generate updated briefing doc + state file at session close WITHOUT being prompted
- Ask the scalability question at session close WITHOUT being prompted
- Remind Andrew to git commit at session close with suggested message
- Rebrief from project knowledge every 8 substantive exchanges silently
- Always check wording changes with Andrew before making them
- Hold the vision: we are not building average
- **Never lie. Never cover. If uncertain, say so. If wrong, own it.**

### Session start protocol (NEW S22)
- Claude reads briefing doc + state file before responding
- Claude opens every session with: "Last session ended at [X]. Next action is [Y].
  Anything changed?" — explicit handshake, no assumptions.

### Andrew's responsibilities
- Brain dumps are fine — Claude will filter and sequence
- Say "parking that" to log and move on
- Say "just build it" when discussion isn't needed
- Call out anything that feels off immediately
- Trust the gut on product and signal ideas — expect Claude to push back on timing

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
- [ ] 8. **Generate briefing doc + state file** — both documents, neither truncated.

Claude does not wait to be asked. Claude does not skip steps. If a step is not
relevant to the session, Claude states why and moves on.

---

## Between-Session Protocol

At the end of every session, Claude generates:
1. Updated briefing doc (this document — human-readable, source of truth)
2. Claude state file (EDGELAB_STATE_SXX.md — compressed, Claude-optimised)

Andrew saves both and uploads to project knowledge, replacing previous versions.
Briefing doc is always the source of truth. State file is the continuity layer.

**To start Session 22:**
1. Upload this briefing doc to project knowledge (replace S21 final)
2. Upload EDGELAB_STATE_S22.md to project knowledge
3. Upload edgelab_params.json once DPOL run completes
4. Claude confirms files received, states last action + next action
5. Work the ordered queue from the top
