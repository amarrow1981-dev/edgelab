# EdgeLab — Master Backlog
# Single source of truth for every idea, feature, signal, bug, and task
# Built: Session 22 — 08/04/2026
# Updated: Session 33 — 13/04/2026

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
| Score prediction v2 | ✅ | S24 |
| w_score_margin activation | ✅ | S28/S31/S32. Active 13/17 tiers. Dominant signal. |
| Score prediction recalibration | ⏳ | Away goals 1.37 pred vs 1.07 actual. Teacher layer will diagnose. |
| Draw rate prior audit | 🔲 | S34 queue item 5. Check flat vs tier-specific in engine. |
| Codebase refactor | 🔲 | Trigger: draw wired + validated + params confirmed. |

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
| Composite draw gate | ✅ | S26. composite_draw_boost. |
| Wire composite draw signal into engine | ✅ | S26. |
| Seed gridsearch from draw_profile.json | ✅ | S26. |
| DPOL rolling window validation of draw signal | ✅ | S28+S31. DPOL strips draw weights. |
| BTTS/scoreline inconsistency fix | ⏳ | Monitor. |
| w_btts as draw signal | ✅ | CONFIRMED DEAD S28+S31+S32. |
| Stage 2 draw rate strategy | 🅿 | Trigger: three-pass post-match teacher proven on draws. |

### Upset layer
| Item | Status | Notes |
|------|--------|-------|
| Upset score 0–1 | ✅ | Stage 1 only |
| Upset flag | ✅ | Stage 1 |
| Upset flip Stage 2 | 🅿 | Trigger: enough Stage 1 history validated. |

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
| Third full DPOL run — threepass seed | ✅ | S29. REGRESSED -0.10pp. Reverted. |
| DPOL candidate logging | ✅ | S29. |
| get_successful_param_directions — signed direction | ✅ | S30. |
| DPOL reads from candidate log | ✅ | S30. |
| S31 DPOL run — first with logging | ✅ | S31. 47.1% overall. |
| S32 DPOL run — first navigated | ✅ | S32/S33 confirmed. 47.6% overall. 17/17 tiers. |
| S33 DPOL run — second navigated | 🔲 | S34 queue item 4. After weather + three-pass. |
| Three-pass full param evolution | ✅ | S28+S32. |
| Three-pass seed into DPOL | ✅ | S28+S32. |
| Three-pass rerun — 218k dataset | ✅ | S32. 46.7% baseline. |
| Three-pass rebuild — post-match teacher layer | ✅ | S32.a+S33. Pass 2b confirmed working. |
| Three-pass rerun — weather + post-match teacher + unified dataset | 🔲 | S34 queue item 3. |
| Draw gridsearch | ✅ | S24+S26. |
| DPOL boldness tuning | ✅ | Currently small. |
| DPOL upset-focused evolution | 🔲 | Trigger: draw intelligence + signals active. |
| DPOL exploration budget | 🅿 | Trigger: S33 navigated run assessed. |
| Weekly update run | 🔲 | M2. |
| Automated prediction pipeline | 🔲 | Small build. |
| DPOL scheduled overnight runs | 🅿 | Trigger: M3. |

---

## SECTION 3 — FIXTURE INTELLIGENCE DATABASE

| Item | Status | Notes |
|------|--------|-------|
| Database schema | ✅ | S29. Three tables: fixtures, param_versions, dpol_candidate_log. |
| edgelab_db.py | ✅ | S29/S30/S33. gary_calls expanded S33. |
| Historical backfill | ✅ | S29. 131,149 fixtures. |
| DPOL candidate logging wired | ✅ | S29. |
| DPOL reads from candidate log | ✅ | S30. |
| Results loop closed | ✅ | S29. |
| Gary nearest-neighbour lookup | ✅ | S30. PatternMemory. |
| Gary nn in weekly pipeline | ✅ | S31. Auto-detect db. |
| Gary call logging | ✅ | S33. gary_calls table. ask() logs silently. results_check completes. |
| Wire weather_load to fixtures table | 🔲 | S34 queue item 2. After retry completes. |
| Nearest-neighbour spatial indexing | 🔲 | Trigger: codebase refactor. |
| PostgreSQL migration path | 🔲 | Trigger: Gary live, multiple users. |

---

## SECTION 4 — SIGNALS

### Phase 1 — Built, dormant
| Signal | Status | Trigger |
|--------|--------|---------|
| Referee home bias (w_ref_signal) | ✅/🔲 | Phase 1 review |
| Away travel load (w_travel_load) | ✅/🔲 | Phase 1 review |
| Fixture timing disruption (w_timing_signal) | ✅/🔲 | Phase 1 review |
| Motivation gap (w_motivation_gap) | ✅/🔲 | Phase 1 review |

### Phase 2 — Built, wiring in progress
| Signal | Status | Notes |
|--------|--------|-------|
| Weather load | ✅/⏳ | Task Scheduler running as SYSTEM. ~69%. Wire when 95%+. |
| Weather cache retry | ⏳ | 10k rows/night. ~3 nights to 95%. |
| Ground coords — 549 teams | ✅ | S31. |
| Wire weather to fixture DB | 🔲 | S34 queue item 2. |
| expected_goals_total as draw signal | ✅ | S26. |
| Composite draw gate | ✅ | S26. |

### Phase 3 — Discussed / designed
| Signal | Status | Notes |
|--------|--------|-------|
| Injury index | 🚫 | BLOCKED on API-Football |
| Manager sack bounce | 🔲 | Trigger: signals active |
| Underdog / park the bus | 🅿 | Trigger: signals active |
| Post-international break performance | 🔲 | Trigger: signals active |
| Cumulative fixture fatigue | 🔲 | Trigger: signals active |
| Seasonal momentum | 🔲 | Trigger: dataset mature |
| Bogey team bias | 🔲 | Trigger: signals active, dataset mature |
| High/low scoring period | 🔲 | Trigger: signals active |
| DataBot team news extension | 🔲 | S34 queue item 8. Trigger: S33 DPOL proven. |

---

## SECTION 5 — GARY

### Core Gary — built
| Item | Status | Notes |
|------|--------|-------|
| Gary personality / system prompt | ✅ | |
| Gary brain / context builder | ✅ | |
| Form block | ✅ | |
| H2H block | ✅ | |
| Engine output block | ✅ | |
| Match flags | ✅ | |
| World context block | ✅ | |
| Honest gap disclosure | ✅ | |
| Gary CLI / chat mode | ✅ | |
| Gary Upset Picks output | ✅ | |
| PatternMemory dataclass | ✅ | S30. |
| Gary nearest-neighbour pattern memory | ✅ | S30. |
| Gary nn in weekly pipeline | ✅ | S31. |
| Gary upset analysis JSON injection | ✅ | S31. |
| Gary call logging | ✅ | S33. Full field set. gary_vs_engine comparison. |

### Gary — not yet built
| Item | Status | Notes |
|------|--------|-------|
| Gary post-match analysis | 🔲 | M2. S34 queue item 7. |
| Gary signal recommendation | 🔲 | M2. Most important long-term feature. |
| Gary persistent memory | 🔲 | M2. |
| Gary temporal awareness | 🅿 | Trigger: API-Football. |
| Gary general football chat | 🅿 | Trigger: M3. |
| Gary acca picks feature | 🅿 | Trigger: Gary live on site. |
| Gary behavioural addiction detection | 🅿 | Trigger: M3. |

---

## SECTION 6 — PRODUCT / ACCA

| Item | Status | Notes |
|------|--------|-------|
| Acca builder | ✅ | S22. |
| Winner + BTTS acca type | ✅ | S24. |
| Qualifying picks list | ✅ | S24. |
| Public HTML predictions page | ✅ | Tab system, search, qualifying picks. |
| HTML generator — Gary upset injection | ✅ | S31. |
| Acca filter rebuild — mutually exclusive pools | ✅ | S32. value/safety/result distinct. |
| Market vs EdgeLab comparison framework | ✅ | S33. Run every prediction round. |
| Disagreement value analysis | ✅ | S33. Avg 3.40 odds on correct calls. Above break-even. |
| H/A/D disagreement diagnostic | 🔲 | S34 queue item 6. 9 wrong calls from 09/04. |
| Predictions archive rolling ledger | 🔲 | Trigger: 4+ weeks data, stable params. |
| Acca threshold tuning | 🅿 | Trigger: results history sufficient. |
| Automated prediction pipeline | 🔲 | Small build. |
| Long shot acca | 🅿 | Trigger: upset flip Stage 2 validated. |

---

## SECTION 7 — DATA AND INFRASTRUCTURE

| Item | Status | Notes |
|------|--------|-------|
| 609 CSVs, 25 years, 17 tiers, 218,317 matches | ✅ | 48 skipped. |
| DataBot | ✅ | Harvester write side effect active. |
| Weather cache | ⏳ | ~69%. Running as SYSTEM. ~3 nights to 95%. |
| Weather cache retry script | ✅ | S31. edgelab_weather_retry.py. |
| Ground coords — 549 teams | ✅ | S31. |
| Wire weather to fixture DB | 🔲 | S34 queue item 2. |
| edgelab_results_check.py | ✅ | S29+S32+S33. complete_gary_call wired S33. |
| edgelab_param_evolution.py | ✅ | S28+S32+S33. Pass 2b confirmed working. |
| edgelab_merge.py | ✅ | S32. Now automated in football bat (S33). |
| edgelab_harvester.py | ✅ | S31. 11 sports. |
| API harvester — football daily | ✅ | S32. Task Scheduler. |
| API harvester — other sports | ⏳ | League IDs unverified. |
| Automate merge in harvester bat | ✅ | S33. COMPLETE. |
| edgelab_db.py | ✅ | S29/S30/S33. gary_calls fully wired S33. |
| edgelab_gary.py | ✅ | S31+S33. ask() logs silently S33. |
| harvester_tasks/run_harvester_football.bat | ✅ | Updated S33. Merge after harvest. |
| PostgreSQL migration | 🔲 | Trigger: Gary live, multiple users. |
| Data product API licensing | 🅿 | Trigger: database mature, M3 complete. |

### Code gaps — all closed
| Gap | Status | Notes |
|-----|--------|-------|
| runner.py param conversion missing params | ✅ | Fixed S32.a. |
| config.py load_params missing fields | ✅ | Fixed S32.a. |
| Post-match teacher layer not built | ✅ | Built S32.a, confirmed S33. |
| Dataset hash stale | 🔲 | Run save_dataset_hash() after next three-pass. |
| edgelab_db (2).py duplicate in folder | 🔲 | Delete manually. |

---

## SECTION 8 — PREDICTION WORKFLOW

| Item | Status | Notes |
|------|--------|-------|
| Weekly prediction windows defined | ✅ | Thu + Sun |
| Full weekly commands documented | ✅ | 7 steps. |
| HTML generator in weekly workflow | ✅ | S30. |
| Gary pattern memory in weekly pipeline | ✅ | S31. |
| Gary call logging in weekly pipeline | ✅ | S33. Silent. No flag needed. |
| Market comparison in weekly workflow | ✅ | S33. Run after results each round. |
| Automated prediction pipeline | 🔲 | Small build. |

---

## SECTION 9 — MILESTONE 2: FEEDBACK LOOP

| # | Item | Status |
|---|------|--------|
| 1 | Weighted loss function | ✅ |
| 2 | Live results auto-ingestion | ✅ S29 |
| 3 | Gary call logging | ✅ S33 |
| 4 | Gary post-match analysis | 🔲 S34 queue item 7 |
| 5 | Gary signal recommendation | 🔲 |

---

## SECTION 10 — PRODUCT / PLATFORM

| Item | Status | Notes |
|------|--------|-------|
| garyknows.com live | ✅ | |
| Email list building via Mailchimp | ✅ | 6 contacts. Free tier. Brevo at 400. |
| gary@garyknows.com email | ✅ | |
| Public predictions HTML | ✅ | Automated + upset injection + distinct acca pools. |
| Predictions HTML on Netlify | ✅ | garypredicts.netlify.app |
| Gary picks live on site | 🔲 | M3 |
| Paid tier / gating | 🔲 | M3 |
| Social content pipeline | ⏳ | Paused until HTML polished. ~3k TikTok views. |
| Gary avatar video | ✅ | 7-sec Kling clip. |
| Predictions archive rolling ledger | 🔲 | Trigger: 4+ weeks data. |
| Companies House registration | 🔲 | Before public launch. |

---

## SECTION 11 — KNOWN BUGS

| Bug | Status | Notes |
|-----|--------|-------|
| Draw intelligence dormant | ⏳ | DPOL strips. Teacher layer three-pass first. |
| Score prediction away goals overestimated | ⏳ | 1.37 pred vs 1.07 actual. Monitor. |
| BTTS/scoreline inconsistency | ⏳ | Monitor. |
| E2 overconfidence w_form | ⏳ | Watch after three-pass. |
| BTTS overcalling | ⏳ | 60% pred vs 50% actual. Monitor. |
| Nearest-neighbour query full table scan | ⏳ | Acceptable at 218k. Flag for refactor. |
| New DPOL params home win regression | ⏳ | 86.4% to 79.5%. 1 week sample. Track. |
| Other sport harvester league IDs unverified | 🔲 | S34 queue item 9. |
| Dataset hash stale | 🔲 | Run save_dataset_hash() after next three-pass. |
| edgelab_db (2).py duplicate | 🔲 | Delete manually. |
| Weather cache ~69% | ⏳ | Task Scheduler running. ~3 nights. |

---

## SECTION 12 — FUTURE EXPANSION

| Item | Status | Notes |
|------|--------|-------|
| Gary as standalone product | 🅿 | |
| Expand to other sports | 🅿 | Trigger: DPOL proven on football. |
| Multi-sport harvester infrastructure | ✅ | S31+S32. 11 sports. Task Scheduler. |
| Data product API licensing | 🅿 | Trigger: database mature, M3 complete. |
| RNG/fraud detection using DPOL | 🅿 | Trigger: M3 complete, separate evaluation. |
| DPOL as standalone B2B product | 🅿 | Trigger: M3 complete, EdgeLab proven. |

---

## SECTION 13 — RETROSPECTIVE EVOLUTION PHILOSOPHY

| Item | Status | Notes |
|------|--------|-------|
| Draw evolution (three-pass) | ✅ | S25. |
| Three-pass full param evolution | ✅ | S28+S32. |
| Three-pass seed into DPOL | ✅ | S28+S32. |
| Three-pass rebuild — post-match teacher | ✅ | S32.a+S33. Confirmed working. |
| Three-pass rerun — weather + teacher + unified | 🔲 | S34 queue item 3. The definitive run. |
| S32 DPOL navigated run | ✅ | S33 confirmed. 47.6% overall. 17/17 tiers. |
| S33 DPOL navigated run | 🔲 | S34 queue item 4. Second navigated run. |
| DPOL exploration budget | 🅿 | Trigger: S33 navigated run assessed. |
| 4th coordinate param + signal search | 🅿 | Design into three-pass rebuild. |
| Market comparison framework | ✅ | S33. Weekly cadence established. |
| Disagreement value analysis | ✅ | S33. Avg 3.40 odds confirmed second week. |

---

## SECTION 14 — VISION

"We are building the ultimate football analyser and the best football brain in existence.
Everybody measures average accuracy — that is not enough.
We need to analyse what is not average and make it average.
We are not building average. We already do that better than everyone else."

"The end goal is a paid online community with access to EdgeLab data in differing tiers.
EdgeLab is the stats provider. Gary is the AI mate who analyses it for you."

"The edge lives in the non-average: the 100% confidence call that loses, the high-chaos
match that defies the model. That is where the market misprices. That is where the money is."

"The product vision: bookmakers will notice — not because of stake sizes, but because of
consistent edge on non-obvious selections."

"45% from the information we have is more valuable than 56% from the market. The edge is
not in the headline accuracy number. It is in the depth of what you know about each prediction."

"Once the database is large enough and covers enough sports, it becomes a data product in
its own right. API-style access to historical match data across football and 10+ other sports."

"The uncertainty is what we need to map, or at least quantify. The dense areas are where
DPOL is consistently right. The sparse areas are where it has not looked or cannot find
signal. Both are valuable. Never stop at not looked."

---

## AUDIT TRAIL

Source: Sessions 1-33 + full Anthropic export (all 34 conversations, 12/04/2026)
Last updated: Session 33 — 13/04/2026
Next update: Session 34 close (unprompted — as files)
