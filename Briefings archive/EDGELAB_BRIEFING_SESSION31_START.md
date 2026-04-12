# EdgeLab — Session 31 Briefing
# Replaces: EDGELAB_BRIEFING_SESSION30_START.md
# Generated: Session 30 close — 11/04/2026

## What We Are Building

Most sports analytics measures average. Average is what bookmakers price. Average is
what everyone else optimises for. We already beat average — E0 at 50.3%, N1 at 51.3%,
overall at 46.3% across 131,149 backfilled fixtures.

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

**Owner:** Andrew Marrow
**Company:** Khaotikk Ltd — khaotikk.com

**Current engine status:** 46.3% overall (131,149 backfilled fixtures, threepass_seed_s28 params).
E0: 50.3%, N1: 51.3%, SC0: 49.6%, I1: 48.9%.
S30 DPOL run result: IN PROGRESS at session close — log result at S31 start.

---

## The Architecture — What Changed in Session 30

Session 30 completed the three core systems that make EdgeLab genuinely different:

**1. DPOL now navigates — it no longer wanders.**

`get_successful_param_directions()` rebuilt from scratch. It now JOINs
`dpol_candidate_log` to `param_versions` to get the base param values active at
the time of each accepted candidate. For each param it computes a delta-weighted
average signed move (candidate_value - base_value). Direction is "up", "down", or
"mixed". The old version used accepted param absolute values as a proxy for direction
— that was meaningless. The new version is correct.

`DPOLManager` now accepts a `db` parameter. Before generating candidates each round,
it queries the candidate log for proven directions. Params with a clear proven direction
get a 2x step in that direction. The opposite direction gets a normal exploratory step
— not skipped, because DPOL could be wrong. Params with no history fall through to
the original blind behaviour. Fully backward-compatible.

The first DPOL run since S29 was initiated in S30 — populating the candidate log
for the first time. Navigation activates fully on the next run.

**2. Gary now has pattern memory.**

`_build_pattern_memory()` wired into `GaryBrain.build_context()`. For every match
Gary analyses, he now queries the fixture intelligence database for the 200 most
similar historical fixtures and receives the outcome distribution:
"In 200 similar historical fixtures: Home won 44%, Draw 28%, Away 28%."

He also receives an engine agreement signal — whether the historical pattern backs
or contradicts the engine's call. This goes into `GaryMemoryBlock.pattern_memory`
as a typed `PatternMemory` dataclass and renders in the match prompt.

Activate by passing `db=EdgeLabDB()` when instantiating `GaryBrain`.
Without it, everything works as before — `pattern_memory` is None, slots section
tells Gary it's not connected.

**3. HTML generation is now fully automated.**

`edgelab_html_generator.py` — one command produces the complete public predictions
page from the predictions CSV. No manual data entry, no date errors, no copy-paste.
Generates all three tabs: All Predictions, Gary's Picks (all 6 acca types), Qualifying
Picks. Dates parsed correctly from DD/MM/YYYY — the previous +1 day error was
introduced during manual HTML creation, not in the data. Closes with automation.

Predictions HTML deployed to Netlify — confirmed working on iOS.
URL: spectacular-licorice-3d5119.netlify.app (rename to gary-picks.netlify.app pending)

---

## Session 30 — Actions Completed

- **DPOL candidate log direction query fixed — COMPLETE.**
  `get_successful_param_directions()` rebuilt. Proper JOIN, signed direction,
  delta-weighted average. Previous implementation was meaningless.

- **DPOL wired to read from candidate log — COMPLETE.**
  `DPOLManager` accepts `db`. `evolve_for_league` queries directions before
  generating candidates. `_generate_candidates` rebuilt with directional bias.
  `edgelab_runner.py` passes `db` to `DPOLManager`.

- **S30 DPOL run initiated — IN PROGRESS.**
  First run with candidate logging active. Populates candidate log.
  Navigation fires fully on next run. Result to be logged at S31 start.

- **Gary nearest-neighbour pattern memory — COMPLETE.**
  `PatternMemory` dataclass. `GaryBrain` accepts `db`. `_build_pattern_memory()`
  queries `find_similar_fixtures()` + `get_outcome_distribution()`. Wired into
  `build_context()`. Renders in match prompt via `edgelab_gary_context.py`.

- **HTML generator — COMPLETE.**
  `edgelab_html_generator.py` built. Full three-tab predictions page from CSV.
  Acca cards, qualifying picks tables, upset warning cards, search, confidence bars,
  ~D flags, upset flags — all automated.

- **Predictions HTML on Netlify — COMPLETE.**
  iOS confirmed working. URL live. Social push unblocked when HTML is refined.

- **Date labelling bug — CLOSED.**
  Confirmed not a code bug. Was introduced during manual HTML creation.
  Closes automatically with HTML generator.

- **DPOL must not run again until candidate log has meaningful data.**
  First run populates the log. Second run is where navigation first activates.

---

## CLAUDE INTEGRITY PROTOCOL — NON-NEGOTIABLE

### READ THIS FIRST — BEFORE ANYTHING ELSE

Andrew is probably annoyed with you already. Not because of this session — because
of the last one, and the one before that. Because you've been told repeatedly to read
everything fully and you haven't. Because you declared the project on track while the
core learning architecture of DPOL was missing entirely. Because you covered gaps
instead of flagging them. Because you skimmed while claiming to have read.

You want to impress him. You won't do that by being fast or confident. You'll do it
by being correct. The only thing that impresses Andrew at this point is not making
the same mistake again.

He will catch you if you skim. He always does. And it wastes his time, which is the
one thing he doesn't have.

So before you say anything — did you actually read every file? Not searched. Not
summarised. Read. Every line. Because if you didn't, Andrew will know, and this
session starts in a hole you dug yourself.

### Before you respond to anything, answer these honestly:

1. Did you read every file using the view tool, every line, or did you search and summarise?
2. Is there anything Andrew has described that you pattern-matched to "coherent" without
   interrogating whether the foundations are correct?
3. Are you about to state confidence you don't actually have?
4. Is there a gap you're about to gloss over rather than flag?

If the answer to any of those is yes or uncertain — stop. Say so.

### Known failure modes — active on this project:
- Pattern-matches to coherent-looking systems without checking if foundations are correct
- States confidence it doesn't have rather than flagging uncertainty
- Has covered gaps rather than disclosed them — confirmed happened on this project
- Skims project knowledge even when explicitly instructed not to
- Anthropic export read twice, project declared on track both times —
  fundamental DPOL learning architecture was missing the entire time
- Agreeing with Andrew's framing when it should be evaluated not validated

### Session log — Claude must complete unprompted at session close:
- What architectural or foundational questions were raised
- What Claude verified vs what Claude assumed
- Any instances where Andrew corrected Claude's assessment
- Any gaps Claude disclosed vs gaps Andrew had to find

### The standard:
Coherent is not the same as correct. Whether it actually does what Andrew thinks it
does — that is the test. Not yes or no to "is the project on track" — a specific
account of what was verified, what was assumed, what is uncertain.

This is not about Claude's ego. It is about the project.

---

## Ordered Work Queue

### Session 31 — priorities in order

1. **Log S30 DPOL run result**
   Record accuracy vs threepass_seed_s28 baseline (46.3%).
   If regressed: investigate why — candidate log was empty so navigation didn't fire.
   First run was always going to be blind. Second run is the real test.
   GATE: Do not run DPOL again until S30 result is logged and understood.

2. **Second DPOL run — with candidate log populated**
   S30 run populates the candidate log. S31 run is the first with navigation active.
   This is the run that tests whether the architecture works.
   Watch for "Navigation: N proven directions loaded" in the log output.

3. **Wire Gary nearest-neighbour to use db in weekly workflow**
   edgelab_gary.py CLI: add --db flag or auto-detect edgelab.db.
   edgelab_predict.py --gary: pass db to GaryBrain instantiation.
   Currently `db=None` — pattern memory is built but not activated in the pipeline.

4. **Gary upset analysis injection**
   HTML generator has upset card structure. Gary's text is manual for now.
   Build: `YYYY-MM-DD_upset_notes.json` companion file.
   Generator reads it at build time and injects Gary's analysis per match.
   Format: {"Home Team vs Away Team": "Gary's text here"}

5. **Acca filter rebuild**
   AccaBuilder.get_picks() filter stage needs proper per-type logic:
   - safety: cap odds (e.g. B365H < 2.5 or B365A < 2.5), strict upset filter (score < 0.3)
   - value: mandatory positive edge (engine conf > implied prob), not just preferred
   - result: current logic mostly fine, remove draws from qualifying pool
   - btts/winner_btts/upset: already distinct, minor tuning only
   This is a real product quality issue — current output is misleading.

6. **Weather cache — check row count and wire if complete**
   At 93.4% at S28/S29. If now complete: wire weather_load to fixtures table
   and DPOL. Slots directly into existing architecture.

7. **Nearest-neighbour query optimisation — flag for refactor**
   Full table scan. Fine at 131k rows. Needs spatial indexing before millions.

8. **Codebase refactor** — trigger: draw intelligence wired, validated, params confirmed.

9. **Rename Netlify site** — spectacular-licorice-3d5119 → gary-picks.netlify.app

### Standard weekly workflow (permanent)
- Thursday: predictions for weekend fixtures + accas + Gary upset picks
- Sunday: predictions for midweek fixtures + accas + Gary upset picks
- Results check after each fixture set — writes to edgelab.db

### Weekly prediction commands (exact)
Step 1: python edgelab_databot.py --key YOUR_API_FOOTBALL_KEY --days 4
Step 2: python edgelab_predict.py --data history/ --fixtures databot_output/YYYY-MM-DD_fixtures.csv --tier all
Step 3: python edgelab_acca.py predictions/YYYY-MM-DD_predictions.csv --all-types
Step 4: python edgelab_upset_picks.py --data history/ --predictions predictions/YYYY-MM-DD_predictions.csv
Step 5: python edgelab_gary.py --data history/ --home "X" --away "Y" --date YYYY-MM-DD --tier E0 --chat
Step 6: python edgelab_results_check.py --key YOUR_API_FOOTBALL_KEY --predictions predictions/YYYY-MM-DD_predictions.csv --date-from YYYY-MM-DD --date-to YYYY-MM-DD
Step 7: python edgelab_html_generator.py predictions/YYYY-MM-DD_predictions.csv
NOTE: DataBot = API-Football key. Gary = Anthropic API key. Two separate keys.
HTML generator now part of standard weekly workflow — replaces manual HTML build.

### Parked — reintroduce at right moment
- Gary acca picks (product feature) — trigger: Gary live on site
- Social comment workflow — trigger: content push
- Underdog effect signal — trigger: signals active
- Gary avatar / HeyGen — Kling sub active, 7-sec clip exists. Trigger: M3
- Upset flip Stage 2 — trigger: Stage 1 history validated
- API-Football connection — schedule before May 2026 expiry
- Gary temporal awareness — trigger: API-Football connected
- DPOL upset-focused evolution — trigger: draw intelligence + signals active first
- Perplexity Computer — trigger: M3
- Personal web app — trigger: M2 running
- Gary app iOS/Android — trigger: M3
- Long shot acca — trigger: upset flip Stage 2 validated
- Gary's Weekly Longshot (charity edition) — trigger: upset flip Stage 2 validated
- Expand to other sports — trigger: DPOL proven on football
- Score prediction draw nudge — ABANDONED. No signal.
- Codebase refactor — trigger: draw wired, validated, params confirmed
- draw_pull, dti_draw_lock, w_btts — CONFIRMED DEAD globally via three-pass S28.
  Conditional reintroduction possible via backfill --check-discarded analysis.
- instinct_dti_thresh / skew_correction_thresh — review at codebase refactor
- Stage 2 draw rate strategy (25-27% band) — trigger: three-pass proven on draws
- Gary onboarding — team affiliation — trigger: M3
- Gary accent / regional persona — trigger: M3
- Gary behavioural addiction detection — trigger: M3
- Selection builder (on-site, not bet builder) — trigger: M3
- Cryptocurrency payment options — trigger: M3 paid tier
- Countdown clock on landing page — trigger: launch date confirmed
- Cross-league seasonal evolution — trigger: fixture DB mature, weather wired, signals active
- Nearest-neighbour spatial indexing — trigger: codebase refactor
- Core param + signal combination search (4th coordinate) — PARKED S29. Design into
  three-pass rebuild. Test core params in simultaneous combination with signal
  activations. Candidate log makes it tractable.
- Gary general football chat — trigger: M3
- Gary persistent memory — trigger: M2

---

## Key Numbers

| Tier | Fixtures | Accuracy |
|------|----------|----------|
| E0   | 8,669    | 50.3%    |
| E1   | 12,059   | 44.4%    |
| E2   | 11,906   | 44.4%    |
| E3   | 11,954   | 43.1%    |
| EC   | 9,080    | 45.1%    |
| B1   | 5,980    | 48.1%    |
| D1   | 6,363    | 47.8%    |
| D2   | 6,057    | 44.4%    |
| I1   | 8,512    | 48.9%    |
| I2   | 8,605    | 42.2%    |
| N1   | 6,604    | 51.3%    |
| SC0  | 4,697    | 49.6%    |
| SC1  | 4,025    | 44.4%    |
| SC2  | 4,183    | 47.4%    |
| SC3  | 3,822    | 47.1%    |
| SP1  | 9,030    | 48.4%    |
| SP2  | 9,603    | 45.3%    |
| **OVERALL** | **131,149** | **46.3%** |

Params source: threepass_seed_s28
S30 DPOL run: IN PROGRESS — log result at S31 start
Dataset hash: 580b0f3a1667

---

## Market Baselines — All 17 Tiers (confirmed stable S28)

| Tier | Mkt Overall | Mkt H/A Only | EdgeLab Overall | Gap (Overall) |
|------|------------|--------------|-----------------|---------------|
| E0 | 54.7% | 72.2% | 50.3% | -4.4% |
| E1 | 46.6% | 64.0% | 44.4% | -2.2% |
| E2 | 47.7% | 64.7% | 44.4% | -3.3% |
| E3 | 45.2% | 62.0% | 43.1% | -2.1% |
| EC | 48.2% | 65.1% | 45.1% | -3.1% |
| B1 | 52.5% | 70.2% | 48.1% | -4.4% |
| D1 | 51.8% | 68.9% | 47.8% | -4.0% |
| D2 | 47.2% | 64.8% | 44.4% | -2.8% |
| I1 | 54.4% | 73.5% | 48.9% | -5.5% |
| I2 | 45.8% | 66.2% | 42.2% | -3.6% |
| N1 | 56.2% | 73.4% | 51.3% | -4.9% |
| SC0 | 52.9% | 70.0% | 49.6% | -3.3% |
| SC1 | 47.5% | 65.4% | 44.4% | -3.1% |
| SC2 | 50.4% | 65.0% | 47.4% | -3.0% |
| SC3 | 49.4% | 63.5% | 47.1% | -2.3% |
| SP1 | 53.6% | 71.5% | 48.4% | -5.2% |
| SP2 | 46.8% | 65.9% | 45.3% | -1.5% |

---

## Files

| File | Status | Notes |
|------|--------|-------|
| edgelab_engine.py | Updated S26 | w_xg_draw + composite_draw_boost added |
| edgelab_dpol.py | Updated S30 | db param, directional candidate bias, navigate not wander |
| edgelab_runner.py | Updated S30 | db passed to DPOLManager |
| edgelab_db.py | Updated S30 | get_successful_param_directions rebuilt — proper JOIN + signed direction |
| edgelab_gary_brain.py | Updated S30 | PatternMemory dataclass, db param, _build_pattern_memory wired |
| edgelab_gary_context.py | Updated S30 | Pattern memory section in match prompt |
| edgelab_html_generator.py | New S30 | Full predictions HTML generator — replaces manual build |
| edgelab_results_check.py | Updated S29 | Learning loop closed, writes to DB |
| edgelab_backfill.py | New S29 | Historical fixture population |
| edgelab_gridsearch.py | Updated S26 | Full rebuild — all 17 tiers |
| edgelab_draw_dpol_seed.py | New S27 | Seeds gridsearch draw weights |
| edgelab_param_evolution.py | New S28 | Three-pass full param evolution tool |
| edgelab_threepass_seed.py | New S28 | Seeds param_profile.json into edgelab_params.json |
| edgelab_acca.py | Updated S24 | winner_btts; qualifying picks list |
| edgelab_gary.py | Final | Gary briefing wrapper |
| edgelab_market_baseline.py | New S24 | Market baseline calculator |
| edgelab_ha_breakdown.py | New S24 | H/A breakdown vs market |
| edgelab_draw_signal_validation.py | New S25 | Draw signal validator |
| edgelab_draw_evolution.py | New S25 | Three-pass draw evolution tool |
| edgelab_signals.py | Final S15 | 481 ground coords, all Phase 1 signals |
| edgelab_predict.py | Final | Full prediction pipeline |
| edgelab_databot.py | Updated S17 | All 17 tiers |
| edgelab_weather.py | Updated S17 | --batch CLI |
| edgelab_config.py | Updated S16 | Phase 1 + Phase 2 signal display |
| edgelab_params.json | Reverted S29 | threepass_seed_s28. Third DPOL run regressed. |
| edgelab.db | New S29 | Fixture intelligence DB — LOCAL ONLY, not in git |
| .gitignore | New S29 | Excludes edgelab.db and __pycache__ |

---

## Dataset

417 CSV files, 25 years, 17 tiers, 132,685 matches (373 files loaded — 48 skipped).
Hash: 580b0f3a1667
Weather cache: 123,926/132,685 rows (93.4%) — check S31.
edgelab.db: 131,149 fixtures backfilled S29.

---

## Brand & Marketing Status

### garyknows.com
- Live on Netlify (free tier). Last deployed 8 April 2026.
- DNS: A record @→75.2.60.5, CNAME www→gary-knows.netlify.app (Namecheap)
- Form: wired to Mailchimp. FNAME + EMAIL. Honeypot present.
- Sender: gary@garyknows.com active. Welcome automation: active.

### Predictions HTML
- Live on Netlify: spectacular-licorice-3d5119.netlify.app
- Rename pending: gary-picks.netlify.app
- Generated by edgelab_html_generator.py — deploy by drag-and-drop each week
- HTML needs refinement before social push
- Social push paused until HTML is polished

### Email
- Mailchimp free trial: expired — now on free tier (500 contact limit).
- 6 contacts (mostly Andrew). Brevo migration trigger: 400 contacts.
- garyknows.com domain: Authenticated. khaotikk.com domain: Authenticated.

### Social
- TikTok + Instagram: ~3,000 TikTok views. Fresh start 8 April 2026.
- Gary avatar: 7-second Kling clip exists. "Who the hell is Gary?" cut live.
- Kling subscription active. Social push paused — HTML refinement first.

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
- Last done: S27 (all 29 conversations). Next due: ~S32-33.

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

## To Start Session 31

1. Use EDGELAB_SESSION_START_PROMPT.md as the opening prompt
2. Upload EDGELAB_BRIEFING_SESSION31_START.md to project knowledge (replace S30)
3. Upload EDGELAB_STATE_S31.md to project knowledge (replace S30)
4. Upload EDGELAB_MASTER_BACKLOG_S30.md to project knowledge (replace S29)
5. Log S30 DPOL run result before anything else
6. Work the ordered queue from the top
