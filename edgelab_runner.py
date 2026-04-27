#!/usr/bin/env python3
"""
EdgeLab Runner v1
-----------------
Wires the prediction engine to DPOL and runs evolution league by league.
"""

import sys
import os
import argparse
import logging
import copy

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from edgelab_engine import (
    load_all_csvs,
    prepare_dataframe,
    evaluate,
    make_pred_fn,
    assign_match_round,
    EngineParams,
)
from edgelab_dpol import DPOLManager, LeagueParams, OutcomeParams
from edgelab_config import (load_params, save_params, show_config,
                             check_dataset_hash, save_dataset_hash,
                             load_outcome_params, save_outcome_params)
from edgelab_scoreline_maps import (
    run_scoreline_maps_for_tier,
    init_scoreline_table,
)

# Fixture intelligence database — logs every candidate DPOL evaluates
try:
    from edgelab_db import EdgeLabDB
    _db = EdgeLabDB()
    _DB_AVAILABLE = True
except Exception as _db_err:
    _DB_AVAILABLE = False
    _db = None
    import logging as _logging
    _logging.getLogger("EdgeLabRunner").warning(f"DB not available: {_db_err}")

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("EdgeLabRunner")
logger.setLevel(logging.INFO)


def _precompute_scoreline_columns(df_features_full, tier):
    """
    Pre-compute top_scoreline_match_outcome and top_scoreline_match_density
    for all rows in df_features_full using batched vectorised engine calls.

    Instead of calling match_fixture_to_scorelines row-by-row (N fixtures x
    M profiles = N*M engine calls), we run each profile against the full
    dataframe in one predict_dataframe call (M vectorised calls total).
    This is orders of magnitude faster.

    Returns df_features_full with two new columns added in-place.
    """
    if not _DB_AVAILABLE or _db is None:
        df_features_full["top_scoreline_match_outcome"] = ""
        df_features_full["top_scoreline_match_density"] = 0.5
        return df_features_full

    try:
        import pandas as pd
        import numpy as np
        from edgelab_engine import EngineParams, predict_dataframe
        from edgelab_db import PARAM_FIELDS

        profiles = _db.get_scoreline_profiles(tier)
        if not profiles:
            df_features_full["top_scoreline_match_outcome"] = ""
            df_features_full["top_scoreline_match_density"] = 0.5
            return df_features_full

        n_rows = len(df_features_full)
        n_profiles = sum(1 for p in profiles.values() if not p.get("merged_to_outcome"))
        print(f"  Pre-computing scoreline match: {n_rows:,} rows x {n_profiles} profiles (batched)...", end="", flush=True)

        # Build a working dataframe with the columns predict_dataframe needs.
        # We reuse the already-prepared features — just add the sentinel FTR column.
        df_work = df_features_full.copy()
        if "FTR" not in df_work.columns:
            df_work["FTR"] = "?"
        if "draw_score" not in df_work.columns:
            df_work["draw_score"] = 0.0

        # Accumulate best similarity per row across all profiles.
        best_similarity = np.zeros(n_rows, dtype=float)
        best_outcome = [""] * n_rows

        for scoreline, profile in profiles.items():
            if profile.get("merged_to_outcome"):
                continue

            outcome = profile["outcome"]
            lp = profile["params"]
            density = float(profile.get("evolved_density", 0.0) or 0.0)

            ep = EngineParams(
                w_form=lp.w_form,
                w_gd=lp.w_gd,
                home_adv=lp.home_adv,
                dti_edge_scale=lp.dti_edge_scale,
                dti_ha_scale=lp.dti_ha_scale,
                draw_margin=lp.draw_margin,
                coin_dti_thresh=lp.coin_dti_thresh,
                draw_pull=getattr(lp, "draw_pull", 0.0),
                dti_draw_lock=getattr(lp, "dti_draw_lock", 999.0),
                w_draw_odds=getattr(lp, "w_draw_odds", 0.0),
                w_draw_tendency=getattr(lp, "w_draw_tendency", 0.0),
                w_h2h_draw=getattr(lp, "w_h2h_draw", 0.0),
                draw_score_thresh=getattr(lp, "draw_score_thresh", 0.55),
                w_score_margin=getattr(lp, "w_score_margin", 0.0),
                w_btts=getattr(lp, "w_btts", 0.0),
                w_xg_draw=getattr(lp, "w_xg_draw", 0.0),
                composite_draw_boost=getattr(lp, "composite_draw_boost", 0.0),
                w_ref_signal=getattr(lp, "w_ref_signal", 0.0),
                w_travel_load=getattr(lp, "w_travel_load", 0.0),
                w_timing_signal=getattr(lp, "w_timing_signal", 0.0),
                w_motivation_gap=getattr(lp, "w_motivation_gap", 0.0),
                w_weather_signal=getattr(lp, "w_weather_signal", 0.0),
                w_venue_form=getattr(lp, "w_venue_form", 0.0),
                w_team_home_adv=getattr(lp, "w_team_home_adv", 0.0),
                w_away_team_adv=getattr(lp, "w_away_team_adv", 0.0),
                w_opp_strength=getattr(lp, "w_opp_strength", 0.0),
                w_season_stage=getattr(lp, "w_season_stage", 0.0),
                w_rest_diff=getattr(lp, "w_rest_diff", 0.0),
                form_window=5,
            )

            try:
                df_result = predict_dataframe(df_work.copy(), ep)
                preds = df_result["prediction"].values
                confs = df_result["confidence"].astype(float).values
            except Exception:
                continue

            # Similarity = confidence if prediction matches population outcome, else halved
            similarity = np.where(preds == outcome, confs, confs * 0.5)
            weighted = similarity * max(density, 0.01)

            # Update best per row
            improved = weighted > best_similarity
            best_similarity = np.where(improved, weighted, best_similarity)
            best_outcome = [outcome if improved[i] else best_outcome[i] for i in range(n_rows)]

        df_features_full["top_scoreline_match_outcome"] = best_outcome
        df_features_full["top_scoreline_match_density"] = best_similarity.tolist()
        print(f" done ({n_profiles} profiles)")

    except Exception as e:
        logger.warning(f"Scoreline pre-pass (batched) failed: {e}")
        df_features_full["top_scoreline_match_outcome"] = ""
        df_features_full["top_scoreline_match_density"] = 0.5

    return df_features_full


def engine_params_to_league_params(ep):
    return LeagueParams(
        w_form=ep.w_form, w_gd=ep.w_gd, home_adv=ep.home_adv,
        dti_edge_scale=ep.dti_edge_scale, dti_ha_scale=ep.dti_ha_scale,
        draw_margin=ep.draw_margin, coin_dti_thresh=ep.coin_dti_thresh,
        draw_pull=ep.draw_pull, dti_draw_lock=ep.dti_draw_lock,
        w_draw_odds=ep.w_draw_odds, w_draw_tendency=ep.w_draw_tendency,
        w_h2h_draw=ep.w_h2h_draw, draw_score_thresh=ep.draw_score_thresh,
        w_score_margin=ep.w_score_margin, w_btts=ep.w_btts,
        w_ref_signal=ep.w_ref_signal, w_travel_load=ep.w_travel_load,
        w_timing_signal=ep.w_timing_signal, w_motivation_gap=ep.w_motivation_gap,
        w_venue_form=getattr(ep, "w_venue_form", 0.0),
        w_team_home_adv=getattr(ep, "w_team_home_adv", 0.0),
        w_away_team_adv=getattr(ep, "w_away_team_adv", 0.0),
        w_opp_strength=getattr(ep, "w_opp_strength", 0.0),
        w_season_stage=getattr(ep, "w_season_stage", 0.0),
        w_rest_diff=getattr(ep, "w_rest_diff", 0.0),
        w_scoreline_agreement=getattr(ep, "w_scoreline_agreement", 0.0),
        w_scoreline_confidence=getattr(ep, "w_scoreline_confidence", 0.0),
    )


def league_params_to_engine_params(lp):
    return EngineParams(
        w_form=lp.w_form, w_gd=lp.w_gd, home_adv=lp.home_adv,
        dti_edge_scale=lp.dti_edge_scale, dti_ha_scale=lp.dti_ha_scale,
        draw_margin=lp.draw_margin, coin_dti_thresh=lp.coin_dti_thresh,
        draw_pull=lp.draw_pull, dti_draw_lock=lp.dti_draw_lock,
        w_draw_odds=lp.w_draw_odds, w_draw_tendency=lp.w_draw_tendency,
        w_h2h_draw=lp.w_h2h_draw, draw_score_thresh=lp.draw_score_thresh,
        w_score_margin=lp.w_score_margin, w_btts=lp.w_btts,
        w_xg_draw=getattr(lp, "w_xg_draw", 0.0),
        composite_draw_boost=getattr(lp, "composite_draw_boost", 0.0),
        w_ref_signal=getattr(lp, "w_ref_signal", 0.0),
        w_travel_load=getattr(lp, "w_travel_load", 0.0),
        w_timing_signal=getattr(lp, "w_timing_signal", 0.0),
        w_motivation_gap=getattr(lp, "w_motivation_gap", 0.0),
        w_weather_signal=getattr(lp, "w_weather_signal", 0.0),
        w_venue_form=getattr(lp, "w_venue_form", 0.0),
        w_team_home_adv=getattr(lp, "w_team_home_adv", 0.0),
        w_away_team_adv=getattr(lp, "w_away_team_adv", 0.0),
        w_opp_strength=getattr(lp, "w_opp_strength", 0.0),
        w_season_stage=getattr(lp, "w_season_stage", 0.0),
        w_rest_diff=getattr(lp, "w_rest_diff", 0.0),
        w_scoreline_agreement=getattr(lp, "w_scoreline_agreement", 0.0),
        w_scoreline_confidence=getattr(lp, "w_scoreline_confidence", 0.0),
        form_window=5,
    )


def print_params(label, p):
    print(f"  {label}:")
    print(f"    w_form={p.w_form:.4f}  w_gd={p.w_gd:.4f}  home_adv={p.home_adv:.4f}")
    print(f"    dti_edge_scale={p.dti_edge_scale:.4f}  dti_ha_scale={p.dti_ha_scale:.4f}")
    print(f"    draw_margin={p.draw_margin:.4f}  coin_dti_thresh={p.coin_dti_thresh:.4f}")
    print(f"    draw_pull={p.draw_pull:.4f}  dti_draw_lock={p.dti_draw_lock:.4f}")


def run_dpol_for_tier(df_tier, tier, window_rounds, boldness, save=True, signals_only=False):
    print(f"\n{'='*60}")
    print(f"  TIER: {tier}  |  Matches: {len(df_tier)}  |  Window: {window_rounds} rounds  |  Boldness: {boldness}")
    if signals_only:
        print(f"  MODE: SIGNALS ONLY — core params locked, searching signal weights only")
    print(f"{'='*60}")

    # Load saved evolved params as starting point, fall back to engine defaults
    saved_lp = load_params(tier)
    if signals_only and saved_lp is None:
        print(f"  ✗ Signals-only requires saved evolved core params for {tier}. Run full DPOL first.")
        return None
    if saved_lp:
        print(f"  ✓ Starting from saved evolved params for {tier}")
        starting_engine_params = league_params_to_engine_params(saved_lp)
    else:
        print(f"  ⚡ No saved params for {tier} — starting from defaults")
        starting_engine_params = EngineParams()

    default_params = EngineParams()

    # Cold baseline (always uses engine defaults so we can compare apples-to-apples)
    df_baseline = prepare_dataframe(df_tier.copy(), default_params)
    baseline_stats = evaluate(df_baseline)

    # Warm baseline — what the saved params already achieve (if we have them)
    if saved_lp:
        df_warm = prepare_dataframe(df_tier.copy(), starting_engine_params)
        warm_stats = evaluate(df_warm)
        print(f"\n  WARM BASELINE (saved params)")
        print(f"    Accuracy : {warm_stats['accuracy']:.1%}  ({warm_stats['correct']}/{warm_stats['total']})")

    print(f"\n  COLD BASELINE (engine defaults)")
    print(f"    Accuracy : {baseline_stats['accuracy']:.1%}  ({baseline_stats['correct']}/{baseline_stats['total']})")
    print(f"    Breakdown: H={baseline_stats['breakdown'].get('H',0):.1%}  D={baseline_stats['breakdown'].get('D',0):.1%}  A={baseline_stats['breakdown'].get('A',0):.1%}")
    print(f"    Predicted: {baseline_stats['predicted_counts']}")
    print(f"    Actual   : {baseline_stats['actual_counts']}")

    # Pre-compute features on the full tier once.
    # The fast pred_fn reuses these — only swaps params on each candidate eval.
    # This fixes the global guard: it now evaluates correctly on the full dataset.
    df_tier = assign_match_round(df_tier)
    df_features_full = prepare_dataframe(df_tier.copy(), starting_engine_params)

    # Pre-compute scoreline match columns once — batched vectorised version.
    df_features_full = _precompute_scoreline_columns(df_features_full, tier)

    # Global guard sample — used for the regression check on every candidate.
    # Evaluating the full tier dataset every round is prohibitively slow on large
    # tiers (E0: 14,683 matches × hundreds of rounds = millions of evals).
    # 3,000 randomly sampled rows is statistically sufficient to catch regressions
    # while reducing global guard time by ~80%. Seed is fixed for consistency.
    GLOBAL_GUARD_SAMPLE = 3000
    if len(df_features_full) > GLOBAL_GUARD_SAMPLE:
        df_global_guard = df_features_full.sample(n=GLOBAL_GUARD_SAMPLE, random_state=42)
    else:
        df_global_guard = df_features_full

    def fast_pred_fn(df_window: pd.DataFrame, league_params) -> pd.Series:
        params = EngineParams(
            w_form=league_params.w_form,
            w_gd=league_params.w_gd,
            home_adv=league_params.home_adv,
            dti_edge_scale=league_params.dti_edge_scale,
            dti_ha_scale=league_params.dti_ha_scale,
            draw_margin=league_params.draw_margin,
            coin_dti_thresh=league_params.coin_dti_thresh,
            draw_pull=league_params.draw_pull,
            dti_draw_lock=league_params.dti_draw_lock,
            w_draw_odds=league_params.w_draw_odds,
            w_draw_tendency=league_params.w_draw_tendency,
            w_h2h_draw=league_params.w_h2h_draw,
            draw_score_thresh=league_params.draw_score_thresh,
            w_score_margin=league_params.w_score_margin,
            w_btts=league_params.w_btts,
            w_xg_draw=getattr(league_params, "w_xg_draw", 0.0),
            composite_draw_boost=getattr(league_params, "composite_draw_boost", 0.0),
            w_ref_signal=getattr(league_params, "w_ref_signal", 0.0),
            w_travel_load=getattr(league_params, "w_travel_load", 0.0),
            w_timing_signal=getattr(league_params, "w_timing_signal", 0.0),
            w_motivation_gap=getattr(league_params, "w_motivation_gap", 0.0),
            w_weather_signal=getattr(league_params, "w_weather_signal", 0.0),
            w_venue_form=getattr(league_params, "w_venue_form", 0.0),
            w_team_home_adv=getattr(league_params, "w_team_home_adv", 0.0),
            w_away_team_adv=getattr(league_params, "w_away_team_adv", 0.0),
            w_opp_strength=getattr(league_params, "w_opp_strength", 0.0),
            w_season_stage=getattr(league_params, "w_season_stage", 0.0),
            w_rest_diff=getattr(league_params, "w_rest_diff", 0.0),
            w_scoreline_agreement=getattr(league_params, "w_scoreline_agreement", 0.0),
            w_scoreline_confidence=getattr(league_params, "w_scoreline_confidence", 0.0),
            form_window=5,
        )
        feat_rows = df_features_full.loc[df_features_full.index.isin(df_window.index)].copy()
        if feat_rows.empty:
            return pd.Series([], dtype=str)
        from edgelab_engine import predict_dataframe
        result = predict_dataframe(feat_rows, params)
        return result["prediction"]

    # Fixture intelligence database — get param version ID for this tier
    _param_version_id = None
    if _DB_AVAILABLE and _db is not None:
        try:
            pv = _db.get_latest_param_version(tier)
            if pv:
                _param_version_id = pv["version_id"]
        except Exception:
            pass

    def _candidate_logger(tier, season, round_num, params, window_acc,
                           global_acc, accepted, base_acc, param_version_id):
        """Write every DPOL candidate evaluation to the fixture intelligence database."""
        if _DB_AVAILABLE and _db is not None:
            try:
                _db.log_dpol_candidate(
                    tier=tier,
                    season=season,
                    round_num=round_num,
                    params=params,
                    window_accuracy=window_acc,
                    global_accuracy=global_acc,
                    accepted=accepted,
                    base_accuracy=base_acc,
                    param_version_id=param_version_id or _param_version_id,
                )
            except Exception as _e:
                pass  # never let logging break evolution

    # DPOL setup — start from saved params if available, else defaults
    initial_lp = engine_params_to_league_params(starting_engine_params)
    dpol = DPOLManager(
        initial_params_factory=lambda t: copy.deepcopy(initial_lp),
        window_rounds=window_rounds,
        boldness=boldness,
        db=_db if _DB_AVAILABLE else None,
    )

    # Process most recent seasons first — navigation directions from recent data
    # are more relevant than directions from 2000-era data.
    seasons = sorted(df_tier["season"].unique(), reverse=True)
    evolution_log = []

    print(f"\n  DPOL EVOLUTION  ({len(seasons)} seasons)")
    print(f"  {'-'*50}")

    for season in seasons:
        df_season = df_features_full[df_features_full["season"] == season].copy()
        max_round = int(df_season["match_round"].max())
        season_improvements = 0

        for rnd in range(window_rounds, max_round + 1):
            df_up_to_round = df_season[df_season["match_round"] <= rnd].copy()
            acc_before = dpol.get_league_state(tier).best_accuracy

            dpol.evolve_for_league(
                df_league=df_up_to_round,
                round_col="match_round",
                pred_fn=fast_pred_fn,
                df_full=df_global_guard,
                min_improvement=0.001,
                signals_only=signals_only,
                candidate_logger=_candidate_logger,
                season_label=season,
                param_version_id=_param_version_id,
            )

            acc_after = dpol.get_league_state(tier).best_accuracy
            if acc_after > acc_before:
                season_improvements += 1
                evolution_log.append({"season": season, "round": rnd, "accuracy": acc_after})

        best_acc = dpol.get_league_state(tier).best_accuracy
        print(f"    Season {season[-10:]:>12}  |  Best acc so far: {best_acc:.1%}  |  Improvements this season: {season_improvements}")

    # Evaluate evolved params on full dataset
    final_state = dpol.get_league_state(tier)
    evolved_params = league_params_to_engine_params(final_state.best_params)
    df_evolved = prepare_dataframe(df_tier.copy(), evolved_params)
    evolved_stats = evaluate(df_evolved)

    print(f"\n  EVOLVED RESULT")
    print(f"    Accuracy : {evolved_stats['accuracy']:.1%}  ({evolved_stats['correct']}/{evolved_stats['total']})")
    print(f"    Breakdown: H={evolved_stats['breakdown'].get('H',0):.1%}  D={evolved_stats['breakdown'].get('D',0):.1%}  A={evolved_stats['breakdown'].get('A',0):.1%}")
    print(f"    Predicted: {evolved_stats['predicted_counts']}")
    print(f"    Actual   : {evolved_stats['actual_counts']}")

    delta = evolved_stats["accuracy"] - baseline_stats["accuracy"]
    direction = "▲" if delta > 0 else ("▼" if delta < 0 else "─")
    print(f"\n  DELTA vs COLD BASELINE: {direction} {delta:+.1%}")
    print(f"\n  FINAL EVOLVED PARAMS:")
    print_params(tier, final_state.best_params)
    print(f"  Best window accuracy reached: {final_state.best_accuracy:.1%}")

    # Auto-save evolved params
    if save:
        if signals_only:
            # Merge signal weights into existing saved params — do NOT touch core params.
            prev = load_params(tier)
            if prev is not None:
                signal_fields = (
                    "w_ref_signal", "w_travel_load", "w_timing_signal",
                    "w_motivation_gap", "w_weather_signal",
                )
                evolved_signals = final_state.best_params
                for field in signal_fields:
                    setattr(prev, field, getattr(evolved_signals, field))
                save_params(
                    tier=tier,
                    params=prev,
                    accuracy=evolved_stats["accuracy"],
                    matches=evolved_stats["total"],
                    source="dpol_signals_only",
                )
                print(f"  ✓ Signal weights merged into saved params — core params unchanged.")
            else:
                print(f"  ✗ No saved params to merge into — skipping save.")
        else:
            prev = load_params(tier)
            should_save = (prev is None) or (evolved_stats["accuracy"] >= baseline_stats["accuracy"])
            if should_save:
                save_params(
                    tier=tier,
                    params=final_state.best_params,
                    accuracy=evolved_stats["accuracy"],
                    matches=evolved_stats["total"],
                    source="dpol_run",
                )
                # Also save new param version to fixture intelligence database
                if _DB_AVAILABLE and _db is not None:
                    try:
                        _db.save_param_version(
                            tier=tier,
                            params=final_state.best_params,
                            accuracy=evolved_stats["accuracy"],
                            matches=evolved_stats["total"],
                            source="dpol_run",
                        )
                    except Exception:
                        pass
                print(f"  ✓ Params saved to config.")
            else:
                print(f"  ✗ No improvement over saved params — not saving.")

    return {
        "tier": tier,
        "baseline_accuracy": baseline_stats["accuracy"],
        "evolved_accuracy": evolved_stats["accuracy"],
        "delta": delta,
        "evolution_log": evolution_log,
        "final_params": final_state.best_params,
    }


def run_outcome_specific_for_tier(df_tier, tier, window_rounds, boldness, save=True, max_seasons=None):
    """
    Outcome-specific DPOL evolution for a single tier.
    Evolves separate H, D, A param sets independently.
    Seeds from existing evolved params — never cold starts.
    Global guard sample: 5000 (D population needs headroom).
    """
    print(f"\n{'='*60}")
    print(f"  TIER: {tier}  |  Matches: {len(df_tier)}  |  MODE: OUTCOME-SPECIFIC")
    print(f"  Window: {window_rounds} rounds  |  Boldness: {boldness}")
    print(f"{'='*60}")

    # Seed each outcome from the existing evolved params
    seed_lp = load_params(tier)
    if seed_lp is None:
        print(f"  ⚠  No evolved params for {tier} — seeding from defaults")
        seed_lp = LeagueParams()
    else:
        print(f"  ✓ Seeding H/D/A from evolved params for {tier}")

    import copy
    outcome_params = OutcomeParams(
        H=copy.deepcopy(seed_lp),
        D=LeagueParams(),  # Cold start — D finds its own position from defaults
        A=copy.deepcopy(seed_lp),
    )
    print(f"  ⚡ D: cold start — finding draw params from defaults")

    # Load previously saved outcome params (subsequent runs resume from last best)
    # D cold start is preserved — only resume D if a genuine outcome-specific key exists
    from edgelab_config import DEFAULT_CONFIG_PATH, _load_raw
    _raw_config = _load_raw(DEFAULT_CONFIG_PATH)
    for outcome in ("H", "D", "A"):
        key = f"{tier}_{outcome}"
        if key in _raw_config:
            # Genuine outcome-specific saved result exists — resume from it
            p = _raw_config[key]["params"]
            defaults = LeagueParams()
            from dataclasses import asdict
            saved = LeagueParams(**{k: p.get(k, getattr(defaults, k)) for k in asdict(defaults).keys()})
            outcome_params.set_outcome(outcome, saved)
            print(f"  ✓ {outcome}: resuming from saved outcome params")
        elif outcome == "D":
            print(f"  ⚡ D: cold start — no prior outcome-specific params")

    default_params = EngineParams()
    df_tier = assign_match_round(df_tier)

    # Show population sizes
    for outcome in ("H", "D", "A"):
        n = (df_tier["FTR"] == outcome).sum()
        print(f"  Population {outcome}: {n:,} matches")

    # Pre-compute features once on full tier
    starting_ep = league_params_to_engine_params(seed_lp)
    df_features_full = prepare_dataframe(df_tier.copy(), starting_ep)

    # Pre-compute scoreline match columns once — batched vectorised version.
    df_features_full = _precompute_scoreline_columns(df_features_full, tier)

    # Global guard: 5000 sample — larger than standard to give D population headroom
    GLOBAL_GUARD_SAMPLE = 5000
    if len(df_features_full) > GLOBAL_GUARD_SAMPLE:
        df_global_guard = df_features_full.sample(n=GLOBAL_GUARD_SAMPLE, random_state=42)
    else:
        df_global_guard = df_features_full

    def fast_pred_fn(df_window: pd.DataFrame, league_params) -> pd.Series:
        params = EngineParams(
            w_form=league_params.w_form,
            w_gd=league_params.w_gd,
            home_adv=league_params.home_adv,
            dti_edge_scale=league_params.dti_edge_scale,
            dti_ha_scale=league_params.dti_ha_scale,
            draw_margin=league_params.draw_margin,
            coin_dti_thresh=league_params.coin_dti_thresh,
            draw_pull=league_params.draw_pull,
            dti_draw_lock=league_params.dti_draw_lock,
            w_draw_odds=league_params.w_draw_odds,
            w_draw_tendency=league_params.w_draw_tendency,
            w_h2h_draw=league_params.w_h2h_draw,
            draw_score_thresh=league_params.draw_score_thresh,
            w_score_margin=league_params.w_score_margin,
            w_btts=league_params.w_btts,
            w_xg_draw=getattr(league_params, "w_xg_draw", 0.0),
            composite_draw_boost=getattr(league_params, "composite_draw_boost", 0.0),
            w_ref_signal=getattr(league_params, "w_ref_signal", 0.0),
            w_travel_load=getattr(league_params, "w_travel_load", 0.0),
            w_timing_signal=getattr(league_params, "w_timing_signal", 0.0),
            w_motivation_gap=getattr(league_params, "w_motivation_gap", 0.0),
            w_weather_signal=getattr(league_params, "w_weather_signal", 0.0),
            w_venue_form=getattr(league_params, "w_venue_form", 0.0),
            w_team_home_adv=getattr(league_params, "w_team_home_adv", 0.0),
            w_away_team_adv=getattr(league_params, "w_away_team_adv", 0.0),
            w_opp_strength=getattr(league_params, "w_opp_strength", 0.0),
            w_season_stage=getattr(league_params, "w_season_stage", 0.0),
            w_rest_diff=getattr(league_params, "w_rest_diff", 0.0),
            w_scoreline_agreement=getattr(league_params, "w_scoreline_agreement", 0.0),
            w_scoreline_confidence=getattr(league_params, "w_scoreline_confidence", 0.0),
            form_window=5,
        )
        feat_rows = df_features_full.loc[df_features_full.index.isin(df_window.index)].copy()
        if feat_rows.empty:
            return pd.Series([], dtype=str)
        from edgelab_engine import predict_dataframe
        result = predict_dataframe(feat_rows, params)
        return result["prediction"]

    dpol = DPOLManager(
        window_rounds=window_rounds,
        boldness=boldness,
        db=_db if _DB_AVAILABLE else None,
    )

    # Show baseline per-outcome accuracy before evolution
    print(f"\n  BASELINE (seeded params)")
    for outcome in ("H", "D", "A"):
        df_outcome = df_features_full[df_features_full["FTR"] == outcome]
        n = len(df_outcome)
        if n == 0:
            continue
        preds = fast_pred_fn(df_outcome, outcome_params.for_outcome(outcome))
        ftr = df_outcome["FTR"].reindex(preds.index)
        correct = sum(1 for p, a in zip(preds, ftr) if p == a == outcome)
        print(f"    {outcome}: {correct}/{n} = {correct/n:.1%} correctly called as {outcome}")

    # Process most recent seasons first — limit to max_seasons if set (test mode)
    seasons = sorted(df_tier["season"].unique(), reverse=True)
    if max_seasons is not None:
        seasons = seasons[:max_seasons]
        print(f"  ⚡ TEST MODE — limiting to {max_seasons} most recent seasons")
    evolution_log = []

    print(f"\n  OUTCOME-SPECIFIC EVOLUTION  ({len(seasons)} seasons)")
    print(f"  {'-'*50}")

    for season in seasons:
        df_season = df_features_full[df_features_full["season"] == season].copy()
        max_round = int(df_season["match_round"].max())

        # D needs a wider window so starts later, but still iterates every round
        # H/A start from window_rounds, D starts from window_rounds*2
        outcome_start = {"H": window_rounds, "D": window_rounds * 2, "A": window_rounds}
        min_start = min(outcome_start.values())

        for rnd in range(min_start, max_round + 1):
            df_up_to_round = df_season[df_season["match_round"] <= rnd].copy()

            outcome_params = dpol.evolve_outcome_specific(
                df_league=df_up_to_round,
                outcome_params=outcome_params,
                round_col="match_round",
                pred_fn=fast_pred_fn,
                df_full=df_global_guard,
                min_improvement=0.001,
                candidate_logger=_candidate_logger if '_candidate_logger' in dir() else None,
                season_label=season,
            )

        print(f"    Season {season[-10:]:>12}  done")

    # Show evolved per-outcome accuracy
    print(f"\n  EVOLVED RESULT")
    outcome_results = {}
    for outcome in ("H", "D", "A"):
        df_outcome = df_features_full[df_features_full["FTR"] == outcome]
        n = len(df_outcome)
        if n == 0:
            continue
        preds = fast_pred_fn(df_outcome, outcome_params.for_outcome(outcome))
        ftr = df_outcome["FTR"].reindex(preds.index)
        correct = sum(1 for p, a in zip(preds, ftr) if p == a == outcome)
        rate = correct / n
        outcome_results[outcome] = {"correct": correct, "total": n, "rate": rate}
        print(f"    {outcome}: {correct}/{n} = {rate:.1%} correctly called as {outcome}")

    # Show key param differences between H, D, A
    print(f"\n  PARAM DIVERGENCE (H vs D vs A)")
    key_params = ["w_form", "w_gd", "home_adv", "draw_margin", "coin_dti_thresh",
                  "w_venue_form", "w_team_home_adv", "w_away_team_adv", "w_opp_strength"]
    for param in key_params:
        h_val = getattr(outcome_params.H, param)
        d_val = getattr(outcome_params.D, param)
        a_val = getattr(outcome_params.A, param)
        if abs(h_val - d_val) > 0.001 or abs(h_val - a_val) > 0.001:
            print(f"    {param:<20} H={h_val:.4f}  D={d_val:.4f}  A={a_val:.4f}")

    # Save
    if save:
        for outcome in ("H", "D", "A"):
            r = outcome_results.get(outcome, {})
            if r:
                save_outcome_params(
                    tier=tier, outcome=outcome,
                    params=outcome_params.for_outcome(outcome),
                    accuracy=r["rate"], matches=r["total"],
                    source="dpol_outcome",
                )
        print(f"\n  ✓ Outcome params saved for {tier} (H, D, A)")

    return {"tier": tier, "outcome_results": outcome_results, "outcome_params": outcome_params}


def main():
    parser = argparse.ArgumentParser(description="EdgeLab Runner — DPOL evolution")
    parser.add_argument("folder", nargs="?", default=".", help="Folder containing E0/E1 CSVs")
    parser.add_argument("--window", type=int, default=6)
    parser.add_argument("--boldness", type=str, default="small", choices=["tiny","small","medium"])
    parser.add_argument("--tier", type=str, default="all",
                        choices=["E0","E1","E2","E3","EC",
                                 "B1","D1","D2","I1","I2","N1",
                                 "SC0","SC1","SC2","SC3","SP1","SP2",
                                 "english","european","both","all"])
    parser.add_argument("--show-config", action="store_true", help="Show saved params after run")
    parser.add_argument("--signals-only", action="store_true",
                        help="Lock core params — search signal weights only. Requires saved evolved params.")
    parser.add_argument("--outcome-specific", action="store_true",
                        help="Run outcome-specific evolution — separate H/D/A param sets. Seeds from evolved params.")
    parser.add_argument("--with-scoreline-maps", action="store_true",
                        help="After outcome-specific evolution, run scoreline map evolution for each tier seeded from evolved H/D/A params. Requires --outcome-specific.")
    parser.add_argument("--seasons", type=int, default=None,
                        help="Limit evolution to most recent N seasons (test mode). Default: all seasons.")
    args = parser.parse_args()

    print("\n╔══════════════════════════════════════════╗")
    print("║         EdgeLab Runner v1 — DPOL         ║")
    print("╚══════════════════════════════════════════╝")
    print(f"\n  CSV folder : {args.folder}")
    print(f"  Window     : {args.window} rounds")
    print(f"  Boldness   : {args.boldness}")
    print(f"  Tier(s)    : {args.tier}")
    if args.signals_only:
        print(f"  Mode       : SIGNALS ONLY (core params locked)")
    if args.outcome_specific:
        print(f"  Mode       : OUTCOME-SPECIFIC (H/D/A separate param sets)")
    if getattr(args, 'with_scoreline_maps', False):
        print(f"  Mode       : + SCORELINE MAPS (863 profiles evolved per tier after H/D/A)")

    print("\n  Loading CSVs...")
    # Build tier filter for load_all_csvs — avoids loading 400k+ harvester rows
    english_tiers  = ["E0","E1","E2","E3","EC"]
    european_tiers = ["B1","D1","D2","I1","I2","N1","SC0","SC1","SC2","SC3","SP1","SP2"]
    all_tiers      = english_tiers + european_tiers

    if args.tier in ("all", "english", "european", "both"):
        load_tier_filter = {
            "all": all_tiers,
            "english": english_tiers,
            "european": european_tiers,
            "both": ["E0","E1"],
        }[args.tier]
    else:
        load_tier_filter = [args.tier]

    df_all = load_all_csvs(args.folder, tiers=load_tier_filter)
    print(f"  Loaded {len(df_all)} rows across {df_all['tier'].nunique()} tiers, {df_all['season'].nunique()} seasons.")

    # Dataset hash safeguard — warn if data has changed since params were saved
    hash_result = check_dataset_hash(args.folder)
    if hash_result["status"] == "ok":
        print(f"  Dataset hash  : ✓ {hash_result['current']}  ({hash_result['message']})")
    elif hash_result["status"] == "no_hash":
        print(f"  Dataset hash  : ⚠  No fingerprint stored yet — will save after this run.")
    elif hash_result["status"] == "changed":
        print(f"\n  ⚠  DATASET CHANGED since params were saved!")
        print(f"     Stored : {hash_result['stored']}")
        print(f"     Current: {hash_result['current']}")
        print(f"     Params may be stale. Full re-evolution recommended.")
        print(f"     Continuing anyway — results will update the stored hash.\n")

    if args.tier == "all":
        tiers_to_run = all_tiers
    elif args.tier == "english":
        tiers_to_run = english_tiers
    elif args.tier == "european":
        tiers_to_run = european_tiers
    elif args.tier == "both":
        tiers_to_run = ["E0","E1"]
    else:
        tiers_to_run = [args.tier]
    all_results = []

    for tier in tiers_to_run:
        df_tier = df_all[df_all["tier"] == tier].copy()
        if df_tier.empty:
            print(f"\n  No data for tier {tier}, skipping.")
            continue
        if args.outcome_specific:
            result = run_outcome_specific_for_tier(df_tier=df_tier, tier=tier, window_rounds=args.window, boldness=args.boldness, save=True, max_seasons=args.seasons)
            # If scoreline maps requested, run immediately after for this tier
            # seeded from the just-evolved outcome params
            if getattr(args, 'with_scoreline_maps', False) and result is not None:
                print(f"\n  ── Scoreline maps for {tier} (seeded from evolved outcome params)")
                outcome_params = result.get("outcome_params")
                if outcome_params is not None:
                    import os as _os
                    _db_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "edgelab.db")
                    init_scoreline_table(_db_path)
                    from datetime import datetime as _dt
                    _run_id = _dt.utcnow().strftime("%Y%m%d_%H%M%S")
                    # Pass outcome params so scoreline maps seed H pops from H params,
                    # D pops from D params, A pops from A params
                    run_scoreline_maps_for_tier(
                        df_tier=df_tier,
                        tier=tier,
                        db_path=_db_path,
                        run_id=_run_id,
                        show_populations=False,
                        outcome_params=outcome_params,
                    )
                else:
                    print(f"  ⚠  No outcome params returned for {tier} — scoreline maps skipped")
        elif args.signals_only:
            result = run_dpol_for_tier(df_tier=df_tier, tier=tier, window_rounds=args.window, boldness=args.boldness, save=True, signals_only=True)
        else:
            result = run_dpol_for_tier(df_tier=df_tier, tier=tier, window_rounds=args.window, boldness=args.boldness, save=True)
        if result is None:
            continue
        all_results.append(result)

    print(f"\n\n{'='*60}")
    print("  FINAL SUMMARY")
    print(f"{'='*60}")
    for r in all_results:
        if "outcome_results" in r:
            # Outcome-specific result
            print(f"\n  {r['tier']} — OUTCOME-SPECIFIC")
            for outcome, data in r["outcome_results"].items():
                print(f"    {outcome}: {data['correct']}/{data['total']} = {data['rate']:.1%}")
        else:
            print(f"  {r['tier']:<6}  {r['baseline_accuracy']:>9.1%}  {r['evolved_accuracy']:>9.1%}    {r['delta']:>+.1%}")

    standard_results = [r for r in all_results if "baseline_accuracy" in r]
    if standard_results:
        total_baseline = sum(r["baseline_accuracy"] for r in standard_results) / len(standard_results)
        total_evolved = sum(r["evolved_accuracy"] for r in standard_results) / len(standard_results)
        print(f"  {'OVERALL':<6}  {total_baseline:>9.1%}  {total_evolved:>9.1%}    {total_evolved-total_baseline:>+.1%}")

    # Save dataset hash now that params have been updated
    saved_hash = save_dataset_hash(args.folder)
    print(f"\n  Dataset hash saved: {saved_hash}")

    print(f"\n  Market baseline: ~49% (E0), ~48% (E1)")
    print()

    if args.show_config:
        show_config()


if __name__ == "__main__":
    main()
