"""
edgelab_draw_signal_validation.py
----------------------------------
Validates the S24 draw signal discovery:
  Does pred_score_draw == 1 correlate with actual draws across the full
  25-year historical dataset?

Run from your EDGELAB folder:
  python edgelab_draw_signal_validation.py --data history/
"""

import argparse
import sys
import numpy as np
import pandas as pd
from scipy import stats

from edgelab_engine import (
    load_all_csvs,
    compute_form,
    compute_goal_diff,
    compute_dti,
    compute_team_draw_tendency,
    compute_h2h,
    compute_score_prediction,
)

TIER_NAMES = {
    "E0":"Premier League","E1":"Championship","E2":"League One","E3":"League Two",
    "EC":"National League","B1":"Belgian First Division","D1":"Bundesliga",
    "D2":"2. Bundesliga","I1":"Serie A","I2":"Serie B","N1":"Eredivisie",
    "SC0":"Scottish Premiership","SC1":"Scottish Championship",
    "SC2":"Scottish League One","SC3":"Scottish League Two",
    "SP1":"La Liga","SP2":"La Liga 2",
}


def run_tier(df_tier: pd.DataFrame, tier: str) -> dict:
    df = df_tier.copy().reset_index(drop=True)

    if len(df) < 100:
        return None

    try:
        df = compute_form(df)
        df = compute_goal_diff(df)
        df = compute_dti(df)
        df = compute_team_draw_tendency(df)
        df = compute_h2h(df)
        df = compute_score_prediction(df)
    except Exception as e:
        print(f"  [{tier}] Pipeline error: {e}")
        return None

    if "pred_score_draw" not in df.columns:
        return None

    df["actual_draw"] = (df["FTR"] == "D").astype(int)

    n_total = len(df)
    n_flagged = int((df["pred_score_draw"] == 1).sum())

    if n_flagged == 0:
        return None

    draw_rate_all      = df["actual_draw"].mean()
    draw_rate_flagged  = df[df["pred_score_draw"] == 1]["actual_draw"].mean()
    draw_rate_not      = df[df["pred_score_draw"] == 0]["actual_draw"].mean()
    lift = draw_rate_flagged / draw_rate_all if draw_rate_all > 0 else 0

    return {
        "tier": tier,
        "n": n_total,
        "n_flagged": n_flagged,
        "flag_rate": n_flagged / n_total,
        "draw_rate_all": draw_rate_all,
        "draw_rate_flagged": draw_rate_flagged,
        "draw_rate_not": draw_rate_not,
        "lift": lift,
        "actual_draw": df["actual_draw"].values,
        "pred_score_draw": df["pred_score_draw"].values,
    }


def run_validation(data_dir: str):
    print("\n" + "=" * 65)
    print("  DRAW SIGNAL VALIDATION — pred_score_draw vs actual draws")
    print("  25-year historical dataset")
    print("=" * 65)

    print(f"\n  Loading data from: {data_dir}")
    try:
        df_all = load_all_csvs(data_dir)
    except FileNotFoundError as e:
        print(f"\n  ERROR: {e}")
        sys.exit(1)

    print(f"  {len(df_all):,} rows loaded across {df_all['tier'].nunique()} tiers\n")

    tier_results = {}
    all_actual = []
    all_flagged = []

    for tier in sorted(df_all["tier"].unique()):
        df_tier = df_all[df_all["tier"] == tier].copy()
        print(f"  Running [{tier}] ({len(df_tier):,} matches)...", end=" ", flush=True)
        result = run_tier(df_tier, tier)
        if result:
            tier_results[tier] = result
            all_actual.append(result["actual_draw"])
            all_flagged.append(result["pred_score_draw"])
            print(f"done — flag rate {result['flag_rate']:.1%}, lift {result['lift']:.2f}x")
        else:
            print("skipped")

    if not tier_results:
        print("\n  ERROR: No tiers processed successfully.")
        sys.exit(1)

    # Overall stats
    combined_actual  = np.concatenate(all_actual)
    combined_flagged = np.concatenate(all_flagged)

    n_total   = len(combined_actual)
    n_flagged = int((combined_flagged == 1).sum())

    overall_draw_rate     = combined_actual.mean()
    draw_rate_flagged     = combined_actual[combined_flagged == 1].mean()
    draw_rate_not_flagged = combined_actual[combined_flagged == 0].mean()
    flag_rate             = n_flagged / n_total
    lift                  = draw_rate_flagged / overall_draw_rate if overall_draw_rate > 0 else 0

    tp = int(combined_actual[combined_flagged == 1].sum())
    fp = int(n_flagged - tp)
    fn = int(combined_actual[combined_flagged == 0].sum())
    tn = int((n_total - n_flagged) - fn)

    contingency = np.array([[tp, fp], [fn, tn]])
    chi2, p_value, _, _ = stats.chi2_contingency(contingency)

    print(f"\n{'='*65}")
    print(f"  OVERALL RESULTS ({n_total:,} matches across all tiers)")
    print(f"  {'─'*60}")
    print(f"  Real-world draw rate:             {overall_draw_rate:.1%}")
    print(f"  pred_score_draw flag rate:        {flag_rate:.1%}")
    print(f"  Draw rate when flagged (==1):     {draw_rate_flagged:.1%}")
    print(f"  Draw rate when NOT flagged (==0): {draw_rate_not_flagged:.1%}")
    print(f"  Lift vs baseline:                 {lift:.3f}x  ({(lift-1)*100:+.1f}%)")
    print(f"  Chi-square p-value:               {p_value:.4f}  ", end="")
    if p_value < 0.001:
        print("*** HIGHLY SIGNIFICANT")
    elif p_value < 0.01:
        print("** SIGNIFICANT")
    elif p_value < 0.05:
        print("* SIGNIFICANT")
    else:
        print("(not significant)")

    print(f"\n  PER-TIER BREAKDOWN")
    print(f"  {'Tier':<6} {'N':>7} {'Flagged':>8} {'Flag%':>7} {'Base%':>7} "
          f"{'When=1':>8} {'When=0':>8} {'Lift':>7}")
    print(f"  {'─'*6} {'─'*7} {'─'*8} {'─'*7} {'─'*7} {'─'*8} {'─'*8} {'─'*7}")

    for tier in sorted(tier_results.keys()):
        r = tier_results[tier]
        print(
            f"  {tier:<6} {r['n']:>7,} {r['n_flagged']:>8,} "
            f"{r['flag_rate']:>7.1%} {r['draw_rate_all']:>7.1%} "
            f"{r['draw_rate_flagged']:>8.1%} {r['draw_rate_not']:>8.1%} "
            f"{r['lift']:>7.3f}x"
        )

    positive = [t for t,r in tier_results.items() if r["lift"] >= 1.10]
    weak     = [t for t,r in tier_results.items() if 1.00 <= r["lift"] < 1.10]
    negative = [t for t,r in tier_results.items() if r["lift"] < 1.00]

    print(f"\n  Signal positive (>=1.10x): {len(positive)} — {', '.join(positive) or 'none'}")
    print(f"  Signal weak (1.00-1.10x):  {len(weak)}  — {', '.join(weak) or 'none'}")
    print(f"  Signal negative (<1.00x):  {len(negative)} — {', '.join(negative) or 'none'}")

    print(f"\n  VERDICT")
    print(f"  {'─'*60}")
    if lift >= 1.15 and p_value < 0.05:
        print(f"  SIGNAL VALID — {lift:.3f}x lift, p={p_value:.4f}")
        print(f"  pred_score_draw should be wired into draw_score.")
        print(f"  The SCORE_DRAW_NUDGE in edgelab_engine.py is justified.")
    elif lift >= 1.05 and p_value < 0.05:
        print(f"  WEAK SIGNAL — {lift:.3f}x lift, p={p_value:.4f}")
        print(f"  Present but modest. Wire with low weight and monitor.")
    elif p_value >= 0.05:
        print(f"  NO SIGNAL — lift of {lift:.3f}x is not statistically significant.")
        print(f"  The 26.6% flag rate is a property of Poisson, not a predictor.")
        print(f"  REMOVE the SCORE_DRAW_NUDGE from edgelab_engine.py.")
    else:
        print(f"  INCONCLUSIVE — {lift:.3f}x lift, p={p_value:.4f}")

    print("\n" + "=" * 65 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Draw signal historical validation")
    parser.add_argument("--data", required=True, help="Path to history/ folder (flat CSVs)")
    args = parser.parse_args()
    run_validation(args.data)
