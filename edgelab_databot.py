#!/usr/bin/env python3
"""
EdgeLab DataBot v1
------------------
Pulls upcoming fixtures and B365 odds from API-Football (v3.football.api-sports.io)
and outputs a CSV that the EdgeLab engine can consume directly.

Usage:
    python edgelab_databot.py --key YOUR_API_KEY
    python edgelab_databot.py --key YOUR_API_KEY --days 7
    python edgelab_databot.py --key YOUR_API_KEY --date 2026-04-05
    python edgelab_databot.py --key YOUR_API_KEY --test

Output:
    databot_output/YYYY-MM-DD_fixtures.csv  — engine-ready CSV
    databot_output/YYYY-MM-DD_fixtures_raw.json  — raw API response for debugging

The CSV format matches football-data.co.uk exactly so load_all_csvs() can consume it.
"""

import os
import sys
import json
import time
import argparse
import logging
from datetime import datetime, timedelta

import requests
import pandas as pd

logging.basicConfig(level=logging.INFO, format="[DataBot] %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

API_BASE = "https://v3.football.api-sports.io"

# English league IDs on API-Football — verified via /leagues endpoint
#   39 = Premier League
#   40 = Championship
#   41 = League One
#   42 = League Two
#   43 = National League (Conference / EC) — confirmed "National League", England
#   45 = FA Cup (NOT the National League)
#
# European league IDs — confirmed from public sources
#   SC1/SC2/SC3 IDs are unverified — check DataBot logs for league name on first fetch
LEAGUE_MAP = {
    # English — verified
    "E0": 39,   # Premier League
    "E1": 40,   # Championship
    "E2": 41,   # League One
    "E3": 42,   # League Two
    "EC": 43,   # National League (Conference) — verified ID 43

    # European — confirmed from public sources
    "SP1": 140,  # La Liga
    "SP2": 141,  # La Liga 2
    "D1":  78,   # Bundesliga
    "D2":  79,   # 2. Bundesliga
    "I1":  135,  # Serie A
    "I2":  136,  # Serie B
    "N1":  88,   # Eredivisie
    "B1":  144,  # Belgian Pro League

    # Scottish — SC0 verified; SC1/SC2/SC3 need live verification via DataBot logs
    "SC0": 179,  # Scottish Premiership — verified
    "SC1": 180,  # Scottish Championship — UNVERIFIED, check log output
    "SC2": 181,  # Scottish League One — UNVERIFIED, check log output
    "SC3": 182,  # Scottish League Two — UNVERIFIED, check log output
}

# Current season (API uses start year — 2025 = 2025/26 season)
CURRENT_SEASON = 2025

OUTPUT_DIR = "databot_output"


# ---------------------------------------------------------------------------
# Team name normalisation
# ---------------------------------------------------------------------------
#
# API-Football returns official club names. football-data.co.uk uses abbreviations.
# This map translates API-Football -> football-data.co.uk so that when upcoming
# fixtures are appended to historical data, team name lookups (form, H2H) work.
#
# Rule: the RIGHT side is always exactly what appears in the historical CSVs.
# If a club isn't listed here, its API-Football name is used as-is.
#
# To add a new mapping: just add a line. The apply_name_map() function picks it up.
# ---------------------------------------------------------------------------

TEAM_NAME_MAP = {
    # Premier League
    "Manchester City":          "Man City",
    "Manchester United":        "Man United",
    "Nottingham Forest":        "Nott'm Forest",
    "Wolverhampton Wanderers":  "Wolves",
    "Queens Park Rangers":      "QPR",
    "Tottenham Hotspur":        "Tottenham",
    "West Bromwich Albion":     "West Brom",
    "Sheffield Wednesday":      "Sheffield Weds",
    "Peterborough United":      "Peterboro",
    "Bristol Rovers":           "Bristol Rvs",
    "Dagenham & Redbridge":     "Dag and Red",
    "Rushden & Diamonds":       "Rushden & D",
    "MK Dons":                  "Milton Keynes Dons",
    "Wimbledon":                "Wimbledon",
    # AFC prefix variants
    "AFC Wimbledon":            "AFC Wimbledon",
    "AFC Telford United":       "AFC Telford United",
    # Clubs where API uses full name, data uses short
    "Wigan Athletic":           "Wigan",
    "Blackburn Rovers":         "Blackburn",
    "Blackpool FC":             "Blackpool",
    "Bolton Wanderers":         "Bolton",
    "Burnley FC":               "Burnley",
    "Brentford FC":             "Brentford",
    "Brighton & Hove Albion":   "Brighton",
    "Cardiff City":             "Cardiff",
    "Charlton Athletic":        "Charlton",
    "Cheltenham Town":          "Cheltenham",
    "Colchester United":        "Colchester",
    "Coventry City":            "Coventry",
    "Crawley Town":             "Crawley Town",
    "Crystal Palace":           "Crystal Palace",
    "Derby County":             "Derby",
    "Doncaster Rovers":         "Doncaster",
    "Exeter City":              "Exeter",
    "Fleetwood Town":           "Fleetwood Town",
    "Forest Green Rovers":      "Forest Green",
    "Gillingham FC":            "Gillingham",
    "Grimsby Town":             "Grimsby",
    "Hartlepool United":        "Hartlepool",
    "Huddersfield Town":        "Huddersfield",
    "Hull City":                "Hull",
    "Ipswich Town":             "Ipswich",
    "Leeds United":             "Leeds",
    "Leicester City":           "Leicester",
    "Leyton Orient":            "Leyton Orient",
    "Lincoln City":             "Lincoln",
    "Luton Town":               "Luton",
    "Mansfield Town":           "Mansfield",
    "Middlesbrough FC":         "Middlesbrough",
    "Millwall FC":              "Millwall",
    "Morecambe FC":             "Morecambe",
    "Newport County":           "Newport County",
    "Northampton Town":         "Northampton",
    "Norwich City":             "Norwich",
    "Notts County":             "Notts County",
    "Oldham Athletic":          "Oldham",
    "Oxford United":            "Oxford",
    "Plymouth Argyle":          "Plymouth",
    "Port Vale":                "Port Vale",
    "Portsmouth FC":            "Portsmouth",
    "Preston North End":        "Preston",
    "Reading FC":               "Reading",
    "Rochdale AFC":             "Rochdale",
    "Rotherham United":         "Rotherham",
    "Salford City":             "Salford",
    "Scunthorpe United":        "Scunthorpe",
    "Sheffield United":         "Sheffield United",
    "Shrewsbury Town":          "Shrewsbury",
    "Southampton FC":           "Southampton",
    "Southend United":          "Southend",
    "Stevenage FC":             "Stevenage",
    "Stockport County":         "Stockport",
    "Stoke City":               "Stoke",
    "Sunderland AFC":           "Sunderland",
    "Sutton United":            "Sutton",
    "Swansea City":             "Swansea",
    "Swindon Town":             "Swindon",
    "Torquay United":           "Torquay",
    "Tranmere Rovers":          "Tranmere",
    "Walsall FC":               "Walsall",
    "Watford FC":               "Watford",
    "West Ham United":          "West Ham",
    "Wrexham AFC":              "Wrexham",
    "Wycombe Wanderers":        "Wycombe",
    "Yeovil Town":              "Yeovil",
    "York City":                "York",
    "Barnet FC":                "Barnet",
    "Barrow AFC":               "Barrow",
    "Bradford City":            "Bradford",
    "Bristol City":             "Bristol City",
    "Burton Albion":            "Burton",
    "Bury FC":                  "Bury",
    "Cambridge United":         "Cambridge",
    "Carlisle United":          "Carlisle",
    "Chesterfield FC":          "Chesterfield",
    "Accrington Stanley":       "Accrington",
    "Aldershot Town":           "Aldershot",
    "Bromley FC":               "Bromley",
    "Darlington FC":            "Darlington",
    "Halifax Town":             "Halifax",
    "Harrogate Town":           "Harrogate",
    "Kidderminster Harriers":   "Kidderminster",
    "Macclesfield Town":        "Macclesfield",
    "Maidenhead United":        "Maidenhead",
    "Maidstone United":         "Maidstone",
    "Boston United":            "Boston Utd",
    "Wealdstone FC":            "Wealdstone",
    "Woking FC":                "Woking",
    "Eastleigh FC":             "Eastleigh",
    "Solihull Moors":           "Solihull",
    "Dorking Wanderers":        "Dorking",
    "Gateshead FC":             "Gateshead",
    "Fylde AFC":                "Fylde",
    "Boreham Wood":             "Boreham Wood",
    "Dover Athletic":           "Dover Athletic",
    "Ebbsfleet United":         "Ebbsfleet",
}


def apply_name_map(name: str) -> str:
    """
    Translate an API-Football team name to its football-data.co.uk equivalent.
    Returns the original name unchanged if no mapping exists.
    Logs a warning for any name that doesn't match — helps catch new clubs.
    """
    mapped = TEAM_NAME_MAP.get(name)
    if mapped:
        return mapped
    # Try stripping common suffixes the API sometimes adds
    for suffix in [" FC", " AFC", " City", " Town", " United", " Rovers", " Athletic"]:
        if name.endswith(suffix):
            stripped = name[:-len(suffix)]
            if stripped in TEAM_NAME_MAP.values():
                return stripped
    return name  # return as-is — engine will use neutral priors, Gary will flag it


# ---------------------------------------------------------------------------
# API client
# ---------------------------------------------------------------------------

class APIFootballClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"x-apisports-key": api_key}
        self.calls_made = 0

    def get(self, endpoint: str, params: dict = None) -> dict:
        """Make a GET request. Returns parsed JSON or empty dict on failure."""
        url = f"{API_BASE}/{endpoint}"
        try:
            resp = requests.get(url, headers=self.headers, params=params, timeout=15)
            self.calls_made += 1
            resp.raise_for_status()
            data = resp.json()
            if data.get("errors") and data["errors"]:
                logger.error(f"API error on {endpoint}: {data['errors']}")
                return {}
            remaining = resp.headers.get("x-ratelimit-requests-remaining", "?")
            n = len(data.get("response", []))
            logger.info(f"  /{endpoint} -> {n} results | calls remaining today: {remaining}")
            return data
        except requests.RequestException as e:
            logger.error(f"Request failed for {endpoint}: {e}")
            return {}

    def test_connection(self) -> bool:
        """Confirm the API key is valid and show account info."""
        print("\n  Testing API connection...")
        data = self.get("status")
        if not data or not data.get("response"):
            print("  X Connection failed -- check your API key.")
            return False
        r = data["response"]
        account = r.get("account", {})
        sub = r.get("subscription", {})
        reqs = r.get("requests", {})
        print(f"  Connected as: {account.get('firstname', '')} {account.get('lastname', '')}")
        print(f"    Plan    : {sub.get('plan', 'unknown')}")
        print(f"    Requests: {reqs.get('current', '?')} used / {reqs.get('limit_day', '?')} daily limit")
        return True


# ---------------------------------------------------------------------------
# Fixture + odds fetching
# ---------------------------------------------------------------------------

def fetch_fixtures(client: APIFootballClient, from_date: str, to_date: str, league_id: int) -> list:
    """Fetch fixtures for a date range and league. Returns API response list."""
    data = client.get("fixtures", params={
        "from": from_date,
        "to": to_date,
        "league": league_id,
        "season": CURRENT_SEASON,
    })
    return data.get("response", [])


def fetch_odds(client: APIFootballClient, fixture_id: int) -> dict:
    """
    Fetch Bet365 Match Winner (1X2) odds for a fixture.
    Returns {"home": float, "draw": float, "away": float} or {} if unavailable.
    """
    data = client.get("odds", params={
        "fixture": fixture_id,
        "bookmaker": 1,   # Bet365
        "bet": 1,         # Match Winner
    })
    response = data.get("response", [])
    if not response:
        return {}
    try:
        bookmakers = response[0].get("bookmakers", [])
        for bm in bookmakers:
            for bet in bm.get("bets", []):
                if bet.get("id") == 1:  # Match Winner
                    values = {v["value"]: float(v["odd"]) for v in bet.get("values", [])}
                    return {
                        "home": values.get("Home"),
                        "draw": values.get("Draw"),
                        "away": values.get("Away"),
                    }
    except (KeyError, IndexError, ValueError):
        pass
    return {}


# ---------------------------------------------------------------------------
# Main data builder
# ---------------------------------------------------------------------------

def build_dataframe(
    client: APIFootballClient,
    from_date: str,
    to_date: str,
    fetch_odds_flag: bool = True,
    odds_delay: float = 0.25,
) -> tuple:
    """
    Pull all English league fixtures for the date range.
    Returns (DataFrame, raw_dump_dict).

    DataFrame columns match football-data.co.uk format exactly:
        Div, Date, HomeTeam, AwayTeam, FTHG, FTAG, FTR, B365H, B365D, B365A
    Plus metadata columns: fixture_id, status, match_date (for logging/debugging).
    """
    all_rows = []
    raw_dump = {}

    for tier, league_id in LEAGUE_MAP.items():
        logger.info(f"\n  [{tier}] Fetching fixtures {from_date} -> {to_date} (league_id={league_id})...")
        fixtures = fetch_fixtures(client, from_date, to_date, league_id)
        raw_dump[tier] = fixtures

        if not fixtures:
            logger.info(f"  [{tier}] No fixtures found for league_id={league_id}.")
            continue

        # Debug: show first fixture's league name so we can verify the ID is correct
        first = fixtures[0]
        league_name = first.get("league", {}).get("name", "unknown")
        league_country = first.get("league", {}).get("country", "unknown")
        logger.info(f"  [{tier}] {len(fixtures)} fixtures — league: '{league_name}' ({league_country})")

        for fx in fixtures:
            fixture_id = fx["fixture"]["id"]
            match_date = fx["fixture"]["date"][:10]          # YYYY-MM-DD
            status     = fx["fixture"]["status"]["short"]    # FT, NS, 1H, etc.
            home_team  = apply_name_map(fx["teams"]["home"]["name"])
            away_team  = apply_name_map(fx["teams"]["away"]["name"])
            home_goals = fx["goals"]["home"]
            away_goals = fx["goals"]["away"]

            # Result -- only if finished
            if status == "FT" and home_goals is not None and away_goals is not None:
                fthg = int(home_goals)
                ftag = int(away_goals)
                ftr  = "H" if fthg > ftag else ("A" if ftag > fthg else "D")
            else:
                fthg = ftag = ftr = ""

            # Odds -- only fetch for upcoming matches (saves API calls)
            b365h = b365d = b365a = None
            if fetch_odds_flag and ftr == "":
                odds = fetch_odds(client, fixture_id)
                b365h = odds.get("home")
                b365d = odds.get("draw")
                b365a = odds.get("away")
                if b365h:
                    logger.info(f"    {home_team} vs {away_team} -- H:{b365h} D:{b365d} A:{b365a}")
                else:
                    logger.info(f"    {home_team} vs {away_team} -- odds not available yet")
                time.sleep(odds_delay)

            # Date format: DD/MM/YYYY (football-data.co.uk style)
            try:
                formatted_date = datetime.strptime(match_date, "%Y-%m-%d").strftime("%d/%m/%Y")
            except ValueError:
                formatted_date = match_date

            all_rows.append({
                "Div":        tier,
                "Date":       formatted_date,
                "HomeTeam":   home_team,
                "AwayTeam":   away_team,
                "FTHG":       fthg,
                "FTAG":       ftag,
                "FTR":        ftr,
                "B365H":      b365h,
                "B365D":      b365d,
                "B365A":      b365a,
                # Metadata (not used by engine)
                "fixture_id": fixture_id,
                "status":     status,
                "match_date": match_date,
            })

    if not all_rows:
        return pd.DataFrame(), raw_dump

    df = pd.DataFrame(all_rows)
    df = df.sort_values(["match_date", "Div"]).reset_index(drop=True)
    return df, raw_dump


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def save_outputs(df: pd.DataFrame, raw_dump: dict, run_date: str) -> str:
    """Save engine-ready CSV and raw JSON. Returns path to CSV."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    csv_path  = os.path.join(OUTPUT_DIR, f"{run_date}_fixtures.csv")
    json_path = os.path.join(OUTPUT_DIR, f"{run_date}_fixtures_raw.json")

    engine_cols = ["Div", "Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR",
                   "B365H", "B365D", "B365A"]
    df[engine_cols].to_csv(csv_path, index=False)

    with open(json_path, "w") as f:
        json.dump(raw_dump, f, indent=2, default=str)

    print(f"\n  Engine CSV : {csv_path}")
    print(f"  Raw JSON   : {json_path}")
    return csv_path


def print_summary(df: pd.DataFrame) -> None:
    """Print a human-readable summary of what was fetched."""
    print(f"\n{'='*66}")
    print(f"  DataBot -- Fixture Summary")
    print(f"{'='*66}")

    upcoming = df[df["FTR"] == ""]
    finished = df[df["FTR"] != ""]

    print(f"\n  Total    : {len(df)} fixtures")
    print(f"  Upcoming : {len(upcoming)}")
    print(f"  Finished : {len(finished)}")

    if not upcoming.empty:
        print(f"\n  {'Tier':<5}  {'Date':<12}  {'Home':<22}  {'Away':<22}  {'H':>5}  {'D':>5}  {'A':>5}")
        print(f"  {'-'*82}")
        for _, row in upcoming.iterrows():
            h = f"{row['B365H']:.2f}" if pd.notna(row.get("B365H")) and row.get("B365H") else "  -  "
            d = f"{row['B365D']:.2f}" if pd.notna(row.get("B365D")) and row.get("B365D") else "  -  "
            a = f"{row['B365A']:.2f}" if pd.notna(row.get("B365A")) and row.get("B365A") else "  -  "
            print(f"  {row['Div']:<5}  {row['Date']:<12}  {row['HomeTeam']:<22}  {row['AwayTeam']:<22}  {h:>5}  {d:>5}  {a:>5}")

    if not finished.empty:
        print(f"\n  Finished results:")
        for _, row in finished.iterrows():
            print(f"  {row['Div']:<5}  {row['Date']:<12}  {row['HomeTeam']:<22}  {row['FTHG']}-{row['FTAG']}  {row['AwayTeam']:<22}  [{row['FTR']}]")

    print(f"\n{'='*66}\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="EdgeLab DataBot -- fixture + odds puller")
    parser.add_argument("--key",      required=True, help="API-Football API key")
    parser.add_argument("--days",     type=int, default=7,
                        help="Days ahead to fetch from today (default: 7)")
    parser.add_argument("--date",     type=str, default=None,
                        help="Fetch a specific date only, YYYY-MM-DD (overrides --days)")
    parser.add_argument("--no-odds",  action="store_true",
                        help="Skip odds fetching (faster, saves API calls)")
    parser.add_argument("--test",     action="store_true",
                        help="Connection test only -- no fixtures fetched")
    args = parser.parse_args()

    print("\n╔══════════════════════════════════════════╗")
    print("║        EdgeLab DataBot v1                ║")
    print("╚══════════════════════════════════════════╝")

    client = APIFootballClient(args.key)

    if not client.test_connection():
        sys.exit(1)

    if args.test:
        print("\n  --test flag: connection confirmed. Exiting.\n")
        sys.exit(0)

    # Determine date range
    today = datetime.today()
    if args.date:
        try:
            from_dt = datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            print(f"  Invalid date: {args.date} -- use YYYY-MM-DD")
            sys.exit(1)
        to_dt = from_dt
    else:
        from_dt = today
        to_dt   = today + timedelta(days=args.days - 1)

    from_date = from_dt.strftime("%Y-%m-%d")
    to_date   = to_dt.strftime("%Y-%m-%d")
    run_date  = today.strftime("%Y-%m-%d")

    print(f"\n  Date range : {from_date} -> {to_date}")
    print(f"  Tiers      : {', '.join(LEAGUE_MAP.keys())}")
    print(f"  Odds       : {'yes (Bet365)' if not args.no_odds else 'skipped'}")
    print(f"  Output dir : {OUTPUT_DIR}/\n")

    result = build_dataframe(
        client=client,
        from_date=from_date,
        to_date=to_date,
        fetch_odds_flag=not args.no_odds,
    )

    df, raw_dump = result

    if df.empty:
        print("\n  No fixtures found for this period.")
        sys.exit(0)

    save_outputs(df, raw_dump, run_date)
    print_summary(df)

    print(f"  API calls this run : {client.calls_made}")
    print(f"\n  Next step -- run predictions:")
    print(f"    python edgelab_engine.py {OUTPUT_DIR}/\n")


if __name__ == "__main__":
    main()
