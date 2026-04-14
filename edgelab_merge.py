#!/usr/bin/env python3
"""
EdgeLab Merge Tool
------------------
Converts harvester_football.db -> football-data.co.uk CSV format -> history/

Bridges the gap between the API-Football harvester database and the CSV
dataset the engine reads. Run once to backfill, then after each daily harvest.

What it does:
  1. Reads all completed matches from harvester_football.db
  2. Translates API-Football team names to football-data.co.uk names
     using TEAM_NAME_MAP from edgelab_databot.py
  3. Groups matches by tier + season
  4. For each tier/season group:
     - Checks if a CSV already exists in history/
     - If it exists: appends only new rows (by match date + teams)
     - If it doesn't: creates a new CSV in the correct format
  5. Reports what was written, what was skipped

Design principles:
  - Never overwrites existing rows — append-only, safe to run repeatedly
  - Skips any match without a completed result (status != FT)
  - Uses the same CSV column format as football-data.co.uk exactly
  - Only touches football — other sports are separate

Usage:
    python edgelab_merge.py
    python edgelab_merge.py --harvester-db harvester_football.db --history-dir history/
    python edgelab_merge.py --dry-run        # show what would be written, don't write
    python edgelab_merge.py --tier E0        # merge a single tier only
    python edgelab_merge.py --status         # show counts without merging
"""

import argparse
import logging
import os
import sqlite3
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from edgelab_databot import TEAM_NAME_MAP, apply_name_map

logging.basicConfig(level=logging.INFO, format="[Merge] %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_HARVESTER_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "harvester_football.db")
DEFAULT_HISTORY_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "history")

# football-data.co.uk CSV columns — this is the exact format the engine expects
CSV_COLUMNS = ["Div", "Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"]

# Season label format: API uses start year integer (e.g. 2024 = 2024/25)
# football-data.co.uk filename format: E0_2024-25.csv (for season 2024)
# We derive the filename from tier + season

def season_label(season_int: int) -> str:
    """Convert API season integer to football-data.co.uk filename label.
    e.g. 2024 -> '2024-25', 2000 -> '2000-01'
    """
    next_year = (season_int + 1) % 100
    return f"{season_int}-{next_year:02d}"


def csv_filename(tier: str, season_int: int) -> str:
    """e.g. tier='E0', season=2024 -> 'E0_2024-25.csv'"""
    return f"{tier}_{season_label(season_int)}.csv"


def match_date_to_uk_format(date_str: str) -> str:
    """Convert YYYY-MM-DD to DD/MM/YYYY (football-data.co.uk format)."""
    try:
        dt = pd.to_datetime(date_str)
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return date_str


def result_from_goals(home_goals: Optional[int],
                      away_goals: Optional[int]) -> Optional[str]:
    """Derive H/D/A from goals. Returns None if goals are missing."""
    if home_goals is None or away_goals is None:
        return None
    if home_goals > away_goals:
        return "H"
    elif away_goals > home_goals:
        return "A"
    return "D"


# ---------------------------------------------------------------------------
# Load harvester DB
# ---------------------------------------------------------------------------

def load_harvester_matches(db_path: str,
                            tier: Optional[str] = None) -> pd.DataFrame:
    """
    Load all completed football matches from harvester_football.db.
    Returns DataFrame with standardised columns.
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Harvester DB not found: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    query = """
        SELECT league_code, season, match_date, home_team, away_team,
               home_goals, away_goals, result, status
        FROM raw_matches
        WHERE sport = 'football'
          AND status = 'FT'
          AND result IS NOT NULL
          AND home_goals IS NOT NULL
          AND away_goals IS NOT NULL
    """
    if tier:
        query += f" AND league_code = '{tier}'"

    rows = conn.execute(query).fetchall()
    conn.close()

    if not rows:
        return pd.DataFrame()

    records = []
    for row in rows:
        records.append({
            "tier":        row["league_code"],
            "season":      int(row["season"]),
            "match_date":  row["match_date"],        # YYYY-MM-DD
            "home_team":   row["home_team"],          # API-Football name
            "away_team":   row["away_team"],          # API-Football name
            "home_goals":  int(row["home_goals"]),
            "away_goals":  int(row["away_goals"]),
            "result":      row["result"],             # H / D / A
        })

    df = pd.DataFrame(records)
    df["parsed_date"] = pd.to_datetime(df["match_date"], errors="coerce")
    df = df.dropna(subset=["parsed_date"])
    df = df.sort_values(["tier", "season", "parsed_date"]).reset_index(drop=True)

    logger.info(f"Loaded {len(df):,} completed matches from harvester DB")
    return df


# ---------------------------------------------------------------------------
# Load existing CSV for a tier/season (if it exists)
# ---------------------------------------------------------------------------

def load_existing_csv(history_dir: str, tier: str,
                      season_int: int) -> Optional[pd.DataFrame]:
    """
    Load an existing history/ CSV for this tier/season.
    Returns None if the file doesn't exist.
    Returns DataFrame with a 'match_key' column for deduplication.
    """
    filename = csv_filename(tier, season_int)
    path = os.path.join(history_dir, filename)

    if not os.path.exists(path):
        return None

    try:
        for enc in ("utf-8-sig", "latin-1", "cp1252"):
            try:
                df = pd.read_csv(path, encoding=enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            logger.warning(f"Could not decode {filename} — skipping")
            return None

        if "HomeTeam" not in df.columns or "AwayTeam" not in df.columns:
            return None

        # Build dedup key: date + home + away (normalised)
        df["match_key"] = (
            df["Date"].astype(str).str.strip() + "_" +
            df["HomeTeam"].astype(str).str.strip().str.lower() + "_" +
            df["AwayTeam"].astype(str).str.strip().str.lower()
        )
        return df

    except Exception as e:
        logger.warning(f"Could not load {filename}: {e}")
        return None


# ---------------------------------------------------------------------------
# Build new rows for a CSV
# ---------------------------------------------------------------------------

def build_new_rows(harvester_rows: pd.DataFrame,
                   existing_df: Optional[pd.DataFrame]) -> pd.DataFrame:
    """
    From harvester rows, filter out any that already exist in the CSV.
    Translate team names and return rows ready to append.
    """
    # Build set of existing match keys for fast dedup
    existing_keys = set()
    if existing_df is not None and "match_key" in existing_df.columns:
        existing_keys = set(existing_df["match_key"].dropna())

    new_rows = []
    for _, row in harvester_rows.iterrows():
        # Translate team names
        home = apply_name_map(str(row["home_team"]))
        away = apply_name_map(str(row["away_team"]))
        date_uk = match_date_to_uk_format(row["match_date"])

        # Build dedup key
        key = f"{date_uk}_{home.strip().lower()}_{away.strip().lower()}"
        if key in existing_keys:
            continue

        new_rows.append({
            "Div":      row["tier"],
            "Date":     date_uk,
            "HomeTeam": home,
            "AwayTeam": away,
            "FTHG":     int(row["home_goals"]),
            "FTAG":     int(row["away_goals"]),
            "FTR":      row["result"],
        })

    if not new_rows:
        return pd.DataFrame(columns=CSV_COLUMNS)

    df = pd.DataFrame(new_rows, columns=CSV_COLUMNS)
    df = df.sort_values("Date").reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# Write to CSV
# ---------------------------------------------------------------------------

def write_to_csv(history_dir: str, tier: str, season_int: int,
                 new_rows: pd.DataFrame,
                 existing_df: Optional[pd.DataFrame],
                 dry_run: bool = False) -> int:
    """
    Write new rows to the CSV file for this tier/season.
    Creates the file if it doesn't exist, appends if it does.
    Returns number of rows written.
    """
    if new_rows.empty:
        return 0

    filename = csv_filename(tier, season_int)
    path = os.path.join(history_dir, filename)

    if dry_run:
        logger.info(f"  [DRY RUN] Would write {len(new_rows)} rows to {filename}")
        return len(new_rows)

    os.makedirs(history_dir, exist_ok=True)

    if existing_df is not None:
        # Append to existing — drop our dedup key column first
        existing_clean = existing_df.drop(
            columns=["match_key"], errors="ignore"
        )
        # Only keep CSV_COLUMNS that exist in the existing file
        existing_cols = [c for c in CSV_COLUMNS if c in existing_clean.columns]
        # Ensure new_rows has same columns
        combined = pd.concat(
            [existing_clean[existing_cols],
             new_rows[existing_cols]],
            ignore_index=True
        )
        # Re-sort by date
        try:
            combined["_sort"] = pd.to_datetime(
                combined["Date"], dayfirst=True, errors="coerce"
            )
            combined = combined.sort_values("_sort").drop(
                columns=["_sort"]
            ).reset_index(drop=True)
        except Exception:
            pass
        combined.to_csv(path, index=False)
    else:
        # New file
        new_rows.to_csv(path, index=False)

    return len(new_rows)


# ---------------------------------------------------------------------------
# Write a single match to harvester_football.db
# Called by DataBot and results_check as a side effect
# ---------------------------------------------------------------------------

def write_match_to_harvester(
    db_path: str,
    sport: str,
    tier: str,
    season: int,
    match_date: str,       # YYYY-MM-DD
    home_team: str,
    away_team: str,
    home_goals: Optional[int],
    away_goals: Optional[int],
    status: str,           # FT / NS / etc
    fixture_id: Optional[int] = None,
    league_id: Optional[int] = None,
    league_name: Optional[str] = None,
    country: Optional[str] = None,
) -> bool:
    """
    Write a single match record to harvester_football.db.
    Called automatically by DataBot (upcoming fixtures) and
    results_check (completed results) as a silent side effect.

    Returns True if written, False if already existed or on error.
    """
    if not os.path.exists(db_path):
        # DB doesn't exist yet — create it
        try:
            from edgelab_harvester import init_db
            conn = init_db(db_path)
            conn.close()
        except Exception as e:
            logger.warning(f"Could not initialise harvester DB: {e}")
            return False

    result = result_from_goals(home_goals, away_goals) if status == "FT" else None

    # Build match_id consistent with harvester format
    fx_id_str = str(fixture_id) if fixture_id else f"{match_date}_{home_team}_{away_team}"
    match_id = f"football_{tier}_{season}_{fx_id_str}"

    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA journal_mode=WAL")

        existing = conn.execute(
            "SELECT 1 FROM raw_matches WHERE match_id = ?", (match_id,)
        ).fetchone()

        if existing:
            # Update result/status if it's now completed and wasn't before
            if status == "FT" and result:
                conn.execute("""
                    UPDATE raw_matches
                    SET home_goals=?, away_goals=?, result=?, status=?
                    WHERE match_id=?
                """, (home_goals, away_goals, result, status, match_id))
                conn.commit()
            conn.close()
            return False  # already existed

        conn.execute("""
            INSERT INTO raw_matches
            (match_id, sport, league_code, league_id, league_name, country,
             season, match_date, home_team, away_team,
             home_goals, away_goals, result, status, raw_json, fetched_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            match_id, sport, tier, league_id, league_name, country,
            season, match_date, home_team, away_team,
            home_goals, away_goals, result, status,
            None,  # no raw_json for databot/results writes
            pd.Timestamp.utcnow().isoformat(),
        ))
        conn.commit()
        conn.close()
        return True

    except Exception as e:
        logger.warning(f"Could not write match to harvester DB: {e}")
        return False


# ---------------------------------------------------------------------------
# Main merge
# ---------------------------------------------------------------------------

def run_merge(
    harvester_db: str = DEFAULT_HARVESTER_DB,
    history_dir: str = DEFAULT_HISTORY_DIR,
    target_tier: Optional[str] = None,
    dry_run: bool = False,
    status_only: bool = False,
):
    print(f"\n{'='*60}")
    print(f"  EdgeLab Merge — Harvester DB -> history/ CSVs")
    print(f"{'='*60}")
    print(f"\n  Harvester DB : {harvester_db}")
    print(f"  History dir  : {history_dir}")
    if dry_run:
        print(f"  Mode         : DRY RUN — no files will be written")
    if target_tier:
        print(f"  Tier filter  : {target_tier}")

    # Load harvester matches
    try:
        df_harvester = load_harvester_matches(harvester_db, tier=target_tier)
    except FileNotFoundError as e:
        print(f"\n  ERROR: {e}")
        sys.exit(1)

    if df_harvester.empty:
        print(f"\n  No completed matches in harvester DB. Nothing to merge.")
        return

    # Status report
    tier_season_counts = df_harvester.groupby(
        ["tier", "season"]
    ).size().reset_index(name="count")
    print(f"\n  Harvester matches available: {len(df_harvester):,}")
    print(f"  Tier/season combos: {len(tier_season_counts)}")

    if status_only:
        print(f"\n  {'Tier':<6} {'Season':>8} {'Matches':>10}")
        print(f"  {'-'*28}")
        for _, row in tier_season_counts.iterrows():
            print(f"  {row['tier']:<6} {row['season']:>8} {row['count']:>10,}")
        return

    # Process tier by tier, season by season
    total_written = 0
    total_skipped = 0
    files_created = 0
    files_updated = 0

    for _, ts_row in tier_season_counts.iterrows():
        tier     = ts_row["tier"]
        season   = int(ts_row["season"])
        filename = csv_filename(tier, season)

        # Get harvester rows for this tier/season
        mask = (df_harvester["tier"] == tier) & (df_harvester["season"] == season)
        harvester_subset = df_harvester[mask]

        # Load existing CSV if present
        existing_df = load_existing_csv(history_dir, tier, season)
        is_new = existing_df is None

        # Build new rows (after dedup against existing)
        new_rows = build_new_rows(harvester_subset, existing_df)

        if new_rows.empty:
            total_skipped += len(harvester_subset)
            continue

        # Write
        written = write_to_csv(
            history_dir, tier, season, new_rows, existing_df, dry_run=dry_run
        )
        total_written += written
        if written > 0:
            if is_new:
                files_created += 1
                print(f"  [NEW]     {filename:<30} {written:>5} rows written")
            else:
                files_updated += 1
                print(f"  [UPDATED] {filename:<30} {written:>5} rows appended")

        total_skipped += len(harvester_subset) - written

    print(f"\n{'='*60}")
    print(f"  MERGE COMPLETE")
    print(f"{'='*60}")
    print(f"\n  Rows written : {total_written:,}")
    print(f"  Rows skipped : {total_skipped:,}  (already in CSV)")
    print(f"  Files created: {files_created}")
    print(f"  Files updated: {files_updated}")

    if not dry_run and total_written > 0:
        print(f"\n  history/ now contains the merged dataset.")
        print(f"  Run three-pass or DPOL to use the expanded data.")
    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="EdgeLab Merge — harvester DB to history/ CSVs"
    )
    parser.add_argument("--harvester-db", default=DEFAULT_HARVESTER_DB,
                        help="Path to harvester_football.db")
    parser.add_argument("--history-dir", default=DEFAULT_HISTORY_DIR,
                        help="Path to history/ folder")
    parser.add_argument("--tier", type=str, default=None,
                        help="Merge a single tier only e.g. E0")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be written without writing")
    parser.add_argument("--status", action="store_true",
                        help="Show available data without merging")
    args = parser.parse_args()

    run_merge(
        harvester_db=args.harvester_db,
        history_dir=args.history_dir,
        target_tier=args.tier,
        dry_run=args.dry_run,
        status_only=args.status,
    )


if __name__ == "__main__":
    main()
