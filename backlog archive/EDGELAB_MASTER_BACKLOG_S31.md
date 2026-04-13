# EdgeLab — Master Backlog
# Single source of truth for every idea, feature, signal, bug, and task
# Built: Session 22 — 08/04/2026
# Updated: Session 31 — 12/04/2026

---

## HOW TO USE THIS DOCUMENT

- Every idea, task, signal, and feature lives here — one place, nothing else
- Status: DONE ✅ | IN PROGRESS ⏳ | QUEUED 🔲 | PARKED 🅿 | NEEDS DATA 📡 | BLOCKED 🚫
- Trigger = what must be true before this item can start
- At every session close, Claude updates this document unprompted — AS A FILE
- Nothing gets built without appearing here first

---

## SECTION 1 — ENGINE CORE

### Prediction fundamentals
| Item | Status | Notes |
|------|--------|-------|
| Form rolling window (last 5) | ✅ | |
| Goal difference rolling window | ✅ | |
| Home advantage | ✅ | |
| DTI (Decision Tension Index) | ✅ | |
| Chaos tier LOW/MED/HIGH | ✅ | |
| Draw margin | ✅ | |
| Coin-flip DTI threshold | ✅ | |
| Confidence score 0–1 | ✅ | |
| Predicted scoreline | ✅ | v2 S24: venue-split + H2H blend |
| BTTS flag + probability | ✅ | |
| Dataset hash / integrity check | ✅ | |
| Score prediction v2 | ✅ | S24. Venue-split + H2H blend. |
| w_score_margin activation | ✅ | S28/S31. Active 15/17 tiers after S31 DPOL. |
| Codebase refactor — all .py files | 🔲 | Trigger: draw wired + validated + params confirmed. |

### Draw intelligence
| Item | Status | Notes |
|------|--------|-------|
| Team draw tendency rolling | ✅ | Small weight in EC, SC3 only |
| Bookmaker implied draw probability | ✅ | Small weight in EC, I2, SC3, SP2 |
| H2H draw rate | ✅ | Small weight in EC, SC3 |
| draw_pull gravity param | ✅ | CONFIRMED DEAD S28+S31. Two independent methods. |
| dti_draw_lock param | ✅ | CONFIRMED DEAD S28+S31. Two independent methods. |
| Draw signal validation | ✅ | S25. pred_score_draw: NO SIGNAL. p=0.1876. |
| SCORE_DRAW_NUDGE | ✅ | S25. REMOVED. Not backed by evidence. |
| Draw evolution tool | ✅ | S25. edgelab_draw_evolution.py. Three-pass. |
| Draw evolution results | ✅ | S25. Best combo: 1.347x. draw_profile.json produced. |
| expected_goals_total as draw signal | ✅ | S26. Wired. w_xg_draw param. 1.088x lift. |
| Composite draw gate | ✅ | S26. Wired. composite_draw_boost param. |
| Wire composite draw signal into engine | ✅ | S26 DONE. |
| Seed gridsearch from draw_profile.json | ✅ | S26 DONE. |
| DPOL rolling window validation of draw signal | ✅ | S28+S31. DPOL strips draw weights every run. |
| BTTS/scoreline inconsistency fix | ⏳ | Partially improved by score prediction v2. Monitor. |
| w_btts as draw signal | ✅ | CONFIRMED DEAD S28+S31. |

### Upset layer
| Item | Status | Notes |
|------|--------|-------|
| Upset score 0–1 | ✅ | Stage 1 only |
| Upset flag | ✅ | Stage 1 |
| Upset flip Stage 2 | 🅿 | Trigger: enough logged Stage 1 history to validate first |

---

## SECTION 2 — DPOL

| Item | Status | Notes |
|------|--------|-------|
| DPOL core window evolution | ✅ | |
| Global guard | ✅ | |
| --tier single/all flags | ✅ | |
| --signals-only flag | ✅ | S19 |
| Flat loss function | ✅ | |
| Weighted loss function (draw misses 1.5x) | ✅ | S22 |
| Full re-evolution — weighted loss | ✅ | S24. 46.2% overall. |
| Full re-evolution — post score prediction v2 + draw changes | ✅ | S27. 46.5% overall. |
| Second full DPOL run — draw seeded | ✅ | S28. 46.8% overall. Draw weights stripped. |
| Third full DPOL run — threepass seed | ✅ | S29. REGRESSED -0.10pp. Reverted. Root cause: no memory. |
| DPOL candidate logging | ✅ | S29. Writes to dpol_candidate_log. |
| get_successful_param_directions — proper signed direction | ✅ | S30. Rebuilt with JOIN + signed delta. |
| DPOL reads from candidate log | ✅ | S30. DPOLManager accepts db. Directional bias. |
| S31 DPOL run — first with logging active | ✅ | S31. 47.1% overall. +1.8pp. All tiers improved. |
| S32 DPOL run — first with navigation active | 🔲 | S32 queue item 6. After weather + unified dataset + three-pass. |
| Three-pass full param evolution | ✅ | S28. edgelab_param_evolution.py. |
| Three-pass seed into DPOL | ✅ | S28. edgelab_threepass_seed.py. 15 tiers seeded. |
| Three-pass rerun — weather + unified dataset | 🔲 | S32 queue item 5. Before navigated DPOL. |
| Draw gridsearch — draw-focused objective | ✅ | S24. |
| Draw gridsearch — seeded from draw_profile.json | ✅ | S26. |
| Signals-only run post weighted loss | ✅ | S24. All dormant. |
| DPOL boldness tuning | ✅ | Currently 'small' |
| DPOL upset-focused evolution | 🔲 | Trigger: draw intelligence + signals active. |
| DPOL exploration vs exploitation budget | 🅿 | Trigger: S32 navigated run assessed. Case 1 behaviour observed. |
| Weekly update run | 🔲 | M2. |
| Automated prediction pipeline (one command) | 🔲 | Small build. |
| DPOL scheduled overnight runs | 🅿 | Trigger: M3 |

---

## SECTION 3 — FIXTURE INTELLIGENCE DATABASE

| Item | Status | Notes |
|------|--------|-------|
| Database schema design | ✅ | S29. Three tables: fixtures, param_versions, dpol_candidate_log. |
| edgelab_db.py | ✅ | S29/S30. get_successful_param_directions rebuilt S30. |
| Historical backfill | ✅ | S29. edgelab_backfill.py. 131,149 fixtures. 17 param versions. |
| DPOL candidate logging wired | ✅ | S29. |
| DPOL reads from candidate log — signed direction | ✅ | S30. |
| Results loop closed | ✅ | S29. edgelab_results_check.py writes post-match completions. |
| Gary nearest-neighbour lookup | ✅ | S30. edgelab_gary_brain.py. PatternMemory dataclass. |
| Gary nn activated in weekly pipeline | ✅ | S31. edgelab_gary.py + edgelab_predict.py. Auto-detect db. |
| Wire weather_load to fixtures table | 🔲 | S32 queue item 2. After retry completes. |
| N1 match count discrepancy | 🔲 | S32 queue item 3. params.json 7,216 vs dataset 6,604. |
| Nearest-neighbour spatial indexing | 🔲 | Trigger: codebase refactor. Full table scan fine at current scale. |
| Discarded param conditional analysis | ✅ | S29. edgelab_backfill.py --check-discarded flag. |
| PostgreSQL migration path | 🔲 | Trigger: Gary live, multiple users. Design already in place. |
| Seasonal/cross-league query layer | 🅿 | Trigger: DB mature, weather wired, signals active. |

---

## SECTION 4 — SIGNALS

### Phase 1 — Built, dormant
| Signal | Status | Trigger |
|--------|--------|---------|
| Referee home bias (w_ref_signal) | ✅/🔲 | Needs direct activation investigation |
| Away travel load (w_travel_load) | ✅/🔲 | Same |
| Fixture timing disruption (w_timing_signal) | ✅/🔲 | Same |
| Motivation gap (w_motivation_gap) | ✅/🔲 | Same |

### Phase 2 — Built, wiring in progress
| Signal | Status | Notes |
|--------|--------|-------|
| Weather load | ✅/⏳ | Retry running. ~98%+ expected. Wire when complete. |
| Weather cache retry | ⏳ | edgelab_weather_retry.py. 98.7% fill rate on rows tested. |
| Ground coords — 549 teams | ✅ | S31. 481→549. All null weather rows now have coords. |
| Wire weather to fixture DB | 🔲 | S32 queue item 2. Re-backfill edgelab.db weather_load. |
| expected_goals_total as draw signal | ✅ | S26 DONE. w_xg_draw param wired. |
| Composite draw gate | ✅ | S26 DONE. |

### Phase 3 — Discussed / designed / discovered
| Signal | Status | Notes |
|--------|--------|-------|
| Injury index | 🚫 | BLOCKED on API-Football |
| Manager sack bounce | 🔲 | Trigger: signals active + feedback loop |
| Underdog / park the bus | 🅿 | Trigger: signals active |
| Public mood / world sentiment | 🔲 | Needs live data |
| E1 home bias investigation | ✅ | S26 DONE. Structurally improved S27. Monitoring. |
| instinct_dti_thresh / skew_correction_thresh | ✅ | S26. Unused stubs. Review at refactor. |
| Market baseline calculator | ✅ | S24. Confirmed stable S28. Permanent benchmark. |
| H/A breakdown vs market | ✅ | S24 |
| Draw evolution tool | ✅ | S25. Three-pass. edgelab_draw_evolution.py |
| Draw signal validation | ✅ | S25. pred_score_draw: NO SIGNAL. |
| Three-pass full param evolution | ✅ | S28. edgelab_param_evolution.py. w_score_margin dominant. |
| draw_pull retest | ✅ | S28+S31. CONFIRMED DEAD both methods. |
| dti_draw_lock retest | ✅ | S28+S31. CONFIRMED DEAD both methods. |
| w_btts retest | ✅ | S28+S31. CONFIRMED DEAD both methods. |

---

## SECTION 5 — GARY

### Core Gary — built
| Item | Status | Notes |
|------|--------|-------|
| Gary personality / system prompt | ✅ | |
| Gary brain / context builder | ✅ | Fixed S24: last8_meetings naming |
| Form block | ✅ | |
| H2H block | ✅ | |
| Engine output block | ✅ | |
| Match flags | ✅ | Fixed S24: weather_load naming |
| World context block | ✅ | |
| Honest gap disclosure | ✅ | |
| Gary CLI / chat mode | ✅ | |
| Gary Upset Picks output | ✅ | |
| PatternMemory dataclass | ✅ | S30. Typed nearest-neighbour output. |
| Gary nearest-neighbour pattern memory | ✅ | S30. db param, _build_pattern_memory(), renders in prompt. |
| Gary nn activated in weekly pipeline | ✅ | S31. Auto-detect edgelab.db in gary.py + predict.py. |
| Gary upset analysis JSON injection | ✅ | S31. html_generator.py full chain wired. |

### Gary — not yet built / not yet wired
| Item | Status | Notes |
|------|--------|-------|
| Gary call logging | 🔲 | M2 |
| Gary post-match analysis | 🔲 | M2 |
| Gary → EdgeLab signal recommendation | 🔲 | M2. Most important long-term feature. Closes M2. |
| Team Chaos Index | 🔲 | |
| Signal Performance Ledger | 🔲 | |
| Bogey team system (full) | 🔲 | |
| Gary persistent memory | 🔲 | M2 |
| Gary temporal awareness | 🅿 | Trigger: API-Football |
| Gary general football chat | 🅿 | Trigger: M3 |
| Gary acca picks feature | 🅿 | Trigger: Gary live on site |
| Social comment workflow | 🅿 | |
| Gary behavioural addiction detection | 🅿 | Trigger: M3. |

---

## SECTION 6 — PRODUCT / ACCA

| Item | Status | Notes |
|------|--------|-------|
| Acca builder | ✅ | S22. edgelab_acca.py. |
| Winner + BTTS acca type | ✅ | S24 |
| Qualifying picks list | ✅ | S24 |
| Public HTML predictions page | ✅ | Tab system, search, qualifying picks tab. |
| Public HTML — league names in acca picks | ✅ | S28. Added manually. |
| Public HTML — automate qualifying picks | ✅ | S30. edgelab_html_generator.py. Full automation. |
| HTML generator — Gary upset analysis injection | ✅ | S31. Companion JSON file. Full chain wired. |
| Acca filter rebuild | 🔲 | S32 queue item 7. result/safety/value not meaningfully distinct. |
| Automated prediction pipeline (one command) | 🔲 | Small build |
| Gary's Weekly Longshot | 🅿 | Trigger: upset flip Stage 2 validated. |
| Selection builder (on-site) | 🅿 | Trigger: M3. |
| Long shot acca | 🅿 | |
| Double upset acca | 🅿 | Trigger: upset flip Stage 2 validated |

---

## SECTION 7 — DATA & INFRASTRUCTURE

| Item | Status | Notes |
|------|--------|-------|
| 417 CSVs, 25 years, 17 tiers | ✅ | 373 load cleanly. 48 skipped. |
| DataBot | ✅ | |
| Weather cache | ⏳ | Retry running. ~98%+ expected on completion. Check S32. |
| Weather cache retry script | ✅ | S31. edgelab_weather_retry.py. 100/100 test confirmed. |
| Ground coords — 549 teams | ✅ | S31. edgelab_signals.py 481→549. |
| Wire weather to fixture DB | 🔲 | S32 queue item 2. Re-backfill edgelab.db weather_load. |
| edgelab_results_check.py | ✅ | Updated S29. Closes learning loop. Writes to DB. |
| edgelab_market_baseline.py | ✅ | S24. Confirmed stable S28. Permanent benchmark. |
| edgelab_ha_breakdown.py | ✅ | S24 |
| edgelab_draw_signal_validation.py | ✅ | S25 |
| edgelab_draw_evolution.py | ✅ | S25 |
| edgelab_param_evolution.py | ✅ | S28. Three-pass full param sweep. |
| edgelab_threepass_seed.py | ✅ | S28. Seeds param_profile.json into edgelab_params.json. |
| edgelab_db.py | ✅ | S29/S30. get_successful_param_directions rebuilt S30. |
| edgelab_backfill.py | ✅ | S29. Historical fixture population. 131,149 fixtures. |
| edgelab_html_generator.py | ✅ | S30/S31. Full predictions HTML + upset injection. |
| edgelab_harvester.py | ✅ | S31. NEW. 11 sports. Newest-first. Checkpoints. |
| API harvester — football first run | ✅ | S31. 87,184 matches, 2010-2026, 443 calls. Isolated. |
| API harvester — daily scheduled run | 🔲 | S32. Windows Task Scheduler. 7,300 calls/day. |
| API harvester — other sports | 🔲 | S32 queue item 8. Verify league IDs first. |
| Unified dataset build | 🔲 | S32 queue item 4. CRITICAL. |
| Merge tool: harvester DB → history/ CSVs | 🔲 | Part of unified dataset build. |
| DataBot write side effect to harvester DB | 🔲 | Part of unified dataset build. No extra calls. |
| results_check write side effect to harvester DB | 🔲 | Part of unified dataset build. No extra calls. |
| Gap analysis: harvester vs CSV dataset | 🔲 | S32. Confirm what's still missing. |
| draw_profile.json | ✅ | S25. |
| gridsearch_results.json | ✅ | S26. |
| param_profile.json | ✅ | S28. Three-pass results for all 17 tiers. |
| edgelab.db | ✅ | S29. 131,149 fixtures. LOCAL ONLY. Not in git. |
| harvester_football.db | ✅ | S31. 87,184 matches. LOCAL ONLY. Not in git. Isolated. |
| .gitignore | ✅ | S29/S31. Excludes edgelab.db, harvester DBs, __pycache__. |
| Personal web app | 🅿 | Trigger: M2 running |
| PostgreSQL migration | 🔲 | Trigger: Gary live with multiple users |
| Data product / API licensing | 🅿 | Trigger: database mature, multiple sports, M3 complete. |

---

## SECTION 8 — PREDICTION WORKFLOW

| Item | Status | Notes |
|------|--------|-------|
| Weekly prediction windows defined | ✅ | Thu + Sun |
| Thursday run — weekend fixtures | ✅ | Done S24 |
| Results check after each fixture set | ✅ | S29. Now writes to DB. |
| Gary opinions on key matches | ✅ | Done S24 |
| Full weekly commands documented | ✅ | Now 7 steps. Upset notes JSON optional. |
| HTML generator in weekly workflow | ✅ | S30. Step 7. |
| Gary pattern memory in weekly workflow | ✅ | S31. Auto-detect edgelab.db. No flag needed. |
| Gary upset JSON in weekly workflow | ✅ | S31. Optional YYYY-MM-DD_upset_notes.json. |
| Background harvest documented | ✅ | S31. Daily harvester command in workflow docs. |
| Automated prediction pipeline (one command) | 🔲 | Small build |
| Workflow enrichment when API-Football live | 🔲 | Trigger: API-Football |

---

## SECTION 9 — MILESTONE 2: FEEDBACK LOOP

| # | Item | Status |
|---|------|--------|
| 1 | Weighted loss function | ✅ |
| 2 | Live results auto-ingestion | ✅ S29 |
| 3 | Gary call logging | 🔲 |
| 4 | Gary post-match analysis | 🔲 |
| 5 | Gary → EdgeLab signal recommendation | 🔲 |

---

## SECTION 10 — PRODUCT / PLATFORM

| Item | Status | Notes |
|------|--------|-------|
| garyknows.com live | ✅ | |
| Email list building via Mailchimp | ✅ | 6 contacts. Free tier. → Brevo at 400. |
| gary@garyknows.com email | ✅ | |
| Public predictions HTML | ✅ | S30/S31. Automated + upset injection. |
| Predictions HTML on Netlify | ✅ | spectacular-licorice-3d5119.netlify.app |
| Rename Netlify predictions site | 🔲 | S32 queue item 9. → gary-picks.netlify.app |
| Gary picks live on site | 🔲 | M3 |
| Paid tier / gating | 🔲 | M3 |
| garyknows.com Mailchimp auth | ✅ | Authenticated |
| khaotikk.com Mailchimp auth | ✅ | Confirmed S28 |
| Migrate Mailchimp → Brevo | 🔲 | Trigger: 400 contacts |
| Social content — Gary Upset Picks format | 🔲 | Paused until HTML polished |
| TikTok / Instagram content pipeline | ⏳ | ~3,000 TikTok views. Fresh start 8 April 2026. |
| Gary avatar video — intro clip | ✅ | 7-second Kling clip exists. |
| Cryptocurrency payment options | 🅿 | Trigger: M3 paid tier |
| Countdown clock on landing page | 🅿 | Add when launch date confirmed. |
| Companies House registration | 🔲 | Before public launch |

---

## SECTION 11 — KNOWN BUGS

| Bug | Status | Notes |
|-----|--------|-------|
| Draw intelligence dormant | ⏳ | DPOL strips draw weights. Core param improvement first. |
| SCORE_DRAW_NUDGE | ✅ | REMOVED S25. |
| E2 overconfidence w_form=0.932 | ⏳ | S31 DPOL pushed higher. Watch. |
| E1 home bias | ✅ | Structurally improved S27. Monitoring. |
| BTTS/scoreline inconsistency | ⏳ | Partially improved by score prediction v2. Monitor. |
| khaotikk.com Mailchimp auth | ✅ | Confirmed S28 |
| instinct_dti_thresh / skew_correction_thresh | ✅ | Unused stubs. Review at refactor. |
| Date labelling — fixtures shown a day early | ✅ | CLOSED S30. Was manual HTML error. |
| Public HTML — iOS tab/search broken | ✅ | Fixed S28. Confirmed working S30. |
| DPOL strips w_score_margin on each run | ✅ | Root cause fixed S29/S30. DB + directional bias prevents this. |
| Nearest-neighbour query full table scan | ⏳ | Acceptable at 131k rows. Flag for refactor. |
| Acca filter — result/safety/value not meaningfully distinct | 🔲 | S32 queue item 7. |
| Gary upset analysis was generic placeholder | ✅ | FIXED S31. JSON injection wired. |
| Gary pattern memory not in weekly pipeline | ✅ | FIXED S31. db auto-detect wired. |
| Weather cache 53% usable coverage | ⏳ | Retry running. ~98%+ expected. |
| Ground coords missing 68 teams | ✅ | FIXED S31. 481→549. |
| N1 match count discrepancy | 🔲 | S32 queue item 3. params.json 7,216 vs dataset 6,604. |
| harvester_football.db isolated | 🔲 | Not feeding engine. Unified dataset build S32. |
| Netlify site name not renamed | 🔲 | S32 queue item 9. |
| Other sport harvester league IDs unverified | 🔲 | Verify before first run S32. |

---

## SECTION 12 — FUTURE EXPANSION

| Item | Status | Notes |
|------|--------|-------|
| Gary as standalone product | 🅿 | |
| Gary integrated into EdgeLab | 🅿 | |
| Most comprehensive football stats website | 🅿 | |
| Expand to other sports | 🅿 | Trigger: DPOL proven on football. Harvester running. |
| DPOL applied to non-sports domains | 🅿 | |
| Khaotikk Ltd as holding entity | 🅿 | |
| Repeatable framework — new sports | ✅ | S29. Architecture designed. Football is proof of concept. |
| Multi-sport harvester infrastructure | ✅ | S31. edgelab_harvester.py. 11 sports. Separate DBs. |
| Data product / API licensing | 🅿 | Trigger: database mature, multiple sports, M3 complete. |

---

## SECTION 13 — RETROSPECTIVE EVOLUTION PHILOSOPHY

| Item | Status | Notes |
|------|--------|-------|
| Draw evolution (three-pass) | ✅ | S25. Proven approach. draw_profile.json produced. |
| Composite draw signal wired | ✅ | S26. engine + DPOL updated. |
| Gridsearch seeded from draw profile | ✅ | S26. 16/17 tiers passed gate. |
| DPOL rolling window validation of draw signal | ✅ | S28. DPOL strips draw weights. Core params first. |
| Three-pass full param evolution | ✅ | S28. edgelab_param_evolution.py. w_score_margin dominant. |
| Three-pass seed into DPOL | ✅ | S28. 15 tiers seeded. |
| draw_pull / dti_draw_lock / w_btts retest | ✅ | S28+S31. CONFIRMED DEAD both methods. |
| Third DPOL run with threepass seed | ✅ | S29. REGRESSED. Reverted. Root cause: no memory. |
| Fixture intelligence database | ✅ | S29. 131,149 fixtures. Map exists. |
| DPOL candidate log | ✅ | S29. Every evaluation stored permanently. |
| get_successful_param_directions — proper signed direction | ✅ | S30. Rebuilt with JOIN. |
| DPOL reads from candidate log | ✅ | S30. Directional bias in _generate_candidates. |
| S31 DPOL run — populates candidate log, new baseline | ✅ | S31. 47.1% overall. All tiers improved. |
| S32 DPOL run — first with navigation active | 🔲 | S32 queue item 6. The real test. |
| Three-pass rerun — weather + unified dataset | 🔲 | S32 queue item 5. Before navigated DPOL. |
| DPOL exploration vs exploitation budget | 🅿 | PARKED S31. Trigger: S32 navigated run assessed. |
| 4th coordinate — simultaneous core param + signal search | 🅿 | PARKED S29. Design into three-pass rebuild. |
| Stage 2 draw rate strategy (25-27% band) | 🅿 | Trigger: three-pass proven on draws. |

---

## SECTION 14 — VISION

> "We are building the ultimate football analyser and the best football brain in existence.
> Everybody measures average accuracy — that is not enough.
> We need to analyse what's not average and make it average.
> We are not building average. We already do that better than everyone else."

> "The end goal is a paid online community with access to EdgeLab data in differing tiers.
> EdgeLab is the stats provider. Gary is the AI mate who analyses it for you."

> "The edge lives in the non-average: the 100% confidence call that loses, the high-chaos
> match that defies the model. That is where the market misprices. That is where the money is."

> "The product vision: bookmakers will notice — not because of stake sizes, but because of
> consistent edge on non-obvious selections. Safe calls build the authority and the track record.
> Upset calls are where the money is. Gary communicates both in plain English. When the upset
> layer, travel signal, motivation gap, and draw intelligence fire together — Gary calling a 3/1,
> a 5/1 and a 7/1 in the same acca with conviction behind each one is a 100/1+ ticket that
> isn't a punt. It's a position."

> "45% from the information we have is more valuable than 56% from the market. The edge isn't
> in the headline accuracy number. It's in the depth of what you know about each prediction."

> "Once the database is large enough and covers enough sports, it becomes a data product in
> its own right. API-style access to historical match data across football and 10+ other sports.
> A separate revenue stream entirely — data licensing, developer access tiers. We would be
> building the thing we are currently paying for."

---

## AUDIT TRAIL

Source: Sessions 1-31 + full Anthropic export (all 29 conversations, 10/04/2026)
Last updated: Session 31 — 12/04/2026
Next update: Session 32 close (unprompted — as files)
