#!/usr/bin/env python3
"""
EdgeLab Acca Builder v1
------------------------
Two-stage accumulator selection. Takes a predictions dataframe and builds
Gary's best acca recommendations for the matchday.

Stage 1 — Filter to high-conviction individual picks.
Stage 2 — Select decorrelated combinations from those picks.

Designed to work directly with the output of edgelab_predict.py.

Usage:
    from edgelab_acca import AccaBuilder, AccaConstraints

    # Default — Gary picks the best available
    builder = AccaBuilder(df_predictions)
    accas = builder.build()
    builder.print_accas(accas)

    # User-constrained — bespoke acca
    constraints = AccaConstraints(
        fold=4,
        max_odds=15.0,
        exclude_tiers=["SC2", "SC3"],
        prefer_btts=False,
        include_upsets=False,
    )
    accas = builder.build(constraints=constraints)

CLI:
    python edgelab_acca.py predictions/2026-04-05_predictions.csv
    python edgelab_acca.py predictions/2026-04-05_predictions.csv --fold 4 --max-odds 20
    python edgelab_acca.py predictions/2026-04-05_predictions.csv --upsets
"""

import os
import sys
import argparse
import itertools
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Stage 1 thresholds — what makes a pick high-conviction
# ---------------------------------------------------------------------------

CONF_THRESHOLD      = 0.52   # minimum engine confidence
CHAOS_ALLOWED       = {"LOW", "MED"}   # HIGH chaos = unreadable, skip
UPSET_FLAG_BLOCKS   = True   # upset flag undermines the prediction — skip
MIN_H2H_SUPPORT     = None   # future: require H2H to agree. Not enforced yet.

# Conviction rating bands
CONVICTION_HIGH     = 0.65   # confidence above this = high conviction
CONVICTION_MED      = 0.55   # confidence above this = medium conviction
# Below CONF_THRESHOLD = not selected


# ---------------------------------------------------------------------------
# Decorrelation — what makes two picks independent
# ---------------------------------------------------------------------------

# Picks from the same tier on the same day are correlated —
# a systemic factor (weather, refereeing trend) could hit both.
# We penalise same-tier same-day pairs in combination scoring.
SAME_TIER_PENALTY   = 0.15

# Same result type (both H, or both A) from the same country — mild correlation
SAME_COUNTRY_RESULT_PENALTY = 0.08


# ---------------------------------------------------------------------------
# Acca types
# ---------------------------------------------------------------------------

ACCA_TYPES = {
    "result":      "Result acca (H/A picks)",
    "btts":        "BTTS acca (both teams to score)",
    "winner_btts": "Winner + BTTS acca (high confidence win AND both teams to score)",
    "mixed":       "Mixed acca (results + BTTS)",
    "upset":       "Upset acca (independent upset flags)",
    "safety":      "Safety acca (highest conviction only, lowest odds)",
    "value":       "Value acca (engine edge vs bookmaker implied)",
}


# ---------------------------------------------------------------------------
# Constraints dataclass — user-configurable
# ---------------------------------------------------------------------------

@dataclass
class AccaConstraints:
    """
    User-defined constraints for bespoke acca building.
    All fields are optional — defaults produce Gary's own selection.
    """
    fold: int = 5                          # number of legs (default 5-fold)
    max_odds: Optional[float] = None       # maximum combined odds (None = no limit)
    min_odds: Optional[float] = None       # minimum combined odds (None = no limit)
    exclude_tiers: List[str] = field(default_factory=list)   # e.g. ["SC2","SC3","EC"]
    include_tiers: List[str] = field(default_factory=list)   # whitelist (empty = all)
    prefer_btts: bool = False              # bias toward BTTS picks
    include_upsets: bool = False           # include upset-flagged picks
    result_types: List[str] = field(default_factory=list)    # e.g. ["H","A"] — empty = all
    max_same_tier: int = 2                 # max picks from same tier in one acca
    acca_type: str = "result"             # result / btts / winner_btts / mixed / upset / safety / value


# ---------------------------------------------------------------------------
# Pick dataclass — one qualifying selection
# ---------------------------------------------------------------------------

@dataclass
class AccaPick:
    home_team: str
    away_team: str
    date: str
    tier: str
    prediction: str          # H / D / A / BTTS
    confidence: float
    dti: float
    chaos_tier: str
    upset_flag: bool
    upset_score: float
    btts_flag: bool
    btts_prob: float
    conviction: str          # HIGH / MED
    selection_label: str     # plain English e.g. "Arsenal to win"
    b365h: Optional[float] = None
    b365d: Optional[float] = None
    b365a: Optional[float] = None
    implied_prob: Optional[float] = None   # bookmaker implied prob for this selection
    edge: Optional[float] = None           # engine confidence - implied prob


# ---------------------------------------------------------------------------
# Acca dataclass — one combination
# ---------------------------------------------------------------------------

@dataclass
class Acca:
    picks: List[AccaPick]
    acca_type: str
    fold: int
    combined_odds: Optional[float]
    decorrelation_score: float    # 1.0 = fully decorrelated, lower = more correlated
    conviction_score: float       # average confidence of picks
    gary_rating: float            # combined score Gary uses to rank accas
    gary_comment: str             # Gary's one-line on this acca


# ---------------------------------------------------------------------------
# Core builder
# ---------------------------------------------------------------------------

class AccaBuilder:
    """
    Two-stage accumulator builder.

    Stage 1: filter predictions to high-conviction picks.
    Stage 2: find the best decorrelated combination.
    """

    def __init__(self, df: pd.DataFrame):
        """
        Args:
            df: predictions dataframe from edgelab_predict.py
                Must contain: HomeTeam, AwayTeam, Date, tier, prediction,
                confidence, dti, chaos_tier, upset_flag, upset_score,
                btts_flag, btts_prob
        """
        self.df = df.copy()
        self._normalise_columns()

    def _normalise_columns(self):
        """Ensure all expected columns exist with safe defaults."""
        defaults = {
            "confidence":   0.0,
            "dti":          0.5,
            "chaos_tier":   "HIGH",
            "upset_flag":   0,
            "upset_score":  0.0,
            "btts_flag":    False,
            "btts_prob":    0.0,
            "draw_score":   0.0,
            "B365H":        np.nan,
            "B365D":        np.nan,
            "B365A":        np.nan,
        }
        for col, default in defaults.items():
            if col not in self.df.columns:
                self.df[col] = default

        # Normalise types
        self.df["upset_flag"]  = self.df["upset_flag"].fillna(0).astype(int)
        self.df["btts_flag"]   = self.df["btts_flag"].fillna(False).astype(bool)
        self.df["confidence"]  = pd.to_numeric(self.df["confidence"], errors="coerce").fillna(0.0)
        self.df["dti"]         = pd.to_numeric(self.df["dti"], errors="coerce").fillna(0.5)
        self.df["btts_prob"]   = pd.to_numeric(self.df["btts_prob"], errors="coerce").fillna(0.0)
        self.df["upset_score"] = pd.to_numeric(self.df["upset_score"], errors="coerce").fillna(0.0)

    # -------------------------------------------------------------------------
    # Stage 1 — filter to qualifying picks
    # -------------------------------------------------------------------------

    def get_picks(self, constraints: Optional[AccaConstraints] = None) -> List[AccaPick]:
        """
        Filter the predictions dataframe to high-conviction qualifying picks.
        Returns a list of AccaPick objects, sorted by confidence descending.
        """
        if constraints is None:
            constraints = AccaConstraints()

        df = self.df.copy()

        # Tier filters
        if constraints.exclude_tiers:
            df = df[~df["tier"].isin(constraints.exclude_tiers)]
        if constraints.include_tiers:
            df = df[df["tier"].isin(constraints.include_tiers)]

        # Result type filter
        if constraints.result_types:
            df = df[df["prediction"].isin(constraints.result_types)]

        # BTTS acca — use btts_flag picks instead of result picks
        if constraints.acca_type == "btts":
            df = df[df["btts_flag"] == True]
            df = df[df["btts_prob"] >= 0.55]
            df = df[df["chaos_tier"].isin(CHAOS_ALLOWED)]
        elif constraints.acca_type == "winner_btts":
            # High confidence H/A win AND btts_flag both true on same match
            df = df[df["prediction"].isin(["H", "A"])]
            df = df[df["confidence"] >= CONF_THRESHOLD]
            df = df[df["btts_flag"] == True]
            df = df[df["btts_prob"] >= 0.55]
            df = df[df["chaos_tier"].isin(CHAOS_ALLOWED)]
            if UPSET_FLAG_BLOCKS and not constraints.include_upsets:
                df = df[df["upset_flag"] == 0]
        elif constraints.acca_type == "upset":
            df = df[df["upset_flag"] == 1]
            df = df[df["chaos_tier"].isin(CHAOS_ALLOWED)]
        else:
            # Standard result acca filters
            df = df[df["confidence"] >= CONF_THRESHOLD]
            df = df[df["chaos_tier"].isin(CHAOS_ALLOWED)]
            if UPSET_FLAG_BLOCKS and not constraints.include_upsets:
                df = df[df["upset_flag"] == 0]
            # Don't include draw predictions in result accas by default
            if constraints.acca_type in ("result", "safety", "value"):
                df = df[df["prediction"] != "D"]
            # Safety: HIGH conviction only
            if constraints.acca_type == "safety":
                df = df[df["confidence"] >= CONVICTION_HIGH]
            # Value: must have odds data so edge can be calculated
            if constraints.acca_type == "value":
                df = df[
                    ((df["prediction"] == "H") & df["B365H"].notna() & (df["B365H"] > 1.0)) |
                    ((df["prediction"] == "A") & df["B365A"].notna() & (df["B365A"] > 1.0)) |
                    ((df["prediction"] == "D") & df["B365D"].notna() & (df["B365D"] > 1.0))
                ]

        if df.empty:
            return []

        picks = []
        for _, row in df.iterrows():
            pred = row["prediction"]
            home = row["HomeTeam"]
            away = row["AwayTeam"]

            # Selection label
            if constraints.acca_type == "btts":
                label = f"{home} vs {away} — BTTS"
                pred_display = "BTTS"
            elif constraints.acca_type == "winner_btts":
                winner = home if pred == "H" else away
                label = f"{winner} to win & BTTS"
                pred_display = pred
            elif pred == "H":
                label = f"{home} to win"
                pred_display = "H"
            elif pred == "A":
                label = f"{away} to win"
                pred_display = "A"
            else:
                label = f"{home} vs {away} — Draw"
                pred_display = "D"

            # Conviction band
            conf = float(row["confidence"])
            if constraints.acca_type == "btts":
                conf = float(row["btts_prob"])

            conviction = "HIGH" if conf >= CONVICTION_HIGH else "MED"

            # Bookmaker implied probability and edge
            b365h = row.get("B365H", np.nan)
            b365d = row.get("B365D", np.nan)
            b365a = row.get("B365A", np.nan)

            implied_prob = None
            edge = None
            if constraints.acca_type in ("btts", "winner_btts"):
                pass  # no direct B365 BTTS odds in current data
            elif pred == "H" and pd.notna(b365h) and b365h > 1.0:
                implied_prob = round(1.0 / b365h, 3)
                edge = round(conf - implied_prob, 3)
            elif pred == "A" and pd.notna(b365a) and b365a > 1.0:
                implied_prob = round(1.0 / b365a, 3)
                edge = round(conf - implied_prob, 3)
            elif pred == "D" and pd.notna(b365d) and b365d > 1.0:
                implied_prob = round(1.0 / b365d, 3)
                edge = round(conf - implied_prob, 3)

            picks.append(AccaPick(
                home_team=home,
                away_team=away,
                date=str(row.get("Date", "")),
                tier=str(row.get("tier", "")),
                prediction=pred_display,
                confidence=conf,
                dti=float(row.get("dti", 0.5)),
                chaos_tier=str(row.get("chaos_tier", "MED")),
                upset_flag=bool(row.get("upset_flag", 0)),
                upset_score=float(row.get("upset_score", 0.0)),
                btts_flag=bool(row.get("btts_flag", False)),
                btts_prob=float(row.get("btts_prob", 0.0)),
                conviction=conviction,
                selection_label=label,
                b365h=float(b365h) if pd.notna(b365h) else None,
                b365d=float(b365d) if pd.notna(b365d) else None,
                b365a=float(b365a) if pd.notna(b365a) else None,
                implied_prob=implied_prob,
                edge=edge,
            ))

        # Sort: HIGH conviction first, then by confidence
        picks.sort(key=lambda p: (0 if p.conviction == "HIGH" else 1, -p.confidence))
        return picks

    # -------------------------------------------------------------------------
    # Stage 2 — evaluate combinations, find best decorrelated set
    # -------------------------------------------------------------------------

    def _decorrelation_score(self, combo: List[AccaPick]) -> float:
        """
        Score a combination of picks for independence (1.0 = fully decorrelated).
        Penalises same-tier same-day pairs and same-country same-result-type pairs.
        """
        score = 1.0
        for i, p1 in enumerate(combo):
            for p2 in combo[i+1:]:
                # Same tier, same date — correlated
                if p1.tier == p2.tier and p1.date == p2.date:
                    score -= SAME_TIER_PENALTY
                # Same country prefix (E, SP, D, I, N, B, SC), same result type
                country1 = p1.tier[:2] if len(p1.tier) >= 2 else p1.tier
                country2 = p2.tier[:2] if len(p2.tier) >= 2 else p2.tier
                if country1 == country2 and p1.prediction == p2.prediction:
                    score -= SAME_COUNTRY_RESULT_PENALTY
        return max(round(score, 3), 0.0)

    def _combined_odds(self, combo: List[AccaPick]) -> Optional[float]:
        """
        Estimate combined decimal odds from bookmaker prices.
        Returns None if any pick is missing odds.
        """
        total = 1.0
        for pick in combo:
            if pick.prediction == "H" and pick.b365h:
                total *= pick.b365h
            elif pick.prediction == "A" and pick.b365a:
                total *= pick.b365a
            elif pick.prediction == "D" and pick.b365d:
                total *= pick.b365d
            else:
                return None  # missing odds — can't compute
        return round(total, 2)

    def _gary_rating(self, combo: List[AccaPick], decor: float, acca_type: str = "result") -> float:
        """
        Gary's composite score for ranking combinations.
        Scoring differs by acca type so that safety/value/result produce distinct picks.

        result  — balanced: confidence + decorrelation + conviction
        safety  — confidence-heavy, penalises any pick without HIGH conviction
        value   — edge-heavy (engine confidence vs bookmaker implied prob)
        btts    — btts_prob weighted
        upset   — upset_score weighted
        """
        avg_conf   = sum(p.confidence for p in combo) / len(combo)
        high_count = sum(1 for p in combo if p.conviction == "HIGH") / len(combo)

        if acca_type == "safety":
            # Safety: lowest odds wins. All picks are already HIGH conviction (filtered upstream).
            # We want the most reliable, shortest-priced combination.
            # Use inverse odds as the primary driver — lower combined odds = higher rating.
            # Falls back to confidence if no odds data available.
            odds = self._combined_odds(combo)
            if odds is not None and odds > 1.0:
                # Normalise: a 5-fold at 2.0 combined is ideal safety. 10.0+ is getting risky.
                # Score = 1 / log(odds+1) so lower odds = higher score.
                import math
                odds_score = round(1.0 / math.log(odds + 1), 4)
                return round((odds_score * 0.6) + (avg_conf * 0.25) + (decor * 0.15), 4)
            else:
                # No odds data — fall back to confidence-heavy
                return round((avg_conf * 0.6) + (high_count * 0.25) + (decor * 0.15), 4)

        if acca_type == "value":
            # Value: reward picks where engine confidence beats bookmaker implied prob.
            edges = [p.edge for p in combo if p.edge is not None]
            avg_edge = sum(edges) / len(edges) if edges else 0.0
            return round((avg_edge * 0.5) + (avg_conf * 0.3) + (decor * 0.2), 4)

        if acca_type == "btts":
            avg_btts = sum(p.btts_prob for p in combo) / len(combo)
            return round((avg_btts * 0.6) + (decor * 0.25) + (avg_conf * 0.15), 4)

        if acca_type == "winner_btts":
            avg_btts = sum(p.btts_prob for p in combo) / len(combo)
            return round((avg_conf * 0.45) + (avg_btts * 0.35) + (decor * 0.20), 4)

        if acca_type == "upset":
            avg_upset = sum(p.upset_score for p in combo) / len(combo)
            return round((avg_upset * 0.6) + (decor * 0.25) + (avg_conf * 0.15), 4)

        # Default: result acca
        return round((avg_conf * 0.6) + (decor * 0.25) + (high_count * 0.15), 4)

    def _gary_comment(self, combo: List[AccaPick], acca_type: str, rating: float) -> str:
        """One-line Gary comment on this acca."""
        high = sum(1 for p in combo if p.conviction == "HIGH")
        tiers = list({p.tier for p in combo})

        if acca_type == "upset":
            return f"Upset special — {len(combo)} independent flags firing. Not a punt, a position."
        if acca_type == "winner_btts":
            return f"{high} confident wins where both teams are expected to score. Goals and results."
        if acca_type == "safety":
            return f"Shortest price I could find. {high}/{len(combo)} bankers. Not exciting. That's the point."
        if rating >= 0.70:
            return f"{high} high-conviction picks, well spread across {len(tiers)} tier(s). This is the one."
        if rating >= 0.60:
            return f"Solid acca. {high} bankers in there. The rest need to behave."
        return f"Decent enough. Gary wouldn't lose sleep over it but he's not dancing either."

    def _check_odds_constraints(
        self,
        odds: Optional[float],
        constraints: AccaConstraints,
    ) -> bool:
        """Return True if odds satisfy user constraints."""
        if odds is None:
            return True  # no odds data — don't filter out
        if constraints.max_odds and odds > constraints.max_odds:
            return False
        if constraints.min_odds and odds < constraints.min_odds:
            return False
        return True

    def _max_same_tier_ok(self, combo: List[AccaPick], max_same: int) -> bool:
        """Return True if no tier appears more than max_same times in combo."""
        from collections import Counter
        counts = Counter(p.tier for p in combo)
        return max(counts.values()) <= max_same

    def build(
        self,
        constraints: Optional[AccaConstraints] = None,
        top_n: int = 3,
    ) -> List[Acca]:
        """
        Build the best accas from the predictions dataframe.

        Args:
            constraints: AccaConstraints — user preferences. None = Gary's defaults.
            top_n:       How many acca options to return (default 3).

        Returns:
            List of Acca objects, best first by gary_rating.
        """
        if constraints is None:
            constraints = AccaConstraints()

        picks = self.get_picks(constraints)

        if not picks:
            logger.info("[AccaBuilder] No qualifying picks found.")
            return []

        fold = constraints.fold

        # If fewer picks than fold, reduce fold to what's available
        if len(picks) < fold:
            logger.info(
                f"[AccaBuilder] Only {len(picks)} picks available — "
                f"reducing fold from {fold} to {len(picks)}"
            )
            fold = len(picks)

        if fold < 2:
            logger.info("[AccaBuilder] Need at least 2 picks for an acca.")
            return []

        # Evaluate all combinations
        # Cap at top 20 picks to keep combinations manageable
        candidate_picks = picks[:20]
        combos = list(itertools.combinations(candidate_picks, fold))

        scored = []
        for combo in combos:
            combo = list(combo)

            # Tier diversity check
            if not self._max_same_tier_ok(combo, constraints.max_same_tier):
                continue

            decor  = self._decorrelation_score(combo)
            odds   = self._combined_odds(combo)
            rating = self._gary_rating(combo, decor, acca_type=constraints.acca_type)

            if not self._check_odds_constraints(odds, constraints):
                continue

            comment = self._gary_comment(combo, constraints.acca_type, rating)
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

        # Safety acca: sort by combined odds ascending (lowest = most reliable)
        # All other types: sort by gary_rating descending
        if constraints.acca_type == "safety":
            has_odds = [a for a in scored if a.combined_odds is not None]
            no_odds  = [a for a in scored if a.combined_odds is None]
            has_odds.sort(key=lambda a: a.combined_odds)
            no_odds.sort(key=lambda a: -a.gary_rating)
            scored = has_odds + no_odds
        else:
            scored.sort(key=lambda a: -a.gary_rating)

        return scored[:top_n]

    # -------------------------------------------------------------------------
    # Output formatting
    # -------------------------------------------------------------------------

    def print_accas(self, accas: List[Acca], label: str = "") -> None:
        """Print formatted acca recommendations to terminal."""
        if label:
            print(f"\n{'='*60}")
            print(f"  {label}")
        print(f"\n{'='*60}")
        print(f"  GARY'S ACCA RECOMMENDATIONS")
        print(f"{'='*60}")

        if not accas:
            print("\n  Nothing clearing Gary's bar today. "
                  "He'd rather tell you nothing than tell you something he doesn't believe.")
            return

        for i, acca in enumerate(accas, 1):
            odds_str = f"  ~{acca.combined_odds:.1f}/1" if acca.combined_odds else ""
            print(f"\n  ── Option {i} — {acca.fold}-fold {ACCA_TYPES.get(acca.acca_type, acca.acca_type)}{odds_str}")
            print(f"     Rating: {acca.gary_rating:.2f}  |  "
                  f"Avg confidence: {acca.conviction_score:.0%}  |  "
                  f"Decorrelation: {acca.decorrelation_score:.2f}")
            print(f"     Gary: \"{acca.gary_comment}\"")
            print()

            for j, pick in enumerate(acca.picks, 1):
                edge_str = f"  edge={pick.edge:+.0%}" if pick.edge is not None else ""
                print(f"     {j}. [{pick.tier}] {pick.date}  {pick.selection_label}")
                print(f"        Conf={pick.confidence:.0%}  DTI={pick.dti:.3f}  "
                      f"{pick.chaos_tier}  [{pick.conviction}]{edge_str}")

        print(f"\n{'='*60}\n")

    def build_all_types(self, fold: int = 5) -> Dict[str, List[Acca]]:
        """
        Build one acca of each type and return as a dict.
        Convenience method for the full matchday briefing.
        """
        results = {}
        for acca_type in ["result", "safety", "value", "winner_btts", "upset", "btts"]:
            constraints = AccaConstraints(fold=fold, acca_type=acca_type)
            accas = self.build(constraints=constraints, top_n=1)
            if accas:
                results[acca_type] = accas
        return results

    def _warn_duplicates(self, all_accas: Dict[str, List["Acca"]]) -> None:
        """
        Check for the same match appearing in more than one acca type.
        Prints a warning for each duplicate so the user can decide whether
        to double-up or diversify.
        """
        match_appearances: Dict[str, List[str]] = {}

        for acca_type, accas in all_accas.items():
            if not accas:
                continue
            for pick in accas[0].picks:
                key = f"{pick.home_team} vs {pick.away_team} ({pick.date})"
                if key not in match_appearances:
                    match_appearances[key] = []
                match_appearances[key].append(acca_type)

        duplicates = {k: v for k, v in match_appearances.items() if len(v) > 1}

        if duplicates:
            print(f"\n  ⚠  DUPLICATE PICKS ACROSS ACCA TYPES:")
            for match, types in duplicates.items():
                type_labels = " + ".join(ACCA_TYPES.get(t, t) for t in types)
                print(f"     {match}  ->  appears in: {type_labels}")
            print(f"     These legs are correlated — consider diversifying.")

    def print_matchday_briefing(self, fold: int = 5) -> None:
        """Print Gary's full matchday acca briefing — all types."""
        print(f"\n{'='*60}")
        print(f"  GARY'S MATCHDAY ACCA BRIEFING")
        print(f"{'='*60}")

        all_accas = self.build_all_types(fold=fold)

        if not all_accas:
            print("\n  Nothing today Gary would put his name to. He's told you. Leave it.")
            return

        for acca_type, accas in all_accas.items():
            if accas:
                acca = accas[0]
                odds_str = f"  ~{acca.combined_odds:.1f}/1" if acca.combined_odds else ""
                print(f"\n  ── {ACCA_TYPES.get(acca_type, acca_type)}{odds_str}")
                print(f"     \"{acca.gary_comment}\"")
                for j, pick in enumerate(acca.picks, 1):
                    print(f"     {j}. {pick.selection_label}  [{pick.tier}]  {pick.confidence:.0%}")

                # Full qualifying picks list for this type
                all_picks = self.get_picks(AccaConstraints(acca_type=acca_type))
                if len(all_picks) > len(acca.picks):
                    print(f"\n     All qualifying picks ({len(all_picks)} total):")
                    for pick in all_picks:
                        edge_str = f"  edge={pick.edge:+.0%}" if pick.edge is not None else ""
                        btts_str = f"  BTTS={pick.btts_prob:.0%}" if acca_type in ("btts", "winner_btts") else ""
                        print(f"       [{pick.conviction}] {pick.date}  {pick.selection_label}  "
                              f"[{pick.tier}]  conf={pick.confidence:.0%}  {pick.chaos_tier}{edge_str}{btts_str}")

        # Duplicate pick warning — flag any match appearing in more than one acca type
        self._warn_duplicates(all_accas)

        print(f"\n{'='*60}\n")


# ---------------------------------------------------------------------------
# Qualifying picks summary — standalone useful output
# ---------------------------------------------------------------------------

def print_qualifying_picks(picks: List[AccaPick]) -> None:
    """Print all picks that cleared Gary's bar, before combination selection."""
    print(f"\n  ── QUALIFYING PICKS ({len(picks)} cleared Gary's bar) ──")
    if not picks:
        print("  None.")
        return

    for pick in picks:
        edge_str = f"  edge={pick.edge:+.0%}" if pick.edge is not None else ""
        print(f"  [{pick.conviction:<4}] [{pick.tier}]  {pick.date}  "
              f"{pick.selection_label:<45}  "
              f"conf={pick.confidence:.0%}  DTI={pick.dti:.3f}  {pick.chaos_tier}{edge_str}")
    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="EdgeLab Acca Builder — Gary's accumulator recommendations"
    )
    parser.add_argument("predictions_csv",
                        help="Path to predictions CSV from edgelab_predict.py")
    parser.add_argument("--fold",      type=int,   default=5,
                        help="Number of legs (default 5)")
    parser.add_argument("--max-odds",  type=float, default=None,
                        help="Maximum combined odds (e.g. 20.0)")
    parser.add_argument("--min-odds",  type=float, default=None,
                        help="Minimum combined odds")
    parser.add_argument("--exclude",   type=str,   default="",
                        help="Comma-separated tiers to exclude e.g. SC2,SC3,EC")
    parser.add_argument("--include",   type=str,   default="",
                        help="Comma-separated tiers to include (whitelist)")
    parser.add_argument("--type",      type=str,   default="result",
                        choices=["result", "btts", "winner_btts", "mixed", "upset", "safety", "value"],
                        help="Acca type (default: result)")
    parser.add_argument("--upsets",    action="store_true",
                        help="Include upset-flagged picks")
    parser.add_argument("--all-types", action="store_true",
                        help="Build one acca of each type — full matchday briefing")
    parser.add_argument("--top",       type=int,   default=3,
                        help="Number of options to show (default 3)")
    parser.add_argument("--picks",     action="store_true",
                        help="Also show all qualifying picks before combinations")
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
        include_upsets=args.upsets,
        acca_type=args.type,
    )

    if args.picks:
        picks = builder.get_picks(constraints)
        print_qualifying_picks(picks)

    accas = builder.build(constraints=constraints, top_n=args.top)
    builder.print_accas(accas)


if __name__ == "__main__":
    main()
