#!/usr/bin/env python3
"""
EdgeLab Weather Wire
--------------------
One-time job. Reads weather_cache.csv and backfills weather_load values
into the fixtures table in edgelab.db.

Match key format in cache: YYYY-MM-DD_HomeTeam_tier
Joins on: match_date + home_team + tier

Safe to run multiple times — only updates rows where weather_load is NULL
unless --overwrite flag is set.

Usage:
    python edgelab_weather_wire.py
    python edgelab_weather_wire.py --cache weather_cache.csv --db edgelab.db
    python edgelab_weather_wire.py --overwrite   # update all rows, not just nulls
    python edgelab_weather_wire.py --dry-run     # show stats without writing
"""

import argparse
import os
import sys
import sqlite3

import pandas as pd

DEFAULT_CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weather_cache.csv")
DEFAULT_DB    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "edgelab.db")


def parse_key(key: str):
    """Returns (date_str, home_team, tier) from YYYY-MM-DD_HomeTeam_tier."""
    parts = key.split("_")
    date_str  = parts[0]
    tier      = parts[-1]
    home_team = "_".join(parts[1:-1])
    return date_str, home_team, tier


def main():
    parser = argparse.ArgumentParser(description="Wire weather_cache.csv into edgelab.db")
    parser.add_argument("--cache",     default=DEFAULT_CACHE, help="Path to weather_cache.csv")
    parser.add_argument("--db",        default=DEFAULT_DB,    help="Path to edgelab.db")
    parser.add_argument("--overwrite", action="store_true",   help="Update all rows, not just NULLs")
    parser.add_argument("--dry-run",   action="store_true",   help="Show stats only, no writes")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  EdgeLab Weather Wire")
    print(f"{'='*60}")
    print(f"  Cache : {args.cache}")
    print(f"  DB    : {args.db}")
    if args.dry_run:
        print(f"  Mode  : DRY RUN — no changes will be made")
    elif args.overwrite:
        print(f"  Mode  : OVERWRITE — updating all rows")
    else:
        print(f"  Mode  : NULL FILL — only updating rows with no weather data")

    # ── Load cache ────────────────────────────────────────────────────────────
    if not os.path.exists(args.cache):
        print(f"\n  ERROR: Cache not found at {args.cache}")
        sys.exit(1)

    print(f"\n  Loading weather cache...")
    df = pd.read_csv(args.cache)
    total_cache  = len(df)
    populated    = df["weather_load"].notna().sum()
    coverage_pct = populated / total_cache * 100

    print(f"  Total rows   : {total_cache:,}")
    print(f"  Populated    : {populated:,} ({coverage_pct:.1f}%)")
    print(f"  Null rows    : {total_cache - populated:,}")

    # Only work with populated rows
    df_populated = df[df["weather_load"].notna()].copy()
    print(f"\n  Using {len(df_populated):,} rows with weather data for wiring...")

    # Parse match keys
    parsed = df_populated["match_key"].apply(parse_key)
    df_populated = df_populated.copy()
    df_populated["match_date"] = parsed.apply(lambda x: x[0])
    df_populated["home_team"]  = parsed.apply(lambda x: x[1])
    df_populated["tier"]       = parsed.apply(lambda x: x[2])

    # ── Connect to DB ─────────────────────────────────────────────────────────
    if not os.path.exists(args.db):
        print(f"\n  ERROR: Database not found at {args.db}")
        sys.exit(1)

    conn = sqlite3.connect(args.db)
    conn.execute("PRAGMA journal_mode=WAL")

    # Check current state
    cursor = conn.execute("SELECT COUNT(*) FROM fixtures")
    total_fixtures = cursor.fetchone()[0]
    cursor = conn.execute("SELECT COUNT(*) FROM fixtures WHERE weather_load IS NOT NULL")
    already_wired  = cursor.fetchone()[0]
    cursor = conn.execute("SELECT COUNT(*) FROM fixtures WHERE weather_load IS NULL")
    null_fixtures  = cursor.fetchone()[0]

    print(f"\n  Database state:")
    print(f"  Total fixtures    : {total_fixtures:,}")
    print(f"  Already wired     : {already_wired:,}")
    print(f"  Null weather_load : {null_fixtures:,}")

    if args.dry_run:
        # Estimate matches
        sample_keys = set(zip(df_populated["match_date"], df_populated["home_team"], df_populated["tier"]))
        cursor = conn.execute("SELECT match_date, home_team, tier FROM fixtures WHERE weather_load IS NULL LIMIT 50000")
        db_null_rows = cursor.fetchall()
        db_keys = set((r[0], r[1], r[2]) for r in db_null_rows)
        estimated_matches = len(sample_keys & db_keys)
        print(f"\n  DRY RUN estimate  : ~{estimated_matches:,} fixtures would be updated")
        conn.close()
        print(f"\n  Dry run complete. Run without --dry-run to apply.\n")
        return

    # ── Wire weather ─────────────────────────────────────────────────────────
    print(f"\n  Wiring weather data...")

    updated   = 0
    not_found = 0

    # Build lookup dict from cache for fast access
    weather_lookup = {}
    for _, row in df_populated.iterrows():
        key = (row["match_date"], row["home_team"], row["tier"])
        weather_lookup[key] = float(row["weather_load"])

    # Fetch fixtures that need updating
    if args.overwrite:
        cursor = conn.execute("SELECT fixture_id, match_date, home_team, tier FROM fixtures")
    else:
        cursor = conn.execute(
            "SELECT fixture_id, match_date, home_team, tier FROM fixtures WHERE weather_load IS NULL"
        )

    rows_to_update = cursor.fetchall()
    total_to_update = len(rows_to_update)
    print(f"  Fixtures to process: {total_to_update:,}")

    BATCH_SIZE = 1000
    batch = []

    for i, row in enumerate(rows_to_update):
        fixture_id, match_date, home_team, tier = row
        key = (match_date, home_team, tier)

        if key in weather_lookup:
            batch.append((weather_lookup[key], fixture_id))
            updated += 1
        else:
            not_found += 1

        # Write in batches
        if len(batch) >= BATCH_SIZE:
            conn.executemany(
                "UPDATE fixtures SET weather_load = ? WHERE fixture_id = ?",
                batch
            )
            conn.commit()
            batch = []

        if (i + 1) % 10000 == 0:
            pct = (i + 1) / total_to_update * 100
            print(f"  [{pct:5.1f}%] Processed {i+1:,}/{total_to_update:,}  "
                  f"updated={updated:,}  not_found={not_found:,}")

    # Final batch
    if batch:
        conn.executemany(
            "UPDATE fixtures SET weather_load = ? WHERE fixture_id = ?",
            batch
        )
        conn.commit()

    conn.close()

    # ── Summary ───────────────────────────────────────────────────────────────
    match_rate = updated / total_to_update * 100 if total_to_update else 0

    print(f"\n{'='*60}")
    print(f"  WIRE COMPLETE")
    print(f"{'='*60}")
    print(f"  Fixtures processed : {total_to_update:,}")
    print(f"  Successfully wired : {updated:,} ({match_rate:.1f}%)")
    print(f"  No cache match     : {not_found:,}")

    if not_found > 0:
        print(f"\n  Note: {not_found:,} fixtures had no matching cache entry.")
        print(f"  These are likely team name mismatches or pre-2001 fixtures")
        print(f"  outside the weather cache coverage range.")

    print(f"\n  Weather is wired. Three-pass can now run.\n")


if __name__ == "__main__":
    main()
