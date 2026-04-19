# EdgeLab — Master Backlog
# Single source of truth for every idea, feature, signal, bug, and task
# Built: Session 22 — 08/04/2026
# Updated: Session 36 — 17/04/2026

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
| Confidence score 0-1 | ✅ | |
| Predicted scoreline | ✅ | v2 S24: venue-split + H2H blend |
| BTTS flag + probability | ✅ | |
| Dataset hash / integrity check | ✅ | |
| Score prediction v2 | ✅ | S24 |
| w_score_margin activation | ✅ | S28/S31/S32. Active 13/17 tiers. Dominant signal. |
| Score prediction recalibration | ⏳ | Away goals 1.37 pred vs 1.07 actual. Teacher layer diagnosing. |
| Draw rate prior audit | ✅ | S34. Confirmed flat 0.26. Fixed to tier-specific TIER_DRAW_RATE lookup. |
| TIER_DRAW_RATE verification | ✅ | S35. Verified against actual dataset. All 17 tiers updated. |
| Codebase refactor | 🔲 | Trigger: draw wired + validated + params confirmed. |
| edgelab_merge.py tier whitelist | ✅ | S36. TIER_WHITELIST added. 17 proven tiers only. 214,968 rows blocked. |

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
| Draw intelligence confirmed in teacher layer | ✅ | S35. w_draw_odds, w_h2h_draw, w_xg_draw, composite_draw_boost all confirmed for D outcomes across multiple tiers. |

### Upset layer
| Item | Status | Notes |
|------|--------|-------|
| Upset score 0-1 | ✅ | Stage 1 only |
| Upset flag | ✅ | Stage 1 |
| Upset acca filter fix | ✅ | S36. Chaos filter removed. upset_score >= 0.65 threshold. Now working. |
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
| S33 DPOL run — second navigated | ✅ | S35 confirmed. 47.7% overall. 17/17 tiers. BEST EVER. |
| Three-pass full param evolution | ✅ | S28+S32. |
| Three-pass seed into DPOL | ✅ | S28+S32. |
| Three-pass rerun — 218k dataset | ✅ | S32. 46.7% baseline. |
| Three-pass rebuild — post-match teacher layer | ✅ | S32.a+S33. Pass 2b confirmed working. |
| Three-pass rerun — weather + post-match teacher + unified dataset | ✅ | S35. First definitive run. 10 tiers with combination gains. |
| S34 DPOL run — third navigated | 🔲 | After outcome-specific evolution. |
| Draw gridsearch | ✅ | S24+S26. |
| DPOL boldness tuning | ✅ | Currently small. |
| DPOL upset-focused evolution | 🔲 | Trigger: draw intelligence + signals active. |
| DPOL exploration budget | 🅿 | Trigger: S34 navigated run assessed. |
| Outcome-specific DPOL evolution | 🔲 | Separate param optimisation per H/D/A. NOW ACTIVE — triggers met. Build sequence: variable neighbourhood first, then this, then param-to-result memory. S37 queue item 7. |
| Scoreline-specific DPOL evolution | 🔲 | Separate from H/D/A. Start logging now, evolve later. Trigger: outcome-specific DPOL proven. Logging starts S37. |
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
| Wire weather_load to fixtures table | ✅ | S35. edgelab_weather_wire.py. 116,755 fixtures updated. |
| Scoreline logging — predicted vs actual | 🔲 | S37 queue item 3. Small build. Log now, evolve later. |
| Match-level param-to-result memory | 🅿 | Extend candidate log to map param combos to actual results. Feeds score prediction. Trigger: fixture DB mature, teacher layer proven. |
| Nearest-neighbour spatial indexing | 🔲 | Trigger: codebase refactor. |
| PostgreSQL migration path | 🔲 | Trigger: Gary live, multiple users. |

---

## SECTION 4 — SIGNALS

### Phase 1 — Built, dormant
| Signal | Status | Trigger |
|--------|--------|---------|
| Referee home bias (w_ref_signal) | ✅/🔲 | Phase 1 review. Data source confirmed: Transfermarkt. |
| Away travel load (w_travel_load) | ✅/🔲 | Phase 1 review |
| Fixture timing disruption (w_timing_signal) | ✅/🔲 | Phase 1 review |
| Motivation gap (w_motivation_gap) | ✅/🔲 | Phase 1 review |

### Phase 2 — Built, wired
| Signal | Status | Notes |
|--------|--------|-------|
| Weather load | ✅ | S35. Wired to fixture DB. 89.1% coverage. |
| Weather cache retry | ✅ | Running nightly. Filling remaining 10.9% gaps. |
| Ground coords — 549 teams | ✅ | S31. |
| Wire weather to fixture DB | ✅ | S35. edgelab_weather_wire.py. |
| expected_goals_total as draw signal | ✅ | S26. |
| Composite draw gate | ✅ | S26. |

### Phase 3 — Discussed / designed
| Signal | Status | Notes |
|--------|--------|-------|
| Injury index | 🚫 | BLOCKED on API-Football. Transfermarkt dataset partially addresses this. |
| Manager sack bounce | 🔲 | Trigger: signals active |
| Post-international break fatigue | 🔲 | Trigger: signals active |
| Referee bias signal | 🔲 | Trigger: signals active. Data: Transfermarkt confirmed. |
| Attendance signal | 🔲 | Trigger: signals active. Data: Transfermarkt confirmed. |
| Squad value differential | 🔲 | Trigger: signals active. Data: Transfermarkt confirmed. |
| Bogey team bias | 🔲 | Trigger: signals active, dataset mature. |
| Underdog effect | 🔲 | Trigger: signals active. |
| Cumulative fixture fatigue | 🔲 | Trigger: signals active. |
| Seasonal momentum | 🔲 | Trigger: dataset mature. |
| High/low scoring period investigation | 🔲 | Trigger: signals active. |

---

## SECTION 5 — GARY

| Item | Status | Notes |
|------|--------|-------|
| Gary core engine call | ✅ | |
| Gary context builder | ✅ | S30. |
| Gary pattern memory (nearest-neighbour) | ✅ | S30. PatternMemory dataclass. |
| Gary in weekly workflow | ✅ | S31. |
| Gary call logging | ✅ | S33. |
| Gary confidence band extraction | ✅ | S33. |
| Gary vs engine tracking | ✅ | S33. gary_vs_engine field. |
| Gary team news (DataBot) | 🔲 | NOW UNBLOCKED. S37 queue item 2. |
| Gary post-match analysis | 🔲 | S37 queue item 6. M2. |
| Gary signal recommendation | 🔲 | M2. |
| Gary historical knowledge layer | 🅿 | Trigger: Gary M2 complete. |
| Gary temporal awareness | 🅿 | Trigger: API-Football connected. |
| Gary general football chat | 🅿 | Trigger: M2/M3. |
| Gary persistent memory | 🅿 | Trigger: M2/M3. |
| Gary avatar HeyGen | 🅿 | Trigger: M3. |
| Gary onboarding, accent, addiction detection | 🅿 | Trigger: M3. |

---

## SECTION 6 — HARVESTER & DATA PIPELINE

| Item | Status | Notes |
|------|--------|-------|
| Multi-sport harvester | ✅ | S31+S32. 11 sports. |
| Task Scheduler — 12 tasks as SYSTEM | ✅ | S32+S33. |
| Football harvester — 121 leagues | ✅ | S34. 313,999 matches. |
| Merge step in football bat | ✅ | S33. Runs after harvest. |
| Merge tier whitelist | ✅ | S36. 17 proven tiers only. 214,968 rows blocked. |
| Other sport harvester league IDs | 🔲 | S37 queue item (deferred). Unverified. |
| South America harvester expansion | 🅿 | Trigger: DB mature, football proven. |
| API-Football expiry May 2026 | ⏳ | Schedule renewal or migration before expiry. |

---

## SECTION 7 — WEATHER

| Item | Status | Notes |
|------|--------|-------|
| Open-Meteo weather fetch | ✅ | S30. |
| Weather cache CSV | ✅ | 131,149 rows. 89.1% populated. |
| Ground coords — 549 teams | ✅ | S31+S32. |
| Weather retry script | ✅ | S32. Nightly Task Scheduler. |
| Wire weather to fixture DB | ✅ | S35. edgelab_weather_wire.py. |
| Weather cache permanent gaps | ⏳ | 14,394 gaps. Team name mismatches + pre-2001. Acceptable. |

---

## SECTION 8 — WORKFLOW & TOOLING

| Item | Status | Notes |
|------|--------|-------|
| Weekly prediction workflow | ✅ | 7-step. Documented in state file. |
| edgelab_databot.py | ✅ | Fixtures + odds. Harvester side effect. |
| edgelab_predict.py | ✅ | Full pipeline. |
| edgelab_acca.py | ✅ | S36. Upset filter fixed. 6 acca types. |
| edgelab_html_generator.py | ✅ | S36. Full rebuild. Sub-tabs per league + acca. Larger font. Upset notes auto-load. |
| edgelab_results_check.py | ✅ | S34. Auto-save CSV. |
| edgelab_upset_picks.py | ✅ | |
| edgelab_market_baseline.py | ✅ | S33. |
| Market comparison in weekly workflow | ✅ | S33. Run after results each round. |
| results_check auto-save in workflow | ✅ | S34. No extra step — fires automatically. |
| Predictions archive rolling ledger | 🔲 | S37 queue item 4. Trigger met: 4+ weeks data. |
| BTTS decorrelation review | 🔲 | S37 queue item 5. max_same_tier too restrictive for BTTS. |
| Automated prediction pipeline | 🔲 | Small build. |

---

## SECTION 9 — MILESTONE 2: FEEDBACK LOOP

| # | Item | Status |
|---|------|--------|
| 1 | Weighted loss function | ✅ |
| 2 | Live results auto-ingestion | ✅ S29 |
| 3 | Gary call logging | ✅ S33 |
| 4 | Gary post-match analysis | 🔲 S37 queue item 6 |
| 5 | Gary signal recommendation | 🔲 |

---

## SECTION 10 — PRODUCT / PLATFORM

| Item | Status | Notes |
|------|--------|-------|
| garyknows.com live | ✅ | |
| Email list building via Mailchimp | ✅ | 6 contacts. Free tier. Brevo at 400. |
| gary@garyknows.com email | ✅ | |
| Public predictions HTML | ✅ | S36. Sub-tabs per league + acca. Larger font. Upset notes. |
| Predictions HTML on Netlify | ✅ | garypredicts.netlify.app. Updated S36. |
| Gary picks live on site | 🔲 | M3 |
| Paid tier / gating | 🔲 | M3 |
| Social content pipeline | ⏳ | Paused until HTML polished. HTML now polished. ~3k TikTok views. |
| Gary avatar video | ✅ | 7-sec Kling clip. |
| Predictions archive rolling ledger | 🔲 | S37 queue item 4. Trigger met. |
| Companies House registration | 🔲 | Before public launch. |
| Cowork setup | 🔲 | Trigger: S35 setup complete. |

---

## SECTION 11 — KNOWN BUGS

| Bug | Status | Notes |
|-----|--------|-------|
| Draw intelligence dormant | ⏳ | DPOL strips. Confirmed in teacher layer. Outcome-specific evolution next. |
| Score prediction away goals overestimated | ⏳ | 1.37 pred vs 1.07 actual. Monitor. |
| BTTS/scoreline inconsistency | ⏳ | Monitor. |
| E2 overconfidence w_form | ⏳ | Watch after next three-pass. |
| BTTS overcalling | ⏳ | 60% pred vs 50% actual. Monitor. |
| Nearest-neighbour single-digit matches at scale | ⏳ | Feature space too restrictive. Fix at refactor. |
| New DPOL params home win regression | ⏳ | Monitor over 4+ weeks with S33 params. |
| Other sport harvester league IDs unverified | 🔲 | Queue item, deferred. |
| Dataset hash stale | 🔲 | Run save_dataset_hash() after dataset changes. |
| Weather cache 10.9% null | ⏳ | Permanent gaps. Acceptable at this coverage. |
| BTTS high-confidence picks excluded by decorrelation | 🔲 | S37 queue item 5. Aldershot 92% not appearing. max_same_tier review. |
| MED picks outperforming HIGH two consecutive weeks | ⏳ | Track 3-4 more rounds. Investigate confidence calibration if pattern holds. |

---

## SECTION 12 — FUTURE EXPANSION

| Item | Status | Notes |
|------|--------|-------|
| Gary as standalone product | 🅿 | |
| Expand to other sports | 🅿 | Trigger: DPOL proven on football. |
| Multi-sport harvester infrastructure | ✅ | S31+S32. 11 sports. Task Scheduler. |
| South America harvester expansion | 🅿 | Trigger: DB mature, football proven. |
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
| Three-pass rerun — weather + teacher + unified | ✅ | S35. First definitive run. 10 tiers with gains. |
| S32 DPOL navigated run | ✅ | S33 confirmed. 47.6% overall. 17/17 tiers. |
| S33 DPOL navigated run | ✅ | S35 confirmed. 47.7% overall. 17/17 tiers. BEST EVER. |
| S34 DPOL navigated run | 🔲 | After outcome-specific evolution. |
| DPOL exploration budget | 🅿 | Trigger: S34 navigated run assessed. |
| Outcome-specific DPOL evolution | 🔲 | Separate H/D/A param profiles. NOW ACTIVE — triggers met. Build sequence: variable neighbourhood → outcome-specific → param-to-result memory. S37 queue item 7. |
| Scoreline-specific DPOL evolution | 🔲 | Separate from H/D/A. Start logging now. Trigger: outcome-specific DPOL proven. S37 queue item 3 (logging only). |
| Match-level param-to-result memory | 🅿 | Extend candidate log to actual result fingerprints. Trigger: fixture DB mature, teacher layer proven. |
| Variable similarity neighbourhood | 🅿 | Replace fixed top-N with threshold-based similarity. Trigger: codebase refactor, fixture DB mature. |
| Market comparison framework | ✅ | S33. Weekly cadence established. |
| Disagreement value analysis | ✅ | S33+S34. 09/04: 10/32 correct @ ~3.0 avg odds. |
| 09/04 H/A/D disagreement diagnostic | ✅ | S34. No miscalibration. Draw blind spot confirmed. |
| Fixture-specific prediction layer | 🅿 | Two-stage: general distribution + fixture fingerprint. Trigger: outcome-specific evolution proven. |
| Density map exploration budget | 🅿 | DPOL needs explicit sparse region exploration. Trigger: S34 navigated run assessed. |

---

## SECTION 14 — NEW ARCHITECTURAL IDEAS (S35+S36)

| Item | Status | Notes |
|------|--------|-------|
| Fixture-specific prediction layer | 🅿 | Two-stage prediction. Stage 1: DPOL general distribution. Stage 2: specific fixture fingerprint. Not a hit rate — a density map. Strong vs weak candidates kept distinct, not averaged. Trigger: outcome-specific evolution proven. |
| Density map exploration budget | 🅿 | DPOL directional bias drives into dense clusters. Sparse regions (uncertain games) need explicit exploration. The non-average games live in sparse regions — that's where the edge is. Trigger: S34 navigated run assessed. |
| Scoreline-specific DPOL evolution | 🔲 | Separate evolution surface — scoreline patterns not just H/D/A. Start logging predicted vs actual scoreline NOW. Map builds passively. Evolve when outcome-specific proven. NOT about predicting scores accurately — about building the param-to-scoreline map over time. S37 queue item 3 (logging only). |

---

## SECTION 15 — DATA SOURCES

| Source | Status | Notes |
|--------|--------|-------|
| football-data.co.uk CSVs | ✅ | 609 files, 25 years, 17 tiers, 218,317 matches. |
| API-Football Pro | ✅ | Active until May 2026. 7,500 calls/day. Predictions + results. |
| Open-Meteo weather | ✅ | 89.1% coverage. Running nightly. |
| Kaggle: International results 1872-2026 | 🔲 | Downloaded S35. CC0. 49,016 matches. Monthly updates. Trigger: Gary M2 complete. |
| Kaggle: Transfermarkt Football Data | 🔲 | Downloaded S35. CC0. 80k+ games, referee, attendance, lineups, appearances, transfers. Weekly updates. Commercial ToS verify before launch. Trigger: signals active. |

---

## SECTION 16 — VISION

"We are building the ultimate football analyser and the best football brain in existence.
Everybody measures average accuracy — that is not enough.
We need to analyse what is not average and make it average.
We are not building average. We already do that better than everyone else."

"The end goal is a paid online community with access to EdgeLab data in differing tiers.
EdgeLab is the stats provider. Gary is the AI mate who analyses it for you."

"The edge lives in the non-average: the 100% confidence call that loses, the high-chaos
match that defies the model. That is where the market misprices. That is where the money is."

"45% from the information we have is more valuable than 56% from the market. The edge is
not in the headline accuracy number. It is in the depth of what you know about each prediction."

"The three ideas that compound each other: variable neighbourhood improves similar match
quality, which improves outcome-specific evolution, which improves param-to-result memory.
Build in that order."

"The uncertainty is what we need to map, or at least quantify. The dense areas are where
DPOL is consistently right. The sparse areas are where it has not looked or cannot find
signal. Both are valuable. Never stop at not looked."

"DPOL is the repeatable framework. Football is the first domain. The architecture is:
define params, define outcome, point at historical data, build the map, navigate it.
Every domain gets its own database built on the same blueprint."

"The scoreline map is not about predicting scores accurately — it's about building
a param-to-scoreline density map that compounds over time. Start logging now."

"MED picks outperforming HIGH two consecutive weeks — the edge may not be in maximum
confidence. Track it. If it holds, the confidence calibration at the top end needs
investigating. The model's certainty and the market's certainty are not the same thing."

---

## AUDIT TRAIL

Source: Sessions 1-36 + full Anthropic export (all 37 conversations, 17/04/2026)
Last updated: Session 36 — 17/04/2026
Next update: Session 37 close (unprompted — as files)
