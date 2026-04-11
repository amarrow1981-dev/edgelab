#!/usr/bin/env python3
"""
EdgeLab Weather Bot — Phase 2 External Signal Layer
-----------------------------------------------------
Fetches weather data from Open-Meteo (free, no API key required).
Covers both historical matches (DPOL training) and upcoming fixtures (Gary briefing).

Two modes:
  - Historical : fetch weather at kickoff for past matches — used by DPOL to learn
                 whether conditions correlate with outcomes
  - Forecast   : fetch weather for upcoming fixtures — used by Gary in his briefing

Output per match:
  - precipitation_mm   : rainfall at kickoff (mm)
  - windspeed_kmh      : wind speed at kickoff (km/h)
  - temperature_c      : temperature at kickoff (°C)
  - weather_load       : normalised 0.0–1.0 signal (heavier = worse conditions)
  - weather_description: plain English for Gary ("Heavy rain, strong wind")
  - weather_flag       : True if conditions are significant enough to flag

Integration:
  - Plugs into edgelab_signals.py alongside travel/timing signals
  - w_weather_signal slot added to LeagueParams in edgelab_dpol.py (0.0 — DPOL activates)
  - Home ground coordinates sourced from GROUND_COORDS in edgelab_signals.py

Usage:
    from edgelab_weather import get_weather_for_fixture, get_weather_batch

    # Single fixture (forecast or historical)
    wx = get_weather_for_fixture(
        home_team="Wigan Athletic",
        match_date="2026-04-12",
        kickoff_hour=15,   # 3pm kickoff — defaults to 15 if unknown
        tier="E2",
    )
    print(wx["weather_description"])   # "Overcast, light rain (2mm), calm"
    print(wx["weather_load"])          # 0.23

    # Batch — add weather columns to a full match dataframe (for DPOL training)
    df = get_weather_batch(df, kickoff_hour=15)
    # Adds: precipitation_mm, windspeed_kmh, temperature_c, weather_load columns

API docs: https://open-meteo.com/en/docs
"""

import time
import logging
from datetime import datetime, date, timedelta
from typing import Optional

import requests
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Open-Meteo endpoints
# ---------------------------------------------------------------------------

FORECAST_URL  = "https://api.open-meteo.com/v1/forecast"
HISTORICAL_URL = "https://archive-api.open-meteo.com/v1/archive"

# Variables we request from the API — hourly so we can pick the kickoff hour
HOURLY_VARS = "precipitation,windspeed_10m,temperature_2m"

# Rate limiting — Open-Meteo free tier allows ~10k requests/day
# We add a small sleep between batch calls to be a good citizen
BATCH_SLEEP_S = 0.2


# ---------------------------------------------------------------------------
# Core thresholds — what counts as "significant" weather
# ---------------------------------------------------------------------------

RAIN_LIGHT_MM   = 1.0   # anything below: dry / negligible
RAIN_HEAVY_MM   = 5.0   # above this: heavy rain flag
WIND_BREEZY_KMH = 30.0  # noticeable wind
WIND_STRONG_KMH = 50.0  # strong wind — real factor
TEMP_COLD_C     = 4.0   # cold conditions
TEMP_HOT_C      = 28.0  # unusual heat for football


# ---------------------------------------------------------------------------
# Ground coords import — we get lat/lon from edgelab_signals
# ---------------------------------------------------------------------------

def _get_ground_coords(home_team: str, tier: str) -> Optional[tuple]:
    """
    Pull home ground coordinates from edgelab_signals.GROUND_COORDS.
    Returns (lat, lon) or None if team not found.
    """
    try:
        from edgelab_signals import GROUND_COORDS
        coords = GROUND_COORDS.get(home_team)
        if coords:
            return coords
        # Try common name variations
        for name, c in GROUND_COORDS.items():
            if name.lower() == home_team.lower():
                return c
        logger.warning(f"[Weather] No ground coords for '{home_team}' — cannot fetch weather")
        return None
    except ImportError:
        logger.error("[Weather] edgelab_signals not available — cannot get ground coords")
        return None


# ---------------------------------------------------------------------------
# Weather load normalisation
# ---------------------------------------------------------------------------

def compute_weather_load(
    precipitation_mm: float,
    windspeed_kmh: float,
    temperature_c: float,
) -> float:
    """
    Normalise raw weather values into a single 0.0–1.0 signal.

    0.0 = perfect conditions (dry, calm, mild)
    1.0 = extreme conditions (heavy rain + gale + freeze)

    Components weighted:
      Rain   : 50% — biggest direct impact on play style and outcomes
      Wind   : 35% — second biggest — kills passing games, benefits direct play
      Temp   : 15% — context signal, less decisive than rain/wind
    """
    # Rain component — 0 at dry, 1.0 at RAIN_HEAVY_MM+
    rain_score = min(precipitation_mm / RAIN_HEAVY_MM, 1.0)

    # Wind component — 0 at calm, 1.0 at WIND_STRONG_KMH+
    wind_score = min(windspeed_kmh / WIND_STRONG_KMH, 1.0)

    # Temp component — penalty for cold or unusual heat, 0 in mild range
    if temperature_c <= TEMP_COLD_C:
        temp_score = min((TEMP_COLD_C - temperature_c) / 10.0, 1.0)
    elif temperature_c >= TEMP_HOT_C:
        temp_score = min((temperature_c - TEMP_HOT_C) / 10.0, 1.0)
    else:
        temp_score = 0.0

    load = (rain_score * 0.50) + (wind_score * 0.35) + (temp_score * 0.15)
    return round(float(np.clip(load, 0.0, 1.0)), 3)


# ---------------------------------------------------------------------------
# Plain English description — for Gary
# ---------------------------------------------------------------------------

def build_weather_description(
    precipitation_mm: float,
    windspeed_kmh: float,
    temperature_c: float,
    weather_load: float,
) -> tuple:
    """
    Returns (description: str, weather_flag: bool).

    weather_flag = True if conditions are significant enough to mention in briefing.
    """
    parts = []

    # Rain
    if precipitation_mm < RAIN_LIGHT_MM:
        parts.append("dry")
    elif precipitation_mm < RAIN_HEAVY_MM:
        parts.append(f"light rain ({precipitation_mm:.1f}mm)")
    else:
        parts.append(f"heavy rain ({precipitation_mm:.1f}mm)")

    # Wind
    if windspeed_kmh >= WIND_STRONG_KMH:
        parts.append(f"strong wind ({windspeed_kmh:.0f}km/h)")
    elif windspeed_kmh >= WIND_BREEZY_KMH:
        parts.append(f"breezy ({windspeed_kmh:.0f}km/h)")
    else:
        parts.append("calm")

    # Temperature
    if temperature_c <= TEMP_COLD_C:
        parts.append(f"{temperature_c:.0f}°C — cold")
    elif temperature_c >= TEMP_HOT_C:
        parts.append(f"{temperature_c:.0f}°C — unusually warm")
    else:
        parts.append(f"{temperature_c:.0f}°C")

    description = ", ".join(parts)
    weather_flag = weather_load >= 0.25  # flag if conditions are more than background noise

    return description, weather_flag


# ---------------------------------------------------------------------------
# API fetch — single fixture
# ---------------------------------------------------------------------------

def _fetch_open_meteo(
    lat: float,
    lon: float,
    match_date: str,
    kickoff_hour: int,
    is_historical: bool,
) -> Optional[dict]:
    """
    Raw API call to Open-Meteo.
    Returns dict of {precipitation_mm, windspeed_kmh, temperature_c} or None on failure.
    """
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
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        hourly = data.get("hourly", {})
        times  = hourly.get("time", [])
        precip = hourly.get("precipitation", [])
        wind   = hourly.get("windspeed_10m", [])
        temp   = hourly.get("temperature_2m", [])

        if not times:
            logger.warning(f"[Weather] Empty hourly data returned for {match_date}")
            return None

        # Find the kickoff hour index
        target = f"{match_date}T{kickoff_hour:02d}:00"
        if target in times:
            idx = times.index(target)
        else:
            # Fall back to closest available hour
            idx = min(kickoff_hour, len(times) - 1)

        return {
            "precipitation_mm": float(precip[idx]) if precip else 0.0,
            "windspeed_kmh":    float(wind[idx])   if wind   else 0.0,
            "temperature_c":    float(temp[idx])   if temp   else 10.0,
        }

    except requests.exceptions.Timeout:
        logger.warning(f"[Weather] Timeout fetching weather for {match_date} at ({lat},{lon})")
        return None
    except requests.exceptions.RequestException as e:
        logger.warning(f"[Weather] Request failed for {match_date}: {e}")
        return None
    except (KeyError, IndexError, ValueError) as e:
        logger.warning(f"[Weather] Parse error for {match_date}: {e}")
        return None


# ---------------------------------------------------------------------------
# Public API — single fixture
# ---------------------------------------------------------------------------

def get_weather_for_fixture(
    home_team: str,
    match_date: str,
    kickoff_hour: int = 15,
    tier: str = "E0",
) -> dict:
    """
    Fetch weather for a single fixture.
    Works for both historical and upcoming matches — auto-detects which endpoint to use.

    Args:
        home_team:    Home team name (must exist in GROUND_COORDS)
        match_date:   ISO date string e.g. "2026-04-12"
        kickoff_hour: Hour of kickoff in 24h format (default 15 = 3pm)
        tier:         League tier e.g. "E0" — used for coord lookup fallback

    Returns:
        dict with keys:
            home_team, match_date, lat, lon,
            precipitation_mm, windspeed_kmh, temperature_c,
            weather_load, weather_description, weather_flag,
            source ("forecast" | "historical" | "unavailable")
    """
    base = {
        "home_team":         home_team,
        "match_date":        match_date,
        "lat":               None,
        "lon":               None,
        "precipitation_mm":  None,
        "windspeed_kmh":     None,
        "temperature_c":     None,
        "weather_load":      None,
        "weather_description": "Weather data unavailable",
        "weather_flag":      False,
        "source":            "unavailable",
    }

    coords = _get_ground_coords(home_team, tier)
    if not coords:
        return base

    lat, lon = coords
    base["lat"] = lat
    base["lon"] = lon

    # Determine whether this is historical or forecast
    try:
        match_dt   = datetime.strptime(match_date, "%Y-%m-%d").date()
        today      = date.today()
        # Open-Meteo historical archive has ~5 day lag — anything older than that is historical
        cutoff     = today - timedelta(days=5)
        is_hist    = match_dt <= cutoff
    except ValueError:
        logger.warning(f"[Weather] Invalid date format: {match_date}")
        return base

    raw = _fetch_open_meteo(lat, lon, match_date, kickoff_hour, is_historical=is_hist)
    if not raw:
        return base

    load = compute_weather_load(
        raw["precipitation_mm"],
        raw["windspeed_kmh"],
        raw["temperature_c"],
    )
    desc, flag = build_weather_description(
        raw["precipitation_mm"],
        raw["windspeed_kmh"],
        raw["temperature_c"],
        load,
    )

    return {
        **base,
        "precipitation_mm":    raw["precipitation_mm"],
        "windspeed_kmh":       raw["windspeed_kmh"],
        "temperature_c":       raw["temperature_c"],
        "weather_load":        load,
        "weather_description": desc,
        "weather_flag":        flag,
        "source":              "historical" if is_hist else "forecast",
    }


# ---------------------------------------------------------------------------
# Public API — batch (for DPOL training dataframe)
# ---------------------------------------------------------------------------

def get_weather_batch(
    df: pd.DataFrame,
    kickoff_hour: int = 15,
    date_col: str = "parsed_date",
    home_col: str = "HomeTeam",
    tier_col: str = "tier",
    sleep_s: float = BATCH_SLEEP_S,
) -> pd.DataFrame:
    """
    Add weather columns to a full match dataframe.
    Used during DPOL training to enrich historical data.

    Adds columns:
        precipitation_mm, windspeed_kmh, temperature_c, weather_load

    Args:
        df:           Match dataframe with date, home team, tier columns
        kickoff_hour: Default kickoff hour — 15 (3pm) if not in data
        date_col:     Column containing match date (parsed to datetime or string)
        home_col:     Column containing home team name
        tier_col:     Column containing league tier
        sleep_s:      Sleep between API calls (rate limiting)

    Returns:
        df with weather columns added. Rows where weather is unavailable get NaN.

    Note:
        This can be slow for large datasets — call once and cache/save results.
        For 137k matches this will take ~8 hours at 0.2s/call.
        Use chunked processing and save progress with to_csv() checkpoints.
    """
    results = []

    total = len(df)
    logger.info(f"[Weather] Fetching weather for {total:,} matches...")

    for idx, row in df.iterrows():
        try:
            match_date = str(row[date_col])[:10]  # ensure YYYY-MM-DD
            home_team  = str(row[home_col])
            tier       = str(row.get(tier_col, "E0"))
        except (KeyError, ValueError):
            results.append({
                "precipitation_mm": np.nan,
                "windspeed_kmh":    np.nan,
                "temperature_c":    np.nan,
                "weather_load":     np.nan,
            })
            continue

        wx = get_weather_for_fixture(
            home_team=home_team,
            match_date=match_date,
            kickoff_hour=kickoff_hour,
            tier=tier,
        )

        results.append({
            "precipitation_mm": wx["precipitation_mm"],
            "windspeed_kmh":    wx["windspeed_kmh"],
            "temperature_c":    wx["temperature_c"],
            "weather_load":     wx["weather_load"],
        })

        if idx % 500 == 0 and idx > 0:
            logger.info(f"[Weather] Progress: {idx:,}/{total:,} matches processed")

        time.sleep(sleep_s)

    wx_df = pd.DataFrame(results, index=df.index)
    return pd.concat([df, wx_df], axis=1)


# ---------------------------------------------------------------------------
# Chunked batch with checkpoint saves — for the full 137k dataset
# ---------------------------------------------------------------------------

def get_weather_batch_chunked(
    df: pd.DataFrame,
    output_path: str,
    chunk_size: int = 1000,
    kickoff_hour: int = 15,
    date_col: str = "parsed_date",
    home_col: str = "HomeTeam",
    tier_col: str = "tier",
) -> pd.DataFrame:
    """
    Same as get_weather_batch() but saves progress to CSV every chunk_size rows.
    Use this for the full 137k match dataset — safe to interrupt and resume.

    Args:
        output_path: Path to save progress CSV e.g. "weather_cache.csv"
        chunk_size:  Save checkpoint every N rows

    On resume: pass the same df and output_path — already-fetched rows are
    loaded from the checkpoint and skipped.
    """
    import os

    # Load existing checkpoint if present
    fetched = {}
    if os.path.exists(output_path):
        cached = pd.read_csv(output_path)
        if "match_key" in cached.columns:
            for _, row in cached.iterrows():
                fetched[row["match_key"]] = row
            logger.info(f"[Weather] Loaded {len(fetched):,} cached results from {output_path}")

    results = []
    total   = len(df)

    for i, (idx, row) in enumerate(df.iterrows()):
        try:
            match_date = str(row[date_col])[:10]
            home_team  = str(row[home_col])
            tier       = str(row.get(tier_col, "E0"))
            match_key  = f"{match_date}_{home_team}_{tier}"
        except (KeyError, ValueError):
            results.append({"precipitation_mm": np.nan, "windspeed_kmh": np.nan,
                            "temperature_c": np.nan, "weather_load": np.nan})
            continue

        # Use cached result if available
        if match_key in fetched:
            r = fetched[match_key]
            results.append({
                "precipitation_mm": r.get("precipitation_mm", np.nan),
                "windspeed_kmh":    r.get("windspeed_kmh",    np.nan),
                "temperature_c":    r.get("temperature_c",    np.nan),
                "weather_load":     r.get("weather_load",     np.nan),
            })
            continue

        # Fetch fresh
        wx = get_weather_for_fixture(
            home_team=home_team,
            match_date=match_date,
            kickoff_hour=kickoff_hour,
            tier=tier,
        )

        result = {
            "match_key":        match_key,
            "precipitation_mm": wx["precipitation_mm"],
            "windspeed_kmh":    wx["windspeed_kmh"],
            "temperature_c":    wx["temperature_c"],
            "weather_load":     wx["weather_load"],
        }
        fetched[match_key] = result
        results.append({k: v for k, v in result.items() if k != "match_key"})

        # Checkpoint save
        if (i + 1) % chunk_size == 0:
            checkpoint = pd.DataFrame(list(fetched.values()))
            checkpoint.to_csv(output_path, index=False)
            logger.info(f"[Weather] Checkpoint saved — {i+1:,}/{total:,} rows processed")

        time.sleep(BATCH_SLEEP_S)

    # Final save
    checkpoint = pd.DataFrame(list(fetched.values()))
    checkpoint.to_csv(output_path, index=False)
    logger.info(f"[Weather] Complete — {total:,} matches. Cache saved to {output_path}")

    wx_df = pd.DataFrame(results, index=df.index)
    return pd.concat([df, wx_df], axis=1)


# ---------------------------------------------------------------------------
# CLI — single fixture test or full batch run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="EdgeLab Weather Bot")
    parser.add_argument("--batch",  type=str, default=None,
                        help="Path to CSV folder (history/) — runs full batch over all CSVs")
    parser.add_argument("--output", type=str, default="weather_cache.csv",
                        help="Output path for batch cache (default: weather_cache.csv)")
    parser.add_argument("--chunk",  type=int, default=1000,
                        help="Checkpoint every N rows (default: 1000)")
    parser.add_argument("--hour",   type=int, default=15,
                        help="Kickoff hour for all matches (default: 15)")
    # Single fixture args (used when --batch not specified)
    parser.add_argument("home",  nargs="?", default="Wigan Athletic")
    parser.add_argument("date",  nargs="?", default="2026-04-12")
    parser.add_argument("kickoff_hour", nargs="?", type=int, default=15)
    parser.add_argument("tier",  nargs="?", default="E2")
    args = parser.parse_args()

    if args.batch:
        # ── Batch mode ────────────────────────────────────────────────────
        import glob
        import os
        sys.path.insert(0, os.path.dirname(__file__))
        from edgelab_engine import load_all_csvs

        print(f"\n╔══════════════════════════════════════════╗")
        print(f"║      EdgeLab Weather Bot — Batch         ║")
        print(f"╚══════════════════════════════════════════╝")
        print(f"\n  CSV folder : {args.batch}")
        print(f"  Output     : {args.output}")
        print(f"  Chunk size : {args.chunk}")
        print(f"  Kickoff    : {args.hour:02d}:00")
        print(f"\n  Loading CSVs...")

        df = load_all_csvs(args.batch)
        print(f"  Loaded {len(df):,} matches across {df['tier'].nunique()} tiers.")
        print(f"\n  Starting weather fetch — this will take a while.")
        print(f"  Checkpoints saved every {args.chunk} rows to {args.output}")
        print(f"  Safe to leave running overnight.\n")

        df_out = get_weather_batch_chunked(
            df=df,
            output_path=args.output,
            kickoff_hour=args.hour,
            chunk_size=args.chunk,
        )

        filled = df_out["weather_load"].notna().sum()
        print(f"\n  Done. {filled:,}/{len(df_out):,} matches with weather data.")
        print(f"  Cache saved to: {args.output}")

    else:
        # ── Single fixture mode ───────────────────────────────────────────
        home = args.home
        dt   = args.date
        hour = args.kickoff_hour
        tier = args.tier

        print(f"\n  Weather check: {home} vs ??? | {dt} {hour:02d}:00 | {tier}")
        print(f"  {'─'*55}")

        wx = get_weather_for_fixture(home, dt, hour, tier)

        print(f"  Source      : {wx['source']}")
        print(f"  Location    : {wx['lat']}, {wx['lon']}")
        print(f"  Rain        : {wx['precipitation_mm']} mm")
        print(f"  Wind        : {wx['windspeed_kmh']} km/h")
        print(f"  Temp        : {wx['temperature_c']} °C")
        print(f"  Load        : {wx['weather_load']}")
        print(f"  Description : {wx['weather_description']}")
        print(f"  Flag        : {wx['weather_flag']}")
        print()
