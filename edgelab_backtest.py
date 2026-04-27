#!/usr/bin/env python3
"""
EdgeLab Backtest
----------------
Walks forward through historical seasons, runs the distribution engine
on each gameweek using only data available up to that point, and scores
predictions against actual results.

This is the ground truth for whether the scoreline map engine actually works.

Usage:
    python edgelab_backtest.py history/ --tier E0
    python edgelab_backtest.py history/ --tier E0 --seasons 3
    python edgelab_backtest.py history/ --tier all
    python edgelab_backtest.py history/ --tier E0 --min-confidence 0.3

Output:
    Overall accuracy vs market baseline
    Breakdown by outcome (H/D/A)
    Breakdown by confidence band
    Breakdown by scatter (how certain the distribution was)
"""

import sys
import os
import argparse
import logging

import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from edgelab_engine import load_all_csvs, prepare_dataframe, EngineParams, assign_match_round
from edgelab_config import load_params

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("EdgeLabBacktest")

ALL_TIERS = ["E0","E1","E2","E3","EC","B1","D1","D2","I1","I2","N1","SC0","SC1","SC2","SC3","SP1","SP2"]


def get_engine_params(tier: str) -> EngineParams:
    from edgelab_dpol import LeagueParams
    lp = load_params(tier)
    if lp is None:
        return EngineParams()
    return EngineParams(
        w_form=lp.w_form, w_gd=lp.w_gd, home_adv=lp.home_adv,
        dti_edge_scale=lp.dti_edge_scale, dti_ha_scale=lp.dti_ha_scale,
        draw_margin=lp.draw_margin, coin_dti_thresh=lp.coin_dti_thresh,
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


def predict_row(row, db, tier):
    """
    Run scoreline-map prediction on a single fixture row.

    Uses the new engine-based similarity function: each scoreline population's
    evolved params are applied to the fixture via the engine. The top match
    is the population whose params produce the highest confidence score on
    this fixture. The outcome and confidence come directly from that population.

    This is a like-for-like test of the similarity fix — not distribution averaging.
    """
    fixture_features = {
        "home_form":      row.get("home_form"),
        "away_form":      row.get("away_form"),
        "home_gd":        row.get("home_gd"),
        "away_gd":        row.get("away_gd"),
        "dti":            row.get("dti"),
        "home_form_home": row.get("home_form_home"),
        "away_form_away": row.get("away_form_away"),
        "home_adv_team":  row.get("home_adv_team"),
        "away_adv_team":  row.get("away_adv_team"),
        "home_form_adj":  row.get("home_form_adj"),
        "away_form_adj":  row.get("away_form_adj"),
        "season_stage":   row.get("season_stage"),
        "rest_days_diff": row.get("rest_days_diff"),
        "odds_draw_prob": row.get("odds_draw_prob"),
    }
    try:
        matches = db.match_fixture_to_scorelines(
            tier=tier, fixture_features=fixture_features, top_n=3
        )
        if not matches:
            return {"prediction": None, "confidence": 0.0, "scatter": 1.0,
                    "top_scoreline": None, "top_outcome": None}

        top = matches[0]
        return {
            "prediction":    top["outcome"],
            "confidence":    top["similarity"],
            "scatter":       1.0 - top["similarity"],   # inverse of confidence
            "top_scoreline": top["scoreline"],
            "top_outcome":   top["outcome"],
        }
    except Exception:
        return {
            "prediction": None, "confidence": 0.0, "scatter": 1.0,
            "top_scoreline": None, "top_outcome": None,
        }


def run_backtest_for_tier(df_tier, tier, db, max_seasons=None, min_confidence=0.0):
    """
    Walk forward through seasons. For each gameweek:
    - Use all prior data as context (form, GD etc)
    - Score the distribution prediction against actual FTR
    - Never use future data

    min_confidence: only score predictions at or above this confidence.
    """
    print(f"\n{'='*60}")
    print(f"  BACKTEST — {tier}  |  {len(df_tier):,} matches")

    # Check profiles exist
    profiles = db.get_scoreline_profiles(tier)
    if not profiles:
        print(f"  ✗ No scoreline profiles for {tier} — run scoreline maps first")
        return None

    viable = {k: v for k, v in profiles.items() if not v.get("merged_to_outcome")}
    print(f"  Profiles: {len(viable)} viable scoreline populations")
    print(f"{'='*60}")

    ep = get_engine_params(tier)
    df_tier = df_tier.copy()
    df_tier = assign_match_round(df_tier)

    seasons = sorted(df_tier["season"].unique(), reverse=False)  # oldest first
    if max_seasons is not None:
        seasons = seasons[-max_seasons:]
        print(f"  Testing on {max_seasons} most recent seasons: {seasons[0]} → {seasons[-1]}")
    else:
        print(f"  Testing on {len(seasons)} seasons: {seasons[0]} → {seasons[-1]}")

    results = []
    FORM_WINDOW = 6  # seasons of prior data to build context — skip first N seasons

    for s_idx, season in enumerate(seasons):
        # Use all data before this season as context
        prior_seasons = seasons[:s_idx]
        if len(prior_seasons) < 2:
            # Not enough context to compute meaningful form/GD
            print(f"    {season}: skipped (insufficient prior context)")
            continue

        df_prior = df_tier[df_tier["season"].isin(prior_seasons)].copy()
        df_season = df_tier[df_tier["season"] == season].copy()
        max_round = int(df_season["match_round"].max())

        season_results = []

        for rnd in range(1, max_round + 1):
            df_up_to_prev_round = df_season[df_season["match_round"] < rnd].copy()
            df_this_round = df_season[df_season["match_round"] == rnd].copy()

            if df_this_round.empty:
                continue

            # Context = all prior seasons + everything in this season before this round
            df_context = pd.concat([df_prior, df_up_to_prev_round], ignore_index=True)

            # Tag the gameweek fixtures as "upcoming" — same pattern as predict.py
            df_context["_upcoming"] = False
            df_this_round["_upcoming"] = True
            df_combined = pd.concat([df_context, df_this_round], ignore_index=True)

            # Run feature pipeline — form/GD/DTI computed from context only
            try:
                df_combined = prepare_dataframe(df_combined, ep)
            except Exception as e:
                continue

            df_gw = df_combined[df_combined["_upcoming"] == True].copy()
            if df_gw.empty:
                continue

            for _, row in df_gw.iterrows():
                actual = row.get("FTR")
                if not actual or actual not in ("H", "D", "A"):
                    continue

                pred_result = predict_row(row, db, tier)
                prediction = pred_result["prediction"]
                confidence = pred_result["confidence"]
                scatter = pred_result["scatter"]

                if prediction is None:
                    continue

                season_results.append({
                    "season":        season,
                    "round":         rnd,
                    "home":          row.get("HomeTeam", ""),
                    "away":          row.get("AwayTeam", ""),
                    "actual":        actual,
                    "prediction":    prediction,
                    "correct":       int(prediction == actual),
                    "confidence":    round(confidence, 4),
                    "scatter":       round(scatter, 4),
                    "top_scoreline": pred_result.get("top_scoreline"),
                })

        n = len(season_results)
        if n > 0:
            acc = sum(r["correct"] for r in season_results) / n
            print(f"    {season}: {sum(r['correct'] for r in season_results)}/{n} = {acc:.1%}")
        results.extend(season_results)

    return results


def print_report(results, tier, min_confidence=0.0):
    if not results:
        print(f"\n  No results to report for {tier}")
        return

    df = pd.DataFrame(results)

    # Apply confidence filter
    if min_confidence > 0:
        df_filtered = df[df["confidence"] >= min_confidence]
        print(f"\n  Confidence filter ≥{min_confidence:.0%}: {len(df_filtered)}/{len(df)} predictions")
    else:
        df_filtered = df

    if df_filtered.empty:
        print("  No predictions above confidence threshold.")
        return

    total = len(df_filtered)
    correct = df_filtered["correct"].sum()
    overall_acc = correct / total

    # Market baseline — approx from actual outcome distribution
    h_rate = (df_filtered["actual"] == "H").mean()
    d_rate = (df_filtered["actual"] == "D").mean()
    a_rate = (df_filtered["actual"] == "A").mean()
    market_baseline = max(h_rate, d_rate, a_rate)  # always predict the most common outcome

    print(f"\n{'='*60}")
    print(f"  BACKTEST RESULTS — {tier}")
    print(f"{'='*60}")
    print(f"\n  Overall : {correct}/{total} = {overall_acc:.1%}  (market baseline: {market_baseline:.1%}  delta: {overall_acc - market_baseline:+.1%})")

    # By outcome
    print(f"\n  BY OUTCOME (how well it predicts each outcome):")
    print(f"  {'Outcome':<10} {'Predicted':>10} {'Correct':>10} {'Acc':>8} {'Recall':>8}")
    print(f"  {'-'*50}")
    for outcome in ("H", "D", "A"):
        predicted_as = df_filtered[df_filtered["prediction"] == outcome]
        n_pred = len(predicted_as)
        n_correct = predicted_as["correct"].sum()
        acc = n_correct / n_pred if n_pred > 0 else 0.0
        # Recall: of all actual X, how many did we call X
        actual_as = df_filtered[df_filtered["actual"] == outcome]
        n_actual = len(actual_as)
        recalled = actual_as[actual_as["prediction"] == outcome]["correct"].sum()
        recall = recalled / n_actual if n_actual > 0 else 0.0
        print(f"  {outcome:<10} {n_pred:>10,} {n_correct:>10,} {acc:>8.1%} {recall:>8.1%}")

    # By confidence band
    print(f"\n  BY CONFIDENCE BAND:")
    print(f"  {'Band':<15} {'N':>8} {'Correct':>10} {'Acc':>8}")
    print(f"  {'-'*45}")
    bands = [
        ("Low  (<20%)",   0.0,  0.20),
        ("Med  (20-40%)", 0.20, 0.40),
        ("High (40-60%)", 0.40, 0.60),
        ("Very (>60%)",   0.60, 1.01),
    ]
    for label, lo, hi in bands:
        band = df_filtered[(df_filtered["confidence"] >= lo) & (df_filtered["confidence"] < hi)]
        n = len(band)
        c = band["correct"].sum()
        acc = c / n if n > 0 else 0.0
        print(f"  {label:<15} {n:>8,} {c:>10,} {acc:>8.1%}")

    # By scatter band
    print(f"\n  BY SCATTER (distribution certainty):")
    print(f"  {'Scatter':<20} {'N':>8} {'Correct':>10} {'Acc':>8}")
    print(f"  {'-'*50}")
    scatter_bands = [
        ("Certain  (<0.3)",   0.0,  0.30),
        ("Clear    (0.3-0.5)",0.30, 0.50),
        ("Unclear  (0.5-0.7)",0.50, 0.70),
        ("Noise    (>0.7)",   0.70, 1.01),
    ]
    for label, lo, hi in scatter_bands:
        band = df_filtered[(df_filtered["scatter"] >= lo) & (df_filtered["scatter"] < hi)]
        n = len(band)
        c = band["correct"].sum()
        acc = c / n if n > 0 else 0.0
        print(f"  {label:<20} {n:>8,} {c:>10,} {acc:>8.1%}")

    print(f"\n  Avg confidence : {df_filtered['confidence'].mean():.1%}")
    print(f"  Avg scatter    : {df_filtered['scatter'].mean():.3f}")
    print()


def main():
    parser = argparse.ArgumentParser(description="EdgeLab Backtest — distribution engine accuracy")
    parser.add_argument("folder", nargs="?", default=".", help="History CSV folder")
    parser.add_argument("--tier", type=str, default="E0")
    parser.add_argument("--seasons", type=int, default=None, help="Test on N most recent seasons")
    parser.add_argument("--min-confidence", type=float, default=0.0,
                        help="Only count predictions at or above this confidence (0.0-1.0)")
    parser.add_argument("--db", type=str, default=None)
    args = parser.parse_args()

    db_path = args.db or os.path.join(os.path.dirname(os.path.abspath(__file__)), "edgelab.db")

    try:
        from edgelab_db import EdgeLabDB
        db = EdgeLabDB(db_path)
    except Exception as e:
        print(f"DB not available: {e}")
        sys.exit(1)

    print("\n╔══════════════════════════════════════════╗")
    print("║       EdgeLab Backtest — v1              ║")
    print("╚══════════════════════════════════════════╝")

    if args.tier == "all":
        tiers_to_run = ALL_TIERS
    else:
        tiers_to_run = [args.tier]

    print(f"\n  Loading CSVs from {args.folder}...")
    df_all = load_all_csvs(args.folder, tiers=tiers_to_run)
    print(f"  Loaded {len(df_all):,} rows")

    for tier in tiers_to_run:
        df_tier = df_all[df_all["tier"] == tier].copy()
        if df_tier.empty:
            print(f"\n  No data for {tier}, skipping.")
            continue

        results = run_backtest_for_tier(
            df_tier=df_tier,
            tier=tier,
            db=db,
            max_seasons=args.seasons,
            min_confidence=args.min_confidence,
        )

        if results:
            print_report(results, tier, min_confidence=args.min_confidence)


if __name__ == "__main__":
    main()
