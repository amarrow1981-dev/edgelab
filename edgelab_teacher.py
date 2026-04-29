"""
EdgeLab Teacher Layer

Primary directive: investigate and learn from incorrect predictions.
Correct calls reinforce existing signal. Incorrect calls are the primary
learning input — autopsy, not celebration.

Architecture (Session 44 design, signed off):
  - Scope: per neighbourhood, per result type. Not tier-level.
  - Fires as part of every DPOL run + manually after results (twice weekly).
  - Does NOT adjust params live — enriches candidate log only.
  - Historical data (25 years) seeds it immediately — no waiting for live results.
  - Closing line movement (B365CH/CD/CA) confirmed as teacher input.

Build order (Session 45):
  1. edgelab_teacher.py — recorder and miss analyser  ← THIS FILE
  2. Verify data looks right across historical results
  3. Wire into edgelab_dpol.py

Table: prediction_result_memory in edgelab.db

Usage:
  # Seed from historical CSVs (one-time or catch-up):
  python edgelab_teacher.py --seed history/

  # Record results after a prediction weekend:
  python edgelab_teacher.py --record predictions/2026-04-24_predictions.csv \\
      --results results/2026-04-24_results.csv

  # Analyse miss patterns for a tier:
  python edgelab_teacher.py --analyse --tier E0

  # Analyse all tiers:
  python edgelab_teacher.py --analyse

  # Show summary stats:
  python edgelab_teacher.py --summary
"""

import os
import sqlite3
import logging
import argparse
import glob
import hashlib
from datetime import datetime
from typing import Optional

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[Teacher] %(message)s")

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "edgelab.db")

# ---------------------------------------------------------------------------
# Match key
# ---------------------------------------------------------------------------

def make_match_key(tier: str, date: str, home: str, away: str) -> str:
    """
    Stable match key — same logic used across predictions, results, and seeder.
    Normalises inputs before hashing so minor whitespace/case differences don't
    produce different keys.
    """
    raw = f"{str(tier).strip().upper()}|{str(date).strip()}|{str(home).strip().lower()}|{str(away).strip().lower()}"
    return hashlib.md5(raw.encode()).hexdigest()


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def get_conn(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def ensure_table(conn: sqlite3.Connection):
    """
    Create prediction_result_memory if it doesn't exist.
    Also handles migration — safe to call on existing DB.
    """
    conn.execute("""
    CREATE TABLE IF NOT EXISTS prediction_result_memory (
        match_key           TEXT PRIMARY KEY,
        tier                TEXT NOT NULL,
        match_date          TEXT NOT NULL,
        home_team           TEXT NOT NULL,
        away_team           TEXT NOT NULL,
        season              TEXT,

        -- Engine prediction snapshot
        prediction          TEXT,
        pred_scoreline      TEXT,
        confidence          REAL,
        dti                 REAL,
        chaos_tier          TEXT,

        -- Per-outcome predictions and confidences
        pred_H              TEXT,
        pred_D              TEXT,
        pred_A              TEXT,
        conf_H              REAL,
        conf_D              REAL,
        conf_A              REAL,

        -- Actual result
        actual              TEXT,
        actual_home_goals   INTEGER,
        actual_away_goals   INTEGER,
        actual_scoreline    TEXT,
        correct             INTEGER,

        -- Opening odds (B365)
        b365h               REAL,
        b365d               REAL,
        b365a               REAL,

        -- Closing odds (B365C) — from raw CSVs
        b365ch              REAL,
        b365cd              REAL,
        b365ca              REAL,

        -- Closing line movement signal
        -- Positive = market moved toward H/D/A (shortened), negative = drifted
        close_move_h        REAL,
        close_move_d        REAL,
        close_move_a        REAL,

        -- Implied probabilities (closing, normalised)
        impl_prob_h         REAL,
        impl_prob_d         REAL,
        impl_prob_a         REAL,

        -- Fixture features at prediction time
        home_form           REAL,
        away_form           REAL,
        home_gd             REAL,
        away_gd             REAL,
        home_form_home      REAL,
        away_form_away      REAL,
        home_adv_team       REAL,
        home_form_adj       REAL,
        away_form_adj       REAL,
        season_stage        REAL,
        rest_days_diff      REAL,
        odds_draw_prob      REAL,

        -- Upset / BTTS signals
        upset_score         REAL,
        upset_flag          INTEGER,
        btts_flag           INTEGER,
        btts_prob           REAL,

        -- Scoreline map signal
        top_scoreline_match TEXT,

        -- Miss analysis fields (populated by analyse pass)
        miss_type           TEXT,    -- 'predicted_H_was_D', 'predicted_A_was_H', etc.
        confidence_band     TEXT,    -- 'high' >=0.8, 'mid' 0.5-0.8, 'low' <0.5
        market_agreed       INTEGER, -- 1 if market favourite matched our prediction
        closing_line_signal TEXT,    -- 'backed_our_call', 'against_our_call', 'neutral'
        neighbourhood_id    TEXT,    -- reserved for future DPOL neighbourhood link

        -- Metadata
        source              TEXT NOT NULL,  -- 'historical_seed' | 'live_record'
        recorded_at         TIMESTAMP NOT NULL
    )
    """)

    # Index for fast neighbourhood queries
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_prm_tier_correct
        ON prediction_result_memory (tier, correct)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_prm_tier_date
        ON prediction_result_memory (tier, match_date)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_prm_miss_type
        ON prediction_result_memory (tier, miss_type)
    """)

    conn.commit()


# ---------------------------------------------------------------------------
# Miss analysis helpers
# ---------------------------------------------------------------------------

def classify_miss(prediction: str, actual: str) -> Optional[str]:
    """Classify the type of miss. Returns None if correct."""
    if prediction == actual:
        return None
    return f"predicted_{prediction}_was_{actual}"


def confidence_band(confidence: float) -> str:
    if confidence >= 0.8:
        return "high"
    elif confidence >= 0.5:
        return "mid"
    return "low"


def market_favourite(b365h: float, b365d: float, b365a: float) -> Optional[str]:
    """Return H/D/A for shortest odds (market favourite). None if any missing."""
    try:
        odds = {"H": float(b365h), "D": float(b365d), "A": float(b365a)}
        if any(v <= 0 for v in odds.values()):
            return None
        return min(odds, key=odds.get)
    except (TypeError, ValueError):
        return None


def closing_line_signal(prediction: str, b365h, b365d, b365a,
                        b365ch, b365cd, b365ca) -> str:
    """
    Did the closing line move toward or away from our prediction?
    'backed_our_call'  — closing odds shorter than opening for predicted outcome
    'against_our_call' — closing odds longer than opening for predicted outcome
    'neutral'          — no meaningful movement or data missing
    """
    try:
        opening = {"H": float(b365h), "D": float(b365d), "A": float(b365a)}
        closing = {"H": float(b365ch), "D": float(b365cd), "A": float(b365ca)}
        if any(v <= 0 for v in list(opening.values()) + list(closing.values())):
            return "neutral"
        open_p = opening[prediction]
        close_p = closing[prediction]
        move = (1 / open_p) - (1 / close_p)  # positive = drifted out (market moved away)
        if move > 0.01:
            return "against_our_call"
        elif move < -0.01:
            return "backed_our_call"
        return "neutral"
    except (TypeError, ValueError, KeyError, ZeroDivisionError):
        return "neutral"


def implied_probs(b365h, b365d, b365a):
    """Return normalised implied probabilities from closing odds."""
    try:
        h, d, a = float(b365h), float(b365d), float(b365a)
        if h <= 0 or d <= 0 or a <= 0:
            return None, None, None
        raw_h, raw_d, raw_a = 1/h, 1/d, 1/a
        total = raw_h + raw_d + raw_a
        return raw_h/total, raw_d/total, raw_a/total
    except (TypeError, ValueError, ZeroDivisionError):
        return None, None, None


def closing_move(open_odds, close_odds):
    """
    Implied prob difference: closing - opening.
    Positive = market shortened (more confident), negative = drifted.
    """
    try:
        o, c = float(open_odds), float(close_odds)
        if o <= 0 or c <= 0:
            return None
        return round((1/c) - (1/o), 4)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


# ---------------------------------------------------------------------------
# Recorder — live predictions + results
# ---------------------------------------------------------------------------

def record_results(predictions_csv: str, results_csv: str,
                   db_path: str = DEFAULT_DB_PATH) -> dict:
    """
    Record prediction outcomes from a completed prediction week.

    predictions_csv: output of edgelab_predict.py
    results_csv:     output of edgelab_results_check.py (has FTR, FTHG, FTAG)

    Returns summary dict with counts.
    """
    preds = pd.read_csv(predictions_csv)
    results = pd.read_csv(results_csv)

    # Normalise column names
    preds.columns = [c.strip() for c in preds.columns]
    results.columns = [c.strip() for c in results.columns]

    # Build match key on both sides
    preds["_key"] = preds.apply(
        lambda r: make_match_key(r.get("tier",""), r.get("Date",""),
                                  r.get("HomeTeam",""), r.get("AwayTeam","")), axis=1)
    results["_key"] = results.apply(
        lambda r: make_match_key(r.get("tier",""), r.get("Date",""),
                                  r.get("HomeTeam",""), r.get("AwayTeam","")), axis=1)

    merged = preds.merge(results[["_key","FTR","FTHG","FTAG",
                                   "B365CH","B365CD","B365CA"]],
                         on="_key", how="left")

    conn = get_conn(db_path)
    ensure_table(conn)

    inserted = 0
    updated = 0
    skipped = 0

    for _, row in merged.iterrows():
        key = row["_key"]
        actual = row.get("FTR")
        if pd.isna(actual):
            skipped += 1
            continue

        prediction = str(row.get("prediction", ""))
        conf = float(row.get("confidence", 0.5)) if not pd.isna(row.get("confidence")) else 0.5
        correct = 1 if prediction == actual else 0

        hg = int(row["FTHG"]) if not pd.isna(row.get("FTHG")) else None
        ag = int(row["FTAG"]) if not pd.isna(row.get("FTAG")) else None
        actual_sl = f"{hg}-{ag}" if hg is not None and ag is not None else None

        b365h = _safe_float(row.get("B365H"))
        b365d = _safe_float(row.get("B365D"))
        b365a = _safe_float(row.get("B365A"))
        b365ch = _safe_float(row.get("B365CH"))
        b365cd = _safe_float(row.get("B365CD"))
        b365ca = _safe_float(row.get("B365CA"))

        # Closing line analysis
        cl_signal = closing_line_signal(prediction, b365h, b365d, b365a,
                                         b365ch, b365cd, b365ca)
        iph, ipd, ipa = implied_probs(
            b365ch or b365h, b365cd or b365d, b365ca or b365a)

        cmh = closing_move(b365h, b365ch) if b365h and b365ch else None
        cmd = closing_move(b365d, b365cd) if b365d and b365cd else None
        cma = closing_move(b365a, b365ca) if b365a and b365ca else None

        fav = market_favourite(b365h or 0, b365d or 0, b365a or 0)
        market_agreed = 1 if fav == prediction else 0 if fav else None

        miss = classify_miss(prediction, actual)
        cb = confidence_band(conf)

        existing = conn.execute(
            "SELECT match_key FROM prediction_result_memory WHERE match_key=?",
            (key,)).fetchone()

        if existing:
            conn.execute("""
                UPDATE prediction_result_memory SET
                    actual=?, actual_home_goals=?, actual_away_goals=?,
                    actual_scoreline=?, correct=?,
                    b365ch=?, b365cd=?, b365ca=?,
                    close_move_h=?, close_move_d=?, close_move_a=?,
                    impl_prob_h=?, impl_prob_d=?, impl_prob_a=?,
                    miss_type=?, confidence_band=?, market_agreed=?,
                    closing_line_signal=?
                WHERE match_key=?
            """, (actual, hg, ag, actual_sl, correct,
                  b365ch, b365cd, b365ca,
                  cmh, cmd, cma,
                  iph, ipd, ipa,
                  miss, cb, market_agreed, cl_signal,
                  key))
            updated += 1
        else:
            conn.execute("""
                INSERT OR IGNORE INTO prediction_result_memory (
                        match_key, tier, match_date, home_team, away_team, season,
                        prediction, pred_scoreline, confidence, dti, chaos_tier,
                        pred_H, pred_D, pred_A, conf_H, conf_D, conf_A,
                        actual, actual_home_goals, actual_away_goals, actual_scoreline, correct,
                        b365h, b365d, b365a,
                        b365ch, b365cd, b365ca,
                        close_move_h, close_move_d, close_move_a,
                        impl_prob_h, impl_prob_d, impl_prob_a,
                        home_form, away_form, home_gd, away_gd,
                        home_form_home, away_form_away, home_adv_team,
                        home_form_adj, away_form_adj, season_stage, rest_days_diff, odds_draw_prob,
                        upset_score, upset_flag, btts_flag, btts_prob,
                        top_scoreline_match,
                        miss_type, confidence_band, market_agreed, closing_line_signal,
                        neighbourhood_id, source, recorded_at
                    ) VALUES (
                        ?,?,?,?,?,?,  ?,?,?,?,?,  ?,?,?,?,?,?,  ?,?,?,?,?,
                        ?,?,?,  ?,?,?,  ?,?,?,  ?,?,?,
                        ?,?,?,?,  ?,?,?,  ?,?,?,?,?,
                        ?,?,?,?,  ?,  ?,?,?,?,  ?,?,?
                    )
            """, (
                key,
                str(row.get("tier","")),
                str(row.get("Date","")),
                str(row.get("HomeTeam","")),
                str(row.get("AwayTeam","")),
                None,  # season — not in predictions CSV
                prediction,
                str(row.get("pred_scoreline","")) or None,
                conf,
                _safe_float(row.get("dti")),
                str(row.get("chaos_tier","")) or None,
                str(row.get("pred_H","")) or None,
                str(row.get("pred_D","")) or None,
                str(row.get("pred_A","")) or None,
                _safe_float(row.get("conf_H")),
                _safe_float(row.get("conf_D")),
                _safe_float(row.get("conf_A")),
                actual, hg, ag, actual_sl, correct,
                b365h, b365d, b365a,
                b365ch, b365cd, b365ca,
                cmh, cmd, cma,
                iph, ipd, ipa,
                _safe_float(row.get("home_form")),
                _safe_float(row.get("away_form")),
                _safe_float(row.get("home_gd")),
                _safe_float(row.get("away_gd")),
                _safe_float(row.get("home_form_home")),
                _safe_float(row.get("away_form_away")),
                _safe_float(row.get("home_adv_team")),
                _safe_float(row.get("home_form_adj")),
                _safe_float(row.get("away_form_adj")),
                _safe_float(row.get("season_stage")),
                _safe_float(row.get("rest_days_diff")),
                _safe_float(row.get("odds_draw_prob")),
                _safe_float(row.get("upset_score")),
                _int_or_none(row.get("upset_flag")),
                _int_or_none(row.get("btts_flag")),
                _safe_float(row.get("btts_prob")),
                str(row.get("top_scoreline_match","")) or None,
                miss, cb, market_agreed, cl_signal,
                None,  # neighbourhood_id — reserved
                "live_record",
                datetime.utcnow().isoformat(),
            ))
            inserted += 1

    conn.commit()
    conn.close()

    summary = {
        "inserted": inserted,
        "updated": updated,
        "skipped": skipped,
        "total": inserted + updated,
    }
    logger.info(f"Record complete — inserted:{inserted} updated:{updated} skipped:{skipped}")
    return summary


# ---------------------------------------------------------------------------
# Historical seeder
# ---------------------------------------------------------------------------

def seed_from_history(history_folder: str, db_path: str = DEFAULT_DB_PATH,
                      tiers: list = None) -> dict:
    """
    Seed prediction_result_memory from historical CSVs.

    For each match: runs the engine with current evolved params to get what
    the engine WOULD have predicted, then records against the known result.

    This gives the teacher 25 years of autopsy data immediately.
    Closing line (B365CH/CD/CA) is read directly from the raw CSVs.

    Only inserts — never overwrites existing records (live records take priority).
    """
    try:
        from edgelab_engine import (
            load_all_csvs, prepare_dataframe, predict_dataframe, EngineParams
        )
        from edgelab_config import load_outcome_params
    except ImportError as e:
        logger.error(f"Import failed: {e}. Run from EDGELAB folder.")
        return {}

    logger.info(f"Loading CSVs from {history_folder} ...")
    df_all = load_all_csvs(history_folder)
    logger.info(f"Loaded {len(df_all):,} matches across {df_all['tier'].nunique()} tiers")

    conn = get_conn(db_path)
    ensure_table(conn)

    total_inserted = 0
    total_skipped = 0
    tier_counts = {}

    # Default to the 17 proven tiers — same whitelist as edgelab_merge.py.
    # Harvester leagues are isolated and should not feed the teacher.
    PROVEN_TIERS = {
        "E0","E1","E2","E3","EC",
        "B1","D1","D2","I1","I2","N1",
        "SC0","SC1","SC2","SC3","SP1","SP2"
    }
    tiers_available = sorted(t for t in df_all["tier"].unique() if t in PROVEN_TIERS)
    if tiers:
        tiers_available = [t for t in tiers_available if t in tiers]

    for tier in tiers_available:
        df_tier = df_all[df_all["tier"] == tier].copy()
        if df_tier.empty:
            continue

        # Load evolved H params for this tier as the representative seed.
        # Seeder uses a single param set per tier for the full prediction pass.
        lp_h = load_outcome_params(tier, "H")
        if lp_h is None:
            logger.warning(f"  {tier}: no evolved params found, using defaults")
            ep = EngineParams()
        else:
            ep = _lp_obj_to_engine_params(lp_h)

        logger.info(f"  Seeding {tier}: {len(df_tier):,} matches ...")

        # prepare_dataframe runs the full pipeline including predict_dataframe.
        # FTR, FTHG, FTAG, and odds columns all survive — they are in final_cols
        # from load_all_csvs and none of the compute functions strip them.
        # Just call prepare_dataframe once and use the output directly.
        try:
            df_pred = prepare_dataframe(df_tier.copy(), ep)
        except Exception as e:
            logger.error(f"  {tier}: engine error — {e}")
            continue

        inserted = 0
        skipped = 0

        for _, row in df_pred.iterrows():
            tier_val = str(row.get("tier", tier))
            date_val = str(row.get("parsed_date", row.get("Date", "")))
            home = str(row.get("HomeTeam", ""))
            away = str(row.get("AwayTeam", ""))
            key = make_match_key(tier_val, date_val, home, away)

            # Skip if already recorded (live record takes priority)
            exists = conn.execute(
                "SELECT 1 FROM prediction_result_memory WHERE match_key=?",
                (key,)).fetchone()
            if exists:
                skipped += 1
                continue

            actual = str(row.get("FTR", "")) or None
            if not actual:
                skipped += 1
                continue

            prediction = str(row.get("prediction", ""))
            conf = _safe_float(row.get("confidence")) or 0.5
            correct = 1 if prediction == actual else 0

            hg = _int_or_none(row.get("FTHG"))
            ag = _int_or_none(row.get("FTAG"))
            actual_sl = f"{hg}-{ag}" if hg is not None and ag is not None else None

            b365h = _safe_float(row.get("B365H"))
            b365d = _safe_float(row.get("B365D"))
            b365a = _safe_float(row.get("B365A"))
            b365ch = _safe_float(row.get("B365CH"))
            b365cd = _safe_float(row.get("B365CD"))
            b365ca = _safe_float(row.get("B365CA"))

            cl_signal = closing_line_signal(prediction, b365h, b365d, b365a,
                                             b365ch, b365cd, b365ca)
            iph, ipd, ipa = implied_probs(
                b365ch or b365h, b365cd or b365d, b365ca or b365a)
            cmh = closing_move(b365h, b365ch) if b365h and b365ch else None
            cmd = closing_move(b365d, b365cd) if b365d and b365cd else None
            cma = closing_move(b365a, b365ca) if b365a and b365ca else None

            fav = market_favourite(b365h or 0, b365d or 0, b365a or 0)
            market_agreed = 1 if fav == prediction else 0 if fav else None

            miss = classify_miss(prediction, actual)
            cb = confidence_band(conf)

            season = str(row.get("season", "")) or None

            try:
                conn.execute("""
                    INSERT OR IGNORE INTO prediction_result_memory (
                        match_key, tier, match_date, home_team, away_team, season,
                        prediction, pred_scoreline, confidence, dti, chaos_tier,
                        pred_H, pred_D, pred_A, conf_H, conf_D, conf_A,
                        actual, actual_home_goals, actual_away_goals, actual_scoreline, correct,
                        b365h, b365d, b365a,
                        b365ch, b365cd, b365ca,
                        close_move_h, close_move_d, close_move_a,
                        impl_prob_h, impl_prob_d, impl_prob_a,
                        home_form, away_form, home_gd, away_gd,
                        home_form_home, away_form_away, home_adv_team,
                        home_form_adj, away_form_adj, season_stage, rest_days_diff, odds_draw_prob,
                        upset_score, upset_flag, btts_flag, btts_prob,
                        top_scoreline_match,
                        miss_type, confidence_band, market_agreed, closing_line_signal,
                        neighbourhood_id, source, recorded_at
                    ) VALUES (
                        ?,?,?,?,?,?,  ?,?,?,?,?,  ?,?,?,?,?,?,  ?,?,?,?,?,
                        ?,?,?,  ?,?,?,  ?,?,?,  ?,?,?,
                        ?,?,?,?,  ?,?,?,  ?,?,?,?,?,
                        ?,?,?,?,  ?,  ?,?,?,?,  ?,?,?
                    )
                """, (
                    key, tier_val, date_val, home, away, season,
                    prediction,
                    str(row.get("pred_scoreline","")) or None,
                    conf,
                    _safe_float(row.get("dti")),
                    str(row.get("chaos_tier","")) or None,
                    None, None, None,  # pred_H/D/A not available in seeder
                    None, None, None,  # conf_H/D/A not available in seeder
                    actual, hg, ag, actual_sl, correct,
                    b365h, b365d, b365a,
                    b365ch, b365cd, b365ca,
                    cmh, cmd, cma,
                    iph, ipd, ipa,
                    _safe_float(row.get("home_form")),
                    _safe_float(row.get("away_form")),
                    _safe_float(row.get("home_gd")),
                    _safe_float(row.get("away_gd")),
                    _safe_float(row.get("home_form_home")),
                    _safe_float(row.get("away_form_away")),
                    _safe_float(row.get("home_adv_team")),
                    _safe_float(row.get("home_form_adj")),
                    _safe_float(row.get("away_form_adj")),
                    _safe_float(row.get("season_stage")),
                    _safe_float(row.get("rest_days_diff")),
                    _safe_float(row.get("odds_draw_prob")),
                    _safe_float(row.get("upset_score")),
                    _int_or_none(row.get("upset_flag")),
                    _int_or_none(row.get("btts_flag")),
                    _safe_float(row.get("btts_prob")),
                    str(row.get("top_scoreline_match","")) or None,
                    miss, cb, market_agreed, cl_signal,
                    None,  # neighbourhood_id
                    "historical_seed",
                    datetime.utcnow().isoformat(),
                ))
                inserted += 1
            except Exception as e:
                logger.debug(f"  Insert error row {key}: {e}")
                skipped += 1

        conn.commit()
        tier_counts[tier] = {"inserted": inserted, "skipped": skipped}
        logger.info(f"  {tier}: inserted {inserted:,}, skipped {skipped:,}")
        total_inserted += inserted
        total_skipped += skipped

    conn.close()
    logger.info(f"Seed complete — total inserted: {total_inserted:,}, skipped: {total_skipped:,}")
    return {"total_inserted": total_inserted, "total_skipped": total_skipped,
            "by_tier": tier_counts}


# ---------------------------------------------------------------------------
# Miss analyser
# ---------------------------------------------------------------------------

def analyse_misses(db_path: str = DEFAULT_DB_PATH, tier: str = None,
                   min_count: int = 3) -> dict:
    """
    Analyse miss patterns from prediction_result_memory.

    Primary directive: understand where and why the engine is wrong.

    Returns structured analysis per tier with:
    - Miss type frequencies
    - Miss rate by confidence band (high-confidence misses are the most interesting)
    - Closing line alignment on misses (did market know before us?)
    - Chaos tier breakdown of misses
    - Most common miss scorelines
    """
    conn = get_conn(db_path)
    ensure_table(conn)

    where = "WHERE actual IS NOT NULL"
    params = []
    if tier:
        where += " AND tier = ?"
        params.append(tier)

    df = pd.read_sql_query(
        f"SELECT * FROM prediction_result_memory {where}", conn, params=params)
    conn.close()

    if df.empty:
        logger.info("No completed predictions found in memory.")
        return {}

    results = {}
    tiers = [tier] if tier else sorted(df["tier"].unique())

    for t in tiers:
        dt = df[df["tier"] == t].copy()
        total = len(dt)
        correct = dt["correct"].sum()
        misses = dt[dt["correct"] == 0].copy()
        n_miss = len(misses)

        if total == 0:
            continue

        acc = correct / total

        # Miss type frequencies
        miss_types = misses["miss_type"].value_counts().to_dict() if n_miss > 0 else {}

        # Miss rate by confidence band
        conf_band_analysis = {}
        for band in ["high", "mid", "low"]:
            band_all = dt[dt["confidence_band"] == band]
            band_miss = misses[misses["confidence_band"] == band]
            if len(band_all) > 0:
                conf_band_analysis[band] = {
                    "total": len(band_all),
                    "misses": len(band_miss),
                    "miss_rate": round(len(band_miss) / len(band_all), 3),
                }

        # High-confidence misses — most important signal
        high_conf_misses = misses[misses["confidence_band"] == "high"]
        hcm_types = high_conf_misses["miss_type"].value_counts().to_dict() if len(high_conf_misses) > 0 else {}

        # Closing line alignment on misses
        cl_on_misses = misses["closing_line_signal"].value_counts().to_dict() if n_miss > 0 else {}

        # Market agreement on misses
        if n_miss > 0 and "market_agreed" in misses.columns:
            mkt_agreed_misses = misses["market_agreed"].sum()
            mkt_agreement_miss_rate = mkt_agreed_misses / n_miss if n_miss > 0 else None
        else:
            mkt_agreement_miss_rate = None

        # Chaos tier breakdown
        chaos_breakdown = {}
        for chaos in ["LOW", "MED", "HIGH"]:
            chaos_all = dt[dt["chaos_tier"] == chaos]
            chaos_miss = misses[misses["chaos_tier"] == chaos]
            if len(chaos_all) > 0:
                chaos_breakdown[chaos] = {
                    "total": len(chaos_all),
                    "misses": len(chaos_miss),
                    "miss_rate": round(len(chaos_miss) / len(chaos_all), 3),
                }

        # Actual scorelines on misses (what actually happened)
        actual_on_misses = misses["actual"].value_counts().to_dict() if n_miss > 0 else {}

        results[t] = {
            "tier": t,
            "total_predictions": total,
            "correct": int(correct),
            "misses": n_miss,
            "accuracy": round(acc, 4),
            "miss_types": miss_types,
            "high_confidence_misses": {
                "count": len(high_conf_misses),
                "types": hcm_types,
            },
            "miss_rate_by_confidence": conf_band_analysis,
            "closing_line_on_misses": cl_on_misses,
            "market_agreed_on_misses": round(mkt_agreement_miss_rate, 3) if mkt_agreement_miss_rate is not None else None,
            "chaos_breakdown": chaos_breakdown,
            "actual_outcome_on_misses": actual_on_misses,
        }

        # Print report
        _print_tier_report(results[t])

    return results


def _print_tier_report(r: dict):
    t = r["tier"]
    print(f"\n{'='*60}")
    print(f"  TEACHER ANALYSIS — {t}")
    print(f"{'='*60}")
    print(f"  Total predictions : {r['total_predictions']:,}")
    print(f"  Correct           : {r['correct']:,} ({r['accuracy']:.1%})")
    print(f"  Misses            : {r['misses']:,}")

    if r["miss_types"]:
        print(f"\n  MISS TYPES (what we said → what happened):")
        for mt, cnt in sorted(r["miss_types"].items(), key=lambda x: -x[1]):
            print(f"    {mt:<35} {cnt:>5}")

    hcm = r["high_confidence_misses"]
    if hcm["count"] > 0:
        print(f"\n  HIGH-CONFIDENCE MISSES ({hcm['count']} — PRIMARY SIGNAL):")
        for mt, cnt in sorted(hcm["types"].items(), key=lambda x: -x[1]):
            print(f"    {mt:<35} {cnt:>5}")

    if r["miss_rate_by_confidence"]:
        print(f"\n  MISS RATE BY CONFIDENCE BAND:")
        for band, data in r["miss_rate_by_confidence"].items():
            print(f"    {band:<6} {data['misses']}/{data['total']} = {data['miss_rate']:.1%}")

    if r["closing_line_on_misses"]:
        print(f"\n  CLOSING LINE ON MISSES:")
        for sig, cnt in sorted(r["closing_line_on_misses"].items(), key=lambda x: -x[1]):
            print(f"    {sig:<30} {cnt:>5}")

    if r["market_agreed_on_misses"] is not None:
        print(f"\n  Market agreed with us on misses: {r['market_agreed_on_misses']:.1%}")

    if r["chaos_breakdown"]:
        print(f"\n  CHAOS TIER BREAKDOWN:")
        for chaos, data in r["chaos_breakdown"].items():
            print(f"    {chaos:<5} {data['misses']}/{data['total']} miss rate {data['miss_rate']:.1%}")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_summary(db_path: str = DEFAULT_DB_PATH):
    """Quick summary of what's in prediction_result_memory."""
    conn = get_conn(db_path)
    ensure_table(conn)

    total = conn.execute("SELECT COUNT(*) FROM prediction_result_memory").fetchone()[0]
    completed = conn.execute(
        "SELECT COUNT(*) FROM prediction_result_memory WHERE actual IS NOT NULL").fetchone()[0]
    correct = conn.execute(
        "SELECT SUM(correct) FROM prediction_result_memory WHERE actual IS NOT NULL").fetchone()[0] or 0
    historical = conn.execute(
        "SELECT COUNT(*) FROM prediction_result_memory WHERE source='historical_seed'").fetchone()[0]
    live = conn.execute(
        "SELECT COUNT(*) FROM prediction_result_memory WHERE source='live_record'").fetchone()[0]

    print(f"\n{'='*50}")
    print(f"  PREDICTION RESULT MEMORY — SUMMARY")
    print(f"{'='*50}")
    print(f"  Total records     : {total:,}")
    print(f"  Completed         : {completed:,}")
    print(f"  Overall accuracy  : {correct/completed:.1%}" if completed > 0 else "  No completed records yet")
    print(f"  Historical seed   : {historical:,}")
    print(f"  Live records      : {live:,}")

    rows = conn.execute("""
        SELECT tier,
               COUNT(*) as n,
               SUM(correct) as c,
               SUM(CASE WHEN actual IS NOT NULL THEN 1 ELSE 0 END) as done
        FROM prediction_result_memory
        GROUP BY tier ORDER BY tier
    """).fetchall()

    if rows:
        print(f"\n  BY TIER:")
        print(f"  {'Tier':<6} {'Total':>7} {'Done':>7} {'Correct':>9} {'Acc':>7}")
        print(f"  {'-'*40}")
        for row in rows:
            acc = f"{row['c']/row['done']:.1%}" if row['done'] > 0 else "—"
            print(f"  {row['tier']:<6} {row['n']:>7,} {row['done']:>7,} {row['c']:>9,} {acc:>7}")

    conn.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_float(val) -> Optional[float]:
    try:
        f = float(val)
        return f if not (f != f) else None  # NaN check
    except (TypeError, ValueError):
        return None


def _int_or_none(val) -> Optional[int]:
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return None


def _lp_obj_to_engine_params(lp):
    """Convert a LeagueParams object directly to EngineParams."""
    from edgelab_engine import EngineParams
    return EngineParams(
        w_form=getattr(lp, "w_form", 1.0),
        w_gd=getattr(lp, "w_gd", 0.3),
        home_adv=getattr(lp, "home_adv", 0.25),
        dti_edge_scale=getattr(lp, "dti_edge_scale", 0.4),
        dti_ha_scale=getattr(lp, "dti_ha_scale", 0.5),
        draw_margin=getattr(lp, "draw_margin", 0.15),
        coin_dti_thresh=getattr(lp, "coin_dti_thresh", 0.7),
        draw_pull=getattr(lp, "draw_pull", 0.08),
        dti_draw_lock=getattr(lp, "dti_draw_lock", 0.85),
        w_draw_odds=getattr(lp, "w_draw_odds", 0.0),
        w_draw_tendency=getattr(lp, "w_draw_tendency", 0.0),
        w_h2h_draw=getattr(lp, "w_h2h_draw", 0.0),
        draw_score_thresh=getattr(lp, "draw_score_thresh", 0.55),
        w_score_margin=getattr(lp, "w_score_margin", 0.0),
        w_btts=getattr(lp, "w_btts", 0.0),
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


def _lp_dict_to_engine_params(lp: dict):
    """Convert a loaded params dict to EngineParams."""
    from edgelab_engine import EngineParams
    return EngineParams(
        w_form=lp.get("w_form", 1.0),
        w_gd=lp.get("w_gd", 0.3),
        home_adv=lp.get("home_adv", 0.25),
        dti_edge_scale=lp.get("dti_edge_scale", 0.4),
        dti_ha_scale=lp.get("dti_ha_scale", 0.5),
        draw_margin=lp.get("draw_margin", 0.15),
        coin_dti_thresh=lp.get("coin_dti_thresh", 0.7),
        draw_pull=lp.get("draw_pull", 0.08),
        dti_draw_lock=lp.get("dti_draw_lock", 0.85),
        w_draw_odds=lp.get("w_draw_odds", 0.0),
        w_draw_tendency=lp.get("w_draw_tendency", 0.0),
        w_h2h_draw=lp.get("w_h2h_draw", 0.0),
        draw_score_thresh=lp.get("draw_score_thresh", 0.55),
        w_score_margin=lp.get("w_score_margin", 0.0),
        w_btts=lp.get("w_btts", 0.0),
        w_xg_draw=lp.get("w_xg_draw", 0.0),
        composite_draw_boost=lp.get("composite_draw_boost", 0.0),
        w_ref_signal=lp.get("w_ref_signal", 0.0),
        w_travel_load=lp.get("w_travel_load", 0.0),
        w_timing_signal=lp.get("w_timing_signal", 0.0),
        w_motivation_gap=lp.get("w_motivation_gap", 0.0),
        w_weather_signal=lp.get("w_weather_signal", 0.0),
        w_venue_form=lp.get("w_venue_form", 0.0),
        w_team_home_adv=lp.get("w_team_home_adv", 0.0),
        w_away_team_adv=lp.get("w_away_team_adv", 0.0),
        w_opp_strength=lp.get("w_opp_strength", 0.0),
        w_season_stage=lp.get("w_season_stage", 0.0),
        w_rest_diff=lp.get("w_rest_diff", 0.0),
        w_scoreline_agreement=lp.get("w_scoreline_agreement", 0.0),
        w_scoreline_confidence=lp.get("w_scoreline_confidence", 0.0),
        form_window=5,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="EdgeLab Teacher Layer — prediction result recorder and miss analyser"
    )
    parser.add_argument("--db", default=DEFAULT_DB_PATH,
                        help="Path to edgelab.db (default: auto-detect)")
    parser.add_argument("--seed", metavar="HISTORY_FOLDER",
                        help="Seed from historical CSVs folder")
    parser.add_argument("--tier", nargs="+",
                        help="Filter to specific tier(s) (used with --seed or --analyse)")
    parser.add_argument("--record", metavar="PREDICTIONS_CSV",
                        help="Record results. Requires --results.")
    parser.add_argument("--results", metavar="RESULTS_CSV",
                        help="Results CSV (output of edgelab_results_check.py)")
    parser.add_argument("--analyse", action="store_true",
                        help="Run miss analysis")
    parser.add_argument("--summary", action="store_true",
                        help="Print summary of prediction_result_memory table")
    parser.add_argument("--min-count", type=int, default=3,
                        help="Minimum count to show in analysis (default: 3)")

    args = parser.parse_args()

    if args.seed:
        tiers = args.tier if args.tier else None
        seed_from_history(args.seed, db_path=args.db, tiers=tiers)

    elif args.record:
        if not args.results:
            parser.error("--record requires --results")
        record_results(args.record, args.results, db_path=args.db)

    elif args.analyse:
        tier = args.tier[0] if args.tier and len(args.tier) == 1 else None
        analyse_misses(db_path=args.db, tier=tier, min_count=args.min_count)

    elif args.summary:
        print_summary(db_path=args.db)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
