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
from edgelab_dpol import DPOLManager, LeagueParams
from edgelab_config import load_params, save_params, show_config, check_dataset_hash, save_dataset_hash

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
        w_ref_signal=lp.w_ref_signal, w_travel_load=lp.w_travel_load,
        w_timing_signal=lp.w_timing_signal, w_motivation_gap=lp.w_motivation_gap,
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

    print(f"\n  COLD BASELINE")
    print(f"    Accuracy : {baseline_stats['accuracy']:.1%}  ({baseline_stats['correct']}/{baseline_stats['total']})")
    print(f"    Breakdown: H={baseline_stats['breakdown'].get('H',0):.1%}  D={baseline_stats['breakdown'].get('D',0):.1%}  A={baseline_stats['breakdown'].get('A',0):.1%}")
    print(f"    Predicted: {baseline_stats['predicted_counts']}")
    print(f"    Actual   : {baseline_stats['actual_counts']}")

    # Pre-compute features on the full tier once.
    # The fast pred_fn reuses these — only swaps params on each candidate eval.
    # This fixes the global guard: it now evaluates correctly on the full dataset.
    df_tier = assign_match_round(df_tier)
    df_features_full = prepare_dataframe(df_tier.copy(), starting_engine_params)

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

    seasons = sorted(df_tier["season"].unique())
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
                df_full=df_features_full,
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

    print("\n  Loading CSVs...")
    df_all = load_all_csvs(args.folder)
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

    english_tiers  = ["E0","E1","E2","E3","EC"]
    european_tiers = ["B1","D1","D2","I1","I2","N1","SC0","SC1","SC2","SC3","SP1","SP2"]
    all_tiers      = english_tiers + european_tiers

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
        result = run_dpol_for_tier(df_tier=df_tier, tier=tier, window_rounds=args.window, boldness=args.boldness, save=True, signals_only=args.signals_only)
        if result is None:
            continue
        all_results.append(result)

    print(f"\n\n{'='*60}")
    print("  FINAL SUMMARY")
    print(f"{'='*60}")
    print(f"  {'Tier':<6}  {'Baseline':>10}  {'Evolved':>10}  {'Delta':>8}")
    print(f"  {'-'*40}")
    for r in all_results:
        print(f"  {r['tier']:<6}  {r['baseline_accuracy']:>9.1%}  {r['evolved_accuracy']:>9.1%}    {r['delta']:>+.1%}")

    if all_results:
        total_baseline = sum(r["baseline_accuracy"] for r in all_results) / len(all_results)
        total_evolved = sum(r["evolved_accuracy"] for r in all_results) / len(all_results)
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
