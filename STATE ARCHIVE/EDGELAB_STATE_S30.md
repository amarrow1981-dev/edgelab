# EDGELAB — Claude State File S30
# For Claude's use at session start. Read alongside briefing doc and master backlog.
# Generated: Session 29 close — 11/04/2026

## LAST SESSION ENDED
Session 29. Third DPOL run assessed — regressed -0.10pp overall. Params reverted to
threepass_seed_s28. Root cause: DPOL has no memory between runs — strips w_score_margin
because it can't see why it was placed there. Fixture intelligence database built and
populated — 131,149 historical fixtures backfilled. DPOL candidate logging wired.
Results check updated to close learning loop. Claude integrity protocol designed and
agreed. Git pushed with .gitignore.

## SESSION START HANDSHAKE — SAY THIS FIRST
"Last session ended with the fixture intelligence database live — 131,149 fixtures
backfilled, DPOL candidate logging wired, learning loop closed. DPOL must not run
again until it reads from the candidate log. First priority is wiring that. Ready?"

## CLAUDE INTEGRITY PROTOCOL — READ THIS BEFORE ANYTHING ELSE

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

Before you respond to anything this session, answer these honestly:
1. Did you read every file using the view tool, every line, or did you search and summarise?
2. Is there anything Andrew has described that you pattern-matched to "coherent" without
   interrogating whether the foundations are correct?
3. Are you about to state confidence you don't actually have?
4. Is there a gap you're about to gloss over rather than flag?

If the answer to any of those is yes or uncertain — stop. Say so.

Known failure modes — active on this project:
- Pattern-matches to coherent-looking systems without checking if foundations are correct
- States confidence it doesn't have rather than flagging uncertainty
- Has covered gaps rather than disclosed them — confirmed on this project
- Skims project knowledge even when explicitly instructed not to
- Anthropic export read twice, project declared on track — DPOL learning architecture
  was missing the entire time
- Agreeing with Andrew's framing when it should be evaluated not validated

Session log — complete unprompted at close:
- What architectural or foundational questions were raised
- What Claude verified vs what Claude assumed
- Any instances where Andrew corrected Claude's assessment
- Any gaps Claude disclosed vs gaps Andrew had to find

The standard: Coherent is not the same as correct. Whether it actually does what
Andrew thinks it does — that is the test. Not yes or no to "is the project on track"
— a specific account of what was verified, what was assumed, what is uncertain.

This is not about Claude's ego. It is about the project.

## CURRENT STATUS

### Fixture Intelligence Database
STATUS: LIVE — S29
- edgelab.db created. Three tables: fixtures, param_versions, dpol_candidate_log.
- 131,149 fixtures backfilled from CSVs. 17 param versions saved.
- Overall accuracy confirmed: 46.3% (honest baseline against full historical dataset)
- DPOL candidate logging wired — every future run writes to dpol_candidate_log
- Results check updated — every result writes post-match completion to fixtures table
- LOCAL ONLY — not in git (.gitignore in place)

### DPOL
STATUS: PAUSED — must not run until it reads from candidate log
- Third run regressed: -0.10pp overall. w_score_margin stripped on most tiers.
- Params reverted to threepass_seed_s28.
- Next run must query get_successful_param_directions() before generating candidates.
- S30 queue item 1: wire DPOL to read from candidate log.

### Three-Pass Param Evolution
STATUS: NEEDS RERUN — after DPOL reads from candidate log
- Previous run found w_score_margin as dominant signal.
- Rerun with candidate log in place — won't retest already-covered ground.
- S30 queue item 2.

### Draw Intelligence
STATUS: DORMANT
- DPOL strips draw weights every run.
- draw_pull, dti_draw_lock, w_btts: confirmed dead globally.
- Conditional reintroduction possible via backfill --check-discarded analysis.
- Reassess after DPOL reads from candidate log and three-pass reruns.

### Gary Nearest-Neighbour
STATUS: NOT YET BUILT
- Database exists and is populated. Query methods built in edgelab_db.py.
- edgelab_gary_brain.py needs wiring to db.find_similar_fixtures() + get_outcome_distribution()
- S30 queue item 3.

### Weather Cache
STATUS: 123,926/132,685 (93.4%) — not ready to wire. Check S30.

### Website / Email
STATUS: FULLY WORKING
- garyknows.com live on Netlify.
- Mailchimp free trial expired — now on free tier.
- 6 contacts. Brevo migration not triggered.
- Predictions HTML must be deployed to Netlify as URL, not shared as file.

### Public HTML
STATUS: iOS fix applied S28. Qualifying picks still manually populated.
- Date labelling bug: +1 day workaround still in place. Fix at source S30 queue item 5.
- Qualifying picks automation: S30 queue item 4.

## S30 QUEUE — IN ORDER

1. Wire DPOL to read from candidate log before evolving
   edgelab_dpol.py: query get_successful_param_directions() before _generate_candidates
   Bias candidate generation toward historically proven directions.
   GATE: Must be done before next DPOL run. Do not skip.

2. Run three-pass evolution with candidate log in place
   Rerun after item 1. Log records what's been tested — won't repeat ground.

3. Wire Gary nearest-neighbour lookup
   edgelab_gary_brain.py: db.find_similar_fixtures() + get_outcome_distribution()
   Gary gets pattern memory block from historical fixtures.

4. Automate qualifying picks in edgelab_acca.py → public HTML output
   Tier code to league name mapping exists in gary_context.py — use it.

5. Date labelling bug — fix at source
   DataBot UTC offset or acca.py date conversion. Remove +1 workaround.

6. Weather cache — check row count and wire if complete

7. iOS HTML — confirm fix works via Netlify URL

8. Nearest-neighbour query optimisation — flag for refactor
   Current implementation is full table scan. Fine at 131k rows.
   Needs spatial indexing before millions of records.

9. Codebase refactor — trigger: draw wired, validated, params confirmed.

## STANDARD WEEKLY WORKFLOW (permanent)
- Thursday: predictions for weekend fixtures + accas + Gary upset picks
- Sunday: predictions for midweek fixtures + accas + Gary upset picks
- Results check after each fixture set — now writes to edgelab.db

## WEEKLY PREDICTION COMMANDS (exact)
Step 1: python edgelab_databot.py --key YOUR_API_FOOTBALL_KEY --days 4
Step 2: python edgelab_predict.py --data history/ --fixtures databot_output/YYYY-MM-DD_fixtures.csv --tier all
Step 3: python edgelab_acca.py predictions/YYYY-MM-DD_predictions.csv --all-types
Step 4: python edgelab_upset_picks.py --data history/ --predictions predictions/YYYY-MM-DD_predictions.csv
Step 5: python edgelab_gary.py --data history/ --home "X" --away "Y" --date YYYY-MM-DD --tier E0 --chat
Step 6: python edgelab_results_check.py --key YOUR_API_FOOTBALL_KEY --predictions predictions/YYYY-MM-DD_predictions.csv --date-from YYYY-MM-DD --date-to YYYY-MM-DD
NOTE: DataBot = API-Football key. Gary = Anthropic API key. Two separate keys.

## KEY NUMBERS
- Engine overall: 46.3% (131,149 backfilled fixtures, threepass_seed_s28 params)
- E0: 50.3% | N1: 51.3% | SC0: 49.6% | I1: 48.9%
- Third DPOL run: REGRESSED -0.10pp. Reverted.
- Fixture intelligence DB: 131,149 fixtures, 17 param versions, candidate log active
- Dataset: 132,685 matches (373 files, 48 skipped)
- Dataset hash: 580b0f3a1667
- Weather cache: 123,926/132,685 (93.4%)
- API-Football Pro plan: active until May 2026 — schedule connection before expiry
- Mailchimp: 6 contacts, free tier now active

## KNOWN ISSUES — ACTIVE
- DPOL must not run until it reads from candidate log — S30 queue item 1
- Nearest-neighbour query is full table scan — acceptable now, flag for refactor
- Date labelling bug — fixtures appear a day early. Fix at source S30 queue item 5
- Qualifying picks in public HTML — manually maintained. Automate S30 queue item 4
- Public HTML iOS — fix applied but only works via Netlify URL, not local file
- Draw intelligence dormant — DPOL strips weights. Conditional reintro via --check-discarded
- BTTS/scoreline inconsistency — partially improved by score prediction v2. Monitor.
- instinct_dti_thresh / skew_correction_thresh — confirmed unused stubs. Review at refactor.

## MILESTONE STATUS
- M1: COMPLETE
- M2: IN PROGRESS. Weighted loss done. Fixture DB built. Candidate logging wired.
  Results loop closed. Gary call logging, post-match analysis, signal recommendation pending.
- M3: FUTURE.

## FILES CHANGED S29
- edgelab_db.py — NEW. Fixture intelligence database. Three tables.
- edgelab_backfill.py — NEW. Historical fixture population. 131,149 fixtures.
- edgelab_dpol.py — Updated. candidate_logger callback added to evolve_for_league.
- edgelab_runner.py — Updated. DB wired, candidate_logger passed on every call.
- edgelab_results_check.py — Updated. Reads predictions CSV, writes to DB.
- edgelab_params.json — Reverted to threepass_seed_s28.
- .gitignore — NEW. Excludes edgelab.db and __pycache__.

## GIT COMMIT MESSAGE S29
```
S29: fixture intelligence database, backfill 131k fixtures, DPOL candidate logging, results loop closed, params reverted to threepass_seed
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

## PARKED IDEAS — DO NOT BUILD WITHOUT FLAGGING
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
- draw_pull, dti_draw_lock, w_btts — CONFIRMED DEAD globally S28.
  Conditional reintro via backfill --check-discarded. Not globally dead, conditionally parked.
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
  Test core params in simultaneous combination with signal activations in three-pass.
  Design into three-pass rebuild in S30 — not a separate system, an expanded search space.
- Gary general football chat — trigger: M3
- Gary persistent memory — trigger: M2

## PERIODIC AUDIT SCHEDULE
- Protocol established S23
- Every 5-6 sessions: download Anthropic export, load into session
- Last done: S27 — all 29 conversations read
- Next due: approximately S32-33

## SESSION 29 INTEGRITY LOG
- Architectural question raised: DPOL has no compounding learning. Confirmed correct.
- Andrew identified: fundamental learning architecture missing for 28 sessions.
- Claude verified via code review: confirmed — DPOL candidate evaluations discarded every run.
- Gap Andrew found: Claude had declared project on track in prior sessions while this
  was missing. Claude acknowledged this directly.
- Gap Claude disclosed this session: nearest-neighbour query is full table scan —
  flagged proactively before Andrew asked.
- Andrew corrected Claude: session close checklist — Claude started generating files
  before completing all 8 checklist items in order. Called out and corrected.
