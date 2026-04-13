#!/usr/bin/env python3
"""
edgelab_param_evolution.py
---------------------------
Three-pass full parameter evolution tool with post-match teacher layer.

Extends the draw evolution philosophy (edgelab_draw_evolution.py) to the
ENTIRE engine parameter space — not just draw signals.

WHAT IT DOES:

  Pass 1 — Prediction pass (pre-match only)
    Runs the full engine pipeline on every historical match using current
    evolved params from edgelab_params.json. Logs the engine's call,
    confidence, DTI, and all feature values alongside the actual result.
    Produces the baseline accuracy per tier.

  Pass 2 — Single-param retrospective sweep
    For each engine param, tests a range of values independently against
    the historical dataset. Measures accuracy impact per tier. Identifies
    which params have headroom (individual signal that DPOL missed because
    it was searching sequentially, not holistically).

  Pass 2b — Post-match teacher layer (S33)
    For each historical match, loads post-match data (shots, corners, cards,
    half-time score etc.) as confirmation signals.
    Identifies which pre-match conditions most reliably correlated with each
    outcome type (H/D/A) AND are confirmed by post-match evidence.
    Builds a feature matrix: pre-match conditions → outcome.
    Maps confirmed signals to engine params.
    Teacher-confirmed params are merged into Pass 3 candidates — giving
    combination testing better-informed starting points than Pass 2 alone.
    This is exactly how edgelab_draw_evolution.py works for draws,
    extended to the full param space across all outcomes.

  Pass 3 — Combination testing (better-informed candidates)
    Takes movers from Pass 2 + teacher-confirmed params from Pass 2b.
    Tests all 2-param and 3-param combinations simultaneously.
    Maps interaction effects. This is what DPOL cannot do — it optimises
    one param at a time and gets stuck in local optima.

PARAM SPACE:
    Core:      w_form, w_gd, home_adv, dti_edge_scale, dti_ha_scale
    Draw core: draw_margin, coin_dti_thresh
    Draw pull: draw_pull, dti_draw_lock  (currently disabled — reintroduced)
    Draw intel: w_draw_odds, w_draw_tendency, w_h2h_draw, draw_score_thresh
                w_xg_draw, composite_draw_boost
    Score:     w_score_margin, w_btts
    (Phase 1/2 signals excluded — not ready to wire)

INTEGRITY:
    Post-match data is NEVER used in Pass 1 or Pass 2 predictions.
    Pass 2b uses post-match data ONLY as retrospective confirmation of
    pre-match signals — never to generate predictions directly.
    Results are suggestions — not direct deployment. Feed into DPOL.

Usage:
    python edgelab_param_evolution.py --data history/
    python edgelab_param_evolution.py --data history/ --tier E0
    python edgelab_param_evolution.py --data history/ --pass 2
    python edgelab_param_evolution.py --data history/ --output param_profile.json
    python edgelab_param_evolution.py --data history/ --top 5
"""

import argparse
import json
import sys
import warnings
from dataclasses import dataclass, asdict
from itertools import combinations
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")

sys.path.insert(0, ".")

from edgelab_engine import (
    EngineParams,
    load_all_csvs,
    compute_form,
    compute_goal_diff,
    compute_dti,
    compute_team_draw_tendency,
    compute_h2h,
    compute_score_prediction,
    compute_odds_draw_prob,
    predict_dataframe,
)
from edgelab_config import load_params

# ---------------------------------------------------------------------------
# Full param space — what we test
# ---------------------------------------------------------------------------

# Each entry: (param_name, [values_to_test], description)
# Values are absolute, not relative — we test specific points in param space.
# draw_pull and dti_draw_lock are REINTRODUCED here after being disabled.

PARAM_CANDIDATES = [
    # Core params — test a band around evolved values
    ("w_form",            [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2],
                          "Form rolling window weight"),
    ("w_gd",              [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.5],
                          "Goal difference weight"),
    ("home_adv",          [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5],
                          "Home advantage bonus"),
    ("dti_edge_scale",    [0.2, 0.3, 0.35, 0.4, 0.45, 0.5, 0.6],
                          "DTI dampening of form/GD"),
    ("dti_ha_scale",      [0.3, 0.4, 0.45, 0.5, 0.55, 0.6, 0.7],
                          "DTI dampening of home advantage"),

    # Draw core
    ("draw_margin",       [0.08, 0.10, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.18],
                          "Score margin to call draw"),
    ("coin_dti_thresh",   [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85],
                          "DTI threshold for coin-flip"),

    # draw_pull — REINTRODUCED. Currently 0.0 everywhere. Tests if parity
    # gravity helps when teams are genuinely evenly matched.
    ("draw_pull",         [0.0, 0.05, 0.08, 0.10, 0.12, 0.15, 0.18, 0.20],
                          "Parity gravity toward draw (reintroduced)"),

    # dti_draw_lock — REINTRODUCED. Currently 999.0 (disabled). Tests if
    # locking high-DTI + parity matches as draws improves accuracy.
    ("dti_draw_lock",     [999.0, 0.9, 0.85, 0.80, 0.75, 0.70, 0.65],
                          "High DTI + parity draw lock (reintroduced)"),

    # Draw intelligence
    ("w_draw_odds",       [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30],
                          "Bookmaker draw probability weight"),
    ("w_draw_tendency",   [0.0, 0.05, 0.10, 0.15, 0.20],
                          "Team rolling draw rate weight"),
    ("w_h2h_draw",        [0.0, 0.05, 0.10, 0.15, 0.20],
                          "H2H draw rate weight"),
    ("draw_score_thresh", [0.35, 0.40, 0.45, 0.50, 0.55, 0.60],
                          "Combined draw score threshold"),
    ("w_xg_draw",         [0.0, 0.05, 0.10, 0.15, 0.20, 0.25],
                          "Expected goals as draw signal"),
    ("composite_draw_boost", [0.0, 0.05, 0.10, 0.15, 0.20],
                          "Composite draw gate boost"),

    # Score prediction
    ("w_score_margin",    [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30],
                          "Predicted goal margin reinforcement"),

    # w_btts — REINTRODUCED. Tests whether BTTS probability in combination
    # with draw params adds signal that DPOL couldn't find alone.
    ("w_btts",            [0.0, 0.05, 0.10, 0.15, 0.20],
                          "BTTS probability draw contribution (reintroduced)"),
]

PARAM_NAMES = [p[0] for p in PARAM_CANDIDATES]

# Minimum accuracy delta to flag a param as a mover in Pass 2
PASS2_MOVER_THRESHOLD = 0.003   # +0.3pp or better
# Top N single-param movers to take into Pass 3 combination testing
PASS3_TOP_N_DEFAULT = 6
# Minimum matches for a combination result to be reportable
PASS3_MIN_MATCHES = 200
# Minimum accuracy improvement to report a combination
PASS3_MIN_IMPROVEMENT = 0.002   # +0.2pp


# ---------------------------------------------------------------------------
# Pipeline helpers
# ---------------------------------------------------------------------------

def run_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """Run full pre-match pipeline. Returns enriched dataframe."""
    df = compute_form(df)
    df = compute_goal_diff(df)
    df = compute_dti(df)
    df = compute_team_draw_tendency(df)
    df = compute_h2h(df)
    df = compute_score_prediction(df)
    if "B365D" in df.columns:
        df = compute_odds_draw_prob(df)
    else:
        df["odds_draw_prob"] = 0.26
    return df


def params_from_dict(base: EngineParams, overrides: dict) -> EngineParams:
    """Return a copy of base EngineParams with overrides applied."""
    d = asdict(base)
    d.update(overrides)
    return EngineParams(**d)


def score_params(df: pd.DataFrame, params: EngineParams) -> Tuple[float, int]:
    """
    Run predictions on df with given params.
    Returns (accuracy, n_matches).
    """
    try:
        result = predict_dataframe(df, params)
        if "FTR" not in result.columns or "prediction" not in result.columns:
            return 0.0, 0
        valid = result.dropna(subset=["FTR", "prediction"])
        if len(valid) == 0:
            return 0.0, 0
        correct = (valid["prediction"] == valid["FTR"]).sum()
        return float(correct / len(valid)), len(valid)
    except Exception:
        return 0.0, 0


def load_evolved_params(tier: str) -> EngineParams:
    """
    Load evolved params from edgelab_params.json for a tier.
    Falls back to EngineParams defaults if not found.
    """
    try:
        lp = load_params(tier)
        if lp is None:
            return EngineParams()
        # Convert LeagueParams to EngineParams field by field
        ep = EngineParams(
            w_form=lp.w_form,
            w_gd=lp.w_gd,
            home_adv=lp.home_adv,
            dti_edge_scale=lp.dti_edge_scale,
            dti_ha_scale=lp.dti_ha_scale,
            draw_margin=lp.draw_margin,
            coin_dti_thresh=lp.coin_dti_thresh,
            draw_pull=getattr(lp, "draw_pull", 0.0),
            dti_draw_lock=getattr(lp, "dti_draw_lock", 999.0),
            w_draw_odds=getattr(lp, "w_draw_odds", 0.0),
            w_draw_tendency=getattr(lp, "w_draw_tendency", 0.0),
            w_h2h_draw=getattr(lp, "w_h2h_draw", 0.0),
            draw_score_thresh=getattr(lp, "draw_score_thresh", 0.55),
            w_score_margin=getattr(lp, "w_score_margin", 0.0),
            w_btts=getattr(lp, "w_btts", 0.0),
            w_xg_draw=getattr(lp, "w_xg_draw", 0.0),
            composite_draw_boost=getattr(lp, "composite_draw_boost", 0.0),
        )
        return ep
    except Exception:
        return EngineParams()


# ---------------------------------------------------------------------------
# Pass 1 — Baseline
# ---------------------------------------------------------------------------

def pass1_baseline(
    processed_tiers: Dict[str, pd.DataFrame],
    evolved_params: Dict[str, EngineParams],
) -> Dict[str, dict]:
    """
    Run predictions with current evolved params.
    Returns per-tier baseline accuracy.
    """
    print(f"\n  PASS 1 — Baseline accuracy with current evolved params")
    print(f"  {'─'*60}")

    results = {}
    for tier, df in processed_tiers.items():
        params = evolved_params[tier]
        acc, n = score_params(df, params)
        results[tier] = {"accuracy": acc, "n": n, "params": asdict(params)}
        print(f"  [{tier:<4}] {acc:.1%}  ({n:,} matches)")

    overall_acc = np.mean([r["accuracy"] for r in results.values()])
    print(f"\n  Overall baseline: {overall_acc:.1%}")
    return results


# ---------------------------------------------------------------------------
# Pass 2 — Single-param sweep
# ---------------------------------------------------------------------------

def pass2_single_param_sweep(
    processed_tiers: Dict[str, pd.DataFrame],
    evolved_params: Dict[str, EngineParams],
    baseline: Dict[str, dict],
    target_tiers: Optional[List[str]] = None,
) -> Dict[str, dict]:
    """
    For each param in PARAM_CANDIDATES, test each value independently
    against current evolved params. Report accuracy delta vs baseline.

    Returns dict of {tier: {param: {best_value, best_acc, delta, all_results}}}
    """
    print(f"\n  PASS 2 — Single-param sweep ({len(PARAM_CANDIDATES)} params)")
    print(f"  {'─'*60}")

    tiers = target_tiers or list(processed_tiers.keys())
    tier_results = {tier: {} for tier in tiers}

    for param_name, values, description in PARAM_CANDIDATES:
        print(f"\n  [{param_name}] {description}")
        print(f"  Testing {len(values)} values across {len(tiers)} tiers...")

        for tier in tiers:
            if tier not in processed_tiers:
                continue
            df = processed_tiers[tier]
            base_params = evolved_params[tier]
            baseline_acc = baseline[tier]["accuracy"]

            param_results = []
            for val in values:
                test_params = params_from_dict(base_params, {param_name: val})
                acc, n = score_params(df, test_params)
                delta = acc - baseline_acc
                param_results.append({
                    "value": val,
                    "accuracy": round(acc, 4),
                    "delta": round(delta, 4),
                    "n": n,
                })

            # Best value
            best = max(param_results, key=lambda x: x["accuracy"])
            tier_results[tier][param_name] = {
                "best_value": best["value"],
                "best_acc": best["accuracy"],
                "delta": best["delta"],
                "baseline_acc": round(baseline_acc, 4),
                "description": description,
                "all_results": param_results,
            }

            delta_str = f"+{best['delta']:.1%}" if best["delta"] >= 0 else f"{best['delta']:.1%}"
            flag = " ◄ MOVER" if best["delta"] >= PASS2_MOVER_THRESHOLD else ""
            print(f"    {tier:<5}  best={best['value']:<8}  acc={best['accuracy']:.1%}  "
                  f"delta={delta_str}{flag}")

    return tier_results


def summarise_pass2(
    pass2_results: Dict[str, dict],
    top_n: int = PASS3_TOP_N_DEFAULT,
) -> Dict[str, List[str]]:
    """
    Identify top N movers per tier from Pass 2.
    Returns {tier: [param_name, ...]} — the candidates to test in Pass 3.
    """
    print(f"\n  PASS 2 SUMMARY — Top movers per tier (threshold: +{PASS2_MOVER_THRESHOLD:.1%})")
    print(f"  {'─'*60}")

    tier_movers = {}
    for tier, params in pass2_results.items():
        movers = [
            (pname, pdata["delta"], pdata["best_value"], pdata["best_acc"])
            for pname, pdata in params.items()
            if pdata["delta"] >= PASS2_MOVER_THRESHOLD
        ]
        movers.sort(key=lambda x: x[1], reverse=True)
        top = movers[:top_n]
        tier_movers[tier] = [m[0] for m in top]

        if top:
            print(f"\n  {tier} — {len(top)} movers:")
            for pname, delta, best_val, best_acc in top:
                print(f"    {pname:<25}  delta=+{delta:.1%}  best_val={best_val}  acc={best_acc:.1%}")
        else:
            print(f"\n  {tier} — no movers above threshold")

    return tier_movers


# ---------------------------------------------------------------------------
# Pass 2b — Post-match teacher layer
# ---------------------------------------------------------------------------

# Pre-match signals we analyse for outcome correlation
TEACHER_PRE_MATCH = [
    "home_form", "away_form", "home_gd", "away_gd", "dti",
    "home_draw_rate", "away_draw_rate", "h2h_draw_rate", "h2h_home_edge",
    "odds_draw_prob", "pred_home_goals", "pred_away_goals", "pred_margin",
    "btts_prob",
]

# Derived pre-match signals
TEACHER_DERIVED = [
    "form_parity",           # how evenly matched (1 = identical form)
    "gd_parity",             # GD closeness
    "form_edge",             # home_form - away_form (directional)
    "gd_edge",               # home_gd - away_gd (directional)
    "expected_goals_total",  # pred_home + pred_away
    "expected_goals_diff",   # abs(pred_home - pred_away)
]

# Post-match confirmation signals (teacher only — never used in predictions)
TEACHER_POST_MATCH = [
    "HTHG", "HTAG",   # half-time goals
    "HS", "AS",        # shots
    "HST", "AST",      # shots on target
    "HC", "AC",        # corners
    "HF", "AF",        # fouls
    "HR", "AR",        # red cards
]

# Minimum lift to flag a pre-match signal as informative for an outcome
TEACHER_LIFT_THRESHOLD = 1.08
# Minimum p-value significance
TEACHER_P_THRESHOLD = 0.05
# Minimum matches in a bin to count
TEACHER_MIN_BIN = 100


def _add_teacher_derived(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived pre-match signals used by the teacher pass."""
    df = df.copy()
    df["form_parity"] = 1.0 - (df["home_form"] - df["away_form"]).abs().clip(0, 1)
    df["gd_parity"]   = (1.0 - ((df["home_gd"] - df["away_gd"]).abs() / 3.0)).clip(0, 1)
    df["form_edge"]   = df["home_form"] - df["away_form"]
    df["gd_edge"]     = df["home_gd"] - df["away_gd"]
    if "pred_home_goals" in df.columns and "pred_away_goals" in df.columns:
        df["expected_goals_total"] = df["pred_home_goals"] + df["pred_away_goals"]
        df["expected_goals_diff"]  = (df["pred_home_goals"] - df["pred_away_goals"]).abs()
    return df


def _analyse_signal_for_outcome(
    df: pd.DataFrame,
    signal: str,
    outcome: str,
    n_bins: int = 5,
) -> Optional[dict]:
    """
    For a given pre-match signal and outcome (H/D/A), measure outcome rate
    across quantile bins. Returns lift stats and best threshold band.
    """
    target_col = f"actual_{outcome}"
    if signal not in df.columns or target_col not in df.columns:
        return None

    df_clean = df[[signal, target_col]].dropna()
    if len(df_clean) < 200:
        return None

    overall_rate = df_clean[target_col].mean()
    if overall_rate == 0:
        return None

    try:
        df_clean = df_clean.copy()
        df_clean["bin"] = pd.qcut(df_clean[signal], q=n_bins, duplicates="drop")
    except Exception:
        return None

    bin_stats = []
    for bin_label, group in df_clean.groupby("bin", observed=True):
        n = len(group)
        hits = group[target_col].sum()
        rate = hits / n if n > 0 else 0
        lift = rate / overall_rate if overall_rate > 0 else 1
        bin_stats.append({
            "bin": str(bin_label),
            "n": int(n),
            "rate": round(float(rate), 4),
            "lift": round(float(lift), 4),
        })

    if not bin_stats:
        return None

    try:
        corr, p_val = stats.pearsonr(df_clean[signal], df_clean[target_col])
    except Exception:
        return None

    best_bin = max(
        (b for b in bin_stats if b["n"] >= TEACHER_MIN_BIN),
        key=lambda x: x["lift"],
        default=None,
    )

    return {
        "signal": signal,
        "outcome": outcome,
        "overall_rate": round(float(overall_rate), 4),
        "correlation": round(float(corr), 4),
        "p_value": round(float(p_val), 4),
        "significant": bool(p_val < TEACHER_P_THRESHOLD),
        "max_lift": round(max(b["lift"] for b in bin_stats), 4),
        "best_bin": best_bin,
        "bins": bin_stats,
    }


def _postmatch_confirmation(
    df_outcome: pd.DataFrame,
    signal: str,
) -> dict:
    """
    For matches with a given outcome, check whether post-match data confirms
    the pre-match signal was capturing genuine pattern rather than noise.

    E.g. for home wins: do high home_form matches show more dominant shot
    counts post-match? If yes, the signal was real. If no, it was luck.

    Returns correlation stats between pre-match signal and post-match dominance.
    """
    results = {}
    available = [c for c in TEACHER_POST_MATCH if c in df_outcome.columns]
    if not available or signal not in df_outcome.columns:
        return results

    df_clean = df_outcome[[signal] + available].dropna(subset=[signal])

    # Half-time score direction — confirms who was dominant from kick-off
    if "HTHG" in df_clean.columns and "HTAG" in df_clean.columns:
        df_clean = df_clean.copy()
        df_clean["ht_margin"] = df_clean["HTHG"] - df_clean["HTAG"]
        try:
            corr, p = stats.pearsonr(
                df_clean[signal].fillna(0),
                df_clean["ht_margin"].fillna(0)
            )
            results["ht_margin_corr"] = round(float(corr), 4)
            results["ht_margin_p"] = round(float(p), 4)
        except Exception:
            pass

    # Shot dominance — home shots - away shots
    if "HS" in df_clean.columns and "AS" in df_clean.columns:
        df_clean = df_clean.copy()
        df_clean["shot_dominance"] = df_clean["HS"] - df_clean["AS"]
        try:
            corr, p = stats.pearsonr(
                df_clean[signal].fillna(0),
                df_clean["shot_dominance"].fillna(0)
            )
            results["shot_dominance_corr"] = round(float(corr), 4)
            results["shot_dominance_p"] = round(float(p), 4)
        except Exception:
            pass

    # Shot on target dominance — cleaner signal
    if "HST" in df_clean.columns and "AST" in df_clean.columns:
        df_clean = df_clean.copy()
        df_clean["sot_dominance"] = df_clean["HST"] - df_clean["AST"]
        try:
            corr, p = stats.pearsonr(
                df_clean[signal].fillna(0),
                df_clean["sot_dominance"].fillna(0)
            )
            results["sot_dominance_corr"] = round(float(corr), 4)
            results["sot_dominance_p"] = round(float(p), 4)
        except Exception:
            pass

    return results


def _map_signal_to_params(signal: str, outcome: str) -> List[str]:
    """
    Map a pre-match signal to the engine params it most directly influences.
    Used to tell Pass 3 which params the teacher evidence supports.
    """
    mapping = {
        "home_form":           ["w_form"],
        "away_form":           ["w_form"],
        "form_edge":           ["w_form"],
        "form_parity":         ["w_form", "draw_margin"],
        "home_gd":             ["w_gd"],
        "away_gd":             ["w_gd"],
        "gd_edge":             ["w_gd"],
        "gd_parity":           ["w_gd", "draw_margin"],
        "dti":                 ["dti_edge_scale", "dti_ha_scale", "coin_dti_thresh"],
        "odds_draw_prob":      ["w_draw_odds"],
        "home_draw_rate":      ["w_draw_tendency"],
        "away_draw_rate":      ["w_draw_tendency"],
        "h2h_draw_rate":       ["w_h2h_draw"],
        "h2h_home_edge":       ["home_adv"],
        "pred_margin":         ["w_score_margin"],
        "expected_goals_diff": ["w_score_margin"],
        "expected_goals_total":["w_xg_draw", "composite_draw_boost"],
        "btts_prob":           ["w_btts"],
        "draw_tendency":       ["w_draw_tendency", "draw_score_thresh"],
    }
    return mapping.get(signal, [])


def pass2b_teacher(
    processed_tiers: Dict[str, pd.DataFrame],
    baseline: Dict[str, dict],
    tier_movers: Dict[str, List[str]],
) -> Dict[str, dict]:
    """
    Pass 2b — Post-match teacher layer.

    For each tier and each outcome (H/D/A):
    1. Analyses which pre-match signals correlate most strongly with that outcome
    2. Validates those signals against post-match data (shots, HT score etc.)
    3. Maps confirmed signals back to engine params
    4. Returns teacher-informed param candidates to merge into Pass 3

    Output: {tier: {"H": [...params], "D": [...params], "A": [...params],
                    "teacher_signals": {...}, "confirmed_params": [...]}}
    """
    print(f"\n  PASS 2b — Post-match teacher layer")
    print(f"  {'─'*60}")
    print(f"  Philosophy: post-match data as confirmation signal.")
    print(f"  Pre-match signals with genuine outcome correlation → param candidates for Pass 3.")
    print(f"  Lift threshold: {TEACHER_LIFT_THRESHOLD}x  |  Significance: p<{TEACHER_P_THRESHOLD}")

    all_signals = TEACHER_PRE_MATCH + TEACHER_DERIVED
    results = {}

    for tier, df in processed_tiers.items():
        print(f"\n  [{tier}] {len(df):,} matches")

        # Add derived signals
        df_t = _add_teacher_derived(df)

        # Label outcomes
        df_t = df_t.copy()
        df_t["actual_H"] = (df_t["FTR"] == "H").astype(int)
        df_t["actual_D"] = (df_t["FTR"] == "D").astype(int)
        df_t["actual_A"] = (df_t["FTR"] == "A").astype(int)

        tier_result = {
            "baseline_acc": baseline[tier]["accuracy"],
            "teacher_signals": {},
            "confirmed_params": [],
            "outcome_candidates": {"H": [], "D": [], "A": []},
        }

        # Check if post-match data is available for this tier
        pm_available = [c for c in TEACHER_POST_MATCH if c in df_t.columns]
        has_postmatch = len(pm_available) >= 4  # need at least HT + shots
        if not has_postmatch:
            print(f"    ⚠  Limited post-match columns ({len(pm_available)}) — teacher pass partial")

        for outcome in ["H", "D", "A"]:
            df_outcome = df_t[df_t[f"actual_{outcome}"] == 1].copy()
            n_outcome = len(df_outcome)
            outcome_rate = n_outcome / len(df_t)

            confirmed_signals = []

            for signal in all_signals:
                result = _analyse_signal_for_outcome(df_t, signal, outcome)
                if result is None:
                    continue

                if not result["significant"] or result["max_lift"] < TEACHER_LIFT_THRESHOLD:
                    continue

                # Post-match confirmation
                if has_postmatch:
                    confirmation = _postmatch_confirmation(df_outcome, signal)
                    result["postmatch_confirmation"] = confirmation

                    # Is the post-match evidence consistent with the pre-match signal?
                    # For H outcome: home dominance in shots/HT should correlate positively
                    # For A outcome: away dominance should correlate positively
                    # For D outcome: parity signals should hold
                    confirmed = False
                    if outcome == "H":
                        ht_c = confirmation.get("ht_margin_corr", 0)
                        sh_c = confirmation.get("shot_dominance_corr", 0)
                        confirmed = (ht_c > 0.05 or sh_c > 0.05)
                    elif outcome == "A":
                        ht_c = confirmation.get("ht_margin_corr", 0)
                        sh_c = confirmation.get("shot_dominance_corr", 0)
                        confirmed = (ht_c < -0.05 or sh_c < -0.05)
                    elif outcome == "D":
                        # Draw: parity signals should correlate with shot parity
                        sot_c = confirmation.get("sot_dominance_corr", 0)
                        confirmed = abs(sot_c) < 0.15  # low dominance = genuine draw
                    result["postmatch_confirmed"] = confirmed
                else:
                    result["postmatch_confirmed"] = None  # can't confirm, still flag

                confirmed_signals.append(result)

            # Map confirmed signals to params
            outcome_params = []
            for sig_result in confirmed_signals:
                if sig_result.get("postmatch_confirmed") is not False:
                    mapped = _map_signal_to_params(sig_result["signal"], outcome)
                    outcome_params.extend(mapped)

            outcome_params = list(dict.fromkeys(outcome_params))  # dedupe, preserve order
            tier_result["outcome_candidates"][outcome] = outcome_params
            tier_result["teacher_signals"][outcome] = confirmed_signals

            n_confirmed = sum(1 for s in confirmed_signals if s.get("postmatch_confirmed") is not False)
            print(f"    {outcome}: {n_outcome:,} matches ({outcome_rate:.1%}) — "
                  f"{len(confirmed_signals)} signals with lift, "
                  f"{n_confirmed} post-match confirmed → params: {outcome_params}")

        # Aggregate confirmed params across all outcomes — these are the
        # teacher's recommendations for Pass 3 combination testing
        all_teacher_params = []
        for outcome in ["H", "D", "A"]:
            all_teacher_params.extend(tier_result["outcome_candidates"][outcome])
        # Dedupe but weight by frequency — params confirmed for multiple outcomes score higher
        from collections import Counter
        param_counts = Counter(all_teacher_params)
        # Sort by count descending — most cross-outcome confirmed params first
        confirmed = [p for p, _ in param_counts.most_common()]
        tier_result["confirmed_params"] = confirmed

        if confirmed:
            print(f"    Teacher-confirmed params for Pass 3: {confirmed}")
        else:
            print(f"    No params confirmed by teacher — Pass 3 uses Pass 2 movers only")

        results[tier] = tier_result

    # Summary
    print(f"\n  PASS 2b SUMMARY")
    print(f"  {'─'*60}")
    tiers_with_teacher = [t for t, r in results.items() if r["confirmed_params"]]
    print(f"  Tiers with teacher-confirmed params: {len(tiers_with_teacher)}/{len(results)}")
    for tier in tiers_with_teacher:
        print(f"    {tier}: {results[tier]['confirmed_params']}")

    return results


# ---------------------------------------------------------------------------
# Pass 3 — Combination testing
# ---------------------------------------------------------------------------

def pass3_combinations(
    processed_tiers: Dict[str, pd.DataFrame],
    evolved_params: Dict[str, EngineParams],
    baseline: Dict[str, dict],
    pass2_results: Dict[str, dict],
    tier_movers: Dict[str, List[str]],
    target_tiers: Optional[List[str]] = None,
    teacher_results: Optional[Dict[str, dict]] = None,
) -> Dict[str, dict]:
    """
    Test all 2-param and 3-param combinations of the top movers per tier.
    For each combo, uses the best values found in Pass 2 for each param.

    Pass 2b teacher results (if provided) are merged in:
    - Teacher-confirmed params that aren't already in Pass 2 movers are added
    - Teacher params with no Pass 2 best value use their midpoint from PARAM_CANDIDATES
    - This gives Pass 3 better-informed candidates than Pass 2 alone

    This maps interaction effects — where params that look weak alone
    are strong when they fire together.
    """
    print(f"\n  PASS 3 — Combination testing")
    if teacher_results:
        print(f"  Teacher layer active — merging Pass 2b candidates")
    print(f"  {'─'*60}")

    tiers = target_tiers or list(processed_tiers.keys())
    tier_combo_results = {}

    for tier in tiers:
        if tier not in processed_tiers or tier not in tier_movers:
            continue

        movers = list(tier_movers[tier])  # Pass 2 movers

        # Merge teacher candidates — add any teacher-confirmed params not already present
        if teacher_results and tier in teacher_results:
            teacher_params = teacher_results[tier].get("confirmed_params", [])
            added = []
            for tp in teacher_params:
                if tp not in movers and tp in PARAM_NAMES:
                    movers.append(tp)
                    added.append(tp)
            if added:
                print(f"\n  {tier} — teacher added {len(added)} params: {added}")

        if len(movers) < 2:
            print(f"\n  {tier} — fewer than 2 candidates, skipping combinations")
            tier_combo_results[tier] = {
                "baseline_acc": round(baseline[tier]["accuracy"], 4),
                "combinations": [], "best": None, "n_tested": 0, "n_improving": 0,
            }
            continue

        df = processed_tiers[tier]
        base_params = evolved_params[tier]
        baseline_acc = baseline[tier]["accuracy"]

        # Best value per param: Pass 2 result if available, else midpoint from PARAM_CANDIDATES
        param_midpoints = {
            p[0]: p[1][len(p[1]) // 2]
            for p in PARAM_CANDIDATES
        }
        best_values = {}
        for pname in movers:
            if pname in pass2_results.get(tier, {}) and tier in pass2_results:
                best_values[pname] = pass2_results[tier][pname]["best_value"]
            elif pname in param_midpoints:
                best_values[pname] = param_midpoints[pname]

        n_pairs = len(list(combinations(movers, 2)))
        n_triples = len(list(combinations(movers, 3))) if len(movers) >= 3 else 0
        total = n_pairs + n_triples
        print(f"\n  {tier} — testing {len(movers)} movers: {n_pairs} pairs"
              f" + {n_triples} triples = {total} combinations")

        combo_results = []

        for size in [2, 3]:
            if size == 3 and len(movers) < 3:
                continue
            for combo in combinations(movers, size):
                overrides = {p: best_values[p] for p in combo if p in best_values}
                if not overrides:
                    continue
                test_params = params_from_dict(base_params, overrides)
                acc, n = score_params(df, test_params)
                delta = acc - baseline_acc
                improvement = delta >= PASS3_MIN_IMPROVEMENT

                combo_results.append({
                    "params": list(combo),
                    "values": overrides,
                    "accuracy": round(acc, 4),
                    "delta": round(delta, 4),
                    "n": n,
                    "improvement": improvement,
                })

        # Sort by accuracy descending
        combo_results.sort(key=lambda x: x["accuracy"], reverse=True)

        # Print top results
        improving = [c for c in combo_results if c["improvement"]]
        print(f"  {len(improving)} combinations improve on baseline ({baseline_acc:.1%})")

        if improving:
            print(f"\n  Top combinations (delta >= +{PASS3_MIN_IMPROVEMENT:.1%}):")
            print(f"  {'Params':<50} {'Acc':>6} {'Delta':>8}")
            print(f"  {'─'*50} {'─'*6} {'─'*8}")
            for c in improving[:15]:
                param_str = " + ".join(c["params"])
                if len(param_str) > 49:
                    param_str = param_str[:46] + "..."
                delta_str = f"+{c['delta']:.1%}"
                print(f"  {param_str:<50} {c['accuracy']:.1%} {delta_str:>8}")

            best = improving[0]
            print(f"\n  BEST COMBINATION FOR {tier}:")
            print(f"    Params: {' + '.join(best['params'])}")
            for p, v in best["values"].items():
                print(f"    {p} = {v}")
            print(f"    Accuracy: {best['accuracy']:.1%}  (baseline: {baseline_acc:.1%}  "
                  f"delta: +{best['delta']:.1%})")
        else:
            print(f"  No combinations improved on baseline.")
            # Still show the best attempt
            if combo_results:
                best_attempt = combo_results[0]
                print(f"  Best attempt: {' + '.join(best_attempt['params'])}  "
                      f"acc={best_attempt['accuracy']:.1%}  delta={best_attempt['delta']:.1%}")

        tier_combo_results[tier] = {
            "baseline_acc": round(baseline_acc, 4),
            "combinations": combo_results[:30],  # save top 30
            "best": improving[0] if improving else None,
            "n_tested": total,
            "n_improving": len(improving),
        }

    return tier_combo_results


# ---------------------------------------------------------------------------
# Final summary + JSON output
# ---------------------------------------------------------------------------

def print_final_summary(
    baseline: Dict[str, dict],
    tier_combo_results: Dict[str, dict],
):
    """Print the overall summary across all tiers."""
    print(f"\n{'='*65}")
    print(f"  THREE-PASS PARAM EVOLUTION — FINAL SUMMARY")
    print(f"{'='*65}")

    tiers_with_gains = []
    for tier, result in tier_combo_results.items():
        best = result.get("best")
        if best:
            tiers_with_gains.append((tier, best["delta"], best))

    tiers_with_gains.sort(key=lambda x: x[1], reverse=True)

    if tiers_with_gains:
        print(f"\n  TIERS WITH COMBINATION GAINS ({len(tiers_with_gains)} tiers):")
        print(f"  {'Tier':<6} {'Baseline':>9} {'Best':>9} {'Delta':>8}  Params")
        print(f"  {'─'*6} {'─'*9} {'─'*9} {'─'*8}  {'─'*40}")
        for tier, delta, best in tiers_with_gains:
            base_acc = baseline[tier]["accuracy"]
            param_str = " + ".join(best["params"])
            print(f"  {tier:<6} {base_acc:>9.1%} {best['accuracy']:>9.1%} "
                  f"+{delta:>7.1%}  {param_str}")
    else:
        print(f"\n  No tiers found combination gains above +{PASS3_MIN_IMPROVEMENT:.1%} threshold.")
        print(f"  Consider lowering --min-improvement or expanding param ranges.")

    print(f"\n  NEXT STEPS:")
    print(f"    1. Review combinations above — especially any involving draw_pull,")
    print(f"       dti_draw_lock, or w_btts (reintroduced params).")
    print(f"    2. For tiers with gains: seed these param combos into edgelab_gridsearch.py")
    print(f"       and run with the standard gate (draw +5pp AND overall within -0.5%).")
    print(f"    3. Any combo that survives gridsearch gate → seed into next DPOL run.")
    print(f"    4. DPOL with a better starting point should hold the combination intact.")


def build_json_output(
    baseline: Dict[str, dict],
    pass2_results: Dict[str, dict],
    tier_movers: Dict[str, List[str]],
    tier_combo_results: Dict[str, dict],
    teacher_results: Optional[Dict[str, dict]] = None,
) -> dict:
    """Build the full JSON output."""
    output = {
        "meta": {
            "tool": "edgelab_param_evolution",
            "pass2_mover_threshold": PASS2_MOVER_THRESHOLD,
            "pass3_min_improvement": PASS3_MIN_IMPROVEMENT,
            "params_tested": PARAM_NAMES,
            "reintroduced_params": ["draw_pull", "dti_draw_lock", "w_btts"],
            "pass2b_teacher_layer": True,
        },
        "baseline": {
            tier: {
                "accuracy": data["accuracy"],
                "n": data["n"],
            }
            for tier, data in baseline.items()
        },
        "pass2_movers": tier_movers,
        "pass2_best_values": {
            tier: {
                pname: pdata["best_value"]
                for pname, pdata in params.items()
                if pdata["delta"] >= PASS2_MOVER_THRESHOLD
            }
            for tier, params in pass2_results.items()
        },
        "pass2b_teacher": {
            tier: {
                "confirmed_params": data["confirmed_params"],
                "outcome_candidates": data["outcome_candidates"],
            }
            for tier, data in (teacher_results or {}).items()
        },
        "pass3_results": {
            tier: {
                "baseline_acc": result["baseline_acc"],
                "n_tested": result["n_tested"],
                "n_improving": result["n_improving"],
                "best": result["best"],
                "top_combinations": result["combinations"][:10],
            }
            for tier, result in tier_combo_results.items()
        },
    }
    return output


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_evolution(
    data_dir: str,
    output_path: str = "param_profile.json",
    target_tiers: Optional[List[str]] = None,
    top_n: int = PASS3_TOP_N_DEFAULT,
    run_pass: int = 3,
):
    print("\n" + "=" * 65)
    print("  EDGELAB PARAM EVOLUTION — Three-Pass Full Param Sweep")
    print("=" * 65)

    if target_tiers:
        print(f"\n  Target tiers: {', '.join(target_tiers)}")
    print(f"  Params in candidate set: {len(PARAM_CANDIDATES)}")
    print(f"  Reintroduced: draw_pull, dti_draw_lock, w_btts")
    print(f"  Pass 3 movers per tier: top {top_n}")

    # Load data
    print(f"\n  Loading data from: {data_dir}")
    try:
        df_all = load_all_csvs(data_dir)
    except FileNotFoundError as e:
        print(f"\n  ERROR: {e}")
        sys.exit(1)

    print(f"  {len(df_all):,} matches loaded across {df_all['tier'].nunique()} tiers")

    all_tiers = sorted(df_all["tier"].unique())
    tiers_to_run = [t for t in all_tiers if t in target_tiers] if target_tiers else all_tiers

    # Run pipeline — Pass 1 data prep
    print(f"\n  Running prediction pipeline on {len(tiers_to_run)} tiers...")
    processed_tiers = {}
    evolved_params = {}

    for tier in tiers_to_run:
        df_tier = df_all[df_all["tier"] == tier].copy().reset_index(drop=True)
        if len(df_tier) < 200:
            print(f"  [{tier}] skipped — insufficient data ({len(df_tier)} matches)")
            continue
        print(f"  [{tier}] {len(df_tier):,} matches...", end=" ", flush=True)
        try:
            df_tier = run_pipeline(df_tier)
            processed_tiers[tier] = df_tier
            evolved_params[tier] = load_evolved_params(tier)
            print("done")
        except Exception as e:
            print(f"ERROR: {e}")

    if not processed_tiers:
        print("\n  ERROR: No tiers processed.")
        sys.exit(1)

    # Pass 1 — Baseline
    baseline = pass1_baseline(processed_tiers, evolved_params)

    if run_pass < 2:
        print(f"\n  Stopping after Pass 1 (--pass 1 specified).")
        return

    # Pass 2 — Single param sweep
    pass2_results = pass2_single_param_sweep(
        processed_tiers, evolved_params, baseline, list(processed_tiers.keys())
    )
    tier_movers = summarise_pass2(pass2_results, top_n=top_n)

    # Pass 2b — Post-match teacher layer
    teacher_results = pass2b_teacher(processed_tiers, baseline, tier_movers)

    if run_pass < 3:
        print(f"\n  Stopping after Pass 2 (--pass 2 specified).")
        output = build_json_output(baseline, pass2_results, tier_movers, {}, teacher_results)
        if output_path:
            with open(output_path, "w") as f:
                json.dump(output, f, indent=2)
            print(f"\n  Results saved to: {output_path}")
        return

    # Pass 3 — Combinations
    tier_combo_results = pass3_combinations(
        processed_tiers, evolved_params, baseline,
        pass2_results, tier_movers, list(processed_tiers.keys()),
        teacher_results=teacher_results,
    )

    print_final_summary(baseline, tier_combo_results)

    # Save output
    output = build_json_output(baseline, pass2_results, tier_movers, tier_combo_results, teacher_results)
    if output_path:
        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)
        print(f"\n  Full results saved to: {output_path}")

    print("\n" + "=" * 65 + "\n")
    return output


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="EdgeLab Param Evolution — Three-pass full param sweep"
    )
    parser.add_argument("--data",    required=True,
                        help="Path to history/ folder")
    parser.add_argument("--output",  default="param_profile.json",
                        help="Output JSON path (default: param_profile.json)")
    parser.add_argument("--tier",    type=str, default=None,
                        help="Single tier or comma-separated list e.g. E0,E1,N1")
    parser.add_argument("--pass",    type=int, default=3, dest="run_pass",
                        choices=[1, 2, 3],
                        help="Stop after this pass (default: 3 — full run)")
    parser.add_argument("--top",     type=int, default=PASS3_TOP_N_DEFAULT,
                        help=f"Top N movers per tier into Pass 3 (default: {PASS3_TOP_N_DEFAULT})")

    args = parser.parse_args()

    target_tiers = None
    if args.tier:
        target_tiers = [t.strip().upper() for t in args.tier.split(",")]

    run_evolution(
        data_dir=args.data,
        output_path=args.output,
        target_tiers=target_tiers,
        top_n=args.top,
        run_pass=args.run_pass,
    )
