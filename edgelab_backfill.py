#!/usr/bin/env python3
"""
EdgeLab Backfill
----------------
One-time job. Reads all historical CSVs, runs the full pre-match pipeline,
and writes every fixture into the fixture intelligence database.

After this runs, the 3D map exists. 132,685 completed fixtures —
every pre-match feature vector, every actual outcome. DPOL and Gary
can query this immediately without a single new evolution run.

This also:
  - Saves the current threepass_seed_s28 params as param versions
  - Marks all backfilled fixtures with which param version they belong to
  - Flags discarded params (draw_pull, dti_draw_lock, w_btts) against
    specific fixture clusters — identifies regions where they may still work

Run once. If the dataset changes, run again — existing records are skipped,
only new fixtures are added.

Usage:
    python edgelab_backfill.py --data history/
    python edgelab_backfill.py --data history/ --tier E0
    python edgelab_backfill.py --data history/ --check-discarded
    python edgelab_backfill.py --data history/ --stats
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from edgelab_engine import (
    load_all_csvs,
    compute_form,
    compute_goal_diff,
    compute_dti,
    compute_team_draw_tendency,
    compute_h2h,
    compute_odds_draw_prob,
    compute_score_prediction,
    predict_dataframe,
    compute_upset_score,
    EngineParams,
)
from edgelab_config import load_params
from edgelab_db import EdgeLabDB, PARAM_FIELDS

logging.basicConfig(level=logging.INFO, format="[Backfill] %(message)s")
logger = logging.getLogger(__name__)

BATCH_SIZE = 5000   # write to DB in batches to manage memory


# ---------------------------------------------------------------------------
# Load evolved params for a tier
# ---------------------------------------------------------------------------

def get_engine_params(tier: str) -> EngineParams:
    """Load threepass_seed params for this tier. Falls back to defaults."""
    from edgelab_dpol import LeagueParams
    lp = load_params(tier)
    if lp is None:
        return EngineParams()
    return EngineParams(
        w_form=lp.w_form, w_gd=lp.w_gd, home_adv=lp.home_adv,
        dti_edge_scale=lp.dti_edge_scale, dti_ha_scale=lp.dti_ha_scale,
        draw_margin=lp.draw_margin, coin_dti_thresh=lp.coin_dti_thresh,
        draw_pull=lp.draw_pull, dti_draw_lock=lp.dti_draw_lock,
        w_draw_odds=lp.w_draw_odds, w_draw_tendency=lp.w_draw_tendency,
        w_h2h_draw=lp.w_h2h_draw, draw_score_thresh=lp.draw_score_thresh,
        w_score_margin=lp.w_score_margin, w_btts=lp.w_btts,
        w_ref_signal=getattr(lp, 'w_ref_signal', 0.0),
        w_travel_load=getattr(lp, 'w_travel_load', 0.0),
        w_timing_signal=getattr(lp, 'w_timing_signal', 0.0),
        w_motivation_gap=getattr(lp, 'w_motivation_gap', 0.0),
        w_weather_signal=getattr(lp, 'w_weather_signal', 0.0),
        form_window=5,
    )


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run_pipeline(df: pd.DataFrame, params: EngineParams) -> pd.DataFrame:
    """Run full pre-match feature pipeline + predictions."""
    df = compute_form(df, window=params.form_window)
    df = compute_goal_diff(df, window=params.form_window)
    df = compute_dti(df)
    df = compute_team_draw_tendency(df, window=params.form_window * 2)
    df = compute_h2h(df, window=8)
    df = compute_odds_draw_prob(df)
    df = compute_score_prediction(df, window=params.form_window)

    # Phase 1 signals — graceful fallback if not available
    try:
        from edgelab_signals import compute_phase1_signals
        df = compute_phase1_signals(df)
    except ImportError:
        pass

    # Weather — pre-computed column if present
    if "weather_load" not in df.columns:
        df["weather_load"] = None

    df = predict_dataframe(df, params)
    df = compute_upset_score(df)
    return df


# ---------------------------------------------------------------------------
# Build fixture records from processed dataframe
# ---------------------------------------------------------------------------

def df_to_fixture_records(
    df: pd.DataFrame,
    param_version_id: str,
    data_source: str = "csv_backfill",
) -> List[Dict]:
    """
    Convert a processed dataframe to fixture records ready for bulk insert.
    Only includes rows with known FTR (completed matches).
    """
    records = []

    # Only completed matches
    completed = df[df["FTR"].isin(["H", "D", "A"])].copy()

    for _, row in completed.iterrows():
        tier = str(row.get("tier", ""))
        season = str(row.get("season", ""))
        home = str(row.get("HomeTeam", ""))
        away = str(row.get("AwayTeam", ""))
        prediction = str(row.get("prediction", ""))
        actual = str(row.get("FTR", ""))

        # Parse date
        match_date = ""
        pd_date = row.get("parsed_date")
        if pd_date is not None:
            try:
                match_date = pd.Timestamp(pd_date).strftime("%Y-%m-%d")
            except Exception:
                match_date = str(row.get("Date", ""))

        if not all([tier, season, home, away, match_date, prediction, actual]):
            continue

        correct = 1 if prediction == actual else 0

        # Parse actual goals
        actual_hg = int(row.get("FTHG", 0)) if pd.notna(row.get("FTHG")) else None
        actual_ag = int(row.get("FTAG", 0)) if pd.notna(row.get("FTAG")) else None

        # Feature vector
        def safe(val, default=None):
            try:
                if val is None or (isinstance(val, float) and np.isnan(val)):
                    return default
                return float(val)
            except (TypeError, ValueError):
                return default

        record = {
            "tier": tier,
            "season": season,
            "match_date": match_date,
            "home_team": home,
            "away_team": away,
            "param_version_id": param_version_id,
            "prediction": prediction,
            "confidence": safe(row.get("confidence")),
            "pred_scoreline": str(row.get("pred_scoreline", "")),
            "draw_score": safe(row.get("draw_score")),
            # Pre-match features
            "home_form": safe(row.get("home_form")),
            "away_form": safe(row.get("away_form")),
            "home_gd": safe(row.get("home_gd")),
            "away_gd": safe(row.get("away_gd")),
            "dti": safe(row.get("dti")),
            "chaos_tier": str(row.get("chaos_tier", "")),
            "odds_draw_prob": safe(row.get("odds_draw_prob")),
            "h2h_draw_rate": safe(row.get("h2h_draw_rate")),
            "h2h_home_edge": safe(row.get("h2h_home_edge")),
            "pred_margin": safe(row.get("pred_margin")),
            "pred_home_goals": safe(row.get("pred_home_goals")),
            "pred_away_goals": safe(row.get("pred_away_goals")),
            "btts_prob": safe(row.get("btts_prob")),
            "btts_flag": safe(row.get("btts_flag")),
            "upset_score": safe(row.get("upset_score")),
            "upset_flag": safe(row.get("upset_flag")),
            "weather_load": safe(row.get("weather_load")),
            "travel_load": safe(row.get("travel_load")),
            "motivation_gap": safe(row.get("motivation_gap")),
            "timing_signal": safe(row.get("timing_signal")),
            "ref_signal": safe(row.get("ref_signal")),
            # Post-match (already known for historical data)
            "actual_result": actual,
            "actual_home_goals": actual_hg,
            "actual_away_goals": actual_ag,
            "correct": correct,
            "completed_at": datetime.utcnow().isoformat(),
            "data_source": data_source,
        }
        records.append(record)

    return records


# ---------------------------------------------------------------------------
# Discarded param analysis
# ---------------------------------------------------------------------------

def analyse_discarded_params(db: EdgeLabDB, df_all: pd.DataFrame):
    """
    For each discarded param, test it against the backfilled fixture cloud
    to find regions of the space where it still has signal.

    Discarded params: draw_pull, dti_draw_lock, w_btts
    These were confirmed dead globally — but may be conditionally alive
    in specific regions.

    Prints a report of any clusters where they show positive signal.
    """
    print(f"\n{'='*60}")
    print("  DISCARDED PARAM CLUSTER ANALYSIS")
    print(f"{'='*60}")
    print("  Testing draw_pull, dti_draw_lock, w_btts against")
    print("  backfilled fixture cloud for conditional signal...")
    print()

    discarded = {
        "draw_pull": [0.08, 0.12, 0.15, 0.20],
        "dti_draw_lock": [0.75, 0.80, 0.85, 0.90],
        "w_btts": [0.05, 0.10, 0.15, 0.20],
    }

    # Define regions of the space to test in
    regions = {
        "high_dti": df_all["dti"] >= 0.75,
        "low_dti": df_all["dti"] < 0.50,
        "tight_form": (df_all["home_form"] - df_all["away_form"]).abs() < 0.1,
        "strong_odds_draw": df_all["odds_draw_prob"] >= 0.30 if "odds_draw_prob" in df_all.columns
                            else pd.Series(False, index=df_all.index),
    }

    tiers = sorted(df_all["tier"].unique())

    for param_name, test_values in discarded.items():
        print(f"  — {param_name}")
        findings = []

        for tier in tiers:
            df_tier = df_all[df_all["tier"] == tier].copy()
            if len(df_tier) < 200:
                continue

            base_params = get_engine_params(tier)
            base_ep = EngineParams(**{f: getattr(base_params, f)
                                      for f in EngineParams.__dataclass_fields__
                                      if hasattr(base_params, f)})

            # Baseline accuracy
            from edgelab_engine import predict_dataframe as _pred
            base_preds = _pred(df_tier, base_ep)
            valid = base_preds[base_preds["FTR"].isin(["H", "D", "A"])]
            if len(valid) == 0:
                continue
            base_acc = (valid["prediction"] == valid["FTR"]).mean()

            for val in test_values:
                # Test this param value in each region
                for region_name, region_mask in regions.items():
                    region_tier = df_tier[region_mask.reindex(df_tier.index, fill_value=False)]
                    if len(region_tier) < 50:
                        continue

                    # Build test params with this value
                    import copy
                    from dataclasses import asdict
                    test_params_dict = asdict(base_ep)
                    test_params_dict[param_name] = val
                    test_ep = EngineParams(**test_params_dict)

                    test_preds = _pred(region_tier, test_ep)
                    valid_t = test_preds[test_preds["FTR"].isin(["H", "D", "A"])]
                    if len(valid_t) < 50:
                        continue

                    region_base = base_preds.loc[
                        base_preds.index.isin(valid_t.index)
                    ]
                    region_base_valid = region_base[region_base["FTR"].isin(["H", "D", "A"])]
                    if len(region_base_valid) == 0:
                        continue

                    region_base_acc = (
                        region_base_valid["prediction"] == region_base_valid["FTR"]
                    ).mean()
                    test_acc = (valid_t["prediction"] == valid_t["FTR"]).mean()
                    delta = test_acc - region_base_acc

                    if delta >= 0.005:  # +0.5pp threshold to flag
                        findings.append({
                            "tier": tier,
                            "region": region_name,
                            "value": val,
                            "n": len(valid_t),
                            "base_acc": round(region_base_acc, 4),
                            "test_acc": round(test_acc, 4),
                            "delta": round(delta, 4),
                        })

        if findings:
            findings.sort(key=lambda x: x["delta"], reverse=True)
            print(f"    CONDITIONAL SIGNAL FOUND in {len(findings)} region(s):")
            for f in findings[:5]:
                print(f"    [{f['tier']}] {f['region']:20s} "
                      f"val={f['value']:.2f}  n={f['n']:4d}  "
                      f"{f['base_acc']:.1%} → {f['test_acc']:.1%}  "
                      f"(+{f['delta']:.1%})")
        else:
            print(f"    No conditional signal found — confirmed dead across all regions")
        print()


# ---------------------------------------------------------------------------
# Main backfill
# ---------------------------------------------------------------------------

def run_backfill(
    data_dir: str,
    db_path: str,
    target_tiers: Optional[List[str]] = None,
    check_discarded: bool = False,
):
    print(f"\n{'='*60}")
    print("  EDGELAB BACKFILL — Populating Fixture Intelligence Database")
    print(f"{'='*60}")
    print(f"\n  Data:     {data_dir}")
    print(f"  Database: {db_path}")

    db = EdgeLabDB(db_path=db_path)

    # ── Load all CSVs ────────────────────────────────────────────────────────
    print(f"\n  Loading historical data...")
    try:
        df_all = load_all_csvs(data_dir)
    except FileNotFoundError as e:
        print(f"\n  ERROR: {e}")
        sys.exit(1)

    all_tiers = sorted(df_all["tier"].unique())
    tiers_to_run = (
        [t for t in all_tiers if t in target_tiers]
        if target_tiers else all_tiers
    )

    print(f"  {len(df_all):,} matches loaded across {len(all_tiers)} tiers")
    print(f"  Processing: {', '.join(tiers_to_run)}")

    total_written = 0
    total_skipped = 0

    # ── Process tier by tier ─────────────────────────────────────────────────
    for tier in tiers_to_run:
        df_tier = df_all[df_all["tier"] == tier].copy().reset_index(drop=True)
        n_matches = len(df_tier)

        if n_matches < 100:
            print(f"\n  [{tier}] Skipped — insufficient data ({n_matches} matches)")
            continue

        print(f"\n  [{tier}] {n_matches:,} matches", end=" ", flush=True)

        # Save param version for this tier — read accuracy from params.json
        params = get_engine_params(tier)
        from edgelab_config import load_params as _lp
        import json as _json
        lp = _lp(tier)

        tier_accuracy = 0.0
        tier_matches = n_matches
        tier_source = "threepass_seed_s28"
        params_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "edgelab_params.json"
        )
        if os.path.exists(params_path):
            with open(params_path) as _f:
                _pj = _json.load(_f)
            if tier in _pj:
                tier_accuracy = _pj[tier].get("accuracy", 0.0)
                tier_matches = _pj[tier].get("matches", n_matches)
                tier_source = _pj[tier].get("source", "threepass_seed_s28")

        if lp:
            version_id = db.save_param_version(
                tier=tier,
                params=lp,
                accuracy=tier_accuracy,
                matches=tier_matches,
                source=tier_source,
            )
        else:
            from edgelab_dpol import LeagueParams
            version_id = db.save_param_version(
                tier=tier,
                params=LeagueParams(),
                accuracy=0.0,
                matches=n_matches,
                source="engine_defaults",
            )

        # Run pipeline
        try:
            df_processed = run_pipeline(df_tier, params)
            print(f"→ pipeline done", end=" ", flush=True)
        except Exception as e:
            print(f"→ PIPELINE ERROR: {e}")
            continue

        # Convert to records and bulk write in batches
        records = df_to_fixture_records(df_processed, version_id)
        n_records = len(records)

        written = 0
        for i in range(0, n_records, BATCH_SIZE):
            batch = records[i:i + BATCH_SIZE]
            w = db.bulk_write_fixtures(batch)
            written += w

        skipped = n_records - written
        total_written += written
        total_skipped += skipped

        print(f"→ {written:,} written, {skipped:,} skipped")

    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  BACKFILL COMPLETE")
    print(f"{'='*60}")
    print(f"\n  Written:  {total_written:,} fixture records")
    print(f"  Skipped:  {total_skipped:,} (already existed)")

    stats = db.get_stats()
    print(f"\n  Database now contains:")
    print(f"    {stats['fixtures']['total']:,} fixtures")
    print(f"    {stats['fixtures']['completed']:,} completed")
    print(f"    {stats['param_versions']} param versions")
    if stats['fixtures']['completed']:
        print(f"    Overall accuracy: {stats['fixtures']['accuracy']:.1%}")

    # ── Per-tier breakdown ───────────────────────────────────────────────────
    print(f"\n  {'Tier':<6} {'Fixtures':>10} {'Accuracy':>10}")
    print(f"  {'-'*30}")
    for t in db.get_tier_stats():
        acc = f"{t['accuracy']:.1%}" if t['accuracy'] else "—"
        print(f"  {t['tier']:<6} {t['total']:>10,} {acc:>10}")

    # ── Discarded param analysis ─────────────────────────────────────────────
    if check_discarded:
        print(f"\n  Running discarded param analysis...")
        # Need fully processed data for this
        print("  Loading full processed dataset for analysis...")
        processed_all = []
        for tier in tiers_to_run:
            df_tier = df_all[df_all["tier"] == tier].copy().reset_index(drop=True)
            if len(df_tier) < 100:
                continue
            params = get_engine_params(tier)
            try:
                df_p = run_pipeline(df_tier, params)
                processed_all.append(df_p)
            except Exception:
                continue
        if processed_all:
            df_combined = pd.concat(processed_all, ignore_index=True)
            analyse_discarded_params(db, df_combined)

    print(f"\n  The map exists. DPOL can now navigate rather than wander.\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="EdgeLab Backfill — populate fixture intelligence database"
    )
    parser.add_argument("--data", required=True,
                        help="Path to history/ folder containing CSVs")
    parser.add_argument("--db", default=None,
                        help="Path to database file (default: edgelab.db alongside scripts)")
    parser.add_argument("--tier", type=str, default=None,
                        help="Single tier or comma-separated e.g. E0,E1,N1")
    parser.add_argument("--check-discarded", action="store_true",
                        help="After backfill, analyse discarded params for conditional signal")
    parser.add_argument("--stats", action="store_true",
                        help="Show database stats and exit (no backfill)")
    args = parser.parse_args()

    from edgelab_db import DEFAULT_DB_PATH
    db_path = args.db or DEFAULT_DB_PATH

    if args.stats:
        db = EdgeLabDB(db_path=db_path)
        db_main_args = type('args', (), {'db': db_path, 'stats': True,
                                          'tiers': False, 'similar': None})()
        stats = db.get_stats()
        print(f"\n  Fixtures:  {stats['fixtures']['total']:,}")
        print(f"  Completed: {stats['fixtures']['completed']:,}")
        if stats['fixtures']['completed']:
            print(f"  Accuracy:  {stats['fixtures']['accuracy']:.1%}")
        print(f"  DPOL log:  {stats['dpol_log']['total_candidates']:,} candidates")
        print()
        return

    target_tiers = None
    if args.tier:
        target_tiers = [t.strip().upper() for t in args.tier.split(",")]

    run_backfill(
        data_dir=args.data,
        db_path=db_path,
        target_tiers=target_tiers,
        check_discarded=args.check_discarded,
    )


if __name__ == "__main__":
    main()
