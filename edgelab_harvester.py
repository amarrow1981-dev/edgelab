#!/usr/bin/env python3
"""
EdgeLab Harvester — Background Data Collection
------------------------------------------------
Uses API-Football to bulk-fetch historical match data and build an owned
database that grows automatically over time.

Two modes:

  FOOTBALL (Pro plan — 7,500 calls/day)
    Fills gaps in the existing CSV dataset and keeps current seasons updated.
    Writes to harvester_football.db (raw_matches table).
    Priority: seasons and leagues not covered by football-data.co.uk CSVs.

  OTHER SPORTS (free tier — 100 calls/day each)
    Basketball, rugby, hockey etc. Runs as a low-priority background process.
    Writes to harvester_{sport}.db — same schema per sport.
    By the time you're ready to build those sports, months of history exist.

Design principles:
  - Chronological fetch — oldest season first, works forward
  - Checkpoint after every batch — safe to stop and resume at any time
  - Hard daily call budget — never exceeds the configured limit
  - Separate DB per sport — keeps football clean, same schema everywhere
  - Set it running, walk away

Usage:
    # Football — fill historical gaps (uses Pro allocation)
    python edgelab_harvester.py --sport football --key YOUR_KEY

    # Football — specific tier and season range
    python edgelab_harvester.py --sport football --key YOUR_KEY --tier E0 --from-season 2020 --to-season 2025

    # Other sport background harvest (100 calls/day)
    python edgelab_harvester.py --sport basketball --key YOUR_KEY --daily-limit 100

    # Test connection and check remaining calls
    python edgelab_harvester.py --sport football --key YOUR_KEY --test

    # Status check — what's in the DB so far
    python edgelab_harvester.py --sport football --key YOUR_KEY --status
"""

import os
import sys
import json
import time
import sqlite3
import argparse
import logging
from datetime import datetime, date
from typing import Optional, List, Dict

import requests

logging.basicConfig(level=logging.INFO, format="[Harvester] %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config — sport definitions
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Prediction run budget — reserve this many calls per day for weekly workflow
# Two prediction runs/week @ ~100 calls each = ~200/week = ~30/day average.
# We reserve 200/day to be safe — leaves 7,300 for harvesting.
# Adjust PREDICTION_RESERVE if your weekly workflow changes.
# ---------------------------------------------------------------------------
PREDICTION_RESERVE = 200

SPORT_CONFIG = {
    "football": {
        "api_base":    "https://v3.football.api-sports.io",
        "daily_limit": 7500 - PREDICTION_RESERVE,  # 7,300 — reserves 200 for predictions
        "db_file":     "harvester_football.db",
        "leagues": {
            # tier_code: (league_id, country, name)
            "E0":  (39,  "England",     "Premier League"),
            "E1":  (40,  "England",     "Championship"),
            "E2":  (41,  "England",     "League One"),
            "E3":  (42,  "England",     "League Two"),
            "EC":  (43,  "England",     "National League"),
            "SP1": (140, "Spain",       "La Liga"),
            "SP2": (141, "Spain",       "La Liga 2"),
            "D1":  (78,  "Germany",     "Bundesliga"),
            "D2":  (79,  "Germany",     "2. Bundesliga"),
            "I1":  (135, "Italy",       "Serie A"),
            "I2":  (136, "Italy",       "Serie B"),
            "N1":  (88,  "Netherlands", "Eredivisie"),
            "B1":  (144, "Belgium",     "Pro League"),
            "SC0": (179, "Scotland",    "Premiership"),
            "SC1": (180, "Scotland",    "Championship"),
            "SC2": (181, "Scotland",    "League One"),
            "SC3": (182, "Scotland",    "League Two"),
        },
        # Seasons to harvest — API uses start year (2020 = 2020/21)
        "seasons": list(reversed(range(2000, 2026))),
    },
    "basketball": {
        "api_base":    "https://v1.basketball.api-sports.io",
        "daily_limit": 100,
        "db_file":     "harvester_basketball.db",
        "leagues": {
            "NBA":        (12,  "USA",    "NBA"),
            "EuroLeague": (120, "World",  "EuroLeague"),
            "NBL":        (8,   "Australia", "NBL"),
        },
        "seasons": list(reversed(range(2020, 2026))),
    },
    "nba": {
        # NBA has its own dedicated endpoint
        "api_base":    "https://v2.nba.api-sports.io",
        "daily_limit": 100,
        "db_file":     "harvester_nba.db",
        "leagues": {
            "NBA": (12, "USA", "NBA"),
        },
        "seasons": list(reversed(range(2020, 2026))),
    },
    "rugby": {
        "api_base":    "https://v1.rugby.api-sports.io",
        "daily_limit": 100,
        "db_file":     "harvester_rugby.db",
        "leagues": {
            "Premiership": (1, "England", "Premiership"),
            "Top14":       (2, "France",  "Top 14"),
            "URC":         (3, "Europe",  "URC"),
        },
        "seasons": list(reversed(range(2020, 2026))),
    },
    "hockey": {
        "api_base":    "https://v1.hockey.api-sports.io",
        "daily_limit": 100,
        "db_file":     "harvester_hockey.db",
        "leagues": {
            "NHL":        (57,  "USA/Canada", "NHL"),
            "KHL":        (103, "Russia",     "KHL"),
            "SHL":        (116, "Sweden",     "SHL"),
        },
        "seasons": list(reversed(range(2020, 2026))),
    },
    "baseball": {
        "api_base":    "https://v1.baseball.api-sports.io",
        "daily_limit": 100,
        "db_file":     "harvester_baseball.db",
        "leagues": {
            "MLB": (1, "USA", "MLB"),
        },
        "seasons": list(reversed(range(2020, 2026))),
    },
    "afl": {
        "api_base":    "https://v1.afl.api-sports.io",
        "daily_limit": 100,
        "db_file":     "harvester_afl.db",
        "leagues": {
            "AFL": (1, "Australia", "AFL"),
        },
        "seasons": list(reversed(range(2020, 2026))),
    },
    "handball": {
        "api_base":    "https://v1.handball.api-sports.io",
        "daily_limit": 100,
        "db_file":     "harvester_handball.db",
        "leagues": {
            "Champions League": (3,  "Europe",  "EHF Champions League"),
            "Bundesliga":       (10, "Germany", "Handball Bundesliga"),
        },
        "seasons": list(reversed(range(2020, 2026))),
    },
    "formula1": {
        "api_base":    "https://v1.formula-1.api-sports.io",
        "daily_limit": 100,
        "db_file":     "harvester_formula1.db",
        "leagues": {
            "F1": (1, "World", "Formula 1"),
        },
        "seasons": list(reversed(range(2020, 2026))),
    },
    "mma": {
        "api_base":    "https://v1.mma.api-sports.io",
        "daily_limit": 100,
        "db_file":     "harvester_mma.db",
        "leagues": {
            "UFC": (1, "World", "UFC"),
        },
        "seasons": list(reversed(range(2020, 2026))),
    },
    "nfl": {
        "api_base":    "https://v1.american-football.api-sports.io",
        "daily_limit": 100,
        "db_file":     "harvester_nfl.db",
        "leagues": {
            "NFL": (1, "USA", "NFL"),
        },
        "seasons": list(reversed(range(2020, 2026))),
    },
}

BATCH_SLEEP    = 0.5   # seconds between API calls
CHECKPOINT_DIR = "harvester_checkpoints"


# ---------------------------------------------------------------------------
# Database — raw_matches table
# Sport-agnostic schema. Same structure for every sport.
# ---------------------------------------------------------------------------

def init_db(db_path: str) -> sqlite3.Connection:
    """Create raw_matches and harvest_log tables if they don't exist."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS raw_matches (
            match_id        TEXT PRIMARY KEY,
            sport           TEXT NOT NULL,
            league_code     TEXT NOT NULL,
            league_id       INTEGER,
            league_name     TEXT,
            country         TEXT,
            season          INTEGER,
            match_date      TEXT,
            home_team       TEXT,
            away_team       TEXT,
            home_goals      INTEGER,
            away_goals      INTEGER,
            result          TEXT,   -- H / D / A / null if not finished
            status          TEXT,   -- FT / NS / etc
            raw_json        TEXT,   -- full API response for this fixture
            fetched_at      TEXT
        )
    """)

    # Harvest log — tracks which (sport, league, season) combos have been fetched
    conn.execute("""
        CREATE TABLE IF NOT EXISTS harvest_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            sport           TEXT NOT NULL,
            league_code     TEXT NOT NULL,
            season          INTEGER NOT NULL,
            fixtures_found  INTEGER DEFAULT 0,
            fixtures_written INTEGER DEFAULT 0,
            fetched_at      TEXT,
            UNIQUE(sport, league_code, season)
        )
    """)

    conn.commit()
    logger.info(f"Database ready: {db_path}")
    return conn


# ---------------------------------------------------------------------------
# API client — reuses the pattern from edgelab_databot.py
# ---------------------------------------------------------------------------

class HarvesterClient:
    """Thin wrapper around requests for API-Football / API-Sports."""

    def __init__(self, api_key: str, api_base: str, daily_limit: int):
        self.api_key     = api_key
        self.api_base    = api_base
        self.daily_limit = daily_limit
        self.calls_made  = 0
        self.session     = requests.Session()
        self.session.headers.update({
            "x-apisports-key": api_key,
        })

    def _get(self, endpoint: str, params: dict) -> Optional[dict]:
        """Make a single API call. Returns parsed JSON or None on failure."""
        if self.calls_made >= self.daily_limit:
            logger.warning(f"Daily limit reached ({self.daily_limit} calls). Stopping.")
            return None

        url = f"{self.api_base}/{endpoint}"
        try:
            resp = self.session.get(url, params=params, timeout=15)
            resp.raise_for_status()
            self.calls_made += 1
            data = resp.json()

            # API-Football wraps responses in {"response": [...], "errors": {...}}
            errors = data.get("errors", {})
            if errors and errors != [] and errors != {}:
                logger.warning(f"API errors: {errors}")
                return None

            return data

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout on {endpoint}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.warning(f"HTTP {e.response.status_code} on {endpoint}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error on {endpoint}: {e}")
            return None

    def test_connection(self) -> bool:
        """Test the API key and return remaining calls."""
        data = self._get("status", {})
        if not data:
            print("\n  Connection failed — check your API key.\n")
            return False
        account = data.get("response", {})
        sub = account.get("subscription", {})
        requests_info = account.get("requests", {})
        remaining = requests_info.get("current", "?")
        limit_day = requests_info.get("limit_day", "?")
        plan = sub.get("plan", "?")
        print(f"\n  API connected. Plan: {plan}. Calls today: {remaining}/{limit_day}")
        return True

    def fetch_fixtures(self, league_id: int, season: int) -> List[dict]:
        """Fetch all fixtures for a league+season. Returns list of fixture dicts."""
        data = self._get("fixtures", {"league": league_id, "season": season})
        if not data:
            return []
        return data.get("response", [])

    def calls_remaining(self) -> int:
        return max(0, self.daily_limit - self.calls_made)


# ---------------------------------------------------------------------------
# Checkpoint — track progress per (sport, league, season)
# ---------------------------------------------------------------------------

def checkpoint_path(sport: str) -> str:
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    return os.path.join(CHECKPOINT_DIR, f"harvester_{sport}_checkpoint.json")


def load_checkpoint(sport: str) -> dict:
    """Load checkpoint — returns dict of completed (league, season) pairs."""
    path = checkpoint_path(sport)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"completed": []}


def save_checkpoint(sport: str, completed: list):
    """Save completed (league_code, season) pairs."""
    path = checkpoint_path(sport)
    with open(path, "w") as f:
        json.dump({"completed": completed}, f, indent=2)


# ---------------------------------------------------------------------------
# Result derivation
# ---------------------------------------------------------------------------

def derive_result(home_goals, away_goals, status: str) -> Optional[str]:
    """Return H/D/A or None if match not finished."""
    if status != "FT":
        return None
    if home_goals is None or away_goals is None:
        return None
    if home_goals > away_goals:
        return "H"
    elif away_goals > home_goals:
        return "A"
    return "D"


# ---------------------------------------------------------------------------
# Main harvest loop
# ---------------------------------------------------------------------------

def harvest(
    sport: str,
    api_key: str,
    target_leagues: Optional[List[str]] = None,
    from_season: Optional[int] = None,
    to_season: Optional[int] = None,
    daily_limit: Optional[int] = None,
):
    config  = SPORT_CONFIG[sport]
    db_path = config["db_file"]
    base    = config["api_base"]
    limit   = daily_limit or config["daily_limit"]
    leagues = config["leagues"]
    seasons = config["seasons"]

    # Apply filters
    if target_leagues:
        leagues = {k: v for k, v in leagues.items() if k in target_leagues}
    if from_season:
        seasons = [s for s in seasons if s >= from_season]
    if to_season:
        seasons = [s for s in seasons if s <= to_season]

    print(f"\n{'='*60}")
    print(f"  EdgeLab Harvester — {sport.upper()}")
    print(f"{'='*60}")
    print(f"  DB         : {db_path}")
    print(f"  Leagues    : {', '.join(leagues.keys())}")
    print(f"  Seasons    : {seasons[0]} → {seasons[-1]}")
    print(f"  Daily limit: {limit} calls  ({PREDICTION_RESERVE} reserved for predictions)")

    client = HarvesterClient(api_key, base, limit)
    if not client.test_connection():
        sys.exit(1)

    conn       = init_db(db_path)
    checkpoint = load_checkpoint(sport)
    completed  = checkpoint["completed"]

    total_written = 0
    total_skipped = 0

    for season in seasons:
        for league_code, (league_id, country, league_name) in leagues.items():

            key = f"{league_code}:{season}"
            if key in completed:
                logger.info(f"  [{league_code} {season}] Already fetched — skipping")
                continue

            if client.calls_remaining() == 0:
                print(f"\n  Daily limit reached. Progress saved. Resume tomorrow.")
                save_checkpoint(sport, completed)
                conn.close()
                return

            print(f"\n  [{league_code} {season}] Fetching {league_name} ({country})...")
            fixtures = client.fetch_fixtures(league_id, season)
            print(f"    {len(fixtures)} fixtures returned  |  "
                  f"{client.calls_remaining()} calls remaining")

            written  = 0
            skipped  = 0

            for fx in fixtures:
                try:
                    fixture_data = fx.get("fixture", {})
                    goals        = fx.get("goals", {})
                    teams        = fx.get("teams", {})

                    match_id   = f"{sport}_{league_code}_{season}_{fixture_data.get('id', '')}"
                    status     = fixture_data.get("status", {}).get("short", "")
                    match_date = fixture_data.get("date", "")[:10]
                    home_team  = teams.get("home", {}).get("name", "")
                    away_team  = teams.get("away", {}).get("name", "")
                    home_goals = goals.get("home")
                    away_goals = goals.get("away")
                    result     = derive_result(home_goals, away_goals, status)

                    # Check if already exists
                    existing = conn.execute(
                        "SELECT 1 FROM raw_matches WHERE match_id = ?", (match_id,)
                    ).fetchone()

                    if existing:
                        skipped += 1
                        continue

                    conn.execute("""
                        INSERT INTO raw_matches
                        (match_id, sport, league_code, league_id, league_name,
                         country, season, match_date, home_team, away_team,
                         home_goals, away_goals, result, status, raw_json, fetched_at)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (
                        match_id, sport, league_code, league_id, league_name,
                        country, season, match_date, home_team, away_team,
                        home_goals, away_goals, result, status,
                        json.dumps(fx), datetime.utcnow().isoformat()
                    ))
                    written += 1

                except Exception as e:
                    logger.warning(f"    Error processing fixture: {e}")
                    continue

            conn.commit()

            # Log to harvest_log
            conn.execute("""
                INSERT INTO harvest_log
                (sport, league_code, season, fixtures_found, fixtures_written, fetched_at)
                VALUES (?,?,?,?,?,?)
                ON CONFLICT(sport, league_code, season) DO UPDATE SET
                    fixtures_found=excluded.fixtures_found,
                    fixtures_written=excluded.fixtures_written,
                    fetched_at=excluded.fetched_at
            """, (sport, league_code, season, len(fixtures), written,
                  datetime.utcnow().isoformat()))
            conn.commit()

            total_written += written
            total_skipped += skipped
            completed.append(key)
            save_checkpoint(sport, completed)

            print(f"    Written: {written}  Skipped: {skipped}  "
                  f"Total so far: {total_written:,}")

            time.sleep(BATCH_SLEEP)

    # Final summary
    print(f"\n{'='*60}")
    print(f"  HARVEST COMPLETE")
    print(f"{'='*60}")
    print(f"  Total written : {total_written:,}")
    print(f"  Total skipped : {total_skipped:,}")
    print(f"  API calls used: {client.calls_made}")

    stats = conn.execute(
        "SELECT COUNT(*) as n, MIN(match_date) as oldest, MAX(match_date) as newest "
        "FROM raw_matches WHERE sport = ?", (sport,)
    ).fetchone()
    print(f"  DB total      : {stats['n']:,} matches")
    print(f"  Date range    : {stats['oldest']} → {stats['newest']}")
    conn.close()


# ---------------------------------------------------------------------------
# Status report
# ---------------------------------------------------------------------------

def show_status(sport: str):
    config  = SPORT_CONFIG[sport]
    db_path = config["db_file"]

    if not os.path.exists(db_path):
        print(f"\n  No database found at {db_path} — nothing harvested yet.\n")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    total = conn.execute(
        "SELECT COUNT(*) as n FROM raw_matches WHERE sport = ?", (sport,)
    ).fetchone()["n"]

    completed_combos = conn.execute(
        "SELECT COUNT(*) as n FROM harvest_log WHERE sport = ?", (sport,)
    ).fetchone()["n"]

    print(f"\n{'='*60}")
    print(f"  Harvester Status — {sport.upper()}")
    print(f"{'='*60}")
    print(f"  Total matches : {total:,}")
    print(f"  Combos done   : {completed_combos}")

    print(f"\n  {'League':<8} {'Season':>8} {'Fixtures':>10}")
    print(f"  {'-'*30}")
    rows = conn.execute(
        "SELECT league_code, season, fixtures_found FROM harvest_log "
        "WHERE sport = ? ORDER BY league_code, season", (sport,)
    ).fetchall()
    for row in rows:
        print(f"  {row['league_code']:<8} {row['season']:>8} {row['fixtures_found']:>10,}")

    conn.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="EdgeLab Harvester — background data collection via API-Football"
    )
    parser.add_argument("--sport",       required=True,
                        choices=list(SPORT_CONFIG.keys()),
                        help="Sport to harvest")
    parser.add_argument("--key",         required=True,
                        help="API-Sports key")
    parser.add_argument("--tier",        type=str, default=None,
                        help="Single tier or comma-separated e.g. E0,E1")
    parser.add_argument("--from-season", type=int, default=None,
                        help="Start season (inclusive) e.g. 2020")
    parser.add_argument("--to-season",   type=int, default=None,
                        help="End season (inclusive) e.g. 2025")
    parser.add_argument("--daily-limit", type=int, default=None,
                        help="Override daily call budget")
    parser.add_argument("--test",        action="store_true",
                        help="Test connection only")
    parser.add_argument("--status",      action="store_true",
                        help="Show harvest status and exit")
    args = parser.parse_args()

    if args.status:
        show_status(args.sport)
        return

    if args.test:
        config = SPORT_CONFIG[args.sport]
        client = HarvesterClient(args.key, config["api_base"],
                                 args.daily_limit or config["daily_limit"])
        client.test_connection()
        return

    target_leagues = [t.strip() for t in args.tier.split(",")] if args.tier else None

    harvest(
        sport=args.sport,
        api_key=args.key,
        target_leagues=target_leagues,
        from_season=args.from_season,
        to_season=args.to_season,
        daily_limit=args.daily_limit,
    )


if __name__ == "__main__":
    main()
