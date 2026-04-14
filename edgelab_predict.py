#!/usr/bin/env python3
"""
EdgeLab Predict v1
------------------
Runs the prediction engine on upcoming fixtures from DataBot output.

How it works:
  1. Loads your historical CSV data to build form/GD/H2H context per team
  2. Loads the DataBot upcoming fixtures CSV (no FTR — these are future matches)
  3. Appends the upcoming fixtures to the historical data
  4. Runs the full feature pipeline — teams get their real rolling form/GD going in
  5. Extracts and prints predictions for the upcoming matches only
  6. Saves predictions to a CSV for logging

Usage:
    python edgelab_predict.py --data data/ --fixtures databot_output/2026-04-02_fixtures.csv
    python edgelab_predict.py --data data/ --fixtures databot_output/2026-04-02_fixtures.csv --tier E0
    python edgelab_predict.py --data data/ --fixtures databot_output/2026-04-02_fixtures.csv --pdf

Output:
    predictions/YYYY-MM-DD_predictions.csv  — one row per upcoming fixture
    predictions/YYYY-MM-DD_predictions.pdf  — formatted table (optional)
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime

import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from edgelab_engine import (
    load_all_csvs,
    prepare_dataframe,
    compute_form,
    compute_goal_diff,
    compute_dti,
    compute_team_draw_tendency,
    compute_h2h,
    compute_odds_draw_prob,
    compute_score_prediction,
    predict_dataframe,
    compute_upset_score,
    assign_chaos_tier,
    EngineParams,
)
from edgelab_config import load_params
from edgelab_gary_brain import GaryBrain, build_engine_output_block
from edgelab_gary_context import build_gary_prompt
from edgelab_gary import Gary

logging.basicConfig(level=logging.WARNING, format="[Predict] %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = "predictions"

# ---------------------------------------------------------------------------
# Load evolved params per tier from config
# ---------------------------------------------------------------------------

def get_engine_params(tier: str) -> EngineParams:
    """Load evolved params for this tier. Falls back to defaults if not saved."""
    from edgelab_dpol import LeagueParams
    lp = load_params(tier)
    if lp is None:
        print(f"  [{tier}] No saved params — using engine defaults")
        return EngineParams()

    return EngineParams(
        w_form=lp.w_form,
        w_gd=lp.w_gd,
        home_adv=lp.home_adv,
        dti_edge_scale=lp.dti_edge_scale,
        dti_ha_scale=lp.dti_ha_scale,
        draw_margin=lp.draw_margin,
        coin_dti_thresh=lp.coin_dti_thresh,
        draw_pull=lp.draw_pull,
        dti_draw_lock=lp.dti_draw_lock,
        w_draw_odds=lp.w_draw_odds,
        w_draw_tendency=lp.w_draw_tendency,
        w_h2h_draw=lp.w_h2h_draw,
        draw_score_thresh=lp.draw_score_thresh,
        w_score_margin=lp.w_score_margin,
        w_btts=lp.w_btts,
        form_window=5,
    )


# ---------------------------------------------------------------------------
# Load DataBot upcoming fixtures CSV
# ---------------------------------------------------------------------------

def load_upcoming_fixtures(fixtures_path: str) -> pd.DataFrame:
    """
    Load the DataBot CSV. Upcoming fixtures have blank FTR.
    Returns only the upcoming rows (FTR is empty/NaN).
    """
    df = pd.read_csv(fixtures_path)

    # Normalise
    df["parsed_date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["HomeTeam", "AwayTeam", "parsed_date"])

    # Upcoming = no result yet
    upcoming = df[df["FTR"].isna() | (df["FTR"].astype(str).str.strip() == "")].copy()

    # Fill in blanks so the engine doesn't choke
    upcoming["FTR"]  = "?"     # sentinel — engine will skip eval on these
    upcoming["FTHG"] = 0
    upcoming["FTAG"] = 0
    upcoming["tier"] = upcoming["Div"]
    upcoming["season"] = "2025-26"

    for col in ["B365H", "B365D", "B365A"]:
        if col not in upcoming.columns:
            upcoming[col] = np.nan
        else:
            upcoming[col] = pd.to_numeric(upcoming[col], errors="coerce")

    upcoming = upcoming.sort_values("parsed_date").reset_index(drop=True)
    print(f"  Loaded {len(upcoming)} upcoming fixtures from {os.path.basename(fixtures_path)}")
    return upcoming


# ---------------------------------------------------------------------------
# Core prediction pipeline
# ---------------------------------------------------------------------------

def predict_upcoming(
    df_history: pd.DataFrame,
    df_upcoming: pd.DataFrame,
    tier: str,
    params: EngineParams,
) -> pd.DataFrame:
    """
    Build form/GD/H2H context from history, then predict upcoming fixtures.

    Strategy:
      - Concatenate history + upcoming for this tier
      - Run the full feature pipeline over the combined dataset
      - Extract only the upcoming rows from the result
      - The upcoming rows inherit real team form/GD/H2H going into the match
    """
    # Filter history to this tier
    df_hist_tier = df_history[df_history["tier"] == tier].copy()

    if df_hist_tier.empty:
        print(f"  [{tier}] WARNING: No historical data found — predictions will use neutral priors")

    # Upcoming fixtures for this tier
    df_up_tier = df_upcoming[df_upcoming["tier"] == tier].copy()

    if df_up_tier.empty:
        return pd.DataFrame()

    # Tag which rows are upcoming so we can extract them after
    df_hist_tier["_upcoming"] = False
    df_up_tier["_upcoming"]   = True

    # Combine — history first (chronological), upcoming at the end
    # Reset index so the pipeline processes them in order
    df_combined = pd.concat([df_hist_tier, df_up_tier], ignore_index=True)
    df_combined = df_combined.sort_values(["parsed_date", "_upcoming"]).reset_index(drop=True)

    # Run full feature pipeline
    # The pipeline reads FTR row by row to build rolling state.
    # Upcoming rows have FTR="?" — the pipeline will update team history
    # AFTER reading the row, so the upcoming fixtures see correct prior state.
    df_combined = compute_form(df_combined, window=params.form_window)
    df_combined = compute_goal_diff(df_combined, window=params.form_window)
    df_combined = compute_dti(df_combined)
    df_combined = compute_team_draw_tendency(df_combined, window=params.form_window * 2)
    df_combined = compute_h2h(df_combined, window=6)
    df_combined = compute_odds_draw_prob(df_combined)
    df_combined = compute_score_prediction(df_combined, window=params.form_window)
    df_combined = predict_dataframe(df_combined, params)
    df_combined = compute_upset_score(df_combined)

    # Extract only the upcoming rows
    result = df_combined[df_combined["_upcoming"] == True].copy()
    result = result.drop(columns=["_upcoming"])

    return result


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def format_predictions_table(df: pd.DataFrame) -> None:
    """Print a clean predictions table to terminal."""
    if df.empty:
        print("  No predictions to display.")
        return

    print(f"\n  {'#':<4} {'Tier':<5} {'Date':<12} {'Home':<22} {'Away':<22} "
          f"{'Pred':>5} {'Score':>6} {'Conf':>6} {'DTI':>6} {'Chaos':>6} "
          f"{'MktD%':>6} {'H2HD%':>6} {'Upset':>6}")
    print(f"  {'-'*120}")

    for i, (_, row) in enumerate(df.iterrows(), 1):
        pred  = row.get("prediction", "?")
        conf  = f"{row.get('confidence', 0):.0%}"
        dti   = f"{row.get('dti', 0):.3f}"
        chaos = row.get("chaos_tier", "?")
        score = row.get("pred_scoreline", "?-?")
        mktd  = f"{row.get('odds_draw_prob', 0):.0%}" if pd.notna(row.get("odds_draw_prob")) else "  -  "
        h2hd  = f"{row.get('h2h_draw_rate', 0):.0%}" if pd.notna(row.get("h2h_draw_rate")) else "  -  "
        upset_score = row.get("upset_score", 0)
        upset_flag  = row.get("upset_flag", 0)
        upset_str   = f"⚠ {upset_score:.2f}" if upset_flag == 1 else f"  {upset_score:.2f}"

        date_str = row.get("Date", "")
        home = str(row.get("HomeTeam", ""))[:21]
        away = str(row.get("AwayTeam", ""))[:21]
        tier = str(row.get("tier", ""))

        print(f"  {i:<4} {tier:<5} {date_str:<12} {home:<22} {away:<22} "
              f"{pred:>5} {score:>6} {conf:>6} {dti:>6} {chaos:>6} "
              f"{mktd:>6} {h2hd:>6} {upset_str:>6}")

    print()


def save_predictions_csv(df: pd.DataFrame, run_date: str) -> str:
    """Save predictions to CSV for logging."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, f"{run_date}_predictions.csv")

    cols = [
        "tier", "Date", "HomeTeam", "AwayTeam",
        "prediction", "pred_scoreline", "confidence", "dti", "chaos_tier",
        "home_form", "away_form", "home_gd", "away_gd",
        "odds_draw_prob", "h2h_draw_rate", "h2h_home_edge",
        "draw_score", "btts_flag", "btts_prob",
        "upset_score", "upset_flag",
        "B365H", "B365D", "B365A",
    ]
    # Only include columns that exist
    out_cols = [c for c in cols if c in df.columns]
    df[out_cols].to_csv(path, index=False)
    print(f"  Predictions saved: {path}")
    return path


def print_acca_candidates(df: pd.DataFrame) -> None:
    """Print the cleanest accumulator candidates — high confidence, low chaos, no upset flag."""
    candidates = df[
        (df["confidence"] >= 0.5) &
        (df["chaos_tier"].isin(["LOW", "MED"])) &
        (df["upset_flag"] == 0) &
        (df["prediction"] != "D")
    ].copy()

    candidates = candidates.sort_values("confidence", ascending=False)

    print(f"\n  ── ACCA CANDIDATES (conf>=50%, LOW/MED chaos, no upset flag, H/A only) ──")
    if candidates.empty:
        print("  None meeting criteria this week.")
        return

    for _, row in candidates.iterrows():
        home = row["HomeTeam"]
        away = row["AwayTeam"]
        pred = row["prediction"]
        winner = home if pred == "H" else away
        conf = f"{row['confidence']:.0%}"
        chaos = row["chaos_tier"]
        date = row["Date"]
        print(f"  {date}  {home} vs {away}  ->  {winner} ({pred})  {conf}  {chaos}")

    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="EdgeLab Predict — upcoming fixture predictions")
    parser.add_argument("--data",     required=True,
                        help="Folder containing historical CSV data (e.g. data/)")
    parser.add_argument("--fixtures", required=True,
                        help="DataBot output CSV with upcoming fixtures")
    parser.add_argument("--tier",     type=str, default="all",
                        help="Tier to predict: E0/E1/E2/E3/EC/all (default: all)")
    parser.add_argument("--pdf",      action="store_true",
                        help="Also generate a PDF predictions table")
    parser.add_argument("--gary",     action="store_true",
                        help="Run Gary on each fixture after predictions are generated")
    parser.add_argument("--key",      type=str, default=None,
                        help="Anthropic API key for Gary (or set ANTHROPIC_API_KEY env var)")
    args = parser.parse_args()

    print("\n╔══════════════════════════════════════════╗")
    print("║        EdgeLab Predict v1                ║")
    print("╚══════════════════════════════════════════╝")

    run_date = datetime.today().strftime("%Y-%m-%d")

    # Load historical data
    print(f"\n  Loading historical data from: {args.data}")
    df_history = load_all_csvs(args.data)
    print(f"  {len(df_history)} historical matches loaded across "
          f"{df_history['tier'].nunique()} tiers")

    # Load upcoming fixtures
    print(f"\n  Loading upcoming fixtures from: {args.fixtures}")
    df_upcoming = load_upcoming_fixtures(args.fixtures)

    if df_upcoming.empty:
        print("\n  No upcoming fixtures found in that file. Exiting.")
        sys.exit(0)

    # Determine which tiers to run
    available_tiers = sorted(df_upcoming["tier"].unique())
    if args.tier == "all":
        tiers = available_tiers
    else:
        tiers = [t for t in args.tier.split(",") if t in available_tiers]
        if not tiers:
            print(f"\n  No fixtures found for tier '{args.tier}'. "
                  f"Available: {available_tiers}")
            sys.exit(0)

    print(f"\n  Predicting for tiers: {', '.join(tiers)}")
    print(f"  {'='*60}")

    all_predictions = []

    for tier in tiers:
        params = get_engine_params(tier)
        n_upcoming = len(df_upcoming[df_upcoming["tier"] == tier])
        print(f"\n  [{tier}] {n_upcoming} fixtures  |  "
              f"params: w_form={params.w_form:.3f}  home_adv={params.home_adv:.3f}  "
              f"draw_intel={'ON' if params.w_draw_odds > 0 or params.w_h2h_draw > 0 else 'OFF'}")

        preds = predict_upcoming(df_history, df_upcoming, tier, params)

        if preds.empty:
            print(f"  [{tier}] No predictions generated.")
            continue

        all_predictions.append(preds)

    if not all_predictions:
        print("\n  No predictions generated. Exiting.")
        sys.exit(0)

    df_all_preds = pd.concat(all_predictions, ignore_index=True)
    df_all_preds = df_all_preds.sort_values(["Date", "tier"]).reset_index(drop=True)

    # Print full table
    print(f"\n{'='*60}")
    print(f"  PREDICTIONS — {len(df_all_preds)} matches")
    print(f"{'='*60}")
    format_predictions_table(df_all_preds)

    # Acca candidates
    print_acca_candidates(df_all_preds)

    # Summary counts
    pred_counts = df_all_preds["prediction"].value_counts().to_dict()
    upset_count = int(df_all_preds["upset_flag"].sum())
    print(f"  Summary: H={pred_counts.get('H',0)}  D={pred_counts.get('D',0)}  "
          f"A={pred_counts.get('A',0)}  |  Upset flags: {upset_count}")

    # Save CSV
    save_predictions_csv(df_all_preds, run_date)

    print(f"\n  Done. {len(df_all_preds)} predictions saved.\n")

    # ---------------------------------------------------------------------------
    # Gary — optional match-by-match analysis
    # ---------------------------------------------------------------------------
    if args.gary:
        api_key = args.key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("\n  --gary flag set but no API key found.")
            print("  Set ANTHROPIC_API_KEY or pass --key YOUR_KEY\n")
        else:
            print(f"\n{'='*60}")
            print(f"  GARY'S TAKE")
            print(f"{'='*60}")
            print(f"  Initialising Gary's brain (loading historical data)...\n")

            brain = GaryBrain(args.data)
            gary  = Gary(api_key=api_key)

            for _, row in df_all_preds.iterrows():
                home = row["HomeTeam"]
                away = row["AwayTeam"]
                tier = row["tier"]
                date = row.get("Date", run_date)

                # Convert DD/MM/YYYY back to YYYY-MM-DD for brain lookup
                try:
                    match_date = pd.to_datetime(date, dayfirst=True).strftime("%Y-%m-%d")
                except Exception:
                    match_date = run_date

                print(f"\n  ── {tier}  {date}  {home} vs {away}")
                print(f"     Engine: {row.get('prediction','?')}  "
                      f"({row.get('confidence', 0):.0%} conf)  "
                      f"DTI={row.get('dti', 0):.3f}  {row.get('chaos_tier','?')}")
                print(f"  {'─'*58}\n")

                try:
                    engine_block = build_engine_output_block(row)
                    ctx = brain.build_context(
                        home_team=home,
                        away_team=away,
                        match_date=match_date,
                        tier=tier,
                        engine_output=engine_block,
                    )
                    response = gary.ask(ctx)
                    print(f"{response}\n")
                except Exception as e:
                    print(f"  [Gary] Error on {home} vs {away}: {e}\n")


if __name__ == "__main__":
    main()
