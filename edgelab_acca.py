#!/usr/bin/env python3
"""
EdgeLab Acca Builder v2
------------------------
Redesigned from scratch S40. Each acca type has its own qualification logic,
rating function, and Gary comment style. No shared rating logic across types.

Acca types:
    result        — H/A picks, high conviction, 3/4/5 fold
    result_btts   — Win predicted + both teams score (btts_prob + scoreline support)
    clean_sheet   — Win predicted + opposition doesn't score (win to nil)
    vs_market     — Engine disagrees with market favourite by 5pp+ edge
    draw          — D picks only, CONVICTION_HIGH threshold
    no_score_draw — 0-0 specifically, gated on pred_scoreline / top_scoreline_match
    upset         — High conviction engine call in HIGH chaos tier
    combo         — Best decorrelated picks across all other types (2 versions: 3-fold, 5-fold)

Usage:
    python edgelab_acca.py predictions/2026-04-17_predictions.csv --all-types
    python edgelab_acca.py predictions/2026-04-17_predictions.csv --type result --fold 5
    python edgelab_acca.py predictions/2026-04-17_predictions.csv --type vs_market
    python edgelab_acca.py predictions/2026-04-17_predictions.csv --picks
"""

import os
import sys
import math
import argparse
import itertools
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from collections import Counter

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Thresholds — central. Change here, changes everywhere.
# ---------------------------------------------------------------------------

CONF_THRESHOLD       = 0.52   # minimum confidence for any result pick
CONVICTION_HIGH      = 0.65   # high conviction band
CONVICTION_MED       = 0.55   # medium conviction band

BTTS_PROB_MIN        = 0.60   # tighter than old 0.55 — reduces misfires
BTTS_SCORELINE_BOOST = 0.10   # gary_rating bonus when pred_scoreline agrees with BTTS

CLEAN_SHEET_CONF_MIN = 0.60   # win confidence minimum for clean sheet pick
MARKET_EDGE_MIN      = 0.05   # minimum engine edge vs bookmaker implied prob (5pp)
RESULT_ACCA_MIN_IMPLIED_PROB = 0.40  # result acca: exclude long shots below 40% implied prob

DRAW_CONF_MIN        = CONVICTION_HIGH   # draws need high conviction only
NO_SCORE_DRAW_CONF   = 0.55             # 0-0 threshold — scoreline gate does heavy lifting

UPSET_CONF_MIN       = CONVICTION_HIGH   # engine must be confident even in chaos
UPSET_SCORE_MIN      = 0.60             # upset score threshold

# Decorrelation penalties
SAME_TIER_PENALTY           = 0.15
SAME_COUNTRY_RESULT_PENALTY = 0.08


# ---------------------------------------------------------------------------
# Acca type registry — labels and descriptions
# ---------------------------------------------------------------------------

ACCA_TYPES = {
    "result":        "Results acca (H/A picks)",
    "result_btts":   "Result + BTTS (win and both teams to score)",
    "clean_sheet":   "Clean sheet acca (win to nil)",
    "vs_market":     "Against the market (engine disagrees with bookie favourite)",
    "draw":          "Draw acca (high conviction draws)",
    "no_score_draw": "No-score draw acca (0-0 specific)",
    "upset":         "Upset acca (confident calls in high-chaos matches)",
    "combo":         "Combo acca (best picks across all types)",
}

ALL_STANDARD_TYPES = ["result", "result_btts", "clean_sheet", "vs_market",
                      "draw", "no_score_draw", "upset"]


# ---------------------------------------------------------------------------
# Constraints dataclass
# ---------------------------------------------------------------------------

@dataclass
class AccaConstraints:
    fold: int = 5
    max_odds: Optional[float] = None
    min_odds: Optional[float] = None
    exclude_tiers: List[str] = field(default_factory=list)
    include_tiers: List[str] = field(default_factory=list)
    result_types: List[str] = field(default_factory=list)
    max_same_tier: int = 2
    acca_type: str = "result"


# ---------------------------------------------------------------------------
# AccaPick dataclass
# ---------------------------------------------------------------------------

@dataclass
class AccaPick:
    home_team: str
    away_team: str
    date: str
    tier: str
    prediction: str
    confidence: float
    dti: float
    chaos_tier: str
    upset_flag: bool
    upset_score: float
    btts_flag: bool
    btts_prob: float
    conviction: str
    selection_label: str
    acca_type: str                        # which type this pick came from
    pred_scoreline: Optional[str] = None  # predicted scoreline e.g. "2-1"
    top_scoreline_match: Optional[str] = None
    b365h: Optional[float] = None
    b365d: Optional[float] = None
    b365a: Optional[float] = None
    implied_prob: Optional[float] = None
    edge: Optional[float] = None


# ---------------------------------------------------------------------------
# Acca dataclass
# ---------------------------------------------------------------------------

@dataclass
class Acca:
    picks: List[AccaPick]
    acca_type: str
    fold: int
    combined_odds: Optional[float]
    decorrelation_score: float
    conviction_score: float
    gary_rating: float
    gary_comment: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_scoreline(scoreline: Optional[str]):
    """Parse 'H-A' string to (int, int) or None."""
    if not scoreline or not isinstance(scoreline, str):
        return None
    parts = scoreline.strip().split("-")
    if len(parts) != 2:
        return None
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None


def _scoreline_has_both_goals(scoreline: Optional[str]) -> bool:
    """True if predicted scoreline has both teams scoring."""
    parsed = _parse_scoreline(scoreline)
    if parsed is None:
        return False
    return parsed[0] > 0 and parsed[1] > 0


def _scoreline_is_clean_sheet(scoreline: Optional[str], prediction: str) -> bool:
    """True if predicted scoreline has the winning team keeping a clean sheet."""
    parsed = _parse_scoreline(scoreline)
    if parsed is None:
        return False
    home_goals, away_goals = parsed
    if prediction == "H":
        return away_goals == 0 and home_goals > 0
    if prediction == "A":
        return home_goals == 0 and away_goals > 0
    return False


def _scoreline_is_nil_nil(scoreline: Optional[str]) -> bool:
    parsed = _parse_scoreline(scoreline)
    if parsed is None:
        return False
    return parsed[0] == 0 and parsed[1] == 0


def _top_match_is_nil_nil(top_scoreline_match: Optional[str]) -> bool:
    if not top_scoreline_match or not isinstance(top_scoreline_match, str):
        return False
    return "0-0" in top_scoreline_match


def _country_prefix(tier: str) -> str:
    return tier[:2] if len(tier) >= 2 else tier


def _conviction_band(conf: float) -> str:
    return "HIGH" if conf >= CONVICTION_HIGH else "MED"


# ---------------------------------------------------------------------------
# Core builder
# ---------------------------------------------------------------------------

class AccaBuilder:

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self._normalise_columns()

    def _normalise_columns(self):
        defaults = {
            "confidence":          0.0,
            "dti":                 0.5,
            "chaos_tier":          "HIGH",
            "upset_flag":          0,
            "upset_score":         0.0,
            "btts_flag":           False,
            "btts_prob":           0.0,
            "draw_score":          0.0,
            "B365H":               np.nan,
            "B365D":               np.nan,
            "B365A":               np.nan,
            "pred_scoreline":      None,
            "top_scoreline_match": None,
        }
        for col, default in defaults.items():
            if col not in self.df.columns:
                self.df[col] = default

        self.df["upset_flag"]  = self.df["upset_flag"].fillna(0).astype(int)
        self.df["btts_flag"]   = self.df["btts_flag"].fillna(False).astype(bool)
        self.df["confidence"]  = pd.to_numeric(self.df["confidence"],  errors="coerce").fillna(0.0)
        self.df["dti"]         = pd.to_numeric(self.df["dti"],         errors="coerce").fillna(0.5)
        self.df["btts_prob"]   = pd.to_numeric(self.df["btts_prob"],   errors="coerce").fillna(0.0)
        self.df["upset_score"] = pd.to_numeric(self.df["upset_score"], errors="coerce").fillna(0.0)

    # -------------------------------------------------------------------------
    # Bookmaker helpers
    # -------------------------------------------------------------------------

    def _get_odds_and_edge(self, row, pred: str):
        b365h = row.get("B365H", np.nan)
        b365d = row.get("B365D", np.nan)
        b365a = row.get("B365A", np.nan)
        conf  = float(row.get("confidence", 0.0))

        b365h = float(b365h) if pd.notna(b365h) else None
        b365d = float(b365d) if pd.notna(b365d) else None
        b365a = float(b365a) if pd.notna(b365a) else None

        implied_prob = None
        edge = None
        if pred == "H" and b365h and b365h > 1.0:
            implied_prob = round(1.0 / b365h, 3)
            edge = round(conf - implied_prob, 3)
        elif pred == "A" and b365a and b365a > 1.0:
            implied_prob = round(1.0 / b365a, 3)
            edge = round(conf - implied_prob, 3)
        elif pred == "D" and b365d and b365d > 1.0:
            implied_prob = round(1.0 / b365d, 3)
            edge = round(conf - implied_prob, 3)

        return b365h, b365d, b365a, implied_prob, edge

    def _market_favourite(self, row) -> Optional[str]:
        """Return H/D/A for whichever bookmaker price is lowest (shortest odds = favourite)."""
        b365h = row.get("B365H", np.nan)
        b365d = row.get("B365D", np.nan)
        b365a = row.get("B365A", np.nan)
        prices = {}
        if pd.notna(b365h) and float(b365h) > 1.0:
            prices["H"] = float(b365h)
        if pd.notna(b365d) and float(b365d) > 1.0:
            prices["D"] = float(b365d)
        if pd.notna(b365a) and float(b365a) > 1.0:
            prices["A"] = float(b365a)
        if not prices:
            return None
        return min(prices, key=prices.get)

    # -------------------------------------------------------------------------
    # Stage 1 — per-type qualification filters
    # -------------------------------------------------------------------------

    def _base_filter(self, df: pd.DataFrame, constraints: AccaConstraints) -> pd.DataFrame:
        """Apply tier filters common to all types."""
        if constraints.exclude_tiers:
            df = df[~df["tier"].isin(constraints.exclude_tiers)]
        if constraints.include_tiers:
            df = df[df["tier"].isin(constraints.include_tiers)]
        return df

    def _qualify_result(self, df: pd.DataFrame) -> pd.DataFrame:
        """H/A picks. High conviction. Low-to-medium chaos only. No draws.
        If pred_scoreline is present, it must not be a draw scoreline — hard gate.
        A pick can't be in the result acca if the score model predicts a draw.
        """
        df = df[df["prediction"].isin(["H", "A"])]
        df = df[df["confidence"] >= CONVICTION_HIGH]
        df = df[df["chaos_tier"].isin({"LOW", "MED"})]
        df = df[df["upset_flag"] == 0]

        qualifying = []
        for _, row in df.iterrows():
            pred = row["prediction"]
            pred_sc = row.get("pred_scoreline", None)
            if isinstance(pred_sc, float) and math.isnan(pred_sc):
                pred_sc = None
            if pred_sc is not None:
                parsed = _parse_scoreline(pred_sc)
                if parsed is not None and parsed[0] == parsed[1]:
                    continue  # score model predicts a draw — exclude from result acca
            # Exclude long shots: implied prob below threshold (e.g. Charlton-type picks)
            _, _, _, implied_prob, _ = self._get_odds_and_edge(row, pred)
            if implied_prob is not None and implied_prob < RESULT_ACCA_MIN_IMPLIED_PROB:
                continue
            qualifying.append(row.name)

        return df.loc[qualifying] if qualifying else df.iloc[0:0]

    def _qualify_result_btts(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Win predicted + BTTS.
        Gate: confidence >= HIGH, btts_prob >= 0.60, chaos LOW/MED.
        If pred_scoreline present, both teams must score — hard gate.
        pred_scoreline agreement also adds a rating bonus at scoring stage.
        """
        df = df[df["prediction"].isin(["H", "A"])]
        df = df[df["confidence"] >= CONVICTION_HIGH]
        df = df[df["btts_prob"] >= BTTS_PROB_MIN]
        df = df[df["chaos_tier"].isin({"LOW", "MED"})]
        df = df[df["upset_flag"] == 0]

        qualifying = []
        for _, row in df.iterrows():
            pred_sc = row.get("pred_scoreline", None)
            if isinstance(pred_sc, float) and math.isnan(pred_sc):
                pred_sc = None
            if pred_sc is not None:
                if not _scoreline_has_both_goals(pred_sc):
                    continue
            qualifying.append(row.name)

        return df.loc[qualifying] if qualifying else df.iloc[0:0]

    def _qualify_clean_sheet(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Win predicted + opposition doesn't score.
        If pred_scoreline is present, it must support a clean sheet — hard gate.
        If pred_scoreline is absent, allow through (no data = don't exclude).
        Note: away goals currently overestimated (1.37 pred vs 1.07 actual).
        Clean sheet picks carry that caveat until score prediction is recalibrated.
        """
        df = df[df["prediction"].isin(["H", "A"])]
        df = df[df["confidence"] >= CLEAN_SHEET_CONF_MIN]
        df = df[df["chaos_tier"].isin({"LOW", "MED"})]
        df = df[df["upset_flag"] == 0]

        qualifying = []
        for _, row in df.iterrows():
            pred   = row["prediction"]
            pred_sc = row.get("pred_scoreline", None)
            if isinstance(pred_sc, float) and math.isnan(pred_sc):
                pred_sc = None
            # If scoreline present, it must support a clean sheet
            if pred_sc is not None:
                if not _scoreline_is_clean_sheet(pred_sc, pred):
                    continue
            qualifying.append(row.name)

        return df.loc[qualifying] if qualifying else df.iloc[0:0]

    def _qualify_vs_market(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Engine picks H/A where bookmaker has the other side favoured.
        Engine must beat bookmaker implied probability by at least MARKET_EDGE_MIN.
        """
        df = df[df["prediction"].isin(["H", "A"])]
        df = df[df["confidence"] >= CONF_THRESHOLD]
        df = df[df["chaos_tier"].isin({"LOW", "MED", "HIGH"})]  # allow HIGH — that's where mispricing lives

        qualifying = []
        for _, row in df.iterrows():
            pred = row["prediction"]
            conf = float(row["confidence"])
            market_fav = self._market_favourite(row)
            _, _, _, implied_prob, edge = self._get_odds_and_edge(row, pred)

            # Engine must disagree with market favourite
            if market_fav is None or market_fav == pred:
                continue
            # Edge must clear the minimum
            if edge is None or edge < MARKET_EDGE_MIN:
                continue

            qualifying.append(row.name)

        return df.loc[qualifying] if qualifying else df.iloc[0:0]

    def _qualify_draw(self, df: pd.DataFrame) -> pd.DataFrame:
        """D picks only. High conviction only. Low chaos only."""
        df = df[df["prediction"] == "D"]
        df = df[df["confidence"] >= DRAW_CONF_MIN]
        df = df[df["chaos_tier"] == "LOW"]
        return df

    def _qualify_no_score_draw(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        0-0 specific. D prediction required.
        Gate: pred_scoreline = '0-0' OR top_scoreline_match contains '0-0'.
        Both signals together = strongest qualification.
        """
        df = df[df["prediction"] == "D"]
        df = df[df["confidence"] >= NO_SCORE_DRAW_CONF]

        qualifying = []
        for _, row in df.iterrows():
            pred_sc  = row.get("pred_scoreline", None)
            top_sc   = row.get("top_scoreline_match", None)
            pred_nil = _scoreline_is_nil_nil(pred_sc)
            top_nil  = _top_match_is_nil_nil(top_sc)
            if pred_nil or top_nil:
                qualifying.append(row.name)

        return df.loc[qualifying] if qualifying else df.iloc[0:0]

    def _qualify_upset(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Engine is highly confident AND the match is HIGH chaos.
        Different from vs_market — market might agree. It's about match volatility.
        """
        df = df[df["prediction"].isin(["H", "A"])]
        df = df[df["confidence"] >= UPSET_CONF_MIN]
        df = df[df["chaos_tier"] == "HIGH"]
        df = df[df["upset_score"] >= UPSET_SCORE_MIN]
        return df

    # -------------------------------------------------------------------------
    # Build AccaPick objects from a filtered dataframe
    # -------------------------------------------------------------------------

    def _build_picks(self, df: pd.DataFrame, acca_type: str) -> List[AccaPick]:
        picks = []
        for _, row in df.iterrows():
            pred = row["prediction"]
            home = row["HomeTeam"]
            away = row["AwayTeam"]
            conf = float(row["confidence"])
            pred_sc = row.get("pred_scoreline", None)
            if isinstance(pred_sc, float) and math.isnan(pred_sc):
                pred_sc = None
            top_sc = row.get("top_scoreline_match", None)
            if isinstance(top_sc, float) and math.isnan(top_sc):
                top_sc = None

            b365h, b365d, b365a, implied_prob, edge = self._get_odds_and_edge(row, pred)

            # Selection label
            if acca_type == "result_btts":
                winner = home if pred == "H" else away
                label = f"{winner} to win & BTTS"
            elif acca_type == "clean_sheet":
                winner = home if pred == "H" else away
                loser  = away if pred == "H" else home
                label = f"{winner} to win & {loser} not to score"
            elif acca_type == "vs_market":
                winner = home if pred == "H" else away
                label = f"{winner} to win (vs market)"
            elif acca_type == "draw":
                label = f"{home} vs {away} — Draw"
            elif acca_type == "no_score_draw":
                label = f"{home} vs {away} — 0-0"
            elif acca_type == "upset":
                winner = home if pred == "H" else away
                label = f"{winner} to win (upset call)"
            elif pred == "H":
                label = f"{home} to win"
            elif pred == "A":
                label = f"{away} to win"
            else:
                label = f"{home} vs {away} — Draw"

            picks.append(AccaPick(
                home_team=home,
                away_team=away,
                date=str(row.get("Date", "")),
                tier=str(row.get("tier", "")),
                prediction=pred,
                confidence=conf,
                dti=float(row.get("dti", 0.5)),
                chaos_tier=str(row.get("chaos_tier", "MED")),
                upset_flag=bool(row.get("upset_flag", 0)),
                upset_score=float(row.get("upset_score", 0.0)),
                btts_flag=bool(row.get("btts_flag", False)),
                btts_prob=float(row.get("btts_prob", 0.0)),
                conviction=_conviction_band(conf),
                selection_label=label,
                acca_type=acca_type,
                pred_scoreline=pred_sc,
                top_scoreline_match=top_sc,
                b365h=b365h,
                b365d=b365d,
                b365a=b365a,
                implied_prob=implied_prob,
                edge=edge,
            ))

        picks.sort(key=lambda p: (0 if p.conviction == "HIGH" else 1, -p.confidence))
        return picks

    def get_picks(self, constraints: Optional[AccaConstraints] = None) -> List[AccaPick]:
        if constraints is None:
            constraints = AccaConstraints()

        df = self._base_filter(self.df.copy(), constraints)
        t = constraints.acca_type

        if t == "result":
            df = self._qualify_result(df)
        elif t == "result_btts":
            df = self._qualify_result_btts(df)
        elif t == "clean_sheet":
            df = self._qualify_clean_sheet(df)
        elif t == "vs_market":
            df = self._qualify_vs_market(df)
        elif t == "draw":
            df = self._qualify_draw(df)
        elif t == "no_score_draw":
            df = self._qualify_no_score_draw(df)
        elif t == "upset":
            df = self._qualify_upset(df)
        elif t == "combo":
            return self._get_combo_picks(constraints)
        else:
            df = self._qualify_result(df)

        return self._build_picks(df, t)

    # -------------------------------------------------------------------------
    # Combo pick collection
    # -------------------------------------------------------------------------

    def _combo_value_score(self, pick: AccaPick) -> float:
        """
        Per-pick value score for combo pool ranking.
        Edge vs market is the primary driver where available.
        Confidence fallback (capped below any edged pick) where odds data absent.

        Edged picks score in range [0.5, 1.0].
        No-edge picks score in range [0.0, 0.49] — always below any edged pick.
        """
        conf = pick.confidence

        # Scoreline signal bonus — any type where scoreline agrees with the call
        sc_bonus = 0.0
        if pick.acca_type == "result_btts" and _scoreline_has_both_goals(pick.pred_scoreline):
            sc_bonus = 0.05
        elif pick.acca_type == "clean_sheet" and _scoreline_is_clean_sheet(pick.pred_scoreline, pick.prediction):
            sc_bonus = 0.05
        elif pick.acca_type == "no_score_draw" and _scoreline_is_nil_nil(pick.pred_scoreline):
            sc_bonus = 0.05

        if pick.edge is not None:
            # Edge available — primary scoring
            # Normalise edge: 0.05 = floor, 0.20+ = near ceiling
            norm_edge = min(max((pick.edge - MARKET_EDGE_MIN) / 0.15, 0.0), 1.0)
            return round(0.50 + (norm_edge * 0.35) + (conf * 0.10) + sc_bonus, 4)
        else:
            # No odds data — confidence fallback, capped at 0.49
            return round(min((conf * 0.45) + sc_bonus, 0.49), 4)

    def _get_combo_picks(self, constraints: AccaConstraints) -> List[AccaPick]:
        """
        Build combo pool in two passes:
        Pass 1 — take the highest value pick from each standard type (type diversity enforced).
        Pass 2 — fill remaining slots from the full pool by value score, deduplicated by match.

        Value score = edge vs market (primary) + confidence (fallback) + scoreline signal.
        Picks with edge data always rank above picks without.
        """
        seen_matches = set()
        pool = []

        # Pass 1 — one top pick per type
        for t in ALL_STANDARD_TYPES:
            c = AccaConstraints(
                fold=constraints.fold,
                exclude_tiers=constraints.exclude_tiers,
                include_tiers=constraints.include_tiers,
                acca_type=t,
            )
            picks = self.get_picks(c)
            if not picks:
                continue
            # Sort by value score, take best
            picks.sort(key=lambda p: -self._combo_value_score(p))
            for p in picks:
                key = f"{p.home_team}|{p.away_team}|{p.date}"
                if key not in seen_matches:
                    seen_matches.add(key)
                    pool.append(p)
                    break  # one per type in pass 1

        # Pass 2 — fill from full pool by value, deduped
        for t in ALL_STANDARD_TYPES:
            c = AccaConstraints(
                fold=constraints.fold,
                exclude_tiers=constraints.exclude_tiers,
                include_tiers=constraints.include_tiers,
                acca_type=t,
            )
            picks = self.get_picks(c)
            picks.sort(key=lambda p: -self._combo_value_score(p))
            for p in picks:
                key = f"{p.home_team}|{p.away_team}|{p.date}"
                if key not in seen_matches:
                    seen_matches.add(key)
                    pool.append(p)

        pool.sort(key=lambda p: -self._combo_value_score(p))
        return pool

    # -------------------------------------------------------------------------
    # Decorrelation
    # -------------------------------------------------------------------------

    def _decorrelation_score(self, combo: List[AccaPick]) -> float:
        score = 1.0
        for i, p1 in enumerate(combo):
            for p2 in combo[i+1:]:
                if p1.tier == p2.tier and p1.date == p2.date:
                    score -= SAME_TIER_PENALTY
                if (_country_prefix(p1.tier) == _country_prefix(p2.tier)
                        and p1.prediction == p2.prediction):
                    score -= SAME_COUNTRY_RESULT_PENALTY
        return max(round(score, 3), 0.0)

    # -------------------------------------------------------------------------
    # Combined odds
    # -------------------------------------------------------------------------

    def _combined_odds(self, combo: List[AccaPick]) -> Optional[float]:
        total = 1.0
        for pick in combo:
            if pick.prediction == "H" and pick.b365h:
                total *= pick.b365h
            elif pick.prediction == "A" and pick.b365a:
                total *= pick.b365a
            elif pick.prediction == "D" and pick.b365d:
                total *= pick.b365d
            else:
                return None
        return round(total, 2)

    # -------------------------------------------------------------------------
    # Rating functions — one per type, no shared logic
    # -------------------------------------------------------------------------

    def _rate_result(self, combo: List[AccaPick], decor: float) -> float:
        avg_conf   = sum(p.confidence for p in combo) / len(combo)
        high_frac  = sum(1 for p in combo if p.conviction == "HIGH") / len(combo)
        return round((avg_conf * 0.60) + (decor * 0.25) + (high_frac * 0.15), 4)

    def _rate_result_btts(self, combo: List[AccaPick], decor: float) -> float:
        avg_conf = sum(p.confidence for p in combo) / len(combo)
        avg_btts = sum(p.btts_prob for p in combo) / len(combo)
        # Bonus if pred_scoreline supports BTTS
        sc_bonus = sum(
            BTTS_SCORELINE_BOOST for p in combo
            if _scoreline_has_both_goals(p.pred_scoreline)
        ) / len(combo)
        return round((avg_conf * 0.40) + (avg_btts * 0.35) + (decor * 0.15) + (sc_bonus * 0.10), 4)

    def _rate_clean_sheet(self, combo: List[AccaPick], decor: float) -> float:
        avg_conf = sum(p.confidence for p in combo) / len(combo)
        # Bonus if pred_scoreline supports clean sheet
        sc_support = sum(
            0.10 for p in combo
            if _scoreline_is_clean_sheet(p.pred_scoreline, p.prediction)
        ) / len(combo)
        return round((avg_conf * 0.55) + (decor * 0.25) + (sc_support * 0.20), 4)

    def _rate_vs_market(self, combo: List[AccaPick], decor: float) -> float:
        edges = [p.edge for p in combo if p.edge is not None]
        avg_edge = sum(edges) / len(edges) if edges else 0.0
        avg_conf = sum(p.confidence for p in combo) / len(combo)
        return round((avg_edge * 0.55) + (avg_conf * 0.25) + (decor * 0.20), 4)

    def _rate_draw(self, combo: List[AccaPick], decor: float) -> float:
        avg_conf = sum(p.confidence for p in combo) / len(combo)
        return round((avg_conf * 0.65) + (decor * 0.35), 4)

    def _rate_no_score_draw(self, combo: List[AccaPick], decor: float) -> float:
        avg_conf = sum(p.confidence for p in combo) / len(combo)
        # Both signals firing = stronger
        dual_signal = sum(
            0.15 for p in combo
            if _scoreline_is_nil_nil(p.pred_scoreline) and _top_match_is_nil_nil(p.top_scoreline_match)
        ) / len(combo)
        return round((avg_conf * 0.55) + (dual_signal * 0.25) + (decor * 0.20), 4)

    def _rate_upset(self, combo: List[AccaPick], decor: float) -> float:
        avg_conf   = sum(p.confidence for p in combo) / len(combo)
        avg_upset  = sum(p.upset_score for p in combo) / len(combo)
        return round((avg_conf * 0.45) + (avg_upset * 0.35) + (decor * 0.20), 4)

    def _rate_combo(self, combo: List[AccaPick], decor: float) -> float:
        avg_conf  = sum(p.confidence for p in combo) / len(combo)
        type_div  = len({p.acca_type for p in combo}) / len(combo)  # type diversity
        return round((avg_conf * 0.50) + (decor * 0.30) + (type_div * 0.20), 4)

    def _gary_rating(self, combo: List[AccaPick], decor: float, acca_type: str) -> float:
        dispatch = {
            "result":        self._rate_result,
            "result_btts":   self._rate_result_btts,
            "clean_sheet":   self._rate_clean_sheet,
            "vs_market":     self._rate_vs_market,
            "draw":          self._rate_draw,
            "no_score_draw": self._rate_no_score_draw,
            "upset":         self._rate_upset,
            "combo":         self._rate_combo,
        }
        fn = dispatch.get(acca_type, self._rate_result)
        return fn(combo, decor)

    # -------------------------------------------------------------------------
    # Gary comments — per type
    # -------------------------------------------------------------------------

    def _gary_comment(self, combo: List[AccaPick], acca_type: str, rating: float) -> str:
        high  = sum(1 for p in combo if p.conviction == "HIGH")
        tiers = list({p.tier for p in combo})
        n     = len(combo)

        if acca_type == "result":
            if rating >= 0.70:
                return f"{high}/{n} bankers. Well spread. This is the one Gary would put his name to."
            if rating >= 0.60:
                return f"Solid. {high} bankers in there. The rest need to behave."
            return f"Decent enough. Gary wouldn't lose sleep over it."

        if acca_type == "result_btts":
            sc_agree = sum(1 for p in combo if _scoreline_has_both_goals(p.pred_scoreline))
            if sc_agree == n:
                return f"Win and goals — scoreline model agrees on all {n} legs. Gary likes this."
            if sc_agree > 0:
                return f"Win and goals — scoreline model agrees on {sc_agree}/{n} legs."
            return f"{n} confident wins where both teams are expected to score."

        if acca_type == "clean_sheet":
            sc_support = sum(1 for p in combo if _scoreline_is_clean_sheet(p.pred_scoreline, p.prediction))
            note = f"Scoreline model supports {sc_support}/{n}." if sc_support > 0 else "Note: score prediction overestimates away goals — treat with care."
            return f"Win to nil. {note}"

        if acca_type == "vs_market":
            edges = [p.edge for p in combo if p.edge is not None]
            avg_e = sum(edges) / len(edges) if edges else 0.0
            return f"Market got it wrong on all {n} legs. Average edge: {avg_e:+.0%}. This is what we're here for."

        if acca_type == "draw":
            return f"{n} high-conviction draw calls. Low chaos only. Gary's earned the right to call draws."

        if acca_type == "no_score_draw":
            dual = sum(1 for p in combo if _scoreline_is_nil_nil(p.pred_scoreline) and _top_match_is_nil_nil(p.top_scoreline_match))
            return f"0-0 specific. {dual}/{n} with both signals firing. Niche. But that's the point."

        if acca_type == "upset":
            return f"{n} confident calls in high-chaos matches. Engine is sure. Match is not. That's the bet."

        if acca_type == "combo":
            types = list({p.acca_type for p in combo})
            return f"Best of everything. {len(types)} different signal types in one acca. Highest value combination."

        return f"Gary's pick."

    # -------------------------------------------------------------------------
    # Constraints check
    # -------------------------------------------------------------------------

    def _check_odds_constraints(self, odds: Optional[float], constraints: AccaConstraints) -> bool:
        if odds is None:
            return True
        if constraints.max_odds and odds > constraints.max_odds:
            return False
        if constraints.min_odds and odds < constraints.min_odds:
            return False
        return True

    def _max_same_tier_ok(self, combo: List[AccaPick], max_same: int) -> bool:
        counts = Counter(p.tier for p in combo)
        return max(counts.values()) <= max_same

    # -------------------------------------------------------------------------
    # Build
    # -------------------------------------------------------------------------

    def build(
        self,
        constraints: Optional[AccaConstraints] = None,
        top_n: int = 3,
    ) -> List[Acca]:
        if constraints is None:
            constraints = AccaConstraints()

        picks = self.get_picks(constraints)

        if not picks:
            return []

        fold = constraints.fold
        if len(picks) < fold:
            fold = len(picks)
        if fold < 2:
            return []

        candidate_picks = picks[:20]
        combos = list(itertools.combinations(candidate_picks, fold))

        scored = []
        for combo in combos:
            combo = list(combo)

            if not self._max_same_tier_ok(combo, constraints.max_same_tier):
                continue

            decor  = self._decorrelation_score(combo)
            odds   = self._combined_odds(combo)
            rating = self._gary_rating(combo, decor, constraints.acca_type)

            if not self._check_odds_constraints(odds, constraints):
                continue

            comment  = self._gary_comment(combo, constraints.acca_type, rating)
            avg_conf = sum(p.confidence for p in combo) / len(combo)

            scored.append(Acca(
                picks=combo,
                acca_type=constraints.acca_type,
                fold=fold,
                combined_odds=odds,
                decorrelation_score=decor,
                conviction_score=round(avg_conf, 3),
                gary_rating=rating,
                gary_comment=comment,
            ))

        if not scored:
            return []

        scored.sort(key=lambda a: -a.gary_rating)
        return scored[:top_n]

    # -------------------------------------------------------------------------
    # Combo acca — two versions: 3-fold and 5-fold best decorrelated
    # -------------------------------------------------------------------------

    def build_combo(self, constraints: Optional[AccaConstraints] = None) -> List[Acca]:
        """Build 3-fold and 5-fold combo accas."""
        results = []
        for fold in [3, 5]:
            c = AccaConstraints(
                fold=fold,
                max_odds=constraints.max_odds if constraints else None,
                min_odds=constraints.min_odds if constraints else None,
                exclude_tiers=constraints.exclude_tiers if constraints else [],
                include_tiers=constraints.include_tiers if constraints else [],
                acca_type="combo",
            )
            built = self.build(c, top_n=1)
            if built:
                results.extend(built)
        return results

    # -------------------------------------------------------------------------
    # Full matchday briefing
    # -------------------------------------------------------------------------

    def build_all_types(self, fold: int = 5) -> Dict[str, List[Acca]]:
        results = {}
        for t in ALL_STANDARD_TYPES:
            c = AccaConstraints(fold=fold, acca_type=t)
            built = self.build(c, top_n=1)
            if built:
                results[t] = built
        # Combo — always 3 and 5 fold
        combos = self.build_combo()
        if combos:
            results["combo"] = combos
        return results

    def _warn_duplicates(self, all_accas: Dict[str, List[Acca]]) -> None:
        match_appearances: Dict[str, List[str]] = {}
        for acca_type, accas in all_accas.items():
            if not accas:
                continue
            for pick in accas[0].picks:
                key = f"{pick.home_team} vs {pick.away_team} ({pick.date})"
                match_appearances.setdefault(key, []).append(acca_type)

        duplicates = {k: v for k, v in match_appearances.items() if len(v) > 1}
        if duplicates:
            print(f"\n  ⚠  DUPLICATE PICKS ACROSS ACCA TYPES:")
            for match, types in duplicates.items():
                print(f"     {match}  ->  {' + '.join(ACCA_TYPES.get(t, t) for t in types)}")
            print(f"     These legs are correlated — consider diversifying.")

    # -------------------------------------------------------------------------
    # Output
    # -------------------------------------------------------------------------

    def print_accas(self, accas: List[Acca], label: str = "") -> None:
        print(f"\n{'='*60}")
        if label:
            print(f"  {label}")
        print(f"  GARY'S ACCA RECOMMENDATIONS")
        print(f"{'='*60}")

        if not accas:
            print("\n  Nothing clearing Gary's bar today. "
                  "He'd rather tell you nothing than tell you something he doesn't believe.")
            return

        for i, acca in enumerate(accas, 1):
            odds_str = f"  ~{acca.combined_odds:.1f}/1" if acca.combined_odds else ""
            print(f"\n  ── Option {i} — {acca.fold}-fold "
                  f"{ACCA_TYPES.get(acca.acca_type, acca.acca_type)}{odds_str}")
            print(f"     Rating: {acca.gary_rating:.3f}  |  "
                  f"Avg confidence: {acca.conviction_score:.0%}  |  "
                  f"Decorrelation: {acca.decorrelation_score:.2f}")
            print(f"     Gary: \"{acca.gary_comment}\"")
            print()
            for j, pick in enumerate(acca.picks, 1):
                edge_str = f"  edge={pick.edge:+.0%}" if pick.edge is not None else ""
                sc_str   = f"  pred={pick.pred_scoreline}" if pick.pred_scoreline else ""
                print(f"     {j}. [{pick.tier}] {pick.date}  {pick.selection_label}")
                print(f"        Conf={pick.confidence:.0%}  DTI={pick.dti:.3f}  "
                      f"{pick.chaos_tier}  [{pick.conviction}]{edge_str}{sc_str}")

        print(f"\n{'='*60}\n")

    def print_matchday_briefing(self, fold: int = 5) -> None:
        print(f"\n{'='*60}")
        print(f"  GARY'S MATCHDAY ACCA BRIEFING")
        print(f"{'='*60}")

        all_accas = self.build_all_types(fold=fold)

        if not all_accas:
            print("\n  Nothing today Gary would put his name to. He's told you. Leave it.")
            return

        for acca_type, accas in all_accas.items():
            if not accas:
                continue
            acca = accas[0]
            odds_str = f"  ~{acca.combined_odds:.1f}/1" if acca.combined_odds else ""
            print(f"\n  ── {ACCA_TYPES.get(acca_type, acca_type)}{odds_str}")
            print(f"     \"{acca.gary_comment}\"")
            for j, pick in enumerate(acca.picks, 1):
                edge_str = f"  edge={pick.edge:+.0%}" if pick.edge is not None else ""
                sc_str   = f"  pred={pick.pred_scoreline}" if pick.pred_scoreline else ""
                print(f"     {j}. {pick.selection_label}  [{pick.tier}]  "
                      f"{pick.confidence:.0%}{edge_str}{sc_str}")

            all_picks = self.get_picks(AccaConstraints(acca_type=acca_type))
            if len(all_picks) > len(acca.picks):
                print(f"\n     All qualifying picks ({len(all_picks)} total):")
                for pick in all_picks:
                    edge_str = f"  edge={pick.edge:+.0%}" if pick.edge is not None else ""
                    sc_str   = f"  pred={pick.pred_scoreline}" if pick.pred_scoreline else ""
                    print(f"       [{pick.conviction}] {pick.date}  {pick.selection_label}  "
                          f"[{pick.tier}]  conf={pick.confidence:.0%}  "
                          f"{pick.chaos_tier}{edge_str}{sc_str}")

        self._warn_duplicates(all_accas)
        print(f"\n{'='*60}\n")


# ---------------------------------------------------------------------------
# Qualifying picks summary
# ---------------------------------------------------------------------------

def print_qualifying_picks(picks: List[AccaPick]) -> None:
    print(f"\n  ── QUALIFYING PICKS ({len(picks)} cleared Gary's bar) ──")
    if not picks:
        print("  None.")
        return
    for pick in picks:
        edge_str = f"  edge={pick.edge:+.0%}" if pick.edge is not None else ""
        sc_str   = f"  pred={pick.pred_scoreline}" if pick.pred_scoreline else ""
        print(f"  [{pick.conviction:<4}] [{pick.tier}]  {pick.date}  "
              f"{pick.selection_label:<50}  "
              f"conf={pick.confidence:.0%}  DTI={pick.dti:.3f}  "
              f"{pick.chaos_tier}{edge_str}{sc_str}")
    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="EdgeLab Acca Builder v2 — Gary's accumulator recommendations"
    )
    parser.add_argument("predictions_csv",
                        help="Path to predictions CSV from edgelab_predict.py")
    parser.add_argument("--fold",      type=int,   default=5)
    parser.add_argument("--max-odds",  type=float, default=None)
    parser.add_argument("--min-odds",  type=float, default=None)
    parser.add_argument("--exclude",   type=str,   default="",
                        help="Comma-separated tiers to exclude e.g. SC2,SC3")
    parser.add_argument("--include",   type=str,   default="",
                        help="Comma-separated tiers to include (whitelist)")
    parser.add_argument("--type",      type=str,   default="result",
                        choices=list(ACCA_TYPES.keys()),
                        help="Acca type (default: result)")
    parser.add_argument("--all-types", action="store_true",
                        help="Full matchday briefing — all types")
    parser.add_argument("--top",       type=int,   default=3,
                        help="Number of options to show (default 3)")
    parser.add_argument("--picks",     action="store_true",
                        help="Show all qualifying picks before combinations")
    args = parser.parse_args()

    if not os.path.exists(args.predictions_csv):
        print(f"\n  File not found: {args.predictions_csv}\n")
        sys.exit(1)

    df = pd.read_csv(args.predictions_csv)
    print(f"\n  Loaded {len(df)} predictions from {os.path.basename(args.predictions_csv)}")

    builder = AccaBuilder(df)

    if args.all_types:
        builder.print_matchday_briefing(fold=args.fold)
        sys.exit(0)

    constraints = AccaConstraints(
        fold=args.fold,
        max_odds=args.max_odds,
        min_odds=args.min_odds,
        exclude_tiers=[t.strip() for t in args.exclude.split(",") if t.strip()],
        include_tiers=[t.strip() for t in args.include.split(",") if t.strip()],
        acca_type=args.type,
    )

    if args.picks:
        picks = builder.get_picks(constraints)
        print_qualifying_picks(picks)

    accas = builder.build(constraints=constraints, top_n=args.top)
    builder.print_accas(accas)


if __name__ == "__main__":
    main()
