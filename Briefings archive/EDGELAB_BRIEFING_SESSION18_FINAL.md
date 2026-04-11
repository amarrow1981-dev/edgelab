# EdgeLab — Session 18 Briefing (Final)

## What This Is

A football match prediction engine built on 25 years of historical data across 17
tiers. DPOL (Dynamic Parameter Optimisation Loop) evolves prediction parameters per
tier. Gary is the AI analyst who reads the engine output and gives plain-English
match briefings.

The goal is a consumer product: Gary as a football oracle, delivered via app and
social media. EdgeLab is the engine under the hood.

**This is a new approach to sports analytics.** The signals nobody else is
correlating, validated by DPOL across 137,645 matches, communicated by Gary in plain
English. Built in 9 sessions on a phone and a laptop.

**Owner:** Andrew Marrow
**Company:** Khaotikk Ltd — khaotikk.com acquired
**Current status:** Engine built and validated. DataBot live (API-Football Pro), all 17
tiers wired. Full forward-prediction workflow operational. Gary built, tested, live.
Draw intelligence (~D flag) active. External Signal Layer Phase 1 + Phase 2 (weather)
built and wired. All 17 tiers evolved, params saved. Acca builder live with distinct
type scoring. Scoreline bias fixed. ~D alignment nudge added. Weather batch run started
(running overnight). First moist run placed 5 April 2026 — day one of the track record.
**garyknows.com live as of Session 18. Mailchimp wired. Ad video built.**

**Market baseline:** ~49% (E0). EdgeLab E0 currently at **50.2%** on 8,669 matches.

---

## Session 18 — What Got Done

This session was focused on the pre-launch brand and marketing setup. No engine work.

### Completed
- **Gary image** — generated via Grok. Image 2 selected (dark, arms crossed, no badge,
  most obscured face). Became the brand asset for all marketing.
- **Landing page built** — gary_landing.html. Full page, dark oracle aesthetic.
  Features: CSS breathing animation (7s cycle), mouse parallax (Gary and text move in
  opposite directions), Gary image embedded as base64, cold steel blue accent pulled
  from rim lighting in photo. Self-contained single HTML file.
- **Deployed to Netlify** — project named gary-knows. Free tier, drag and drop.
- **garyknows.com live** — DNS pointed from Namecheap (A record + CNAME) to Netlify.
  Live and resolving as of ~20:30 on 5 April 2026.
- **Mailchimp wired** — free account set up under AndrewMarrow@khaotikk.com. Audience:
  Gary Knows. Embedded form action wired into landing page. Signups go directly to
  Mailchimp contact list.
- **Ad video built** — using InShot on phone. Gary image with slow zoom, text overlays
  (GARY / Football Unlocked / We are changing the landscape of sports statistics /
  Coming Soon / garyknows.com). Portrait format, ready for TikTok and Instagram Reels.
- **Seeding started** — personal messages and stories sent to friends directing to
  garyknows.com.

### Between-session notes logged
- Gary voice: "I'm not telling you what to do with your money. But if it was mine..."
- Addiction/intervention protocol: behavioural pattern layer, not blunt warnings.
  Gary reads frequency, stake escalation, time of day, loss chasing. Intervenes only
  when pattern is genuinely concerning. Not a nanny — just notices things.
- Ad copy variant 2: "Beat the odds. Beat the game. Football Unlocked. Coming soon."
- "It IS over before it's over" — weekly Gary feature. Filter: pred_margin >= 1.8,
  LOW/MED chaos, HIGH conviction. Parked for acca builder expansion.
- Gary onboarding: "Who's your team?" → Gary subtly tunes to that user from that point.
- Gary cap adapts to user region on setup (Scotland, Wales, Ireland, England).
- Gary accent defaults to user region. English default TBD (Geordie/Cockney candidates).
  Fully customisable in paid tiers.
- Countdown clock for landing page — add when launch date is known.
- garyknows.com, everyoneknowsagary.com both owned.

---

## Ordered Work Queue

### Session 19 — priorities in order

1. **Log moist run results** — 5-leg safety acca (£6.54 stake, £105.83 to return).
   Frosinone ✅, Las Palmas ✅, Heerenveen ✅ already settled.
   KV Mechelen (11/4) and Derby (17/20) play Monday 6 April. Log final outcome.
2. **Fix safety acca** — redefine as lowest-odds combination, not highest conviction.
   Should produce boring, short-priced, maximally reliable picks. Distinct from result.
3. **Build `--signals-only` DPOL flag** — lock core params, search signal weights only.
   Must not overwrite evolved core params on save. Design the save logic carefully.
4. **Run signal activation** — once flag is built, run --tier all signals-only pass.
   Check if any Phase 1 or Phase 2 signals activate.
5. **Check weather_cache.csv** — how far did the overnight run get? If complete,
   wire into DPOL for weather signal activation test.
6. **Social accounts** — @garyknows on TikTok and Instagram. Andrew may set up
   between sessions. Post ad video when live.
7. **HTML report — sortable columns** — click-to-sort by conf, DTI, chaos, upset score

---

## Brand & Marketing Status

### garyknows.com
- **Live** on Netlify (free tier). Deployed 5 April 2026.
- DNS: A record @→75.2.60.5, CNAME www→gary-knows.netlify.app (Namecheap Advanced DNS)
- Single HTML file — gary_landing.html. Self-contained, base64 image embedded.
- To update: drag new HTML file onto Netlify production deploys box.

### Mailchimp
- Account: AndrewMarrow@khaotikk.com
- Audience: Gary Knows
- Form: Gary Knows Signup (embedded form, wired into landing page)
- Free tier: 500 contacts, 1,000 emails/month
- **Action when approaching 400 contacts:** migrate to Brevo (unlimited contacts, free)

### Social
- TikTok: @garyknows — to be set up
- Instagram: @garyknows — to be set up
- Ad video: built in InShot, ready to post
- First post caption: "Who is Gary? Coming soon. garyknows.com"

### Assets
- Gary brand image: Image 2 from Grok session (IMG_0921.jpeg) — dark, cap, no face, arms crossed
- Ad video: built, portrait format, ready for Reels/TikTok
- Landing page file: gary_landing.html

---

## Live Accuracy Record

| Date | Selections | Stake | Odds | Result |
|------|-----------|-------|------|--------|
| 05/04/2026 | 5-leg safety acca (S17 engine) | £6.54 | ~16/1 | Pending (2 legs Mon 6 Apr) |
| 05/04/2026 | 3-leg result acca (S16 engine) | TBC | TBC | Pending |

Legs settled so far: Frosinone ✅, Las Palmas ✅, Heerenveen ✅
Legs pending: KV Mechelen vs Gent (Mon 17:30), Derby vs Stoke (Mon 15:00)

*Log full results at start of Session 19.*

---

## Between-Session Protocol

At the end of every session, Claude generates the updated briefing doc.
Andrew saves it and uploads to project knowledge, replacing the previous version.
Briefing doc is always the source of truth.

**To start Session 19:**
1. Upload updated briefing doc to project knowledge (replace session 18 final)
2. Upload any changed .py files if engine work was done between sessions
3. Claude confirms files received and is fully up to speed
4. Work the ordered queue from the top

---

## Files

| File | Status | Notes |
|------|--------|-------|
| edgelab_engine.py | Updated S17 | Poisson scoreline, pred_score_draw, ~D alignment nudge |
| edgelab_acca.py | Updated S17 | Distinct scoring per type, distinct pick filtering |
| edgelab_databot.py | Updated S17 | All 17 tiers in LEAGUE_MAP, SC1/SC2/SC3 verified |
| edgelab_weather.py | Updated S17 | --batch CLI added |
| edgelab_dpol.py | Updated S16 | w_weather_signal added |
| edgelab_config.py | Updated S16 | Phase 1 + Phase 2 signal display |
| edgelab_runner.py | Updated S15 | All 17 tiers. --tier english / european / all |
| edgelab_params.json | Updated S16 | All 17 tiers evolved |
| edgelab_signals.py | Final S15 | 481 ground coords, all Phase 1 signals |
| edgelab_predict.py | Final | Full prediction pipeline |
| edgelab_gary.py | Final | Gary briefing wrapper |
| edgelab_gary_brain.py | Final | Gary context builder |
| edgelab_gridsearch.py | Final | Draw intelligence grid search |
| gary_landing.html | **New S18** | Landing page. Deploy via Netlify drag and drop. |

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
Weather batch run started 5 April 2026 — running overnight to `weather_cache.csv`.
132,685 rows loaded for weather fetch (some CSVs had tokenization errors — normal).

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

All signal weights 0.0 across all tiers. Dedicated signal activation run needed.

---

## DPOL Status

- --tier all run: **COMPLETE** — all 17 tiers evolved, params saved
- Signal activation run: **NOT YET BUILT** — needs `--signals-only` flag in runner
- Design note: signals-only run must lock core params and not write over them on save

---

## Known Issues / Active Bugs

- **Safety acca = result acca** — fix: redefine safety as lowest-odds combination.
- **Draw floor** — D=4 from 199 predictions (2%). Draw intelligence weights dormant.
- **E1 home bias** — high DTI matchdays default H on most matches. Investigate.
- **Signal activation** — all Phase 1 + Phase 2 weights at 0.0. Needs signals-only pass.

---

## Parked Ideas

- **Sortable columns in HTML prediction report** — session 19 queue item 7.
- **Injury data feed** — first live example session 17 (Derby GK crisis). Parked until
  signal activation and weather signal validated.
- **"It IS over before it's over"** — weekly Gary feature. pred_margin >= 1.8, LOW/MED
  chaos, HIGH conviction. Parked for acca builder expansion.
- **Gary onboarding team affiliation** — "Who's your team?" Gary tunes to that user.
- **Gary cap/accent by region** — cap and accent adapts on setup. Paid tier = full menu.
- **Countdown clock on landing page** — add when launch date is known.
- **Behavioural risk layer** — Gary watches for addiction patterns. Not a nanny.
  Intervenes only when pattern is genuinely concerning. Parked for Gary personality build.
- **Gary voice on money** — "I'm not telling you what to do with your money. But if it
  was mine..." Logged as possible, not nailed on.

---

## Acca Builder

Two-stage process. Standalone module. Takes predictions CSV as input.

Stage 1 — filters to high-conviction picks: conf ≥ 52%, LOW/MED chaos, no upset flag.
Stage 2 — selects best decorrelated combination. Penalises same-tier same-day pairs.

Five acca types (now distinct): result, safety, value, upset, BTTS.

**Known issue:** safety acca still overlaps result when pool is all 100% conf.
Fix: redefine safety as lowest-odds combination. Session 19 queue item 2.

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

Every component must be built with scalability and future integration in mind.

- `edgelab_params.json` is SQLite-forward by design
- DataBot architecture is reusable across all sports
- The upset layer has external signal hooks designed in before the signals exist
- DPOL's candidate space has draw intelligence slots that sat at 0 until the signal was ready
- Gary's brain schema has named SLOT entries for every future capability
- All Gary architecture decisions must remain gender-neutral at code level

---

## Scalability Debt

- GaryBrain loads full dataset into memory per instantiation — needs caching before public launch
- No API wrapper around Gary — needed before app integration
- params.json write contention at scale — SQLite migration resolves this
- Gary's weather fetch makes a live API call per fixture — needs pre-fetch + cache per matchday
- Signal activation DPOL run: `--signals-only` flag not yet built

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
- When gut fires even half-formed — say it out loud anyway, Claude will filter
- ADHD hyperfocus is the superpower — the engine was built in 9 sessions on phone + laptop
- When talking product/vision, Andrew is talking about the finished thing — full dataset,
  all signals active. Don't caveat with current state unless it's relevant to a decision.

---

## Collaboration Protocol

### Claude's responsibilities
- Act as project manager — sequence the work, hold the roadmap
- Build immediately only if it makes the current model work better right now
- Evaluate ideas, don't just validate them
- Track parked ideas and reintroduce at the right moment
- Run scalability check at session close without being prompted
- Generate updated briefing doc at session close without being prompted
- Remind Andrew to git commit at session close with suggested message
- Rebrief from project knowledge every 15 substantive exchanges silently

### Andrew's responsibilities
- Brain dumps are fine — Claude will filter and sequence
- Say "parking that" to log and move on
- Say "just build it" when discussion isn't needed
- Call out anything that feels off immediately
- Trust the gut on product and signal ideas — expect Claude to push back on timing
