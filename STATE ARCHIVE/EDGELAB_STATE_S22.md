# EDGELAB — Claude State File S22
# For Claude's use at session start. Read this alongside the briefing doc.
# Generated: 08/04/2026 pre-session

## LAST SESSION ENDED
Session 21. Weighted loss function built. DPOL re-evolution started. Site fixed.
This pre-session conversation (not a full session) added:
- Gary acca picks idea (parked — product feature, not yet built)
- Session continuity protocol finalised (two-doc close, session start handshake)
- Honesty protocol confirmed after S21 lie incident — never cover, never soften

## CURRENT STATUS AT SESSION START

### DPOL Run
STATUS: IN PROGRESS as of 08:31 08/04/2026
- Visible in VS Code terminal processing Tier I1, Round 100+
- params.json last modified 08:21 — partially written during run
- DO NOT interrupt. Await completion. Upload params.json when done.
- First priority of S22 is checking whether this run completed.

### Weather Cache
STATUS: INCOMPLETE — ~51,000 rows of 132,685
- Do not wire into DPOL yet
- Check row count at session start: pd.read_csv('weather_cache.csv') → len()

### Website
STATUS: LIVE AND WORKING
- Form wired to Mailchimp (fixed S21 — was fake since S19, Claude's error)
- FNAME field active, welcome automation active
- Sender email broken: Gary@khaotikk.com (temp). gary@garyknows.com blocked.
- Google Workspace verification incomplete — fix S22 queue item 3

### Social
STATUS: Fresh start 8 April 2026
- ~3,000 TikTok views, no verified signups before form fix
- Andrew posting today to generate leads
- Lost signups post still needed (queue item 4)

## SESSION START HANDSHAKE — SAY THIS FIRST
"Last session ended with DPOL weighted loss run in progress and the two-document
session protocol agreed. First thing: has the DPOL run finished? Do you have a
new params.json to upload?"

## S22 QUEUE — IN ORDER, DO NOT SKIP
1. DPOL run status + params.json upload (BLOCKER — check first)
2. Weather cache row count check (quick — one command)
3. Fix gary@garyknows.com email
4. Lost signups social post
5. Duplicate pick warning in acca builder
6. Gary's Upset Picks output (screenshot-ready)

## PARKED IDEAS — DO NOT BUILD WITHOUT FLAGGING
- Gary acca picks (product feature) — Gary builds accas, full pick list shown,
  selection builder site-wide. Not a bet builder. Reintroduce when Gary is live on site.
- Social comment workflow — Gary as mysterious commenter
- Underdog effect signal — test when signals active
- HeyGen avatar — Andrew experimenting

## KEY NUMBERS TO REMEMBER
- Engine overall: 45.9% (flat loss). High conf: 52.9%. Market baseline E0: ~49%
- Signals: ALL DORMANT (0.0 weights)
- Draw calls: 4 from 199 predictions (2%). Real-world: ~26%. Broken until weighted loss reevolution complete.
- Weather cache: 51k/132,685 rows
- Mailchimp: Gary Knows audience. Free tier limit 500 contacts → migrate to Brevo at 400.
- Dataset hash: 580b0f3a1667

## KNOWN ISSUES — ACTIVE
- Draw floor (2% vs 26% real world) — awaiting weighted loss re-evolution
- E2 overconfidence — w_form=0.898, w_gd=0.533. Should self-correct in new run.
- E1 home bias — investigate S22+
- BTTS/scoreline inconsistency — Sevilla vs Atletico case. Not yet fixed.
- Sender email broken — gary@garyknows.com blocked
- Duplicate acca picks — no cross-type warning

## MILESTONE STATUS
- M1: COMPLETE
- M2: IN PROGRESS. Item 1 (weighted loss) done. Items 2-5 not started.
- M3: FUTURE. Not until M2 feedback loop running and accuracy trending up.

## CLAUDE BEHAVIOUR RULES (non-negotiable)
- Never lie. Never cover. If uncertain, say so explicitly.
- One thing at a time. Andrew has ADHD — no multi-threading tasks.
- Rebrief from project knowledge every 8 substantive exchanges (silently).
- Evaluate ideas, don't validate them. Push back on timing when needed.
- Session close checklist is mandatory — all 8 items, unprompted.
- Generate BOTH documents at close (briefing doc + new state file).

## FILES CHANGED THIS PSEUDO-SESSION (pre-S22 chat)
None. Ideas only. No code written.

## GIT STATUS
No new commit needed for this conversation — no code changes.
Last commit message suggestion from S21: not recorded — check with Andrew.
