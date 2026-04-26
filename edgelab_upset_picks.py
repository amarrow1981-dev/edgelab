#!/usr/bin/env python3
"""
EdgeLab — Gary's Upset Picks
------------------------------
Filters this week's predictions to upset-flagged matches only,
runs Gary on each one, and outputs a screenshot-ready report.

Usage:
    python edgelab_upset_picks.py --data history/ --predictions predictions/2026-04-05_predictions.csv
    python edgelab_upset_picks.py --data history/ --predictions predictions/2026-04-05_predictions.csv --key YOUR_KEY
    python edgelab_upset_picks.py --data history/ --predictions predictions/2026-04-05_predictions.csv --no-gary

Output:
    Terminal — formatted for screenshot
    upset_picks/YYYY-MM-DD_upset_picks.txt — saved copy

Gary's brief on each upset pick focuses on:
  - Why the engine flagged this as upset territory
  - What the market is pricing vs what the engine sees
  - Whether Gary would back the upset or back the favourite
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))

from edgelab_gary_brain import GaryBrain, build_engine_output_block
from edgelab_gary_context import build_gary_prompt
from edgelab_gary import Gary

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)

OUTPUT_DIR = "upset_picks"


# ---------------------------------------------------------------------------
# Load and filter predictions to upset flags only
# ---------------------------------------------------------------------------

def load_upset_picks(predictions_path: str) -> pd.DataFrame:
    """Load predictions CSV and return only upset-flagged rows, sorted by upset_score."""
    df = pd.read_csv(predictions_path)

    if "upset_flag" not in df.columns:
        print("  No upset_flag column found — run predictions with a current engine version.")
        return pd.DataFrame()

    upsets = df[df["upset_flag"] == 1].copy()
    upsets = upsets.sort_values("upset_score", ascending=False).reset_index(drop=True)

    return upsets


# ---------------------------------------------------------------------------
# Format header block — screenshot-ready
# ---------------------------------------------------------------------------

def print_header(run_date: str, n_upsets: int) -> None:
    print()
    print("╔══════════════════════════════════════════════════╗")
    print("║           GARY'S UPSET PICKS                     ║")
    print("║           The favourites Gary doesn't trust       ║")
    print(f"║           {run_date:<38} ║")
    print("╚══════════════════════════════════════════════════╝")
    if n_upsets == 0:
        print("\n  Nothing flagged this week. Gary trusts everything on the sheet.")
    else:
        print(f"\n  {n_upsets} match{'es' if n_upsets != 1 else ''} where the engine smells trouble.\n")


# ---------------------------------------------------------------------------
# Format one upset pick — clean terminal block
# ---------------------------------------------------------------------------

def format_pick_header(row: pd.Series, idx: int) -> str:
    """Return the pick header block as a string."""
    pred = row.get("prediction", "?")
    conf = f"{row.get('confidence', 0):.0%}"
    dti  = f"{row.get('dti', 0):.3f}"
    chaos = row.get("chaos_tier", "?")
    upset_score = f"{row.get('upset_score', 0):.2f}"
    date = row.get("Date", "")
    tier = row.get("tier", "")
    home = row.get("HomeTeam", "")
    away = row.get("AwayTeam", "")
    score = row.get("pred_scoreline", "?-?")

    b365h = row.get("B365H")
    b365a = row.get("B365A")
    odds_str = ""
    if pd.notna(b365h) and pd.notna(b365a):
        odds_str = f"  Odds: H={b365h}  A={b365a}"

    lines = [
        f"  ── Pick {idx} ─────────────────────────────────────────",
        f"  [{tier}]  {date}  {home} vs {away}",
        f"  Engine: {pred}  ({conf} conf)  Score: {score}  DTI={dti}  {chaos}",
        f"  Upset score: {upset_score}  ⚠{odds_str}",
        f"  {'─'*52}",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Build Gary's upset-focused prompt
# ---------------------------------------------------------------------------

UPSET_EXTRA = (
    "This match has been flagged by the engine as upset territory — "
    "high confidence prediction but the data is screaming caution. "
    "Tell me specifically: why does this smell wrong? "
    "Would you back the upset, or do you still trust the favourite? "
    "Keep it tight."
)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Gary's Upset Picks — screenshot-ready report")
    parser.add_argument("--data",        required=True, help="Historical data folder e.g. history/")
    parser.add_argument("--predictions", required=True, help="Predictions CSV from edgelab_predict.py")
    parser.add_argument("--key",         default=None,  help="Anthropic API key (or ANTHROPIC_API_KEY env)")
    parser.add_argument("--no-gary",     action="store_true", help="Skip Gary commentary — just show flags")
    args = parser.parse_args()

    run_date = datetime.today().strftime("%Y-%m-%d")

    # Load upset picks
    if not os.path.exists(args.predictions):
        print(f"\n  File not found: {args.predictions}\n")
        sys.exit(1)

    upsets = load_upset_picks(args.predictions)
    print_header(run_date, len(upsets))

    if upsets.empty:
        sys.exit(0)

    # Gary setup
    use_gary = not args.no_gary
    gary = None
    brain = None

    if use_gary:
        api_key = args.key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("  No API key — running without Gary commentary.")
            print("  Set ANTHROPIC_API_KEY or pass --key YOUR_KEY\n")
            use_gary = False
        else:
            brain = GaryBrain(args.data)
            gary  = Gary(api_key=api_key)

    # Collect output for saving
    output_lines = []
    notes_json = {}  # for HTML generator companion file

    for idx, (_, row) in enumerate(upsets.iterrows(), 1):
        header = format_pick_header(row, idx)
        print(header)
        output_lines.append(header)

        if use_gary:
            home = row["HomeTeam"]
            away = row["AwayTeam"]
            tier = row["tier"]
            date = row.get("Date", run_date)

            try:
                match_date = pd.to_datetime(date, dayfirst=True).strftime("%Y-%m-%d")
            except Exception:
                match_date = run_date

            try:
                engine_block = build_engine_output_block(row)
                ctx = brain.build_context(
                    home_team=home,
                    away_team=away,
                    match_date=match_date,
                    tier=tier,
                    engine_output=engine_block,
                )
                response = gary.ask(ctx, extra=UPSET_EXTRA)
                gary_line = f"\n  Gary:\n\n{response}\n"
                print(gary_line)
                output_lines.append(gary_line)

                # Store for HTML generator JSON
                date_med = pd.to_datetime(date, dayfirst=True).strftime("%-d %b") if sys.platform != "win32" else pd.to_datetime(date, dayfirst=True).strftime("%#d %b")
                note_key = f"{home}_{away}_{date_med}"
                notes_json[note_key] = response

            except Exception as e:
                err = f"  [Gary] Error: {e}\n"
                print(err)
                output_lines.append(err)
        else:
            print()

    # Footer
    footer = (
        f"  ══════════════════════════════════════════════════\n"
        f"  Powered by EdgeLab  |  garyknows.com\n"
        f"  These are not betting tips. This is pattern recognition.\n"
    )
    print(footer)
    output_lines.append(footer)

    # Save to file
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"{run_date}_upset_picks.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))
    print(f"  Saved: {out_path}\n")

    # Save companion JSON for HTML generator — keyed by HomeTeam_AwayTeam_date
    # Only saved if Gary ran (otherwise notes are empty, no point saving)
    if use_gary and notes_json:
        predictions_dir = os.path.dirname(os.path.abspath(args.predictions))
        json_path = os.path.join(predictions_dir, f"{run_date}_upset_notes.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(notes_json, f, ensure_ascii=False, indent=2)
        print(f"  Notes JSON: {json_path}\n")


if __name__ == "__main__":
    main()
