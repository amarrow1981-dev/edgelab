# EdgeLab — Session 34 Briefing
# Replaces: EDGELAB_BRIEFING_SESSION33_START.md
# Generated: Session 33 close — 13/04/2026

## What We Are Building

Most sports analytics measures average. Average is what bookmakers price. Average is
what everyone else optimises for. We already beat average — E0 at 51.1%, N1 at 52.9%,
overall at 47.6% across 218,317 matches (S32 DPOL run, confirmed S33).

That is not the goal. The goal is to understand what is not average.

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

The unconventional signal thesis: Everyone else is fishing in the same pond — form,
GD, H2H, home advantage. The market has priced all of that in efficiently. Matching it
is the floor, not the ceiling. The ceiling is the signals nobody else is looking for.
Across 218k+ matches, if a signal has any real predictive power, DPOL will find it.

Gary is both a standalone product and integrated into EdgeLab.
The goal is the most comprehensive football and sports statistics platform on earth.
Once DPOL is proven on football — expand to other sports and repeat the formula.
All under Khaotikk Ltd.

The product vision: bookmakers will notice — not because of stake sizes, but because
of consistent edge on non-obvious selections. Safe calls build the authority and the
track record. Upset calls are where the money is. Gary communicates both in plain
English. When the upset layer, travel signal, motivation gap, and draw intelligence
fire together — Gary calling a 3/1, a 5/1 and a 7/1 in the same acca with conviction
behind each one is a 100/1+ ticket that is not a punt. It is a position.

This is not a betting tool. This is the best football brain ever built.

Owner: Andrew Marrow
Company: Khaotikk Ltd — khaotikk.com

Current engine status: 47.6% overall on 218,317 matches (S32 DPOL, confirmed S33).
Navigation fired on all 17 tiers. 17/17 tiers improved vs three-pass baseline.

---

## The Architecture — What Changed in Session 33

1. S32 DPOL confirmed — 47.6% overall, navigation working.
17/17 tiers improved. +2.1pp overall vs starting params.
N1 52.9%, I1 51.0%, E0 51.1%, SP1 50.5%, SP2 45.7%.

2. Pass 2b post-match teacher layer — confirmed working.
E0 test passed. Teacher confirmed params: w_form, w_gd, w_score_margin, w_h2h_draw,
w_btts for E0. Away win signals mostly unconfirmed by post-match evidence — the away
model is genuinely noisier than the home model. Diagnostic value confirmed.
Full three-pass gated on weather reaching 95%.

3. Gary call logging — fully wired.
Every Gary ask() silently logs to gary_calls table in edgelab.db.
Captures: full engine output, Gary full response, extracted prediction, confidence band,
upset/draw flags, pattern memory context.
complete_gary_call wired into results_check.py — marks gary_correct, engine_correct,
gary_vs_engine on every result. Migration safe on existing edgelab.db.

4. Merge automated in football harvester bat file.
edgelab_merge.py runs automatically after each nightly football harvest.

5. Market vs EdgeLab comparison framework confirmed.
Week 1 disagreement analysis: EdgeLab 11 correct calls at avg 3.40 odds — above
break-even (29.4% needed, 42.3% achieved). Market 9 correct at avg 2.09 — below
break-even. Core product thesis confirmed in data for second consecutive week.
Market comparison runs every prediction round as standard workflow step.

6. Git commit format fixed.
All future commits: single quotes, no special characters, no parentheses, no percent signs.

---

## CLAUDE INTEGRITY PROTOCOL — NON-NEGOTIABLE

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
- Clear downloads folder of .py files — Windows renames duplicates silently

Session log — complete unprompted at close:
- What architectural or foundational questions were raised
- What Claude verified vs what Claude assumed
- Any instances where Andrew corrected Claude
- Any gaps Claude disclosed vs gaps Andrew had to find

---

## Ordered Work Queue

Session 34 — priorities in order

1. Check weather retry progress
   harvester_logs\weather_retry.log
   If 95%+ — proceed to item 2 immediately.

2. Wire weather to fixture DB
   Re-backfill edgelab.db weather_load from weather_cache.csv.
   GATE: do not run three-pass until weather is wired.

3. Three-pass full param evolution — weather + post-match teacher + unified dataset
   First definitive run with all improvements simultaneously.
   Watch Pass 2b confidence scores — should increase season-over-season.
   Seed via edgelab_threepass_seed.py.

4. S33 DPOL run — second navigated run
   Navigation + weather + post-match teacher seeded params.
   Compare to S32 DPOL result. This is where the full architecture proves itself.

5. Draw rate prior audit
   Check whether draw rate assumption in engine is flat or tier-specific.
   If flat — fix before draw intelligence build.

6. Full H/A/D disagreement analysis
   Pull the 9 wrong disagreement calls from 09/04 predictions.
   Confidence, chaos tier, DTI, upset score for each.
   Diagnose: miscalibrated or should have flagged uncertainty?

7. Gary post-match analysis — M2 item.

8. DataBot extension — team news at prediction time
   Trigger: S33 DPOL proven.

9. Verify other sport harvester league IDs.

10. Predictions archive — rolling HTML ledger
    Trigger: 4+ weeks predictions data, stable engine params.

11. Nearest-neighbour query — flag for refactor.

12. Codebase refactor — trigger: draw wired, validated, params confirmed.

---

## Results Monitoring — track each prediction round

Metric | Baseline | Direction
Result accuracy vs market | Week 1 old params +1.7pp, new -2.5pp (1 week only) | up
Disagreement win avg odds | 3.40 | maintain/up
Home win accuracy | 79.5% new params | up
Away win accuracy | 17.1% new params | up
Draw prediction | 0.0% both systems | up with draw intelligence
MED band accuracy | 84.2% S32.a baseline | maintain/up
Away goals predicted | 1.37 vs 1.07 actual | down toward 1.07
BTTS overcall | 60% pred vs 50% actual | converge

---

## Standard Weekly Workflow (permanent — updated S33)

Thursday: predictions + accas + Gary upset picks + market comparison
Sunday: predictions + accas + Gary upset picks + market comparison

Step 1: python edgelab_databot.py --key YOUR_API_FOOTBALL_KEY --days 4
Step 2: python edgelab_predict.py --data history/ --fixtures databot_output/YYYY-MM-DD_fixtures.csv --tier all
Step 3: python edgelab_acca.py predictions/YYYY-MM-DD_predictions.csv --all-types
Step 4: python edgelab_upset_picks.py --data history/ --predictions predictions/YYYY-MM-DD_predictions.csv
Step 5: python edgelab_gary.py --data history/ --home "X" --away "Y" --date YYYY-MM-DD --tier E0 --chat
Step 6: python edgelab_results_check.py --key YOUR_API_FOOTBALL_KEY --predictions predictions/YYYY-MM-DD_predictions.csv --date-from YYYY-MM-DD --date-to YYYY-MM-DD
Step 7: python edgelab_html_generator.py predictions/YYYY-MM-DD_predictions.csv
NOTE: Merge runs automatically after nightly harvest (automated S33).
NOTE: DataBot = API-Football key. Gary = Anthropic API key.
NOTE: edgelab.db auto-detected — Gary pattern memory and call logging active silently.
NOTE: Create predictions/YYYY-MM-DD_upset_notes.json before Step 7 for Gary text.

Background Processes (Task Scheduler — all SYSTEM):
Football harvest: 02:00 daily (merge runs automatically after)
Weather retry: 01:00 daily (10k rows, 3s sleep)
Other sports: 03:00–04:30 staggered
Logs: harvester_logs\

File Management:
DELETE old .py file BEFORE copying new version from downloads.
Windows silently renames: edgelab_db.py becomes edgelab_db (2).py. This breaks everything.

Git Commits — PowerShell safe format every time:
git commit -m 'message here — single quotes, no special chars, no brackets, no percent signs'

---

## Parked — do not build without flagging

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
- Data product API licensing — trigger: database mature, multiple sports, M3 complete
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
- High/low scoring period investigation — trigger: signals active
- Phase 1 signal activation investigation — trigger: Phase 1 review
- Cumulative fixture fatigue signal — trigger: signals active
- Seasonal momentum signal — trigger: dataset mature
- Score prediction away goals recalibration — monitor each round
- RNG/fraud detection using DPOL — trigger: M3 complete, separate evaluation
- DPOL as standalone B2B product — trigger: M3 complete, EdgeLab proven
- Predictions archive rolling ledger — trigger: 4+ weeks data, stable params
- Market comparison as standalone script — trigger: weekly workflow demands it

---

## Key Numbers

Tier | S32 DPOL Result
E0   | 51.1%
E1   | 44.7%
E2   | 45.0%
E3   | 43.4%
EC   | 46.2%
B1   | 49.2%
D1   | 49.7%
D2   | 44.2%
I1   | 51.0%
I2   | 42.6%
N1   | 52.9%
SC0  | 50.3%
SC1  | 44.7%
SC2  | 49.1%
SC3  | 48.2%
SP1  | 50.5%
SP2  | 45.7%
OVERALL | 47.6%

S31 baseline: 47.1% on 131,149 matches.
S32 three-pass baseline: 46.7% on 218,317 matches.

---

## Files

File | Status | Notes
edgelab_engine.py | Updated S26 | w_xg_draw + composite_draw_boost
edgelab_dpol.py | Updated S30 | db param, directional candidate bias
edgelab_runner.py | Updated S32.a | Global guard 3k sample, all params, newest-first seasons
edgelab_db.py | Updated S33 | gary_calls expanded, full logging, migration updated
edgelab_config.py | Updated S32.a | load_params loads all param fields
edgelab_param_evolution.py | Updated S33 | Pass 2b confirmed working
edgelab_results_check.py | Updated S33 | complete_gary_call wired silently
edgelab_gary.py | Updated S33 | ask logs silently, confidence band, ctx.gary_memory fix
edgelab_gary_brain.py | Updated S30 | PatternMemory dataclass
edgelab_gary_context.py | Updated S30 | Pattern memory in match prompt
edgelab_predict.py | Updated S31 | db auto-detect
edgelab_html_generator.py | Updated S31 | Upset notes injection
edgelab_signals.py | Updated S31 | Ground coords 549 teams
edgelab_params.json | Updated S32 | S32 DPOL all 17 tiers
edgelab_acca.py | Updated S32 | Mutually exclusive acca pools
edgelab_databot.py | Updated S32 | Harvester write side effect
edgelab_merge.py | New S32 | Harvester DB to history CSV merge
edgelab_harvester.py | New S31 | Background data collection
edgelab_backfill.py | New S29 | Historical fixture population
edgelab_threepass_seed.py | New S28 | Seeds param_profile into params.json
edgelab.db | Live S29 | LOCAL ONLY
harvester_football.db | New S31 | LOCAL ONLY
setup_harvester_tasks.ps1 | New S32 | Task Scheduler 12 tasks
harvester_tasks/run_harvester_football.bat | Updated S33 | Merge step added after harvest

---

## Dataset

609 CSV files, 25 years, 17 tiers, 218,317 matches (48 skipped).
Weather cache: ~69% — Task Scheduler running as SYSTEM, expected 95% within 3 nights.
edgelab.db: 131,149 fixtures, candidate log populated, gary_calls table active.
harvester_football.db: 87,184 matches, 2010-2026.

---

## Brand and Marketing

garyknows.com: live. garypredicts.netlify.app: live.
Mailchimp: 6 contacts, free tier. Brevo migration trigger: 400 contacts.
Social: paused. Gary avatar: 7-sec Kling clip exists.

---

## Periodic Audit

Last done: S32 — all 34 conversations. Next due: S37-38.

---

## Session Close Checklist

1. Scalability check
2. Queue review — completed / in progress / deferred
3. Files updated — confirm changes, update files table
4. Known issues updated
5. Params table updated if DPOL run completed
6. Brand/marketing updated
7. Git commit message — PowerShell safe: single quotes, no special chars
8. Generate briefing doc + state file + master backlog — none truncated — AS FILES

---

## To Start Session 34

1. Use EDGELAB_SESSION_START_PROMPT.md as opening prompt
2. Upload EDGELAB_BRIEFING_SESSION34_START.md to project knowledge
3. Upload EDGELAB_STATE_S34.md to project knowledge
4. Upload EDGELAB_MASTER_BACKLOG_S33.md to project knowledge
5. Check weather retry log first — if 95%+ proceed straight to wiring
6. Work queue from top
