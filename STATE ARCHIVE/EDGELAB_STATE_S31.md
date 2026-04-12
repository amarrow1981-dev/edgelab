# EDGELAB — Claude State File S31
# For Claude's use at session start. Read alongside briefing doc and master backlog.
# Generated: Session 30 close — 11/04/2026

## LAST SESSION ENDED
Session 30. DPOL candidate log direction query fixed — proper JOIN, signed direction.
DPOL wired to read from candidate log before generating candidates. S30 DPOL run
initiated (in progress at session close — still on EC tier). Gary nearest-neighbour
pattern memory built and wired — PatternMemory dataclass, db param on GaryBrain,
_build_pattern_memory() queries fixture DB per match. HTML generator built —
edgelab_html_generator.py replaces manual predictions HTML build entirely.
Predictions HTML deployed to Netlify, confirmed working on iOS.

## SESSION START HANDSHAKE — SAY THIS FIRST
"Last session ended with DPOL navigation wired, Gary's pattern memory live, and the
HTML generator built. First thing: what did the S30 DPOL run produce? Log the result
before we do anything else — that number determines whether the navigation is working."

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
Andrew thinks it does — that is the test.

This is not about Claude's ego. It is about the project.

## CURRENT STATUS

### DPOL Navigation
STATUS: WIRED S30 — first navigated run in progress
- get_successful_param_directions() rebuilt — proper JOIN to param_versions,
  signed direction (candidate_value - base_value), delta-weighted average.
- DPOLManager accepts db param. evolve_for_league queries directions before
  generating candidates. _generate_candidates uses directional bias (2x step
  in proven direction, normal exploratory step opposite).
- S30 run populates candidate log. Navigation fires fully on SECOND run (S31).
- S30 run result: IN PROGRESS AT SESSION CLOSE — log at S31 start.

### Fixture Intelligence Database
STATUS: LIVE — S29
- edgelab.db: 131,149 fixtures, 17 param versions.
- DPOL candidate log: populating during S30 run.
- Gary nearest-neighbour: WIRED S30.

### Gary Pattern Memory
STATUS: BUILT AND WIRED S30 — activate by passing db=EdgeLabDB() to GaryBrain
- PatternMemory dataclass in edgelab_gary_brain.py
- GaryBrain accepts optional db parameter
- _build_pattern_memory() queries find_similar_fixtures() + get_outcome_distribution()
- Renders in match prompt: "In N similar historical fixtures: H X%, D Y%, A Z%"
- Engine agreement signal: "agrees" / "disagrees" / "mixed"
- NOT YET ACTIVATED in weekly workflow — edgelab_gary.py and edgelab_predict.py
  still instantiate GaryBrain without db. Wire in S31 queue item 3.

### HTML Generator
STATUS: BUILT S30
- edgelab_html_generator.py — one command builds complete predictions page
- Replaces manual HTML build entirely
- Usage: python edgelab_html_generator.py predictions/YYYY-MM-DD_predictions.csv
- Now part of standard weekly workflow (Step 7)
- Gary upset analysis: card structure built, text is manual input for now.
  Wire via companion JSON in S31 (queue item 4).

### Three-Pass Param Evolution
STATUS: NEEDS RERUN — after S30 DPOL result assessed
- Previous run found w_score_margin as dominant signal.
- Rerun after S30 result logged and understood.

### Draw Intelligence
STATUS: DORMANT
- DPOL strips draw weights. Reassess after second navigated run.

### Weather Cache
STATUS: 123,926/132,685 (93.4%) — check S31.

### Website / Email
STATUS: FULLY WORKING
- garyknows.com live on Netlify.
- Predictions HTML: spectacular-licorice-3d5119.netlify.app (rename pending)
- Mailchimp free tier. 6 contacts.

## S31 QUEUE — IN ORDER

1. Log S30 DPOL run result
   Record accuracy vs 46.3% baseline. If regressed: first run was blind
   (candidate log empty), navigation didn't fire. Expected. Second run is the test.
   GATE: Log result and understand it before running DPOL again.

2. Second DPOL run — first with navigation active
   S30 populated the candidate log. S31 run is where navigation fires.
   Watch for "Navigation: N proven directions loaded" in output.
   This is the test of the S29-S30 architecture.

3. Wire Gary db in weekly workflow
   edgelab_gary.py: add --db flag or auto-detect edgelab.db.
   edgelab_predict.py --gary: pass db=EdgeLabDB() to GaryBrain.
   Pattern memory is built but not activated in the pipeline yet.

4. Gary upset analysis injection
   HTML generator has upset card structure, text is generic placeholder.
   Build: YYYY-MM-DD_upset_notes.json companion file.
   Generator reads it and injects Gary's text per match.
   Format: {"Home Team vs Away Team": "Gary's analysis here"}

5. Acca filter rebuild
   AccaBuilder.get_picks() filter stage — per-type logic:
   safety: cap odds (B365H/A < 2.5), upset score < 0.3
   value: mandatory positive edge required, not just preferred
   result: remove draws from qualifying pool
   btts/winner_btts/upset: already distinct, minor tuning
   Real product quality issue — current output is misleading.

6. Weather cache — check row count and wire if complete
   At 93.4% at S29. If complete: wire to DPOL + fixtures table.

7. Rename Netlify site
   spectacular-licorice-3d5119 → gary-picks.netlify.app
   Site configuration → General → Site details → Change site name

8. Nearest-neighbour query optimisation — flag for refactor
   Full table scan. Fine at 131k. Needs spatial indexing before millions.

9. Codebase refactor — trigger: draw wired, validated, params confirmed.

## STANDARD WEEKLY WORKFLOW (permanent — updated S30)
- Thursday: predictions for weekend fixtures + accas + Gary upset picks
- Sunday: predictions for midweek fixtures + accas + Gary upset picks
- Results check after each fixture set — writes to edgelab.db

## WEEKLY PREDICTION COMMANDS (exact — Step 7 added S30)
Step 1: python edgelab_databot.py --key YOUR_API_FOOTBALL_KEY --days 4
Step 2: python edgelab_predict.py --data history/ --fixtures databot_output/YYYY-MM-DD_fixtures.csv --tier all
Step 3: python edgelab_acca.py predictions/YYYY-MM-DD_predictions.csv --all-types
Step 4: python edgelab_upset_picks.py --data history/ --predictions predictions/YYYY-MM-DD_predictions.csv
Step 5: python edgelab_gary.py --data history/ --home "X" --away "Y" --date YYYY-MM-DD --tier E0 --chat
Step 6: python edgelab_results_check.py --key YOUR_API_FOOTBALL_KEY --predictions predictions/YYYY-MM-DD_predictions.csv --date-from YYYY-MM-DD --date-to YYYY-MM-DD
Step 7: python edgelab_html_generator.py predictions/YYYY-MM-DD_predictions.csv
NOTE: DataBot = API-Football key. Gary = Anthropic API key. Two separate keys.

## KEY NUMBERS
- Engine overall: 46.3% (131,149 backfilled fixtures, threepass_seed_s28 params)
- E0: 50.3% | N1: 51.3% | SC0: 49.6% | I1: 48.9%
- S30 DPOL run: IN PROGRESS — log at S31 start
- Fixture intelligence DB: 131,149 fixtures, 17 param versions, candidate log active
- Dataset: 132,685 matches (373 files, 48 skipped)
- Dataset hash: 580b0f3a1667
- Weather cache: 123,926/132,685 (93.4%)
- API-Football Pro plan: active until May 2026 — schedule connection before expiry
- Mailchimp: 6 contacts, free tier

## KNOWN ISSUES — ACTIVE
- S30 DPOL run result pending — log at S31 start before any further DPOL work
- Gary pattern memory not activated in weekly pipeline — wire db in S31 queue item 3
- Gary upset analysis in HTML is generic placeholder — wire JSON injection S31 queue 4
- Acca filter rebuild needed — result/safety/value not meaningfully distinct — S31 queue 5
- Nearest-neighbour query full table scan — acceptable now, flag for refactor
- Weather cache 93.4% — check S31
- BTTS/scoreline inconsistency — monitoring
- Netlify site name not renamed yet — spectacular-licorice-3d5119

## MILESTONE STATUS
- M1: COMPLETE
- M2: IN PROGRESS. Weighted loss done. Fixture DB built. Candidate logging wired.
  Results loop closed. DPOL navigation wired. Gary pattern memory built.
  Gary call logging, post-match analysis, signal recommendation pending.
- M3: FUTURE.

## FILES CHANGED S30
- edgelab_db.py — Updated. get_successful_param_directions() rebuilt with proper JOIN
  and signed direction computation. Previous implementation was meaningless.
- edgelab_dpol.py — Updated. DPOLManager accepts db param. evolve_for_league queries
  proven directions. _generate_candidates rebuilt with directional bias.
- edgelab_runner.py — Updated. db passed to DPOLManager.
- edgelab_gary_brain.py — Updated. PatternMemory dataclass. GaryBrain accepts db.
  _build_pattern_memory() built. build_context() wired.
- edgelab_gary_context.py — Updated. _build_pattern_memory_section() added.
  _build_slots_section() updated. match_prompt() includes pattern memory.
- edgelab_html_generator.py — NEW. Full predictions HTML generator.

## GIT COMMIT MESSAGE S30
```
S30: DPOL candidate log navigation, Gary nearest-neighbour pattern memory, HTML generator, Netlify deploy
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

## PERIODIC AUDIT SCHEDULE
- Protocol established S23
- Every 5-6 sessions: download Anthropic export, load into session
- Last done: S27 — all 29 conversations read
- Next due: approximately S32-33

## SESSION 30 INTEGRITY LOG
- Architectural question raised: get_successful_param_directions() was meaningless —
  using absolute param values not signed deltas vs base. Identified by Claude on
  code review before building, fixed before wiring.
- Claude verified: DPOL candidate log empty at session start (confirmed via db --stats).
  Navigation cannot fire until first run completes — noted proactively.
- Andrew flagged: Gary acca picks pulling same pool across types — not meaningfully
  distinct. Claude confirmed on code review. Added to queue as formal item.
- Gap Claude disclosed: Gary pattern memory not wired in edgelab_gary.py or
  edgelab_predict.py — built but not activated in pipeline. Flagged proactively,
  added to S31 queue.
- No instances where Andrew had to find a gap Claude missed.
