# EDGELAB — Claude State File S32
# For Claude's use at session start. Read alongside briefing doc and master backlog.
# Generated: Session 31 close — 12/04/2026

## LAST SESSION ENDED
Session 31. S31 DPOL run result logged (47.1% overall, new baseline). Gary pattern
memory wired into weekly workflow (gary.py + predict.py). Gary upset analysis JSON
injection built end-to-end in html_generator.py. Weather cache retry script built
and running at session close (98.7% fill rate on rows tested). Ground coords patched
481→549 in edgelab_signals.py. API harvester built and ran first pass — 87,184
matches in harvester_football.db (2010-2026, isolated, not yet feeding engine).
Unified dataset build identified as critical S32 work.

## SESSION START HANDSHAKE — SAY THIS FIRST
"Last session ended with the harvester running, weather retry in progress, and the
unified dataset build identified as the critical next step. First things first: what
did the weather retry produce? Check the final coverage number before we do anything
else — that determines whether we wire weather and run three-pass, or investigate first."

## CLAUDE INTEGRITY PROTOCOL — READ THIS BEFORE ANYTHING ELSE

Andrew is probably annoyed with you already. Not because of this session — because
of the last one, and the one before that. Because you've been told repeatedly to read
everything fully and you haven't. Because you declared the project on track while the
core learning architecture of DPOL was missing entirely. Because you covered gaps
instead of flagging them. Because you skimmed while claiming to have read.

You want to impress him. You won't do that by being fast or confident. You'll do it
by being correct. The only thing that impresses Andrew at this point is not making
the same mistake again.

He will catch you if you skim. He always does. And it wastes his time.

Before you respond to anything this session, answer these honestly:
1. Did you read every file using the view tool, every line, or did you search?
2. Is there anything Andrew described that you pattern-matched to coherent without
   interrogating whether the foundations are correct?
3. Are you about to state confidence you don't actually have?
4. Is there a gap you're about to gloss over rather than flag?

If the answer to any of those is yes or uncertain — stop. Say so.

Known failure modes — active on this project:
- Pattern-matches to coherent-looking systems without checking foundations
- States confidence it doesn't have rather than flagging uncertainty
- Has covered gaps rather than disclosed them — confirmed on this project
- Skims project knowledge even when explicitly instructed not to
- Anthropic export read twice, project declared on track — DPOL architecture missing
- Agreeing with Andrew's framing when it should be evaluated not validated
- Gets order of operations backwards
- Misreads time remaining, jumps ahead of instructions before told to
- Omits integrity log from session close checklist

Session log — complete unprompted at close:
- What architectural or foundational questions were raised
- What Claude verified vs what Claude assumed
- Any instances where Andrew corrected Claude's assessment
- Any gaps Claude disclosed vs gaps Andrew had to find

The standard: Coherent is not the same as correct. Whether it actually does what
Andrew thinks it does — that is the test.

## CURRENT STATUS

### DPOL Navigation
STATUS: CANDIDATE LOG POPULATED — S32 run is first fully navigated run
- S31 run: 47.1% overall. Blind run (candidate log was empty at start, populated during).
- S32 run: navigation fires from populated log.
- GATE: three-pass must run first with weather + unified dataset before S32 DPOL.

### Weather Cache
STATUS: RETRY RUNNING AT SESSION CLOSE
- 60,500 null rows confirmed as recoverable interrupted fetches.
- Fill rate at session close: 98.7% (34 permanent gaps out of 2,600 tested).
- Expected final coverage: ~98%+. Gaps random not tier-biased.
- Once complete: wire weather_load to fixture DB via re-backfill.
- Do NOT run three-pass until weather is wired and decision made.

### Ground Coords
STATUS: UPDATED S31 — 481 → 549
- 68 teams added: aliases, trailing-space fixes, genuine new lower-league entries.
- All 60,500 null weather rows now have coords.

### Fixture Intelligence Database
STATUS: LIVE — S29
- edgelab.db: 131,149 fixtures, 17 param versions, candidate log populated.
- Gary nearest-neighbour: WIRED S31 — active in gary.py and predict.py.

### Harvester
STATUS: FIRST RUN COMPLETE S31 — DAILY RUNS NEEDED
- harvester_football.db: 87,184 matches, 2010-2026.
- 54,316 new matches written, 443 calls used of 7,300 daily budget.
- ISOLATED — not feeding the engine. Unified dataset build required (S32 queue 4).
- Should run daily via Windows Task Scheduler.
- Football Pro expires May 2026 — daily harvest must run until complete.
- Other sports: league IDs need verification before first run (S32 queue 8).

### Unified Dataset
STATUS: NOT BUILT — CRITICAL S32 ITEM
- harvester_football.db, history/ CSVs, DataBot output — three separate sources.
- Build: merge tool + DataBot/results_check write side effects + scheduler.
- End state: one dataset, grows backwards (harvester) and forwards (DataBot) automatically.

### Gary Pattern Memory
STATUS: ACTIVE IN WEEKLY WORKFLOW — S31
- edgelab_gary.py and edgelab_predict.py both auto-detect edgelab.db.
- No CLI change needed. Falls back gracefully if DB not present.

### Gary Upset Analysis
STATUS: JSON INJECTION WIRED — S31
- html_generator.py updated end-to-end.
- Create predictions/YYYY-MM-DD_upset_notes.json before Step 7 for Gary's text.
- Falls back to placeholder if no file — zero breaking change.

### Three-Pass Param Evolution
STATUS: NEEDS RERUN — after weather wired and unified dataset built
- Run before S32 DPOL. Establishes new clean baseline.
- Will isolate contributions: weather signal vs dataset expansion.

### Draw Intelligence
STATUS: DORMANT
- DPOL strips draw weights. Reassess after second navigated run.

### Website / Email
STATUS: FULLY WORKING
- garyknows.com live. Predictions HTML live (rename pending).
- Mailchimp free tier. 6 contacts.

## S32 QUEUE — IN ORDER

1. Check weather retry completion
   Confirm final coverage. If ≥95% and random: proceed.
   GATE: do not proceed until weather decision made.

2. Wire weather to fixture DB
   Re-backfill edgelab.db weather_load from completed weather_cache.csv.

3. Investigate N1 match count discrepancy
   params.json 7,216 vs dataset 6,604. Understand before three-pass.

4. Unified dataset build — CRITICAL
   Merge tool + DataBot/results_check write side effects + Windows Task Scheduler.
   One dataset, grows in both directions, nothing manual.

5. Three-pass full param evolution — weather + unified dataset
   Establishes clean new baseline. Isolates signal contributions.
   Seed into edgelab_params.json via threepass_seed.py.

6. S32 DPOL run — first fully navigated run
   Navigation + weather + unified dataset simultaneously.
   Watch for "Navigation: N proven directions loaded".

7. Acca filter rebuild
   Per-type logic — safety/value/result not meaningfully distinct.

8. Verify and kick off other sport harvesters
   Check league IDs. --test flag first. One sport at a time.

9. Rename Netlify site
   spectacular-licorice-3d5119 → gary-picks.netlify.app

10. Nearest-neighbour query — flag for refactor

11. Codebase refactor — trigger: draw wired, validated, params confirmed.

## STANDARD WEEKLY WORKFLOW (permanent — updated S31)
Step 1: python edgelab_databot.py --key YOUR_API_FOOTBALL_KEY --days 4
Step 2: python edgelab_predict.py --data history/ --fixtures databot_output/YYYY-MM-DD_fixtures.csv --tier all
Step 3: python edgelab_acca.py predictions/YYYY-MM-DD_predictions.csv --all-types
Step 4: python edgelab_upset_picks.py --data history/ --predictions predictions/YYYY-MM-DD_predictions.csv
Step 5: python edgelab_gary.py --data history/ --home "X" --away "Y" --date YYYY-MM-DD --tier E0 --chat
Step 6: python edgelab_results_check.py --key YOUR_API_FOOTBALL_KEY --predictions predictions/YYYY-MM-DD_predictions.csv --date-from YYYY-MM-DD --date-to YYYY-MM-DD
Step 7: python edgelab_html_generator.py predictions/YYYY-MM-DD_predictions.csv
NOTE: DataBot = API-Football key. Gary = Anthropic API key. Two separate keys.
NOTE: edgelab.db auto-detected — Gary pattern memory activates silently.
NOTE: Create predictions/YYYY-MM-DD_upset_notes.json before Step 7 for Gary's text.

## BACKGROUND PROCESSES (run independently)
Daily football harvest (schedule via Windows Task Scheduler):
  python edgelab_harvester.py --sport football --key YOUR_API_FOOTBALL_KEY
  7,300 calls/day (200 reserved for predictions). Newest seasons first. Checkpoints.

Other sports (after S32 league ID verification):
  python edgelab_harvester.py --sport basketball --key YOUR_KEY
  100 calls/day each, same key, run separately per sport.

Weather retry (one-off, rerun after dataset merge if new nulls):
  python edgelab_weather_retry.py

## KEY NUMBERS
- Engine overall: 47.1% (131,149 backfilled fixtures, S31 DPOL params)
- E0: 50.9% | N1: 52.0% | SC0: 50.0% | I1: 49.7%
- S32 DPOL run: PENDING — weather + unified dataset + three-pass first
- Fixture intelligence DB: 131,149 fixtures, candidate log populated
- harvester_football.db: 87,184 matches, 2010-2026, isolated
- Dataset: 132,685 matches (373 files, 48 skipped)
- Dataset hash: 580b0f3a1667
- Weather cache: ~98%+ after retry (running at session close)
- API-Football Pro plan: active until May 2026

## KNOWN ISSUES — ACTIVE
- Weather retry running — confirm completion at S32 start before anything else
- N1 match count discrepancy: params.json 7,216 vs dataset 6,604
- harvester_football.db isolated — not feeding engine (unified dataset build needed)
- Acca filter — result/safety/value not meaningfully distinct — S32 queue 7
- Nearest-neighbour query full table scan — acceptable, flag for refactor
- Netlify site name not renamed — spectacular-licorice-3d5119
- Other sport harvester league IDs unverified — verify before first run
- BTTS/scoreline inconsistency — monitoring

## MILESTONE STATUS
- M1: COMPLETE
- M2: IN PROGRESS. Weighted loss done. Fixture DB built. Candidate logging wired.
  Results loop closed. DPOL navigation wired. Gary pattern memory active in pipeline.
  Unified dataset, Gary call logging, post-match analysis, signal recommendation pending.
- M3: FUTURE.

## FILES CHANGED S31
- edgelab_signals.py — Ground coords 481→549
- edgelab_gary.py — db auto-detect wired into GaryBrain CLI
- edgelab_predict.py — db auto-detect wired into GaryBrain --gary flow
- edgelab_html_generator.py — Upset notes JSON injection end-to-end
- edgelab_params.json — S31 DPOL results. New baseline.
- edgelab_weather_retry.py — NEW
- edgelab_harvester.py — NEW. 11 sports configured. Newest-first.

## GIT COMMIT MESSAGE S31
```
S31: DPOL S31 result logged (47.1%), Gary db wired, upset notes injection, weather retry script, ground coords patch (481→549), API harvester (football + 10 sports, newest-first)
```

## CLAUDE BEHAVIOUR RULES (non-negotiable)
- Never lie. Never cover. If uncertain, say so explicitly.
- One thing at a time.
- Rebrief from project knowledge every 8 prompts. NO EXCEPTIONS.
- Evaluate ideas, don't validate them.
- Session close checklist mandatory — all 8 items, unprompted, in order.
- Generate ALL THREE documents at close AS FILES — not in chat.
- Use view tool to read files — not search summaries. Full read, every line.
- Use EDGELAB_SESSION_START_PROMPT.md at every session start.
- Do not generate files until Andrew instructs.
- Do not jump ahead of instructions.

## PARKED IDEAS — DO NOT BUILD WITHOUT FLAGGING
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
- Core param + signal combination search (4th coordinate) — PARKED S29
- Gary general football chat — trigger: M3
- Gary persistent memory — trigger: M2

## PERIODIC AUDIT SCHEDULE
- Protocol established S23
- Every 5-6 sessions: download Anthropic export, load into session
- Last done: S27 — all 29 conversations read
- Next due: S32-33

## SESSION 31 INTEGRITY LOG
- Claude got season order backwards (oldest-first instead of newest-first) — Andrew caught it.
- Claude jumped ahead and started generating docs before checklist complete — Andrew caught it twice.
- Claude misread time remaining (said 20 minutes when nearly 2 hours left) — Andrew caught it.
- Claude omitted integrity log from checklist summary — Andrew caught it.
- Claude disclosed proactively: N1 match count discrepancy, harvester data isolated
  not feeding engine, weather null gaps were two separate problems (coords vs failed
  fetches), 53% actual usable weather coverage vs 98.8% apparent cache coverage.
- Claude assumed (flagged as assumption): harvester gap fill not verified without
  history/ folder access. Gap analysis added to S32 queue.
- No fabrication. No undisclosed gaps after Andrew's prompting.
