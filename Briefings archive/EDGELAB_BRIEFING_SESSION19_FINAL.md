# EdgeLab — Session 19 Briefing (Final)

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
type scoring. Safety acca fixed (lowest-odds). --signals-only DPOL flag built.
Signal activation run started locally. Weather batch run restarted (resumed from 2015).
garyknows.com live. Mailchimp wired with welcome automation active.
First moist run placed 5 April 2026 — 2 legs still pending at session close.

**Market baseline:** ~49% (E0). EdgeLab E0 currently at **50.2%** on 8,669 matches.

---

## Session 19 — What Got Done

### Engine
- **Safety acca fixed** — now picks lowest-odds combination from HIGH conviction pool.
  Previously overlapped with result acca. Now distinct: boring, short-priced, reliable.
  Gary comment: "Shortest price I could find. Not exciting. That's the point."
- **`--signals-only` DPOL flag built** — added to edgelab_runner.py and edgelab_dpol.py.
  Locks core evolved params, searches signal weights only (Phase 1 + Phase 2).
  Save logic merges signal weights back into existing params without overwriting core.
  Run with: `python edgelab_runner.py history/ --tier all --signals-only`
- **Signal activation run started** — running locally. Status unknown at session close.

### Weather
- **Weather run restarted** — had stopped at December 2015 (~18,000 rows, 14% done).
  Restarted with resume logic — loaded cached rows and continued from there.
  Checkpointing every 1,000 rows. Safe to leave running overnight.

### Marketing & Brand
- **Landing page updated** (now index.html on Netlify):
  - Name field added to signup form (above email field)
  - Gary visibility fixed on mobile — raises higher, fills 115vh from top
  - Body copy updated (confirmed with Andrew before change)
  - Deployed to Netlify via Gary-knows folder (index.html + preview.png)
- **Brand identity locked** — dark/moody/minimal aesthetic applies to both
  Gary (consumer) and EdgeLab (engine). Consistent across all assets going forward.
- **GARY wordmark** — screenshot from garyknows.com, hosted at garyknows.com/preview.png
- **Welcome email built** (gary_welcome_email.html):
  - Same aesthetic as landing page — dark background, blue accents, Bebas Neue wordmark
  - GARY rendered as hosted image (no font dependency, renders everywhere)
  - Subject: "You're on the list."
  - Body: [First Name], / You'll be the first to know. / Gary will be in touch soon.
- **Mailchimp domain authentication** — 3 DNS records added to Namecheap (khaotikk.com):
  - CNAME k2._domainkey → dkim2.mcsv.net
  - CNAME k3._domainkey → dkim3.mcsv.net
  - TXT _dmarc → v=DMARC1; p=none;
  - Propagation in progress (up to 48 hours). Emails landing in spam until complete.
- **Welcome automation live** — triggers on new Gary Knows signup. Active 6 April 2026.
- **Existing list emailed** — 4 recipients. Landed in spam (authentication pending). Normal.
- **Sender email** — currently AndrewMarrow@khaotikk.com. Needs garyknows.com address.
  Google Workspace setup required. Parked.

### Social (noted this session)
- TikTok: @_garyknows live. First post: 200 views in 49 mins with no followers.
- Instagram: live, not yet performing.
- Ad video updated — "be the first to know" replacing old line.
- Repeatable format confirmed — keep template, swap wording.
- Marketing strategy noted: Gary as mysterious commenter on football pages. One comment,
  no replies, just the call. Intrigue → follow. Try this week.
- Gary blog noted: weekly post, Gary's voice, what he called, what happened.
  Screenshots of correct calls = credibility content.

---

## Ordered Work Queue

### Session 20 — priorities in order

1. **Log moist run results** — KV Mechelen vs Gent (Mon 17:30) and Derby vs Stoke
   (Mon 15:00) played 6 April. Log full outcome of the 5-leg safety acca.
2. **Check signals-only run** — did any Phase 1 or Phase 2 signals activate?
   Upload updated edgelab_params.json if run completed.
3. **Check weather cache** — how far did it get? If complete, wire into DPOL for
   weather signal activation test.
4. **HTML report — sortable columns** — click-to-sort by conf, DTI, chaos, upset score.
5. **Sender email** — set up gary@garyknows.com or similar on Google Workspace.
   Update Mailchimp sender address on campaign and automation.
6. **FNAME wiring** — confirm name field in Mailchimp form maps to FNAME merge tag.
   Check Audience → Signup forms → Form builder.

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
- Free tier: 500 contacts, 1,000 emails/month — 12 days trial remaining
- **Action when approaching 400 contacts:** migrate to Brevo (unlimited contacts, free)
- Domain authentication: in progress (up to 48 hours)
- Welcome automation: **ACTIVE** since 6 April 2026
- Sender address: needs updating to garyknows.com address (parked)

### Social
- TikTok: @_garyknows — live, 200 views/49 mins/no followers on first post
- Instagram: @_garyknows — live, not yet performing
- Ad video: updated wording, repeatable format confirmed

### Assets
- Gary brand image: IMG_0921.jpeg — dark, cap, no face, arms crossed
- GARY wordmark: preview.png — hosted at https://garyknows.com/preview.png
- Landing page: index.html (in Gary-knows folder on Desktop)
- Welcome email: gary_welcome_email.html

### Brand Identity
- Aesthetic: #060a0e background, #4a9bc4 blue accents, Bebas Neue wordmark, Barlow body
- Applies consistently to: landing page, email, all future Gary and EdgeLab assets
- Always check wording changes with Andrew before making them

---

## Live Accuracy Record

| Date | Selections | Stake | Odds | Result |
|------|-----------|-------|------|--------|
| 05/04/2026 | 5-leg safety acca (S17 engine) | £6.54 | ~16/1 | Pending — log S20 |
| 05/04/2026 | 3-leg result acca (S16 engine) | TBC | TBC | Pending |

Legs settled: Frosinone ✅, Las Palmas ✅, Heerenveen ✅
Legs pending: KV Mechelen vs Gent (Mon 17:30), Derby vs Stoke (Mon 15:00)

*Log full results at start of Session 20.*

---

## Between-Session Protocol

At the end of every session, Claude generates the updated briefing doc.
Andrew saves it and uploads to project knowledge, replacing the previous version.
Briefing doc is always the source of truth.

**To start Session 20:**
1. Upload updated briefing doc to project knowledge (replace session 19 final)
2. Upload edgelab_acca.py, edgelab_dpol.py, edgelab_runner.py (all updated S19)
3. Upload edgelab_params.json if signals-only run completed
4. Claude confirms files received and is fully up to speed
5. Work the ordered queue from the top

---

## Files

| File | Status | Notes |
|------|--------|-------|
| edgelab_engine.py | Updated S17 | Poisson scoreline, pred_score_draw, ~D alignment nudge |
| edgelab_acca.py | **Updated S19** | Safety acca fixed — lowest-odds combination |
| edgelab_databot.py | Updated S17 | All 17 tiers in LEAGUE_MAP |
| edgelab_weather.py | Updated S17 | --batch CLI added |
| edgelab_dpol.py | **Updated S19** | _generate_candidates_signals_only added |
| edgelab_config.py | Updated S16 | Phase 1 + Phase 2 signal display |
| edgelab_runner.py | **Updated S19** | --signals-only flag, signal-safe save logic |
| edgelab_params.json | Updated S16 | All 17 tiers evolved. May have signal updates. |
| edgelab_signals.py | Final S15 | 481 ground coords, all Phase 1 signals |
| edgelab_predict.py | Final | Full prediction pipeline |
| edgelab_gary.py | Final | Gary briefing wrapper |
| edgelab_gary_brain.py | Final | Gary context builder |
| edgelab_gridsearch.py | Final | Draw intelligence grid search |
| index.html | **Updated S19** | Landing page. Name field, mobile fix. |
| gary_welcome_email.html | **New S19** | Welcome email, hosted GARY wordmark image. |

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
132,685 rows total for weather fetch.

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
- Signal activation run: **STARTED S19** — running locally, status unknown at close

---

## Known Issues / Active Bugs

- **Draw floor** — D=4 from 199 predictions (2%). Draw intelligence weights dormant.
- **E1 home bias** — high DTI matchdays default H on most matches. Investigate.
- **Signal activation** — all Phase 1 + Phase 2 weights at 0.0. Run started S19.
- **Sender email** — Mailchimp sending from khaotikk.com, not garyknows.com.

---

## Parked Ideas

- **Injury data feed** — parked until signal activation and weather signal validated.
- **"It IS over before it's over"** — weekly Gary feature. Parked for acca builder expansion.
- **Gary onboarding team affiliation** — "Who's your team?" Gary tunes to that user.
- **Gary cap/accent by region** — adapts on setup. Paid tier = full menu.
- **Countdown clock on landing page** — add when launch date is known.
- **Behavioural risk layer** — Gary watches for addiction patterns. Not a nanny.
- **Gary voice on money** — "I'm not telling you what to do with your money. But if it was mine..."
- **Gary blog** — weekly post, Gary's voice, what he called, what happened. Parked.
- **Gary commenting strategy** — mysterious commenter on football pages. Try this week.

---

## Acca Builder

Two-stage process. Standalone module. Takes predictions CSV as input.

Stage 1 — filters to high-conviction picks: conf ≥ 52%, LOW/MED chaos, no upset flag.
Stage 2 — selects best decorrelated combination. Penalises same-tier same-day pairs.

Five acca types (distinct): result, safety, value, upset, BTTS.

**Safety acca** — sorted by lowest combined odds. HIGH conviction gate (≥65%) applies.
Gary comment: "Shortest price I could find. Not exciting. That's the point."

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
- DPOL's candidate space has draw intelligence slots that sat at 0 until ready
- Gary's brain schema has named SLOT entries for every future capability
- All Gary architecture decisions must remain gender-neutral at code level

---

## Scalability Debt

- GaryBrain loads full dataset into memory per instantiation — needs caching before launch
- No API wrapper around Gary — needed before app integration
- params.json write contention at scale — SQLite migration resolves this
- Gary's weather fetch makes a live API call per fixture — needs pre-fetch + cache

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
- ADHD hyperfocus is the superpower — the engine was built in 9 sessions on phone + laptop
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

### Andrew's responsibilities
- Brain dumps are fine — Claude will filter and sequence
- Say "parking that" to log and move on
- Say "just build it" when discussion isn't needed
- Call out anything that feels off immediately
- Trust the gut on product and signal ideas — expect Claude to push back on timing
