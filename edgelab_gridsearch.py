"""
EdgeLab Grid Search — Draw Intelligence Weights
------------------------------------------------
Searches for optimal draw intelligence params per tier.

S26 UPDATE: Seeds starting params from draw_profile.json rather than
searching from zero. The draw evolution Pass 3 identified which signals
have lift and at what levels — this gridsearch tests the neighbourhood
around those seeded values rather than the full blind space.

Also covers all 17 tiers (previously only E1/E2/E3/EC).
Also includes w_xg_draw and composite_draw_boost (new S26 params).

Usage:
  python edgelab_gridsearch.py history/
  python edgelab_gridsearch.py history/ --draw-profile draw_profile.json
  python edgelab_gridsearch.py history/ --tier E0
"""

import sys
import json
import warnings
import argparse
import itertools

warnings.filterwarnings("ignore")
sys.path.insert(0, ".")

from edgelab_engine import (
    load_all_csvs, prepare_dataframe, predict_dataframe,
    evaluate, assign_match_round, EngineParams
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_seed_weights(profile_path: str, tier: str) -> dict:
    """
    Load per-tier suggested draw weights from draw_profile.json.
    Falls back to universal suggested weights if tier not found.
    Returns a dict with keys: w_draw_odds, w_draw_tendency, w_h2h_draw,
    draw_score_thresh. w_xg_draw and composite_draw_boost default to 0.
    """
    try:
        with open(profile_path) as f:
            profile = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return _zero_seeds()

    # Per-tier first
    tier_data = profile.get("per_tier", {}).get(tier, {})
    weights = tier_data.get("suggested_weights", {})

    # Fall back to universal if tier has nothing useful
    if not weights or all(v == 0.0 for k, v in weights.items() if k != "draw_score_thresh" and k != "notes"):
        weights = profile.get("universal", {}).get("suggested_weights", {})

    return {
        "w_draw_odds":       float(weights.get("w_draw_odds", 0.0)),
        "w_draw_tendency":   float(weights.get("w_draw_tendency", 0.0)),
        "w_h2h_draw":        float(weights.get("w_h2h_draw", 0.0)),
        "draw_score_thresh": float(weights.get("draw_score_thresh", 0.55)),
        "w_xg_draw":         0.0,   # new param — always start at 0, DPOL activates
        "composite_draw_boost": 0.0, # new param — always start at 0, DPOL activates
    }


def _zero_seeds() -> dict:
    return {
        "w_draw_odds": 0.0,
        "w_draw_tendency": 0.0,
        "w_h2h_draw": 0.0,
        "draw_score_thresh": 0.55,
        "w_xg_draw": 0.0,
        "composite_draw_boost": 0.0,
    }


def build_search_grid(seed: dict) -> list:
    """
    Build search grid centred on the seeded values.
    For each weight param, search seed ± 0.10 in 0.05 steps, minimum 0.
    Always include 0.0 as a candidate (so baseline is always tested).
    draw_score_thresh: fixed candidates around seeded value.
    w_xg_draw and composite_draw_boost: small grid, always include 0.
    """

    def _range(seed_val: float, step: float = 0.05, spread: float = 0.10) -> list:
        lo = max(0.0, round(seed_val - spread, 4))
        hi = round(seed_val + spread, 4)
        vals = set()
        v = lo
        while v <= hi + 1e-9:
            vals.add(round(v, 4))
            v = round(v + step, 4)
        vals.add(0.0)  # always include zero
        vals.add(round(seed_val, 4))  # always include seed itself
        return sorted(vals)

    odds_grid      = _range(seed["w_draw_odds"])
    tendency_grid  = _range(seed["w_draw_tendency"])
    h2h_grid       = _range(seed["w_h2h_draw"])
    thresh_grid    = sorted({0.40, 0.45, 0.50, 0.55, round(seed["draw_score_thresh"], 2)})

    # New params: always start from 0, small search range
    xg_grid        = [0.0, 0.05, 0.10, 0.15, 0.20]
    boost_grid     = [0.0, 0.05, 0.10, 0.15]

    return odds_grid, tendency_grid, h2h_grid, thresh_grid, xg_grid, boost_grid


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_gridsearch(data_dir: str, profile_path: str, tier_filter: str = None):

    print("\n╔══════════════════════════════════════════════════════╗")
    print("║   EdgeLab Grid Search — Draw Intelligence (S26)     ║")
    print("║   Seeded from draw_profile.json — all 17 tiers      ║")
    print("╚══════════════════════════════════════════════════════╝\n")

    print("  Loading CSVs...")
    df_all = load_all_csvs(data_dir)
    print(f"  Loaded {len(df_all):,} rows\n")

    # Load saved engine params
    try:
        with open("edgelab_params.json") as f:
            raw = json.load(f)
        saved = {
            tier: entry["params"]
            for tier, entry in raw.items()
            if not tier.startswith("_") and "params" in entry
        }
    except FileNotFoundError:
        saved = {}
        print("  WARNING: edgelab_params.json not found — using default params\n")

    # Determine which tiers to run
    all_tiers = sorted(df_all["tier"].unique().tolist())
    if tier_filter:
        tiers = [t for t in all_tiers if t == tier_filter]
        if not tiers:
            print(f"  ERROR: tier '{tier_filter}' not found in data. Available: {all_tiers}")
            sys.exit(1)
    else:
        tiers = all_tiers

    print(f"  Running on tiers: {tiers}")
    print(f"  Draw profile: {profile_path}\n")

    DRAW_IMPROVEMENT_MIN = 0.05   # draw accuracy must improve by at least 5pp
    OVERALL_TOLERANCE    = 0.005  # overall accuracy may not drop more than 0.5%

    results_summary = {}

    for tier in tiers:
        df_tier = df_all[df_all["tier"] == tier].copy()
        if df_tier.empty:
            print(f"  {tier}: no data, skipping")
            continue

        df_tier = assign_match_round(df_tier)

        # Base params from saved edgelab_params.json
        p = saved.get(tier, {})
        base = EngineParams(
            w_form              = p.get("w_form", 0.7),
            w_gd                = p.get("w_gd", 0.4),
            home_adv            = p.get("home_adv", 0.3),
            dti_edge_scale      = p.get("dti_edge_scale", 0.4),
            dti_ha_scale        = p.get("dti_ha_scale", 0.5),
            draw_margin         = p.get("draw_margin", 0.12),
            coin_dti_thresh     = p.get("coin_dti_thresh", 0.7),
            draw_pull           = p.get("draw_pull", 0.0),
            dti_draw_lock       = p.get("dti_draw_lock", 999),
            w_draw_odds         = 0.0,
            w_draw_tendency     = 0.0,
            w_h2h_draw          = 0.0,
            draw_score_thresh   = 0.55,
            w_score_margin      = 0.0,
            w_btts              = 0.0,
            w_xg_draw           = 0.0,
            composite_draw_boost= 0.0,
            form_window         = 5,
        )

        # Load seed weights from draw profile for this tier
        seed = load_seed_weights(profile_path, tier)

        # Pre-compute features once — expensive, do it once per tier
        df_feat = prepare_dataframe(df_tier.copy(), base)

        # Baseline
        baseline_df       = predict_dataframe(df_feat.copy(), base)
        baseline_stats    = evaluate(baseline_df)
        baseline_acc      = baseline_stats["accuracy"]
        baseline_draw_acc = baseline_stats["breakdown"].get("D", 0.0)

        # Build search grids centred on seeds
        odds_g, tend_g, h2h_g, thresh_g, xg_g, boost_g = build_search_grid(seed)

        n_combos = len(odds_g) * len(tend_g) * len(h2h_g) * len(thresh_g) * len(xg_g) * len(boost_g)

        print(f"  ── {tier}  ({len(df_tier):,} matches)  Baseline: {baseline_acc:.3%}  "
              f"Draw acc: {baseline_draw_acc:.1%} ──")
        print(f"     Seeds: w_odds={seed['w_draw_odds']}  w_tend={seed['w_draw_tendency']}  "
              f"w_h2h={seed['w_h2h_draw']}  thresh={seed['draw_score_thresh']}")
        print(f"     Search grid: {n_combos:,} combinations")

        best_draw_acc    = baseline_draw_acc
        best_combo       = None
        best_stats       = None
        seen_best_draw   = baseline_draw_acc
        seen_best_overall= baseline_acc
        seen_best_combo  = None
        n_tested         = 0

        for w_odds, w_tend, w_h2h, thresh, w_xg, w_boost in itertools.product(
            odds_g, tend_g, h2h_g, thresh_g, xg_g, boost_g
        ):
            # Skip all-zero draw weights (that's baseline)
            if w_odds == 0.0 and w_tend == 0.0 and w_h2h == 0.0 and w_xg == 0.0 and w_boost == 0.0:
                continue

            test_params = EngineParams(
                w_form              = base.w_form,
                w_gd                = base.w_gd,
                home_adv            = base.home_adv,
                dti_edge_scale      = base.dti_edge_scale,
                dti_ha_scale        = base.dti_ha_scale,
                draw_margin         = base.draw_margin,
                coin_dti_thresh     = base.coin_dti_thresh,
                draw_pull           = base.draw_pull,
                dti_draw_lock       = base.dti_draw_lock,
                w_draw_odds         = w_odds,
                w_draw_tendency     = w_tend,
                w_h2h_draw          = w_h2h,
                draw_score_thresh   = thresh,
                w_score_margin      = 0.0,
                w_btts              = 0.0,
                w_xg_draw           = w_xg,
                composite_draw_boost= w_boost,
                form_window         = 5,
            )

            result_df  = predict_dataframe(df_feat.copy(), test_params)
            stats      = evaluate(result_df)
            acc        = stats["accuracy"]
            draw_acc   = stats["breakdown"].get("D", 0.0)
            n_tested  += 1

            # Track best draw seen regardless of gates
            if draw_acc > seen_best_draw:
                seen_best_draw   = draw_acc
                seen_best_overall= acc
                seen_best_combo  = (w_odds, w_tend, w_h2h, thresh, w_xg, w_boost)

            # Gated: draw +5pp AND overall within -0.5%
            draw_improved = (draw_acc - baseline_draw_acc) >= DRAW_IMPROVEMENT_MIN
            overall_ok    = acc >= (baseline_acc - OVERALL_TOLERANCE)

            if draw_improved and overall_ok and draw_acc > best_draw_acc:
                best_draw_acc = draw_acc
                best_combo    = (w_odds, w_tend, w_h2h, thresh, w_xg, w_boost)
                best_stats    = stats

        print(f"     Tested {n_tested:,} combinations")

        if best_combo is not None:
            w_odds, w_tend, w_h2h, thresh, w_xg, w_boost = best_combo
            overall_delta = best_stats["accuracy"] - baseline_acc
            draw_delta    = best_draw_acc - baseline_draw_acc
            sign = "+" if overall_delta >= 0 else ""
            print(f"     ✓ DRAW IMPROVEMENT FOUND")
            print(f"       Overall : {baseline_acc:.3%} -> {best_stats['accuracy']:.3%}  ({sign}{overall_delta:.3%})")
            print(f"       Draw acc: {baseline_draw_acc:.1%} -> {best_draw_acc:.1%}  (+{draw_delta:.1%})")
            print(f"       w_draw_odds={w_odds}  w_draw_tendency={w_tend}  w_h2h_draw={w_h2h}")
            print(f"       draw_score_thresh={thresh}  w_xg_draw={w_xg}  composite_draw_boost={w_boost}")
            print(f"       Draws predicted: {best_stats['predicted_counts'].get('D',0)}  "
                  f"(actual: {best_stats['actual_counts'].get('D',0)})")
            print(f"       H acc: {best_stats['breakdown'].get('H',0):.1%}  "
                  f"A acc: {best_stats['breakdown'].get('A',0):.1%}")
            results_summary[tier] = {
                "baseline_overall":  round(baseline_acc, 6),
                "best_overall":      round(best_stats["accuracy"], 6),
                "overall_delta":     round(best_stats["accuracy"] - baseline_acc, 6),
                "baseline_draw_acc": round(baseline_draw_acc, 6),
                "best_draw_acc":     round(best_draw_acc, 6),
                "draw_delta":        round(best_draw_acc - baseline_draw_acc, 6),
                "w_draw_odds":       w_odds,
                "w_draw_tendency":   w_tend,
                "w_h2h_draw":        w_h2h,
                "draw_score_thresh": thresh,
                "w_xg_draw":         w_xg,
                "composite_draw_boost": w_boost,
                "draws_predicted":   best_stats["predicted_counts"].get("D", 0),
                "draws_actual":      best_stats["actual_counts"].get("D", 0),
                "passed_gate":       True,
            }
        else:
            print(f"     ✗ No combo cleared both gates (draw +5pp, overall within -0.5%)")
            if seen_best_combo is not None:
                sc = seen_best_combo
                print(f"       Best seen regardless: draw {seen_best_draw:.1%}  "
                      f"overall {seen_best_overall:.3%}  "
                      f"(odds={sc[0]} tend={sc[1]} h2h={sc[2]} thresh={sc[3]} xg={sc[4]} boost={sc[5]})")
            results_summary[tier] = {
                "baseline_overall":  round(baseline_acc, 6),
                "best_overall":      round(baseline_acc, 6),
                "overall_delta":     0.0,
                "baseline_draw_acc": round(baseline_draw_acc, 6),
                "best_draw_acc":     round(baseline_draw_acc, 6),
                "draw_delta":        0.0,
                "w_draw_odds":       0.0,
                "w_draw_tendency":   0.0,
                "w_h2h_draw":        0.0,
                "draw_score_thresh": 0.55,
                "w_xg_draw":         0.0,
                "composite_draw_boost": 0.0,
                "draws_predicted":   0,
                "draws_actual":      0,
                "passed_gate":       False,
            }
        print()

    # ---------------------------------------------------------------------------
    # Summary table
    # ---------------------------------------------------------------------------
    print("\n╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                         GRID SEARCH SUMMARY — ALL TIERS                   ║")
    print("╠══════╦══════════╦═════════════╦═════════════╦═══════╦═══════╦═════════════╣")
    print("║ Tier ║ Overall Δ║ Draw Base   ║ Draw Best   ║ Odds  ║  H2H  ║  Gate       ║")
    print("╠══════╬══════════╬═════════════╬═════════════╬═══════╬═══════╬═════════════╣")
    for tier, r in sorted(results_summary.items()):
        sign  = "+" if r["overall_delta"] >= 0 else ""
        gate  = "✓ PASS" if r["passed_gate"] else "✗ FAIL"
        print(f"║ {tier:<4} ║ {sign}{r['overall_delta']:>+.2%}  ║  {r['baseline_draw_acc']:.1%}      ║  {r['best_draw_acc']:.1%}      ║ {r['w_draw_odds']:.2f}  ║ {r['w_h2h_draw']:.2f}  ║ {gate:<11} ║")
    print("╚══════╩══════════╩═════════════╩═════════════╩═══════╩═══════╩═════════════╝")

    passed = sum(1 for r in results_summary.values() if r["passed_gate"])
    print(f"\n  {passed}/{len(results_summary)} tiers passed the draw improvement gate.")

    # Save results
    with open("gridsearch_results.json", "w") as f:
        json.dump(results_summary, f, indent=2)
    print("  Results saved to gridsearch_results.json\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EdgeLab Grid Search — Draw Intelligence")
    parser.add_argument("data", help="Path to history/ folder")
    parser.add_argument("--draw-profile", default="draw_profile.json",
                        help="Path to draw_profile.json (default: draw_profile.json)")
    parser.add_argument("--tier", default=None,
                        help="Run on a single tier only (e.g. --tier E0)")
    args = parser.parse_args()

    run_gridsearch(args.data, args.draw_profile, args.tier)
