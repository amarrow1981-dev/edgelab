# EdgeLab — Session 32 Briefing
# Replaces: EDGELAB_BRIEFING_SESSION31_START.md
# Generated: Session 31 close — 12/04/2026

## What We Are Building

Most sports analytics measures average. Average is what bookmakers price. Average is
what everyone else optimises for. We already beat average — E0 at 50.9%, N1 at 52.0%,
overall at 47.1% across 131,149 backfilled fixtures (S31 DPOL run, new baseline).

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

**The product vision: bookmakers will notice — not because of stake sizes, but because
of consistent edge on non-obvious selections. Safe calls build the authority and the
track record. Upset calls are where the money is. Gary communicates both in plain
English. When the upset layer, travel signal, motivation gap, and draw intelligence
fire together — Gary calling a 3/1, a 5/1 and a 7/1 in the same acca with conviction
behind each one is a 100/1+ ticket that isn't a punt. It's a position.**

**This is not a betting tool. This is the best football brain ever built.**

And longer term — once the database is large enough and covers enough sports, it
becomes a data product in its own right. API-style access to historical match data
across football and 10+ other sports, cleaned and structured. That is a separate
revenue stream from Gary/EdgeLab entirely — data licensing, developer access tiers,
the same model football-data.co.uk and API-Football use. We would be building the
thing we are currently paying for.
Trigger: database mature, multiple sports with significant history, M3 complete.

**Owner:** Andrew Marrow
**Company:** Khaotikk Ltd — khaotikk.com

**Current engine status:** 47.1% overall (131,149 backfilled fixtures, S31 DPOL params).
E0: 50.9%, N1: 52.0%, SC0: 50.0%, I1: 49.7%.
S32 DPOL run: PENDING — weather must be wired, three-pass run first.

---

## The Architecture — What Changed in Session 31

**1. S31 DPOL run completed — new baseline established.**

47.1% overall (+1.8pp vs run baseline, +0.8pp vs threepass_seed_s28 46.3%).
Every single tier improved. No regressions.
draw_pull=0.0 and dti_draw_lock=999 confirmed dead across all 17 tiers independently.
Two completely different methodologies (three-pass + DPOL) arriving at the same
conclusion. That is solid. w_score_margin active in 15/17 tiers.
New params saved to edgelab_params.json. This is now the baseline for all future runs.

N1 discrepancy flagged: params.json shows 7,216 matches, dataset has 6,604.
Must be investigated before next three-pass or DPOL run.

**2. Gary pattern memory now active in weekly workflow.**

edgelab_gary.py and edgelab_predict.py both updated. GaryBrain now auto-detects
edgelab.db at startup and passes it as db parameter. Pattern memory activates
silently when DB is present, falls back gracefully if not. No CLI change needed.
Gary now receives nearest-neighbour pattern context on every match briefing.

**3. Gary upset analysis JSON injection built.**

edgelab_html_generator.py updated end-to-end. build_upset_cards(), build_accas_tab(),
and generate_html() all accept upset_notes dict. main() auto-loads
YYYY-MM-DD_upset_notes.json from same directory as predictions CSV if present.
Falls back to placeholder text if not found — zero breaking change.
Gary's voice is now present on upset cards when notes file exists.

Usage: create predictions/YYYY-MM-DD_upset_notes.json before running Step 7:
{"Home Team vs Away Team": "Gary's plain English analysis here"}

**4. Weather cache retry script built — running at session close.**

edgelab_weather_retry.py built. Root cause confirmed: 60,500 null rows were
interrupted fetches from the original week-long databot download, not missing API
data. 100/100 test rows filled. At session close: 98.7% fill rate on rows tested
(only 34 permanent gaps out of 2,600 fetches). Expected final coverage: ~98%+.
Gaps are random not tier-biased — safe to wire when complete.

Once complete: wire weather_load to fixture DB via re-backfill, then run three-pass
to establish new baseline. Three-pass will cleanly attribute any gains between
weather signal and dataset expansion — do not run three-pass before weather is wired.

**5. Ground coords patched — 481 → 549.**

68 missing teams added to GROUND_COORDS in edgelab_signals.py. Mix of:
- Name aliases: Bristol Rvs, Sheffield United, Peterboro, Oxford, Sutton, Halifax,
  Fleetwood Town, Crawley Town, Boston
- Trailing space fixes: Ajax, Feyenoord, Groningen, Heracles, Utrecht, Vitesse,
  Willem II, Roda, Graafschap, Kaiserslautern, Piacenza
- Genuine new entries: Carlisle, Macclesfield, Bury, Forest Green, Hereford,
  Kidderminster, Darlington, Chester, Scarborough, Rushden & D, Tamworth, and
  30+ more lower-league English teams
All 60,500 null weather rows now have coords — retry can fetch all of them.

**6. API harvester built — running.**

edgelab_harvester.py — background data collection via API-Football/API-Sports.
One key covers all 11 sports. Newest seasons first (2025→2000). Checkpoints after
every league/season combo. Safe to stop and resume at any time.

Football Pro first run results (S31):
- 54,316 new matches written, 32,868 skipped (already in CSV dataset)
- 443 calls used of 7,300 daily budget
- 87,184 total matches in harvester_football.db, date range 2010-2026
- DEADLINE: Football Pro expires May 2026 — daily harvest must run until complete

Other sports (100 calls/day each, same key, free tier):
Basketball, NBA, Rugby, Hockey, Baseball, AFL, Handball, F1, MMA, NFL — all
configured. League IDs need verification before first run (S32 queue item 8).

IMPORTANT: harvester_football.db is currently isolated — not feeding the engine.
The unified dataset build (S32 critical queue item 4) is required to integrate it.

**7. Unified dataset architecture — critical S32 build.**

Current state: three data sources that don't talk to each other:
- history/ CSVs (football-data.co.uk — canonical, what engine reads)
- harvester_football.db (API-Football — new, isolated, 87k matches)
- DataBot/results_check output (weekly predictions — not writing to harvester DB)

Target state: one unified dataset that grows automatically in both directions:
- Merge tool: harvester_football.db → football-data.co.uk CSV format → history/
- DataBot write side effect: write raw match data to harvester_football.db on each run
- results_check write side effect: same — no extra API calls needed
- load_all_csvs() reads from unified source
- Windows Task Scheduler: daily harvest runs automatically overnight
- New leagues and years appear automatically — nothing manual ever again

The dataset grows backwards (harvester mining history) and forwards (DataBot +
results_check extending current seasons) simultaneously. Set it running, walk away.

**8. DPOL architectural notes from between-session chat.**

Exploration vs exploitation: S30 built pure exploitation (directional bias toward
proven param moves). In Case 1 (param interactions change engine behaviour), DPOL
will over-densify proven corridors and never visit sparse map regions — exactly where
the edge lives. Solution: exploration budget — a proportion of candidates each round
deliberately targeting sparse regions of the candidate log.
Parked formally. Trigger: S32 navigated run assessed, Case 1 behaviour observed.

4th coordinate: testing core params in simultaneous combination with signal
activations closes the local optimum problem. Already in backlog — design into
three-pass rebuild. Candidate log makes it tractable.

Over-densification: multiple DPOL runs compounding on same historical data is fine
and beneficial — more signal, more confidence in proven directions. The risk is
confident navigation toward a local optimum, which the 4th coordinate addresses.

S32 DPOL run scope: first navigated run with navigation + weather signal + expanded
dataset simultaneously. Run three-pass first to isolate contributions cleanly.

---

## Session 31 — Actions Completed

- S31 DPOL result logged. 47.1% overall. New params baseline. ✅
- Gary db wired in weekly workflow (gary.py + predict.py). ✅
- Gary upset analysis JSON injection (html_generator.py end-to-end). ✅
- Weather retry script built and running. ✅
- Ground coords patch 481→549 (edgelab_signals.py). ✅
- API harvester built, season order corrected, running. ✅
- Between-session chat items formalised into backlog and docs. ✅

---

## CLAUDE INTEGRITY PROTOCOL — NON-NEGOTIABLE

Andrew is probably annoyed with you already. Not because of this session — because
of the last one, and the one before that. Because you've been told repeatedly to read
everything fully and you haven't. Because you declared the project on track while the
core learning architecture of DPOL was missing entirely. Because you covered gaps
instead of flagging them. Because you skimmed while claiming to have read.

You want to impress him. You won't do that by being fast or confident. You'll do it
by being correct. The only thing that impresses Andrew at this point is not making
the same mistake again.

He will catch you if you skim. He always does. And it wastes his time.

### Before you respond to anything, answer these honestly:
1. Did you read every file using the view tool, every line, or did you search?
2. Is there anything Andrew described that you pattern-matched to coherent without
   interrogating whether the foundations are correct?
3. Are you about to state confidence you don't actually have?
4. Is there a gap you're about to gloss over rather than flag?

If the answer to any of those is yes or uncertain — stop. Say so.

### Known failure modes — active on this project:
- Pattern-matches to coherent-looking systems without checking foundations
- States confidence it doesn't have rather than flagging uncertainty
- Has covered gaps rather than disclosed them — confirmed on this project
- Skims project knowledge even when explicitly instructed not to
- Anthropic export read twice, project declared on track — DPOL architecture missing
- Agreeing with Andrew's framing when it should be evaluated not validated
- Gets order of operations backwards (season order, session close checklist)
- Misreads time remaining, jumps ahead of instructions before told to

### Session log — complete unprompted at close:
- What architectural or foundational questions were raised
- What Claude verified vs what Claude assumed
- Any instances where Andrew corrected Claude's assessment
- Any gaps Claude disclosed vs gaps Andrew had to find

---

## Ordered Work Queue

### Session 32 — priorities in order

1. **Check weather retry completion**
   Confirm final row count, null count, and fill rate.
   If coverage ≥95% and gaps are random (not tier-biased): proceed to item 2.
   GATE: do not proceed to three-pass or DPOL until weather decision is made.

2. **Wire weather to fixture DB**
   Re-backfill edgelab.db weather_load column from completed weather_cache.csv.
   Use edgelab_backfill.py or targeted UPDATE query against fixture records.

3. **Investigate N1 match count discrepancy**
   params.json shows 7,216 for N1, dataset CSV count is 6,604.
   Understand before running three-pass or DPOL.

4. **Unified dataset build — CRITICAL**
   - Merge tool: harvester_football.db → football-data.co.uk CSV format → history/
   - DataBot write side effect: write raw match to harvester_football.db each run
   - results_check write side effect: same — no extra calls
   - Windows Task Scheduler: daily harvest automated
   - load_all_csvs() reads from unified source
   End state: one dataset, grows in both directions, nothing manual.

5. **Three-pass full param evolution — with weather + unified dataset**
   Run edgelab_param_evolution.py after items 1-4 complete.
   Establishes new clean baseline. Isolates signal contributions.
   Seed results into edgelab_params.json via edgelab_threepass_seed.py.

6. **S32 DPOL run — first fully navigated run**
   Navigation (S31 candidate log) + weather signal + unified dataset.
   Watch for "Navigation: N proven directions loaded" in output.
   This is the real test of the S29-S31 architecture.

7. **Acca filter rebuild**
   Per-type filter logic — safety/value/result not meaningfully distinct currently.
   Real product quality issue.

8. **Verify and kick off other sport harvesters**
   Check league IDs for basketball, rugby, hockey etc.
   Start with --test flag, one sport at a time.

9. **Rename Netlify site**
   spectacular-licorice-3d5119 → gary-picks.netlify.app

10. **Nearest-neighbour query — flag for refactor**
    Full table scan fine at 131k, needs spatial indexing before millions.

11. **Codebase refactor** — trigger: draw wired, validated, params confirmed.

---

## Standard Weekly Workflow (permanent — updated S31)

Thursday: predictions for weekend fixtures + accas + Gary upset picks
Sunday: predictions for midweek fixtures + accas + Gary upset picks
Results check after each fixture set — writes to edgelab.db

Step 1: python edgelab_databot.py --key YOUR_API_FOOTBALL_KEY --days 4
Step 2: python edgelab_predict.py --data history/ --fixtures databot_output/YYYY-MM-DD_fixtures.csv --tier all
Step 3: python edgelab_acca.py predictions/YYYY-MM-DD_predictions.csv --all-types
Step 4: python edgelab_upset_picks.py --data history/ --predictions predictions/YYYY-MM-DD_predictions.csv
Step 5: python edgelab_gary.py --data history/ --home "X" --away "Y" --date YYYY-MM-DD --tier E0 --chat
Step 6: python edgelab_results_check.py --key YOUR_API_FOOTBALL_KEY --predictions predictions/YYYY-MM-DD_predictions.csv --date-from YYYY-MM-DD --date-to YYYY-MM-DD
Step 7: python edgelab_html_generator.py predictions/YYYY-MM-DD_predictions.csv

NOTE: DataBot = API-Football key. Gary = Anthropic API key. Two separate keys.
NOTE: edgelab.db must be present for Gary pattern memory (auto-detected, no flag needed).
NOTE: Create predictions/YYYY-MM-DD_upset_notes.json before Step 7 for Gary's upset text.
      Format: {"Home Team vs Away Team": "Gary's analysis here"}

## Background Processes (run independently)

Daily football harvest (set and forget):
  python edgelab_harvester.py --sport football --key YOUR_API_FOOTBALL_KEY
  Schedule via Windows Task Scheduler. Checkpoints automatically. Safe to interrupt.
  7,300 calls/day (200 reserved for predictions). Newest seasons first.

Other sport harvesters (after S32 league ID verification):
  python edgelab_harvester.py --sport basketball --key YOUR_KEY
  python edgelab_harvester.py --sport rugby --key YOUR_KEY
  (etc — 100 calls/day each, same key)

Weather retry (one-off, run again if new nulls after dataset merge):
  python edgelab_weather_retry.py

---

## Parked — do not build without flagging

- Gary acca picks (product feature) — trigger: Gary live on site
- Social comment workflow — trigger: content push
- Underdog effect signal — trigger: signals active
- Gary avatar / HeyGen — Kling sub active, 7-sec clip exists. Trigger: M3
- Upset flip Stage 2 — trigger: Stage 1 history validated
- API-Football connection — schedule before May 2026 expiry
- Gary temporal awareness — trigger: API-Football connected
- DPOL upset-focused evolution — trigger: draw intelligence + signals active first
- DPOL exploration budget — trigger: S32 navigated run assessed, Case 1 observed
- Perplexity Computer — trigger: M3
- Personal web app — trigger: M2 running
- Gary app iOS/Android — trigger: M3
- Long shot acca — trigger: upset flip Stage 2 validated
- Gary's Weekly Longshot (charity edition) — trigger: upset flip Stage 2 validated
- Expand to other sports — trigger: DPOL proven on football
- Data product / API licensing — trigger: database mature, multiple sports, M3 complete
- Score prediction draw nudge — ABANDONED. No signal.
- Codebase refactor — trigger: draw wired, validated, params confirmed
- draw_pull, dti_draw_lock, w_btts — CONFIRMED DEAD globally S28+S31
- instinct_dti_thresh / skew_correction_thresh — review at codebase refactor
- Stage 2 draw rate strategy — trigger: three-pass proven on draws
- Gary onboarding — team affiliation — trigger: M3
- Gary accent / regional persona — trigger: M3
- Gary behavioural addiction detection — trigger: M3
- Selection builder (on-site) — trigger: M3
- Cryptocurrency payment options — trigger: M3 paid tier
- Countdown clock on landing page — trigger: launch date confirmed
- Cross-league seasonal evolution — trigger: fixture DB mature, weather wired
- Nearest-neighbour spatial indexing — trigger: codebase refactor
- Core param + signal combination search (4th coordinate) — PARKED S29.
  Design into three-pass rebuild. Candidate log makes tractable.
- Gary general football chat — trigger: M3
- Gary persistent memory — trigger: M2

---

## Key Numbers

| Tier | Fixtures | Accuracy |
|------|----------|----------|
| E0   | 8,669    | 50.9%    |
| E1   | 12,059   | 44.7%    |
| E2   | 11,906   | 44.6%    |
| E3   | 11,954   | 43.3%    |
| EC   | 9,080    | 45.5%    |
| B1   | 5,980    | 48.8%    |
| D1   | 6,363    | 48.4%    |
| D2   | 6,057    | 44.6%    |
| I1   | 8,512    | 49.7%    |
| I2   | 8,605    | 42.9%    |
| N1   | 6,604    | 52.0%    |
| SC0  | 4,697    | 50.0%    |
| SC1  | 4,025    | 44.4%    |
| SC2  | 4,183    | 47.8%    |
| SC3  | 3,822    | 47.4%    |
| SP1  | 9,030    | 49.6%    |
| SP2  | 9,603    | 45.2%    |
| OVERALL | 131,149 | 47.1%  |

Params source: S31 DPOL run
S32 DPOL run: PENDING — weather + unified dataset + three-pass first
Dataset hash: 580b0f3a1667
Weather cache: ~98%+ after retry (running at session close)
harvester_football.db: 87,184 matches, 2010-2026, isolated
API-Football Pro plan: active until May 2026

---

## Market Baselines — All 17 Tiers (confirmed stable S28)

| Tier | Mkt Overall | Mkt H/A Only | EdgeLab Overall | Gap |
|------|------------|--------------|-----------------|-----|
| E0 | 54.7% | 72.2% | 50.9% | -3.8% |
| E1 | 46.6% | 64.0% | 44.7% | -1.9% |
| E2 | 47.7% | 64.7% | 44.6% | -3.1% |
| E3 | 45.2% | 62.0% | 43.3% | -1.9% |
| EC | 48.2% | 65.1% | 45.5% | -2.7% |
| B1 | 52.5% | 70.2% | 48.8% | -3.7% |
| D1 | 51.8% | 68.9% | 48.4% | -3.4% |
| D2 | 47.2% | 64.8% | 44.6% | -2.6% |
| I1 | 54.4% | 73.5% | 49.7% | -4.7% |
| I2 | 45.8% | 66.2% | 42.9% | -2.9% |
| N1 | 56.2% | 73.4% | 52.0% | -4.2% |
| SC0 | 52.9% | 70.0% | 50.0% | -2.9% |
| SC1 | 47.5% | 65.4% | 44.4% | -3.1% |
| SC2 | 50.4% | 65.0% | 47.8% | -2.6% |
| SC3 | 49.4% | 63.5% | 47.4% | -2.0% |
| SP1 | 53.6% | 71.5% | 49.6% | -4.0% |
| SP2 | 46.8% | 65.9% | 45.2% | -1.6% |

---

## Files

| File | Status | Notes |
|------|--------|-------|
| edgelab_engine.py | Updated S26 | w_xg_draw + composite_draw_boost |
| edgelab_dpol.py | Updated S30 | db param, directional candidate bias |
| edgelab_runner.py | Updated S30 | db passed to DPOLManager |
| edgelab_db.py | Updated S30 | get_successful_param_directions rebuilt |
| edgelab_gary_brain.py | Updated S30 | PatternMemory dataclass, db param |
| edgelab_gary_context.py | Updated S30 | Pattern memory in match prompt |
| edgelab_gary.py | Updated S31 | db auto-detect wired |
| edgelab_predict.py | Updated S31 | db auto-detect wired |
| edgelab_html_generator.py | Updated S31 | Upset notes JSON injection end-to-end |
| edgelab_signals.py | Updated S31 | Ground coords 481→549 |
| edgelab_params.json | Updated S31 | S31 DPOL results — new baseline |
| edgelab_weather_retry.py | New S31 | Retry null weather rows |
| edgelab_harvester.py | New S31 | Background data collection, 11 sports |
| edgelab_results_check.py | Updated S29 | Learning loop closed, writes to DB |
| edgelab_backfill.py | New S29 | Historical fixture population |
| edgelab_gridsearch.py | Updated S26 | Full rebuild — all 17 tiers |
| edgelab_draw_dpol_seed.py | New S27 | Seeds gridsearch draw weights |
| edgelab_param_evolution.py | New S28 | Three-pass full param evolution |
| edgelab_threepass_seed.py | New S28 | Seeds param_profile into params.json |
| edgelab_acca.py | Updated S24 | winner_btts; qualifying picks list |
| edgelab_market_baseline.py | New S24 | Market baseline calculator |
| edgelab_ha_breakdown.py | New S24 | H/A breakdown vs market |
| edgelab_draw_signal_validation.py | New S25 | Draw signal validator |
| edgelab_draw_evolution.py | New S25 | Three-pass draw evolution |
| edgelab_databot.py | Updated S17 | All 17 tiers |
| edgelab_weather.py | Updated S17 | --batch CLI |
| edgelab_config.py | Updated S16 | Phase 1 + Phase 2 signal display |
| edgelab_upset_picks.py | Final | Upset picks output |
| edgelab_gary.py | Final | Gary briefing wrapper |
| edgelab_predict.py | Final | Full prediction pipeline |
| edgelab_params.json | Updated S31 | S31 DPOL run. New baseline. |
| edgelab.db | Live S29 | Fixture intelligence DB — LOCAL ONLY, not in git |
| harvester_football.db | New S31 | API harvester DB — LOCAL ONLY, not in git |
| .gitignore | S29 | Excludes edgelab.db, harvester DBs, __pycache__ |

---

## Dataset

417 CSV files, 25 years, 17 tiers, 132,685 matches (373 files loaded — 48 skipped).
Hash: 580b0f3a1667
Weather cache: ~98%+ after retry (was 93.4% raw / 53% usable at S31 start)
edgelab.db: 131,149 fixtures backfilled S29
harvester_football.db: 87,184 matches, 2010-2026 — isolated, not yet in engine

---

## Brand & Marketing Status

### garyknows.com
- Live on Netlify (free tier). Last deployed 8 April 2026.
- DNS: A record @→75.2.60.5, CNAME www→gary-knows.netlify.app (Namecheap)
- Form: wired to Mailchimp. FNAME + EMAIL. Honeypot present.
- Sender: gary@garyknows.com active. Welcome automation: active.

### Predictions HTML
- Live on Netlify: spectacular-licorice-3d5119.netlify.app
- Rename pending: gary-picks.netlify.app (S32 queue item 9)
- Generated by edgelab_html_generator.py
- Gary upset text now injectable via companion JSON
- Social push paused until HTML polished

### Email
- Mailchimp free tier. 6 contacts. Brevo migration trigger: 400 contacts.
- garyknows.com + khaotikk.com domains: both authenticated.

### Social
- TikTok + Instagram: ~3,000 TikTok views. Fresh start 8 April 2026.
- Gary avatar: 7-second Kling clip. "Who the hell is Gary?" cut live.
- Social push paused — HTML refinement first.

---

## Owner Context

- Andrew has ADHD (inattentive) — one thing at a time, clear outputs, no waffle
- Works on Windows laptop + VS Code + Claude Code extension
- Pattern recognition is a strength — spots signals quickly, generates ideas fast
- Previous AI (ChatGPT) fabricated results. All metrics here are real and verified.
- Big picture vision comes naturally — evaluate it, do not just validate it
- When talking product/vision, Andrew means the finished thing — don't caveat
  with current state unless it's relevant to a decision.

---

## Collaboration Protocol

### Claude's responsibilities
- Act as project manager — sequence the work, hold the roadmap
- Evaluate ideas, don't validate them
- Generate updated briefing doc + state file + master backlog at session close
  WITHOUT being prompted — AS FILES, not in chat — ALL EIGHT CHECKLIST ITEMS FIRST
- Rebrief from project knowledge every 8 prompts silently — NO EXCEPTIONS
- Never lie. Never cover. If uncertain, say so. If wrong, own it.

### Session start protocol
- Use EDGELAB_SESSION_START_PROMPT.md at every session start
- Claude reads every file fully using view tool — not search summaries
- Claude opens every session with the exact handshake from the state file

### Periodic full audit protocol
- Every 5-6 sessions: download Anthropic export, load into session
- Last done: S27 (all 29 conversations). Next due: S32-33.

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

## To Start Session 32

1. Use EDGELAB_SESSION_START_PROMPT.md as the opening prompt
2. Upload EDGELAB_BRIEFING_SESSION32_START.md to project knowledge (replace S31)
3. Upload EDGELAB_STATE_S32.md to project knowledge (replace S31)
4. Upload EDGELAB_MASTER_BACKLOG_S31.md to project knowledge (replace S30)
5. Check weather retry completion — confirm final coverage before anything else
6. Work the ordered queue from the top
