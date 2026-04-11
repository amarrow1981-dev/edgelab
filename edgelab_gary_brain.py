#!/usr/bin/env python3
"""
EdgeLab Gary Brain v1
---------------------
Data access layer for Gary's knowledge schema.

Given a home team, away team, date, and tier — queries the historical CSV data
and returns a fully populated GaryContext object matching schema v1.0.

Schema sections populated in v1:
  ✓ MATCH_CONTEXT    — fixture facts, league positions (approx from form data)
  ✓ FORM             — last 5 results, goals, clean sheets, current streak
  ✓ H2H              — last 6 meetings, win/draw/loss rates, bogey flag
  ✓ MATCH_FLAGS      — post-intl-break, fixture congestion, rest days
  ✓ WORLD_CONTEXT    — static event table, crowd context (Covid etc.)
  ✓ ENGINE_OUTPUT    — receives pre-computed engine output dict
  — GARY_MEMORY      — all SLOTs, populated when those systems exist

Usage:
    from edgelab_gary_brain import GaryBrain, build_engine_output_block

    brain = GaryBrain("history/")
    ctx = brain.build_context(
        home_team="Wigan Athletic",
        away_team="Leyton Orient",
        match_date="2026-04-02",
        tier="E2",
        engine_output=build_engine_output_block(prediction_row),
    )
    print(ctx)  # human-readable summary
    gary_dict = ctx.to_dict()  # structured dict to pass to Claude API
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any

import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from edgelab_engine import load_all_csvs

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING, format="[GaryBrain] %(message)s")


# ---------------------------------------------------------------------------
# World Context — static event table
# Crowd events and macro world events with date ranges.
# New events are added here as rows. Gary reads this automatically.
# ---------------------------------------------------------------------------

WORLD_EVENTS = [
    # Covid — behind closed doors
    {
        "start": "2020-03-13",
        "end":   "2021-05-17",
        "event_type": "pandemic",
        "severity_tier": "CRITICAL",
        "crowd_context": "behind_closed_doors",
        "event_description": "COVID-19 pandemic. Football suspended then played behind closed doors. Home advantage data from this period is unreliable.",
    },
    # Covid — reduced capacity (return of fans, limited numbers)
    {
        "start": "2021-05-18",
        "end":   "2021-09-01",
        "event_type": "pandemic",
        "severity_tier": "HIGH",
        "crowd_context": "reduced_capacity",
        "event_description": "Post-COVID partial return of fans. Crowd sizes restricted. Home advantage still suppressed.",
    },
    # Ukraine invasion — collective European anxiety
    {
        "start": "2022-02-24",
        "end":   "2022-05-31",
        "event_type": "conflict",
        "severity_tier": "HIGH",
        "crowd_context": "normal",
        "event_description": "Russian invasion of Ukraine. Significant collective anxiety across Europe during this period.",
    },
    # Queen Elizabeth II death — national event, UK mood shift
    {
        "start": "2022-09-08",
        "end":   "2022-09-19",
        "event_type": "national_event",
        "severity_tier": "MED",
        "crowd_context": "normal",
        "event_description": "Death of Queen Elizabeth II. Round of matches postponed. National period of mourning in the UK.",
    },
    # UK cost of living crisis peak
    {
        "start": "2022-10-01",
        "end":   "2023-04-01",
        "event_type": "economic_shock",
        "severity_tier": "MED",
        "crowd_context": "normal",
        "event_description": "UK cost of living crisis peak. Energy prices, inflation at 40-year highs. Potential effect on attendance and away support.",
    },
]

# International break dates (approximate — English football calendar)
# Format: (start_date, end_date)
INTERNATIONAL_BREAKS = [
    # 2024-25 season
    ("2024-09-02", "2024-09-10"),
    ("2024-10-07", "2024-10-15"),
    ("2024-11-11", "2024-11-19"),
    ("2025-03-17", "2025-03-25"),
    # 2025-26 season
    ("2025-09-01", "2025-09-09"),
    ("2025-10-06", "2025-10-14"),
    ("2025-11-10", "2025-11-18"),
    ("2026-03-23", "2026-03-31"),
]


# ---------------------------------------------------------------------------
# Schema dataclasses — mirror schema v1.0 exactly
# ---------------------------------------------------------------------------

@dataclass
class MatchContextBlock:
    home_team: str
    away_team: str
    date: str
    tier: str
    kickoff: Optional[str] = None
    # League positions — populated if standings data available, else None
    home_position: Optional[int] = None
    away_position: Optional[int] = None
    home_points: Optional[int] = None
    away_points: Optional[int] = None
    home_gd_season: Optional[int] = None   # season cumulative GD
    away_gd_season: Optional[int] = None


@dataclass
class TeamFormBlock:
    """Form for one team."""
    last5_results: List[str] = field(default_factory=list)     # e.g. ["W","W","D","L","W"]
    last5_goals_scored: List[int] = field(default_factory=list)
    last5_goals_conceded: List[int] = field(default_factory=list)
    last5_clean_sheets: int = 0
    current_streak: str = ""   # e.g. "W3" / "D1" / "L2"
    avg_goals_scored: float = 0.0
    avg_goals_conceded: float = 0.0
    form_score: float = 0.0    # engine form score (0-1)


@dataclass
class FormBlock:
    home: TeamFormBlock = field(default_factory=TeamFormBlock)
    away: TeamFormBlock = field(default_factory=TeamFormBlock)


@dataclass
class H2HMeeting:
    date: str
    home_team: str
    away_team: str
    score: str        # e.g. "2-1"
    result: str       # H / D / A (from home team perspective at that fixture)


@dataclass
class H2HBlock:
    last8_meetings: List[H2HMeeting] = field(default_factory=list)
    h2h_home_win_rate: float = 0.0    # home team win rate in H2H (current home team)
    h2h_draw_rate: float = 0.0
    h2h_away_win_rate: float = 0.0
    bogey_flag: bool = False
    bogey_direction: Optional[str] = None   # e.g. "Wigan struggles vs Leyton Orient"
    meetings_found: int = 0


@dataclass
class MatchFlagsBlock:
    post_international_break: bool = False
    days_since_break: Optional[int] = None
    dead_rubber: bool = False          # motivation-derived
    relegation_battle: bool = False    # motivation-derived
    promotion_chase: bool = False      # motivation-derived
    six_pointer_flag: bool = False     # both teams in same zone
    fixture_congestion_home: bool = False
    fixture_congestion_away: bool = False
    rest_days_home: Optional[int] = None
    rest_days_away: Optional[int] = None
    # External Signal Layer — Phase 1 (session 14)
    travel_km: Optional[float] = None          # away team journey distance
    travel_load: Optional[float] = None        # normalised 0-1 travel burden
    travel_description: Optional[str] = None   # plain English e.g. "Marathon journey — 380km"
    is_midweek: bool = False
    bank_holiday_flag: bool = False
    festive_flag: bool = False
    timing_signal: Optional[float] = None      # 0-1 disruption signal
    timing_description: Optional[str] = None   # plain English
    home_motivation: Optional[float] = None    # 0-1 motivation score
    away_motivation: Optional[float] = None
    motivation_gap: Optional[float] = None     # home - away
    referee_name: Optional[str] = None
    referee_home_rate: Optional[float] = None
    referee_bias_description: Optional[str] = None
    # SLOTs
    injury_index: None = None          # SLOT — future
    # External Signal Layer — Phase 2 (session 16) — weather
    weather_load: Optional[float] = None             # normalised 0-1 conditions signal
    weather_description: Optional[str] = None        # plain English e.g. "Heavy rain, strong wind"
    weather_flag: bool = False                        # True if conditions significant enough to mention


@dataclass
class WorldContextBlock:
    world_event_flag: bool = False
    event_type: Optional[str] = None
    severity_tier: Optional[str] = None
    crowd_context: str = "normal"
    event_description: Optional[str] = None
    # SLOTs
    sentiment_index: None = None       # SLOT — news API
    social_mood_score: None = None     # SLOT — future


@dataclass
class EngineOutputBlock:
    prediction: Optional[str] = None
    confidence: Optional[float] = None
    dti: Optional[float] = None
    chaos_tier: Optional[str] = None
    draw_score: Optional[float] = None
    approx_draw_flag: Optional[bool] = None
    upset_score: Optional[float] = None
    upset_flag: Optional[bool] = None
    pred_scoreline: Optional[str] = None
    btts_flag: Optional[bool] = None
    # SLOTs
    signal_ledger_context: None = None   # SLOT
    team_chaos_index: None = None        # SLOT
    bogey_team_alert: None = None        # SLOT
    weekly_scoring_index: None = None    # SLOT
    player_dpol_output: None = None      # SLOT


@dataclass
class GaryMemoryBlock:
    """All SLOTs — nothing populated until those systems exist."""
    signal_performance_ledger: None = None
    pattern_memory: None = None
    meta_learning_context: None = None
    param_resurrection_candidates: None = None
    sport_specific_context: None = None


@dataclass
class GaryContext:
    """
    The full assembled brain context for a single match.
    This is what Gary receives before forming an opinion.
    """
    match_context: MatchContextBlock
    form: FormBlock
    h2h: H2HBlock
    match_flags: MatchFlagsBlock
    world_context: WorldContextBlock
    engine_output: EngineOutputBlock
    gary_memory: GaryMemoryBlock = field(default_factory=GaryMemoryBlock)

    def to_dict(self) -> dict:
        """Serialise to dict for Claude API / JSON."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def __str__(self) -> str:
        """Human-readable summary for terminal output / debugging."""
        ctx = self.match_context
        f = self.form
        h = self.h2h
        e = self.engine_output
        wc = self.world_context
        fl = self.match_flags

        lines = [
            f"\n{'='*66}",
            f"  GARY'S BRAIN — {ctx.home_team} vs {ctx.away_team}",
            f"  {ctx.tier}  |  {ctx.date}",
            f"{'='*66}",
        ]

        # Engine output
        if e.prediction:
            conf_str = f"{e.confidence:.0%}" if e.confidence else "?"
            lines.append(f"\n  ENGINE: {e.prediction}  ({conf_str} confidence)  "
                         f"DTI={e.dti:.3f}  Chaos={e.chaos_tier}")
            if e.pred_scoreline:
                lines.append(f"  Scoreline: {e.pred_scoreline}  BTTS={'YES' if e.btts_flag else 'NO'}")
            if e.upset_flag:
                lines.append(f"  ⚠  UPSET FLAG  (score={e.upset_score:.2f})")
            if e.approx_draw_flag:
                lines.append(f"  ~D  DRAW CANDIDATE  (draw_score={e.draw_score:.2f})")

        # Form
        lines.append(f"\n  FORM (last 5):")
        lines.append(f"    {ctx.home_team:<25} {' '.join(f.home.last5_results):<15} "
                     f"GS:{f.home.avg_goals_scored:.1f}  GC:{f.home.avg_goals_conceded:.1f}  "
                     f"Streak:{f.home.current_streak}")
        lines.append(f"    {ctx.away_team:<25} {' '.join(f.away.last5_results):<15} "
                     f"GS:{f.away.avg_goals_scored:.1f}  GC:{f.away.avg_goals_conceded:.1f}  "
                     f"Streak:{f.away.current_streak}")

        # H2H
        if h.meetings_found > 0:
            lines.append(f"\n  H2H (last {h.meetings_found} meetings):")
            for m in h.last8_meetings:
                lines.append(f"    {m.date}  {m.home_team} {m.score} {m.away_team}  [{m.result}]")
            lines.append(f"    Rates — H:{h.h2h_home_win_rate:.0%}  D:{h.h2h_draw_rate:.0%}  "
                         f"A:{h.h2h_away_win_rate:.0%}")
            if h.bogey_flag:
                lines.append(f"  ⚠  BOGEY: {h.bogey_direction}")
        else:
            lines.append(f"\n  H2H: No meetings found in dataset")

        # Match flags
        flag_items = []
        if fl.post_international_break:
            flag_items.append(f"POST-INTL-BREAK ({fl.days_since_break}d)")
        if fl.fixture_congestion_home:
            flag_items.append(f"{ctx.home_team.split()[0]} CONGESTED")
        if fl.fixture_congestion_away:
            flag_items.append(f"{ctx.away_team.split()[0]} CONGESTED")
        if fl.rest_days_home is not None:
            flag_items.append(f"Rest: {ctx.home_team.split()[0]}={fl.rest_days_home}d / "
                              f"{ctx.away_team.split()[0]}={fl.rest_days_away}d")
        if flag_items:
            lines.append(f"\n  FLAGS: {' | '.join(flag_items)}")

        # World context
        if wc.world_event_flag:
            lines.append(f"\n  WORLD: [{wc.severity_tier}] {wc.event_type.upper()}  "
                         f"Crowd: {wc.crowd_context}")
            lines.append(f"    {wc.event_description}")

        lines.append(f"\n{'='*66}\n")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helper: build EngineOutputBlock from a predictions DataFrame row
# ---------------------------------------------------------------------------

def build_engine_output_block(row: pd.Series) -> EngineOutputBlock:
    """
    Convert a row from edgelab_predict output into an EngineOutputBlock.
    Pass in a single row from the predictions DataFrame.
    """
    def _get(key, default=None):
        val = row.get(key, default)
        return None if pd.isna(val) else val

    return EngineOutputBlock(
        prediction=_get("prediction"),
        confidence=_get("confidence"),
        dti=_get("dti"),
        chaos_tier=_get("chaos_tier"),
        draw_score=_get("draw_score"),
        approx_draw_flag=bool(_get("approx_draw_flag", False)),
        upset_score=_get("upset_score"),
        upset_flag=bool(_get("upset_flag", 0)),
        pred_scoreline=_get("pred_scoreline"),
        btts_flag=bool(_get("btts_flag", False)),
    )


# ---------------------------------------------------------------------------
# GaryBrain — main class
# ---------------------------------------------------------------------------

class GaryBrain:
    """
    The data access layer for Gary's knowledge schema.

    Loads historical data once, then answers queries about any fixture.
    Designed to be instantiated once at startup and reused across many matches.
    """

    def __init__(self, data_folder: str):
        """
        Load all historical CSVs. This is the only I/O at startup.

        Args:
            data_folder: Path to folder containing historical CSV files.
        """
        print(f"  [GaryBrain] Loading historical data from {data_folder}...")
        self.df = load_all_csvs(data_folder)
        self.df = self.df.sort_values("parsed_date").reset_index(drop=True)
        n = len(self.df)
        tiers = sorted(self.df["tier"].unique())
        seasons = self.df["season"].nunique()
        print(f"  [GaryBrain] Ready — {n:,} matches | {len(tiers)} tiers | {seasons} seasons")

    # -----------------------------------------------------------------------
    # Main entry point
    # -----------------------------------------------------------------------

    def build_context(
        self,
        home_team: str,
        away_team: str,
        match_date: str,
        tier: str,
        engine_output: Optional[EngineOutputBlock] = None,
    ) -> GaryContext:
        """
        Build a full GaryContext for a fixture.

        Args:
            home_team:    Exact team name as it appears in the CSV data
            away_team:    Exact team name as it appears in the CSV data
            match_date:   ISO format date string e.g. "2026-04-05"
            tier:         League tier e.g. "E0", "E1", "E2", "E3", "EC"
            engine_output: Optional pre-built EngineOutputBlock from predictions

        Returns:
            GaryContext — fully populated schema object
        """
        dt = pd.to_datetime(match_date)

        # All history for this tier up to (but not including) this match date
        df_tier = self.df[
            (self.df["tier"] == tier) &
            (self.df["parsed_date"] < dt)
        ].copy()

        match_ctx   = self._build_match_context(home_team, away_team, match_date, tier, df_tier)
        form        = self._build_form(home_team, away_team, df_tier)
        h2h         = self._build_h2h(home_team, away_team, df_tier)
        flags       = self._build_match_flags(home_team, away_team, dt, df_tier)
        world_ctx   = self._build_world_context(dt)
        eng_out     = engine_output if engine_output is not None else EngineOutputBlock()

        return GaryContext(
            match_context=match_ctx,
            form=form,
            h2h=h2h,
            match_flags=flags,
            world_context=world_ctx,
            engine_output=eng_out,
            gary_memory=GaryMemoryBlock(),
        )

    # -----------------------------------------------------------------------
    # MATCH_CONTEXT
    # -----------------------------------------------------------------------

    def _build_match_context(
        self, home_team: str, away_team: str,
        match_date: str, tier: str, df_tier: pd.DataFrame
    ) -> MatchContextBlock:

        # Approximate league position: rank teams by cumulative points in current season
        # "Current season" = most recent season with data before match date
        pos_home = pos_away = pts_home = pts_away = gd_home = gd_away = None

        if not df_tier.empty:
            latest_season = df_tier["season"].iloc[-1]
            df_season = df_tier[df_tier["season"] == latest_season]

            if not df_season.empty:
                standings = self._compute_standings(df_season)
                pos_home  = standings.get(home_team, {}).get("position")
                pos_away  = standings.get(away_team, {}).get("position")
                pts_home  = standings.get(home_team, {}).get("points")
                pts_away  = standings.get(away_team, {}).get("points")
                gd_home   = standings.get(home_team, {}).get("gd")
                gd_away   = standings.get(away_team, {}).get("gd")

        return MatchContextBlock(
            home_team=home_team,
            away_team=away_team,
            date=match_date,
            tier=tier,
            home_position=pos_home,
            away_position=pos_away,
            home_points=pts_home,
            away_points=pts_away,
            home_gd_season=gd_home,
            away_gd_season=gd_away,
        )

    def _compute_standings(self, df_season: pd.DataFrame) -> Dict[str, dict]:
        """
        Compute basic standings table from a season's results.
        Returns dict of {team_name: {points, gd, played, position}}.
        """
        teams: Dict[str, dict] = {}

        def get(t):
            if t not in teams:
                teams[t] = {"points": 0, "gd": 0, "played": 0}
            return teams[t]

        for _, row in df_season.iterrows():
            ht, at = row["HomeTeam"], row["AwayTeam"]
            hg, ag = int(row["FTHG"]), int(row["FTAG"])
            ftr = row["FTR"]

            get(ht)["played"] += 1
            get(at)["played"] += 1
            get(ht)["gd"] += (hg - ag)
            get(at)["gd"] += (ag - hg)

            if ftr == "H":
                get(ht)["points"] += 3
            elif ftr == "A":
                get(at)["points"] += 3
            else:
                get(ht)["points"] += 1
                get(at)["points"] += 1

        # Sort by points then GD
        sorted_teams = sorted(
            teams.items(),
            key=lambda x: (x[1]["points"], x[1]["gd"]),
            reverse=True
        )
        for i, (team, stats) in enumerate(sorted_teams, 1):
            teams[team]["position"] = i

        return teams

    # -----------------------------------------------------------------------
    # FORM
    # -----------------------------------------------------------------------

    def _build_form(
        self, home_team: str, away_team: str, df_tier: pd.DataFrame
    ) -> FormBlock:
        home_form = self._team_form(home_team, df_tier)
        away_form = self._team_form(away_team, df_tier)
        return FormBlock(home=home_form, away=away_form)

    def _team_form(self, team: str, df_tier: pd.DataFrame, window: int = 5) -> TeamFormBlock:
        """Get last `window` matches for a team and build form block."""
        # All matches involving this team
        mask = (df_tier["HomeTeam"] == team) | (df_tier["AwayTeam"] == team)
        df_team = df_tier[mask].sort_values("parsed_date").tail(window)

        if df_team.empty:
            return TeamFormBlock(current_streak="?")

        results = []
        goals_scored = []
        goals_conceded = []
        clean_sheets = 0

        for _, row in df_team.iterrows():
            is_home = row["HomeTeam"] == team
            ftr = row["FTR"]
            hg, ag = int(row["FTHG"]), int(row["FTAG"])

            if is_home:
                gs, gc = hg, ag
                outcome = "W" if ftr == "H" else ("D" if ftr == "D" else "L")
            else:
                gs, gc = ag, hg
                outcome = "W" if ftr == "A" else ("D" if ftr == "D" else "L")

            results.append(outcome)
            goals_scored.append(gs)
            goals_conceded.append(gc)
            if gc == 0:
                clean_sheets += 1

        # Current streak
        streak = self._compute_streak(results)

        # Form score (wins=1, draws=0.4, losses=0)
        score_map = {"W": 1.0, "D": 0.4, "L": 0.0}
        form_score = float(np.mean([score_map[r] for r in results])) if results else 0.5

        return TeamFormBlock(
            last5_results=results,
            last5_goals_scored=goals_scored,
            last5_goals_conceded=goals_conceded,
            last5_clean_sheets=clean_sheets,
            current_streak=streak,
            avg_goals_scored=round(float(np.mean(goals_scored)), 2) if goals_scored else 0.0,
            avg_goals_conceded=round(float(np.mean(goals_conceded)), 2) if goals_conceded else 0.0,
            form_score=round(form_score, 3),
        )

    def _compute_streak(self, results: List[str]) -> str:
        """e.g. ["W","W","D","L","W"] -> "W1" (most recent)"""
        if not results:
            return ""
        latest = results[-1]
        count = 0
        for r in reversed(results):
            if r == latest:
                count += 1
            else:
                break
        return f"{latest}{count}"

    # -----------------------------------------------------------------------
    # H2H
    # -----------------------------------------------------------------------

    def _build_h2h(
        self, home_team: str, away_team: str, df_tier: pd.DataFrame, window: int = 8
    ) -> H2HBlock:
        """
        Find all historical meetings between these two teams.
        Meetings can be in either home/away configuration.
        """
        mask = (
            ((df_tier["HomeTeam"] == home_team) & (df_tier["AwayTeam"] == away_team)) |
            ((df_tier["HomeTeam"] == away_team) & (df_tier["AwayTeam"] == home_team))
        )
        df_h2h = df_tier[mask].sort_values("parsed_date").tail(window)

        if df_h2h.empty:
            return H2HBlock()

        meetings = []
        # From the perspective of the current home team
        home_wins = draws = away_wins = 0

        for _, row in df_h2h.iterrows():
            ht, at = row["HomeTeam"], row["AwayTeam"]
            hg, ag = int(row["FTHG"]), int(row["FTAG"])
            ftr = row["FTR"]
            score = f"{hg}-{ag}"
            date_str = row["parsed_date"].strftime("%Y-%m-%d")

            # Translate result into current home team perspective
            if ht == home_team:
                result_from_home = ftr   # H = current home team won, etc.
            else:
                # Roles flipped — away team was home in this meeting
                if ftr == "H":
                    result_from_home = "A"   # away team (now home) won
                elif ftr == "A":
                    result_from_home = "H"
                else:
                    result_from_home = "D"

            if result_from_home == "H":
                home_wins += 1
            elif result_from_home == "D":
                draws += 1
            else:
                away_wins += 1

            meetings.append(H2HMeeting(
                date=date_str,
                home_team=ht,
                away_team=at,
                score=score,
                result=ftr,
            ))

        n = len(meetings)
        h_rate = round(home_wins / n, 3)
        d_rate  = round(draws / n, 3)
        a_rate  = round(away_wins / n, 3)

        # Bogey flag: one team wins 70%+ of meetings
        bogey_flag = False
        bogey_direction = None
        if h_rate >= 0.625:
            bogey_flag = True
            bogey_direction = f"{away_team} struggles vs {home_team}"
        elif a_rate >= 0.625:
            bogey_flag = True
            bogey_direction = f"{home_team} struggles vs {away_team}"

        return H2HBlock(
            last8_meetings=meetings,
            h2h_home_win_rate=h_rate,
            h2h_draw_rate=d_rate,
            h2h_away_win_rate=a_rate,
            bogey_flag=bogey_flag,
            bogey_direction=bogey_direction,
            meetings_found=n,
        )

    # -----------------------------------------------------------------------
    # MATCH_FLAGS
    # -----------------------------------------------------------------------

    def _build_match_flags(
        self, home_team: str, away_team: str, match_dt: datetime, df_tier: pd.DataFrame
    ) -> MatchFlagsBlock:

        # Post-international break?
        post_break, days_since = self._check_international_break(match_dt)

        # Rest days — how many days since last match for each team
        rest_home = self._days_since_last_match(home_team, match_dt, df_tier)
        rest_away = self._days_since_last_match(away_team, match_dt, df_tier)

        # Fixture congestion: played within last 4 days
        CONGESTION_THRESH = 4
        congestion_home = rest_home is not None and rest_home <= CONGESTION_THRESH
        congestion_away = rest_away is not None and rest_away <= CONGESTION_THRESH

        # Phase 1 external signals
        try:
            from edgelab_signals import get_signal_context

            # Get approximate standings for motivation
            home_pos = away_pos = home_pts = away_pts = None
            if not df_tier.empty:
                latest_season = df_tier["season"].iloc[-1]
                df_season = df_tier[df_tier["season"] == latest_season]
                if not df_season.empty:
                    standings = self._compute_standings(df_season)
                    home_pos = standings.get(home_team, {}).get("position")
                    away_pos = standings.get(away_team, {}).get("position")
                    home_pts = standings.get(home_team, {}).get("points")
                    away_pts = standings.get(away_team, {}).get("points")

            tier = df_tier["tier"].iloc[0] if not df_tier.empty else "E1"
            matches_played = max(0, (match_dt - pd.to_datetime(
                f"{str(match_dt.year if match_dt.month >= 8 else match_dt.year - 1)}-08-01"
            )).days // 7)

            sig_ctx = get_signal_context(
                home_team=home_team, away_team=away_team,
                match_date=match_dt.strftime("%Y-%m-%d"), tier=tier,
                home_pos=home_pos, away_pos=away_pos,
                home_pts=home_pts, away_pts=away_pts,
                matches_played=matches_played,
            )
            mot = sig_ctx["motivation"]

            # Phase 2 — weather (graceful fallback if module unavailable)
            wx_load = wx_desc = None
            wx_flag = False
            try:
                from edgelab_weather import get_weather_for_fixture
                wx = get_weather_for_fixture(
                    home_team=home_team,
                    match_date=match_dt.strftime("%Y-%m-%d"),
                    kickoff_hour=15,
                    tier=tier,
                )
                if wx["source"] != "unavailable":
                    wx_load = wx["weather_load"]
                    wx_desc = wx["weather_description"]
                    wx_flag = wx["weather_flag"]
            except ImportError:
                pass  # weather module optional

            return MatchFlagsBlock(
                post_international_break=post_break,
                days_since_break=days_since,
                dead_rubber=mot["dead_rubber_flag"],
                six_pointer_flag=mot["six_pointer_flag"],
                fixture_congestion_home=congestion_home,
                fixture_congestion_away=congestion_away,
                rest_days_home=rest_home,
                rest_days_away=rest_away,
                travel_km=sig_ctx["travel_km"],
                travel_load=sig_ctx["travel_load"],
                travel_description=sig_ctx["travel_description"],
                is_midweek=sig_ctx["is_midweek"],
                bank_holiday_flag=sig_ctx["bank_holiday_flag"],
                festive_flag=sig_ctx["festive_flag"],
                timing_signal=sig_ctx["timing_signal"],
                timing_description=sig_ctx["timing_description"],
                home_motivation=mot["home_motivation"],
                away_motivation=mot["away_motivation"],
                motivation_gap=mot["motivation_gap"],
                weather_load=wx_load,
                weather_description=wx_desc,
                weather_flag=wx_flag,
            )

        except ImportError:
            # signals module not available — fall back to basic flags only
            pass

        return MatchFlagsBlock(
            post_international_break=post_break,
            days_since_break=days_since,
            fixture_congestion_home=congestion_home,
            fixture_congestion_away=congestion_away,
            rest_days_home=rest_home,
            rest_days_away=rest_away,
        )

    def _check_international_break(self, match_dt: datetime) -> tuple:
        """Returns (is_post_break: bool, days_since_break: int|None)."""
        POST_BREAK_WINDOW = 7   # flag matches within 7 days of break ending

        for start_str, end_str in INTERNATIONAL_BREAKS:
            break_end = pd.to_datetime(end_str)
            break_start = pd.to_datetime(start_str)

            if break_start <= match_dt <= break_end:
                return True, 0   # match is during the break (unusual but possible)

            days_after = (match_dt - break_end).days
            if 0 < days_after <= POST_BREAK_WINDOW:
                return True, int(days_after)

        return False, None

    def _days_since_last_match(
        self, team: str, match_dt: datetime, df_tier: pd.DataFrame
    ) -> Optional[int]:
        """Days between last match and this fixture for a given team."""
        mask = (df_tier["HomeTeam"] == team) | (df_tier["AwayTeam"] == team)
        df_team = df_tier[mask].sort_values("parsed_date")

        if df_team.empty:
            return None

        last_match = df_team["parsed_date"].iloc[-1]
        return int((match_dt - last_match).days)

    # -----------------------------------------------------------------------
    # WORLD_CONTEXT
    # -----------------------------------------------------------------------

    def _build_world_context(self, match_dt: datetime) -> WorldContextBlock:
        """Check static world events table against match date."""
        for event in WORLD_EVENTS:
            start = pd.to_datetime(event["start"])
            end   = pd.to_datetime(event["end"])
            if start <= match_dt <= end:
                return WorldContextBlock(
                    world_event_flag=True,
                    event_type=event["event_type"],
                    severity_tier=event["severity_tier"],
                    crowd_context=event["crowd_context"],
                    event_description=event["event_description"],
                )

        return WorldContextBlock(world_event_flag=False, crowd_context="normal")


# ---------------------------------------------------------------------------
# Team name fuzzy matching — helps with slight name variations across seasons
# ---------------------------------------------------------------------------

def find_team_name(brain: GaryBrain, search: str, tier: str = None) -> List[str]:
    """
    Find team names in the dataset that match a search string.
    Useful for checking exact team names before building context.

    Example:
        find_team_name(brain, "wigan", "E2")
        -> ["Wigan Athletic"]
    """
    df = brain.df
    if tier:
        df = df[df["tier"] == tier]

    all_teams = pd.concat([df["HomeTeam"], df["AwayTeam"]]).unique()
    search_lower = search.lower()
    matches = [t for t in all_teams if search_lower in t.lower()]
    return sorted(set(matches))


# ---------------------------------------------------------------------------
# CLI — test a fixture lookup
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    data_folder = sys.argv[1] if len(sys.argv) > 1 else "history/"

    brain = GaryBrain(data_folder)

    # Default test: Wigan vs Leyton Orient (the first live result)
    home = sys.argv[2] if len(sys.argv) > 2 else "Wigan Athletic"
    away = sys.argv[3] if len(sys.argv) > 3 else "Leyton Orient"
    date = sys.argv[4] if len(sys.argv) > 4 else "2026-04-02"
    tier = sys.argv[5] if len(sys.argv) > 5 else "E2"

    # Check team names
    print(f"\n  Checking team names...")
    matches_h = find_team_name(brain, home.split()[0], tier)
    matches_a = find_team_name(brain, away.split()[0], tier)
    print(f"  '{home}' matches: {matches_h}")
    print(f"  '{away}' matches: {matches_a}")

    # Build context
    ctx = brain.build_context(
        home_team=home,
        away_team=away,
        match_date=date,
        tier=tier,
    )

    print(ctx)

    # Also dump JSON so we can see what Gary would receive
    out_path = f"gary_context_{home.split()[0].lower()}_{away.split()[0].lower()}.json"
    with open(out_path, "w") as f:
        f.write(ctx.to_json())
    print(f"  Context saved to {out_path}")
