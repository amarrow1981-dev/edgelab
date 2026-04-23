#!/usr/bin/env python3
"""
EdgeLab Engine v1
-----------------
Prediction engine for football results using form, goal difference,
home advantage, and DTI (Decision Tension Index).

Designed to work with:
- football-data.co.uk CSVs (E0, E1, etc.)
- EdgeLab DPOL via make_pred_fn()

Key outputs per match:
  - Prediction: H / D / A
  - Confidence: 0.0 - 1.0
  - DTI score: 0.0 - 1.0 (higher = more volatile / uncertain)
  - Chaos tier: LOW / MED / HIGH
"""

import os
import glob
import copy
import logging
from dataclasses import dataclass
from typing import List, Dict, Callable, Optional, Tuple

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[EdgeLab] %(message)s")


# ---------------------------------------------------------------------------
# Parameters (mirrors LeagueParams in DPOL — must stay in sync)
# ---------------------------------------------------------------------------

@dataclass
class EngineParams:
    w_form: float = 1.0           # weight applied to form score
    w_gd: float = 0.3             # weight applied to goal difference
    home_adv: float = 0.25        # flat home advantage bonus
    dti_edge_scale: float = 0.4   # DTI dampens form/GD signal
    dti_ha_scale: float = 0.5     # DTI dampens home advantage
    draw_margin: float = 0.12     # scores within this margin → draw
    coin_dti_thresh: float = 0.767 # DTI above this → flip uncertain draws to win
    form_window: int = 5          # how many recent matches to score form over
    draw_pull: float = 0.0        # disabled — no draw signal in current features
    dti_draw_lock: float = 999.0  # disabled — no draw signal in current features
    # --- Draw intelligence layer (session 6) ---
    w_draw_odds: float = 0.0      # weight of bookmaker implied draw probability
    w_draw_tendency: float = 0.0  # weight of team draw tendency signal
    w_h2h_draw: float = 0.0       # weight of H2H draw history signal
    draw_score_thresh: float = 0.55  # combined draw score above this → call draw
    # --- Score prediction layer (session 6) ---
    w_score_margin: float = 0.0   # weight of predicted goal margin signal (reinforces H/A calls)
    w_btts: float = 0.0           # weight of BTTS signal on draw probability
    # --- External Signal Layer — Phase 1 (session 14) ---
    # All start at 0.0. DPOL activates signals that correlate with outcomes.
    w_ref_signal:    float = 0.0  # referee home bias signal weight
    w_travel_load:   float = 0.0  # away travel distance disadvantage weight
    w_timing_signal: float = 0.0  # fixture timing disruption weight
    w_motivation_gap: float = 0.0 # home vs away motivation gap weight
    # --- External Signal Layer — Phase 2 (session 16) ---
    w_weather_signal: float = 0.0 # weather conditions burden weight (rain, wind, cold)
    # --- Composite draw signal layer (session 26) ---
    # Wired from draw evolution Pass 3 findings.
    # odds_draw_prob is the anchor signal (1.202x lift individually).
    # expected_goals_total is an independent draw signal (1.088x lift).
    # Composite gate fires when odds + supporting signal align simultaneously
    # — combinations reach 1.347x lift vs 1.202x individual best.
    # All weights start at 0.0 — inert until DPOL activates.
    w_xg_draw: float = 0.0           # weight of expected goals total as draw signal
                                      # low xG total (tight match) = draw-positive
    composite_draw_boost: float = 0.0 # additive boost to draw_score when composite
                                      # gate fires: odds_draw_prob > 0.288 AND at
                                      # least one supporting signal in draw-positive band
    # --- Fixture Specificity Layer (session 38) ---
    # All start at 0.0 — inert until DPOL activates.
    # These replace or supplement the averaging assumptions in the core engine.
    w_venue_form:    float = 0.0  # venue-split form weight vs blended form
                                   # home_form_home / away_form_away replace home_form / away_form
                                   # when this weight is active
    w_team_home_adv: float = 0.0  # team-specific home advantage weight
                                   # replaces flat home_adv when active
                                   # derived from each team's actual historical home record
    w_away_team_adv: float = 0.0  # away team's natural away strength weight
                                   # away team's historical away win rate vs their home win rate
                                   # Man City away at Burnley ≠ Man City away at Chelsea
                                   # evolved independently from w_team_home_adv — DPOL finds balance
    w_opp_strength:  float = 0.0  # opponent-adjusted form weight
                                   # weights each result in form window by opponent's GD
                                   # a win against a strong team scores higher than vs weak
    w_season_stage:  float = 0.0  # season stage signal weight
                                   # early season (low) vs late season (high) context
                                   # captures motivation, fatigue, nothing-to-play-for
    w_rest_diff:     float = 0.0  # rest days differential weight
                                   # positive = home team more rested, negative = away more rested
    # --- Layer Agreement Layer (session 41) ---
    # All start at 0.0 — inert until DPOL activates.
    # These allow DPOL to learn how much to trust agreement/disagreement
    # between the outcome layer and the scoreline map layer.
    w_scoreline_agreement:  float = 0.0  # confidence adjustment when outcome layer and
                                          # scoreline map layer agree or disagree on outcome.
                                          # agree → boost confidence; disagree → reduce.
                                          # read from top_scoreline_match outcome vs prediction.
    w_scoreline_confidence: float = 0.0  # confidence adjustment based on how clearly the
                                          # fixture matched one scoreline population vs many.
                                          # high clarity match → boost; scattered → reduce.
                                          # read from top_scoreline_match density score.


# ---------------------------------------------------------------------------
# CSV loading
# ---------------------------------------------------------------------------

def load_csv(path: str, tier: str, season_label: str) -> pd.DataFrame:
    """Load a single football-data CSV and normalise columns."""
    for enc in ("utf-8-sig", "latin-1", "cp1252"):
        try:
            raw = pd.read_csv(path, encoding=enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(f"Could not decode {path}")

    # Drop empty rows (some files have trailing blank lines)
    raw = raw.dropna(subset=["HomeTeam", "AwayTeam", "FTR"])

    # ---------------------------------------------------------------------------
    # Column retention — CSV Audit (Session 12)
    # Only keep columns with a defined purpose. Everything else is dropped.
    #
    # PRE-MATCH (available before kickoff — may feed prediction features):
    #   B365H/D/A       — Bet365 1X2 odds (draw intel, upset signal) [ACTIVE]
    #   B365>2.5/<2.5   — Over/Under 2.5 goals odds [PARKED — 31% coverage]
    #   HY/AY           — Yellow cards pre-match rolling [PARKED]
    #
    # POST-MATCH (only available after final whistle — analysis/DPOL/Gary only):
    #   HTHG/HTAG/HTR   — Half-time score [PARKED — pattern memory, Gary post-match]
    #   HS/AS           — Total shots [PARKED]
    #   HST/AST         — Shots on target — xG proxy [PARKED]
    #   HF/AF           — Fouls [PARKED]
    #   HC/AC           — Corners [PARKED]
    #   HR/AR           — Red cards — discipline signal [PARKED]
    #
    # DROPPED (noise — redundant bookmaker odds we don't use):
    #   BW/BF/PS/WH/1XB/Max/Avg/BFE odds, AH lines, closing odds (C prefix)
    # ---------------------------------------------------------------------------

    # Slice only the columns we want from the raw dataframe first,
    # then add computed columns — avoids pandas fragmentation warning.
    keep_from_csv = ["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"]

    pre_match_optional = [
        "B365H", "B365D", "B365A",
        "B365>2.5", "B365<2.5",
        "HY", "AY",
    ]
    post_match_optional = [
        "HTHG", "HTAG", "HTR",
        "HS", "AS",
        "HST", "AST",
        "HF", "AF",
        "HC", "AC",
        "HR", "AR",
    ]
    for col in pre_match_optional + post_match_optional:
        if col in raw.columns:
            keep_from_csv.append(col)

    df = raw[keep_from_csv].copy()

    # Now add computed columns cleanly (no fragmentation)
    df["parsed_date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["parsed_date"])
    df["tier"]   = tier
    df["season"] = season_label

    # Numeric coercion
    df["FTHG"] = pd.to_numeric(df["FTHG"], errors="coerce").fillna(0).astype(int)
    df["FTAG"] = pd.to_numeric(df["FTAG"], errors="coerce").fillna(0).astype(int)

    for col in ["B365H", "B365D", "B365A", "B365>2.5", "B365<2.5",
                "HTHG", "HTAG", "HS", "AS", "HST", "AST",
                "HF", "AF", "HC", "AC", "HY", "AY", "HR", "AR"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Reorder: computed cols first, then source cols
    final_cols = (["parsed_date", "tier", "season", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"] +
                  [c for c in pre_match_optional + post_match_optional if c in df.columns])
    df = df[final_cols].sort_values("parsed_date").reset_index(drop=True)
    return df


def load_all_csvs(folder: str, tiers: list = None) -> pd.DataFrame:
    """
    Load all football CSVs from a folder.
    Tier is detected from the Div column inside each file (E0, E1, E2, E3, EC).
    Optionally filter to specific tiers e.g. tiers=["E0","E1"].
    Returns a single combined DataFrame with tier and season columns.
    """
    frames = []
    skipped = []

    for path in sorted(glob.glob(os.path.join(folder, "*.csv"))):
        fname = os.path.basename(path)
        try:
            peek = pd.read_csv(path, encoding="utf-8-sig", nrows=1)
            if "Div" not in peek.columns or "FTR" not in peek.columns:
                skipped.append(fname)
                continue
            div = str(peek["Div"].iloc[0]).strip()
            if tiers and div not in tiers:
                continue
            df = load_csv(path, tier=div, season_label=fname)
            if len(df) > 0:
                frames.append(df)
        except Exception as e:
            skipped.append(f"{fname} ({e})")
            continue

    if skipped:
        logger.info(f"Skipped {len(skipped)} files: {skipped[:5]}{'...' if len(skipped)>5 else ''}")

    if not frames:
        raise FileNotFoundError(f"No valid football CSVs found in {folder}")

    combined = pd.concat(frames, ignore_index=True)
    tier_counts = combined.groupby("tier").size().to_dict()
    logger.info(f"Loaded {len(combined)} rows from {len(frames)} files. Tiers: {tier_counts}")
    return combined


# ---------------------------------------------------------------------------
# Feature calculation
# ---------------------------------------------------------------------------

def compute_form(df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    """
    For each match, compute rolling form score for home and away team
    based on the last `window` matches (wins=1, draws=0.4, losses=0).
    Returns df with added columns: home_form, away_form.
    """
    df = df.copy().reset_index(drop=True)

    team_results: Dict[str, List[float]] = {}
    home_forms = [0.0] * len(df)
    away_forms = [0.0] * len(df)

    hts = df["HomeTeam"].tolist()
    ats = df["AwayTeam"].tolist()
    ftrs = df["FTR"].tolist()

    for i in range(len(df)):
        ht, at, ftr = hts[i], ats[i], ftrs[i]
        hf = _rolling_form(team_results.get(ht, []), window)
        af = _rolling_form(team_results.get(at, []), window)
        home_forms[i] = hf
        away_forms[i] = af
        _update_history(team_results, ht, 1.0 if ftr == "H" else (0.4 if ftr == "D" else 0.0))
        _update_history(team_results, at, 1.0 if ftr == "A" else (0.4 if ftr == "D" else 0.0))

    df["home_form"] = home_forms
    df["away_form"] = away_forms
    return df


def _rolling_form(history: List[float], window: int) -> float:
    if not history:
        return 0.5  # neutral when no data
    recent = history[-window:]
    return float(np.mean(recent))


def _update_history(store: Dict[str, List[float]], team: str, score: float):
    if team not in store:
        store[team] = []
    store[team].append(score)


def compute_goal_diff(df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    """
    Rolling average goal difference per team over last `window` matches.
    Adds: home_gd, away_gd.
    """
    df = df.copy().reset_index(drop=True)

    team_gd: Dict[str, List[float]] = {}
    home_gds = [0.0] * len(df)
    away_gds  = [0.0] * len(df)

    hts    = df["HomeTeam"].tolist()
    ats    = df["AwayTeam"].tolist()
    hgoals = df["FTHG"].tolist()
    agoals = df["FTAG"].tolist()

    for i in range(len(df)):
        ht, at = hts[i], ats[i]
        home_gds[i] = _rolling_mean(team_gd.get(ht, []), window)
        away_gds[i] = _rolling_mean(team_gd.get(at, []), window)
        _update_history(team_gd, ht, int(hgoals[i]) - int(agoals[i]))
        _update_history(team_gd, at, int(agoals[i]) - int(hgoals[i]))

    df["home_gd"] = home_gds
    df["away_gd"] = away_gds
    return df


def _rolling_mean(history: List[float], window: int) -> float:
    if not history:
        return 0.0
    return float(np.mean(history[-window:]))


def compute_dti(df: pd.DataFrame) -> pd.DataFrame:
    """
    Decision Tension Index — how uncertain/volatile is this match?

    DTI is high when:
    - Form scores are very close
    - Goal difference is minimal
    - Both teams in middling form (no clear dominant side)

    Returns df with added column: dti (0.0 - 1.0)
    """
    df = df.copy()

    form_diff = (df["home_form"] - df["away_form"]).abs()
    gd_diff = (df["home_gd"] - df["away_gd"]).abs()

    # Normalise each component to 0-1 (inverted — closer = higher tension)
    max_form_diff = form_diff.max() if form_diff.max() > 0 else 1.0
    max_gd_diff = gd_diff.max() if gd_diff.max() > 0 else 1.0

    form_tension = 1.0 - (form_diff / max_form_diff)
    gd_tension = 1.0 - (gd_diff / max_gd_diff)

    # Midfield factor — teams neither dominant nor terrible have more tension
    avg_form = (df["home_form"] + df["away_form"]) / 2
    mid_factor = 1.0 - (2 * (avg_form - 0.5).abs())
    mid_factor = mid_factor.clip(0, 1)

    dti = (0.45 * form_tension + 0.35 * gd_tension + 0.20 * mid_factor).clip(0.0, 1.0)
    df["dti"] = dti.round(4)
    return df


def assign_chaos_tier(dti: float) -> str:
    if dti >= 0.75:
        return "HIGH"
    elif dti >= 0.50:
        return "MED"
    return "LOW"


# ---------------------------------------------------------------------------
# Tier-specific draw rate priors — verified against actual dataset S35
# Used as neutral fallback in all draw intelligence functions.
# Default 0.26 if tier not found.
# ---------------------------------------------------------------------------

TIER_DRAW_RATE = {
    "B1":  0.248,
    "D1":  0.247,
    "D2":  0.273,
    "E0":  0.245,
    "E1":  0.270,
    "E2":  0.264,
    "E3":  0.271,
    "EC":  0.254,
    "I1":  0.266,
    "I2":  0.321,
    "N1":  0.235,
    "SC0": 0.240,
    "SC1": 0.271,
    "SC2": 0.201,
    "SC3": 0.209,
    "SP1": 0.252,
    "SP2": 0.299,
}


def get_tier_draw_prior(df: pd.DataFrame) -> float:
    """Return tier-specific draw rate prior from the dataframe's tier column."""
    if "tier" in df.columns:
        tier = df["tier"].iloc[0] if len(df) > 0 else None
        if tier and tier in TIER_DRAW_RATE:
            return TIER_DRAW_RATE[tier]
    return 0.26


# ---------------------------------------------------------------------------
# Draw intelligence features (session 6)
# Three new signals built chronologically from raw match data.
# All use the same rolling-history pattern as form/GD — no lookahead.
# ---------------------------------------------------------------------------

def compute_team_draw_tendency(df: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    """
    For each match, compute the rolling draw rate for home and away team
    over their last  matches (any result: H, D, or A).

    Returns df with added columns:
      home_draw_rate  — home team's recent draw rate (0.0 – 1.0)
      away_draw_rate  — away team's recent draw rate (0.0 – 1.0)
    """
    df = df.copy().reset_index(drop=True)
    NEUTRAL = get_tier_draw_prior(df)  # tier-specific draw rate prior

    team_history: Dict[str, List[float]] = {}  # 1.0=draw, 0.0=non-draw
    home_rates = [NEUTRAL] * len(df)
    away_rates = [NEUTRAL] * len(df)

    hts  = df["HomeTeam"].tolist()
    ats  = df["AwayTeam"].tolist()
    ftrs = df["FTR"].tolist()

    for i in range(len(df)):
        ht, at, ftr = hts[i], ats[i], ftrs[i]
        # Use history if we have at least 3 matches, else neutral prior
        h_hist = team_history.get(ht, [])
        a_hist = team_history.get(at, [])
        home_rates[i] = float(np.mean(h_hist[-window:])) if len(h_hist) >= 3 else NEUTRAL
        away_rates[i] = float(np.mean(a_hist[-window:])) if len(a_hist) >= 3 else NEUTRAL
        # Update history (1 if draw, 0 otherwise)
        drew = 1.0 if ftr == "D" else 0.0
        _update_history(team_history, ht, drew)
        _update_history(team_history, at, drew)

    df["home_draw_rate"] = home_rates
    df["away_draw_rate"] = away_rates
    return df


def compute_h2h(df: pd.DataFrame, window: int = 6) -> pd.DataFrame:
    """
    For each match, compute head-to-head stats between the two teams
    using all previous meetings in the dataset (regardless of home/away).

    Returns df with added columns:
      h2h_draw_rate   — draw rate in past meetings (0.0 – 1.0)
      h2h_home_edge   — home team win rate minus away team win rate in past meetings
                        positive = home team historically stronger, negative = away stronger

    Both fall back to neutral values (0.26 draw, 0.0 edge) when < 2 meetings.
    H2H is identified as sorted (TeamA, TeamB) pair — symmetric.
    """
    df = df.copy().reset_index(drop=True)
    NEUTRAL_DRAW = get_tier_draw_prior(df)  # tier-specific draw rate prior
    NEUTRAL_EDGE = 0.0

    # h2h_store[pair] = list of (home_won, drew, away_won) tuples
    # pair = tuple(sorted([home, away]))
    h2h_store: Dict[tuple, List[tuple]] = {}

    h2h_draw_rates = [NEUTRAL_DRAW] * len(df)
    h2h_home_edges = [NEUTRAL_EDGE]  * len(df)

    hts  = df["HomeTeam"].tolist()
    ats  = df["AwayTeam"].tolist()
    ftrs = df["FTR"].tolist()

    for i in range(len(df)):
        ht, at, ftr = hts[i], ats[i], ftrs[i]
        pair = tuple(sorted([ht, at]))
        history = h2h_store.get(pair, [])

        if len(history) >= 2:
            recent = history[-window:]
            n      = len(recent)
            draws  = sum(1 for r in recent if r[1])
            h2h_draw_rates[i] = draws / n

            # Home edge: from perspective of TODAY's home team.
            # Count wins for each team across all past meetings regardless
            # of who was home in those meetings.
            # Positive = today's home team historically stronger.
            # Negative = today's away team historically stronger.
            ht_wins = sum(
                1 for r in recent
                if (r[3] == ht and r[0])   # today's HT was home and won
                or (r[3] == at and r[2])   # today's HT was away and won
            )
            at_wins = sum(
                1 for r in recent
                if (r[3] == at and r[0])   # today's AT was home and won
                or (r[3] == ht and r[2])   # today's AT was away and won
            )
            h2h_home_edges[i] = (ht_wins - at_wins) / n
        
        # Store: (home_won, drew, away_won, who_was_home)
        drew_flag     = ftr == "D"
        home_won_flag = ftr == "H"
        away_won_flag = ftr == "A"
        if pair not in h2h_store:
            h2h_store[pair] = []
        h2h_store[pair].append((home_won_flag, drew_flag, away_won_flag, ht))

    df["h2h_draw_rate"] = h2h_draw_rates
    df["h2h_home_edge"] = h2h_home_edges
    return df


def compute_score_prediction(df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    """
    Predict an expected scoreline for each match using rolling goals history.

    For each team we track:
      - goals_scored:   rolling avg goals scored per match
      - goals_conceded: rolling avg goals conceded per match

    Expected home goals = avg of (home team's scoring rate, away team's conceding rate)
    Expected away goals = avg of (away team's scoring rate, home team's conceding rate)

    Returns df with added columns:
      pred_home_goals   — raw expected home goals (float)
      pred_away_goals   — raw expected away goals (float)
      pred_scoreline    — display string e.g. "2-1"
      pred_margin       — pred_home_goals - pred_away_goals (signed, used as signal)
      btts_prob         — estimated both-teams-to-score probability (0.0 – 1.0)
                          derived from each team's historical scoring rate
      btts_flag         — 1 if btts_prob >= 0.5, else 0

    All use strictly prior data — no lookahead.
    Falls back to league average (1.5 goals each) before enough history exists.

    v2 improvements:
      - Venue-split goal tracking: home scoring rate vs away scoring rate tracked
        separately. Eliminates the main cause of result/scoreline contradictions.
      - H2H goal blending: blends team rates (75%) with H2H avg goals (25%)
        for fixture-specific context when >=2 prior meetings exist.
    """
    df = df.copy().reset_index(drop=True)

    LEAGUE_AVG_GOALS = 1.5   # neutral prior
    BTTS_THRESH      = 0.5
    H2H_WEIGHT       = 0.25  # 25% H2H, 75% team rolling rates
    H2H_MIN_MEETINGS = 2     # minimum meetings before H2H blend activates

    # Venue-split histories
    home_scored:   Dict[str, List[float]] = {}
    away_scored:   Dict[str, List[float]] = {}
    home_conceded: Dict[str, List[float]] = {}
    away_conceded: Dict[str, List[float]] = {}

    # H2H goal history: (who_was_home, home_goals, away_goals)
    h2h_goals: Dict[tuple, List[tuple]] = {}

    pred_home_goals = [LEAGUE_AVG_GOALS] * len(df)
    pred_away_goals = [LEAGUE_AVG_GOALS] * len(df)

    hts    = df["HomeTeam"].tolist()
    ats    = df["AwayTeam"].tolist()
    hgoals = df["FTHG"].tolist()
    agoals = df["FTAG"].tolist()

    for i in range(len(df)):
        ht, at = hts[i], ats[i]
        hg, ag = float(hgoals[i]), float(agoals[i])

        # ── Team rolling rates (venue-split) ────────────────────────────────
        ht_hs = home_scored.get(ht, [])
        at_ac = away_conceded.get(at, [])
        h_rate = _rolling_mean(ht_hs, window) if ht_hs else LEAGUE_AVG_GOALS
        a_conc = _rolling_mean(at_ac, window) if at_ac else LEAGUE_AVG_GOALS
        team_exp_home = (h_rate + a_conc) / 2.0

        at_as = away_scored.get(at, [])
        ht_hc = home_conceded.get(ht, [])
        a_rate = _rolling_mean(at_as, window) if at_as else LEAGUE_AVG_GOALS
        h_conc = _rolling_mean(ht_hc, window) if ht_hc else LEAGUE_AVG_GOALS
        team_exp_away = (a_rate + h_conc) / 2.0

        # ── H2H goal blend ───────────────────────────────────────────────────
        pair = tuple(sorted([ht, at]))
        h2h_history = h2h_goals.get(pair, [])

        if len(h2h_history) >= H2H_MIN_MEETINGS:
            recent = h2h_history[-6:]
            h2h_home_g, h2h_away_g = [], []
            for (rec_ht, rec_hg, rec_ag) in recent:
                if rec_ht == ht:
                    h2h_home_g.append(rec_hg)
                    h2h_away_g.append(rec_ag)
                else:
                    h2h_home_g.append(rec_ag)
                    h2h_away_g.append(rec_hg)
            h2h_exp_home = float(np.mean(h2h_home_g)) if h2h_home_g else team_exp_home
            h2h_exp_away = float(np.mean(h2h_away_g)) if h2h_away_g else team_exp_away
            exp_home = (1 - H2H_WEIGHT) * team_exp_home + H2H_WEIGHT * h2h_exp_home
            exp_away = (1 - H2H_WEIGHT) * team_exp_away + H2H_WEIGHT * h2h_exp_away
        else:
            exp_home = team_exp_home
            exp_away = team_exp_away

        pred_home_goals[i] = round(exp_home, 3)
        pred_away_goals[i] = round(exp_away, 3)

        # ── Update histories ─────────────────────────────────────────────────
        _update_history(home_scored,   ht, hg)
        _update_history(home_conceded, ht, ag)
        _update_history(away_scored,   at, ag)
        _update_history(away_conceded, at, hg)
        if pair not in h2h_goals:
            h2h_goals[pair] = []
        h2h_goals[pair].append((ht, hg, ag))

    phg = np.array(pred_home_goals)
    pag = np.array(pred_away_goals)

    # Scoreline: sample from Poisson distribution using expected goals as lambda.
    # This produces realistic variety (1-0, 2-0, 2-1, 3-1, 1-1 etc.) rather than
    # collapsing every ~1.6 vs ~0.8 match to 2-1 via naive rounding.
    # Seed is fixed per-row using the index so output is reproducible.
    rng = np.random.default_rng(seed=42)
    home_int = np.clip(rng.poisson(lam=np.maximum(phg, 0.1)), 0, 9)
    away_int = np.clip(rng.poisson(lam=np.maximum(pag, 0.1)), 0, 9)
    scorelines = [f"{h}-{a}" for h, a in zip(home_int, away_int)]

    # Flag when the scoreline predicts a draw — used by draw intelligence layer
    # to align ~D flag with scoreline. When both signals agree, the draw call
    # is much more reliable.
    pred_score_draw = (home_int == away_int).astype(int)

    # Predicted margin (signed float — used as a DPOL signal)
    pred_margin = phg - pag

    # BTTS probability — simplified: P(home scores) * P(away scores)
    # Estimate P(team scores) as: min(1, avg_goals_scored / 1.5)
    # Capped so a team averaging 3 goals doesn't give P=2.0
    p_home_scores = np.clip(phg / LEAGUE_AVG_GOALS, 0.0, 1.0)
    p_away_scores = np.clip(pag / LEAGUE_AVG_GOALS, 0.0, 1.0)
    btts_prob = (p_home_scores * p_away_scores).round(4)
    btts_flag = (btts_prob >= BTTS_THRESH).astype(int)

    df["pred_home_goals"]  = phg
    df["pred_away_goals"]  = pag
    df["pred_scoreline"]   = scorelines
    df["pred_margin"]      = pred_margin.round(3)
    df["pred_score_draw"]  = pred_score_draw   # 1 when scoreline is a draw
    df["btts_prob"]        = btts_prob
    df["btts_flag"]        = btts_flag

    return df


def compute_odds_draw_prob(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert B365D bookmaker draw odds to implied probability.
    Formula: implied_prob = 1 / B365D

    Note: bookmaker odds contain a margin (overround), so raw implied probabilities
    sum to > 1.0 across H/D/A. We normalise by the total implied probability across
    all three outcomes to get a fair market probability estimate.

    Returns df with added column:
      odds_draw_prob  — market's fair implied draw probability (0.0 – 1.0)
                        NaN rows fall back to league-average (0.26)
    """
    df = df.copy()
    NEUTRAL = get_tier_draw_prior(df)  # tier-specific draw rate prior

    if "B365D" not in df.columns:
        df["odds_draw_prob"] = NEUTRAL
        return df

    if "B365H" in df.columns and "B365A" in df.columns:
        # Normalised implied probability (removes bookmaker margin)
        imp_h = 1.0 / pd.to_numeric(df["B365H"], errors="coerce")
        imp_d = 1.0 / pd.to_numeric(df["B365D"], errors="coerce")
        imp_a = 1.0 / pd.to_numeric(df["B365A"], errors="coerce")
        total = imp_h + imp_d + imp_a
        odds_draw_prob = (imp_d / total).clip(0.05, 0.80)
    else:
        # Fallback: raw implied probability from draw odds alone
        imp_d = 1.0 / pd.to_numeric(df["B365D"], errors="coerce")
        odds_draw_prob = imp_d.clip(0.05, 0.80)

    # Fill missing with neutral prior
    df["odds_draw_prob"] = odds_draw_prob.fillna(NEUTRAL)
    return df


# ---------------------------------------------------------------------------
# Core prediction
# ---------------------------------------------------------------------------

def predict_match(
    home_form: float,
    away_form: float,
    home_gd: float,
    away_gd: float,
    dti: float,
    params: EngineParams,
) -> Tuple[str, float]:
    """
    Predict a single match result.
    Returns (prediction, confidence).
    """
    # DTI dampening — high uncertainty shrinks form/GD signal
    dti_damp = 1.0 - (dti * params.dti_edge_scale)
    dti_ha_damp = 1.0 - (dti * params.dti_ha_scale)

    # Raw score differential (home minus away)
    form_diff = (home_form - away_form) * params.w_form * dti_damp
    gd_diff = (home_gd - away_gd) * params.w_gd * dti_damp
    ha_bonus = params.home_adv * dti_ha_damp

    score = form_diff + gd_diff + ha_bonus

    # Determine outcome
    if abs(score) <= params.draw_margin:
        prediction = "D"
        # Coin-flip for high-DTI draws — assign to most likely winner
        if dti >= params.coin_dti_thresh:
            if score > 0:
                prediction = "H"
            elif score < 0:
                prediction = "A"
            # If exactly 0 after HA, stay as Draw
    elif score > 0:
        prediction = "H"
    else:
        prediction = "A"

    # Confidence: distance from margin, scaled 0-1
    confidence = min(abs(score) / (params.draw_margin * 4 + 0.001), 1.0)

    return prediction, round(confidence, 4)


# ---------------------------------------------------------------------------
# Batch prediction
# ---------------------------------------------------------------------------

def predict_dataframe(df: pd.DataFrame, params: EngineParams) -> pd.DataFrame:
    """
    Run predictions over a prepared DataFrame (must have home_form, away_form,
    home_gd, away_gd, dti columns already computed).

    Vectorised — runs on entire DataFrame at once for speed.
    Adds columns: prediction, confidence, chaos_tier.
    """
    df = df.copy()

    dti_damp    = 1.0 - (df["dti"] * params.dti_edge_scale)
    dti_ha_damp = 1.0 - (df["dti"] * params.dti_ha_scale)

    form_diff = (df["home_form"] - df["away_form"]) * params.w_form * dti_damp
    gd_diff   = (df["home_gd"]   - df["away_gd"])   * params.w_gd   * dti_damp
    ha_bonus  = params.home_adv * dti_ha_damp

    score = form_diff + gd_diff + ha_bonus

    # Base prediction from score
    pred = pd.Series("D", index=df.index)
    pred[score >  params.draw_margin] = "H"
    pred[score < -params.draw_margin] = "A"

    # draw_pull: if teams are evenly matched, pull score toward zero
    # form_gap is on 0-1 scale. gd_gap is in raw goals (median ~1.0) so we
    # normalise it to 0-1 using a soft cap of 3 goals as "maximum difference".
    # This means both gaps are on the same scale before comparing to draw_pull.
    GD_NORMALISE = 3.0
    form_gap = (df["home_form"] - df["away_form"]).abs()
    gd_gap   = ((df["home_gd"]  - df["away_gd"]).abs() / GD_NORMALISE).clip(0, 1)
    parity_mask = (form_gap < params.draw_pull) & (gd_gap < params.draw_pull)
    score = score.copy()
    score[parity_mask] *= (1.0 - params.draw_pull)

    # Re-evaluate base prediction after draw_pull adjustment
    pred = pd.Series("D", index=df.index)
    pred[score >  params.draw_margin] = "H"
    pred[score < -params.draw_margin] = "A"

    # dti_draw_lock: high DTI + parity = protect the draw from coin-flip
    draw_lock_mask = (pred == "D") & (df["dti"] >= params.dti_draw_lock) & parity_mask

    # Coin-flip: high-DTI draws -> flip to most likely side (unless draw-locked)
    coin_mask = (pred == "D") & (df["dti"] >= params.coin_dti_thresh) & ~draw_lock_mask
    pred[coin_mask & (score > 0)] = "H"
    pred[coin_mask & (score < 0)] = "A"

    # --- Draw intelligence layer ---
    # Combine three draw signals into a single draw_score (0.0 - 1.0).
    # Each signal is already on a 0-1 scale:
    #   odds_draw_prob   — market implied probability (~0.15 to 0.50)
    #   avg_draw_rate    — average of both teams rolling draw tendency
    #   h2h_draw_rate    — draw rate in past H2H meetings
    # draw_score is a weighted sum of the three signals.
    # When draw_score exceeds draw_score_thresh, override the prediction to D.
    # Params start at 0.0 so this layer is inert until DPOL activates it.
    _draw_prior = get_tier_draw_prior(df)  # tier-specific neutral prior for fillna
    if (params.w_draw_odds + params.w_draw_tendency + params.w_h2h_draw) > 0:
        odds_signal    = df["odds_draw_prob"].fillna(_draw_prior) if "odds_draw_prob" in df.columns else pd.Series(_draw_prior, index=df.index)
        tendency_signal = ((df["home_draw_rate"].fillna(_draw_prior) + df["away_draw_rate"].fillna(_draw_prior)) / 2) if "home_draw_rate" in df.columns else pd.Series(_draw_prior, index=df.index)
        h2h_signal     = df["h2h_draw_rate"].fillna(_draw_prior) if "h2h_draw_rate" in df.columns else pd.Series(_draw_prior, index=df.index)

        total_w = params.w_draw_odds + params.w_draw_tendency + params.w_h2h_draw
        draw_score = (
            params.w_draw_odds      * odds_signal +
            params.w_draw_tendency  * tendency_signal +
            params.w_h2h_draw       * h2h_signal
        ) / total_w

        # Override to draw when draw_score is high enough
        draw_intel_mask = draw_score >= params.draw_score_thresh
        pred[draw_intel_mask] = "D"
        df["draw_score"] = draw_score.round(4)
    else:
        df["draw_score"] = 0.0

    # --- Composite draw signal layer (session 26) ---
    # Two additions from draw evolution Pass 3:
    #
    # 1. expected_goals_total as a standalone draw signal (1.088x lift).
    #    Low xG total = tight match = draw-positive.
    #    Inverted and normalised: xG total of 2.0 or below → signal toward 1.0.
    #    Soft cap at 4.0 goals total (above that, draw is very unlikely).
    #    Added to draw_score weighted by w_xg_draw.
    #
    # 2. Composite gate: when odds_draw_prob > 0.288 (market pricing draw)
    #    AND at least one supporting signal is in draw-positive band,
    #    add composite_draw_boost to draw_score.
    #    Supporting signals (from Pass 3 combinations):
    #      - form_parity > 0.70  (teams closely matched in form)
    #      - home_draw_rate > 0.28 (home team draws frequently)
    #      - h2h_draw_rate > 0.28 (this fixture draws frequently)
    #    Both additions are strictly additive — they cannot override draw_score
    #    alone, only push it closer to draw_score_thresh.
    #    Both start at 0.0 so this block is fully inert until DPOL activates.

    if params.w_xg_draw > 0 or params.composite_draw_boost > 0:
        # Ensure draw_score column exists (may be 0.0 if draw intel layer was inert)
        if "draw_score" not in df.columns:
            df["draw_score"] = pd.Series(0.0, index=df.index)

        # 1. xG total signal
        if params.w_xg_draw > 0 and "pred_home_goals" in df.columns and "pred_away_goals" in df.columns:
            xg_total = (df["pred_home_goals"].fillna(1.5) + df["pred_away_goals"].fillna(1.5))
            # Invert: low xG → high signal. Normalise over [0, 4.0] range, clip.
            XG_CAP = 4.0
            xg_draw_signal = (1.0 - (xg_total / XG_CAP)).clip(0.0, 1.0)
            df["draw_score"] = (df["draw_score"] + params.w_xg_draw * xg_draw_signal).clip(0.0, 1.0)

        # 2. Composite gate
        if params.composite_draw_boost > 0 and "odds_draw_prob" in df.columns:
            anchor = df["odds_draw_prob"].fillna(_draw_prior) > 0.288

            form_parity_signal = pd.Series(False, index=df.index)
            if "home_form" in df.columns and "away_form" in df.columns:
                form_parity = 1.0 - (df["home_form"] - df["away_form"]).abs().clip(0, 1)
                form_parity_signal = form_parity > 0.70

            home_draw_signal = pd.Series(False, index=df.index)
            if "home_draw_rate" in df.columns:
                home_draw_signal = df["home_draw_rate"].fillna(_draw_prior) > 0.28

            h2h_draw_signal = pd.Series(False, index=df.index)
            if "h2h_draw_rate" in df.columns:
                h2h_draw_signal = df["h2h_draw_rate"].fillna(_draw_prior) > 0.28

            supporting = form_parity_signal | home_draw_signal | h2h_draw_signal
            composite_gate = anchor & supporting

            df["draw_score"] = (
                df["draw_score"] + composite_gate.astype(float) * params.composite_draw_boost
            ).clip(0.0, 1.0)

        # Re-evaluate draw overrides with updated draw_score
        draw_intel_mask_c = df["draw_score"] >= params.draw_score_thresh
        pred[draw_intel_mask_c] = "D"

    # --- Score prediction signals ---
    # w_score_margin: predicted goal margin reinforces H/A confidence.
    #   A large predicted margin (e.g. 2.0) boosts score toward that side,
    #   tightening the result. Signed: positive = home advantage predicted.
    #   Weight starts at 0 — DPOL activates if it helps.
    # w_btts: high BTTS probability adds to draw_score (both teams likely to
    #   score = game unlikely to be one-sided = draw more plausible).
    #   Only feeds draw_score, not the core score differential.
    if "pred_margin" in df.columns and params.w_score_margin > 0:
        score = score + df["pred_margin"].fillna(0.0) * params.w_score_margin

        # Re-evaluate base prediction after score margin adjustment
        pred = pd.Series("D", index=df.index)
        pred[score >  params.draw_margin] = "H"
        pred[score < -params.draw_margin] = "A"

        # Re-apply coin-flip on updated preds
        coin_mask2 = (pred == "D") & (df["dti"] >= params.coin_dti_thresh)
        pred[coin_mask2 & (score > 0)] = "H"
        pred[coin_mask2 & (score < 0)] = "A"

    if "btts_prob" in df.columns and params.w_btts > 0 and "draw_score" in df.columns:
        # BTTS signal contributes to draw_score — re-evaluate draw overrides
        btts_signal = df["btts_prob"].fillna(0.5)
        df["draw_score"] = (df["draw_score"] + params.w_btts * btts_signal).clip(0.0, 1.0)
        draw_intel_mask2 = df["draw_score"] >= params.draw_score_thresh
        pred[draw_intel_mask2] = "D"

    # --- External Signal Layer — Phase 1 ---
    # Each signal adjusts the core score differential.
    # Signals start at 0.0 (inert) — DPOL activates if they improve accuracy.
    #
    # ref_signal    : referee home bias. 0.5 = neutral. >0.5 = home-biased ref.
    #                 Boosts home score proportionally above neutral baseline.
    # travel_load   : away team travel distance (0=local, 1=marathon trip).
    #                 Subtracts from score (away disadvantage).
    # timing_signal : fixture disruption (midweek/bank holiday/festive).
    #                 Reduces signal strength (both teams affected — dampens score).
    # motivation_gap: home_motivation - away_motivation (-1 to 1).
    #                 Adds directly to score — higher motivated home team = boost.
    if params.w_ref_signal > 0 and "ref_signal" in df.columns:
        sig_ref = df["ref_signal"].fillna(0.5)
        score = score + params.w_ref_signal * (sig_ref - 0.5) * 2  # 0.5=neutral → no effect

    if params.w_travel_load > 0 and "travel_load" in df.columns:
        sig_travel = df["travel_load"].fillna(0.0)
        score = score - params.w_travel_load * sig_travel  # away disadvantage

    if params.w_timing_signal > 0 and "timing_signal" in df.columns:
        sig_timing = df["timing_signal"].fillna(0.0)
        score = score * (1.0 - params.w_timing_signal * sig_timing)  # dampens overall signal

    if params.w_motivation_gap > 0 and "motivation_gap" in df.columns:
        sig_motivate = df["motivation_gap"].fillna(0.0)
        score = score + params.w_motivation_gap * sig_motivate

    # Re-evaluate predictions after external signal adjustments (if any were active)
    if any([params.w_ref_signal, params.w_travel_load,
            params.w_timing_signal, params.w_motivation_gap]) > 0:
        pred = pd.Series("D", index=df.index)
        pred[score >  params.draw_margin] = "H"
        pred[score < -params.draw_margin] = "A"
        coin_mask3 = (pred == "D") & (df["dti"] >= params.coin_dti_thresh)
        pred[coin_mask3 & (score > 0)] = "H"
        pred[coin_mask3 & (score < 0)] = "A"

    confidence = (score.abs() / (params.draw_margin * 4 + 0.001)).clip(0, 1).round(4)

    # --- Fixture Specificity Layer (Session 38) ---
    # All signals start at 0.0 — inert until DPOL activates them.
    # Each replaces or supplements an averaging assumption in the core engine.

    # Venue-split form: replace blended form with venue-specific form
    # when w_venue_form > 0. Blends: (1-w)*blended + w*venue_split
    if getattr(params, "w_venue_form", 0.0) > 0:
        wvf = params.w_venue_form
        if "home_form_home" in df.columns and "away_form_away" in df.columns:
            venue_form_diff = (
                (df["home_form_home"] * wvf + df["home_form"] * (1 - wvf)) -
                (df["away_form_away"] * wvf + df["away_form"] * (1 - wvf))
            ) * params.w_form * dti_damp
            # Delta vs original form_diff
            orig_form_diff = (df["home_form"] - df["away_form"]) * params.w_form * dti_damp
            score = score + (venue_form_diff - orig_form_diff)

    # Team-specific home advantage: blend with flat home_adv
    if getattr(params, "w_team_home_adv", 0.0) > 0:
        wtha = params.w_team_home_adv
        if "home_adv_team" in df.columns:
            team_ha = df["home_adv_team"].fillna(0.0)
            # Replace flat home_adv contribution partially with team-specific
            flat_ha  = params.home_adv * dti_ha_damp
            team_ha_contrib = (
                params.home_adv * (1 - wtha) + team_ha * wtha
            ) * dti_ha_damp
            score = score + (team_ha_contrib - flat_ha)

    # Away team natural away strength: subtracts from home advantage.
    # away_adv_team is (away_win_rate - home_win_rate) * 0.5 for the away team.
    # Most teams: negative (worse away than home) → small reduction to score.
    # Strong away sides (Man City): less negative or positive → larger reduction.
    # Evolved independently from w_team_home_adv — DPOL finds their balance.
    if getattr(params, "w_away_team_adv", 0.0) > 0:
        wata = params.w_away_team_adv
        if "away_adv_team" in df.columns:
            away_adv = df["away_adv_team"].fillna(0.0)
            # away_adv is signed: positive = strong away side, negative = weak away side.
            # Subtract from score: a strong away side erodes the home advantage.
            score = score - wata * away_adv * dti_ha_damp

    # Opponent-adjusted form: blend with raw form
    if getattr(params, "w_opp_strength", 0.0) > 0:
        wos = params.w_opp_strength
        if "home_form_adj" in df.columns and "away_form_adj" in df.columns:
            adj_form_diff = (
                (df["home_form_adj"] * wos + df["home_form"] * (1 - wos)) -
                (df["away_form_adj"] * wos + df["away_form"] * (1 - wos))
            ) * params.w_form * dti_damp
            orig_form_diff = (df["home_form"] - df["away_form"]) * params.w_form * dti_damp
            score = score + (adj_form_diff - orig_form_diff)

    # Season stage: late-season dampens signal (both teams settled / motivations unclear)
    if getattr(params, "w_season_stage", 0.0) > 0:
        wss = params.w_season_stage
        if "season_stage" in df.columns:
            # Early season (stage~0): slight boost to home signal (predictable)
            # Late season (stage~1): slight dampening (unpredictable motivation)
            stage = df["season_stage"].fillna(0.5)
            stage_factor = 1.0 - (wss * (stage - 0.5))  # dampens in late season
            score = score * stage_factor

    # Rest days differential: more rested team has slight advantage
    if getattr(params, "w_rest_diff", 0.0) > 0:
        wrd = params.w_rest_diff
        if "rest_days_diff" in df.columns:
            # Positive diff = home more rested = boost to home score
            # Normalise: 7 days diff is large, cap at 14 days
            rest_signal = (df["rest_days_diff"].fillna(0.0) / 14.0).clip(-1.0, 1.0)
            score = score + wrd * rest_signal

    # Re-evaluate predictions after fixture specificity adjustments
    if any([
        getattr(params, "w_venue_form", 0.0),
        getattr(params, "w_team_home_adv", 0.0),
        getattr(params, "w_away_team_adv", 0.0),
        getattr(params, "w_opp_strength", 0.0),
        getattr(params, "w_season_stage", 0.0),
        getattr(params, "w_rest_diff", 0.0),
    ]):
        pred = pd.Series("D", index=df.index)
        pred[score >  params.draw_margin] = "H"
        pred[score < -params.draw_margin] = "A"
        coin_mask_fs = (pred == "D") & (df["dti"] >= params.coin_dti_thresh)
        pred[coin_mask_fs & (score > 0)] = "H"
        pred[coin_mask_fs & (score < 0)] = "A"
        # Recompute confidence with updated score
        confidence = (score.abs() / (params.draw_margin * 4 + 0.001)).clip(0, 1).round(4)

    # --- Layer Agreement Layer (Session 41) ---
    # w_scoreline_agreement: adjusts confidence based on whether the outcome
    # layer (pred) agrees with the scoreline map layer (top_scoreline_match outcome).
    # agree → positive confidence adjustment; disagree → negative.
    # w_scoreline_confidence: adjusts confidence based on how clearly the fixture
    # matched a scoreline population. Uses top_scoreline_match_density if present.
    # Both start at 0.0 — inert until DPOL activates them.
    w_sa = getattr(params, "w_scoreline_agreement", 0.0)
    w_sc = getattr(params, "w_scoreline_confidence", 0.0)

    if (w_sa > 0 or w_sc > 0):
        confidence = confidence.copy()

        if w_sa > 0 and "top_scoreline_match_outcome" in df.columns:
            sl_outcome = df["top_scoreline_match_outcome"].fillna("")
            agree_mask    = (sl_outcome != "") & (sl_outcome == pred)
            disagree_mask = (sl_outcome != "") & (sl_outcome != pred)
            confidence = (confidence + w_sa * agree_mask.astype(float)).clip(0, 1)
            confidence = (confidence - w_sa * disagree_mask.astype(float)).clip(0, 1)

        if w_sc > 0 and "top_scoreline_match_density" in df.columns:
            # density score is in [0, 1] range — 0.5 is neutral midpoint.
            # above 0.5 = clear match → boost; below 0.5 = scattered → reduce.
            density = df["top_scoreline_match_density"].fillna(0.5)
            density_signal = (density - 0.5) * 2.0  # rescale to [-1, 1]
            confidence = (confidence + w_sc * density_signal).clip(0, 1)

        confidence = confidence.round(4)

    df["prediction"] = pred
    df["confidence"]  = confidence
    df["chaos_tier"]  = df["dti"].apply(assign_chaos_tier)
    return df


# ---------------------------------------------------------------------------
# Upset layer — v1
# ---------------------------------------------------------------------------
#
# Scores each match on how likely an upset is, using signals available
# before kickoff from current data sources.
#
# ARCHITECTURE — two-stage design:
#   Stage 1 (now):  flag only. upset_score computed, upset_flag set, prediction
#                   unchanged. Accumulates history so the signal can be validated.
#   Stage 2 (later, when validated): DPOL gets upset_flip_thresh. If upset_score
#                   exceeds it, prediction flips. Earns the right to flip by
#                   proving predictive power on logged Stage 1 data first.
#
# SIGNALS — v1 uses internal signals only (all already in the dataframe):
#
#   1. dti_confidence_tension  — HIGH DTI but also HIGH engine confidence.
#      The engine is certain, but the match is volatile. That tension is the
#      clearest internal upset signal. When both are high simultaneously, the
#      engine is probably over-weighting form/GD and under-weighting chaos.
#
#   2. odds_gap  — market's implied favourite probability vs engine confidence.
#      When the engine is more confident than the market, the market is pricing
#      in risk the engine can't see. Large gap = upset candidate.
#      Computed from B365H/B365A vs engine confidence + prediction direction.
#
#   3. h2h_upset_rate  — how often the historically weaker team wins this
#      fixture. Complements h2h_draw_rate already in the engine.
#      Uses h2h_home_edge (already computed) to derive upset tendency.
#
# EXTERNAL SIGNAL HOOKS — not built yet, but designed in:
#   These will plug in as additional additive terms when data is available:
#   - rest_days_gap      : one team significantly more rested than the other
#   - travel_load        : midweek away game before this fixture
#   - injury_index       : key player absence (API-Football, ~2018+)
#   - motivation_index   : season context — already safe/relegated/nothing to play for
#   - weather_factor     : heavy conditions favour underdogs (lower tiers especially)
#   Each adds to upset_score. Weights tunable by DPOL once data exists.
#
# OUTPUT COLUMNS:
#   upset_score  — float 0.0–1.0. Higher = more upset risk on current prediction.
#   upset_flag   — 1 if upset_score >= UPSET_FLAG_THRESH, else 0.
#                  Default threshold 0.60 — tunable, eventually a DPOL param.

def compute_upset_score(df: pd.DataFrame, flag_thresh: float = 0.60) -> pd.DataFrame:
    """
    Compute upset_score and upset_flag for each match.

    Must be called AFTER predict_dataframe — reads prediction and confidence columns.

    Args:
        df:           DataFrame with prediction, confidence, dti, h2h_home_edge,
                      odds_draw_prob, B365H, B365A columns.
        flag_thresh:  upset_score threshold above which upset_flag = 1.
                      Default 0.60. Will become a DPOL parameter in Stage 2.

    Returns df with added columns: upset_score, upset_flag.
    """
    df = df.copy()

    # ── Signal 1: DTI × confidence tension ──────────────────────────────────
    # Both scaled 0–1. Product peaks when both are simultaneously high.
    # A match where the engine is 80% confident AND DTI is 0.85 is the
    # textbook upset setup — engine over-certain on a volatile match.
    dti        = df["dti"].clip(0.0, 1.0)
    confidence = df["confidence"].clip(0.0, 1.0) if "confidence" in df.columns else pd.Series(0.5, index=df.index)
    sig_tension = (dti * confidence).clip(0.0, 1.0)

    # ── Signal 2: odds gap ───────────────────────────────────────────────────
    # Market's implied probability for the predicted outcome vs engine confidence.
    # If engine says 75% home win but market only implies 55%, the 20pt gap
    # is the market pricing in upset risk the engine is missing.
    # Gap is expressed as a 0–1 fraction of maximum possible disagreement (1.0).
    sig_odds_gap = pd.Series(0.0, index=df.index)

    if "B365H" in df.columns and "B365A" in df.columns and "B365D" in df.columns and "prediction" in df.columns:
        imp_h_raw = pd.to_numeric(df["B365H"], errors="coerce")
        imp_d_raw = pd.to_numeric(df["B365D"], errors="coerce")
        imp_a_raw = pd.to_numeric(df["B365A"], errors="coerce")

        # Normalised fair market probabilities (removes bookmaker overround)
        total = (1.0 / imp_h_raw) + (1.0 / imp_d_raw) + (1.0 / imp_a_raw)
        mkt_h = (1.0 / imp_h_raw) / total
        mkt_a = (1.0 / imp_a_raw) / total

        # Market's implied probability for the engine's predicted outcome
        pred = df["prediction"]
        mkt_for_pred = pd.Series(0.33, index=df.index)  # neutral fallback
        mkt_for_pred[pred == "H"] = mkt_h[pred == "H"]
        mkt_for_pred[pred == "A"] = mkt_a[pred == "A"]
        # Draw predictions don't generate upset risk — skip

        # Gap: engine confidence minus market probability for same outcome
        # Only meaningful for H/A predictions (draws excluded — no clear favourite)
        ha_mask = pred.isin(["H", "A"])
        gap = (confidence - mkt_for_pred).clip(0.0, 1.0)
        sig_odds_gap[ha_mask] = gap[ha_mask].fillna(0.0)

    # ── Signal 3: H2H upset tendency ────────────────────────────────────────
    # h2h_home_edge is already computed: positive = home team historically
    # dominates, negative = away team historically dominates.
    # An upset signal fires when the engine predicts H but history shows
    # the away team tends to win this fixture (and vice versa).
    sig_h2h_upset = pd.Series(0.0, index=df.index)

    if "h2h_home_edge" in df.columns and "prediction" in df.columns:
        edge = df["h2h_home_edge"].fillna(0.0)
        pred = df["prediction"]

        # Engine says H but H2H history favours away → upset risk
        h_pred_away_hist = (pred == "H") & (edge < -0.15)
        # Engine says A but H2H history favours home → upset risk
        a_pred_home_hist = (pred == "A") & (edge > 0.15)

        # Scale the signal: larger historical edge contradiction = stronger signal
        # Clip edge to [-1, 1], take absolute value as magnitude
        edge_magnitude = edge.abs().clip(0.0, 1.0)
        sig_h2h_upset[h_pred_away_hist] = edge_magnitude[h_pred_away_hist]
        sig_h2h_upset[a_pred_home_hist] = edge_magnitude[a_pred_home_hist]

    # ── External signal hooks — Phase 1 (now active when columns present) ───
    # These plug in as additional additive terms to upset_score.
    # When the columns exist (after compute_phase1_signals runs), they contribute.
    sig_rest     = ((df["rest_days_gap"].clip(0, 7) / 7) if "rest_days_gap" in df.columns
                    else pd.Series(0.0, index=df.index))
    sig_travel   = (df["travel_load"].clip(0, 1)     if "travel_load"     in df.columns
                    else pd.Series(0.0, index=df.index))
    sig_motivate = (df["motivation_gap"].abs().clip(0, 1) if "motivation_gap" in df.columns
                    else pd.Series(0.0, index=df.index))
    # weight these at a conservative fixed amount until DPOL can tune them
    # (each adds max 0.05 to upset_score until formally parameterised)
    EXTERNAL_W = 0.05
    # sig_weather  = df["weather_factor"].clip(0,1)  if "weather_factor"  in df.columns else 0

    # ── Combine signals ──────────────────────────────────────────────────────
    # Weighted sum — v1 weights reflect signal reliability at this stage.
    # tension is the strongest internal signal, odds_gap second, h2h third.
    # Weights will become DPOL parameters in Stage 2.
    W_TENSION  = 0.45
    W_ODDS_GAP = 0.35
    W_H2H      = 0.20

    upset_score = (
        W_TENSION  * sig_tension  +
        W_ODDS_GAP * sig_odds_gap +
        W_H2H      * sig_h2h_upset +
        EXTERNAL_W * sig_travel   +   # away travel burden → upset risk
        EXTERNAL_W * sig_motivate     # motivation gap → more motivated underdog
    ).clip(0.0, 1.0).round(4)

    # Only flag H/A predictions — draw calls don't have a clear favourite to upset
    pred = df["prediction"] if "prediction" in df.columns else pd.Series("D", index=df.index)
    upset_flag = ((upset_score >= flag_thresh) & pred.isin(["H", "A"])).astype(int)

    df["upset_score"] = upset_score
    df["upset_flag"]  = upset_flag

    return df



# ---------------------------------------------------------------------------
# Fixture Specificity Layer (Session 38)
# Five new feature functions — all additive, nothing breaks existing pipeline.
# Each adds new columns alongside existing ones.
# New params in EngineParams (all 0.0 default) gate each signal in predict_dataframe.
# ---------------------------------------------------------------------------

def compute_venue_split_form(df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    """
    Venue-specific form: last N home games for home team, last N away games
    for away team. Current blended form treats all venues as equivalent.

    Adds: home_form_home, away_form_away
    Falls back to 0.5 neutral until sufficient venue history exists.
    """
    df = df.copy().reset_index(drop=True)

    home_results: Dict[str, List[float]] = {}
    away_results: Dict[str, List[float]] = {}
    home_form_home = [0.5] * len(df)
    away_form_away = [0.5] * len(df)

    hts  = df["HomeTeam"].tolist()
    ats  = df["AwayTeam"].tolist()
    ftrs = df["FTR"].tolist()

    for i in range(len(df)):
        ht, at, ftr = hts[i], ats[i], ftrs[i]
        home_form_home[i] = _rolling_form(home_results.get(ht, []), window)
        away_form_away[i] = _rolling_form(away_results.get(at, []), window)
        _update_history(home_results, ht,
                        1.0 if ftr == "H" else (0.4 if ftr == "D" else 0.0))
        _update_history(away_results, at,
                        1.0 if ftr == "A" else (0.4 if ftr == "D" else 0.0))

    df["home_form_home"] = home_form_home
    df["away_form_away"] = away_form_away
    return df


def compute_team_home_advantage(df: pd.DataFrame) -> pd.DataFrame:
    """
    Per-team home advantage from actual historical record.
    Replaces flat home_adv=0.25 when w_team_home_adv is active.

    Adds: home_adv_team — differential between team's home win rate
    and away win rate, normalised to [-0.5, 0.5].
    Falls back to 0.0 (neutral) until MIN_GAMES threshold met.
    """
    df = df.copy().reset_index(drop=True)
    MIN_GAMES = 5

    team_home_wins:  Dict[str, int] = {}
    team_home_games: Dict[str, int] = {}
    team_away_wins:  Dict[str, int] = {}
    team_away_games: Dict[str, int] = {}
    home_adv_vals = [0.0] * len(df)

    hts  = df["HomeTeam"].tolist()
    ats  = df["AwayTeam"].tolist()
    ftrs = df["FTR"].tolist()

    for i in range(len(df)):
        ht, at, ftr = hts[i], ats[i], ftrs[i]

        ht_hg = team_home_games.get(ht, 0)
        ht_ag = team_away_games.get(ht, 0)

        if ht_hg >= MIN_GAMES and ht_ag >= MIN_GAMES:
            home_rate = team_home_wins.get(ht, 0) / ht_hg
            away_rate = team_away_wins.get(ht, 0) / ht_ag
            home_adv_vals[i] = round((home_rate - away_rate) * 0.5, 4)

        team_home_games[ht] = ht_hg + 1
        team_away_games[at] = team_away_games.get(at, 0) + 1
        if ftr == "H":
            team_home_wins[ht] = team_home_wins.get(ht, 0) + 1
        elif ftr == "A":
            team_away_wins[at] = team_away_wins.get(at, 0) + 1

    df["home_adv_team"] = home_adv_vals
    return df


def compute_away_team_advantage(df: pd.DataFrame) -> pd.DataFrame:
    """
    Per-team away strength from actual historical record.
    Mirror of compute_team_home_advantage — but from the away team's perspective.

    Man City away at Burnley is not the same as Man City away at Chelsea.
    This captures the away team's natural away record independent of who
    they are facing. Combined with home_adv_team, DPOL finds the balance:
    how much does the home team's home strength matter vs the away team's
    away strength?

    Adds: away_adv_team — the away team's historical away win rate minus
    their home win rate, normalised to [-0.5, 0.5].
    Positive = strong away side (wins more away than home — rare but real).
    Negative = poor away side (wins more at home than away — most teams).
    Falls back to 0.0 (neutral) until MIN_GAMES threshold met.

    Note: sign convention matches home_adv_team — both express the team's
    venue advantage as a positive number when the venue is beneficial.
    A strong away side (e.g. Man City away) has a less negative or positive
    away_adv_team, which reduces the effective home advantage in the score.
    """
    df = df.copy().reset_index(drop=True)
    MIN_GAMES = 5

    team_home_wins:  Dict[str, int] = {}
    team_home_games: Dict[str, int] = {}
    team_away_wins:  Dict[str, int] = {}
    team_away_games: Dict[str, int] = {}
    away_adv_vals = [0.0] * len(df)

    hts  = df["HomeTeam"].tolist()
    ats  = df["AwayTeam"].tolist()
    ftrs = df["FTR"].tolist()

    for i in range(len(df)):
        ht, at, ftr = hts[i], ats[i], ftrs[i]

        at_ag = team_away_games.get(at, 0)
        at_hg = team_home_games.get(at, 0)

        if at_ag >= MIN_GAMES and at_hg >= MIN_GAMES:
            away_rate = team_away_wins.get(at, 0) / at_ag
            home_rate = team_home_wins.get(at, 0) / at_hg
            # away_rate - home_rate: positive = better away than home (strong away side)
            # negative = worse away than home (most teams)
            away_adv_vals[i] = round((away_rate - home_rate) * 0.5, 4)

        team_home_games[ht] = team_home_games.get(ht, 0) + 1
        team_away_games[at] = at_ag + 1
        if ftr == "H":
            team_home_wins[ht] = team_home_wins.get(ht, 0) + 1
        elif ftr == "A":
            team_away_wins[at] = team_away_wins.get(at, 0) + 1

    df["away_adv_team"] = away_adv_vals
    return df


def compute_opponent_adjusted_form(df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    """
    Form weighted by opponent strength. A win against a top-4 side counts
    more than a win against a relegation team.

    Opponent strength proxy: opponent's rolling GD at time of match,
    normalised across the dataset to [0,1].

    Requires home_gd, away_gd already computed.
    Adds: home_form_adj, away_form_adj
    """
    if "home_gd" not in df.columns or "away_gd" not in df.columns:
        df = df.copy()
        df["home_form_adj"] = df.get("home_form", pd.Series(0.5, index=df.index))
        df["away_form_adj"] = df.get("away_form", pd.Series(0.5, index=df.index))
        return df

    df = df.copy().reset_index(drop=True)

    all_gd = pd.concat([df["home_gd"], df["away_gd"]])
    gd_min = float(all_gd.min())
    gd_range = float(all_gd.max() - gd_min)
    if gd_range == 0:
        gd_range = 1.0

    def gd_to_strength(gd: float) -> float:
        return float(np.clip((gd - gd_min) / gd_range, 0.0, 1.0))

    team_adj_history: Dict[str, List[Tuple[float, float]]] = {}
    home_form_adj = [0.5] * len(df)
    away_form_adj = [0.5] * len(df)

    hts  = df["HomeTeam"].tolist()
    ats  = df["AwayTeam"].tolist()
    ftrs = df["FTR"].tolist()
    hgds = df["home_gd"].tolist()
    agds = df["away_gd"].tolist()

    for i in range(len(df)):
        ht, at, ftr = hts[i], ats[i], ftrs[i]
        h_gd, a_gd = hgds[i], agds[i]

        for team, hist, form_arr, result_val, opp_gd in [
            (ht, team_adj_history.get(ht, []), home_form_adj,
             1.0 if ftr == "H" else (0.4 if ftr == "D" else 0.0), a_gd),
            (at, team_adj_history.get(at, []), away_form_adj,
             1.0 if ftr == "A" else (0.4 if ftr == "D" else 0.0), h_gd),
        ]:
            if len(hist) >= 3:
                recent = hist[-window:]
                weights = [w for _, w in recent]
                results = [r for r, _ in recent]
                total_w = sum(weights)
                if total_w > 0:
                    val = sum(r * w for r, w in zip(results, weights)) / total_w
                else:
                    val = _rolling_form(results, window)
            else:
                val = 0.5

            if team == ht:
                home_form_adj[i] = round(val, 4)
            else:
                away_form_adj[i] = round(val, 4)

            if team not in team_adj_history:
                team_adj_history[team] = []
            team_adj_history[team].append((result_val, gd_to_strength(opp_gd)))

    df["home_form_adj"] = home_form_adj
    df["away_form_adj"] = away_form_adj
    return df


def compute_season_stage(df: pd.DataFrame) -> pd.DataFrame:
    """
    Season stage: how far through the season each match is.
    0.0 = first gameweek, 1.0 = final gameweek.

    Requires parsed_date and season columns.
    Adds: season_stage, matches_played_home, matches_played_away
    """
    df = df.copy().reset_index(drop=True)

    season_stage        = [0.5] * len(df)
    matches_played_home = [0]   * len(df)
    matches_played_away = [0]   * len(df)

    if "parsed_date" not in df.columns or "season" not in df.columns:
        df["season_stage"]        = season_stage
        df["matches_played_home"] = matches_played_home
        df["matches_played_away"] = matches_played_away
        return df

    for season in df["season"].unique():
        season_mask = df["season"] == season
        season_df   = df[season_mask]
        dates       = sorted(season_df["parsed_date"].unique())
        max_round   = len(dates)
        date_to_round = {d: i + 1 for i, d in enumerate(dates)}
        team_match_count: Dict[str, int] = {}

        for idx in season_df.index:
            rd = date_to_round.get(df.at[idx, "parsed_date"], 1)
            season_stage[idx] = round(rd / max_round, 4) if max_round > 0 else 0.5
            ht = df.at[idx, "HomeTeam"]
            at = df.at[idx, "AwayTeam"]
            matches_played_home[idx] = team_match_count.get(ht, 0)
            matches_played_away[idx] = team_match_count.get(at, 0)
            team_match_count[ht] = team_match_count.get(ht, 0) + 1
            team_match_count[at] = team_match_count.get(at, 0) + 1

    df["season_stage"]        = season_stage
    df["matches_played_home"] = matches_played_home
    df["matches_played_away"] = matches_played_away
    return df


def compute_rest_days(df: pd.DataFrame) -> pd.DataFrame:
    """
    Days since each team's last match. Derivable purely from parsed_date.
    3 days rest vs 7 days rest is a measurable fixture congestion signal.

    Adds: home_rest_days, away_rest_days, rest_days_diff
    Falls back to 7.0 (typical between-match gap) when no prior match.
    """
    df = df.copy().reset_index(drop=True)
    NEUTRAL = 7.0

    if "parsed_date" not in df.columns:
        df["home_rest_days"] = NEUTRAL
        df["away_rest_days"] = NEUTRAL
        df["rest_days_diff"] = 0.0
        return df

    team_last: Dict[str, any] = {}
    home_rest = [NEUTRAL] * len(df)
    away_rest = [NEUTRAL] * len(df)

    hts   = df["HomeTeam"].tolist()
    ats   = df["AwayTeam"].tolist()
    dates = df["parsed_date"].tolist()

    for i in range(len(df)):
        ht, at, d = hts[i], ats[i], dates[i]
        home_rest[i] = float(max(0, (d - team_last[ht]).days)) if ht in team_last else NEUTRAL
        away_rest[i] = float(max(0, (d - team_last[at]).days)) if at in team_last else NEUTRAL
        team_last[ht] = d
        team_last[at] = d

    hr = np.array(home_rest)
    ar = np.array(away_rest)
    df["home_rest_days"] = hr.round(1)
    df["away_rest_days"] = ar.round(1)
    df["rest_days_diff"] = (hr - ar).round(1)
    return df


def prepare_dataframe(df: pd.DataFrame, params: EngineParams) -> pd.DataFrame:
    """Full pipeline: compute form, GD, DTI, draw intelligence, external signals,
    fixture specificity features, then predict."""
    df = compute_form(df, window=params.form_window)
    df = compute_goal_diff(df, window=params.form_window)
    df = compute_dti(df)
    df = compute_team_draw_tendency(df, window=params.form_window * 2)
    df = compute_h2h(df, window=6)
    df = compute_odds_draw_prob(df)
    df = compute_score_prediction(df, window=params.form_window)
    # Phase 1 external signals — referee, travel, timing, motivation
    try:
        from edgelab_signals import compute_phase1_signals
        df = compute_phase1_signals(df)
    except ImportError:
        pass   # signals module optional — engine works without it
    # Phase 2 external signals — weather (pre-computed, joined before engine runs)
    if "weather_load" not in df.columns:
        df["weather_load"] = 0.0
    # Fixture Specificity Layer (Session 38) — all additive, inert until DPOL activates
    df = compute_venue_split_form(df, window=params.form_window)
    df = compute_team_home_advantage(df)
    df = compute_away_team_advantage(df)
    df = compute_opponent_adjusted_form(df, window=params.form_window)
    df = compute_season_stage(df)
    df = compute_rest_days(df)
    df = predict_dataframe(df, params)
    df = compute_upset_score(df)   # runs after predict — reads prediction + confidence
    return df


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate(df: pd.DataFrame) -> Dict:
    """
    Compare predictions to actual FTR.
    Returns dict of accuracy stats.
    """
    total = len(df)
    if total == 0:
        return {}

    correct = (df["prediction"] == df["FTR"]).sum()
    accuracy = correct / total

    # Breakdown by actual result
    breakdown = {}
    for result in ["H", "D", "A"]:
        subset = df[df["FTR"] == result]
        if len(subset) > 0:
            acc = (subset["prediction"] == subset["FTR"]).sum() / len(subset)
            breakdown[result] = round(acc, 4)

    # Predictions made per class
    pred_counts = df["prediction"].value_counts().to_dict()

    return {
        "total": total,
        "correct": int(correct),
        "accuracy": round(accuracy, 4),
        "breakdown": breakdown,
        "predicted_counts": pred_counts,
        "actual_counts": df["FTR"].value_counts().to_dict(),
    }


# ---------------------------------------------------------------------------
# DPOL bridge — this is the key wiring point
# ---------------------------------------------------------------------------

def make_pred_fn(base_df: pd.DataFrame) -> Callable:
    """
    Returns a pred_fn compatible with DPOLManager.evolve_for_league().

    The DPOL passes a window DataFrame and a LeagueParams object.
    This bridge:
      1. Converts LeagueParams → EngineParams
      2. Re-runs feature computation on the window
      3. Returns a Series of predictions

    Usage:
        pred_fn = make_pred_fn(df_league)
        dpol.evolve_for_league(df_league, pred_fn=pred_fn)
    """
    def pred_fn(df_window: pd.DataFrame, league_params) -> pd.Series:
        # Convert DPOL LeagueParams to EngineParams
        params = EngineParams(
            w_form=league_params.w_form,
            w_gd=league_params.w_gd,
            home_adv=league_params.home_adv,
            dti_edge_scale=league_params.dti_edge_scale,
            dti_ha_scale=league_params.dti_ha_scale,
            draw_margin=league_params.draw_margin,
            coin_dti_thresh=league_params.coin_dti_thresh,
            form_window=5,
            w_draw_odds=getattr(league_params, "w_draw_odds", 0.0),
            w_draw_tendency=getattr(league_params, "w_draw_tendency", 0.0),
            w_h2h_draw=getattr(league_params, "w_h2h_draw", 0.0),
            draw_score_thresh=getattr(league_params, "draw_score_thresh", 0.55),
            w_xg_draw=getattr(league_params, "w_xg_draw", 0.0),
            composite_draw_boost=getattr(league_params, "composite_draw_boost", 0.0),
            w_scoreline_agreement=getattr(league_params, "w_scoreline_agreement", 0.0),
            w_scoreline_confidence=getattr(league_params, "w_scoreline_confidence", 0.0),
            w_away_team_adv=getattr(league_params, "w_away_team_adv", 0.0),
        )
        # Find the start index of the window in the full base_df,
        # then prepend enough prior rows to warm up the rolling calculations.
        WARMUP = 20  # rows of prior history to prepend

        if len(df_window) == 0:
            return pd.Series([], dtype=str)

        # Match window back to base_df by index if possible
        try:
            window_start_idx = df_window.index[0]
            warmup_start = max(0, window_start_idx - WARMUP)
            df_context = base_df.iloc[warmup_start:].copy()
        except Exception:
            df_context = df_window.copy()

        # Run full feature pipeline on the context block
        df_context = compute_form(df_context, window=params.form_window)
        df_context = compute_goal_diff(df_context, window=params.form_window)
        df_context = compute_dti(df_context)
        df_context = predict_dataframe(df_context, params)

        # Extract only the window rows from the result
        preds = df_context.loc[df_context.index.isin(df_window.index), "prediction"]
        return preds

    return pred_fn


# ---------------------------------------------------------------------------
# assign_match_round — needed by DPOL
# ---------------------------------------------------------------------------

def assign_match_round(df: pd.DataFrame, matches_per_round: int = 10) -> pd.DataFrame:
    """
    Assign a sequential round number to each match within a season.
    Assumes matches_per_round teams play per round (10 for 20-team league).
    Groups by date within season, assigns round index.
    """
    df = df.copy()
    df["match_round"] = 0

    for season in df["season"].unique():
        mask = df["season"] == season
        season_df = df[mask].copy()
        dates = sorted(season_df["parsed_date"].unique())
        date_to_round = {d: i + 1 for i, d in enumerate(dates)}
        df.loc[mask, "match_round"] = season_df["parsed_date"].map(date_to_round)

    return df


# ---------------------------------------------------------------------------
# Run baseline (standalone)
# ---------------------------------------------------------------------------

def run_baseline(csv_folder: str, params: Optional[EngineParams] = None) -> None:
    """
    Load all CSVs, run predictions, print accuracy per tier and overall.
    """
    if params is None:
        params = EngineParams()

    df_all = load_all_csvs(csv_folder)

    results = []
    for tier in df_all["tier"].unique():
        df_tier = df_all[df_all["tier"] == tier].copy()
        df_tier = prepare_dataframe(df_tier, params)
        stats = evaluate(df_tier)
        stats["tier"] = tier
        results.append(stats)
        print(
            f"  Tier={tier}  Accuracy={stats['accuracy']:.1%}  "
            f"Correct={stats['correct']}/{stats['total']}  "
            f"Preds={stats['predicted_counts']}  Actual={stats['actual_counts']}"
        )

    # Overall
    total_correct = sum(r["correct"] for r in results)
    total_matches = sum(r["total"] for r in results)
    overall = total_correct / total_matches if total_matches else 0
    print(f"\n  OVERALL: {overall:.1%}  ({total_correct}/{total_matches})")


if __name__ == "__main__":
    import sys

    folder = sys.argv[1] if len(sys.argv) > 1 else "."
    print(f"Running EdgeLab baseline on CSVs in: {folder}\n")
    run_baseline(folder)
