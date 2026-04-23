#!/usr/bin/env python3
"""
EdgeLab Scoreline Maps
----------------------
Builds scoreline-specific param profiles — the foundational layer of the
outcome-specific architecture.

Rather than asking "what params maximise overall accuracy?", this asks:
"what param signature best describes the conditions surrounding each
specific scoreline in history?"

Each scoreline population (1-0 H, 2-1 H, 0-0 D, 0-1 A etc.) is evolved
independently. The result is a density map: for any live fixture, the engine
can ask which historical scoreline populations it most resembles — not as a
score prediction, but as a param fingerprint.

H/D/A is derived from this — the outcome label falls out of whichever
scoreline populations fire most strongly. The map is the architecture.

Key design principles:
- Populations never bleed into each other. 1-0 H evolves only on 1-0 H rows.
- Volume does not confer advantage. 1-0 is the most common scoreline in
  football — it does not get a bigger voice in the map than 3-2 H.
- Thin populations merge to their parent outcome group (H/D/A) rather than
  producing noisy maps from insufficient data. The minimum sample threshold
  is derived from the distribution itself, not hardcoded.
- The loss function is membership density — how tightly does this param set
  cluster this scoreline's conditions vs the rest of the tier?
  Not accuracy. Not draw weight. Pure population description.
- Features are computed ONCE per tier and cached. Candidate evaluation only
  re-runs predict_dataframe (fast, vectorised) not the full pipeline.
- All structural thresholds are derived from the data. No magic numbers.

Usage:
    python edgelab_scoreline_maps.py history/ --tier E0
    python edgelab_scoreline_maps.py history/ --tier all
    python edgelab_scoreline_maps.py history/ --tier E0 --show-populations

Output:
    Evolved param profiles saved to edgelab.db scoreline_param_profiles table.
    One row per (tier, scoreline) with full param set and population stats.
"""

import sys
import os
import argparse
import logging
import copy
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from edgelab_engine import (
    load_all_csvs,
    prepare_dataframe,
    predict_dataframe,
    EngineParams,
)
from edgelab_dpol import LeagueParams
from edgelab_config import load_params

# Suppress noisy signal warnings
logging.basicConfig(level=logging.WARNING)
logging.getLogger("EdgeLab").setLevel(logging.ERROR)
logging.getLogger("edgelab_signals").setLevel(logging.ERROR)
logger = logging.getLogger("ScorelineMaps")
logger.setLevel(logging.INFO)

ALL_TIERS = [
    "E0", "E1", "E2", "E3", "EC",
    "B1", "D1", "D2", "I1", "I2", "N1",
    "SC0", "SC1", "SC2", "SC3", "SP1", "SP2",
]

# Features used for density scoring.
# Split into two groups:
# - Param-independent: computed once, cached for the full tier
# - Param-sensitive: recomputed per candidate via predict_dataframe
DENSITY_FEATURES_STATIC = [
    "home_form", "away_form", "home_gd", "away_gd", "dti",
]
DENSITY_FEATURES_DYNAMIC = [
    "pred_margin", "confidence", "draw_score",
]
DENSITY_FEATURES = DENSITY_FEATURES_STATIC + DENSITY_FEATURES_DYNAMIC


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def init_scoreline_table(db_path: str):
    import sqlite3
    from edgelab_db import PARAM_FIELDS
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        param_cols = "\n    ".join(f"p_{p}  REAL" for p in PARAM_FIELDS)
        conn.execute(f"""
        CREATE TABLE IF NOT EXISTS scoreline_param_profiles (
            profile_id          TEXT PRIMARY KEY,
            tier                TEXT NOT NULL,
            scoreline           TEXT NOT NULL,
            outcome             TEXT NOT NULL,
            population_size     INTEGER NOT NULL,
            merged_to_outcome   INTEGER NOT NULL DEFAULT 0,
            evolved_density     REAL,
            baseline_density    REAL,
            delta_density       REAL,
            evolved_at          TIMESTAMP NOT NULL,
            run_id              TEXT,
            {param_cols}
        )
        """)

        # Migration — add any missing param columns to existing table.
        # Handles the case where the table was created before all params
        # were included (e.g. from a broken first run).
        existing = {
            row[1]
            for row in conn.execute(
                "PRAGMA table_info(scoreline_param_profiles)"
            ).fetchall()
        }
        for p in PARAM_FIELDS:
            col = f"p_{p}"
            if col not in existing:
                try:
                    conn.execute(
                        f"ALTER TABLE scoreline_param_profiles ADD COLUMN {col} REAL"
                    )
                    logger.info(f"Migration: added scoreline_param_profiles.{col}")
                except Exception:
                    pass

        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_scp_tier "
            "ON scoreline_param_profiles(tier)"
        )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_scp_tier_scoreline "
            "ON scoreline_param_profiles(tier, scoreline)"
        )
        conn.commit()


def save_scoreline_profile(
    db_path, tier, scoreline, outcome, population_size,
    merged, evolved_density, baseline_density, params, run_id,
):
    import sqlite3
    import hashlib
    from datetime import datetime
    from edgelab_db import PARAM_FIELDS

    profile_id = hashlib.md5(f"{tier}_{scoreline}".encode()).hexdigest()[:16]
    delta = evolved_density - baseline_density
    param_cols = [f"p_{p}" for p in PARAM_FIELDS]
    param_vals = [getattr(params, p, 0.0) for p in PARAM_FIELDS]
    base_cols = [
        "profile_id", "tier", "scoreline", "outcome",
        "population_size", "merged_to_outcome",
        "evolved_density", "baseline_density", "delta_density",
        "evolved_at", "run_id",
    ]
    base_vals = [
        profile_id, tier, scoreline, outcome,
        population_size, int(merged),
        round(evolved_density, 6), round(baseline_density, 6), round(delta, 6),
        datetime.utcnow().isoformat(), run_id,
    ]
    all_cols = base_cols + param_cols
    all_vals = base_vals + param_vals
    placeholders = ",".join("?" * len(all_cols))
    col_str = ",".join(all_cols)
    update_str = ",".join(f"{c}=excluded.{c}" for c in all_cols if c != "profile_id")
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(
            f"INSERT INTO scoreline_param_profiles ({col_str}) VALUES ({placeholders}) "
            f"ON CONFLICT(profile_id) DO UPDATE SET {update_str}",
            all_vals,
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Population analysis
# ---------------------------------------------------------------------------

def analyse_populations(df_tier: pd.DataFrame) -> Dict[str, Dict]:
    total = len(df_tier)
    if total == 0:
        return {}
    df = df_tier.copy()
    df["scoreline"] = (
        df["FTHG"].astype(int).astype(str) + "-" +
        df["FTAG"].astype(int).astype(str)
    )
    counts = df["scoreline"].value_counts().to_dict()
    outcome_map = {
        sl: df[df["scoreline"] == sl]["FTR"].iloc[0]
        for sl in counts
    }
    return {
        sl: {"count": c, "outcome": outcome_map[sl], "pct_of_tier": round(c / total, 4)}
        for sl, c in counts.items()
    }


def derive_min_population(populations: Dict[str, Dict]) -> int:
    counts = sorted([p["count"] for p in populations.values()], reverse=True)
    if len(counts) < 3:
        return 0
    gaps = [counts[i] - counts[i+1] for i in range(len(counts)-1)]
    best_ratio, elbow_idx = 0.0, len(counts) - 1
    for i, gap in enumerate(gaps):
        ratio = gap / (counts[i] if counts[i] > 0 else 1)
        if ratio > best_ratio:
            best_ratio = ratio
            elbow_idx = i + 1
    return counts[elbow_idx] if elbow_idx < len(counts) else 0


# ---------------------------------------------------------------------------
# Density scoring — operates on pre-cached normalised feature matrix
# ---------------------------------------------------------------------------

def build_feat_norm(df_featured: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    available = [c for c in DENSITY_FEATURES if c in df_featured.columns]
    vals = df_featured[available].fillna(0.0).values.astype(float)
    means = vals.mean(axis=0)
    stds = vals.std(axis=0)
    stds = np.where(stds > 0, stds, 1.0)
    return (vals - means) / stds, means, stds


def score_density(pop_mask: np.ndarray, feat_norm: np.ndarray) -> float:
    pop_norm = feat_norm[pop_mask]
    if len(pop_norm) < 2:
        return 0.0
    centroid = pop_norm.mean(axis=0)
    intra = float(np.sqrt(((pop_norm - centroid) ** 2).sum(axis=1)).mean())
    inter = float(np.sqrt(((feat_norm - centroid) ** 2).sum(axis=1)).mean())
    if inter == 0:
        return 0.0
    return round((inter - intra) / inter, 6)


# ---------------------------------------------------------------------------
# Param helpers
# ---------------------------------------------------------------------------

def lp_to_ep(lp: LeagueParams) -> EngineParams:
    return EngineParams(
        w_form=lp.w_form, w_gd=lp.w_gd, home_adv=lp.home_adv,
        dti_edge_scale=lp.dti_edge_scale, dti_ha_scale=lp.dti_ha_scale,
        draw_margin=lp.draw_margin, coin_dti_thresh=lp.coin_dti_thresh,
        draw_pull=lp.draw_pull, dti_draw_lock=lp.dti_draw_lock,
        w_draw_odds=lp.w_draw_odds, w_draw_tendency=lp.w_draw_tendency,
        w_h2h_draw=lp.w_h2h_draw, draw_score_thresh=lp.draw_score_thresh,
        w_score_margin=lp.w_score_margin,
        w_xg_draw=getattr(lp, "w_xg_draw", 0.0),
        composite_draw_boost=getattr(lp, "composite_draw_boost", 0.0),
        w_ref_signal=getattr(lp, "w_ref_signal", 0.0),
        w_travel_load=getattr(lp, "w_travel_load", 0.0),
        w_timing_signal=getattr(lp, "w_timing_signal", 0.0),
        w_motivation_gap=getattr(lp, "w_motivation_gap", 0.0),
        w_weather_signal=getattr(lp, "w_weather_signal", 0.0),
        w_venue_form=getattr(lp, "w_venue_form", 0.0),
        w_team_home_adv=getattr(lp, "w_team_home_adv", 0.0),
        w_away_team_adv=getattr(lp, "w_away_team_adv", 0.0),
        w_opp_strength=getattr(lp, "w_opp_strength", 0.0),
        w_season_stage=getattr(lp, "w_season_stage", 0.0),
        w_rest_diff=getattr(lp, "w_rest_diff", 0.0),
        w_scoreline_agreement=getattr(lp, "w_scoreline_agreement", 0.0),
        w_scoreline_confidence=getattr(lp, "w_scoreline_confidence", 0.0),
        form_window=5,
    )


# ---------------------------------------------------------------------------
# Candidate generation
# ---------------------------------------------------------------------------

def generate_candidates(base: LeagueParams, step: float) -> List[LeagueParams]:
    candidates = []

    def add(name, val):
        c = copy.deepcopy(base)
        setattr(c, name, val)
        candidates.append(c)

    for name in ("w_form", "w_gd", "home_adv", "dti_edge_scale",
                 "dti_ha_scale", "draw_margin", "coin_dti_thresh"):
        cur = getattr(base, name)
        add(name, cur * (1 + step))
        down = cur * (1 - step)
        if down > 0:
            add(name, down)

    for name in ("w_score_margin", "w_draw_odds", "w_h2h_draw",
                 "w_xg_draw", "w_weather_signal",
                 "w_ref_signal", "w_travel_load",
                 "w_timing_signal", "w_motivation_gap",
                 "w_venue_form", "w_team_home_adv", "w_away_team_adv", "w_opp_strength",
                 "w_season_stage", "w_rest_diff",
                 "w_scoreline_agreement", "w_scoreline_confidence"):
        cur = getattr(base, name)
        add(name, cur + step)
        if cur > 0:
            add(name, max(0.0, cur - step))

    return candidates


# ---------------------------------------------------------------------------
# Evolution loop — fast, using cached features
# ---------------------------------------------------------------------------

def evolve_population(
    pop_mask: np.ndarray,
    df_featured: pd.DataFrame,
    feat_norm: np.ndarray,
    starting_lp: LeagueParams,
    pop_fraction: float,
    max_iterations: int,
) -> Tuple[LeagueParams, float, float]:
    """
    Evolve params for one scoreline population using cached features.
    Dynamic features (confidence, draw_score, pred_margin) are recomputed
    per candidate via predict_dataframe. Static features are cached.

    Uses multi-scale search: bold steps first to escape the average,
    fine steps to refine. Cold start — each population finds its own
    signature from neutral ground.
    """
    best_lp = copy.deepcopy(starting_lp)
    current_norm = feat_norm.copy()
    baseline = score_density(pop_mask, current_norm)
    best = baseline

    # Multi-scale: bold first to find a distinctive region, fine to refine.
    # Scales derived from population fraction — more data = finer refinement.
    step_coarse = max(0.15, min(0.40, 0.40 - (0.25 * pop_fraction)))
    step_fine   = max(0.05, min(0.15, 0.15 - (0.10 * pop_fraction)))
    schedules = [
        (step_coarse, max(3, max_iterations // 2)),
        (step_fine,   max(2, max_iterations // 2)),
    ]

    for step, n_iter in schedules:
        for _ in range(n_iter):
            candidates = generate_candidates(best_lp, step)
            improved = False

            for cand_lp in candidates:
                try:
                    cand_ep = lp_to_ep(cand_lp)
                    df_pred = predict_dataframe(df_featured.copy(), cand_ep)

                    df_updated = df_featured.copy()
                    for col in DENSITY_FEATURES_DYNAMIC:
                        if col in df_pred.columns:
                            df_updated[col] = df_pred[col]
                    cand_norm, _, _ = build_feat_norm(df_updated)

                    density = score_density(pop_mask, cand_norm)
                    if density > best + 0.0005:
                        best = density
                        best_lp = copy.deepcopy(cand_lp)
                        current_norm = cand_norm
                        improved = True
                except Exception:
                    continue

            if not improved:
                step *= 0.5
                if step < 0.005:
                    break

    return best_lp, baseline, best


# ---------------------------------------------------------------------------
# Tier runner
# ---------------------------------------------------------------------------

def run_scoreline_maps_for_tier(
    df_tier: pd.DataFrame,
    tier: str,
    db_path: str,
    run_id: str,
    show_populations: bool = False,
    outcome_params=None,  # OutcomeParams — if provided, seed each population from matching outcome
) -> Dict:
    print(f"\n{'='*60}")
    print(f"  SCORELINE MAPS — {tier}  |  {len(df_tier):,} matches")
    if outcome_params is not None:
        print(f"  Seed: outcome-specific params (H→H pops, D→D pops, A→A pops)")
    print(f"{'='*60}")

    df_tier = df_tier.copy()
    df_tier["scoreline"] = (
        df_tier["FTHG"].astype(int).astype(str) + "-" +
        df_tier["FTAG"].astype(int).astype(str)
    )

    populations = analyse_populations(df_tier)
    min_pop = derive_min_population(populations)

    print(f"\n  Populations : {len(populations)}")
    print(f"  Min viable  : {min_pop} (data-derived)")

    if show_populations:
        print(f"\n  {'Scoreline':<10} {'Count':>7} {'Out':>4} {'%':>7}  Status")
        print(f"  {'-'*42}")
        for sl, info in sorted(populations.items(),
                                key=lambda x: x[1]["count"], reverse=True):
            status = "EVOLVE" if info["count"] >= min_pop else f"→ {info['outcome']}"
            print(f"  {sl:<10} {info['count']:>7,} {info['outcome']:>4} "
                  f"{info['pct_of_tier']:>6.1%}  {status}")

    saved = load_params(tier)
    saved_lp = saved if saved is not None else LeagueParams()

    # Determine starting params:
    # If outcome_params provided, each population seeds from its matching outcome params.
    # Otherwise cold start (each population finds its own signature from defaults).
    if outcome_params is not None:
        print(f"  Start       : outcome-specific seed (H/D/A params per population)")
        # We'll select seed per-population based on outcome — see evolve loop below
        default_starting_lp = LeagueParams()  # fallback only
    else:
        default_starting_lp = LeagueParams()
        print(f"  Start       : cold (defaults) — scoreline maps escape the average")

    # ── Precompute features ONCE ─────────────────────────────────────────
    # Use averaged starting params for feature computation (neutral baseline)
    print(f"  Computing features...", end="", flush=True)
    starting_ep = lp_to_ep(default_starting_lp)
    df_featured = prepare_dataframe(df_tier.copy(), starting_ep)
    feat_norm, _, _ = build_feat_norm(df_featured)
    print(f" done")

    viable = {sl: i for sl, i in populations.items() if i["count"] >= min_pop}
    thin = {sl: i for sl, i in populations.items() if i["count"] < min_pop}

    print(f"  Evolving    : {len(viable)}  |  Merging: {len(thin)}\n")

    results = {
        "tier": tier, "total_populations": len(populations),
        "viable": len(viable), "merged": len(thin),
        "improvements": 0, "avg_delta": 0.0,
    }
    deltas = []

    for scoreline, info in sorted(viable.items(),
                                   key=lambda x: x[1]["count"], reverse=True):
        pop_outcome = info["outcome"]
        count = info["count"]
        pop_mask = (df_featured["scoreline"] == scoreline).values
        pop_fraction = count / len(df_tier)
        max_iter = max(5, min(30, int(30 * pop_fraction * 10)))

        print(f"  [{scoreline}] n={count:,} iter={max_iter}", end="", flush=True)

        # Seed from outcome-specific params if available, else cold start
        if outcome_params is not None:
            seed_lp = copy.deepcopy(outcome_params.for_outcome(pop_outcome))
        else:
            seed_lp = copy.deepcopy(default_starting_lp)

        best_lp, baseline, best_density = evolve_population(
            pop_mask=pop_mask,
            df_featured=df_featured,
            feat_norm=feat_norm.copy(),
            starting_lp=seed_lp,
            pop_fraction=pop_fraction,
            max_iterations=max_iter,
        )

        delta = best_density - baseline
        deltas.append(delta)
        d = "▲" if delta > 0.0005 else ("─" if abs(delta) <= 0.0005 else "▼")
        print(f"  {baseline:.4f}→{best_density:.4f} {d}{delta:+.4f}")

        if delta > 0.0005:
            results["improvements"] += 1

        save_scoreline_profile(
            db_path=db_path, tier=tier, scoreline=scoreline,
            outcome=pop_outcome, population_size=count, merged=False,
            evolved_density=best_density, baseline_density=baseline,
            params=best_lp, run_id=run_id,
        )

    for scoreline, info in thin.items():
        # Merged populations use the appropriate outcome seed if available
        if outcome_params is not None:
            thin_seed = copy.deepcopy(outcome_params.for_outcome(info["outcome"]))
        else:
            thin_seed = saved_lp
        save_scoreline_profile(
            db_path=db_path, tier=tier, scoreline=scoreline,
            outcome=info["outcome"], population_size=info["count"],
            merged=True, evolved_density=0.0, baseline_density=0.0,
            params=thin_seed, run_id=run_id,
        )

    if deltas:
        results["avg_delta"] = round(sum(deltas) / len(deltas), 4)

    print(f"\n  {results['improvements']}/{results['viable']} improved  "
          f"avg Δ: {results['avg_delta']:+.4f}")
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="EdgeLab Scoreline Maps — scoreline-specific param profiles"
    )
    parser.add_argument("folder", nargs="?", default=".")
    parser.add_argument("--tier", type=str, default="all")
    parser.add_argument("--db", type=str, default=None)
    parser.add_argument("--show-populations", action="store_true")
    args = parser.parse_args()

    db_path = args.db or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "edgelab.db"
    )

    print("\n╔══════════════════════════════════════════╗")
    print("║     EdgeLab Scoreline Maps Builder       ║")
    print("╚══════════════════════════════════════════╝")
    print(f"\n  Folder : {args.folder}")
    print(f"  DB     : {db_path}")
    print(f"  Tier   : {args.tier}")

    init_scoreline_table(db_path)

    from datetime import datetime
    run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    print(f"\n  Loading CSVs...")
    df_all = load_all_csvs(args.folder)
    print(f"  {len(df_all):,} rows, {df_all['tier'].nunique()} tiers")

    tiers_to_run = ALL_TIERS if args.tier == "all" else [
        t.strip().upper() for t in args.tier.split(",")
    ]

    all_results = []
    for tier in tiers_to_run:
        df_tier = df_all[df_all["tier"] == tier].copy()
        if df_tier.empty:
            print(f"\n  No data for {tier} — skipping")
            continue
        result = run_scoreline_maps_for_tier(
            df_tier=df_tier, tier=tier, db_path=db_path,
            run_id=run_id, show_populations=args.show_populations,
        )
        all_results.append(result)

    print(f"\n\n{'='*60}")
    print("  FINAL SUMMARY")
    print(f"{'='*60}")
    print(f"  {'Tier':<6}  {'Pops':>5}  {'Evol':>5}  {'Mrgd':>5}  "
          f"{'Imprvd':>7}  {'Avg Δ':>8}")
    print(f"  {'-'*48}")
    for r in all_results:
        print(f"  {r['tier']:<6}  {r['total_populations']:>5}  "
              f"{r['viable']:>5}  {r['merged']:>5}  "
              f"{r['improvements']:>7}  {r['avg_delta']:>+8.4f}")

    print(f"\n  Run ID : {run_id}\n")


if __name__ == "__main__":
    main()
