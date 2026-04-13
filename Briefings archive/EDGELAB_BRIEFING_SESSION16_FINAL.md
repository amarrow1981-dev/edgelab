# EdgeLab — Session Briefing Document
*Last updated: Session 16 — 5 April 2026 (final)*

---

## What EdgeLab Is

A multi-layer football prediction engine designed to go beyond standard statistics.
The core insight: **uncertainty itself is information** — detecting when a match is
unpredictable and using that to make smarter calls, particularly on upsets and draws.

**The edge is in the signals nobody else is correlating.** Anyone can build a form +
home advantage model. EdgeLab's advantage comes from unconventional external signals —
weather, world mood, public holidays, fixture timing, travel load, motivation, referee
patterns — correlated against outcomes across thousands of matches. DPOL validates
which signals actually matter. Gary communicates them in plain English.

**Owner:** Andrew Marrow
**Company:** Khaotikk Ltd (name decided session 16 — khaotikk.com acquired)
**Current status:** Engine built and validated. DataBot live (API-Football Pro).
Full forward-prediction workflow operational. Gary built, tested, live.
Draw intelligence (~D flag) performing strongly in live conditions.
External Signal Layer Phase 1 built, wired, extended to all 17 tiers.
Phase 2 weather bot built and wired (edgelab_weather.py).
European DPOL run complete. --tier all run complete. All 17 tiers evolved, params saved.
Acca builder live (edgelab_acca.py). First moist run Easter Monday 6 April 2026.
E0 first time above 50% (50.2%). Signal weights all dormant — dedicated activation run needed.

**Market baseline:** ~49% (E0). EdgeLab E0 currently at **50.2%** on 8,669 matches.

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
- ADHD hyperfocus is the superpower — the engine was built in 9 sessions on a phone then a laptop

---

## Collaboration Protocol

### Claude's responsibilities

- Act as project manager — sequence the work, hold the roadmap, don't let ideas jump the queue
- Build immediately only if it makes the current model work better right now. Otherwise park it.
- Evaluate ideas, don't just validate them
- Track parked ideas and reintroduce at the right moment
- Run scalability check at session close without being prompted
- Generate updated briefing doc at session close without being prompted
- Remind Andrew to git commit at session close with suggested message
- Rebrief from project knowledge every 8-10 substantive exchanges, immediately after any product tangent

### Andrew's responsibilities

- Brain dumps are fine — Claude will filter and sequence
- Say "parking that" to log and move on
- Say "just build it" when discussion isn't needed
- Call out anything that feels off immediately
- Trust the gut on product and signal ideas — expect Claude to push back on timing

---

## Build Philosophy

- Build one thing. Test it. Improve or remove it. Move on.
- Build immediately only if it makes the current model work better right now
- Everything else goes on the parked list in the right place
- All Gary architecture decisions must remain gender-neutral at code level — personality lives in prompts only

---

## Core Design Philosophy

Every component must be built with scalability and future integration in mind.

- `edgelab_params.json` is SQLite-forward by design
- DataBot architecture is reusable across all sports
- Gary's brain schema has named SLOT entries for every future capability

---

## Session Closing Protocol

Before closing every session Claude must:
1. Ask: **Has today's work introduced any new scalability debt?**
2. Generate updated briefing doc
3. Remind Andrew to git commit with suggested message
4. Remind Andrew to upload updated briefing doc and changed .py files to project knowledge

**Current known scalability debt:**
- GaryBrain loads full dataset into memory per instantiation — needs caching before public launch
- No API wrapper around Gary — needed before app integration
- params.json write contention at scale — SQLite migration resolves this
- Gary's weather fetch makes a live API call per fixture — needs pre-fetch + cache per matchday before public launch

---

## Company & Brand

**Company name:** Khaotikk Ltd
**Domain:** khaotikk.com (acquired 5 April 2026, £8.37/yr)
**Existing domains:** garyknows.com, everyoneknowsagary.com
**Companies House:** Not yet registered — £100, do before taking revenue
**Trademark:** File before public launch. UK IPO ~£170-200 per class.
File for: EdgeLab, Gary, Gaby, Khaotikk, garyknows, "Everyone knows a Gary"

**Brand structure:**
- Khaotikk Ltd — parent company
- EdgeLab — data/analytics platform
- Gary — AI football analyst (consumer product)
- Gaby — female analyst, same engine (future)

---

## Product Vision — Gary

**No last name. Nobody knows it. Something to do with Sandra from the shop.**
Tagline: **"Everyone knows a Gary."**

- Knowledgeable but never arrogant
- Honest when uncertain — "this one's a coin flip mate, I'd leave it"
- Has opinions, explains them, occasionally wrong, always transparent
- Delivered via Claude API

### Gary Interface Stack (parked — future)

- WhatsApp-style UI — tips and accas as push notifications from a mate
- Proactive personalised texts — Gary checks in about fixtures he knows you care about
- Incoming call notification — one tap answers, feels like picking up from a mate
- Proactive video calls — Gary rings with the big tips
- On-demand FaceTime — you ring Gary when you want his read
- Launch moment — text launches first. Gary rings on a pixelated Nokia to announce video upgrade. The upgrade is a plot point.

### Gary Modes

- **Standard Gary** — knowledgeable mate, honest, warm, plain English
- **Gary Unfiltered** — pub version. Swears a bit. User opt-in setting.

### Gary Features (parked — future)

- **Gary remembers you** — logs recommendations, whether backed, result. "You didn't listen last week." Not yet built — memory SLOTs empty.
- **Confidence calibration display** — running track of whether confidence bands actually hit
- **Gary spots bookmaker edge** — flags engine confidence vs implied probability. Premium tier.
- **Devil's Gary** — shadow Gary who always takes the opposite position. Great TikTok content.
- **Printable acca slip** — formatted bet slip for bookies counter
- **Direct bookmaker integration** — Gary loads bet into user's account. Needs track record first.
- **Bookmaker advertising** — sponsored placements in free tier

### Gaby

Same engine, same DPOL, same brain schema as Gary. Distinct voice and personality.
Women's football specialism. Build when Gary is stable. Estimated one week of work.
Architecture already supports it — system prompt is the only Gary-specific thing.

### Sports Expansion (parked)

Cobey (basketball), Cooper (American football), Rico (baseball).
Same DPOL brain, different data + personality.

### Long Term Vision

Khaotikk as sports data platform. Own the data layer. World's best sports analytics site.
Light years away — revisit when Gary has revenue and user base.

---

## Freemium Tier Structure

| Tier | Price | Features |
|------|-------|----------|
| Free | £0 | Chat with Gary, basic predictions, bookmaker ads |
| Regular | £5-10/month | Full predictions, confidence, chaos ratings, pre-generated accas |
| Serious Punter | £15-20/month | DTI breakdown, draw intelligence, upset flags |
| The Edge | £25-30/month | Team Chaos Index, upset patterns, bogey alerts, bespoke live acca builder |

---

## Beta Launch Targets

- **August 2026** — working beta, free tier live, first paying users
- **End of 2026** — revenue from subscriptions (not betting dependent)

### Pre-Launch Marketing

- Email newsletter — Gary's tips, stats, accas. Build list before launch. Mailchimp free tier.
- Landing page — Claude can build
- Paid social — Facebook/Instagram, football + betting interest targeting. £5-10/day to start.

---

## Self-Funding Protocol

Small stake per round on Gary's acca selections. All returns back into the build.
Real money = most honest feedback loop. Live accuracy record starts from first bet.

**First moist run: Easter Monday 6 April 2026**
- Leyton Orient & Yes (Result/BTTS) — 5/1
- Derby & Yes (Result/BTTS) — 3/1
- Plymouth & Yes (Result/BTTS) — 3/1
- Treble: 95/1 (+5% acca boost, Bet365)
- Results: TBC — log in session 17

---

## Architecture

```
Match Data (CSV / API)         External Signal Sources
        |                               |
        |              ┌────────────────┤
        |              │  Weather       │ Open-Meteo [BUILT S16]
        |              │  Ground data   │ 481 entries, all 17 tiers [ACTIVE]
        |              │  Calendar      │ Bank holidays, fixture timing [ACTIVE]
        |              │  Referee       │ Already in CSVs [ACTIVE]
        |              │  Motivation    │ Derived from standings [ACTIVE]
        |              │  [Injury]      │ SLOT — future
        |              │  [Sentiment]   │ SLOT — future
        |              └────────────────┤
        |
Pre-processor → Feature Engine → Prediction Engine → DPOL → DataBot
        |
Output: H/D/A + confidence + DTI + chaos tier + draw score + scoreline + btts
        + upset_score + upset_flag + external signal context
        |
Gary — full match briefing via --gary flag
        |
Acca Builder (edgelab_acca.py) — two-stage, five acca types [BUILT S16]
```

---

## Files

| File | Status | Notes |
|------|--------|-------|
| edgelab_engine.py | Updated S16 | w_weather_signal added |
| edgelab_dpol.py | Updated S16 | w_weather_signal added |
| edgelab_runner.py | Updated S15 | All 17 tiers |
| edgelab_config.py | Updated S16 | Phase 1 + Phase 2 signal display |
| edgelab_params.json | Updated S16 | All 17 tiers evolved |
| edgelab_signals.py | Final S15 | 481 ground coords, all Phase 1 signals |
| edgelab_weather.py | New S16 | Phase 2 weather bot |
| edgelab_gary_brain.py | Updated S16 | Weather live, SLOT promoted |
| edgelab_gary_context.py | Final S15 | Tier vocabulary, all 17 tiers |
| edgelab_gary.py | Final | Gary API wrapper |
| edgelab_databot.py | Final S15 | English IDs verified. European NOT YET WIRED. |
| edgelab_predict.py | Final | Full prediction pipeline |
| edgelab_acca.py | New S16 | Two-stage acca builder |
| edgelab_gridsearch.py | Final | Draw intelligence grid search |

---

## API-Football League IDs

### English — verified
| Tier | ID |
|------|----|
| E0 | 39 |
| E1 | 40 |
| E2 | 41 |
| E3 | 42 |
| EC | 43 |

### European — confirmed from public sources, NOT YET WIRED INTO DATABOT
| Tier | ID | Notes |
|------|----|-------|
| SP1 | 140 | La Liga |
| SP2 | 141 | La Liga 2 |
| D1 | 78 | Bundesliga |
| D2 | 79 | 2. Bundesliga |
| I1 | 135 | Serie A |
| I2 | 136 | Serie B |
| N1 | 88 | Eredivisie |
| B1 | 144 | Belgian Pro League |
| SC0 | 179 | Scottish Premiership |
| SC1 | 180? | Needs live verification |
| SC2 | 181? | Needs live verification |
| SC3 | 182? | Needs live verification |

**Wire European IDs into DataBot before next weekend. Priority.**

---

## Dataset

417 CSV files, 25 years, 17 tiers, 137,645 matches. Hash: 580b0f3a1667

---

## Evolved Params — Final

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

## Known Issues

- **2-1 scoreline bias** — disproportionate 2-1 predictions. Investigate distribution.
- **Zero draws predicted** — 0 draws from 45 Easter Monday predictions. Draw floor needed at high DTI.
- **Acca builder identical output bug** — result/safety/value accas producing same picks.
- **E1 home bias** — high DTI matchdays default to H on every match.
- **Signal activation** — all weights dormant. Needs locked-params signal-only DPOL pass.

---

## Ordered Work Queue

### Session 17 — priorities in order

1. **Log Easter Monday moist run results** — day one of the track record
2. **Wire European league IDs into DataBot** — before next weekend's card. Unlocks 150-200 matches for acca builder.
3. **Fix acca builder identical output bug**
4. **Fix 2-1 scoreline bias** — investigate and add variety
5. **Verify SC1/SC2/SC3 DataBot IDs** — live test fetch
6. **Dedicated signal activation DPOL run** — lock core params, search signal weights only
7. **Pre-launch email newsletter** — landing page + Mailchimp
8. **Weather batch run** — get_weather_batch_chunked() on full 137k dataset overnight
9. **Companies House** — Khaotikk Ltd registration, £100

---

## How to Run

```bash
python edgelab_databot.py --key YOUR_KEY --days 7
python edgelab_predict.py --data history/ --fixtures databot_output/YYYY-MM-DD_fixtures.csv
python edgelab_acca.py predictions/YYYY-MM-DD_predictions.csv --all-types
python edgelab_runner.py history/ --tier all --boldness small
python edgelab_config.py show
python edgelab_weather.py "Wigan Athletic" "2026-04-12" 15 E2
```

---

## How to Resume

1. Upload this briefing doc to project knowledge (replace old version)
2. Upload changed .py files + edgelab_params.json
3. Claude confirms files received and is fully up to speed
4. Work ordered queue from the top
