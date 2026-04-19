# EDGELAB — Claude State File S37
# For Claude's use at session start. Read alongside briefing doc and master backlog.
# Generated: Session 36 close — 17/04/2026

## LAST SESSION ENDED
Session 36. edgelab_merge.py tier whitelist added — 17 proven tiers only, 214,968
harvester rows correctly blocked. OneDrive confirmed not active sync — folder is on
local Desktop (Windows redirects Desktop to OneDrive path on this machine). Weekend
predictions run — 120 fixtures, 13 leagues, deployed to garypredicts.netlify.app.
HTML generator fully rebuilt — sub-tabs per league, per acca type, larger font, upset
notes auto-load. Acca upset filter fixed — upset_score >= 0.65 threshold, chaos filter
removed. Upset acca now working: Reading, Everton, Sampdoria ~49/1.

## SESSION START HANDSHAKE — SAY THIS FIRST
"Last session ended with the tier whitelist fix confirmed, weekend predictions deployed,
and the HTML generator rebuilt with sub-tabs. First thing this session: run results
check on the 17-20 April predictions and analyse MED vs HIGH pick accuracy, upset acca
hit check, and disagreement call results. What's the current status?"

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
- TIER_DRAW_RATE values were estimates — now verified S35
- Three-pass ran on harvester leagues before tier filter applied — S35, Claude missed it
- Harvester leagues bleeding into history/ not caught proactively — S35
- Instructed manual Python indentation edits via chat across 6+ attempts — S36
  Root cause: nested elif inside wrong block. Fix: always write the file, never instruct
  manual indentation edits. Andrew had to upload the file for Claude to fix it properly.
- OneDrive path confirmed as local Desktop on this machine — Windows redirects — S36

Session log — complete unprompted at close:
- What architectural or foundational questions were raised
- What Claude verified vs what Claude assumed
- Any instances where Andrew corrected Claude
- Any gaps Claude disclosed vs gaps Andrew had to find

## CURRENT STATUS

### S33 DPOL Run
STATUS: COMPLETE — BEST RESULT IN PROJECT HISTORY
- 47.7% overall on 218,317 matches
- 17/17 tiers improved vs cold baseline
- Delta vs cold baseline: +2.3pp
- Key: N1 53.0%, E0 51.4%, I1 51.0%, D1 50.2%, SP1 50.4%
- SP2: +5.1pp — largest single-tier improvement ever
- First run with weather + tier-specific draw priors + teacher layer simultaneously

### Merge Tier Whitelist
STATUS: COMPLETE S36
- TIER_WHITELIST constant added to edgelab_merge.py
- Only 17 proven tiers merge into history/
- 214,968 harvester rows blocked (non-whitelisted leagues stay in harvester_football.db)
- 85,776 whitelisted rows available across 236 tier/season combos
- Nightly bat file calls merge without flags — whitelist applies automatically

### OneDrive
STATUS: RESOLVED S36
- OneDrive sync is off
- EDGELAB folder is at C:\Users\amarr\OneDrive\Desktop — this IS the local Desktop
- Windows redirects Desktop to OneDrive path on this machine
- No move needed. Bat files correct. Task Scheduler unaffected.

### Weather
STATUS: WIRED — 89.1% COVERAGE
- 116,755 fixtures in edgelab.db now have weather_load
- 14,394 permanent gaps (team name variations, pre-2001 data)
- Weather retry still running nightly

### Weekend Predictions S36
STATUS: DEPLOYED
- 120 fixtures, 13 leagues, 17-20 April 2026
- garypredicts.netlify.app updated with sub-tab layout
- Upset acca: Reading to win (100%), Everton to win (95%), Sampdoria to win (84%) — ~49/1
- Key disagreements: Everton H vs Liverpool, Reading H vs Cardiff, Mansfield H vs Luton
- Results check not yet run — do this first in S37

### HTML Generator
STATUS: REBUILT S36
- Sub-tabs per league in Predictions tab
- Sub-tabs per acca type in Gary's Picks (Result, Safety, Value, Winner+BTTS, BTTS, Upset, Upset Watch)
- Sub-tabs per acca type in All Candidates
- Font sizes increased (body 16px, table 15px)
- Upset notes auto-loaded from companion JSON
- Acca upset filter: upset_score >= 0.65, chaos filter removed

### Acca Builder
STATUS: UPDATED S36
- Upset acca now working — 3 qualifying picks this round
- upset_score >= 0.65 threshold correctly excludes borderline calls (Leverkusen 0.62)
- Known issue: BTTS high-confidence picks excluded by decorrelation — review max_same_tier

### Task Scheduler
STATUS: ALL 12 TASKS RUNNING AS SYSTEM
- Football: 02:00 (with merge after — now tier-whitelisted)
- Weather retry: 01:00
- Other sports: 03:00-04:30

## S37 QUEUE — IN ORDER

1. Results check — 17-20 April predictions
   Analyse MED vs HIGH pick accuracy (MED outperformed HIGH last two weeks).
   Upset acca hit check: Reading, Everton, Sampdoria.
   Disagreement call analysis vs market.

2. DataBot team news — NOW UNBLOCKED
   Wire team news into Gary's match briefing.

3. Scoreline logging — small build, high future value
   Log predicted vs actual scoreline in results loop.
   No evolution logic needed — just passive data accumulation.

4. Predictions archive rolling ledger — trigger met
   Round-by-round accuracy vs market, searchable, public.

5. BTTS decorrelation review
   max_same_tier too restrictive for BTTS type.
   Aldershot 92% not appearing — investigate.

6. Gary post-match analysis — M2

7. Outcome-specific DPOL evolution — build sequence:
   a. Variable similarity neighbourhood
   b. Outcome-specific DPOL (separate H/D/A param profiles)
   c. Match-level param-to-result memory

8. Periodic audit — due S37-38.

## STANDARD WEEKLY WORKFLOW (permanent — updated S33)
Step 1: python edgelab_databot.py --key YOUR_API_FOOTBALL_KEY --days 4
Step 2: python edgelab_predict.py --data history/ --fixtures databot_output/YYYY-MM-DD_fixtures.csv --tier all
Step 3: python edgelab_acca.py predictions/YYYY-MM-DD_predictions.csv --all-types
Step 4: python edgelab_upset_picks.py --data history/ --predictions predictions/YYYY-MM-DD_predictions.csv
Step 5: python edgelab_gary.py --data history/ --home "X" --away "Y" --date YYYY-MM-DD --tier E0 --chat
Step 6: python edgelab_results_check.py --key YOUR_API_FOOTBALL_KEY --predictions predictions/YYYY-MM-DD_predictions.csv --date-from YYYY-MM-DD --date-to YYYY-MM-DD
Step 7: python edgelab_html_generator.py predictions/YYYY-MM-DD_predictions.csv
NOTE: Step 6 auto-saves to results/YYYY-MM-DD_results.csv — no extra step.
NOTE: Merge runs automatically after nightly harvest — tier whitelist now active.
NOTE: DataBot = API-Football key. Gary = Anthropic API key.
NOTE: edgelab.db auto-detected — Gary pattern memory and call logging active silently.
NOTE: Create predictions/YYYY-MM-DD_upset_notes.json before Step 7.

## BACKGROUND PROCESSES (Task Scheduler — SYSTEM)
Football: 02:00 (merge automatic after — tier whitelist active)
Weather retry: 01:00 (10k rows, 3s sleep)
Other sports: 03:00-04:30
Logs: harvester_logs\

## KEY NUMBERS
- S33 DPOL overall: 47.7% (218,317 matches) — BEST EVER
- S32 DPOL overall: 47.6% (218,317 matches)
- S31 baseline: 47.1% (131,149 matches)
- S33 three-pass baseline: 45.5% cold → 47.7% evolved (+2.3pp)
- Weather cache: 89.1% — 116,755 wired
- edgelab.db: 131,149 fixtures, weather_load wired, candidate log populated, gary_calls active
- harvester_football.db: 313,999 matches, 121 leagues
- API-Football Pro: active until May 2026

## KNOWN ISSUES — ACTIVE
- Away goals overestimated (1.37 pred vs 1.07 actual) — teacher layer diagnosing
- BTTS overcalling (60% pred vs 50% actual) — monitor
- BTTS high-confidence picks excluded by decorrelation — max_same_tier review needed
- Other sport harvester league IDs unverified
- Draw intelligence dormant — reassess after outcome-specific evolution
- Nearest-neighbour returning single-digit matches at scale — fix at refactor
- New DPOL params home win regression — monitor with S33 params over 4+ weeks
- Dataset hash may be stale — run save_dataset_hash() after any dataset changes
- Weather cache 10.9% still null — permanent gaps acceptable
- MED picks outperforming HIGH last two weeks — track 3-4 more rounds, investigate if pattern holds

## MILESTONE STATUS
- M1: COMPLETE
- M2: IN PROGRESS. S33 DPOL proven. DataBot team news now unblocked.
  Gary post-match analysis, signal recommendation, scoreline logging pending.
- M3: FUTURE

## FILES CHANGED S36
- edgelab_merge.py — TIER_WHITELIST added, 17 proven tiers only
- edgelab_html_generator.py — Full rebuild, sub-tabs, larger font, upset notes auto-load
- edgelab_acca.py — Upset acca filter: upset_score >= 0.65, chaos filter removed

## GIT COMMIT MESSAGE S36
git commit -m 'S36: merge tier whitelist 17 tiers only, html generator sub-tabs per league and acca larger font upset notes auto-load, acca upset filter fixed upset score threshold 0.65, weekend predictions deployed'

## CLAUDE BEHAVIOUR RULES (non-negotiable)
- Never lie. Never cover. If uncertain, say so explicitly.
- One thing at a time.
- Rebrief from project knowledge every 8 prompts. NO EXCEPTIONS.
- Evaluate ideas, do not validate them.
- Session close checklist mandatory — all 8 items, unprompted, in order.
- INTEGRITY LOG must be completed in state file before any documents are generated.
- Generate ALL THREE documents at close AS FILES — not in chat.
- Use view tool to read files — not search summaries. Full read, every line.
- Use EDGELAB_SESSION_START_PROMPT.md at every session start.
- Do not generate files until ALL EIGHT checklist items are complete.
- Do not jump ahead of instructions.
- Git commits: single quotes, no special characters, no brackets, no percent signs.
- Upload correct project files at session start — briefing, state, backlog from latest session.
- When fixing Python files: always write a replacement file. Never instruct manual indentation edits via chat.

## PARKED IDEAS — DO NOT BUILD WITHOUT FLAGGING
- Gary acca picks — trigger: Gary live on site
- Social comment workflow — trigger: content push
- Underdog effect signal — trigger: signals active
- Gary avatar HeyGen — trigger: M3
- Upset flip Stage 2 — trigger: Stage 1 history validated
- API-Football connection — schedule before May 2026 expiry
- Gary temporal awareness — trigger: API-Football connected
- DPOL upset-focused evolution — trigger: signals active
- DPOL exploration budget — trigger: S34 navigated run assessed
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
- DataBot team news — NOW UNBLOCKED — S33 DPOL proven. S37 queue item 2.
- Bogey team bias — trigger: signals active, dataset mature
- Phase 1 signal activation investigation — trigger: Phase 1 review
- RNG/fraud detection using DPOL — trigger: M3 complete
- DPOL as standalone B2B product — trigger: M3 complete
- Predictions archive rolling ledger — trigger: 4+ weeks data ✅. S37 queue item 4.
- Outcome-specific DPOL evolution — NOW ACTIVE. S37 queue item 7.
- Match-level param-to-result memory — trigger: fixture DB mature, teacher layer proven
- Variable similarity neighbourhood — trigger: codebase refactor, fixture DB mature
- South America harvester expansion — trigger: DB mature, football proven
- Cowork workflow integration — trigger: S35 setup complete
- Fixture-specific prediction layer — trigger: outcome-specific evolution proven
- Density map exploration budget — trigger: S34 navigated run assessed
- Scoreline-specific DPOL evolution — trigger: outcome-specific DPOL proven. Logging starts S37.
- International results dataset integration — trigger: Gary M2 complete
- Transfermarkt dataset integration — trigger: signals workstream active. ToS verify first.
- Referee signal activation — trigger: signals active. Data source confirmed.
- Attendance signal — trigger: signals active. Data source confirmed (Transfermarkt).
- Squad value differential signal — trigger: signals active. Data source confirmed.
- Encryption / IP protection — trigger: before public launch
- Companies House registration — trigger: before public launch

## PERIODIC AUDIT SCHEDULE
Last done: S35 — full export re-read (all 37 conversations, 17/04/2026).
Next due: S37-38.

## SESSION 36 INTEGRITY LOG
- OneDrive path confusion — Claude gave incorrect move commands initially.
  Root cause: assumed standard Windows path, didn't account for OneDrive Desktop redirect.
  Andrew identified via screenshots. Resolved: folder is correctly local, no move needed.
- edgelab_acca.py upset filter fix — 6+ failed attempts via manual chat instructions.
  Root cause: instructing Python indentation changes via text is error-prone.
  Claude should have written a replacement file on the first attempt.
  Andrew had to upload the file directly for Claude to read and fix correctly.
  NEW RULE ADDED: always write the file. Never instruct manual indentation edits.
- 13 leagues in predictions correctly identified as expected behaviour — no fixtures
  for N1, SC0, SC3, SP1 this weekend. Claude confirmed correctly.
- No fabrication. No undisclosed gaps after the above.
- All three documents generated as files at session close.
