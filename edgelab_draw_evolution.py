#!/usr/bin/env python3
"""
edgelab_draw_evolution.py
--------------------------
Two-pass draw evolution tool.

WHAT IT DOES:
  Pass 1 — Prediction pass (pre-match only)
    Runs the full engine pipeline on every historical match using only
    pre-match data. Logs the engine's call, confidence, DTI, and all
    pre-match signal values alongside the actual result.

  Pass 2 — Retrospective reassessment (post-match as teacher)
    Filters to actual draw matches. For each draw, loads the post-match
    data (shots, corners, cards, half-time score etc.) as confirmation
    context. Builds a feature matrix comparing pre-match conditions in
    draws vs non-draws. Identifies which pre-match signals have the
    highest draw rate lift and at what threshold bands.

OUTPUT:
  - Universal draw profile (across all 17 tiers)
  - Per-tier draw profile (where patterns diverge)
  - Suggested draw intelligence param weights per tier
  - Printed report + JSON output ready for targeted DPOL gridsearch

INTEGRITY:
  Post-match data is NEVER used in the prediction pass.
  It is ONLY used in retrospective analysis to validate pre-match signals.
  The suggested params are a starting point — not direct deployment.

Usage:
  python edgelab_draw_evolution.py --data history/
  python edgelab_draw_evolution.py --data history/ --output draw_profile.json
"""

import argparse
import json
import sys
import warnings
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")

from edgelab_engine import (
    load_all_csvs,
    compute_form,
    compute_goal_diff,
    compute_dti,
    compute_team_draw_tendency,
    compute_h2h,
    compute_score_prediction,
    compute_odds_draw_prob,
)

# ── Pre-match signal columns (used in prediction — always available) ──────────
PRE_MATCH_SIGNALS = [
    "home_form",       # rolling form score
    "away_form",
    "home_gd",         # rolling goal difference
    "away_gd",
    "dti",             # decision tension index
    "home_draw_rate",  # rolling draw tendency
    "away_draw_rate",
    "h2h_draw_rate",   # H2H draw history
    "h2h_home_edge",   # H2H directional edge
    "odds_draw_prob",  # bookmaker implied draw probability
    "pred_home_goals", # expected goals from score prediction
    "pred_away_goals",
    "pred_margin",     # expected goal margin
    "btts_prob",       # both teams to score probability
]

# Derived signals we compute from pre-match data
DERIVED_SIGNALS = [
    "form_parity",     # 1 - abs(home_form - away_form) — how evenly matched
    "gd_parity",       # 1 - abs(home_gd - away_gd)/3 — GD closeness
    "draw_tendency",   # avg of home + away draw rates
    "expected_goals_total",  # pred_home + pred_away goals
    "expected_goals_diff",   # abs(pred_home - pred_away)
]

# Post-match columns (retrospective teacher — never used in predictions)
POST_MATCH_COLS = [
    "HTHG", "HTAG",    # half-time goals
    "HS", "AS",        # total shots
    "HST", "AST",      # shots on target
    "HC", "AC",        # corners
    "HF", "AF",        # fouls
    "HY", "AY",        # yellow cards
    "HR", "AR",        # red cards
]


# ── Pipeline ──────────────────────────────────────────────────────────────────

def run_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """Run full pre-match engine pipeline. Returns enriched dataframe."""
    df = compute_form(df)
    df = compute_goal_diff(df)
    df = compute_dti(df)
    df = compute_team_draw_tendency(df)
    df = compute_h2h(df)
    df = compute_score_prediction(df)
    if "B365D" in df.columns:
        df = compute_odds_draw_prob(df)
    else:
        df["odds_draw_prob"] = 0.26  # neutral prior if no odds
    return df


def add_derived_signals(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived pre-match signals."""
    df = df.copy()
    df["form_parity"] = 1.0 - (df["home_form"] - df["away_form"]).abs().clip(0, 1)
    df["gd_parity"]   = (1.0 - ((df["home_gd"] - df["away_gd"]).abs() / 3.0)).clip(0, 1)
    df["draw_tendency"] = (df["home_draw_rate"] + df["away_draw_rate"]) / 2.0
    df["expected_goals_total"] = df["pred_home_goals"] + df["pred_away_goals"]
    df["expected_goals_diff"]  = (df["pred_home_goals"] - df["pred_away_goals"]).abs()
    return df


# ── Signal analysis ───────────────────────────────────────────────────────────

def analyse_signal(df: pd.DataFrame, signal: str, n_bins: int = 5) -> dict:
    """
    For a given pre-match signal, measure draw rate across quantile bins.
    Returns lift per bin and the best threshold for draw prediction.
    """
    if signal not in df.columns:
        return None

    col = df[signal].dropna()
    if len(col) < 100:
        return None

    df_clean = df[[signal, "actual_draw"]].dropna()
    overall_draw_rate = df_clean["actual_draw"].mean()

    try:
        df_clean["bin"] = pd.qcut(df_clean[signal], q=n_bins, duplicates="drop")
    except Exception:
        return None

    bin_stats = []
    for bin_label, group in df_clean.groupby("bin", observed=True):
        n = len(group)
        draws = group["actual_draw"].sum()
        draw_rate = draws / n if n > 0 else 0
        lift = draw_rate / overall_draw_rate if overall_draw_rate > 0 else 1
        bin_stats.append({
            "bin": str(bin_label),
            "n": int(n),
            "draw_rate": round(float(draw_rate), 4),
            "lift": round(float(lift), 4),
        })

    if not bin_stats:
        return None

    # Pearson correlation of signal with actual_draw
    corr, p_val = stats.pearsonr(df_clean[signal], df_clean["actual_draw"])

    # Best bin (highest lift, minimum 100 matches)
    best_bin = max((b for b in bin_stats if b["n"] >= 100), key=lambda x: x["lift"], default=None)

    return {
        "signal": signal,
        "overall_draw_rate": round(float(overall_draw_rate), 4),
        "correlation": round(float(corr), 4),
        "p_value": round(float(p_val), 4),
        "significant": bool(p_val < 0.05),
        "max_lift": round(max(b["lift"] for b in bin_stats), 4),
        "best_bin": best_bin,
        "bins": bin_stats,
    }


def validate_with_postmatch(df_draws: pd.DataFrame, signal: str) -> dict:
    """
    For draw matches only, check whether the post-match data confirms
    the pre-match signal is genuinely predictive.

    Specifically: among draw matches, do high-signal values correlate
    with tight post-match stats (e.g. equal shots, equal half-time)?
    This confirms the signal was capturing genuine competitive balance,
    not noise.
    """
    results = {}

    available_post = [c for c in POST_MATCH_COLS if c in df_draws.columns]
    if not available_post or signal not in df_draws.columns:
        return results

    df_clean = df_draws[[signal] + available_post].dropna(subset=[signal])

    # Half-time draw rate — draws that were level at HT are "genuine" draws
    if "HTHG" in df_clean.columns and "HTAG" in df_clean.columns:
        df_clean["ht_draw"] = (df_clean["HTHG"] == df_clean["HTAG"]).astype(int)
        corr, p = stats.pearsonr(df_clean[signal].fillna(0), df_clean["ht_draw"].fillna(0))
        results["ht_draw_correlation"] = round(float(corr), 4)
        results["ht_draw_p_value"] = round(float(p), 4)

    # Shot parity — evenly contested matches
    if "HS" in df_clean.columns and "AS" in df_clean.columns:
        df_clean["shot_parity"] = 1 - (
            (df_clean["HS"] - df_clean["AS"]).abs() /
            (df_clean["HS"] + df_clean["AS"] + 1)
        )
        corr, p = stats.pearsonr(df_clean[signal].fillna(0), df_clean["shot_parity"].fillna(0))
        results["shot_parity_correlation"] = round(float(corr), 4)
        results["shot_parity_p_value"] = round(float(p), 4)

    return results


def suggest_draw_weights(signal_results: list) -> dict:
    """
    From the signal analysis results, suggest draw intelligence param weights.
    Only suggests non-zero weights for signals that are statistically
    significant AND show meaningful lift (>= 1.08x).
    """
    suggestions = {
        "w_draw_odds": 0.0,
        "w_draw_tendency": 0.0,
        "w_h2h_draw": 0.0,
        "draw_score_thresh": 0.55,
        "notes": [],
    }

    for r in signal_results:
        if r is None or not r.get("significant"):
            continue

        lift = r["max_lift"]
        signal = r["signal"]

        if lift < 1.08:
            continue

        if signal == "odds_draw_prob":
            suggestions["w_draw_odds"] = round(min(lift - 1.0, 0.5), 2)
            suggestions["notes"].append(f"odds_draw_prob: {lift:.3f}x lift — activate w_draw_odds")

        elif signal == "draw_tendency":
            suggestions["w_draw_tendency"] = round(min(lift - 1.0, 0.4), 2)
            suggestions["notes"].append(f"draw_tendency: {lift:.3f}x lift — activate w_draw_tendency")

        elif signal == "h2h_draw_rate":
            suggestions["w_h2h_draw"] = round(min(lift - 1.0, 0.3), 2)
            suggestions["notes"].append(f"h2h_draw_rate: {lift:.3f}x lift — activate w_h2h_draw")

    return suggestions


# ── Main ──────────────────────────────────────────────────────────────────────

def run_evolution(data_dir: str, output_path: str = None):
    print("\n" + "=" * 65)
    print("  EDGELAB DRAW EVOLUTION — Three-Pass Draw Analysis")
    print("=" * 65)

    # Load data
    print(f"\n  Loading data from: {data_dir}")
    try:
        df_all = load_all_csvs(data_dir)
    except FileNotFoundError as e:
        print(f"\n  ERROR: {e}")
        sys.exit(1)

    print(f"  {len(df_all):,} matches loaded across {df_all['tier'].nunique()} tiers")

    all_signals = PRE_MATCH_SIGNALS + DERIVED_SIGNALS
    all_tiers = sorted(df_all["tier"].unique())

    # ── PASS 1 — Run full pipeline on all data ────────────────────────────────
    print(f"\n  PASS 1 — Running prediction pipeline...")
    print(f"  {'─'*60}")

    processed_tiers = {}
    for tier in all_tiers:
        df_tier = df_all[df_all["tier"] == tier].copy().reset_index(drop=True)
        if len(df_tier) < 200:
            continue
        print(f"  [{tier}] {len(df_tier):,} matches...", end=" ", flush=True)
        try:
            df_tier = run_pipeline(df_tier)
            df_tier = add_derived_signals(df_tier)
            df_tier["actual_draw"] = (df_tier["FTR"] == "D").astype(int)
            processed_tiers[tier] = df_tier
            n_draws = df_tier["actual_draw"].sum()
            draw_rate = df_tier["actual_draw"].mean()
            print(f"done — {n_draws:,} draws ({draw_rate:.1%})")
        except Exception as e:
            print(f"ERROR: {e}")

    if not processed_tiers:
        print("\n  ERROR: No tiers processed.")
        sys.exit(1)

    df_combined = pd.concat(processed_tiers.values(), ignore_index=True)
    df_draws_all = df_combined[df_combined["actual_draw"] == 1].copy()

    print(f"\n  Total: {len(df_combined):,} matches, {len(df_draws_all):,} actual draws "
          f"({len(df_draws_all)/len(df_combined):.1%})")

    # ── PASS 2 — Universal draw signal analysis ───────────────────────────────
    print(f"\n  PASS 2 — Universal draw signal analysis (all tiers combined)...")
    print(f"  {'─'*60}")

    universal_results = []
    for signal in all_signals:
        result = analyse_signal(df_combined, signal)
        if result:
            # Post-match validation on draw matches
            pm_validation = validate_with_postmatch(df_draws_all, signal)
            result["postmatch_validation"] = pm_validation
            universal_results.append(result)
            status = "✓ SIG" if result["significant"] else "  ---"
            print(f"  {status}  {signal:<30}  lift={result['max_lift']:.3f}x  "
                  f"corr={result['correlation']:+.3f}  p={result['p_value']:.4f}")

    # Rank by significance + lift
    significant = sorted(
        [r for r in universal_results if r["significant"] and r["max_lift"] >= 1.08],
        key=lambda x: x["max_lift"], reverse=True
    )

    print(f"\n  Significant signals with meaningful lift (>=1.08x): {len(significant)}")
    for r in significant:
        best = r.get("best_bin", {})
        print(f"    {r['signal']:<30}  max lift={r['max_lift']:.3f}x  "
              f"best band: {best.get('bin','?')} ({best.get('draw_rate',0):.1%} draw rate)")

    # Suggested universal weights
    universal_weights = suggest_draw_weights(universal_results)

    # ── Per-tier analysis ─────────────────────────────────────────────────────
    print(f"\n  PER-TIER DRAW PROFILE")
    print(f"  {'─'*60}")

    tier_profiles = {}
    for tier, df_tier in processed_tiers.items():
        df_draws_tier = df_tier[df_tier["actual_draw"] == 1].copy()
        tier_signal_results = []

        for signal in all_signals:
            result = analyse_signal(df_tier, signal)
            if result:
                pm_val = validate_with_postmatch(df_draws_tier, signal)
                result["postmatch_validation"] = pm_val
                tier_signal_results.append(result)

        tier_sig = sorted(
            [r for r in tier_signal_results if r["significant"] and r["max_lift"] >= 1.08],
            key=lambda x: x["max_lift"], reverse=True
        )

        tier_weights = suggest_draw_weights(tier_signal_results)
        tier_profiles[tier] = {
            "n": len(df_tier),
            "n_draws": int(df_tier["actual_draw"].sum()),
            "draw_rate": round(float(df_tier["actual_draw"].mean()), 4),
            "significant_signals": tier_sig,
            "suggested_weights": tier_weights,
        }

        top_signals = [r["signal"] for r in tier_sig[:3]]
        print(f"  {tier:<5}  draw={tier_profiles[tier]['draw_rate']:.1%}  "
              f"sig signals: {len(tier_sig)}  top: {', '.join(top_signals) or 'none'}")

    # ── PASS 3 — Combination signal testing ──────────────────────────────────
    # Only test combinations of signals that individually showed p<0.05
    # and lift >= 1.03x. Tests all 2-signal and 3-signal combos.
    # A combo "fires" when ALL signals in the group are in their draw-positive
    # band simultaneously. Measures draw rate and lift when that happens.
    print(f"\n  PASS 3 — Combination signal testing...")
    print(f"  {'─'*60}")

    # Candidate signals: significant with any positive lift
    candidates = [
        r for r in universal_results
        if r and r.get("significant") and r["max_lift"] >= 1.03
    ]
    candidate_names = [r["signal"] for r in candidates]
    print(f"  Candidate signals for combination: {len(candidate_names)}")

    # For each candidate, find the draw-positive threshold (top quantile bin)
    # i.e. the value above/below which draw rate is highest
    def get_draw_positive_mask(df: pd.DataFrame, signal: str,
                                signal_result: dict) -> pd.Series:
        """Return boolean mask for rows where this signal is in draw-positive zone."""
        if signal not in df.columns:
            return pd.Series(False, index=df.index)

        # Find the best bin from the signal analysis
        best_bin = signal_result.get("best_bin")
        if not best_bin:
            return pd.Series(False, index=df.index)

        # Parse the bin interval string e.g. "(0.288, 0.712]"
        try:
            bin_str = best_bin["bin"].strip()
            left_open = bin_str.startswith("(")
            parts = bin_str.strip("([])").split(",")
            lo, hi = float(parts[0].strip()), float(parts[1].strip())
            col = df[signal].fillna(df[signal].median())
            if left_open:
                return (col > lo) & (col <= hi)
            else:
                return (col >= lo) & (col <= hi)
        except Exception:
            # Fallback: top half of distribution
            median = df[signal].median()
            corr = signal_result.get("correlation", 0)
            if corr >= 0:
                return df[signal].fillna(median) >= median
            else:
                return df[signal].fillna(median) <= median

    # Build masks for all candidates on combined dataset
    candidate_masks = {}
    candidate_lookup = {r["signal"]: r for r in candidates}
    for sig in candidate_names:
        mask = get_draw_positive_mask(df_combined, sig, candidate_lookup[sig])
        candidate_masks[sig] = mask

    overall_draw_rate_comb = df_combined["actual_draw"].mean()
    MIN_MATCHES = 500   # minimum matches for a combination to be reportable
    COMBO_LIFT_THRESHOLD = 1.15  # must clear this to be interesting

    combo_results = []

    from itertools import combinations

    total_pairs = len(list(combinations(candidate_names, 2)))
    total_triples = len(list(combinations(candidate_names, 3)))
    print(f"  Testing {total_pairs} pairs and {total_triples} triples...")

    for size in [2, 3]:
        for combo in combinations(candidate_names, size):
            # Combined mask: all signals in draw-positive zone simultaneously
            combined_mask = pd.Series(True, index=df_combined.index)
            for sig in combo:
                combined_mask = combined_mask & candidate_masks[sig]

            n_combo = combined_mask.sum()
            if n_combo < MIN_MATCHES:
                continue

            draw_rate_combo = df_combined.loc[combined_mask, "actual_draw"].mean()
            lift_combo = draw_rate_combo / overall_draw_rate_comb

            if lift_combo < COMBO_LIFT_THRESHOLD:
                continue

            # Chi-square vs rest
            draws_in  = int(df_combined.loc[combined_mask,  "actual_draw"].sum())
            draws_out = int(df_combined.loc[~combined_mask, "actual_draw"].sum())
            n_in      = int(n_combo)
            n_out     = int((~combined_mask).sum())

            contingency = np.array([
                [draws_in,  n_in  - draws_in],
                [draws_out, n_out - draws_out],
            ])
            try:
                _, p_val, _, _ = stats.chi2_contingency(contingency)
            except Exception:
                p_val = 1.0

            if p_val >= 0.05:
                continue

            combo_results.append({
                "signals": list(combo),
                "size": size,
                "n": int(n_combo),
                "draw_rate": round(float(draw_rate_combo), 4),
                "lift": round(float(lift_combo), 4),
                "p_value": round(float(p_val), 4),
            })

    # Sort by lift descending
    combo_results.sort(key=lambda x: x["lift"], reverse=True)

    if combo_results:
        print(f"\n  COMBINATION SIGNALS (lift >={COMBO_LIFT_THRESHOLD}x, p<0.05, n>={MIN_MATCHES}):")
        print(f"  {'Signals':<55} {'N':>7} {'DrawRate':>9} {'Lift':>7} {'p':>8}")
        print(f"  {'─'*55} {'─'*7} {'─'*9} {'─'*7} {'─'*8}")
        for c in combo_results[:25]:  # top 25
            sig_str = " + ".join(c["signals"])
            if len(sig_str) > 54:
                sig_str = sig_str[:51] + "..."
            print(f"  {sig_str:<55} {c['n']:>7,} {c['draw_rate']:>9.1%} "
                  f"{c['lift']:>7.3f}x {c['p_value']:>8.4f}")

        # Find the best combo overall
        best = combo_results[0]
        print(f"\n  BEST COMBINATION: {' + '.join(best['signals'])}")
        print(f"    Draw rate: {best['draw_rate']:.1%} vs baseline {overall_draw_rate_comb:.1%}")
        print(f"    Lift: {best['lift']:.3f}x across {best['n']:,} matches  p={best['p_value']:.4f}")

        # Combos that include the existing draw signals (actionable via DPOL)
        actionable_signals = {"odds_draw_prob", "draw_tendency", "h2h_draw_rate",
                               "home_draw_rate", "away_draw_rate"}
        actionable_combos = [
            c for c in combo_results
            if any(s in actionable_signals for s in c["signals"])
        ]
        if actionable_combos:
            print(f"\n  ACTIONABLE COMBOS (include existing draw signals):")
            for c in actionable_combos[:10]:
                sig_str = " + ".join(c["signals"])
                print(f"    {sig_str:<55} lift={c['lift']:.3f}x  n={c['n']:,}")
    else:
        print(f"  No combinations cleared {COMBO_LIFT_THRESHOLD}x lift with p<0.05 and n>={MIN_MATCHES}.")
        print(f"  Weak individual signals do not combine into a strong draw predictor.")

    # ── Summary report ────────────────────────────────────────────────────────
    print(f"\n{'='*65}")
    print(f"  DRAW EVOLUTION SUMMARY")
    print(f"{'='*65}")

    print(f"\n  UNIVERSAL DRAW SIGNALS (ranked by lift):")
    if significant:
        for r in significant:
            best = r.get("best_bin", {})
            pm = r.get("postmatch_validation", {})
            postmatch_note = ""
            if pm.get("ht_draw_correlation", 0) > 0.05:
                postmatch_note = " [confirmed by HT data]"
            elif pm.get("shot_parity_correlation", 0) > 0.05:
                postmatch_note = " [confirmed by shot parity]"
            print(f"    {r['signal']:<30}  lift={r['max_lift']:.3f}x  "
                  f"p={r['p_value']:.4f}{postmatch_note}")
    else:
        print("    No universal signals cleared the 1.08x lift threshold.")

    print(f"\n  SUGGESTED UNIVERSAL DRAW PARAMS:")
    for k, v in universal_weights.items():
        if k != "notes":
            print(f"    {k:<25} = {v}")
    for note in universal_weights.get("notes", []):
        print(f"    NOTE: {note}")

    print(f"\n  PER-TIER PARAM VARIATIONS (where tier differs from universal):")
    for tier, profile in sorted(tier_profiles.items()):
        tw = profile["suggested_weights"]
        diffs = []
        for param in ["w_draw_odds", "w_draw_tendency", "w_h2h_draw"]:
            if abs(tw.get(param, 0) - universal_weights.get(param, 0)) >= 0.05:
                diffs.append(f"{param}={tw[param]:.2f}")
        if diffs:
            print(f"    {tier:<5}  {', '.join(diffs)}")
        else:
            print(f"    {tier:<5}  matches universal")

    print(f"\n  NEXT STEP:")
    print(f"    Use the suggested weights above as starting params for a")
    print(f"    targeted draw gridsearch in edgelab_gridsearch.py.")
    print(f"    Gate: draw accuracy must improve >=5pp AND overall <=0.5% drop.")

    # ── JSON output ───────────────────────────────────────────────────────────
    output = {
        "meta": {
            "total_matches": int(len(df_combined)),
            "total_draws": int(len(df_draws_all)),
            "overall_draw_rate": round(float(len(df_draws_all) / len(df_combined)), 4),
            "tiers_analysed": list(processed_tiers.keys()),
        },
        "combinations": {
            "top_combos": combo_results[:20],
            "best": combo_results[0] if combo_results else None,
            "actionable": [
                c for c in combo_results
                if any(s in {"odds_draw_prob","draw_tendency","h2h_draw_rate",
                             "home_draw_rate","away_draw_rate"} for s in c["signals"])
            ][:10],
        },
        "universal": {
            "significant_signals": significant,
            "suggested_weights": universal_weights,
        },
        "per_tier": {
            tier: {
                "n": p["n"],
                "n_draws": p["n_draws"],
                "draw_rate": p["draw_rate"],
                "suggested_weights": p["suggested_weights"],
                "top_signals": [r["signal"] for r in p["significant_signals"][:5]],
            }
            for tier, p in tier_profiles.items()
        },
    }

    if output_path:
        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)
        print(f"\n  Profile saved to: {output_path}")

    print("\n" + "=" * 65 + "\n")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EdgeLab Draw Evolution — two-pass draw analysis")
    parser.add_argument("--data",   required=True, help="Path to history/ folder")
    parser.add_argument("--output", default="draw_profile.json",
                        help="Output JSON path (default: draw_profile.json)")
    args = parser.parse_args()
    run_evolution(args.data, args.output)
