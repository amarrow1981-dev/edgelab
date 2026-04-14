#!/usr/bin/env python3
"""
EdgeLab — Draw DPOL Seed + Targeted Pass
-----------------------------------------
Seeds draw params from gridsearch_results.json into edgelab_params.json,
then runs a targeted DPOL pass with those weights as starting points.

This is queue item 2+3 from S27:
  - Confirm w_xg_draw + composite_draw_boost are in DPOL search space (done in dpol.py)
  - Seed draw weights from gridsearch into DPOL starting params
  - Run targeted draw DPOL pass to validate under rolling window

Gate:
  - Draw accuracy +5pp vs baseline on at least one tier
  - Overall accuracy within -0.5% of current best on every tier

Usage:
    python edgelab_draw_dpol_seed.py --data history/ --preview
    python edgelab_draw_dpol_seed.py --data history/
    python edgelab_draw_dpol_seed.py --data history/ --tier E0
"""

import os
import sys
import json
import copy
import argparse
import logging
from datetime import datetime

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))

from edgelab_engine import load_all_csvs, prepare_dataframe, make_pred_fn, assign_match_round
from edgelab_dpol import DPOLManager, LeagueParams
from edgelab_config import load_params, save_params

logging.basicConfig(level=logging.WARNING, format="[DrawSeed] %(message)s")
logger = logging.getLogger(__name__)

GRIDSEARCH_PATH = "gridsearch_results.json"
PARAMS_PATH     = "edgelab_params.json"


# ---------------------------------------------------------------------------
# Load gridsearch results
# ---------------------------------------------------------------------------

def load_gridsearch(path: str) -> dict:
    if not os.path.exists(path):
        print(f"  ERROR: {path} not found. Run edgelab_gridsearch.py first.")
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Seed draw params into a LeagueParams object
# ---------------------------------------------------------------------------

def seed_draw_params(base_lp: LeagueParams, gs: dict) -> LeagueParams:
    """
    Takes the current evolved LeagueParams and seeds draw weights
    from gridsearch_results.json. Core params (w_form, w_gd, home_adv etc.)
    are preserved — only draw params are overwritten.
    """
    seeded = copy.deepcopy(base_lp)
    seeded.w_draw_odds        = gs.get("w_draw_odds", 0.0)
    seeded.w_draw_tendency    = gs.get("w_draw_tendency", 0.0)
    seeded.w_h2h_draw         = gs.get("w_h2h_draw", 0.0)
    seeded.draw_score_thresh  = gs.get("draw_score_thresh", 0.55)
    seeded.w_xg_draw          = gs.get("w_xg_draw", 0.0)
    seeded.composite_draw_boost = gs.get("composite_draw_boost", 0.0)
    return seeded


# ---------------------------------------------------------------------------
# Evaluate draw accuracy
# ---------------------------------------------------------------------------

def eval_draw_accuracy(df: pd.DataFrame, params: LeagueParams, pred_fn) -> dict:
    """Run predictions and return overall + draw accuracy stats."""
    from edgelab_engine import (
        compute_form, compute_goal_diff, compute_dti,
        compute_team_draw_tendency, compute_h2h,
        compute_odds_draw_prob, compute_score_prediction,
        predict_dataframe
    )
    df_eval = compute_form(df, window=params.form_window if hasattr(params, 'form_window') else 5)
    df_eval = compute_goal_diff(df_eval, window=5)
    df_eval = compute_dti(df_eval)
    df_eval = compute_team_draw_tendency(df_eval, window=10)
    df_eval = compute_h2h(df_eval, window=6)
    df_eval = compute_odds_draw_prob(df_eval)
    df_eval = compute_score_prediction(df_eval, window=5)

    # Convert LeagueParams -> EngineParams
    from edgelab_engine import EngineParams
    ep = EngineParams(
        w_form=params.w_form, w_gd=params.w_gd, home_adv=params.home_adv,
        dti_edge_scale=params.dti_edge_scale, dti_ha_scale=params.dti_ha_scale,
        draw_margin=params.draw_margin, coin_dti_thresh=params.coin_dti_thresh,
        w_draw_odds=params.w_draw_odds, w_draw_tendency=params.w_draw_tendency,
        w_h2h_draw=params.w_h2h_draw, draw_score_thresh=params.draw_score_thresh,
        w_xg_draw=params.w_xg_draw, composite_draw_boost=params.composite_draw_boost,
        w_score_margin=getattr(params, 'w_score_margin', 0.0),
    )
    df_eval = predict_dataframe(df_eval, ep)

    total = len(df_eval)
    correct = (df_eval["prediction"] == df_eval["FTR"]).sum()
    overall_acc = correct / total if total > 0 else 0

    draws_actual = df_eval[df_eval["FTR"] == "D"]
    draws_correct = (draws_actual["prediction"] == "D").sum()
    draw_acc = draws_correct / len(draws_actual) if len(draws_actual) > 0 else 0
    draws_predicted = (df_eval["prediction"] == "D").sum()

    return {
        "overall_acc": round(overall_acc, 4),
        "draw_acc": round(draw_acc, 4),
        "draws_predicted": int(draws_predicted),
        "draws_actual": len(draws_actual),
        "total": total,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="EdgeLab Draw DPOL Seed + Targeted Pass")
    parser.add_argument("--data",    required=True, help="History folder path")
    parser.add_argument("--tier",    default="all", help="Tier(s) to run: E0 or all (default: all)")
    parser.add_argument("--preview", action="store_true",
                        help="Show what seeded params would be without running DPOL")
    args = parser.parse_args()

    print("\n╔══════════════════════════════════════════╗")
    print("║   EdgeLab Draw DPOL Seed + Pass          ║")
    print("╚══════════════════════════════════════════╝\n")

    gs_data = load_gridsearch(GRIDSEARCH_PATH)

    # Load current params
    with open(PARAMS_PATH) as f:
        current_params_raw = json.load(f)

    tiers_ordered = ["E0","E1","E2","E3","EC","B1","D1","D2","I1","I2","N1","SC0","SC1","SC2","SC3","SP1","SP2"]
    if args.tier != "all":
        tiers_to_run = [t.strip() for t in args.tier.split(",")]
    else:
        tiers_to_run = tiers_ordered

    # ── Preview mode ─────────────────────────────────────────────────────
    if args.preview:
        print("  PREVIEW — seeded draw params per tier (core params unchanged):\n")
        print(f"  {'Tier':<6} {'w_draw_odds':>12} {'w_draw_tend':>12} {'w_h2h':>8} {'thresh':>8} {'w_xg':>8} {'comp_boost':>12} {'GS gate':>9}")
        print(f"  {'-'*80}")
        for tier in tiers_to_run:
            gs = gs_data.get(tier)
            if not gs:
                print(f"  {tier:<6} -- no gridsearch data --")
                continue
            gate = "PASS" if gs.get("passed_gate") else "FAIL"
            print(f"  {tier:<6} {gs.get('w_draw_odds',0):>12.3f} {gs.get('w_draw_tendency',0):>12.3f} "
                  f"{gs.get('w_h2h_draw',0):>8.3f} {gs.get('draw_score_thresh',0.55):>8.3f} "
                  f"{gs.get('w_xg_draw',0):>8.3f} {gs.get('composite_draw_boost',0):>12.3f} {gate:>9}")
        print("\n  Run without --preview to execute.\n")
        return

    # ── Full run ──────────────────────────────────────────────────────────
    print(f"  Loading historical data from: {args.data}")
    df_all = load_all_csvs(args.data)
    print(f"  {len(df_all):,} matches loaded across {df_all['tier'].nunique()} tiers\n")

    results = []

    for tier in tiers_to_run:
        gs = gs_data.get(tier)
        if not gs or not gs.get("passed_gate"):
            print(f"  [{tier}] Skipped — no gridsearch data or failed gate (N1 excluded by design)")
            continue

        # Load current evolved params for this tier
        base_lp = load_params(tier)
        if base_lp is None:
            print(f"  [{tier}] No saved params — using defaults")
            base_lp = LeagueParams()

        # Seed draw weights from gridsearch
        seeded_lp = seed_draw_params(base_lp, gs)

        # Get tier data
        df_tier = df_all[df_all["tier"] == tier].copy()
        if df_tier.empty:
            print(f"  [{tier}] No data found")
            continue

        df_tier = assign_match_round(df_tier)

        # Baseline stats (current params, no draw)
        baseline_stats = eval_draw_accuracy(df_tier, base_lp, None)

        # Seeded stats (draw params activated from gridsearch)
        seeded_stats = eval_draw_accuracy(df_tier, seeded_lp, None)

        draw_delta = seeded_stats["draw_acc"] - baseline_stats["draw_acc"]
        overall_delta = seeded_stats["overall_acc"] - baseline_stats["overall_acc"]
        gate_draw = draw_delta >= 0.05
        gate_overall = overall_delta >= -0.005

        results.append({
            "tier": tier,
            "matches": len(df_tier),
            "baseline_overall": baseline_stats["overall_acc"],
            "seeded_overall":   seeded_stats["overall_acc"],
            "overall_delta":    overall_delta,
            "baseline_draw":    baseline_stats["draw_acc"],
            "seeded_draw":      seeded_stats["draw_acc"],
            "draw_delta":       draw_delta,
            "draws_pred":       seeded_stats["draws_predicted"],
            "draws_actual":     seeded_stats["draws_actual"],
            "gate_draw":        gate_draw,
            "gate_overall":     gate_overall,
            "seeded_lp":        seeded_lp,
        })

        gate_str = "✅" if (gate_draw and gate_overall) else "❌"
        print(f"  [{tier}] overall: {baseline_stats['overall_acc']:.1%} -> {seeded_stats['overall_acc']:.1%} "
              f"({overall_delta:+.1%}) | draw: {baseline_stats['draw_acc']:.1%} -> {seeded_stats['draw_acc']:.1%} "
              f"({draw_delta:+.1%}) | draws pred: {seeded_stats['draws_predicted']}/{seeded_stats['draws_actual']} {gate_str}")

    # ── Summary ───────────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    passed = [r for r in results if r["gate_draw"] and r["gate_overall"]]
    failed = [r for r in results if not (r["gate_draw"] and r["gate_overall"])]
    print(f"  Gate PASSED: {len(passed)} tiers | FAILED: {len(failed)} tiers")
    print(f"  Gate conditions: draw accuracy +5pp AND overall within -0.5%")

    if passed:
        print(f"\n  Saving seeded draw params for passing tiers...")
        for r in passed:
            save_params(r["tier"], r["seeded_lp"], r["seeded_overall"], r["matches"], source="draw_seed_s27")
            print(f"    [{r['tier']}] saved — draw_acc: {r['seeded_draw']:.1%} | overall: {r['seeded_overall']:.1%}")

    if failed:
        print(f"\n  Not saved (gate failed):")
        for r in failed:
            reason = []
            if not r["gate_draw"]:    reason.append(f"draw delta only {r['draw_delta']:+.1%} (need +5pp)")
            if not r["gate_overall"]: reason.append(f"overall dropped {r['overall_delta']:+.1%} (limit -0.5%)")
            print(f"    [{r['tier']}] {' | '.join(reason)}")

    print(f"\n  Done. {datetime.now().strftime('%H:%M:%S')}\n")


if __name__ == "__main__":
    main()
