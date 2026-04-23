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


def _lp_to_ep(lp) -> EngineParams:
    """Convert LeagueParams to EngineParams."""
    from edgelab_dpol import LeagueParams
    defaults = LeagueParams()
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
        w_scoreline_agreement=getattr(lp, "w_scoreline_agreement", 0.0),
        w_scoreline_confidence=getattr(lp, "w_scoreline_confidence", 0.0),
        form_window=5,
    )


def get_outcome_params(tier: str):
    """
    Load H, D, A outcome-specific params for a tier.
    Returns dict: {'H': EngineParams, 'D': EngineParams, 'A': EngineParams}
    Falls back to overall evolved params if outcome-specific not saved.
    Falls back to defaults if neither exists.
    """
    from edgelab_config import load_outcome_params
    result = {}
    fallback = get_engine_params(tier)
    for outcome in ("H", "D", "A"):
        lp = load_outcome_params(tier, outcome)
        result[outcome] = _lp_to_ep(lp) if lp is not None else fallback
    return result


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


def predict_upcoming_outcome_routed(
    df_history: pd.DataFrame,
    df_upcoming: pd.DataFrame,
    tier: str,
    outcome_params: dict,
) -> pd.DataFrame:
    """
    Outcome-routed prediction pipeline.

    Runs the full feature pipeline once (using overall evolved params for
    feature computation), then applies H, D, A param sets independently
    to each upcoming fixture. Routes to the final prediction using:

    Decision logic:
      1. Get predictions from H_params, D_params, A_params independently
      2. If D_params call D: check draw_score and odds_draw_prob signal strength
         - If draw evidence is strong (draw_score > 0.3 OR odds_draw_prob > 0.28):
           call D
      3. Otherwise: take H or A — whichever param set calls its own outcome
         with higher confidence
      4. If H_params call H and A_params call A: take higher confidence
      5. If both call same outcome: use that

    Adds columns: pred_H, pred_A, pred_D, conf_H, conf_A, conf_D,
                  outcome_routed (True/False — was routing used?)
    """
    from edgelab_engine import predict_dataframe as _pred_df

    # Use overall params for feature computation (neutral starting point)
    overall_params = get_engine_params(tier)

    df_hist_tier = df_history[df_history["tier"] == tier].copy()
    df_up_tier = df_upcoming[df_upcoming["tier"] == tier].copy()
    if df_up_tier.empty:
        return pd.DataFrame()

    df_hist_tier["_upcoming"] = False
    df_up_tier["_upcoming"] = True
    df_combined = pd.concat([df_hist_tier, df_up_tier], ignore_index=True)
    df_combined = df_combined.sort_values(["parsed_date", "_upcoming"]).reset_index(drop=True)

    # Feature pipeline once
    df_combined = prepare_dataframe(df_combined, overall_params)

    # Extract upcoming rows with features computed
    df_feat = df_combined[df_combined["_upcoming"] == True].copy()
    df_feat = df_feat.drop(columns=["_upcoming"])

    # ── Scoreline profile matching — pre-pass before predict calls ──────────
    # Populate top_scoreline_match_outcome and top_scoreline_match_density on
    # df_feat BEFORE the per-outcome predict_dataframe calls so the engine can
    # read them when w_scoreline_agreement / w_scoreline_confidence are active.
    scoreline_profiles_available = False
    _sdb = None
    try:
        from edgelab_db import EdgeLabDB
        _sdb = EdgeLabDB()
        _profiles_cache = _sdb.get_scoreline_profiles(tier)
        scoreline_profiles_available = len(_profiles_cache) > 0
    except Exception:
        _profiles_cache = {}

    sl_outcomes_col = []
    sl_densities_col = []
    sl_top_col = []

    for _, row in df_feat.iterrows():
        top_scoreline = None
        scoreline_outcome_signal = None
        top_density = 0.5  # neutral fallback

        if scoreline_profiles_available and _sdb is not None:
            try:
                fixture_features = {
                    "home_form": row.get("home_form"),
                    "away_form": row.get("away_form"),
                    "home_gd": row.get("home_gd"),
                    "away_gd": row.get("away_gd"),
                    "dti": row.get("dti"),
                    "home_form_home": row.get("home_form_home"),
                    "away_form_away": row.get("away_form_away"),
                    "home_adv_team": row.get("home_adv_team"),
                    "season_stage": row.get("season_stage"),
                    "rest_days_diff": row.get("rest_days_diff"),
                    "odds_draw_prob": row.get("odds_draw_prob"),
                }
                matches = _sdb.match_fixture_to_scorelines(
                    tier=tier,
                    fixture_features=fixture_features,
                    top_n=3,
                )
                if matches:
                    top_scoreline = matches[0]["scoreline"]
                    top_density = float(matches[0].get("similarity", 0.5))
                    outcomes = [m["outcome"] for m in matches[:2]]
                    if len(set(outcomes)) == 1:
                        scoreline_outcome_signal = outcomes[0]
            except Exception:
                pass

        sl_outcomes_col.append(scoreline_outcome_signal or "")
        sl_densities_col.append(top_density)
        sl_top_col.append(top_scoreline or "")

    df_feat["top_scoreline_match_outcome"]  = sl_outcomes_col
    df_feat["top_scoreline_match_density"]  = sl_densities_col
    # top_scoreline_match (display string) will be finalised after routing

    # ── Per-outcome predictions ──────────────────────────────────────────────
    # df_feat now has top_scoreline_match_outcome and top_scoreline_match_density
    # so predict_dataframe will pick them up for w_scoreline_agreement/confidence.
    for outcome in ("H", "D", "A"):
        p = outcome_params[outcome]
        result = _pred_df(df_feat, p)
        df_feat[f"pred_{outcome}"] = result["prediction"]
        df_feat[f"conf_{outcome}"] = result["confidence"]

    # ── Routing decision — row by row ────────────────────────────────────────
    final_preds = []
    final_confs = []
    routed = []
    top_scorelines = []

    for idx, row in df_feat.iterrows():
        pred_H = row["pred_H"]
        pred_D = row["pred_D"]
        pred_A = row["pred_A"]
        conf_H = row["conf_H"]
        conf_D = row["conf_D"]
        conf_A = row["conf_A"]
        draw_score = row.get("draw_score", 0.0)
        odds_draw = row.get("odds_draw_prob", 0.0)

        top_scoreline = row.get("top_scoreline_match_outcome", "") or ""
        scoreline_outcome_signal = top_scoreline if top_scoreline else None

        # D route — D params call D AND supporting draw evidence
        draw_evidence = (draw_score or 0) > 0.3 or (odds_draw or 0) > 0.28
        # Scoreline signal can also trigger D route
        if scoreline_outcome_signal == "D" and pred_D == "D":
            draw_evidence = True

        if pred_D == "D" and draw_evidence:
            final_preds.append("D")
            final_confs.append(conf_D)
            routed.append(True)
            top_scorelines.append(row.get("top_scoreline_match_outcome", ""))
            continue

        # H/A route — use whichever calls its own outcome with more confidence
        # Scoreline signal can boost confidence for the matching outcome
        h_correct = pred_H == "H"
        a_correct = pred_A == "A"

        # Apply scoreline signal boost
        effective_conf_H = conf_H * 1.1 if (scoreline_outcome_signal == "H" and h_correct) else conf_H
        effective_conf_A = conf_A * 1.1 if (scoreline_outcome_signal == "A" and a_correct) else conf_A

        if h_correct and a_correct:
            if effective_conf_H >= effective_conf_A:
                final_preds.append("H")
                final_confs.append(conf_H)
            else:
                final_preds.append("A")
                final_confs.append(conf_A)
        elif h_correct:
            final_preds.append("H")
            final_confs.append(conf_H)
        elif a_correct:
            final_preds.append("A")
            final_confs.append(conf_A)
        else:
            base_pred = row.get("prediction", "H")
            base_conf = row.get("confidence", 0.5)
            final_preds.append(base_pred)
            final_confs.append(base_conf)

        routed.append(False)
        top_scorelines.append(row.get("top_scoreline_match_outcome", ""))

    df_feat["prediction"] = final_preds
    df_feat["confidence"] = final_confs
    df_feat["outcome_routed"] = routed
    df_feat["top_scoreline_match"] = top_scorelines

    # Recompute upset score with new predictions
    from edgelab_engine import compute_upset_score
    df_feat = compute_upset_score(df_feat)

    return df_feat


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

    # Run full feature pipeline via prepare_dataframe
    # This automatically includes all fixture specificity features (venue-split
    # form, team-specific home advantage, opponent-adjusted form, season stage,
    # rest days) added in Session 38. Using prepare_dataframe ensures predict
    # always stays in sync with engine changes rather than maintaining a
    # duplicate call sequence.
    df_combined = prepare_dataframe(df_combined, params)

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
    """Save predictions to CSV and log to fixture intelligence DB with team_id."""
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
        # Outcome-specific routing (Session 39)
        "pred_H", "pred_D", "pred_A",
        "conf_H", "conf_D", "conf_A",
        "outcome_routed", "top_scoreline_match",
        # Fixture specificity (Session 38)
        "home_form_home", "away_form_away",
        "home_adv_team",
        "home_form_adj", "away_form_adj",
        "season_stage",
        "home_rest_days", "away_rest_days", "rest_days_diff",
    ]
    out_cols = [c for c in cols if c in df.columns]
    df[out_cols].to_csv(path, index=False)
    print(f"  Predictions saved: {path}")

    # Log to fixture intelligence DB with team_id
    _log_predictions_to_db(df, run_date)

    return path


def _log_predictions_to_db(df: pd.DataFrame, run_date: str):
    """
    Write prediction records to edgelab.db at prediction time.
    Includes team_id from the identity layer for cross-source joins.
    Silent — never blocks prediction output if DB write fails.
    """
    try:
        from edgelab_db import EdgeLabDB
        db = EdgeLabDB()

        resolver = None
        try:
            from edgelab_identity import TeamResolver
            resolver = TeamResolver()
        except Exception:
            pass

        written = 0
        for _, row in df.iterrows():
            try:
                tier = str(row.get("tier", ""))
                home = str(row.get("HomeTeam", ""))
                away = str(row.get("AwayTeam", ""))
                date_raw = str(row.get("Date", run_date))
                try:
                    match_date = pd.to_datetime(
                        date_raw, dayfirst=True
                    ).strftime("%Y-%m-%d")
                except Exception:
                    match_date = run_date

                home_team_id = resolver.resolve(home, tier=tier, source="football_data") if resolver else None
                away_team_id = resolver.resolve(away, tier=tier, source="football_data") if resolver else None

                param_version_id = None
                try:
                    pv = db.get_latest_param_version(tier)
                    if pv:
                        param_version_id = pv["version_id"]
                except Exception:
                    pass

                def _f(key, default=0.0):
                    v = row.get(key, default)
                    return float(v) if v is not None else default

                features = {
                    "home_form":      _f("home_form"),
                    "away_form":      _f("away_form"),
                    "home_gd":        _f("home_gd"),
                    "away_gd":        _f("away_gd"),
                    "dti":            _f("dti"),
                    "chaos_tier":     str(row.get("chaos_tier", "MED")),
                    "odds_draw_prob":  _f("odds_draw_prob"),
                    "h2h_draw_rate":   _f("h2h_draw_rate"),
                    "h2h_home_edge":   _f("h2h_home_edge"),
                    "pred_margin":     _f("pred_margin"),
                    "pred_home_goals": _f("pred_home_goals"),
                    "pred_away_goals": _f("pred_away_goals"),
                    "btts_prob":       _f("btts_prob"),
                    "btts_flag":       int(row.get("btts_flag", 0) or 0),
                    "upset_score":     _f("upset_score"),
                    "upset_flag":      int(row.get("upset_flag", 0) or 0),
                    "draw_score":      _f("draw_score"),
                    "weather_load":    _f("weather_load"),
                    "home_form_home":  _f("home_form_home", 0.5),
                    "away_form_away":  _f("away_form_away", 0.5),
                    "home_adv_team":   _f("home_adv_team"),
                    "home_form_adj":   _f("home_form_adj", 0.5),
                    "away_form_adj":   _f("away_form_adj", 0.5),
                    "season_stage":    _f("season_stage", 0.5),
                    "home_rest_days":  _f("home_rest_days", 7.0),
                    "away_rest_days":  _f("away_rest_days", 7.0),
                    "rest_days_diff":  _f("rest_days_diff"),
                }
                if home_team_id:
                    features["home_team_id"] = home_team_id
                if away_team_id:
                    features["away_team_id"] = away_team_id

                db.write_fixture_prematch(
                    tier=tier,
                    season="2025-26",
                    match_date=match_date,
                    home_team=home,
                    away_team=away,
                    prediction=str(row.get("prediction", "?")),
                    confidence=float(row.get("confidence", 0) or 0),
                    pred_scoreline=str(row.get("pred_scoreline", "?-?")),
                    features=features,
                    param_version_id=param_version_id,
                    data_source="predict_live",
                )
                written += 1
            except Exception:
                pass

        if written:
            print(f"  DB: {written} fixtures logged (team_id wired)")
    except Exception:
        pass


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
        outcome_params = get_outcome_params(tier)
        n_upcoming = len(df_upcoming[df_upcoming["tier"] == tier])
        overall_p = get_engine_params(tier)
        print(f"\n  [{tier}] {n_upcoming} fixtures  |  "
              f"outcome-specific routing active  |  "
              f"base: w_form={overall_p.w_form:.3f}  home_adv={overall_p.home_adv:.3f}")

        preds = predict_upcoming_outcome_routed(df_history, df_upcoming, tier, outcome_params)

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
