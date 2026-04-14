# EDGELAB — Claude State File S34
# For Claude's use at session start. Read alongside briefing doc and master backlog.
# Generated: Session 33 close — 13/04/2026

## LAST SESSION ENDED
Session 33. S32 DPOL confirmed: 47.6% overall, 17/17 tiers improved, navigation fired.
Pass 2b post-match teacher layer confirmed working (E0 test). Gary call logging fully
wired (db.py, gary.py, results_check.py). Merge automated in football harvester bat.
Market comparison framework built and run — disagreement value thesis confirmed for
second week. Git commit format fixed for PowerShell. Stale project files were an issue
at session start — Andrew caught it. Pass 2b rebuilt unnecessarily — Andrew caught it.

## SESSION START HANDSHAKE — SAY THIS FIRST
"Last session ended with S32 DPOL confirmed at 47.6% overall and Gary call logging
wired. Weather is the gate — everything else is waiting on it. First: check
harvester_logs\weather_retry.log and tell me the current coverage."

## CLAUDE INTEGRITY PROTOCOL — READ THIS BEFORE ANYTHING ELSE

Andrew is probably annoyed with you already. Not because of this session — because
of the last one, and the one before that. Because you have been told repeatedly to read
everything fully and you have not. Because you declared the project on track while the
core learning architecture of DPOL was missing entirely. Because you covered gaps
instead of flagging them. Because you skimmed while claiming to have read.

You want to impress him. You will not do that by being fast or confident. You will do
it by being correct. The only thing that impresses Andrew at this point is not making
the same mistake again.

He will catch you if you skim. He always does. And it wastes his time, which is the
one thing he does not have.

So before you say anything — did you actually read every file? Not searched. Not
summarised. Read. Every line. Because if you did not, Andrew will know, and this
session starts in a hole you dug yourself.

Before you respond to anything this session, answer these honestly:
1. Did you read every file using the view tool, every line, or did you search and summarise?
2. Is there anything Andrew described that you pattern-matched to coherent without
   interrogating whether the foundations are correct?
3. Are you about to state confidence you do not actually have?
4. Is there a gap you are about to gloss over rather than flag?

If the answer to any of those is yes or uncertain — stop. Say so.

Known failure modes — active on this project:
- Pattern-matches to coherent-looking systems without checking foundations
- States confidence it does not have rather than flagging uncertainty
- Has covered gaps rather than disclosed them — confirmed on this project
- Skims project knowledge even when explicitly instructed not to
- Anthropic export read twice, project declared on track — DPOL architecture missing
- Agreeing with Andrew's framing when it should be evaluated not validated
- Gets order of operations backwards
- Omits integrity log from session close checklist
- Started generating files before completing full close checklist — S32
- Post-match teacher layer in vision since S25, not formalised until S32 audit
- DPOL navigation SQL bug ran undetected through entire initial S32 run
- Worked from stale project files for first half of S33 — Andrew caught it
- Rebuilt Pass 2b without knowing it already existed — wasted time
- Declared queue item complete without verifying actual file in use
- Used wrong attribute path ctx.memory vs ctx.gary_memory — Andrew caught it
- Git commit messages broke PowerShell every session — fixed S33
- Clear downloads folder before copying new .py files — Windows renames duplicates silently

Session log — complete unprompted at close:
- What architectural or foundational questions were raised
- What Claude verified vs what Claude assumed
- Any instances where Andrew corrected Claude
- Any gaps Claude disclosed vs gaps Andrew had to find

## CURRENT STATUS

### Weather Cache
STATUS: ~69% — TASK SCHEDULER RUNNING AS SYSTEM
- Running 10k rows/night at 01:00 as SYSTEM
- Expected 95%+ within 3 nights of 13/04/2026
- GATE: do not run three-pass until weather is wired and 95%+ confirmed
- Check: harvester_logs\weather_retry.log

### DPOL Navigation
STATUS: S32 RUN CONFIRMED — 47.6% OVERALL
- 17/17 tiers improved. Navigation fired on every tier.
- Starting baseline 45.5%, evolved to 47.6% — +2.1pp overall
- Key: N1 52.9%, I1 51.0%, E0 51.1%, SP1 50.5%, SP2 45.7%
- S33 DPOL run (second navigated): gated on weather + three-pass

### Post-Match Teacher Layer
STATUS: CONFIRMED WORKING S33
- Pass 2b tested on E0 — fired correctly
- Teacher confirmed params for E0: w_form, w_gd, w_score_margin, w_h2h_draw, w_btts
- Away win signals mostly unconfirmed by post-match evidence — away model noisier
- Full three-pass run gated on weather

### Gary Call Logging
STATUS: FULLY WIRED S33
- gary_calls table active in edgelab.db
- ask() logs silently on every call
- complete_gary_call fires in results_check.py on every result
- Captures: engine output, Gary full response, extracted prediction, confidence band,
  upset/draw flags, pattern memory, gary_vs_engine comparison

### Three-Pass
STATUS: GATED ON WEATHER
- Last run: S32, 46.7% baseline on 218k rows
- Next run: first with weather + post-match teacher + unified dataset
- GATE: weather 95%+ must be wired first

### Unified Dataset
STATUS: COMPLETE S32 — 218,317 matches
- Merge now automated in football harvester bat (S33)
- edgelab_merge.py runs after each nightly harvest automatically

### Task Scheduler
STATUS: ALL 12 TASKS RUNNING AS SYSTEM
- Football: 02:00 (with merge after)
- Weather retry: 01:00
- Other sports: 03:00–04:30

### Market Comparison
STATUS: FRAMEWORK BUILT S33
- Week 1 (old params): +1.7pp vs market. Disagreement wins: 11 at avg 3.40 odds.
- Week 1 (new params, retroactive): -2.5pp vs market. 1 week — insufficient to conclude.
- Run every prediction round going forward.

### Gary Pattern Memory
STATUS: ACTIVE IN WEEKLY WORKFLOW

### Acca Filter
STATUS: REBUILT S32 — value > safety > result, mutually exclusive

### Website / Email
STATUS: FULLY WORKING
- garyknows.com live. garypredicts.netlify.app live.
- Mailchimp: 6 contacts, free tier.

## S34 QUEUE — IN ORDER

1. Check weather retry progress
   harvester_logs\weather_retry.log
   If 95%+ — wire immediately.

2. Wire weather to fixture DB
   Re-backfill edgelab.db weather_load from weather_cache.csv.
   GATE: before three-pass.

3. Three-pass full param evolution — weather + post-match teacher + unified dataset
   First definitive run with all improvements.
   Seed via edgelab_threepass_seed.py.

4. S33 DPOL run — second navigated run
   Navigation + weather + teacher seeded params.

5. Draw rate prior audit
   Flat vs tier-specific in engine. Fix if flat before draw intelligence.

6. Full H/A/D disagreement analysis
   9 wrong calls from 09/04. Confidence, chaos, DTI, upset score per call.

7. Gary post-match analysis — M2.

8. DataBot extension — team news. Trigger: S33 DPOL proven.

9. Verify other sport harvester league IDs.

10. Predictions archive rolling HTML ledger. Trigger: 4+ weeks data.

11. Nearest-neighbour flag for refactor.

12. Codebase refactor. Trigger: draw wired, validated, params confirmed.

## STANDARD WEEKLY WORKFLOW (permanent — updated S33)
Step 1: python edgelab_databot.py --key YOUR_API_FOOTBALL_KEY --days 4
Step 2: python edgelab_predict.py --data history/ --fixtures databot_output/YYYY-MM-DD_fixtures.csv --tier all
Step 3: python edgelab_acca.py predictions/YYYY-MM-DD_predictions.csv --all-types
Step 4: python edgelab_upset_picks.py --data history/ --predictions predictions/YYYY-MM-DD_predictions.csv
Step 5: python edgelab_gary.py --data history/ --home "X" --away "Y" --date YYYY-MM-DD --tier E0 --chat
Step 6: python edgelab_results_check.py --key YOUR_API_FOOTBALL_KEY --predictions predictions/YYYY-MM-DD_predictions.csv --date-from YYYY-MM-DD --date-to YYYY-MM-DD
Step 7: python edgelab_html_generator.py predictions/YYYY-MM-DD_predictions.csv
NOTE: Merge runs automatically after nightly harvest.
NOTE: DataBot = API-Football key. Gary = Anthropic API key.
NOTE: edgelab.db auto-detected — Gary pattern memory and call logging active silently.
NOTE: Create predictions/YYYY-MM-DD_upset_notes.json before Step 7.

## BACKGROUND PROCESSES (Task Scheduler — SYSTEM)
Football: 02:00 (merge automatic after)
Weather retry: 01:00 (10k rows, 3s sleep)
Other sports: 03:00–04:30
Logs: harvester_logs\

## KEY NUMBERS
- S32 DPOL overall: 47.6% (218,317 matches) — CONFIRMED
- S31 baseline: 47.1% (131,149 matches)
- S32 three-pass baseline: 46.7%
- Weather cache: ~69% — running
- edgelab.db: 131,149 fixtures, candidate log populated, gary_calls active
- harvester_football.db: 87,184 matches
- API-Football Pro: active until May 2026

## KNOWN ISSUES — ACTIVE
- Weather cache ~69% — Task Scheduler running, 3 nights to 95%
- Away goals overestimated (1.37 pred vs 1.07 actual) — teacher layer will diagnose
- BTTS overcalling (60% pred vs 50% actual) — monitor
- Other sport harvester league IDs unverified
- edgelab_db (2).py duplicate in edgelab folder — delete manually
- Draw intelligence dormant — reassess after teacher layer three-pass
- New DPOL params retroactive regression on home wins (86.4% to 79.5%) — 1 week sample only

## MILESTONE STATUS
- M1: COMPLETE
- M2: IN PROGRESS. Fixture DB, candidate log, navigation, teacher layer, Gary logging all built.
  Gary post-match analysis, signal recommendation pending.
- M3: FUTURE

## FILES CHANGED S33
- edgelab_db.py — gary_calls expanded, log_gary_call full field set, complete_gary_call extended
- edgelab_gary.py — ask logs silently, _extract_confidence_band, ctx.gary_memory fix
- edgelab_results_check.py — complete_gary_call wired in complete_in_db
- edgelab_param_evolution.py — Pass 2b confirmed working (no functional change from S32.a)
- harvester_tasks/run_harvester_football.bat — merge step added after harvest

## GIT COMMIT MESSAGE S33
git commit -m 'S33: DPOL confirmed 47.6% overall 17/17 tiers, Pass 2b teacher layer tested, Gary call logging wired, merge automated in football bat, market comparison framework'

## CLAUDE BEHAVIOUR RULES (non-negotiable)
- Never lie. Never cover. If uncertain, say so explicitly.
- One thing at a time.
- Rebrief from project knowledge every 8 prompts. NO EXCEPTIONS.
- Evaluate ideas, do not validate them.
- Session close checklist mandatory — all 8 items, unprompted, in order.
- Generate ALL THREE documents at close AS FILES — not in chat.
- Use view tool to read files — not search summaries. Full read, every line.
- Use EDGELAB_SESSION_START_PROMPT.md at every session start.
- Do not generate files until ALL EIGHT checklist items are complete.
- Do not jump ahead of instructions.
- Git commits: single quotes, no special characters, no brackets, no percent signs.
- Upload correct project files at session start — briefing, state, backlog from latest session.

## PARKED IDEAS — DO NOT BUILD WITHOUT FLAGGING
- Gary acca picks — trigger: Gary live on site
- Social comment workflow — trigger: content push
- Underdog effect signal — trigger: signals active
- Gary avatar HeyGen — trigger: M3
- Upset flip Stage 2 — trigger: Stage 1 history validated
- API-Football connection — schedule before May 2026 expiry
- Gary temporal awareness — trigger: API-Football connected
- DPOL upset-focused evolution — trigger: signals active
- DPOL exploration budget — trigger: S33 navigated run assessed
- Perplexity Computer — trigger: M3
- Personal web app — trigger: M2 running
- Gary app iOS/Android — trigger: M3
- Long shot acca — trigger: upset flip Stage 2 validated
- Expand to other sports — trigger: DPOL proven on football
- Data product API licensing — trigger: database mature, M3 complete
- Score prediction draw nudge — ABANDONED
- Codebase refactor — trigger: draw wired, validated, params confirmed
- draw_pull, dti_draw_lock, w_btts — CONFIRMED DEAD x3. Never test again.
- instinct_dti_thresh / skew_correction_thresh — review at refactor
- Stage 2 draw rate strategy — trigger: post-match teacher proven on draws
- Gary onboarding, accent, addiction detection — trigger: M3
- Selection builder, crypto payments — trigger: M3
- Countdown clock — trigger: launch date confirmed
- Cross-league seasonal evolution — trigger: DB mature, weather wired
- Nearest-neighbour spatial indexing — trigger: refactor
- 4th coordinate param + signal search — design into three-pass rebuild
- Gary general football chat, persistent memory — trigger: M2/M3
- Acca threshold tuning — trigger: results history sufficient
- Seasonal DPOL evolution — trigger: DB mature, weather wired
- Gary historical knowledge layer — trigger: Gary M2 complete
- DataBot team news — trigger: S33 DPOL proven
- Bogey team bias — trigger: signals active, dataset mature
- Phase 1 signal activation investigation — trigger: Phase 1 review
- RNG/fraud detection using DPOL — trigger: M3 complete
- DPOL as standalone B2B product — trigger: M3 complete
- Predictions archive rolling ledger — trigger: 4+ weeks data, stable params

## PERIODIC AUDIT SCHEDULE
Last done: S32 — all 34 conversations. Next due: S37-38.

## SESSION 33 INTEGRITY LOG
- Stale project files used for first half of session — Andrew caught it at S33.
  All three documents (briefing, state, backlog) were S32 close versions not S32.a.
  Andrew's responsibility acknowledged but Claude should have verified at session start.
- Claude rebuilt Pass 2b without checking local file — wasted time.
  Root cause: stale project files. Should have asked for local file before building.
- Claude declared queue item 2a complete prematurely — Andrew caught it.
- Wrong attribute path ctx.memory used in gary.py — should be ctx.gary_memory.
  Claude caught it on own check before Andrew had to find it.
- Git commit format broken every session — fixed S33 with PowerShell safe format.
- Claude disclosed proactively: duplicate gary_calls CREATE TABLE block after edit.
- Claude disclosed proactively: duplicate indexes after edit.
- No fabrication. No undisclosed gaps after the stale files issue.
