# EdgeLab — Master Backlog
# Single source of truth for every idea, feature, signal, bug, and task
# Built: Session 22 — 08/04/2026
# Updated: Session 27 — 10/04/2026 (full Anthropic export audit)

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
| Codebase refactor — all .py files | 🔲 | Clean rebuild, same interfaces. Trigger: after draw wired + validated. S27-28. |

### Draw intelligence
| Item | Status | Notes |
|------|--------|-------|
| Team draw tendency rolling | ✅ | Dormant — weight=0.0 |
| Bookmaker implied draw probability | ✅ | Dormant — weight=0.0 |
| H2H draw rate | ✅ | Dormant — weight=0.0 |
| draw_pull gravity param | ✅ | Disabled — 0.0 |
| dti_draw_lock param | ✅ | Disabled — 999.0 |
| Draw signal validation | ✅ | S25. pred_score_draw: NO SIGNAL. p=0.1876. |
| SCORE_DRAW_NUDGE | ✅ | S25. REMOVED. Not backed by evidence. |
| Draw evolution tool | ✅ | S25. edgelab_draw_evolution.py. Three-pass. |
| Draw evolution results | ✅ | S25. Best combo: 1.347x. draw_profile.json produced. |
| expected_goals_total as draw signal | ✅ | S26. Wired. w_xg_draw param. 1.088x lift. |
| Composite draw gate | ✅ | S26. Wired. odds_draw_prob > 0.288 AND supporting signal. composite_draw_boost param. |
| Wire composite draw signal into engine | ✅ | S26 DONE. Both params in EngineParams + LeagueParams. |
| Seed gridsearch from draw_profile.json | ✅ | S26 DONE. 16/17 tiers passed gate. |
| DPOL rolling window validation of draw signal | ⏳ | S27. DPOL run complete — results being assessed. |
| BTTS/scoreline inconsistency fix | ⏳ | Partially improved by score prediction v2. Monitor. |

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
| Full re-evolution — post score prediction v2 + draw changes | ⏳ | S27. DPOL run complete — assessing results now. |
| Draw gridsearch — draw-focused objective | ✅ | S24. E2 minor only. |
| Draw gridsearch — seeded from draw_profile.json | ✅ | S26 DONE. 16/17 tiers passed gate. gridsearch_results.json saved. |
| Seed draw weights from gridsearch into DPOL | 🔲 | S27 queue item 2. After overnight results assessed. |
| Confirm w_xg_draw + composite_draw_boost in DPOL search space | 🔲 | S27 queue item 3. |
| Signals-only run post weighted loss | ✅ | S24. All dormant. |
| DPOL boldness tuning | ✅ | Currently 'small' |
| DPOL upset-focused evolution | 🔲 | Trigger: draw intelligence + signals active. |
| DPOL run type taxonomy | ✅ | S23. |
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
| Weather load | ✅/📡 | Cache 79.4% complete. Wire when complete. |
| Weather cache completion | ⏳ | 105,388/132,685. Check S27. |
| Wire weather to DPOL | 🔲 | Trigger: cache complete |
| Missing stadium coords | 🔲 | Bristol Rvs, Oxford, AFC Wimbledon, Crawley, Carlisle |
| expected_goals_total as draw signal | ✅ | S26 DONE. 1.088x lift. w_xg_draw param wired. |
| Composite draw gate | ✅ | S26 DONE. odds_draw_prob anchor + supporting signals. |

### Phase 3 — Discussed / designed / discovered
| Signal | Status | Notes |
|--------|--------|-------|
| Injury index | 🚫 | BLOCKED on API-Football |
| Manager sack bounce | 🔲 | Trigger: signals active + feedback loop |
| Underdog / park the bus | 🅿 | Trigger: signals active |
| Public mood / world sentiment | 🔲 | Needs live data |
| E1 home bias investigation | ✅ | S26 DONE. Confirmed: 80.3% H predictions vs 43.8% actual. Monitoring. |
| instinct_dti_thresh / skew_correction_thresh | ✅ | S26 CLARIFIED. Confirmed unused stubs. Review at refactor. |
| Market baseline calculator | ✅ | S24 |
| H/A breakdown vs market | ✅ | S24 |
| Draw evolution tool | ✅ | S25. Three-pass. edgelab_draw_evolution.py |
| Draw signal validation | ✅ | S25. pred_score_draw: NO SIGNAL. |
| Three-pass full param evolution | 🅿 | Andrew's S25-26 idea. Extend draw evolution philosophy to ALL params. Pass 1: predict pre-match only. Pass 2: single-param retrospective. Pass 3: combination testing. Full param space ~30-40 candidates, ~10k+ triples. Trigger: draw intelligence proven under DPOL rolling window validation. |
| Retest previously discarded params via three-pass | 🅿 | Params that showed no individual signal may behave differently when interactions mapped. Trigger: three-pass proven on draws. |

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
| Gary → EdgeLab signal recommendation | 🔲 | M2. Gary analyses misses, identifies patterns, recommends signal changes back to EdgeLab. This is the feedback loop that closes M2 and the most important long-term feature. |
| Team Chaos Index | 🔲 | |
| Signal Performance Ledger | 🔲 | |
| Bogey team system (full) | 🔲 | |
| Gary persistent memory | 🔲 | M2 |
| Gary temporal awareness | 🅿 | Trigger: API-Football |
| Gary general football chat | 🅿 | Trigger: M3 |
| Gary acca picks feature | 🅿 | Trigger: Gary live on site |
| Social comment workflow | 🅿 | Use upset picks + Gary commentary as comments on football pages. Gary calls it before the game, screenshots result after. |
| Gary behavioural addiction detection | 🅿 | Pattern-based only — not blunt warnings. Reads frequency, stake escalation, time patterns, loss chasing. Intervenes quietly in Gary's voice only when the pattern is genuinely concerning. Not 3 bets on a Saturday. Trigger: M3. |
| Gary onboarding — team affiliation | 🅿 | "Who's your team?" on first use. Gary responds in character. From that point Gary is subtly tuned to that user — their fixtures get more attention, Gary sounds like he gives a damn. Retention mechanic: Gary isn't a tool, he's YOUR Gary. Trigger: M3. |
| Gary accent / regional persona | 🅿 | Default by region: Scottish, Welsh, Irish, English. English default: Geordie or Cockney (TBD — Geordie preferred). Fully customisable in paid tiers. Trigger: M3. |
| Gary avatar — visual identity | 🅿 | Settled design: flat cap pulled low, dark football shirt, straight dark jeans, white Adidas Sambas, slight paunch, stubble. Face never fully visible. "GARY" on the back of the shirt. 7-second intro clip exists (Kling). Kling subscription active. Trigger: M3. |

---

## SECTION 5 — ACCA BUILDER

| Item | Status | Notes |
|------|--------|-------|
| Acca builder core | ✅ | |
| Result, safety, value, upset, BTTS accas | ✅ | |
| Winner + BTTS acca type | ✅ | S24 |
| Decorrelation | ✅ | |
| Duplicate pick warning | ✅ | |
| Full qualifying picks list in matchday briefing | ✅ | S24 |
| Public HTML qualifying picks tab | ✅ | S26 FIXED. Tab system rebuilt. Manually maintained. |
| Automate qualifying picks into public HTML | 🔲 | S27 queue item 4. Wire edgelab_acca.py output to HTML. |
| Over 2.5 goals acca type | 🔲 | Derivable from pred_home_goals + pred_away_goals. No new data needed. |
| Home bankers acca type | 🔲 | H predictions only, high conf, LOW/MED chaos, no upset flag. Up to 10-fold for long shot variant. |
| Underdog acca type | 🔲 | Mix of value picks + 1-2 upset flags. Signal-backed, not random. Distinct from pure upset acca. |
| Gary's Weekly Longshot | 🅿 | Single weekly selection, 8-10 fold, highest upset scores + value edge. Target 500/1+. Gary explains every leg. Charity donation of winnings — sidesteps pooled betting regulation. When it lands it's a brand story. Trigger: upset flip Stage 2 validated. |
| Selection builder (on-site) | 🅿 | User builds their own selections from Gary's full qualifying picks list. NOT called a bet builder. Gary shows full list for every acca type — user picks from it. Site-wide. Trigger: M3. |
| Long shot acca | 🅿 | |
| Double upset acca | 🅿 | Trigger: upset flip Stage 2 validated |
| Automated prediction pipeline (one command) | 🔲 | Small build |

---

## SECTION 6 — DATA & INFRASTRUCTURE

| Item | Status | Notes |
|------|--------|-------|
| 417 CSVs, 25 years, 17 tiers | ✅ | 373 load cleanly. 48 skipped. |
| DataBot | ✅ | |
| Weather cache | ⏳ | 105,388/132,685 (79.4%). Check S27. |
| edgelab_results_check.py | ✅ | Built S20. Pulls results from API-Football against predictions CSV. Not yet in automatic feedback loop. |
| edgelab_market_baseline.py | ✅ | S24 |
| edgelab_ha_breakdown.py | ✅ | S24 |
| edgelab_draw_signal_validation.py | ✅ | S25 |
| edgelab_draw_evolution.py | ✅ | S25 |
| draw_profile.json | ✅ | S25. In EDGELAB folder. |
| gridsearch_results.json | ✅ | S26. Per-tier draw params that cleared gate. |
| Live results auto-ingestion | 🔲 | M2. results_check.py exists but not in automatic loop. |
| API-Football connection | 🔲 | Pro plan active until May 2026 |
| Personal web app | 🅿 | Trigger: M2 running |

---

## SECTION 7 — PREDICTION WORKFLOW

| Item | Status | Notes |
|------|--------|-------|
| Weekly prediction windows defined | ✅ | Thu + Sun |
| Thursday run — weekend fixtures | ✅ | Done S24 |
| Sunday run — midweek fixtures | 🔲 | Deferred S25-26. Check if still relevant. |
| Results check after each fixture set | 🔲 | Permanent workflow |
| Gary opinions on key matches | ✅ | Done S24 — 4 upset picks |
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
| Email list building via Mailchimp | ✅ | → Brevo at 400 contacts |
| gary@garyknows.com email | ✅ | |
| Public predictions HTML | ✅ | S24. Tab system fixed S26. |
| Gary picks live on site | 🔲 | M3 |
| Paid tier / gating | 🔲 | M3 |
| khaotikk.com Mailchimp auth | 🔲 | Unconfirmed — check S27 |
| Migrate Mailchimp → Brevo | 🔲 | Trigger: 400 contacts |
| Social content — Gary Upset Picks format | 🔲 | Screenshot Gary's upset call before game. Screenshot result after. Comment on football pages pre-match. |
| TikTok / Instagram content pipeline | ⏳ | ~3,000 TikTok views. Fresh start 8 April 2026. Repeatable video format established. |
| Gary avatar video — intro clip | ✅ | 7-second Kling clip exists. Cap, Sambas, turns to reveal GARY. "Who the hell is Gary?" cut live. |
| Cryptocurrency payment options | 🅿 | Trigger: M3 paid tier |
| Countdown clock on landing page | 🅿 | Add when launch date is confirmed. |
| Companies House registration | 🔲 | Before public launch |

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
| Draw intelligence dormant | ⏳ | Wired S26. DPOL run complete S27 — assessing results. |
| SCORE_DRAW_NUDGE | ✅ | REMOVED S25. Not backed by evidence. |
| E2 overconfidence w_form=0.94 | ⏳ | Monitoring |
| E1 home bias | ⏳ | CONFIRMED S26. 80.3% H predictions vs 43.8% actual. Monitor after full DPOL re-run. |
| BTTS/scoreline inconsistency | ⏳ | Partially improved by score prediction v2 |
| khaotikk.com Mailchimp auth | 🔲 | Confirm S27 |
| instinct_dti_thresh / skew_correction_thresh | ✅ | CLARIFIED S26. Confirmed unused stubs. Review at refactor. |
| Public HTML qualifying picks tab | ✅ | FIXED S26. Tab system rebuilt. |
| Qualifying picks manually maintained in HTML | 🔲 | Automate via edgelab_acca.py S27 |
| Public HTML — iOS Safari tab/search unresponsive | 🔲 | Confirmed broken on iPhone (S27). Android works. Fix: add onkeyup + onchange fallbacks to oninput on search input. S27. |
| Gary H2H last8_meetings naming | ✅ | FIXED S24 |
| Gary weather_factor/weather_load | ✅ | FIXED S24 |
| Date labelling — fixtures shown a day early | 🔲 | Investigate S27. Likely in acca.py HTML date conversion or databot UTC offset handling. |

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
| DPOL rolling window validation of draw signal | ⏳ | S27. DPOL run complete — assessing. |
| Three-pass full param evolution | 🅿 | Extend draw evolution philosophy to ALL params (~30-40 candidates, ~10k+ triples). Pass 1: predict pre-match only. Pass 2: single-param retrospective. Pass 3: combination testing. Gives DPOL a map of param interactions before it searches. Draw evolution Pass 3 proved this works. Trigger: draw intelligence proven under DPOL rolling window validation. |
| Retest previously discarded params via three-pass | 🅿 | Params with no individual signal may combine meaningfully. Trigger: three-pass proven on draws and validated through full DPOL. |

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

Source: Sessions 1-27 + full Anthropic export (all 29 conversations, 10/04/2026)
Last updated: Session 27 — 10/04/2026
Next update: Session 27 close (unprompted — as files)
