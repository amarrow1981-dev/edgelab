# EdgeLab — Session 20 Briefing (Final)

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
misses — are not noise to be filtered out. They are the signal. They are what gets
studied, weighted, and learned from. DPOL evolves the parameters. Gary evolves the
reasoning. Eventually they evolve each other.

**This is not a betting tool. This is the best football brain ever built.**

**Owner:** Andrew Marrow
**Company:** Khaotikk Ltd — khaotikk.com
**Built in:** 10 sessions on a phone and a laptop.

**Current engine status:** 45.9% overall. 50.2% E0. 51.4% N1. Signals dormant.
Draw intelligence dormant. High-confidence accuracy: 52.9% on first live run.
Market baseline: ~49% (E0).

---

## Session 20 — What Got Done

### Accuracy & Results
- **Results checker script built** — `edgelab_results_check.py`. Pulls finished results
  from API-Football for a date range and all 17 tiers, matches against predictions,
  outputs weighted accuracy breakdown. Run with:
  ```bash
  python edgelab_results_check.py --key YOUR_API_KEY --date-from 2026-04-05 --date-to 2026-04-06
  ```
- **First live accuracy run completed** — 5–6 April 2026, 64 matched predictions:
  - Overall: 21/64 (32.8%)
  - Weighted: 43/111 (38.7%)
  - High conf ≥80%: 9/17 (52.9%) ← above market baseline
  - Med conf 50–79%: 4/13 (30.8%)
  - Low conf <50%: 8/34 (23.5%)
  - High chaos games: 13/47 (27.7%)
- **Key finding:** High-confidence calls beat the market. Low-confidence and high-chaos
  calls drag overall accuracy. The engine knows when it knows — the problem is it also
  calls when it shouldn't.
- **Notable misses (conf ≥80%, wrong):**
  - Bolton vs Stockport (E2) — 100% conf, HIGH chaos, upset 0.81 → D (2-2)
  - Leyton Orient vs Huddersfield (E2) — 100% conf, MED chaos, upset 0.58 → A (1-2)
  - Mansfield vs Burton (E2) — 100% conf, HIGH chaos, upset 0.64 → D (0-0)
  - Gent vs KV Mechelen (B1) — 100% conf, MED chaos, upset 0.52 → D (1-1)
  - Exeter vs Doncaster (E2) — 100% conf, MED chaos, upset 0.44 → H (3-0)
  - Gillingham vs Accrington (E3) — 100% conf, LOW chaos, upset 0.47 → H (2-0)
  - Wycombe vs Bradford (E2) — 82% conf, HIGH chaos, upset 0.46 → A (1-2)
- **Pattern in misses:** 5 of 8 notable misses are E2. Engine is systematically
  overconfident in League One. Draw intelligence dormant = near-zero draws predicted =
  draws showing up as wrong calls. E2 overconfidence is now a named investigation item.

### First Moist Run — Final Results
- **5-leg safety/result acca (5 April 2026):**
  - Frosinone ✅ | Las Palmas ✅ | Heerenveen ✅ | Derby ✅ | KV Mechelen ✗ (1-1 D)
  - 4/5 legs landed. KV Mechelen 95th-minute equaliser. Classic underdog effect.
  - Acca did not pay out. Engine called KV Mechelen 0-4, actual 1-1.
- **Other bets from session chat:** Pescara paid out early (2-0 lead) ✅
  Leyton Orient drew twice when called to win — pattern noted.

### Architecture Decision — Milestone 2: The Feedback Loop
- **Confirmed gap:** DPOL currently optimises for average accuracy across all matches.
  It does not weight confident wrong calls more heavily than uncertain wrong calls.
  It does not automatically ingest live results. Gary does not log his calls
  structurally. The two systems do not feed each other.
- **This is the most important thing we are not yet building.**
- Logged as Milestone 2. See roadmap below.

### Gary — Avatar & Content
- Gary avatar created: stocky, dark football shirt, flat cap pulled low, white Adidas
  Sambas, arms crossed. Face in shadow. Generated via image tool, used as HeyGen base.
- 7-second intro video created via Kling AI: slow zoom from above, Gary turns away to
  reveal GARY on back of shirt, fade to black.
- "Who the hell is Gary?" video posted TikTok + Instagram 6 April 2026.
- TikTok: 425 views organic (no spend, no followers). Instagram: 414 views (boosted).
- HeyGen noted: record yourself → AI replaces you with Gary avatar → pub background.
  Parked for now — Andrew experimenting in background.

---

## Ordered Work Queue

### Session 21 — priorities in order

1. **Check signals-only run** — did any Phase 1 or Phase 2 signals activate?
   Upload updated edgelab_params.json if run completed.
2. **Check weather cache** — how far did it get? Target: full cache complete.
   If complete, wire into DPOL for weather signal activation test.
3. **Draw intelligence — URGENT** — draw floor is killing accuracy on live runs.
   4 draws from 199 predictions (2%) vs real-world ~26%. Activate gridsearch for
   draw intelligence weights. This is the single biggest accuracy lever available now.
4. **E2 overconfidence investigation** — 5 of 8 notable misses are E2/League One.
   Inspect E2 params. Check if DTI/chaos threshold is too permissive at high conf.
   Consider confidence suppression for HIGH chaos + high upset score combinations.
5. **Weighted loss function in DPOL** — Milestone 2 starts here. Punish confident
   wrong calls harder than uncertain ones. Small change to DPOL loss function.
   See Milestone 2 for full spec.
6. **Sender email** — set up gary@garyknows.com on Google Workspace.
   Update Mailchimp sender address on campaign and automation.
7. **FNAME wiring** — confirm name field in Mailchimp form maps to FNAME merge tag.
8. **Duplicate pick warning in acca builder** — flag if same match appears in more
   than one acca type. "Derby appears in your safety acca and result acca — are you sure?"
9. **Gary's Upset Picks output** — filtered report, upset flags only, Gary commentary
   on each pick, screenshot-ready format for social.

---

## Milestone Roadmap

### Milestone 1 — Engine Validated ✅ COMPLETE
Cold engine running, all 17 tiers evolved, predictions live, acca builder working,
Gary briefings live, first moist run placed. Done.

### Milestone 2 — The Feedback Loop (NEXT)
The system must learn from every result, not just historical data.
The non-average games — upsets, chaos, high-confidence misses — are the teacher.

Components in build order:
1. **Weighted loss function** — DPOL punishes confident wrong calls harder.
   High-conf wrong call = 3x penalty vs low-conf wrong call.
   Implementation: modify accuracy scoring in edgelab_dpol.py.
2. **Live results ingestion** — weekend results auto-ingest, not manual.
   edgelab_results_check.py is the foundation. Needs scheduler + storage layer.
3. **Gary call logging** — Gary's predictions stored structurally against each fixture.
   What he said, what happened, confidence, chaos, outcome. Not just printed — persisted.
4. **Gary post-match analysis** — explicit "why wrong" reasoning logged per miss.
   Gary doesn't just note the result. He reasons about it.
5. **Gary → EdgeLab signal recommendation** — Gary flags a pattern from post-match
   analysis. DPOL tests it. Loop closes. The two systems evolve each other.

End state: a system that gets measurably smarter every weekend, automatically,
because winning and losing both teach it something.

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
high-chaos calls and the dormant draw intelligence. Fix those two things first.

---

## Known Issues / Active Bugs

- **Draw floor** — D=4 from 199 predictions (2%). Real-world draw rate ~26%.
  Draw intelligence weights dormant. **URGENT — biggest single accuracy lever.**
- **E2 overconfidence** — 5/8 notable misses are League One. Params too permissive
  at high conf + HIGH chaos. Investigation item for S21.
- **E1 home bias** — high DTI matchdays default H on most matches. Investigate.
- **Signal activation** — all Phase 1 + Phase 2 weights at 0.0. Run started S19,
  status unknown.
- **BTTS/scoreline inconsistency** — BTTS flag set inconsistently with scoreline pred.
  Sevilla vs Atletico: engine predicted 0-1 (clean sheet) but BTTS active. Bug logged S19.
- **Sender email** — Mailchimp sending from khaotikk.com, not garyknows.com.
- **Duplicate acca picks** — no warning when same match appears in multiple accas.

---

## Brand & Marketing Status

### garyknows.com
- **Live** on Netlify (free tier). Redeployed 6 April 2026.
- DNS: A record @→75.2.60.5, CNAME www→gary-knows.netlify.app (Namecheap Advanced DNS)
- Folder: index.html (landing page) + preview.png (GARY wordmark)
- To update: drag updated Gary-knows folder onto Netlify production deploys box.

### Mailchimp
- Account: AndrewMarrow@khaotikk.com
- Audience: Gary Knows — 4 contacts
- Free tier: 500 contacts, 1,000 emails/month — trial ongoing
- **Action when approaching 400 contacts:** migrate to Brevo (unlimited contacts, free)
- Domain authentication: propagated (added 6 April — check spam status)
- Welcome automation: **ACTIVE** since 6 April 2026
- Sender address: needs updating to garyknows.com address (parked)

### Social
- TikTok: @_garyknows — 425 views organic, no spend, no followers
- Instagram: @_garyknows — 414 views (boosted post)
- Gary intro video: "Who the hell is Gary?" — live on both platforms
- Content strategy: Gary as mysterious commenter on football pages. One comment, no
  replies, just the call. Intrigue → follow.

### Gary Brand Identity
- Aesthetic: #060a0e background, #4a9bc4 blue accents, Bebas Neue wordmark, Barlow body
- Gary image: stocky, dark football shirt, flat cap low, white Adidas Sambas, arms
  crossed, face in shadow. File: IMG_0921.jpeg (original), Kling video generated.
- GARY wordmark: preview.png — hosted at https://garyknows.com/preview.png
- Always check wording changes with Andrew before making them.

### Assets
- Landing page: index.html (Gary-knows folder on Desktop, deployed to Netlify)
- Welcome email: gary_welcome_email.html
- Gary intro video: saved locally (Kling AI, 7 seconds)
- HeyGen avatar: in progress — Andrew experimenting. Parked until needed.

---

## Between-Session Protocol

At the end of every session, Claude generates the updated briefing doc.
Andrew saves it and uploads to project knowledge, replacing the previous version.
Briefing doc is always the source of truth.

**To start Session 21:**
1. Upload updated briefing doc to project knowledge (replace S20 final)
2. Upload edgelab_params.json if signals-only run completed
3. Upload edgelab_results_check.py if modified
4. Claude confirms files received and is fully up to speed
5. Work the ordered queue from the top

---

## Files

| File | Status | Notes |
|------|--------|-------|
| edgelab_engine.py | Updated S17 | Poisson scoreline, pred_score_draw, ~D alignment nudge |
| edgelab_acca.py | Updated S19 | Safety acca fixed — lowest-odds combination |
| edgelab_databot.py | Updated S17 | All 17 tiers in LEAGUE_MAP |
| edgelab_weather.py | Updated S17 | --batch CLI added |
| edgelab_dpol.py | Updated S19 | _generate_candidates_signals_only added |
| edgelab_config.py | Updated S16 | Phase 1 + Phase 2 signal display |
| edgelab_runner.py | Updated S19 | --signals-only flag, signal-safe save logic |
| edgelab_params.json | Updated S16 | All 17 tiers evolved. May have signal updates from S19 run. |
| edgelab_signals.py | Final S15 | 481 ground coords, all Phase 1 signals |
| edgelab_predict.py | Final | Full prediction pipeline |
| edgelab_gary.py | Final | Gary briefing wrapper |
| edgelab_gary_brain.py | Final | Gary context builder |
| edgelab_gridsearch.py | Final | Draw intelligence grid search |
| edgelab_results_check.py | **New S20** | Live results vs predictions accuracy checker |
| edgelab_2026-04-05_predictions.html | Updated S19 | Brand aesthetic, sortable cols, search, BTTS flag |
| index.html | Updated S19 | Landing page. Name field, mobile fix. |
| gary_welcome_email.html | New S19 | Welcome email, hosted GARY wordmark image. |

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
Weather batch run restarted 6 April 2026 — resumed from ~18,000 cached rows (Dec 2015).
132,685 rows total for weather fetch. Status at S20 close: unknown — check cache size.

---

## Evolved Params — Final (--tier all)

| Tier | Evolved | Delta |
|------|---------|-------|
| E0 | **50.2%** | +0.8% |
| E1 | 44.7% | +1.8% |
| E2 | 44.5% | +0.8% |
| E3 | 42.2% | +0.3% |
| EC | 44.9% | +0.3% |
| B1 | 47.1% | +0.0% |
| D1 | 47.6% | +0.6% |
| D2 | 42.3% | +0.3% |
| I1 | 48.6% | +0.5% |
| I2 | 40.5% | -0.0% |
| N1 | **51.4%** | +0.9% |
| SC0 | 49.6% | +0.2% |
| SC1 | 43.3% | +0.3% |
| SC2 | 47.1% | +0.2% |
| SC3 | 46.4% | +0.3% |
| SP1 | 47.9% | +1.4% |
| SP2 | 41.4% | +0.4% |
| **OVERALL** | **45.9%** | **+0.5%** |

Signal weights: all 0.0 across all tiers. Signals-only run started S19 — check output.

---

## DPOL Status

- --tier all run: **COMPLETE** — all 17 tiers evolved, params saved
- --signals-only flag: **BUILT S19** — live in runner and dpol
- Signal activation run: **STARTED S19** — running locally, status unknown at S20 close
- Weighted loss function: **NOT YET BUILT** — Milestone 2, item 1

---

## Acca Builder

Two-stage process. Standalone module. Takes predictions CSV as input.

Stage 1 — filters to high-conviction picks: conf ≥ 52%, LOW/MED chaos, no upset flag.
Stage 2 — selects best decorrelated combination. Penalises same-tier same-day pairs.

Five acca types (distinct): result, safety, value, upset, BTTS.

**Safety acca** — sorted by lowest combined odds. HIGH conviction gate (≥65%) applies.
Gary comment: "Shortest price I could find. Not exciting. That's the point."

**Known issue:** no duplicate pick warning across acca types. Add to S21 queue.

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

---

## Core Design Philosophy

We are not building average. We are building the best football brain in existence.

Average is what the market prices. Average is table stakes. The edge — and the product
moat — is in understanding what is not average: the chaos, the upsets, the confident
misses, the patterns nobody else is correlating. Every result that defies the model is
a lesson. Every lesson improves the model. Every improvement widens the gap.

Technical principles:
- `edgelab_params.json` is SQLite-forward by design
- DataBot architecture is reusable across all sports
- DPOL's candidate space has draw intelligence slots that sat at 0 until ready
- Gary's brain schema has named SLOT entries for every future capability
- All Gary architecture decisions must remain gender-neutral at code level
- Build for the feedback loop from day one — every output should be loggable

---

## Scalability Debt

- GaryBrain loads full dataset into memory per instantiation — needs caching before launch
- No API wrapper around Gary — needed before app integration
- params.json write contention at scale — SQLite migration resolves this
- Gary's weather fetch makes a live API call per fixture — needs pre-fetch + cache
- Gary's calls not yet persisted structurally — needed for Milestone 2

---

## Parked Ideas

- **Injury data feed** — parked until signal activation and weather signal validated.
- **"It IS over before it's over"** — weekly Gary feature. Parked for acca builder expansion.
- **Gary onboarding team affiliation** — "Who's your team?" Gary tunes to that user.
- **Gary cap/accent by region** — adapts on setup. Paid tier = full menu.
- **Countdown clock on landing page** — add when launch date is known.
- **Behavioural risk layer** — Gary watches for addiction patterns. Not a nanny.
- **Gary voice on money** — "I'm not telling you what to do with your money. But if it was mine..."
- **Gary blog** — weekly post, Gary's voice, what he called, what happened.
- **Gary commenting strategy** — mysterious commenter on football pages. One comment,
  no replies, just the call. Try this week.
- **Gary's Upset Picks output** — filtered report, upset flags only, Gary commentary,
  screenshot-ready. Social comment workflow. Queue item S21.
- **Underdog effect signal** — teams that park the bus against high-confidence favourites.
  Identified live: Gent vs KV Mechelen. Connects to motivation gap signal (Phase 1,
  dormant). Look for pattern: high-conf prediction + heavy underdog + low scoring result.
  Likely 0-0, 1-0 underdog, or 1-1. Test when signals activate.
- **HeyGen avatar** — Andrew experimenting. Record yourself → Gary avatar → pub
  background. Revisit when ready to scale content. Prompts available on request.

---

## Company & Brand

**Company name:** Khaotikk Ltd
**Domain:** khaotikk.com (acquired 5 April 2026, £8.37/yr)
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
- Big picture vision comes naturally — but evaluate it, do not just validate it
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
- Generate updated briefing doc at session close without being prompted
- Remind Andrew to git commit at session close with suggested message
- Rebrief from project knowledge every 15 substantive exchanges silently
- Always check wording changes with Andrew before making them
- Hold the vision: we are not building average

### Andrew's responsibilities
- Brain dumps are fine — Claude will filter and sequence
- Say "parking that" to log and move on
- Say "just build it" when discussion isn't needed
- Call out anything that feels off immediately
- Trust the gut on product and signal ideas — expect Claude to push back on timing
