# EdgeLab — Master Backlog
# Single source of truth for every idea, feature, signal, bug, and task
# Built: Session 22 — 08/04/2026
# Updated: Session 28 — 10/04/2026

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
| w_score_margin activation | ✅ | S28. Seeded 0.1–0.3 across 15 tiers via threepass_seed_s28. |
| Codebase refactor — all .py files | 🔲 | Clean rebuild, same interfaces. Trigger: after draw wired + validated. |

### Draw intelligence
| Item | Status | Notes |
|------|--------|-------|
| Team draw tendency rolling | ✅ | Dormant — weight=0.0 |
| Bookmaker implied draw probability | ✅ | Dormant — weight=0.0 |
| H2H draw rate | ✅ | Dormant — weight=0.0 |
| draw_pull gravity param | ✅ | CONFIRMED DEAD S28. Zero signal via three-pass. Keep at 0.0. |
| dti_draw_lock param | ✅ | CONFIRMED DEAD S28. Zero signal via three-pass. Keep at 999.0. |
| Draw signal validation | ✅ | S25. pred_score_draw: NO SIGNAL. p=0.1876. |
| SCORE_DRAW_NUDGE | ✅ | S25. REMOVED. Not backed by evidence. |
| Draw evolution tool | ✅ | S25. edgelab_draw_evolution.py. Three-pass. |
| Draw evolution results | ✅ | S25. Best combo: 1.347x. draw_profile.json produced. |
| expected_goals_total as draw signal | ✅ | S26. Wired. w_xg_draw param. 1.088x lift. |
| Composite draw gate | ✅ | S26. Wired. composite_draw_boost param. |
| Wire composite draw signal into engine | ✅ | S26 DONE. |
| Seed gridsearch from draw_profile.json | ✅ | S26 DONE. |
| DPOL rolling window validation of draw signal | ✅ | S28. DPOL strips draw weights every run. Core param improvement first. |
| BTTS/scoreline inconsistency fix | ⏳ | Partially improved by score prediction v2. Monitor. |
| w_btts as draw signal | ✅ | CONFIRMED DEAD S28. Zero signal via three-pass. |

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
| Third full DPOL run — threepass seed | ⏳ | S28. Running overnight. Results pending S29. |
| Draw gridsearch — draw-focused objective | ✅ | S24. |
| Draw gridsearch — seeded from draw_profile.json | ✅ | S26. gridsearch_results.json saved. |
| Three-pass full param evolution | ✅ | S28. edgelab_param_evolution.py built and run. param_profile.json saved. |
| Three-pass seed into DPOL | ✅ | S28. edgelab_threepass_seed.py built and run. 15 tiers seeded. |
| Signals-only run post weighted loss | ✅ | S24. All dormant. |
| DPOL boldness tuning | ✅ | Currently 'small' |
| DPOL upset-focused evolution | 🔲 | Trigger: draw intelligence + signals active. |
| Weekly update run | 🔲 | M2. |
| Prediction run | 🔲 | Must be fast. Thu + Sun. |
| Automated prediction pipeline (one command) | 🔲 | Small build. |
| DPOL scheduled overnight runs | 🅿 | Trigger: M3 |

---

## SECTION 3 — SIGNALS

### Phase 1 — Built, dormant
| Signal | Status | Trigger |
|--------|--------|---------|
| Referee home bias (w_ref_signal) | ✅/🔲 | Needs direct activation investigation |
| Away travel load (w_travel_load) | ✅/🔲 | Same |
| Fixture timing disruption (w_timing_signal) | ✅/🔲 | Same |
| Motivation gap (w_motivation_gap) | ✅/🔲 | Same |

### Phase 2 — Built, not wired
| Signal | Status | Notes |
|--------|--------|-------|
| Weather load | ✅/📡 | Cache 93.4% complete. Wire when complete. |
| Weather cache completion | ⏳ | 123,926/132,685. Check S29. |
| Wire weather to DPOL | 🔲 | Trigger: cache complete |
| Missing stadium coords | 🔲 | Bristol Rvs, Oxford, AFC Wimbledon, Crawley, Carlisle |
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
| instinct_dti_thresh / skew_correction_thresh | ✅ | S26 CLARIFIED. Confirmed unused stubs. Review at refactor. |
| Market baseline calculator | ✅ | S24. Confirmed stable S28. Permanent benchmark. |
| H/A breakdown vs market | ✅ | S24 |
| Draw evolution tool | ✅ | S25. Three-pass. edgelab_draw_evolution.py |
| Draw signal validation | ✅ | S25. pred_score_draw: NO SIGNAL. |
| Three-pass full param evolution | ✅ | S28. edgelab_param_evolution.py. w_score_margin dominant signal. |
| draw_pull retest | ✅ | S28. CONFIRMED DEAD. Zero signal individually and in combination. |
| dti_draw_lock retest | ✅ | S28. CONFIRMED DEAD. Zero signal individually and in combination. |
| w_btts retest | ✅ | S28. CONFIRMED DEAD. Zero signal individually and in combination. |
| Retest previously discarded params via three-pass | ✅ | S28. DONE. draw_pull/dti_draw_lock/w_btts all dead. |

---

## SECTION 4 — GARY

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

### Gary — not yet built
| Item | Status | Notes |
|------|--------|-------|
| Gary call logging | 🔲 | M2 |
| Gary post-match analysis | 🔲 | M2 |
| Gary → EdgeLab signal recommendation | 🔲 | M2. Gary analyses misses, identifies patterns, recommends signal changes back to EdgeLab. Closes M2. Most important long-term feature. |
| Team Chaos Index | 🔲 | |
| Signal Performance Ledger | 🔲 | |
| Bogey team system (full) | 🔲 | |
| Gary persistent memory | 🔲 | M2 |
| Gary temporal awareness | 🅿 | Trigger: API-Football |
| Gary general football chat | 🅿 | Trigger: M3 |
| Gary acca picks feature | 🅿 | Trigger: Gary live on site |
| Social comment workflow | 🅿 | Use upset picks + Gary commentary as comments on football pages. Gary calls it before the game, screenshots result after. |
| Gary behavioural addiction detection | 🅿 | Pattern-based only — not blunt warnings. Trigger: M3. |

---

## SECTION 5 — PRODUCT / ACCA

| Item | Status | Notes |
|------|--------|-------|
| Acca builder | ✅ | S22. edgelab_acca.py. |
| Winner + BTTS acca type | ✅ | S24 |
| Qualifying picks list | ✅ | S24 |
| Public HTML predictions page | ✅ | Tab system, search, qualifying picks tab. |
| Public HTML — league names in acca picks | ✅ | S28. Added manually. |
| Public HTML — automate qualifying picks | 🔲 | S29. Wire acca.py output to HTML. Include tier→league name mapping. |
| Automated prediction pipeline (one command) | 🔲 | Small build |
| Gary's Weekly Longshot | 🅿 | Single weekly selection, 8-10 fold, highest upset scores + value edge. Trigger: upset flip Stage 2 validated. |
| Selection builder (on-site) | 🅿 | Trigger: M3. |
| Long shot acca | 🅿 | |
| Double upset acca | 🅿 | Trigger: upset flip Stage 2 validated |

---

## SECTION 6 — DATA & INFRASTRUCTURE

| Item | Status | Notes |
|------|--------|-------|
| 417 CSVs, 25 years, 17 tiers | ✅ | 373 load cleanly. 48 skipped. |
| DataBot | ✅ | |
| Weather cache | ⏳ | 123,926/132,685 (93.4%). Check S29. |
| edgelab_results_check.py | ✅ | Built S20. Not in automatic feedback loop. |
| edgelab_market_baseline.py | ✅ | S24. Confirmed stable S28. Permanent benchmark. |
| edgelab_ha_breakdown.py | ✅ | S24 |
| edgelab_draw_signal_validation.py | ✅ | S25 |
| edgelab_draw_evolution.py | ✅ | S25 |
| edgelab_param_evolution.py | ✅ | S28. Three-pass full param sweep. |
| edgelab_threepass_seed.py | ✅ | S28. Seeds param_profile.json into edgelab_params.json. |
| draw_profile.json | ✅ | S25. |
| gridsearch_results.json | ✅ | S26. |
| param_profile.json | ✅ | S28. Three-pass results for all 17 tiers. |
| Live results auto-ingestion | 🔲 | M2. results_check.py exists but not in automatic loop. |
| API-Football connection | 🔲 | Pro plan active until May 2026 |
| Personal web app | 🅿 | Trigger: M2 running |

---

## SECTION 7 — PREDICTION WORKFLOW

| Item | Status | Notes |
|------|--------|-------|
| Weekly prediction windows defined | ✅ | Thu + Sun |
| Thursday run — weekend fixtures | ✅ | Done S24 |
| Sunday run — midweek fixtures | 🔲 | Deferred. Check if still relevant. |
| Results check after each fixture set | 🔲 | Permanent workflow |
| Gary opinions on key matches | ✅ | Done S24 |
| Full weekly commands documented | ✅ | In briefing + state |
| Automated prediction pipeline (one command) | 🔲 | Small build |
| Workflow enrichment when API-Football live | 🔲 | Trigger: API-Football |

---

## SECTION 8 — MILESTONE 2: FEEDBACK LOOP

| # | Item | Status |
|---|------|--------|
| 1 | Weighted loss function | ✅ |
| 2 | Live results auto-ingestion | 🔲 |
| 3 | Gary call logging | 🔲 |
| 4 | Gary post-match analysis | 🔲 |
| 5 | Gary → EdgeLab signal recommendation | 🔲 |

---

## SECTION 9 — PRODUCT / PLATFORM

| Item | Status | Notes |
|------|--------|-------|
| garyknows.com live | ✅ | |
| Email list building via Mailchimp | ✅ | 6 contacts. → Brevo at 400. |
| gary@garyknows.com email | ✅ | |
| Public predictions HTML | ✅ | iOS fix S28. League names S28. |
| Gary picks live on site | 🔲 | M3 |
| Paid tier / gating | 🔲 | M3 |
| garyknows.com Mailchimp auth | ✅ | Authenticated |
| khaotikk.com Mailchimp auth | ✅ | Confirmed S28 |
| Migrate Mailchimp → Brevo | 🔲 | Trigger: 400 contacts |
| Social content — Gary Upset Picks format | 🔲 | Paused until HTML on Netlify |
| TikTok / Instagram content pipeline | ⏳ | ~3,000 TikTok views. Fresh start 8 April 2026. |
| Gary avatar video — intro clip | ✅ | 7-second Kling clip exists. "Who the hell is Gary?" cut live. |
| Cryptocurrency payment options | 🅿 | Trigger: M3 paid tier |
| Countdown clock on landing page | 🅿 | Add when launch date confirmed. |
| Companies House registration | 🔲 | Before public launch |
| Deploy predictions HTML to Netlify | 🔲 | Share URL not file. Required for iOS tabs to work. |

---

## SECTION 10 — TOOLS & EXTERNAL SERVICES

| Item | Status | Notes |
|------|--------|-------|
| Kling subscription | ✅ | Active. Used for Gary avatar video generation. |
| Perplexity Computer | 🅿 | Trigger: M3 |
| Periodic full context audit | ✅ | Last done S27 (full Anthropic export). Next due ~S32-33. |
| Session start prompt | ✅ | EDGELAB_SESSION_START_PROMPT.md |

---

## SECTION 11 — KNOWN BUGS

| Bug | Status | Notes |
|-----|--------|-------|
| Draw intelligence dormant | ✅ | DPOL strips draw weights. Core param improvement first. Reassess post S29 DPOL. |
| SCORE_DRAW_NUDGE | ✅ | REMOVED S25. |
| E2 overconfidence w_form=0.796 | ⏳ | Monitoring. Threepass may change this. |
| E1 home bias | ✅ | Structurally improved S27. Monitoring. |
| BTTS/scoreline inconsistency | ⏳ | Partially improved by score prediction v2 |
| khaotikk.com Mailchimp auth | ✅ | Confirmed S28 |
| instinct_dti_thresh / skew_correction_thresh | ✅ | CLARIFIED S26. Unused stubs. Review at refactor. |
| Qualifying picks manually maintained in HTML | 🔲 | Automate S29 via edgelab_acca.py |
| Public HTML — iOS tab/search broken | ✅ | Fixed S28. Works only via Netlify URL — not local file. |
| Date labelling — fixtures shown a day early | 🔲 | Workaround: manual +1 day on HTML. Fix at source S29. |
| Market baseline table | ✅ | Confirmed stable S28. S24 numbers = permanent benchmark. |

---

## SECTION 12 — FUTURE EXPANSION

| Item | Status | Notes |
|------|--------|-------|
| Gary as standalone product | 🅿 | |
| Gary integrated into EdgeLab | 🅿 | |
| Most comprehensive football stats website | 🅿 | |
| Expand to other sports | 🅿 | Trigger: DPOL proven on football |
| DPOL applied to non-sports domains | 🅿 | |
| Khaotikk Ltd as holding entity | 🅿 | |

---

## SECTION 12B — RETROSPECTIVE EVOLUTION PHILOSOPHY

| Item | Status | Notes |
|------|--------|-------|
| Draw evolution (three-pass) | ✅ | S25. Proven approach. draw_profile.json produced. |
| Composite draw signal wired | ✅ | S26. engine + DPOL updated. |
| Gridsearch seeded from draw profile | ✅ | S26. 16/17 tiers passed gate. |
| DPOL rolling window validation of draw signal | ✅ | S28. DPOL strips draw weights. Core params first. |
| Three-pass full param evolution | ✅ | S28. edgelab_param_evolution.py. w_score_margin dominant. 7 tiers with combo gains. |
| Three-pass seed into DPOL | ✅ | S28. 15 tiers seeded. Third DPOL overnight. |
| draw_pull / dti_draw_lock / w_btts retest | ✅ | S28. CONFIRMED DEAD. Remove from future candidate lists. |
| Retest previously discarded params via three-pass | ✅ | S28. DONE. All dead. No new candidates identified. |
| Stage 2 draw rate strategy (25-27% band) | 🅿 | Trigger: three-pass proven on draws. |

---

## SECTION 13 — VISION

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

---

## AUDIT TRAIL

Source: Sessions 1-28 + full Anthropic export (all 29 conversations, 10/04/2026)
Last updated: Session 28 — 10/04/2026
Next update: Session 29 close (unprompted — as files)
