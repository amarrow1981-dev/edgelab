#!/usr/bin/env python3
"""
EdgeLab Fixture Intelligence Database
--------------------------------------
The foundational learning layer for EdgeLab.

Every fixture ever processed lives here. Every DPOL candidate ever tested
lives here. This is the 3D map — the accumulated knowledge that makes DPOL
a learning system rather than a repeating optimiser.

THREE TABLES:

  fixtures
    One row per match. Written at prediction time (pre-match features +
    engine output). Completed when the result comes in (actual result,
    correct/wrong). This is the coordinate cloud — every point in the space.

  param_versions
    Every set of params that has ever been active, per tier. Versioned so
    fixture records know exactly what was running when they were predicted.
    Allows the cloud to be filtered and coloured by param version.

  dpol_candidate_log
    Every candidate tested in every evolution round. The trail DPOL has
    walked through param space. What was tried, what was accepted, what
    was rejected. This is what stops DPOL walking the same ground forever.

DESIGN PRINCIPLES:

  - Append-only for fixture records. Pre-match written at prediction time,
    post-match written when result comes in. History is immutable.
  - Versioned params. Every fixture knows which param version predicted it.
  - SQLite now, PostgreSQL when scaling to live product. Same schema,
    same queries, different engine. Migration is one afternoon's work.
  - Sport-agnostic structure. This is the football instance of the
    repeatable framework. Cricket, NBA etc get their own database built
    on the same blueprint.

Usage:
    from edgelab_db import EdgeLabDB

    db = EdgeLabDB()  # creates edgelab.db in current directory

    # Write a param version
    version_id = db.save_param_version(tier="E0", params=lp, accuracy=0.507,
                                        matches=8669, source="threepass_seed_s28")

    # Write a fixture at prediction time
    db.write_fixture_prematch(fixture_id="E0_20260409_Arsenal_Chelsea",
                               tier="E0", season="2025-26", ...)

    # Complete a fixture when result comes in
    db.complete_fixture(fixture_id=..., actual_result="H",
                        actual_home_goals=2, actual_away_goals=1)

    # Log a DPOL candidate evaluation
    db.log_dpol_candidate(tier="E0", season="2025-26", round=18,
                           params=candidate_params, window_accuracy=0.512,
                           global_accuracy=0.509, accepted=True, ...)

    # Query: find similar historical fixtures (nearest-neighbour for Gary/DPOL)
    similar = db.find_similar_fixtures(feature_vector={...}, n=200)

    # Query: what param directions have historically helped this tier?
    directions = db.get_successful_param_directions(tier="E0", top_n=10)
"""

import os
import sqlite3
import hashlib
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[EdgeLabDB] %(message)s")

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "edgelab.db")

# All param field names — single source of truth
PARAM_FIELDS = [
    "w_form", "w_gd", "home_adv", "dti_edge_scale", "dti_ha_scale",
    "draw_margin", "coin_dti_thresh", "draw_pull", "dti_draw_lock",
    "w_draw_odds", "w_draw_tendency", "w_h2h_draw", "draw_score_thresh",
    "w_score_margin", "w_btts", "w_xg_draw", "composite_draw_boost",
    "w_ref_signal", "w_travel_load", "w_timing_signal", "w_motivation_gap",
    "w_weather_signal",
]

# Pre-match feature fields stored per fixture
FEATURE_FIELDS = [
    "home_form", "away_form", "home_gd", "away_gd",
    "dti", "chaos_tier",
    "odds_draw_prob", "h2h_draw_rate", "h2h_home_edge",
    "pred_margin", "pred_home_goals", "pred_away_goals",
    "btts_prob", "btts_flag",
    "upset_score", "upset_flag",
    "draw_score",
    "weather_load", "travel_load", "motivation_gap", "timing_signal",
    "ref_signal",
]


# ---------------------------------------------------------------------------
# Database class
# ---------------------------------------------------------------------------

class EdgeLabDB:
    """
    Single access point for the EdgeLab fixture intelligence database.
    All reads and writes go through this class.
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._init_db()

    # -----------------------------------------------------------------------
    # Initialisation
    # -----------------------------------------------------------------------

    def _init_db(self):
        """Create tables if they don't exist. Safe to call on every startup."""
        with self._conn() as conn:
            self._create_tables(conn)
        logger.info(f"Database ready: {self.db_path}")

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row   # rows accessible by column name
        conn.execute("PRAGMA journal_mode=WAL")   # safe concurrent writes
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _migrate_schema(self, conn: sqlite3.Connection):
        """
        Add any missing columns to existing tables.
        Safe to run on any existing database — skips columns that already exist.
        This means you never need to delete edgelab.db when we add new columns.
        """
        # Get existing columns for each table
        def existing_cols(table):
            try:
                rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
                return {row[1] for row in rows}
            except Exception:
                return set()

        pv_cols = existing_cols("param_versions")
        fx_cols = existing_cols("fixtures")
        cl_cols = existing_cols("dpol_candidate_log")

        # Add missing param columns to param_versions
        for p in PARAM_FIELDS:
            if p not in pv_cols and pv_cols:  # only if table exists
                try:
                    conn.execute(f"ALTER TABLE param_versions ADD COLUMN {p} REAL")
                    logger.info(f"Migration: added param_versions.{p}")
                except Exception:
                    pass

        # Add missing feature columns to fixtures
        for f in FEATURE_FIELDS:
            if f not in fx_cols and fx_cols:
                col_type = "TEXT" if f == "chaos_tier" else "REAL"
                try:
                    conn.execute(f"ALTER TABLE fixtures ADD COLUMN {f} {col_type}")
                    logger.info(f"Migration: added fixtures.{f}")
                except Exception:
                    pass

        # Add missing param columns to dpol_candidate_log
        for p in PARAM_FIELDS:
            pname = f"p_{p}"
            if pname not in cl_cols and cl_cols:
                try:
                    conn.execute(f"ALTER TABLE dpol_candidate_log ADD COLUMN {pname} REAL")
                    logger.info(f"Migration: added dpol_candidate_log.{pname}")
                except Exception:
                    pass

        conn.commit()

    def _create_tables(self, conn: sqlite3.Connection):
        """Create all three tables. Idempotent — safe to run on existing db."""

        # Run migrations first — adds missing columns to any existing tables
        self._migrate_schema(conn)

        # ── param_versions ──────────────────────────────────────────────────
        param_cols = "\n    ".join(f"{p}  REAL" for p in PARAM_FIELDS)
        conn.execute(f"""
        CREATE TABLE IF NOT EXISTS param_versions (
            version_id          TEXT PRIMARY KEY,
            tier                TEXT NOT NULL,
            source              TEXT NOT NULL,
            created_at          TIMESTAMP NOT NULL,
            accuracy            REAL,
            matches_validated   INTEGER,
            {param_cols}
        )
        """)

        # ── fixtures ────────────────────────────────────────────────────────
        feature_cols = "\n    ".join(f"{f}  REAL" for f in FEATURE_FIELDS
                                     if f != "chaos_tier")
        conn.execute(f"""
        CREATE TABLE IF NOT EXISTS fixtures (
            fixture_id          TEXT PRIMARY KEY,
            tier                TEXT NOT NULL,
            season              TEXT NOT NULL,
            match_date          TEXT NOT NULL,
            home_team           TEXT NOT NULL,
            away_team           TEXT NOT NULL,

            -- Param version active at prediction time
            param_version_id    TEXT REFERENCES param_versions(version_id),

            -- Engine output
            prediction          TEXT,
            confidence          REAL,
            pred_scoreline      TEXT,
            draw_score          REAL,

            -- Pre-match features
            chaos_tier          TEXT,
            {feature_cols},

            -- Post-match completion
            actual_result       TEXT,
            actual_home_goals   INTEGER,
            actual_away_goals   INTEGER,
            correct             INTEGER,
            completed_at        TIMESTAMP,

            -- Metadata
            created_at          TIMESTAMP NOT NULL,
            data_source         TEXT NOT NULL
        )
        """)

        # ── dpol_candidate_log ───────────────────────────────────────────────
        candidate_param_cols = "\n    ".join(f"p_{p}  REAL" for p in PARAM_FIELDS)
        conn.execute(f"""
        CREATE TABLE IF NOT EXISTS dpol_candidate_log (
            log_id              INTEGER PRIMARY KEY AUTOINCREMENT,
            tier                TEXT NOT NULL,
            season              TEXT NOT NULL,
            round               INTEGER NOT NULL,
            evaluated_at        TIMESTAMP NOT NULL,

            -- Candidate params tested (prefixed p_ to avoid SQL keyword clashes)
            {candidate_param_cols},

            -- Result
            window_accuracy     REAL NOT NULL,
            global_accuracy     REAL,
            accepted            INTEGER NOT NULL DEFAULT 0,
            delta_vs_base       REAL,

            -- Context
            base_accuracy       REAL,
            param_version_id    TEXT REFERENCES param_versions(version_id)
        )
        """)

        # ── Indexes ──────────────────────────────────────────────────────────
        conn.execute("CREATE INDEX IF NOT EXISTS idx_fixtures_tier ON fixtures(tier)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_fixtures_date ON fixtures(match_date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_fixtures_season ON fixtures(tier, season)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_fixtures_completed ON fixtures(completed_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_candidate_tier ON dpol_candidate_log(tier)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_candidate_season ON dpol_candidate_log(tier, season)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_param_versions_tier ON param_versions(tier)")

        conn.commit()

    # -----------------------------------------------------------------------
    # Param versions
    # -----------------------------------------------------------------------

    def save_param_version(
        self,
        tier: str,
        params,            # LeagueParams or dict
        accuracy: float,
        matches: int,
        source: str,
    ) -> str:
        """
        Save a param version. Returns the version_id.
        Safe to call multiple times — same params + source + tier = same ID.
        """
        params_dict = _params_to_dict(params)
        version_id = _make_version_id(tier, source, params_dict)

        with self._conn() as conn:
            existing = conn.execute(
                "SELECT version_id FROM param_versions WHERE version_id = ?",
                (version_id,)
            ).fetchone()

            if not existing:
                cols = ["version_id", "tier", "source", "created_at",
                        "accuracy", "matches_validated"] + PARAM_FIELDS
                vals = [version_id, tier, source,
                        datetime.utcnow().isoformat(),
                        round(accuracy, 6), matches] + [
                    params_dict.get(p, 0.0) for p in PARAM_FIELDS
                ]
                placeholders = ",".join("?" * len(cols))
                col_str = ",".join(cols)
                conn.execute(
                    f"INSERT INTO param_versions ({col_str}) VALUES ({placeholders})",
                    vals
                )
                conn.commit()
                logger.info(f"Param version saved: {version_id} ({tier}, {source}, {accuracy:.1%})")
            else:
                logger.info(f"Param version already exists: {version_id}")

        return version_id

    def get_param_version(self, version_id: str) -> Optional[Dict]:
        """Load a param version by ID."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM param_versions WHERE version_id = ?",
                (version_id,)
            ).fetchone()
        return dict(row) if row else None

    def get_latest_param_version(self, tier: str) -> Optional[Dict]:
        """Get the most recently saved param version for a tier."""
        with self._conn() as conn:
            row = conn.execute(
                """SELECT * FROM param_versions
                   WHERE tier = ?
                   ORDER BY created_at DESC LIMIT 1""",
                (tier,)
            ).fetchone()
        return dict(row) if row else None

    # -----------------------------------------------------------------------
    # Fixtures — pre-match write
    # -----------------------------------------------------------------------

    def write_fixture_prematch(
        self,
        tier: str,
        season: str,
        match_date: str,
        home_team: str,
        away_team: str,
        prediction: str,
        confidence: float,
        pred_scoreline: str,
        features: Dict[str, Any],
        param_version_id: Optional[str] = None,
        data_source: str = "databot_live",
    ) -> str:
        """
        Write a fixture record at prediction time.
        Returns the fixture_id.
        Post-match completion added later via complete_fixture().
        """
        fixture_id = _make_fixture_id(tier, match_date, home_team, away_team)

        with self._conn() as conn:
            existing = conn.execute(
                "SELECT fixture_id FROM fixtures WHERE fixture_id = ?",
                (fixture_id,)
            ).fetchone()

            if existing:
                logger.info(f"Fixture already exists: {fixture_id} — skipping")
                return fixture_id

            # Base columns
            base_cols = [
                "fixture_id", "tier", "season", "match_date",
                "home_team", "away_team", "param_version_id",
                "prediction", "confidence", "pred_scoreline",
                "created_at", "data_source",
            ]
            base_vals = [
                fixture_id, tier, season, match_date,
                home_team, away_team, param_version_id,
                prediction, round(confidence, 4), pred_scoreline,
                datetime.utcnow().isoformat(), data_source,
            ]

            # Feature columns — chaos_tier is TEXT, rest are REAL
            feature_cols = []
            feature_vals = []
            for f in FEATURE_FIELDS:
                val = features.get(f)
                feature_cols.append(f)
                feature_vals.append(val)

            # draw_score separately (engine output, not a feature)
            draw_score = features.get("draw_score")

            all_cols = base_cols + ["draw_score"] + feature_cols
            all_vals = base_vals + [draw_score] + feature_vals

            placeholders = ",".join("?" * len(all_cols))
            col_str = ",".join(all_cols)
            conn.execute(
                f"INSERT INTO fixtures ({col_str}) VALUES ({placeholders})",
                all_vals
            )
            conn.commit()

        logger.info(f"Fixture written: {fixture_id} → {prediction} ({confidence:.0%})")
        return fixture_id

    # -----------------------------------------------------------------------
    # Fixtures — post-match completion
    # -----------------------------------------------------------------------

    def complete_fixture(
        self,
        fixture_id: str,
        actual_result: str,
        actual_home_goals: int,
        actual_away_goals: int,
    ) -> bool:
        """
        Complete a fixture record when the result comes in.
        Writes actual result and whether the prediction was correct.
        Returns True if updated, False if fixture not found.
        """
        with self._conn() as conn:
            row = conn.execute(
                "SELECT prediction, completed_at FROM fixtures WHERE fixture_id = ?",
                (fixture_id,)
            ).fetchone()

            if not row:
                logger.warning(f"Fixture not found for completion: {fixture_id}")
                return False

            if row["completed_at"]:
                logger.info(f"Fixture already completed: {fixture_id}")
                return True

            correct = 1 if row["prediction"] == actual_result else 0

            conn.execute(
                """UPDATE fixtures
                   SET actual_result = ?,
                       actual_home_goals = ?,
                       actual_away_goals = ?,
                       correct = ?,
                       completed_at = ?
                   WHERE fixture_id = ?""",
                (actual_result, actual_home_goals, actual_away_goals,
                 correct, datetime.utcnow().isoformat(), fixture_id)
            )
            conn.commit()

        result_str = "✓" if correct else "✗"
        logger.info(f"Fixture completed: {fixture_id} → {actual_result} {result_str}")
        return True

    def complete_fixture_by_teams(
        self,
        tier: str,
        match_date: str,
        home_team: str,
        away_team: str,
        actual_result: str,
        actual_home_goals: int,
        actual_away_goals: int,
    ) -> bool:
        """Complete a fixture by team names rather than fixture_id."""
        fixture_id = _make_fixture_id(tier, match_date, home_team, away_team)
        return self.complete_fixture(
            fixture_id, actual_result, actual_home_goals, actual_away_goals
        )

    # -----------------------------------------------------------------------
    # DPOL candidate log
    # -----------------------------------------------------------------------

    def log_dpol_candidate(
        self,
        tier: str,
        season: str,
        round_num: int,
        params,
        window_accuracy: float,
        global_accuracy: Optional[float],
        accepted: bool,
        base_accuracy: float,
        param_version_id: Optional[str] = None,
    ) -> int:
        """
        Log a DPOL candidate evaluation.
        Returns the log_id of the inserted row.
        """
        params_dict = _params_to_dict(params)
        delta = window_accuracy - base_accuracy

        param_cols = [f"p_{p}" for p in PARAM_FIELDS]
        param_vals = [params_dict.get(p, 0.0) for p in PARAM_FIELDS]

        base_cols = [
            "tier", "season", "round", "evaluated_at",
            "window_accuracy", "global_accuracy", "accepted",
            "delta_vs_base", "base_accuracy", "param_version_id",
        ]
        base_vals = [
            tier, season, round_num, datetime.utcnow().isoformat(),
            round(window_accuracy, 6),
            round(global_accuracy, 6) if global_accuracy is not None else None,
            1 if accepted else 0,
            round(delta, 6), round(base_accuracy, 6),
            param_version_id,
        ]

        all_cols = base_cols + param_cols
        all_vals = base_vals + param_vals
        placeholders = ",".join("?" * len(all_cols))
        col_str = ",".join(all_cols)

        with self._conn() as conn:
            cursor = conn.execute(
                f"INSERT INTO dpol_candidate_log ({col_str}) VALUES ({placeholders})",
                all_vals
            )
            conn.commit()
            return cursor.lastrowid

    # -----------------------------------------------------------------------
    # Queries — DPOL intelligence
    # -----------------------------------------------------------------------

    def get_successful_param_directions(
        self,
        tier: str,
        top_n: int = 10,
        min_delta: float = 0.001,
    ) -> List[Dict]:
        """
        For a given tier, find which param changes have historically
        improved accuracy the most when accepted by DPOL.

        Returns a list of dicts:
            {
                param:       str,   — param name e.g. "w_form"
                direction:   str,   — "up" | "down" | "mixed"
                avg_delta:   float, — mean accuracy gain across accepted moves
                avg_signed_move: float, — mean signed change (candidate - base)
                count:       int,   — number of accepted moves for this param
            }

        Direction is computed properly: for each accepted candidate we
        join to param_versions to get the base param value that was
        active at the time, then compute (candidate_value - base_value).
        Positive = moving up helped. Negative = moving down helped.
        "mixed" means both directions helped across different rounds.

        This is what DPOL reads to bias its candidate generation —
        stop wandering, start navigating.
        """
        # Fetch all accepted candidates for this tier with sufficient delta,
        # joined to the param_version that was active when they were tested.
        # The JOIN gives us the base param values so we can compute direction.
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT cl.*, pv.{param_cols}
                   FROM dpol_candidate_log cl
                   LEFT JOIN param_versions pv
                       ON cl.param_version_id = pv.version_id
                   WHERE cl.tier = ?
                     AND cl.accepted = 1
                     AND cl.delta_vs_base >= ?
                   ORDER BY cl.delta_vs_base DESC""".format(
                    param_cols=", ".join(f"pv.{p} AS base_{p}" for p in PARAM_FIELDS)
                ),
                (tier, min_delta)
            ).fetchall()

        if not rows:
            return []

        # For each param, collect signed moves across all accepted candidates.
        # signed_move = candidate_value - base_value
        # weighted by delta_vs_base so bigger improvements carry more signal.
        results = []
        for p in PARAM_FIELDS:
            signed_moves = []   # (signed_move, delta_vs_base)

            for row in rows:
                candidate_val = row[f"p_{p}"]
                base_val = row[f"base_{p}"]
                delta = row["delta_vs_base"]

                # Skip rows where either value is missing
                # (param_version_id not set — older log entries pre-S29)
                if candidate_val is None or base_val is None:
                    continue

                signed_move = candidate_val - base_val

                # Only count moves where the param actually changed
                # (ignore candidates that happened to leave this param untouched)
                if abs(signed_move) < 1e-9:
                    continue

                signed_moves.append((signed_move, delta))

            if not signed_moves:
                continue

            # Weighted average signed move (weight = delta_vs_base)
            total_weight = sum(d for _, d in signed_moves)
            if total_weight <= 0:
                continue

            avg_signed = sum(m * d for m, d in signed_moves) / total_weight
            avg_delta = sum(d for _, d in signed_moves) / len(signed_moves)

            if avg_delta < min_delta:
                continue

            # Direction: consistent if avg_signed clearly positive or negative.
            # "mixed" if the signal is weak (competing moves roughly cancel out).
            DIRECTION_THRESHOLD = 0.1  # avg signed move must be at least 10% of step
            if avg_signed > DIRECTION_THRESHOLD:
                direction = "up"
            elif avg_signed < -DIRECTION_THRESHOLD:
                direction = "down"
            else:
                direction = "mixed"

            results.append({
                "param":            p,
                "direction":        direction,
                "avg_delta":        round(avg_delta, 4),
                "avg_signed_move":  round(avg_signed, 4),
                "count":            len(signed_moves),
            })

        # Sort by avg_delta descending — strongest proven movers first
        results.sort(key=lambda x: x["avg_delta"], reverse=True)
        return results[:top_n]

    def find_similar_fixtures(
        self,
        feature_vector: Dict[str, float],
        tier: Optional[str] = None,
        n: int = 200,
        completed_only: bool = True,
    ) -> List[Dict]:
        """
        Find the N most similar historical fixtures to a given feature vector.
        Uses Euclidean distance across the numeric feature space.

        This is the nearest-neighbour lookup for Gary and DPOL.
        Gary calls this to get pattern memory.
        DPOL calls this to find historical fixtures with similar conditions.

        Args:
            feature_vector: dict of feature_name -> value for the target fixture
            tier:           optional — restrict to same tier
            n:              how many similar fixtures to return
            completed_only: only return fixtures with known outcomes

        Returns:
            List of fixture dicts sorted by similarity (closest first),
            each including distance, actual_result, prediction, correct.
        """
        where_clauses = []
        params = []

        if completed_only:
            where_clauses.append("completed_at IS NOT NULL")
        if tier:
            where_clauses.append("tier = ?")
            params.append(tier)

        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        with self._conn() as conn:
            rows = conn.execute(
                f"SELECT * FROM fixtures {where_sql}",
                params
            ).fetchall()

        if not rows:
            return []

        # Numeric features to use for distance calculation
        distance_features = [
            f for f in FEATURE_FIELDS
            if f not in ("chaos_tier",) and feature_vector.get(f) is not None
        ]

        results = []
        target = [feature_vector.get(f, 0.0) or 0.0 for f in distance_features]

        for row in rows:
            row_dict = dict(row)
            candidate = [row_dict.get(f, 0.0) or 0.0 for f in distance_features]

            # Euclidean distance
            dist = sum((a - b) ** 2 for a, b in zip(target, candidate)) ** 0.5
            row_dict["_distance"] = round(dist, 4)
            results.append(row_dict)

        results.sort(key=lambda x: x["_distance"])
        return results[:n]

    def get_outcome_distribution(
        self,
        similar_fixtures: List[Dict],
    ) -> Dict:
        """
        Given a list of similar fixtures (from find_similar_fixtures),
        return the outcome distribution.

        Gary reads this: "In the 200 most similar historical fixtures,
        Home won 44%, Draw 28%, Away won 28%."
        """
        if not similar_fixtures:
            return {"H": 0, "D": 0, "A": 0, "total": 0}

        counts = {"H": 0, "D": 0, "A": 0}
        for f in similar_fixtures:
            result = f.get("actual_result")
            if result in counts:
                counts[result] += 1

        total = sum(counts.values())
        return {
            "H": counts["H"],
            "D": counts["D"],
            "A": counts["A"],
            "total": total,
            "H_pct": round(counts["H"] / total, 3) if total else 0,
            "D_pct": round(counts["D"] / total, 3) if total else 0,
            "A_pct": round(counts["A"] / total, 3) if total else 0,
        }

    # -----------------------------------------------------------------------
    # Queries — reporting and status
    # -----------------------------------------------------------------------

    def get_stats(self) -> Dict:
        """Quick database health check — row counts and completion rates."""
        with self._conn() as conn:
            n_fixtures = conn.execute("SELECT COUNT(*) FROM fixtures").fetchone()[0]
            n_completed = conn.execute(
                "SELECT COUNT(*) FROM fixtures WHERE completed_at IS NOT NULL"
            ).fetchone()[0]
            n_correct = conn.execute(
                "SELECT COUNT(*) FROM fixtures WHERE correct = 1"
            ).fetchone()[0]
            n_candidates = conn.execute(
                "SELECT COUNT(*) FROM dpol_candidate_log"
            ).fetchone()[0]
            n_accepted = conn.execute(
                "SELECT COUNT(*) FROM dpol_candidate_log WHERE accepted = 1"
            ).fetchone()[0]
            n_param_versions = conn.execute(
                "SELECT COUNT(*) FROM param_versions"
            ).fetchone()[0]
            tiers = conn.execute(
                "SELECT DISTINCT tier FROM fixtures ORDER BY tier"
            ).fetchall()

        accuracy = round(n_correct / n_completed, 4) if n_completed else 0

        return {
            "fixtures": {
                "total": n_fixtures,
                "completed": n_completed,
                "pending": n_fixtures - n_completed,
                "accuracy": accuracy,
            },
            "dpol_log": {
                "total_candidates": n_candidates,
                "accepted": n_accepted,
                "rejected": n_candidates - n_accepted,
            },
            "param_versions": n_param_versions,
            "tiers": [r[0] for r in tiers],
        }

    def get_tier_stats(self) -> List[Dict]:
        """Per-tier breakdown of fixture counts and accuracy."""
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT tier,
                          COUNT(*) as total,
                          SUM(CASE WHEN completed_at IS NOT NULL THEN 1 ELSE 0 END) as completed,
                          SUM(CASE WHEN correct = 1 THEN 1 ELSE 0 END) as correct
                   FROM fixtures
                   GROUP BY tier
                   ORDER BY tier"""
            ).fetchall()

        results = []
        for row in rows:
            completed = row["completed"]
            correct = row["correct"]
            acc = round(correct / completed, 4) if completed else None
            results.append({
                "tier": row["tier"],
                "total": row["total"],
                "completed": completed,
                "accuracy": acc,
            })
        return results

    def fixture_exists(self, tier: str, match_date: str,
                       home_team: str, away_team: str) -> bool:
        """Check if a fixture is already in the database."""
        fixture_id = _make_fixture_id(tier, match_date, home_team, away_team)
        with self._conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM fixtures WHERE fixture_id = ?", (fixture_id,)
            ).fetchone()
        return row is not None

    # -----------------------------------------------------------------------
    # Bulk operations
    # -----------------------------------------------------------------------

    def bulk_write_fixtures(self, fixture_records: List[Dict]) -> int:
        """
        Write multiple fixture records in a single transaction.
        Used by the backfill script for performance.
        Returns number of records written.
        """
        written = 0
        with self._conn() as conn:
            for rec in fixture_records:
                fixture_id = _make_fixture_id(
                    rec["tier"], rec["match_date"],
                    rec["home_team"], rec["away_team"]
                )
                existing = conn.execute(
                    "SELECT 1 FROM fixtures WHERE fixture_id = ?", (fixture_id,)
                ).fetchone()
                if existing:
                    continue

                # Build insert
                base_cols = [
                    "fixture_id", "tier", "season", "match_date",
                    "home_team", "away_team", "param_version_id",
                    "prediction", "confidence", "pred_scoreline",
                    "draw_score", "actual_result", "actual_home_goals",
                    "actual_away_goals", "correct", "completed_at",
                    "created_at", "data_source",
                ]
                base_vals = [
                    fixture_id,
                    rec.get("tier"), rec.get("season"), rec.get("match_date"),
                    rec.get("home_team"), rec.get("away_team"),
                    rec.get("param_version_id"),
                    rec.get("prediction"), rec.get("confidence"),
                    rec.get("pred_scoreline"), rec.get("draw_score"),
                    rec.get("actual_result"), rec.get("actual_home_goals"),
                    rec.get("actual_away_goals"), rec.get("correct"),
                    rec.get("completed_at"),
                    datetime.utcnow().isoformat(),
                    rec.get("data_source", "csv_backfill"),
                ]

                feature_cols = list(FEATURE_FIELDS)
                feature_vals = [rec.get(f) for f in feature_cols]

                all_cols = base_cols + feature_cols
                all_vals = base_vals + feature_vals
                placeholders = ",".join("?" * len(all_cols))
                col_str = ",".join(all_cols)

                conn.execute(
                    f"INSERT INTO fixtures ({col_str}) VALUES ({placeholders})",
                    all_vals
                )
                written += 1

            conn.commit()

        return written


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _make_fixture_id(tier: str, match_date: str,
                     home_team: str, away_team: str) -> str:
    """
    Deterministic fixture ID from tier + date + teams.
    Same fixture always gets the same ID regardless of when it's processed.
    """
    raw = f"{tier}_{match_date}_{home_team}_{away_team}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def _make_version_id(tier: str, source: str, params_dict: Dict) -> str:
    """Deterministic param version ID."""
    key_params = {p: round(params_dict.get(p, 0.0), 6) for p in PARAM_FIELDS}
    raw = f"{tier}_{source}_{json.dumps(key_params, sort_keys=True)}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def _params_to_dict(params) -> Dict:
    """Convert LeagueParams or dict to plain dict."""
    if isinstance(params, dict):
        return params
    # LeagueParams dataclass
    try:
        from dataclasses import asdict
        return asdict(params)
    except Exception:
        return {p: getattr(params, p, 0.0) for p in PARAM_FIELDS}


# ---------------------------------------------------------------------------
# CLI — status check and basic queries
# ---------------------------------------------------------------------------

def main():
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="EdgeLab DB — status and queries")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="Path to database file")
    parser.add_argument("--stats", action="store_true", help="Show database stats")
    parser.add_argument("--tiers", action="store_true", help="Show per-tier breakdown")
    parser.add_argument("--similar", type=str, default=None,
                        help="Find similar fixtures to a tier (e.g. E0)")
    args = parser.parse_args()

    db = EdgeLabDB(db_path=args.db)

    if args.stats or (not args.tiers and not args.similar):
        stats = db.get_stats()
        print(f"\n{'='*55}")
        print(f"  EdgeLab Fixture Intelligence Database")
        print(f"  {args.db}")
        print(f"{'='*55}")
        print(f"\n  Fixtures:       {stats['fixtures']['total']:,} total")
        print(f"  Completed:      {stats['fixtures']['completed']:,}")
        print(f"  Pending:        {stats['fixtures']['pending']:,}")
        if stats['fixtures']['completed']:
            print(f"  Accuracy:       {stats['fixtures']['accuracy']:.1%}")
        print(f"\n  DPOL log:       {stats['dpol_log']['total_candidates']:,} candidates")
        print(f"  Accepted:       {stats['dpol_log']['accepted']:,}")
        print(f"  Param versions: {stats['param_versions']}")
        if stats['tiers']:
            print(f"\n  Tiers:          {', '.join(stats['tiers'])}")
        print()

    if args.tiers:
        tier_stats = db.get_tier_stats()
        print(f"\n  {'Tier':<6} {'Total':>8} {'Done':>8} {'Accuracy':>10}")
        print(f"  {'-'*35}")
        for t in tier_stats:
            acc = f"{t['accuracy']:.1%}" if t['accuracy'] else "—"
            print(f"  {t['tier']:<6} {t['total']:>8,} {t['completed']:>8,} {acc:>10}")
        print()


if __name__ == "__main__":
    main()
