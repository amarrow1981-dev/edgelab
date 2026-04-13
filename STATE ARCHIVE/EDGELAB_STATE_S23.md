# EDGELAB — Claude State File S23
# For Claude's use at session start. Read alongside briefing doc and master backlog.
# Generated: Session 22 close — 08/04/2026

## LAST SESSION ENDED
Session 22. Full project audit. Weighted loss built. Master backlog created from
all 24 conversations + codebase. Email fixed. Duplicate acca warning built.
Gary Upset Picks built. DPOL weighted loss run started at session close.

## SESSION START HANDSHAKE — SAY THIS FIRST
"Last session ended with the weighted loss DPOL run in progress. First thing:
has the run finished? Do you have a new params.json to upload?"

## CURRENT STATUS

### DPOL Run
STATUS: IN PROGRESS at session close 08/04/2026
- Weighted loss function active (draw misses 1.5x penalty)
- First priority S23: check if complete, upload params.json
- Key questions when complete:
  * Did draw intelligence activate? (draw_pull, w_draw_odds, w_draw_tendency > 0)
  * Did draw calls increase from 2%?
  * Did E2 w_form drop from 0.94?

### Weather Cache
STATUS: RUNNING — 51,000/132,685 rows
- Bot restarted end of S22
- Do not wire to DPOL until 132,685 rows complete

### Website / Email
STATUS: FULLY WORKING
- gary@garyknows.com — created, signed in ✅
- Mailchimp sender: gary@garyknows.com ✅
- Welcome automation: active ✅
- khaotikk.com Mailchimp auth: validating (DNS added S22, up to 48hrs)

### Master Backlog
STATUS: NEW — built S22 from all 24 conversations + codebase
- File: EDGELAB_MASTER_BACKLOG.md
- Must be uploaded to project knowledge at S23 start
- Updated at every session close alongside briefing doc

## S23 QUEUE — IN ORDER

1. DPOL weighted loss results + params.json upload (BLOCKER)
2. Re-run draw gridsearch
3. Signals-only DPOL run
4. Check weather cache row count
5. Check khaotikk.com Mailchimp auth
6. Clarify instinct_dti_thresh / skew_correction_thresh
7. E1 home bias investigation

## KEY NUMBERS
- Engine overall: 46.1% (flat loss weighted run). High conf: 52.9%. Market baseline E0: ~49%
- Signals: ALL DORMANT (0.0 weights)
- Draw calls: 2% vs real-world ~26% — weighted loss should fix
- Weather cache: 51k/132,685 rows
- Mailchimp: Gary Knows audience. Migrate to Brevo at 400 contacts.
- Dataset hash: 580b0f3a1667
- API-Football Pro plan: active until May 2026 — schedule connection before expiry

## KNOWN ISSUES — ACTIVE
- Draw floor 2% vs 26% — weighted loss run in progress
- E2 overconfidence w_form=0.94 — monitor after run
- E1 home bias — investigate S23
- BTTS/scoreline inconsistency — Sevilla vs Atletico — not fixed
- khaotikk.com Mailchimp auth — validating
- instinct_dti_thresh / skew_correction_thresh — purpose unclear, clarify S23

## MILESTONE STATUS
- M1: COMPLETE
- M2: IN PROGRESS. Weighted loss done. Items 2-5 not started.
- M3: FUTURE.

## FILES CHANGED S22
- edgelab_dpol.py — weighted loss function
- edgelab_acca.py — duplicate pick warning
- edgelab_upset_picks.py — NEW
- EDGELAB_MASTER_BACKLOG.md — NEW

## GIT COMMIT MESSAGE S22
```
S22: weighted loss function, upset picks, acca duplicate warning, master backlog, email fixed

- edgelab_dpol.py: weighted loss in _evaluate_params (draw misses 1.5x penalty)
- edgelab_acca.py: duplicate pick warning across acca types
- edgelab_upset_picks.py: new — Gary upset picks, screenshot-ready output
- EDGELAB_MASTER_BACKLOG.md: new — full project backlog from codebase + all 24 conversations
- gary@garyknows.com: Google Workspace user created, Mailchimp sender updated, automation live
```

## CLAUDE BEHAVIOUR RULES (non-negotiable)
- Never lie. Never cover. If uncertain, say so explicitly.
- One thing at a time. Andrew has ADHD.
- Rebrief from project knowledge every 8 substantive exchanges. NO EXCEPTIONS.
- Evaluate ideas, don't validate them.
- Session close checklist mandatory — all 8 items, unprompted.
- Generate ALL THREE documents at close: briefing doc + state file + master backlog.
- Andrew is watching. Earn the trust back through consistent execution.

## PARKED IDEAS — DO NOT BUILD WITHOUT FLAGGING
- Gary acca picks (product feature) — trigger: Gary live on site
- Social comment workflow — trigger: S23 content push
- Underdog effect signal — trigger: signals active
- HeyGen avatar — Andrew's call
- Upset flip Stage 2 — trigger: Stage 1 history validated
- API-Football connection — schedule before May 2026 expiry
- Personal web app (Andrew's dashboard) — trigger: M2 running
- Gary app iOS/Android — trigger: M3
- Push notifications / WhatsApp-style interface — trigger: M3
- FaceTime Gary — trigger: AI video avatar available
- Skool platform community — trigger: M3
- Long shot acca / double upset acca — trigger: upset flip Stage 2 validated
- Expand to other sports — trigger: DPOL proven on football
