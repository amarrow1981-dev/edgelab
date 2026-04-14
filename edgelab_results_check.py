#!/usr/bin/env python3
"""
EdgeLab Results Checker
-----------------------
Fetches actual results from API-Football, compares against predictions,
and completes fixture records in the fixture intelligence database.

This closes the learning loop:
  1. Predictions written to DB at prediction time (pre-match record)
  2. This script writes actual results back (post-match completion)
  3. DPOL and Gary can now read completed records for pattern learning

Usage:
    python edgelab_results_check.py --key YOUR_API_KEY
    python edgelab_results_check.py --key YOUR_API_KEY --date-from 2026-04-10 --date-to 2026-04-12
    python edgelab_results_check.py --key YOUR_API_KEY --predictions predictions/2026-04-09_predictions.csv
    python edgelab_results_check.py --key YOUR_API_KEY --predictions predictions/2026-04-09_predictions.csv --complete-db

Output:
    Prints comparison table: predicted vs actual, confidence, chaos, correct/wrong.
    Prints accuracy summary broken down by confidence band and chaos tier.
    If --complete-db flag set (or predictions CSV provided), writes results to edgelab.db.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    print("requests not installed. Run: pip install requests --break-system-packages")
    sys.exit(1)

try:
    import pandas as pd
except ImportError:
    pd = None

API_BASE = "https://v3.football.api-sports.io"

LEAGUE_MAP = {
    "E0": 39,  "E1": 40,  "E2": 41,  "E3": 42,  "EC": 43,
    "SP1": 140,"SP2": 141,"D1": 78,  "D2": 79,
    "I1": 135, "I2": 136, "N1": 88,  "B1": 144,
    "SC0": 179,"SC1": 180,"SC2": 181,"SC3": 182,
}

ALL_TIERS = list(LEAGUE_MAP.keys())


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def get_headers(api_key: str) -> dict:
    return {"x-apisports-key": api_key}


def fetch_results_for_league(api_key: str, league_id: int, date_str: str) -> list:
    """Fetch finished fixtures for a league on a given date."""
    url = f"{API_BASE}/fixtures"
    params = {
        "league": league_id,
        "season": 2025,
        "date": date_str,
        "status": "FT",
    }
    resp = requests.get(url, headers=get_headers(api_key), params=params, timeout=15)
    resp.raise_for_status()
    return resp.json().get("response", [])


# ---------------------------------------------------------------------------
# Matching helpers
# ---------------------------------------------------------------------------

def result_from_score(home_goals: int, away_goals: int) -> str:
    if home_goals > away_goals:
        return "H"
    elif away_goals > home_goals:
        return "A"
    return "D"


def normalise(name: str) -> str:
    """Lowercase + strip for fuzzy team name matching."""
    return (name.lower().strip()
            .replace(".", "").replace("-", " ")
            .replace("  ", " "))


def match_teams(api_home: str, api_away: str, pred_home: str, pred_away: str) -> bool:
    """Check if API team names match prediction team names (fuzzy)."""
    ah, aa = normalise(api_home), normalise(api_away)
    ph, pa = normalise(pred_home), normalise(pred_away)
    home_match = (ah in ph or ph in ah or
                  ah[:6] == ph[:6])   # first 6 chars match
    away_match = (aa in pa or pa in aa or
                  aa[:6] == pa[:6])
    return home_match and away_match


# ---------------------------------------------------------------------------
# Prediction loading
# ---------------------------------------------------------------------------

def load_predictions_from_csv(csv_path: str) -> list:
    """
    Load predictions from a predictions CSV file.
    Returns list of dicts with keys: tier, date, home_team, away_team,
    prediction, confidence, chaos_tier, upset_score, upset_flag.
    """
    if pd is None:
        print("pandas not available — cannot load CSV")
        return []

    if not os.path.exists(csv_path):
        print(f"  Predictions file not found: {csv_path}")
        return []

    df = pd.read_csv(csv_path)
    records = []
    for _, row in df.iterrows():
        records.append({
            "tier":        str(row.get("tier", "")),
            "date":        str(row.get("Date", "")),
            "home_team":   str(row.get("HomeTeam", "")),
            "away_team":   str(row.get("AwayTeam", "")),
            "prediction":  str(row.get("prediction", "")),
            "confidence":  float(row.get("confidence", 0)),
            "chaos_tier":  str(row.get("chaos_tier", "")),
            "upset_score": float(row.get("upset_score", 0)),
            "upset_flag":  int(row.get("upset_flag", 0)),
        })
    return records


def match_prediction_from_list(
    api_home: str, api_away: str, tier: str, predictions: list
) -> dict:
    """Find matching prediction from list for an API fixture."""
    for row in predictions:
        if row.get("tier") != tier:
            continue
        if match_teams(api_home, api_away, row["home_team"], row["away_team"]):
            return row
    return None


# ---------------------------------------------------------------------------
# Database completion
# ---------------------------------------------------------------------------

def complete_in_db(
    tier: str, match_date: str, home_team: str, away_team: str,
    actual_result: str, home_goals: int, away_goals: int,
) -> bool:
    """Complete a fixture record in the database. Also completes Gary's call if logged."""
    try:
        from edgelab_db import EdgeLabDB
        db = EdgeLabDB()
        fixture_ok = db.complete_fixture_by_teams(
            tier=tier,
            match_date=match_date,
            home_team=home_team,
            away_team=away_team,
            actual_result=actual_result,
            actual_home_goals=home_goals,
            actual_away_goals=away_goals,
        )
        # Complete Gary's call silently — no error if not logged
        actual_score = f"{home_goals}-{away_goals}"
        try:
            db.complete_gary_call(
                tier=tier,
                match_date=match_date,
                home_team=home_team,
                away_team=away_team,
                actual_result=actual_result,
                actual_score=actual_score,
            )
        except Exception:
            pass
        return fixture_ok
    except Exception as e:
        return False


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def confidence_weight(conf: float) -> int:
    """Weight for weighted accuracy: high conf = 3, med = 2, low = 1."""
    if conf >= 0.80:
        return 3
    elif conf >= 0.50:
        return 2
    return 1


def conf_display(conf: float) -> str:
    """Display confidence as percentage string."""
    if conf <= 1.0:
        return f"{conf:.0%}"
    return f"{int(conf)}%"   # legacy int format


def conf_float(conf) -> float:
    """Normalise confidence to 0-1 float."""
    try:
        c = float(conf)
        return c if c <= 1.0 else c / 100.0
    except (TypeError, ValueError):
        return 0.0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="EdgeLab Results Checker")
    parser.add_argument("--key", required=True, help="API-Football key")
    parser.add_argument("--date-from", default=None,
                        help="Start date YYYY-MM-DD (default: yesterday)")
    parser.add_argument("--date-to", default=None,
                        help="End date YYYY-MM-DD (default: today)")
    parser.add_argument("--predictions", default=None,
                        help="Path to predictions CSV from edgelab_predict.py")
    parser.add_argument("--tiers", default="all",
                        help="Comma-separated tiers to check, or 'all'")
    parser.add_argument("--complete-db", action="store_true",
                        help="Write results back to fixture intelligence database")
    parser.add_argument("--no-db", action="store_true",
                        help="Skip database completion even if predictions CSV provided")
    args = parser.parse_args()

    # Date range
    today = datetime.utcnow().date()
    if args.date_from:
        from_dt = datetime.strptime(args.date_from, "%Y-%m-%d").date()
    else:
        from_dt = today - timedelta(days=1)

    if args.date_to:
        to_dt = datetime.strptime(args.date_to, "%Y-%m-%d").date()
    else:
        to_dt = today

    dates = []
    d = from_dt
    while d <= to_dt:
        dates.append(d.strftime("%Y-%m-%d"))
        d += timedelta(days=1)

    # Tiers
    if args.tiers == "all":
        tiers_to_check = ALL_TIERS
    else:
        tiers_to_check = [t.strip().upper() for t in args.tiers.split(",")]

    # Predictions
    predictions = []
    write_to_db = False

    if args.predictions:
        predictions = load_predictions_from_csv(args.predictions)
        print(f"\n  Loaded {len(predictions)} predictions from {os.path.basename(args.predictions)}")
        write_to_db = not args.no_db
        if write_to_db:
            print("  DB completion: ON — results will be written to edgelab.db")
    elif args.complete_db:
        write_to_db = True
        print("  DB completion: ON (no predictions CSV — will log results only)")

    print(f"\n  Fetching results: {args.date_from or from_dt} -> {args.date_to or to_dt}")
    print(f"  Tiers: {', '.join(tiers_to_check)}\n")

    # Fetch and match
    all_results = []
    db_completed = 0
    db_failed = 0

    for tier in tiers_to_check:
        league_id = LEAGUE_MAP.get(tier)
        if not league_id:
            continue

        for date_str in dates:
            try:
                fixtures = fetch_results_for_league(args.key, league_id, date_str)
                time.sleep(0.35)  # rate limit

                for fix in fixtures:
                    home = fix["teams"]["home"]["name"]
                    away = fix["teams"]["away"]["name"]
                    hg = fix["goals"]["home"]
                    ag = fix["goals"]["away"]

                    if hg is None or ag is None:
                        continue

                    actual = result_from_score(hg, ag)
                    score_str = f"{hg}-{ag}"

                    # Match against predictions if we have them
                    pred_row = None
                    if predictions:
                        pred_row = match_prediction_from_list(
                            home, away, tier, predictions
                        )

                    # Complete in DB
                    if write_to_db:
                        completed = complete_in_db(
                            tier=tier,
                            match_date=date_str,
                            home_team=home,
                            away_team=away,
                            actual_result=actual,
                            home_goals=hg,
                            away_goals=ag,
                        )
                        if completed:
                            db_completed += 1
                        else:
                            db_failed += 1

                    # Silent side effect — write completed result to harvester DB.
                    # Closes the loop: DataBot writes fixture pre-match,
                    # results_check writes the completed result post-match.
                    # No extra API calls. Same data, second destination.
                    try:
                        from edgelab_merge import write_match_to_harvester
                        from edgelab_databot import apply_name_map
                        write_match_to_harvester(
                            db_path="harvester_football.db",
                            sport="football",
                            tier=tier,
                            season=2025,
                            match_date=date_str,
                            home_team=apply_name_map(home),
                            away_team=apply_name_map(away),
                            home_goals=hg,
                            away_goals=ag,
                            status="FT",
                            league_id=LEAGUE_MAP.get(tier),
                        )
                    except Exception:
                        pass  # harvester write is best-effort — never blocks results_check

                    if pred_row:
                        pred = pred_row["prediction"]
                        conf = conf_float(pred_row["confidence"])
                        chaos = pred_row["chaos_tier"]
                        upset = float(pred_row.get("upset_score", 0))
                        correct = (pred == actual)

                        all_results.append({
                            "home": home,
                            "away": away,
                            "tier": tier,
                            "date": date_str,
                            "pred": pred,
                            "actual": actual,
                            "score": score_str,
                            "conf": conf,
                            "chaos": chaos,
                            "upset": upset,
                            "correct": correct,
                        })

            except Exception as e:
                print(f"  [!] {tier} {date_str}: {e}")

    # DB completion summary
    if write_to_db:
        print(f"\n  Database: {db_completed} fixtures completed, {db_failed} not found in DB")

    if not all_results:
        if predictions:
            print("\n  No matched results found. Check team name mapping or date range.")
        else:
            print("\n  No predictions loaded — showing raw results only.")
            print("  Pass --predictions path/to/predictions.csv to see match comparison.")
        return

    # ── Output table ─────────────────────────────────────────────────────────
    print(f"\n{'='*105}")
    print(f"  RESULTS — {len(all_results)} matched predictions")
    print(f"{'='*105}")
    print(f"  {'Home':<24} {'Away':<24} {'Tier':<5} {'Pred':>4} {'Act':>4} "
          f"{'Score':>6} {'Conf':>6} {'Chaos':>6} {'Upset':>6}  {'✓?':>3}")
    print(f"  {'-'*100}")

    # Sort: wrong high-conf first — most interesting failures at top
    sorted_results = sorted(all_results, key=lambda r: (-r["conf"], r["correct"]))

    correct_count = 0
    weighted_correct = 0
    weighted_total = 0

    bands = {
        "high":  {"correct": 0, "total": 0},  # conf >= 0.80
        "med":   {"correct": 0, "total": 0},  # conf 0.50-0.79
        "low":   {"correct": 0, "total": 0},  # conf < 0.50
    }
    chaos_buckets = {
        "LOW":  {"correct": 0, "total": 0},
        "MED":  {"correct": 0, "total": 0},
        "HIGH": {"correct": 0, "total": 0},
    }
    upset_flag_results = {"correct": 0, "total": 0}

    for r in sorted_results:
        mark = "✓" if r["correct"] else "✗"
        upset_str = f"{r['upset']:.2f}" if r["upset"] else "  —  "
        flag = " ⚠" if r["upset"] >= 0.5 else ""

        print(f"  {r['home']:<24} {r['away']:<24} {r['tier']:<5} "
              f"{r['pred']:>4} {r['actual']:>4} {r['score']:>6} "
              f"{conf_display(r['conf']):>6} {r['chaos']:>6} {upset_str:>6}  "
              f"{mark}{flag}")

        w = confidence_weight(r["conf"])
        weighted_total += w
        if r["correct"]:
            correct_count += 1
            weighted_correct += w

        # Confidence bands
        if r["conf"] >= 0.80:
            bands["high"]["total"] += 1
            if r["correct"]: bands["high"]["correct"] += 1
        elif r["conf"] >= 0.50:
            bands["med"]["total"] += 1
            if r["correct"]: bands["med"]["correct"] += 1
        else:
            bands["low"]["total"] += 1
            if r["correct"]: bands["low"]["correct"] += 1

        # Chaos buckets
        ch = r["chaos"]
        if ch in chaos_buckets:
            chaos_buckets[ch]["total"] += 1
            if r["correct"]: chaos_buckets[ch]["correct"] += 1

        # Upset flag
        if r["upset"] >= 0.5:
            upset_flag_results["total"] += 1
            if r["correct"]: upset_flag_results["correct"] += 1

    total = len(all_results)

    print(f"\n{'='*105}")
    print(f"\n  OVERALL:           {correct_count}/{total}  "
          f"({100*correct_count/total:.1f}%)")
    print(f"  WEIGHTED:          {weighted_correct}/{weighted_total}  "
          f"({100*weighted_correct/weighted_total:.1f}%)")

    print(f"\n  BY CONFIDENCE:")
    for band, label in [("high", "HIGH (≥80%)  "),
                         ("med",  "MED (50-79%) "),
                         ("low",  "LOW (<50%)   ")]:
        b = bands[band]
        if b["total"]:
            pct = 100 * b["correct"] / b["total"]
            print(f"    {label}  {b['correct']}/{b['total']}  ({pct:.1f}%)")

    print(f"\n  BY CHAOS TIER:")
    for ch in ["LOW", "MED", "HIGH"]:
        b = chaos_buckets[ch]
        if b["total"]:
            pct = 100 * b["correct"] / b["total"]
            print(f"    {ch:<6}  {b['correct']}/{b['total']}  ({pct:.1f}%)")

    if upset_flag_results["total"]:
        b = upset_flag_results
        pct = 100 * b["correct"] / b["total"]
        print(f"\n  UPSET FLAGGED:     {b['correct']}/{b['total']}  ({pct:.1f}%)")
        if pct < 40:
            print(f"    -> Upset flags firing correctly — these are genuine volatility signals")

    # Notable misses — high conf, wrong
    notable = [r for r in all_results if not r["correct"] and r["conf"] >= 0.80]
    if notable:
        print(f"\n  NOTABLE MISSES (conf ≥80%, wrong):")
        for r in sorted(notable, key=lambda x: -x["conf"]):
            print(f"    [{r['tier']}] {r['home']} vs {r['away']}  "
                  f"-> predicted {r['pred']}, actual {r['actual']} ({r['score']})  "
                  f"conf={conf_display(r['conf'])}  chaos={r['chaos']}  "
                  f"upset={r['upset']:.2f}")

    print()


if __name__ == "__main__":
    main()
