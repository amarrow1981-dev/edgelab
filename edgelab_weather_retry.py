#!/usr/bin/env python3
"""
EdgeLab Weather Cache Retry
-----------------------------
Targets only null weather_load rows in weather_cache.csv.
Skips anything already populated — safe to run multiple times.

Reasons rows may be null:
  1. Home team coords were missing at time of original fetch (now fixed in signals.py)
  2. Original batch script timed out or hit rate limits and wrote nulls silently
  3. Open-Meteo had a transient failure for that date/location

This script retries all of the above. Rows that genuinely can't be fetched
(Open-Meteo has no data for that location/date) remain null after retry.

Usage:
    python edgelab_weather_retry.py
    python edgelab_weather_retry.py --cache weather_cache.csv --batch-sleep 0.3
    python edgelab_weather_retry.py --limit 1000   # test run — first 1000 nulls only
    python edgelab_weather_retry.py --tier E1       # retry a specific tier only

Progress is saved every --checkpoint rows (default 500).
Safe to interrupt and resume — already-populated rows are never re-fetched.
"""

import argparse
import logging
import time
import sys
import os
from datetime import date

import pandas as pd
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from edgelab_signals import GROUND_COORDS
from edgelab_weather import (
    compute_weather_load,
    HISTORICAL_URL,
    FORECAST_URL,
    HOURLY_VARS,
)

logging.basicConfig(level=logging.INFO, format="[WeatherRetry] %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_CACHE   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weather_cache.csv")
KICKOFF_HOUR    = 15   # assume 3pm if unknown
BATCH_SLEEP     = 0.25  # seconds between API calls — be a good citizen
CHECKPOINT_EVERY = 500  # save progress every N fetches


# ---------------------------------------------------------------------------
# Key parsing — match_key format: YYYY-MM-DD_HomeTeam_tier
# ---------------------------------------------------------------------------

def parse_key(key: str):
    """Returns (date_str, home_team, tier) from a match_key."""
    parts = key.split("_")
    date_str  = parts[0]
    tier      = parts[-1]
    home_team = "_".join(parts[1:-1])
    return date_str, home_team, tier


# ---------------------------------------------------------------------------
# Single fetch — wraps Open-Meteo call
# ---------------------------------------------------------------------------

def fetch_weather(lat: float, lon: float, match_date: str) -> dict | None:
    """
    Fetch weather for a single fixture.
    Returns {precipitation_mm, windspeed_kmh, temperature_c} or None on failure.
    """
    today = date.today().isoformat()
    is_historical = match_date <= today

    url = HISTORICAL_URL if is_historical else FORECAST_URL

    params = {
        "latitude":        lat,
        "longitude":       lon,
        "start_date":      match_date,
        "end_date":        match_date,
        "hourly":          HOURLY_VARS,
        "timezone":        "Europe/London",
        "wind_speed_unit": "kmh",
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        hourly = data.get("hourly", {})
        times  = hourly.get("time", [])
        precip = hourly.get("precipitation", [])
        wind   = hourly.get("windspeed_10m", [])
        temp   = hourly.get("temperature_2m", [])

        if not times:
            return None

        target = f"{match_date}T{KICKOFF_HOUR:02d}:00"
        if target in times:
            idx = times.index(target)
        else:
            idx = min(KICKOFF_HOUR, len(times) - 1)

        return {
            "precipitation_mm": float(precip[idx]) if precip else 0.0,
            "windspeed_kmh":    float(wind[idx])   if wind   else 0.0,
            "temperature_c":    float(temp[idx])   if temp   else 10.0,
        }

    except requests.exceptions.Timeout:
        logger.warning(f"Timeout for {match_date}")
        return None
    except requests.exceptions.HTTPError as e:
        logger.warning(f"HTTP {e.response.status_code} for {match_date}")
        return None
    except Exception as e:
        logger.warning(f"Unexpected error for {match_date}: {e}")
        return None


# ---------------------------------------------------------------------------
# Main retry loop
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Retry null weather rows in cache")
    parser.add_argument("--cache",        default=DEFAULT_CACHE, help="Path to weather_cache.csv")
    parser.add_argument("--batch-sleep",  type=float, default=BATCH_SLEEP, help="Sleep between API calls (s)")
    parser.add_argument("--checkpoint",   type=int,   default=CHECKPOINT_EVERY, help="Save every N fetches")
    parser.add_argument("--limit",        type=int,   default=None, help="Max rows to retry (test mode)")
    parser.add_argument("--tier",         type=str,   default=None, help="Retry a specific tier only e.g. E1")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  EdgeLab Weather Cache Retry")
    print(f"{'='*60}")
    print(f"  Cache : {args.cache}")
    if args.tier:
        print(f"  Tier  : {args.tier} only")
    if args.limit:
        print(f"  Limit : {args.limit} rows (test mode)")

    # Load cache
    df = pd.read_csv(args.cache)
    total_rows = len(df)
    print(f"\n  Total cache rows   : {total_rows:,}")
    print(f"  Populated rows     : {df['weather_load'].notna().sum():,}")
    print(f"  Null rows          : {df['weather_load'].isna().sum():,}")

    # Find null rows
    null_mask = df["weather_load"].isna()

    # Tier filter
    if args.tier:
        tier_mask = df["match_key"].str.endswith(f"_{args.tier}")
        null_mask = null_mask & tier_mask

    null_idx = df[null_mask].index.tolist()
    print(f"  Rows to retry      : {len(null_idx):,}")

    if args.limit:
        null_idx = null_idx[:args.limit]
        print(f"  (capped at {args.limit} for test run)")

    if not null_idx:
        print("\n  Nothing to retry. Cache is complete.")
        return

    print(f"\n  Starting retry...\n")

    fetched     = 0
    filled      = 0
    no_coords   = 0
    no_data     = 0
    errors      = 0

    for i, idx in enumerate(null_idx):
        key = df.at[idx, "match_key"]
        match_date, home_team, tier = parse_key(key)

        # Get coords
        coords = GROUND_COORDS.get(home_team)
        if not coords:
            # Try case-insensitive match
            for name, c in GROUND_COORDS.items():
                if name.lower().strip() == home_team.lower().strip():
                    coords = c
                    break

        if not coords:
            no_coords += 1
            if no_coords <= 5:
                logger.warning(f"No coords for '{home_team}' — skipping")
            continue

        lat, lon = coords

        # Fetch
        result = fetch_weather(lat, lon, match_date)
        fetched += 1

        if result is not None:
            weather_load = compute_weather_load(
                result["precipitation_mm"],
                result["windspeed_kmh"],
                result["temperature_c"],
            )
            df.at[idx, "precipitation_mm"] = result["precipitation_mm"]
            df.at[idx, "windspeed_kmh"]    = result["windspeed_kmh"]
            df.at[idx, "temperature_c"]    = result["temperature_c"]
            df.at[idx, "weather_load"]     = weather_load
            filled += 1
        else:
            no_data += 1

        # Progress
        if (i + 1) % 100 == 0:
            pct = (i + 1) / len(null_idx) * 100
            print(f"  [{pct:5.1f}%]  Processed {i+1:,}/{len(null_idx):,}  "
                  f"filled={filled:,}  no_data={no_data:,}  no_coords={no_coords:,}")

        # Checkpoint save
        if fetched % args.checkpoint == 0:
            df.to_csv(args.cache, index=False)
            print(f"  >>> Checkpoint saved at {fetched:,} fetches")

        time.sleep(args.batch_sleep)

    # Final save
    df.to_csv(args.cache, index=False)

    # Summary
    final_populated = df["weather_load"].notna().sum()
    final_null      = df["weather_load"].isna().sum()
    coverage        = final_populated / total_rows * 100

    print(f"\n{'='*60}")
    print(f"  RETRY COMPLETE")
    print(f"{'='*60}")
    print(f"  Rows attempted     : {len(null_idx):,}")
    print(f"  Fetched from API   : {fetched:,}")
    print(f"  Successfully filled: {filled:,}")
    print(f"  No data returned   : {no_data:,}  (likely permanent gaps)")
    print(f"  No coords found    : {no_coords:,}")
    print(f"\n  Cache coverage now : {final_populated:,} / {total_rows:,}  ({coverage:.1f}%)")
    print(f"  Remaining nulls    : {final_null:,}")

    if no_data > 0:
        print(f"\n  {no_data:,} rows had no data from Open-Meteo.")
        print(f"  These are likely permanent — Open-Meteo archive gaps.")
        print(f"  Consider ERA5 via Copernicus CDS for these if coverage matters.")
    print()


if __name__ == "__main__":
    main()
