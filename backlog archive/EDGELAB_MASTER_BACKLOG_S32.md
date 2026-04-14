# EdgeLab — Master Backlog
# Single source of truth for every idea, feature, signal, bug, and task
# Built: Session 22 — 08/04/2026
# Updated: Session 32 + 32.a — 13/04/2026

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
| w_score_margin activation | ✅ | S28/S31/S32. Active 13/17 tiers. Dominant signal. |
| Score prediction recalibration | ⏳ | Away goals 1.37 pred vs 1.07 actual. Monitor. Post-match teacher will diagnose. |
| Codebase refactor — all .py files | 🔲 | Trigger: draw wired + validated + params confirmed. |

### Draw intelligence
| Item | Status | Notes |
|------|--------|-------|
| Team draw tendency rolling | ✅ | Small weight EC, SC3 only |
| Bookmaker implied draw probability | ✅ | Small weight EC, I2, SC3, SP2 |
| H2H draw rate | ✅ | Small weight EC, SC3 |
| draw_pull gravity param | ✅ | CONFIRMED DEAD S28+S31+S32. Never test again. |
| dti_draw_lock param | ✅ | CONFIRMED DEAD S28+S31+S32. Never test again. |
| Draw signal validation | ✅ | S25. pred_score_draw: NO SIGNAL. |
| SCORE_DRAW_NUDGE | ✅ | S25. REMOVED. |
| Draw evolution tool | ✅ | S25. edgelab_draw_evolution.py. |
| Draw evolution results | ✅ | S25. Best combo: 1.347x. draw_profile.json. |
| expected_goals_total as draw signal | ✅ | S26. w_xg_draw param. 1.088x lift. |
| Composite draw gate | ✅ | S26. composite_draw_boost param. |
| DPOL rolling window validation of draw signal | ✅ | S28+S31. DPOL strips draw weights. |
| BTTS/scoreline inconsistency fix | ⏳ | BTTS overcalling 60% pred vs 50% actual. Monitor. |
| w_btts as draw signal | ✅ | CONFIRMED DEAD S28+S31+S32. |

### Upset layer
| Item | Status | Notes |
|------|--------|-------|
| Upset score 0–1 | ✅ | Stage 1 only |
| Upset flag | ✅ | Stage 1. 57.1% accuracy S32.a results |
| Upset flip Stage 2 | 🅿 | Trigger: Stage 1 history validated |

---

## SECTION 2 — DPOL

| Item | Status | Notes |
|------|--------|-------|
| DPOL core window evolution | ✅ | |
| Global guard | ✅ | S32.a: now uses 3,000-row sample for speed |
| --tier single/all flags | ✅ | |
| --signals-only flag | ✅ | S19 |
| Flat loss function | ✅ | |
| Weighted loss function (draw misses 1.5x) | ✅ | S22 |
| Full re-evolution — weighted loss | ✅ | S24. 46.2% overall. |
| Full re-evolution — post score prediction v2 | ✅ | S27. 46.5% overall. |
| Second full DPOL run — draw seeded | ✅ | S28. 46.8% overall. |
| Third full DPOL run — threepass seed | ✅ | S29. REGRESSED. Root cause: no memory. |
| DPOL candidate logging | ✅ | S29. |
| get_successful_param_directions — signed direction | ✅ | S30. Rebuilt with JOIN. |
| DPOL navigation SQL bug | ✅ | S32.a FIXED. pv.pv.w_form → pv.w_form |
| DPOL reads from candidate log | ✅ | S30. Directional bias. |
| Season order newest-first | ✅ | S32.a FIXED. Was oldest-first. |
| fast_pred_fn — all params (Gap A) | ✅ | S32.a FIXED. 7 params were missing. |
| S31 DPOL run | ✅ | S31. 47.1% overall. +1.8pp. |
| S32 DPOL run — first navigated | ⏳ | In progress at S32.a close. SQL bug fixed mid-run. |
| S33 DPOL run — second navigated | 🔲 | S33 queue item 4. After weather + rebuilt three-pass. |
| Three-pass full param evolution | ✅ | S28. edgelab_param_evolution.py. |
| Three-pass seed into DPOL | ✅ | S28+S32. edgelab_threepass_seed.py. |
| Three-pass rerun — 218k dataset | ✅ | S32. 46.7% baseline. |
| Three-pass rebuild — post-match teacher layer | ✅ | S32.a BUILT. Pass 2b in edgelab_param_evolution.py. |
| Three-pass rerun — weather + teacher + unified | 🔲 | S33 queue item 3. After items 1 and 2. |
| DPOL exploration vs exploitation budget | 🅿 | Trigger: S33 navigated run assessed. |
| Weekly update run | 🔲 | M2. |
| Automated prediction pipeline | 🔲 | Small build. |
| DPOL scheduled overnight runs | 🅿 | Trigger: M3 |

---

## SECTION 3 — FIXTURE INTELLIGENCE DATABASE

| Item | Status | Notes |
|------|--------|-------|
| Database schema design | ✅ | S29. Three tables. |
| edgelab_db.py | ✅ | S32.a. SQL double-prefix bug fixed. |
| Historical backfill | ✅ | S29. 131,149 fixtures. |
| DPOL candidate logging wired | ✅ | S29. |
| DPOL reads from candidate log | ✅ | S30. |
| Results loop closed | ✅ | S29. writes to DB. |
| 09/04 results written to DB | ✅ | S32.a. |
| Gary nearest-neighbour lookup | ✅ | S30. |
| Gary nn in weekly pipeline | ✅ | S31. Auto-detect db. |
| Wire weather_load to fixtures table | 🔲 | S33 queue item 2. After ≥95% coverage. |
| Nearest-neighbour spatial indexing | 🔲 | Trigger: refactor. |
| Discarded param conditional analysis | ✅ | S29. |
| PostgreSQL migration path | 🔲 | Trigger: Gary live, multiple users. |

---

## SECTION 4 — SIGNALS

### Phase 1 — Built, dormant
| Signal | Status | Notes |
|--------|--------|-------|
| Referee home bias (w_ref_signal) | ✅/🔲 | Built. Dormant. Activation investigation needed. |
| Away travel load (w_travel_load) | ✅/🔲 | Built. Dormant. Ground coords available. |
| Fixture timing disruption (w_timing_signal) | ✅/🔲 | Built. Dormant. |
| Motivation gap (w_motivation_gap) | ✅/🔲 | Built. Dormant. Needs live standings data. |

### Phase 2 — Built, wiring in progress
| Signal | Status | Notes |
|--------|--------|-------|
| Weather load | ✅/⏳ | Task Scheduler running as SYSTEM. ~5 days to complete. Wire when ≥95%. |
| Weather cache retry | ⏳ | 61.4% at S32 close. Running. |
| Ground coords — 549 teams | ✅ | S31. |
| Wire weather to fixture DB | 🔲 | S33 queue item 2. |
| expected_goals_total as draw signal | ✅ | S26. w_xg_draw. |
| Composite draw gate | ✅ | S26. |

### Phase 3 — Discussed / designed / to investigate
| Signal | Status | Notes |
|--------|--------|-------|
| Injury index | 🚫 | BLOCKED on API-Football |
| DataBot extension — team news | 🔲 | Trigger: S33 DPOL proven. Pull injuries/suspensions at prediction time. |
| Manager sack bounce | 🔲 | Trigger: signals active + feedback loop |
| Underdog / park the bus | 🅿 | Trigger: signals active |
| Public mood / world sentiment | 🔲 | Needs live data |
| Bogey team bias formalised | 🔲 | Trigger: signals active, dataset mature. In vision since S9. |
| High/low scoring period investigation | 🔲 | Trigger: signals active. Your observation S9. |
| Cumulative fixture fatigue | 🔲 | Trigger: signals active |
| Seasonal momentum | 🔲 | Trigger: dataset mature |
| Crowd/atmosphere proxy | 🔲 | Trigger: attendance data available |
| Post-international break performance | 🔲 | Trigger: signals active |
| Manager tenure effects | 🔲 | Trigger: signals active |
| Score prediction away goals recalibration | ⏳ | Monitor each round. Post-match teacher will diagnose. |

---

## SECTION 5 — GARY

### Core Gary — built
| Item | Status | Notes |
|------|--------|-------|
| Gary personality / system prompt | ✅ | |
| Gary brain / context builder | ✅ | |
| Form, H2H, engine output, match flags blocks | ✅ | |
| Gary CLI / chat mode | ✅ | |
| Gary Upset Picks output | ✅ | |
| PatternMemory dataclass | ✅ | S30. |
| Gary nearest-neighbour pattern memory | ✅ | S30. |
| Gary nn in weekly pipeline | ✅ | S31. Auto-detect. |
| Gary upset analysis JSON injection | ✅ | S31. |

### Gary — not yet built
| Item | Status | Notes |
|------|--------|-------|
| Gary call logging | 🔲 | M2. S33 queue item 5. |
| Gary post-match analysis | 🔲 | M2. S33 queue item 6. |
| Gary → EdgeLab signal recommendation | 🔲 | M2. Closes M2. |
| Gary historical knowledge layer (pre-1993) | 🔲 | Trigger: Gary M2 complete. Sources: RSSSF, football-reference.com. |
| Team Chaos Index | 🔲 | |
| Signal Performance Ledger | 🔲 | |
| Bogey team system (full) | 🔲 | |
| Gary persistent memory | 🔲 | M2 |
| Gary temporal awareness | 🅿 | Trigger: API-Football |
| Gary general football chat | 🅿 | Trigger: M3 |
| Gary acca picks feature | 🅿 | Trigger: Gary live on site |

---

## SECTION 6 — PRODUCT / ACCA

| Item | Status | Notes |
|------|--------|-------|
| Acca builder | ✅ | S22. edgelab_acca.py. |
| Winner + BTTS acca type | ✅ | S24 |
| Qualifying picks list | ✅ | S24 |
| Public HTML predictions page | ✅ | Tab system, search, qualifying picks. |
| HTML generator — Gary upset analysis injection | ✅ | S31. |
| Acca filter rebuild — mutually exclusive pools | ✅ | S32. value > safety > result. |
| First results analysis | ✅ | S32.a. 48.8% result, 84.2% MED band, 56.2% within-1 goal. |
| Acca threshold tuning | 🅿 | Trigger: enough results history. Gary will evaluate. |
| Automated prediction pipeline | 🔲 | Small build |
| Gary's Weekly Longshot | 🅿 | Trigger: upset flip Stage 2 validated. |

---

## SECTION 7 — DATA & INFRASTRUCTURE

| Item | Status | Notes |
|------|--------|-------|
| 609 CSVs, 218,317 matches, 17 tiers | ✅ | S32 merge. 48 skipped. |
| DataBot | ✅ | S32: harvester write side effect |
| Weather cache | ⏳ | 61.4%. Task Scheduler as SYSTEM. |
| Ground coords — 549 teams | ✅ | S31. |
| edgelab_results_check.py | ✅ | S32.a. LEAGUE_MAP bug fixed. Writes to DB + harvester. |
| edgelab_market_baseline.py | ✅ | S24. |
| edgelab_param_evolution.py | ✅ | S32.a. Pass 2b post-match teacher. |
| edgelab_threepass_seed.py | ✅ | S28. |
| edgelab_db.py | ✅ | S32.a. SQL bug fixed. |
| edgelab_runner.py | ✅ | S32.a. Global guard, all params, newest-first. |
| edgelab_config.py | ✅ | S32.a. load_params() complete. |
| edgelab_backfill.py | ✅ | S29. |
| edgelab_html_generator.py | ✅ | S31. |
| edgelab_harvester.py | ✅ | S31. 11 sports. |
| API harvester — football | ✅ | S31. 87,184 matches, 2010-2026. |
| API harvester — daily scheduled | ✅ | S32.a. Task Scheduler as SYSTEM. |
| API harvester — other sports | ⏳ | Registered. League IDs unverified. |
| Unified dataset build | ✅ | S32. 85,632 rows merged. edgelab_merge.py. |
| Task Scheduler — SYSTEM credentials | ✅ | S32.a. All 12 tasks. |
| Automate merge in harvester bat | 🔲 | S33 queue item 7. |
| edgelab.db | ✅ | S29. 131,149 fixtures. LOCAL ONLY. |
| harvester_football.db | ✅ | S31. 87,184 matches. LOCAL ONLY. |
| setup_harvester_tasks.ps1 | ✅ | S32. 12 tasks. |

---

## SECTION 8 — PREDICTION WORKFLOW

| Item | Status | Notes |
|------|--------|-------|
| Weekly prediction windows defined | ✅ | Thu + Sun |
| Results check after each set | ✅ | S29/S32.a. Writes to DB + harvester. |
| Gary opinions on key matches | ✅ | |
| Full weekly commands documented | ✅ | 7 steps. |
| Background harvest documented | ✅ | Task Scheduler as SYSTEM. |
| Results monitoring metrics defined | ✅ | S32.a. 8 metrics tracked. |
| Automated prediction pipeline | 🔲 | Small build |

---

## SECTION 9 — MILESTONE 2: FEEDBACK LOOP

| # | Item | Status |
|---|------|--------|
| 1 | Weighted loss function | ✅ |
| 2 | Live results auto-ingestion | ✅ S29 |
| 3 | Post-match teacher layer | ✅ S32.a |
| 4 | Gary call logging | 🔲 S33 queue item 5 |
| 5 | Gary post-match analysis | 🔲 S33 queue item 6 |
| 6 | Gary → EdgeLab signal recommendation | 🔲 |

---

## SECTION 10 — PRODUCT / PLATFORM

| Item | Status | Notes |
|------|--------|-------|
| garyknows.com live | ✅ | |
| Email list via Mailchimp | ✅ | 6 contacts. → Brevo at 400. |
| gary@garyknows.com email | ✅ | |
| Public predictions HTML | ✅ | Automated + upset injection + distinct acca pools. |
| Predictions HTML on Netlify | ✅ | garypredicts.netlify.app |
| Gary picks live on site | 🔲 | M3 |
| Paid tier / gating | 🔲 | M3 |
| Migrate Mailchimp → Brevo | 🔲 | Trigger: 400 contacts |
| Social content pipeline | 🔲 | Paused |
| Gary avatar video | ✅ | 7-second Kling clip exists. |
| Companies House registration | 🔲 | Before public launch |

---

## SECTION 11 — KNOWN BUGS

| Bug | Status | Notes |
|-----|--------|-------|
| DPOL navigation SQL double-prefix | ✅ | FIXED S32.a. |
| Global guard full dataset eval | ✅ | FIXED S32.a. 3,000-row sample. |
| fast_pred_fn missing 7 params (Gap A) | ✅ | FIXED S32.a. |
| config.py load_params() missing 8 fields (Gap B) | ✅ | FIXED S32.a. |
| Season order oldest-first | ✅ | FIXED S32.a. Now newest-first. |
| results_check LEAGUE_MAP UnboundLocalError | ✅ | FIXED S32.a. |
| Draw intelligence dormant | ⏳ | DPOL strips draw weights. Post-match teacher first. |
| E2 overconfidence w_form=0.932 | ⏳ | S31 DPOL pushed higher. Watch. |
| BTTS/scoreline inconsistency | ⏳ | 60% predicted vs 50% actual. Monitor. |
| Away goals overestimated (1.37 vs 1.07) | ⏳ | Monitor. Post-match teacher will diagnose. |
| Nearest-neighbour full table scan | ⏳ | Acceptable at 218k. Flag for refactor. |
| Weather cache 61.4% | ⏳ | Task Scheduler as SYSTEM. Running. |
| Other sport harvester league IDs unverified | 🔲 | S33 queue item 8. |
| Dataset hash stale | 🔲 | Run save_dataset_hash() after S32 DPOL. |
| edgelab_db (2).py duplicate in folder | 🔲 | Delete manually. |
| Score prediction away goals | ⏳ | v2 fix was partial. Monitor. |

---

## SECTION 12 — FUTURE EXPANSION

| Item | Status | Notes |
|------|--------|-------|
| Gary as standalone product | 🅿 | |
| Gary integrated into EdgeLab | 🅿 | |
| Most comprehensive football stats website | 🅿 | |
| Expand to other sports | 🅿 | Trigger: DPOL proven on football. |
| DPOL applied to non-sports domains | 🅿 | |
| Khaotikk Ltd as holding entity | 🅿 | |
| Repeatable framework — new sports | ✅ | S29. |
| Multi-sport harvester infrastructure | ✅ | S31+S32. 11 sports. Task Scheduler. |
| Data product / API licensing | 🅿 | Trigger: database mature, multiple sports, M3. |

---

## SECTION 13 — RETROSPECTIVE EVOLUTION PHILOSOPHY

| Item | Status | Notes |
|------|--------|-------|
| Draw evolution (three-pass) | ✅ | S25. draw_profile.json. |
| Composite draw signal wired | ✅ | S26. |
| Gridsearch seeded from draw profile | ✅ | S26. |
| DPOL rolling window validation | ✅ | S28. |
| Three-pass full param evolution | ✅ | S28+S32. w_score_margin dominant. |
| Three-pass seed into DPOL | ✅ | S28+S32. 13 tiers seeded S32. |
| draw_pull / dti_draw_lock / w_btts retest | ✅ | DEAD x3. Never test again. |
| Fixture intelligence database | ✅ | S29. 131,149 fixtures. |
| DPOL candidate log | ✅ | S29. |
| get_successful_param_directions — signed | ✅ | S30. |
| DPOL reads from candidate log | ✅ | S30. |
| S31 DPOL run | ✅ | S31. 47.1% overall. |
| S32 DPOL run — first navigated | ⏳ | In progress. SQL bug fixed mid-run. |
| S33 DPOL run — second navigated | 🔲 | S33 queue item 4. |
| Three-pass rebuild — post-match teacher | ✅ | S32.a BUILT. Pass 2b. |
| Three-pass rerun — weather + teacher | 🔲 | S33 queue item 3. |
| DPOL exploration vs exploitation budget | 🅿 | Trigger: S33 run assessed. |
| 4th coordinate — core param + signal | 🅿 | Design into three-pass rebuild. |
| Stage 2 draw rate strategy | 🅿 | Trigger: teacher proven on draws. |
| Seasonal DPOL evolution | 🅿 | Trigger: DB mature, weather wired. |

---

## SECTION 14 — VISION

> "We are building the ultimate football analyser and the best football brain in existence.
> Everybody measures average accuracy — that is not enough.
> We need to analyse what's not average and make it average.
> We are not building average. We already do that better than everyone else."

> "The unconventional signal thesis: everyone else is fishing in the same pond.
> The ceiling is the signals nobody else is looking for.
> Across 218k+ matches, if a signal has any real predictive power, DPOL will find it.
> You don't need to know in advance what the pattern is — you need the data in the
> feature space and let DPOL discover it."

> "We know what we can and can't predict. Our job is to figure out what we can't."

> "The end goal is a paid online community with access to EdgeLab data in differing tiers.
> EdgeLab is the stats provider. Gary is the AI mate who analyses it for you."

> "45% from the information we have is more valuable than 56% from the market. The edge
> isn't in the headline accuracy number. It's in the depth of what you know."

---

## AUDIT TRAIL

Source: Sessions 1-32 + S32.a + full Anthropic export (all 34 conversations, 12/04/2026)
Last updated: Session 32 + 32.a — 13/04/2026
Next update: Session 33 close (unprompted — as files)
