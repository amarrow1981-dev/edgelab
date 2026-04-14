# EDGELAB — Claude State File S33
# For Claude's use at session start. Read alongside briefing doc and master backlog.
# Generated: Session 32 + 32.a close — 13/04/2026

## LAST SESSION ENDED
Session 32 + 32.a (extended session, same chat thread).
S32 DPOL run in progress — first navigated run, all bugs fixed mid-session.
Six critical DPOL bugs fixed in S32.a. Post-match teacher layer built.
First results analysis complete. Task Scheduler now running as SYSTEM.

## SESSION START HANDSHAKE — SAY THIS FIRST
"S32 ended with DPOL still running — first fully navigated run with all bugs fixed.
First things first: what did the DPOL produce? Check edgelab_params.json and confirm
the result. Note: the navigation SQL bug was fixed mid-run, so early E0 rounds ran
blind — the rest should have navigated correctly."

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
- Skips project knowledge even when explicitly instructed not to
- Anthropic export read twice, declared on track — DPOL architecture missing
- Agreeing with Andrew's framing when it should be evaluated not validated
- Gets order of operations backwards
- Omits integrity log from session close checklist
- Started generating files before completing checklist — S32
- Post-match teacher layer in vision since S25, not formalised until S32
- DPOL navigation SQL bug ran undetected through initial S32 run
- Clear downloads folder of .py files — Windows renames duplicates silently

Session log — complete unprompted at close:
- What architectural questions were raised
- What Claude verified vs assumed
- Any instances where Andrew corrected Claude
- Gaps Claude disclosed vs gaps Andrew had to find

The standard: Coherent is not the same as correct.

## CURRENT STATUS

### DPOL Navigation
STATUS: S32 RUN IN PROGRESS AT SESSION CLOSE
- SQL bug fixed mid-run (early E0 rounds ran blind, rest navigated)
- Three-pass seeded params, 218k dataset, no weather (deliberate)
- Confirm result at S33 start before anything else
- GATE: understand result before further evolution work

### DPOL Bugs Fixed S32.a
All six fixed and deployed:
1. edgelab_db.py — SQL double-prefix `pv.pv.w_form` → navigation silent fail
2. edgelab_runner.py — global guard full dataset → 3,000-row sample
3. edgelab_runner.py — fast_pred_fn missing 7 params (Gap A)
4. edgelab_config.py — load_params() missing 8 param fields (Gap B)
5. edgelab_runner.py — season order oldest-first → newest-first
6. edgelab_results_check.py — LEAGUE_MAP UnboundLocalError

### Post-Match Teacher Layer
STATUS: BUILT S32.a
- edgelab_param_evolution.py now has Pass 2b
- Architecture: Pass1 → Pass2 → Pass2b (teacher) → Pass3 (confidence-weighted)
- Covers ALL outcome combinations (not just H→D — confirmed S32.a)
- Season-by-season diagnostic output built in
- Post-match data NEVER used in predictions — retrospective teacher only
- GATE: must run three-pass before next DPOL to get teacher-validated seeded params

### Weather Cache
STATUS: TASK SCHEDULER RUNNING AS SYSTEM
- Coverage at S32 close: ~61.4%
- Task Scheduler: EdgeLab_WeatherRetry — 01:00 daily as SYSTEM
- Check: harvester_logs\weather_retry.log
- GATE: ≥95% coverage before wiring to fixture DB and running three-pass

### Task Scheduler
STATUS: ALL 12 TASKS RUNNING AS SYSTEM S32.a
- No longer requires login credentials — fires regardless of lock state
- All 12 tasks confirmed updated to SYSTEM

### Unified Dataset
STATUS: COMPLETE S32 — 218,317 matches, 609 files
- edgelab_merge.py: run after each daily harvest

### Three-Pass
STATUS: LAST RUN S32 — REBUILD DONE S32.a, NEEDS RERUN
- Pass 2b post-match teacher built S32.a
- Next run: after weather wired (item 2)
- First run with teacher layer + weather + unified dataset

### Results Analysis (09/04 predictions)
STATUS: COMPLETE S32.a
- Result accuracy: 48.8% (137 predictions)
- MED band (50-79%): 84.2% — primary acca pool
- HIGH band (≥80%): 52.3% — overcalling draws
- Total goals within 1: 56.2%
- Away goals within 1: 71.9%
- BTTS: 60% predicted vs 50% actual — overcalling
- Away goals: 1.37 predicted vs 1.07 actual — monitor
- Correct score: 7.4% (market range)
- Upset flag: 57.1%

### Fixture Intelligence Database
STATUS: LIVE — 131,149 fixtures, 09/04 results written

### Gary Pattern Memory
STATUS: ACTIVE IN WEEKLY WORKFLOW

### Acca Filter
STATUS: REBUILT S32 — value > safety > result, mutually exclusive

## S33 QUEUE — IN ORDER

1. Confirm S32 DPOL results
   GATE: before any evolution work.

2. Wire weather to fixture DB
   Confirm ≥95%. Re-backfill edgelab.db weather_load.
   GATE: before three-pass.

3. Three-pass — weather + post-match teacher + unified dataset
   First run with all improvements. Watch Pass 2b confidence trend.

4. S33 DPOL run — second navigated run

5. Gary call logging — M2

6. Gary post-match analysis — M2

7. Automate merge in harvester bat file

8. Verify other sport harvester league IDs

9. DataBot extension — team news at prediction time
   Trigger: S33 DPOL proven

10. Nearest-neighbour flag for refactor

11. Codebase refactor — trigger: draw wired, validated, params confirmed

## STANDARD WEEKLY WORKFLOW
Step 1: python edgelab_databot.py --key YOUR_API_FOOTBALL_KEY --days 4
Step 2: python edgelab_predict.py --data history/ --fixtures databot_output/YYYY-MM-DD_fixtures.csv --tier all
Step 3: python edgelab_acca.py predictions/YYYY-MM-DD_predictions.csv --all-types
Step 4: python edgelab_upset_picks.py --data history/ --predictions predictions/YYYY-MM-DD_predictions.csv
Step 5: python edgelab_gary.py --data history/ --home "X" --away "Y" --date YYYY-MM-DD --tier E0 --chat
Step 6: python edgelab_results_check.py --key YOUR_API_FOOTBALL_KEY --predictions predictions/YYYY-MM-DD_predictions.csv --date-from YYYY-MM-DD --date-to YYYY-MM-DD
Step 7: python edgelab_html_generator.py predictions/YYYY-MM-DD_predictions.csv
NOTE: After daily harvest: python edgelab_merge.py (until automated)

## BACKGROUND PROCESSES (Task Scheduler — SYSTEM)
Football: 02:00 | Weather retry: 01:00 | Sports: 03:00–04:30 | Logs: harvester_logs\

## KEY NUMBERS
- Three-pass baseline: 46.7% (218,317 matches)
- S31 baseline: 47.1% (131,149 matches)
- S32 DPOL result: PENDING
- Weather cache: ~61.4% — running
- API-Football Pro: active until May 2026

## KNOWN ISSUES — ACTIVE
- S32 DPOL result pending — confirm at S33 start
- Weather cache ~61.4% — Task Scheduler running
- BTTS overcalling (60% pred vs 50% actual) — monitor
- Away goals overestimated (1.37 vs 1.07) — post-match teacher will diagnose
- Other sport harvester league IDs unverified
- Dataset hash stale — run save_dataset_hash() after S32 DPOL
- edgelab_db (2).py duplicate in edgelab folder — delete manually

## MILESTONE STATUS
- M1: COMPLETE
- M2: IN PROGRESS. Fixture DB, candidate log, navigation, teacher layer built.
  Gary call logging, post-match analysis, signal recommendation pending.
- M3: FUTURE

## FILES CHANGED S32 + S32.a
S32: edgelab_acca.py, edgelab_databot.py, edgelab_results_check.py, edgelab_merge.py (NEW),
     edgelab_params.json, param_profile.json, setup_harvester_tasks.ps1 (NEW)
S32.a: edgelab_db.py, edgelab_runner.py, edgelab_config.py, edgelab_param_evolution.py,
       edgelab_results_check.py

## GIT COMMIT MESSAGE S32 + S32.a
```
S32+S32.a: Unified dataset (85,632 rows), Task Scheduler SYSTEM, three-pass 218k, acca filter rebuild, 6 DPOL bug fixes (SQL navigation, global guard 3k sample, fast_pred_fn missing params, config load_params gaps, season order, LEAGUE_MAP), post-match teacher layer (Pass 2b), first results analysis (48.8% result, 84.2% MED band, 56.2% within-1 goal)
```

## CLAUDE BEHAVIOUR RULES (non-negotiable)
- Never lie. Never cover. If uncertain, say so.
- One thing at a time.
- Rebrief every 8 prompts. NO EXCEPTIONS.
- Evaluate ideas, don't validate them.
- Session close: all 8 items, unprompted, in order, AS FILES.
- Use view tool — not search. Full read, every line.
- Do not generate files until ALL EIGHT checklist items complete.

## SESSION 32 + 32.a INTEGRITY LOG
- DPOL navigation SQL bug ran through entire initial S32 run — Andrew spotted slowness, Claude found bug during deep audit Andrew requested. Should have been caught in S32 audit.
- Claude identified 6 DPOL bugs proactively during deep analysis.
- Claude started generating files before checklist — Andrew caught it (S32).
- Andrew verified Pass 2b covers all outcomes not just H→D — code was correct, explanation was illustrative.
- Andrew caught score prediction away goals overestimation — flagged as monitoring item.
- Claude disclosed proactively: season order oldest-first (counterproductive for navigation).
- Claude disclosed proactively: Task Scheduler never fired — diagnosed as credentials issue.
- No fabrication. No undisclosed gaps after Andrew's prompting.

## PERIODIC AUDIT SCHEDULE
Last done: S32 — all 34 conversations. Next due: S37-38.
