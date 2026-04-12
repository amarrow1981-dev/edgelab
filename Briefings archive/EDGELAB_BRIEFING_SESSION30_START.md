# EdgeLab — Session 30 Briefing
# Replaces: EDGELAB_BRIEFING_SESSION29_START.md
# Generated: Session 29 close — 11/04/2026

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

---

## The Architecture — What Changed in Session 29

Session 29 was the most important architectural session in the project's history.

The fundamental problem identified: DPOL has been a local search with no memory.
Every run discards everything it learned. The only thing surviving between runs was
a handful of numbers in a JSON file. This is why accuracy gains have been small and
non-compounding — DPOL was repeating the same loop rather than building on prior knowledge.

**What was built in S29:**

The Fixture Intelligence Database (edgelab.db). Three tables:

- fixtures — every match ever processed. Pre-match feature vector written at
  prediction time. Actual result written when results come in. One row, two states.
  131,149 historical fixtures backfilled from CSVs. The 3D map now exists.

- param_versions — every set of params that has ever been active, per tier.
  Versioned so every fixture record knows exactly what was running when it was predicted.

- dpol_candidate_log — every candidate DPOL tests in every evolution round.
  Accepted and rejected. This is the trail DPOL has walked through param space.
  Previously thrown away every run. Now stored permanently and growing.

**What this means:**

DPOL no longer starts blind. It starts with 131,149 completed data points already mapped.
Every future run adds to the candidate log. Over time DPOL can read that log and navigate
toward regions of param space that have historically worked, rather than wandering.

Gary can now query the nearest 200 historical fixtures to any prediction — not just
rolling form and H2H, but actual pattern memory from similar historical situations.

The results check now closes the loop — every result writes back to complete the
fixture record. Pre-match written at prediction time. Post-match written when result
comes in.

**The repeatable framework:**
This database architecture is the blueprint for all future sports expansions. Football
gets its own database. Cricket, NBA, financial markets each get their own instance
built on the same blueprint. They do not share data — they share the architecture.

---

## Session 29 — Actions Completed

- **Third DPOL run assessed — REGRESSED.** Overall -0.10pp vs threepass seed.
  w_score_margin stripped back on most tiers by DPOL's local search.
  Params reverted to threepass_seed_s28. Third run results discarded.
  Root cause confirmed: DPOL has no memory of why values were placed where they were.
  This is the architectural problem the fixture intelligence database solves.

- **Fixture intelligence database built — COMPLETE.**
  edgelab_db.py built. Three tables: fixtures, param_versions, dpol_candidate_log.
  SQLite now, PostgreSQL path designed for scale.

- **Historical backfill — COMPLETE.**
  edgelab_backfill.py built and run. 131,149 fixtures written to edgelab.db.
  17 param versions saved. Overall accuracy 46.3% confirmed as honest baseline.
  Discarded param analysis built into backfill via --check-discarded flag.

- **DPOL candidate logging wired — COMPLETE.**
  edgelab_dpol.py updated — candidate_logger callback added.
  edgelab_runner.py updated — DB wired, candidate_logger passed on every call.
  Every future DPOL run writes every candidate evaluation to dpol_candidate_log.

- **Results check updated — COMPLETE.**
  edgelab_results_check.py rebuilt. Reads predictions CSV, matches API results,
  writes completions back to edgelab.db. Learning loop closed.

- **Cross-league seasonal evolution — PARKED with schema noted.**
  Tier and season dimensions built into fixtures table as first-class fields.

- **Claude integrity protocol — designed and agreed.**
  Added to briefing doc and state file as first-class section.

- **DPOL must not run again until it reads from the candidate log.**

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
Coherent is not the same as correct. The DPOL architecture looked coherent for
28 sessions while the core learning mechanism was absent. Coherence is not the test.
Whether it actually does what Andrew thinks it does — that is the test.

When asked "is the project on track" — give a specific account of what was verified,
what was assumed, and what is uncertain. Anything less is a cover.

This is not about Claude's ego or impressing Andrew. It is about the project.
The project is the only thing that matters.

---

## Ordered Work Queue

### Session 30 — priorities in order

1. **Wire DPOL to read from candidate log before evolving**
   edgelab_dpol.py: before _generate_candidates, query get_successful_param_directions()
   Use result to bias candidate generation — larger steps in proven directions,
   skip directions that have consistently failed.
   GATE: Must be built before next DPOL run. DPOL must not run blind again.

2. **Run three-pass evolution with candidate log in place**
   Rerun three-pass param evolution once DPOL reads from the log.
   Candidate log records every combination tested — won't retest covered ground.

3. **Wire Gary nearest-neighbour lookup**
   edgelab_gary_brain.py: add db.find_similar_fixtures() + get_outcome_distribution()
   Gary receives: "In 200 similar historical fixtures, H won 44%, D 28%, A 28%."

4. **Public HTML qualifying picks — automate in edgelab_acca.py**
   Tier code to league name mapping already exists in gary_context.py — use it.

5. **Date labelling bug — fix at source**
   DataBot UTC offset or acca.py date conversion. Fix properly, remove +1 workaround.

6. **Weather cache — check row count and wire if complete**
   At 93.4% at S28. If complete: wire to DPOL. Weather slots into fixtures table.

7. **iOS HTML — confirm fix works via Netlify URL**
   Deploy HTML to Netlify. Share URL not file.

8. **Nearest-neighbour query optimisation — flag for refactor**
   Current find_similar_fixtures() is full table scan. Fine at 131k rows.
   Needs spatial indexing before database reaches millions of records.

9. **Codebase refactor** — trigger: draw intelligence wired, validated, params confirmed.

### Standard weekly workflow (permanent)
- Thursday: predictions for weekend fixtures + accas + Gary upset picks
- Sunday: predictions for midweek fixtures + accas + Gary upset picks
- Results check after each fixture set completes — now also writes to edgelab.db

### Weekly prediction commands (exact)
Step 1: python edgelab_databot.py --key YOUR_API_FOOTBALL_KEY --days 4
Step 2: python edgelab_predict.py --data history/ --fixtures databot_output/YYYY-MM-DD_fixtures.csv --tier all
Step 3: python edgelab_acca.py predictions/YYYY-MM-DD_predictions.csv --all-types
Step 4: python edgelab_upset_picks.py --data history/ --predictions predictions/YYYY-MM-DD_predictions.csv
Step 5: python edgelab_gary.py --data history/ --home "X" --away "Y" --date YYYY-MM-DD --tier E0 --chat
Step 6: python edgelab_results_check.py --key YOUR_API_FOOTBALL_KEY --predictions predictions/YYYY-MM-DD_predictions.csv --date-from YYYY-MM-DD --date-to YYYY-MM-DD
NOTE: DataBot = API-Football key. Gary = Anthropic API key. Two separate keys.

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
- Core param + signal combination search (4th coordinate) — PARKED S29. Add to three-pass
  rebuild design in S30. Test core params (home_adv, draw_margin, DTI scales etc) in
  simultaneous combination with signal activations. Current three-pass assumes core params
  are correct and searches signal space on top. This closes that gap — core params may be
  in wrong region for certain signal combinations to fire. Candidate log makes it tractable.
  Design decision for three-pass rebuild, not a separate system.

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

Params source: threepass_seed_s28 (third DPOL run regressed S29, reverted)
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
| edgelab_dpol.py | Updated S29 | candidate_logger callback added |
| edgelab_runner.py | Updated S29 | DB wired, candidate logger |
| edgelab_results_check.py | Updated S29 | Learning loop closed, writes to DB |
| edgelab_db.py | New S29 | Fixture intelligence database |
| edgelab_backfill.py | New S29 | Historical fixture population |
| edgelab_gridsearch.py | Updated S26 | Full rebuild — all 17 tiers |
| edgelab_draw_dpol_seed.py | New S27 | Seeds gridsearch draw weights |
| edgelab_param_evolution.py | New S28 | Three-pass full param evolution tool |
| edgelab_threepass_seed.py | New S28 | Seeds param_profile.json into edgelab_params.json |
| edgelab_acca.py | Updated S24 | winner_btts; qualifying picks list |
| edgelab_gary_brain.py | Updated S24 | last8_meetings fix |
| edgelab_gary_context.py | Updated S24 | weather_load fix |
| edgelab_upset_picks.py | Built S22 | |
| edgelab_databot.py | Updated S17 | All 17 tiers |
| edgelab_weather.py | Updated S17 | --batch CLI |
| edgelab_config.py | Updated S16 | Phase 1 + Phase 2 signal display |
| edgelab_runner.py | Updated S19 | --signals-only flag |
| edgelab_signals.py | Final S15 | 481 ground coords, all Phase 1 signals |
| edgelab_predict.py | Final | Full prediction pipeline |
| edgelab_gary.py | Final | Gary briefing wrapper |
| edgelab_market_baseline.py | New S24 | Market baseline calculator |
| edgelab_ha_breakdown.py | New S24 | H/A breakdown vs market |
| edgelab_draw_signal_validation.py | New S25 | Draw signal validator |
| edgelab_draw_evolution.py | New S25 | Three-pass draw evolution tool |
| draw_profile.json | New S25 | Draw signal profile |
| gridsearch_results.json | New S26 | Per-tier draw params from gridsearch |
| param_profile.json | New S28 | Three-pass full param evolution results |
| edgelab_params.json | Reverted S29 | threepass_seed_s28. Third DPOL run regressed. |
| edgelab.db | New S29 | Fixture intelligence DB — LOCAL ONLY, not in git |
| .gitignore | New S29 | Excludes edgelab.db and __pycache__ |
| edgelab_2026-04-09_predictions_public.html | Updated S28 | iOS tab fix, dates +1 day |

---

## Dataset

417 CSV files, 25 years, 17 tiers, 132,685 matches (373 files loaded — 48 skipped).
Hash: 580b0f3a1667
Weather cache: 123,926/132,685 rows (93.4%) — not ready to wire. Check S30.
edgelab.db: 131,149 fixtures backfilled S29.

---

## Brand & Marketing Status

### garyknows.com
- Live on Netlify (free tier). Last deployed 8 April 2026.
- DNS: A record @→75.2.60.5, CNAME www→gary-knows.netlify.app (Namecheap)
- Form: wired to Mailchimp. FNAME + EMAIL. Honeypot present.
- Sender: gary@garyknows.com active. Welcome automation: active.
- Predictions HTML: MUST be deployed to Netlify as URL, not shared as file.
- Social push paused — HTML must be on Netlify first.

### Email
- Mailchimp free trial: expired ~S30 — now on free tier (500 contact limit).
- 6 contacts (mostly Andrew). Brevo migration trigger: 400 contacts.
- garyknows.com domain: Authenticated. khaotikk.com domain: Authenticated.

### Social
- TikTok + Instagram: ~3,000 TikTok views. Fresh start 8 April 2026.
- Gary avatar: 7-second Kling clip exists. "Who the hell is Gary?" cut live.
- Kling subscription active. Social push paused — Netlify first.

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

## To Start Session 30

1. Use EDGELAB_SESSION_START_PROMPT.md as the opening prompt
2. Upload EDGELAB_BRIEFING_SESSION30_START.md to project knowledge (replace S29)
3. Upload EDGELAB_STATE_S30.md to project knowledge (replace S29)
4. Upload EDGELAB_MASTER_BACKLOG_S29.md to project knowledge (replace S28)
5. Claude confirms files received, states last action + next action
6. Work the ordered queue from the top
