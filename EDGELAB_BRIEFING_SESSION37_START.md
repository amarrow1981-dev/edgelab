# EdgeLab — Session 37 Briefing
# Replaces: EDGELAB_BRIEFING_SESSION36_START.md
# Generated: Session 36 close — 17/04/2026

## What We Are Building

Most sports analytics measures average. Average is what bookmakers price. Average is
what everyone else optimises for. We already beat average — E0 at 51.4%, N1 at 53.0%,
overall at 47.7% across 218,317 matches (S33 DPOL run, confirmed S35).

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

Current engine status: 47.7% overall on 218,317 matches (S33 DPOL run, confirmed S35).
Navigation fired on all 17 tiers. 17/17 tiers improved vs three-pass baseline.
Best result in project history.

---

## The Architecture — What Changed in Session 36

1. edgelab_merge.py tier whitelist — COMPLETE.
   TIER_WHITELIST constant added. Only the original 17 proven tiers merge into history/.
   All other harvester leagues accumulate in harvester_football.db only.
   Dry run confirmed: 214,968 rows blocked, 85,776 whitelisted rows available.
   Nightly merge now safe — no further contamination of the engine dataset.

2. OneDrive — RESOLVED.
   EDGELAB folder is at C:\Users\amarr\OneDrive\Desktop — this IS the local Desktop
   on this machine (Windows redirects Desktop to OneDrive path). OneDrive sync is off.
   No move needed. Bat files are correct. Task Scheduler unaffected.

3. Weekend predictions — COMPLETE. First live test of full S33 architecture.
   120 fixtures across 13 leagues (N1, SC0, SC3, SP1 had no fixtures this round).
   Deployed to garypredicts.netlify.app.
   Disagreement calls to watch: Everton vs Liverpool (H, 95%, upset score 0.74),
   Reading vs Cardiff (H, 100%, upset score 0.85), Mansfield vs Luton (H, 100%).
   Upset acca: Reading, Everton, Sampdoria — 3-fold ~49/1.

4. HTML generator rebuilt — COMPLETE.
   Sub-tabs per league in Predictions tab.
   Sub-tabs per acca type in Gary's Picks tab (Result, Safety, Value, Winner+BTTS,
   BTTS, Upset Acca, Upset Watch).
   Sub-tabs per acca type in All Candidates tab.
   Font sizes increased throughout (body 16px, table cells 15px).
   Upset notes auto-loaded from companion JSON file.
   edgelab_html_generator.py fully rebuilt — not a patch job.

5. Acca upset filter fixed — COMPLETE.
   Previous: filtered by chaos tier (CHAOS_ALLOWED = LOW/MED) — blocked all upset
   picks because they all have HIGH chaos. Zero qualifying picks every week.
   Fixed: filter by upset_score >= 0.65 instead. Chaos filter removed for upset type.
   Leverkusen (0.62) correctly excluded. Reading (0.85), Everton (0.74) correctly included.

6. Known issues identified this session:
   - BTTS high-confidence picks excluded by decorrelation — Aldershot 92% not appearing.
     max_same_tier logic may be too restrictive for BTTS type specifically.
   - MED picks outperforming HIGH last two weeks — track over next 3-4 rounds.
     If pattern holds, investigate confidence calibration at top end.

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
- Clear downloads folder before copying new .py files — Windows renames duplicates silently
- TIER_DRAW_RATE values were estimates — now verified S35
- Three-pass ran on harvester leagues before tier filter applied — S35, Claude missed it
- Harvester leagues bleeding into history/ not caught proactively — S35
- Instructed manual Python indentation edits via chat — always write the file instead — S36
- OneDrive path confusion — confirmed local Desktop IS the OneDrive path on this machine — S36

Session log — complete unprompted at close:
- What architectural or foundational questions were raised
- What Claude verified vs what Claude assumed
- Any instances where Andrew corrected Claude
- Any gaps Claude disclosed vs gaps Andrew had to find

---

## Ordered Work Queue

Session 37 — priorities in order

1. Run results check on 17-20 April predictions
   python edgelab_results_check.py --key YOUR_KEY --predictions predictions/2026-04-17_predictions.csv --date-from 2026-04-18 --date-to 2026-04-21
   Analyse: MED vs HIGH pick accuracy, upset acca hit check, disagreement call analysis.

2. DataBot team news — NOW UNBLOCKED (S33 DPOL proven)
   Wire team news into Gary's match briefing.
   Gary should know about key absences before making a call.

3. Scoreline logging — small build, high future value
   Add predicted vs actual scoreline logging to results loop.
   Feeds scoreline-specific DPOL evolution map passively.
   No evolution logic needed yet — just logging.

4. Predictions archive rolling ledger — trigger now met (4+ weeks data, stable params)
   Rolling HTML showing round-by-round accuracy vs market.
   Searchable, public track record. Separate from weekly predictions HTML.

5. BTTS decorrelation review
   Aldershot at 92% not appearing in BTTS acca — max_same_tier too restrictive for BTTS.
   BTTS picks from same league are less correlated than result picks.
   Review and adjust acca builder logic.

6. Gary post-match analysis — M2
   After results in, Gary analyses key calls: what he got right, what he missed, why.

7. Outcome-specific DPOL evolution — triggers met, build sequence:
   a. Variable similarity neighbourhood (replace fixed top-N with threshold-based)
   b. Outcome-specific DPOL evolution (separate H/D/A param profiles)
   c. Match-level param-to-result memory

8. Periodic audit — due S37-38. Full export re-read.

---

## Parked Ideas — Do Not Build Without Flagging

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
- Bogey team bias — trigger: signals active, dataset mature
- Phase 1 signal activation investigation — trigger: Phase 1 review
- RNG/fraud detection using DPOL — trigger: M3 complete
- DPOL as standalone B2B product — trigger: M3 complete
- Predictions archive rolling ledger — trigger: 4+ weeks data ✅ NOW ACTIVE. S37 queue.
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

---

## Key Numbers

Tier | S32 DPOL | S33 DPOL
E0   | 51.1%    | 51.4%
E1   | 44.7%    | 44.8%
E2   | 45.0%    | 45.1%
E3   | 43.4%    | 43.3%
EC   | 46.2%    | 46.1%
B1   | 49.2%    | 49.4%
D1   | 49.7%    | 50.2%
D2   | 44.2%    | 44.5%
I1   | 51.0%    | 51.0%
I2   | 42.6%    | 43.1%
N1   | 52.9%    | 53.0%
SC0  | 50.3%    | 50.5%
SC1  | 44.7%    | 44.7%
SC2  | 49.1%    | 49.7%
SC3  | 48.2%    | 48.6%
SP1  | 50.5%    | 50.4%
SP2  | 45.7%    | 45.7%
OVERALL | 47.6% | 47.7%

S31 baseline: 47.1% on 131,149 matches.
S32 three-pass baseline: 46.7% on 218,317 matches.
S33 DPOL cold baseline: 45.5%. Evolved to 47.7%. Delta: +2.3pp.

17/04 predictions: 120 fixtures, 13 leagues.
Upset acca: Reading, Everton, Sampdoria — ~49/1.
Key disagreements: Everton H (95%), Reading H (100%), Mansfield H (100%).

Weather cache: 89.1% populated (116,755 / 131,149). 14,394 permanent gaps.

---

## Files

File | Status | Notes
edgelab_engine.py | Updated S35 | TIER_DRAW_RATE lookup — verified actual draw rates
edgelab_results_check.py | Updated S34 | Auto-save results CSV, odds in all_results
edgelab_dpol.py | Updated S30 | db param, directional candidate bias
edgelab_runner.py | Updated S32.a | Global guard 3k sample, all params, newest-first seasons
edgelab_db.py | Updated S33 | gary_calls expanded, full logging, migration updated
edgelab_config.py | Updated S32.a | load_params loads all param fields
edgelab_param_evolution.py | Updated S33 | Pass 2b confirmed working
edgelab_gary.py | Updated S33 | ask logs silently, confidence band, ctx.gary_memory fix
edgelab_gary_brain.py | Updated S30 | PatternMemory dataclass
edgelab_gary_context.py | Updated S30 | Pattern memory in match prompt
edgelab_predict.py | Updated S31 | db auto-detect
edgelab_html_generator.py | Updated S36 | Full rebuild — sub-tabs per league and acca, larger font, upset notes auto-load
edgelab_signals.py | Updated S31 | Ground coords 549 teams
edgelab_acca.py | Updated S36 | Upset acca filter — upset_score >= 0.65, chaos filter removed
edgelab_merge.py | Updated S36 | TIER_WHITELIST — 17 proven tiers only merge into history/
edgelab_params.json | Updated S35 | S33 DPOL all 17 tiers — 47.7% overall
edgelab_acca.py | Updated S32 | Mutually exclusive acca pools
edgelab_databot.py | Updated S32 | Harvester write side effect
edgelab_backfill.py | New S29 | Historical fixture population
edgelab_threepass_seed.py | New S28 | Seeds param_profile into params.json
edgelab_weather_wire.py | New S35 | Wires weather_cache.csv into edgelab.db
check_draw_rates.py | New S35 | Verifies TIER_DRAW_RATE against actual dataset
edgelab.db | Live S29 | LOCAL ONLY
harvester_football.db | Updated S34 | 313,999 matches, LOCAL ONLY
param_profile.json | Updated S35 | S33 three-pass results
setup_harvester_tasks.ps1 | New S32 | Task Scheduler 12 tasks
harvester_tasks/run_harvester_football.bat | Updated S33 | Merge step added after harvest

---

## Dataset

609 CSV files, 25 years, 17 proven tiers, 218,317 matches — engine dataset.
Harvester leagues remain in harvester_football.db — isolated by tier whitelist in edgelab_merge.py.
harvester_football.db: 313,999 matches, 121 leagues, 2010-2026 — isolated (intended).
Weather cache: 89.1% populated. edgelab.db: 131,149 fixtures, weather_load wired.
New data sources: international_results_1872_2026.zip, transfermarkt_football_data.zip — downloaded, not integrated.

---

## Brand and Marketing

garyknows.com: live. garypredicts.netlify.app: live — updated S36 with sub-tab layout.
Mailchimp: 6 contacts, free tier. Brevo migration trigger: 400 contacts.
Social: paused. Gary avatar: 7-sec Kling clip exists.
New data sources acquired from Kaggle — referee, attendance, squad value signals now have data.

---

## Periodic Audit

Last done: S35 — full export re-read (all 37 conversations). Next due: S37-38.

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
   INTEGRITY LOG — complete in state file before generating any documents

---

## To Start Session 37

1. Use EDGELAB_SESSION_START_PROMPT.md as opening prompt
2. Upload EDGELAB_BRIEFING_SESSION37_START.md to project knowledge
3. Upload EDGELAB_STATE_S37.md to project knowledge
4. Upload EDGELAB_MASTER_BACKLOG_S36.md to project knowledge
5. Run results check on 17-20 April predictions first
6. Then DataBot team news build
7. Then scoreline logging
