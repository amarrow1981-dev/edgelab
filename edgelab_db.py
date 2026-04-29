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
    # Fixture Specificity Layer (Session 38)
    "w_venue_form", "w_team_home_adv", "w_away_team_adv", "w_opp_strength",
    "w_season_stage", "w_rest_diff",
    # Layer Agreement Layer (Session 41)
    "w_scoreline_agreement", "w_scoreline_confidence",
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
    # Fixture Specificity Layer (Session 38)
    "home_form_home", "away_form_away",       # venue-split form
    "home_adv_team", "away_adv_team",         # team-specific venue advantage
    "home_form_adj", "away_form_adj",          # opponent-adjusted form
    "season_stage",                            # season stage 0→1
    "home_rest_days", "away_rest_days", "rest_days_diff",  # rest days
]


# ---------------------------------------------------------------------------
# Database class
# ---------------------------------------------------------------------------

def _miss_type_to_param_hints(miss_type: str) -> list:
    """
    Translate a dominant miss type into param direction hints for DPOL.

    These are educated starting biases — not overrides. DPOL still evaluates
    each candidate against the loss function. If the hint is wrong for this
    tier's data, DPOL's global guard will reject it.

    Format: [{param, direction}] where direction is "up" or "down".
    """
    hints = {
        # Called H, was D — overcalling home wins as decisive
        # Fix: widen draw band, reduce home advantage weight
        "predicted_H_was_D": [
            {"param": "draw_margin",    "direction": "up"},
            {"param": "home_adv",       "direction": "down"},
        ],
        # Called H, was A — strongly overweighting home signals
        # Fix: reduce form and GD weight (they're noisy here), reduce home adv
        "predicted_H_was_A": [
            {"param": "w_form",         "direction": "down"},
            {"param": "w_gd",           "direction": "down"},
            {"param": "home_adv",       "direction": "down"},
        ],
        # Called A, was H — underweighting home advantage
        "predicted_A_was_H": [
            {"param": "home_adv",       "direction": "up"},
            {"param": "w_away_team_adv","direction": "down"},
        ],
        # Called A, was D — away calls that should have been draws
        "predicted_A_was_D": [
            {"param": "draw_margin",    "direction": "up"},
            {"param": "w_away_team_adv","direction": "down"},
        ],
        # Called D, was H — draw calls that should have been home wins
        "predicted_D_was_H": [
            {"param": "draw_margin",    "direction": "down"},
            {"param": "home_adv",       "direction": "up"},
        ],
        # Called D, was A — draw calls that should have been away wins
        "predicted_D_was_A": [
            {"param": "draw_margin",    "direction": "down"},
            {"param": "w_away_team_adv","direction": "up"},
        ],
    }
    return hints.get(miss_type, [])


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

        # Add actual_scoreline column for scoreline map logging
        if "actual_scoreline" not in fx_cols and fx_cols:
            try:
                conn.execute("ALTER TABLE fixtures ADD COLUMN actual_scoreline TEXT")
                logger.info("Migration: added fixtures.actual_scoreline")
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

        # Add missing columns to gary_calls if it exists
        gc_cols = existing_cols("gary_calls")
        gary_calls_expected = [
            ("call_id", "TEXT"), ("fixture_id", "TEXT"), ("tier", "TEXT"),
            ("match_date", "TEXT"), ("home_team", "TEXT"), ("away_team", "TEXT"),
            ("engine_prediction", "TEXT"), ("engine_confidence", "REAL"),
            ("upset_flag", "INTEGER"), ("chaos_tier", "TEXT"), ("dti", "REAL"),
            ("engine_draw_score", "REAL"), ("engine_btts_flag", "INTEGER"),
            ("engine_upset_score", "REAL"), ("engine_pred_scoreline", "TEXT"),
            ("gary_prediction", "TEXT"), ("gary_narrative", "TEXT"),
            ("gary_response", "TEXT"), ("gary_confidence_band", "TEXT"),
            ("gary_upset_called", "INTEGER"), ("gary_draw_called", "INTEGER"),
            ("pattern_n_similar", "INTEGER"), ("pattern_h_pct", "REAL"),
            ("pattern_d_pct", "REAL"), ("pattern_a_pct", "REAL"),
            ("pattern_agreement", "TEXT"),
            ("actual_result", "TEXT"), ("actual_score", "TEXT"),
            ("correct", "INTEGER"), ("engine_correct", "INTEGER"),
            ("gary_vs_engine", "TEXT"),
            ("completed_at", "TIMESTAMP"), ("logged_at", "TIMESTAMP"),
            ("param_version_id", "TEXT"),
        ]
        for col_name, col_type in gary_calls_expected:
            if col_name not in gc_cols and gc_cols:
                try:
                    conn.execute(f"ALTER TABLE gary_calls ADD COLUMN {col_name} {col_type}")
                    logger.info(f"Migration: added gary_calls.{col_name}")
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
            actual_scoreline    TEXT,
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

        # ── gary_calls ───────────────────────────────────────────────────────
        conn.execute("""
        CREATE TABLE IF NOT EXISTS gary_calls (
            call_id             TEXT PRIMARY KEY,
            fixture_id          TEXT REFERENCES fixtures(fixture_id),
            tier                TEXT NOT NULL,
            match_date          TEXT NOT NULL,
            home_team           TEXT NOT NULL,
            away_team           TEXT NOT NULL,

            -- Engine output at call time
            engine_prediction   TEXT,
            engine_confidence   REAL,
            upset_flag          INTEGER,
            chaos_tier          TEXT,
            dti                 REAL,

            -- Gary's call
            gary_prediction     TEXT,
            gary_narrative      TEXT,

            -- Post-match completion
            actual_result       TEXT,
            correct             INTEGER,
            completed_at        TIMESTAMP,

            -- Metadata
            logged_at           TIMESTAMP NOT NULL
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
        conn.execute("CREATE INDEX IF NOT EXISTS idx_gary_calls_fixture ON gary_calls(fixture_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_gary_calls_date ON gary_calls(match_date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_gary_calls_tier ON gary_calls(tier)")

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
            actual_scoreline = f"{actual_home_goals}-{actual_away_goals}"

            conn.execute(
                """UPDATE fixtures
                   SET actual_result = ?,
                       actual_home_goals = ?,
                       actual_away_goals = ?,
                       actual_scoreline = ?,
                       correct = ?,
                       completed_at = ?
                   WHERE fixture_id = ?""",
                (actual_result, actual_home_goals, actual_away_goals,
                 actual_scoreline, correct, datetime.utcnow().isoformat(), fixture_id)
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
                """SELECT cl.*, {param_cols}
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

    def get_miss_patterns(
        self,
        tier: str,
        min_samples: int = 50,
    ) -> Dict:
        """
        Query prediction_result_memory for miss patterns in a tier.

        Called by DPOL at the start of each tier evolution to pre-load
        the teacher's signal — what types of mistakes does the engine
        historically make here, and under what conditions?

        Returns a dict with:
            dominant_miss:      str  — most frequent miss type e.g. "predicted_H_was_D"
            miss_rate:          float — overall miss rate for the tier
            high_conf_miss_rate: float — miss rate among high-confidence predictions
            dominant_hc_miss:   str  — most frequent high-confidence miss type
            closing_against_pct: float — % of misses where closing line was against us
            param_hints:        list of dicts [{param, direction}] — suggested bias
            sample_size:        int  — number of completed predictions used

        param_hints translates dominant miss patterns into param directions:
            predicted_H_was_D → draw_margin up, home_adv down
            predicted_H_was_A → w_form down, w_gd down (over-weighting home signals)
            predicted_A_was_H → home_adv up, w_away_team_adv down
            predicted_D_was_H → draw_margin down, w_draw_odds up
            predicted_D_was_A → draw_margin down, w_away_team_adv up

        Returns empty dict if prediction_result_memory table doesn't exist
        or has insufficient data for this tier.
        """
        try:
            with self._conn() as conn:
                # Check table exists
                tables = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='prediction_result_memory'"
                ).fetchone()
                if not tables:
                    return {}

                rows = conn.execute("""
                    SELECT miss_type, confidence_band, closing_line_signal, correct
                    FROM prediction_result_memory
                    WHERE tier = ? AND actual IS NOT NULL
                """, (tier,)).fetchall()

            if len(rows) < min_samples:
                return {}

            total = len(rows)
            misses = [r for r in rows if r["correct"] == 0]
            n_miss = len(misses)

            if n_miss == 0:
                return {"miss_rate": 0.0, "sample_size": total, "param_hints": []}

            miss_rate = n_miss / total

            # Dominant miss type
            miss_counts = {}
            for r in misses:
                mt = r["miss_type"] or "unknown"
                miss_counts[mt] = miss_counts.get(mt, 0) + 1
            dominant_miss = max(miss_counts, key=miss_counts.get)

            # High-confidence miss rate
            hc_all = [r for r in rows if r["confidence_band"] == "high"]
            hc_miss = [r for r in hc_all if r["correct"] == 0]
            high_conf_miss_rate = len(hc_miss) / len(hc_all) if hc_all else None

            # Dominant high-confidence miss
            hcm_counts = {}
            for r in hc_miss:
                mt = r["miss_type"] or "unknown"
                hcm_counts[mt] = hcm_counts.get(mt, 0) + 1
            dominant_hc_miss = max(hcm_counts, key=hcm_counts.get) if hcm_counts else None

            # Closing line alignment on misses
            against = sum(1 for r in misses if r["closing_line_signal"] == "against_our_call")
            closing_against_pct = against / n_miss if n_miss > 0 else 0.0

            # Translate dominant miss into param hints
            # Primary focus: the dominant HIGH-CONFIDENCE miss (most actionable signal)
            target_miss = dominant_hc_miss or dominant_miss
            param_hints = _miss_type_to_param_hints(target_miss)

            return {
                "dominant_miss":       dominant_miss,
                "miss_rate":           round(miss_rate, 4),
                "high_conf_miss_rate": round(high_conf_miss_rate, 4) if high_conf_miss_rate is not None else None,
                "dominant_hc_miss":    dominant_hc_miss,
                "closing_against_pct": round(closing_against_pct, 4),
                "param_hints":         param_hints,
                "sample_size":         total,
            }

        except Exception as e:
            logger.warning(f"[Teacher] get_miss_patterns failed for {tier}: {e}")
            return {}


    def find_similar_fixtures(
        self,
        feature_vector: Dict[str, float],
        tier: Optional[str] = None,
        n: int = 200,
        completed_only: bool = True,
        max_distance: Optional[float] = None,
    ) -> List[Dict]:
        """
        Find similar historical fixtures to a given feature vector.

        Self-tuning variable neighbourhood — finds the natural elbow in the
        distance distribution for each query fixture. The elbow is the point
        where the gap between consecutive distances is largest relative to
        local variation. Everything before it is the genuine neighbourhood.
        Everything after is "close by rank, not by nature."

        This means neighbourhood size is determined by the data, not a
        parameter. A common fixture type in a dense region gets many
        neighbours. A rare fixture in a sparse region gets few — and that
        sparsity is itself meaningful signal.

        Key design:
        - Features z-score normalised across candidate pool — all features
          contribute equally regardless of raw scale.
        - Feature mask built per query — dormant signals (zero/null in the
          query fixture) excluded so they don't pollute distance calculation.
        - max_distance overrides self-tuning when explicit control is needed.

        Args:
            feature_vector:  dict of feature_name -> value for target fixture
            tier:            optional — restrict to same tier
            n:               max results to return (hard cap in both modes)
            completed_only:  only return fixtures with known outcomes
            max_distance:    normalised distance threshold override.
                             None (default) = self-tuning elbow detection.

        Returns:
            List of fixture dicts sorted by similarity (closest first).
            Each dict includes:
              _distance            — normalised Euclidean distance
              _neighbourhood_size  — genuine neighbourhood size at elbow
              _active_features     — number of features used
              _cutoff_method       — 'elbow', 'manual', or 'all'
              _cutoff_distance     — distance threshold used
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

        row_dicts = [dict(r) for r in rows]

        # ── Feature mask: only features meaningful for this specific fixture ──
        # Signal fields (Phase 1/2) start at 0 when dormant. Exclude them from
        # the distance calculation when they're not active in the query fixture.
        # Core fields (form, gd, dti etc.) are always included if present.
        # Activation threshold is derived per-feature from the pool's own spread —
        # a value must exceed 5% of that feature's std to count as active.
        # No hardcoded cutoff — the data sets its own scale.
        SIGNAL_FIELDS = {
            "weather_load", "travel_load", "motivation_gap",
            "timing_signal", "ref_signal",
        }
        ALWAYS_INCLUDE = {
            "home_form", "away_form", "home_gd", "away_gd",
            "dti", "pred_margin", "pred_home_goals", "pred_away_goals",
        }

        import math

        # Compute per-feature std across the full candidate pool first.
        # Used both for activation thresholds and z-score normalisation.
        all_numeric = [f for f in FEATURE_FIELDS if f != "chaos_tier"]
        pool_vals: Dict[str, List[float]] = {f: [] for f in all_numeric}
        for rd in row_dicts:
            for f in all_numeric:
                v = rd.get(f)
                pool_vals[f].append(float(v) if v is not None else 0.0)

        col_mean: Dict[str, float] = {}
        col_std: Dict[str, float] = {}
        for f in all_numeric:
            vals = pool_vals[f]
            mean = sum(vals) / len(vals)
            variance = sum((v - mean) ** 2 for v in vals) / len(vals)
            col_mean[f] = mean
            col_std[f] = math.sqrt(variance) if variance > 0 else 1.0

        # A feature is active in this fixture if its value exceeds 5% of the
        # feature's own spread. Scales with the feature — no single cutoff.
        ACTIVATION_FRACTION = 0.05

        active_features = []
        for f in all_numeric:
            val = feature_vector.get(f)
            if val is None:
                continue
            fval = float(val)
            if f not in ALWAYS_INCLUDE:
                threshold = col_std[f] * ACTIVATION_FRACTION
                if abs(fval) < threshold:
                    continue  # not meaningfully active for this fixture
            active_features.append(f)

        if not active_features:
            return []

        # ── Normalise query vector using pool stats ───────────────────────────
        target_norm = [
            (float(feature_vector.get(f, 0.0) or 0.0) - col_mean[f]) / col_std[f]
            for f in active_features
        ]

        # ── Distance calculation ──────────────────────────────────────────────
        scored = []
        for rd in row_dicts:
            candidate_norm = [
                (float(rd.get(f) or 0.0) - col_mean[f]) / col_std[f]
                for f in active_features
            ]
            dist = math.sqrt(
                sum((a - b) ** 2 for a, b in zip(target_norm, candidate_norm))
            )
            rd["_distance"] = round(dist, 4)
            scored.append(rd)

        scored.sort(key=lambda x: x["_distance"])

        # ── Threshold selection ───────────────────────────────────────────────
        # If max_distance is explicitly provided, use it directly.
        # Otherwise, find the natural elbow in the distance distribution —
        # the point where the gap between consecutive distances is largest
        # relative to local variation. Everything before the elbow is the
        # genuine neighbourhood. Everything after is "similar by rank, not nature."
        if max_distance is not None:
            cutoff = max_distance
            method = "manual"
        else:
            distances = [r["_distance"] for r in scored]

            if len(distances) < 4:
                # Too few candidates to find an elbow — return all
                cutoff = distances[-1] if distances else 0.0
                method = "all"
            else:
                # Compute gaps between consecutive sorted distances.
                # Normalise each gap by the local median gap in a window
                # around it — this makes the elbow detection robust to
                # overall scale differences between fixture types.
                WINDOW = max(5, len(distances) // 20)  # 5% of candidates, min 5
                gaps = [distances[i+1] - distances[i] for i in range(len(distances)-1)]

                normalised_gaps = []
                for i, gap in enumerate(gaps):
                    lo = max(0, i - WINDOW)
                    hi = min(len(gaps), i + WINDOW + 1)
                    window_gaps = sorted(gaps[lo:hi])
                    median_gap = window_gaps[len(window_gaps) // 2]
                    norm = gap / median_gap if median_gap > 1e-9 else gap
                    normalised_gaps.append(norm)

                # Find the largest normalised gap — that's the elbow.
                # No hardcoded minimum — derive the meaningful search start
                # from the distance distribution itself. The first significant
                # jump above the baseline noise level marks where the dense
                # cluster ends. Baseline noise = median of all normalised gaps.
                # We start searching from the first gap that exceeds it,
                # meaning we skip the tight inner cluster automatically.
                MAX_NEIGHBOURS = n  # never return more than the n cap

                search_gaps = normalised_gaps[:MAX_NEIGHBOURS]
                all_sorted_gaps = sorted(search_gaps)
                baseline_noise = all_sorted_gaps[len(all_sorted_gaps) // 2]

                # Find where we first leave the noise floor — that's our
                # search start. Then find the biggest gap from there.
                search_start = 1
                for i, ng in enumerate(search_gaps):
                    if ng > baseline_noise:
                        search_start = i
                        break

                elbow_idx = search_start  # default: first gap above noise
                best_gap = 0.0
                for i in range(search_start, len(search_gaps)):
                    if search_gaps[i] > best_gap:
                        best_gap = search_gaps[i]
                        elbow_idx = i

                cutoff = distances[elbow_idx]
                method = "elbow"

        within = [r for r in scored if r["_distance"] <= cutoff]
        neighbourhood_size = len(within)
        results = within[:n]

        for r in results:
            r["_neighbourhood_size"] = neighbourhood_size
            r["_active_features"] = len(active_features)
            r["_cutoff_method"] = method
            r["_cutoff_distance"] = round(cutoff, 4)

        return results

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

    def get_scoreline_profiles(self, tier: str) -> Dict[str, Dict]:
        """
        Load all evolved scoreline param profiles for a tier.

        Returns dict keyed by scoreline string e.g. '1-0', '2-1', '0-0'.
        Each value contains the evolved params, density scores, outcome,
        and population size.

        Used by the prediction routing layer to match a live fixture against
        historical scoreline populations and read their param signatures.
        """
        try:
            with self._conn() as conn:
                rows = conn.execute(
                    """
                    SELECT scoreline, outcome, population_size,
                           evolved_density, baseline_density, delta_density,
                           merged_to_outcome,
                           """ + ", ".join(f"p_{p}" for p in PARAM_FIELDS) + """
                    FROM scoreline_param_profiles
                    WHERE tier = ?
                    ORDER BY evolved_density DESC
                    """,
                    (tier,)
                ).fetchall()
        except Exception:
            return {}

        profiles = {}
        col_names = (
            ["scoreline", "outcome", "population_size",
             "evolved_density", "baseline_density", "delta_density",
             "merged_to_outcome"] +
            [f"p_{p}" for p in PARAM_FIELDS]
        )
        for row in rows:
            d = dict(zip(col_names, row))
            scoreline = d.pop("scoreline")
            # Rebuild LeagueParams from stored p_ columns
            from edgelab_dpol import LeagueParams
            lp_kwargs = {p: d.pop(f"p_{p}", 0.0) or 0.0 for p in PARAM_FIELDS}
            d["params"] = LeagueParams(**lp_kwargs)
            profiles[scoreline] = d
        return profiles

    def match_fixture_to_scorelines(
        self,
        tier: str,
        fixture_features: Dict,
        top_n: int = 5,
    ) -> List[Dict]:
        """
        Given a live fixture's features, find the top N scoreline populations
        it most resembles.

        Similarity is computed by running the fixture through each population's
        evolved params via the engine and reading the confidence score for that
        population's own outcome. This is a like-for-like comparison in the same
        space — the engine scores the fixture as if it were a match from that
        population, and confidence is how strongly those params fire on it.

        This replaces the previous cosine similarity approach which compared
        fixture feature values against param weights — apples and oranges.

        Returns list of dicts: scoreline, outcome, similarity (confidence score),
        evolved_density, population_size — sorted by similarity descending.
        """
        profiles = self.get_scoreline_profiles(tier)
        if not profiles:
            return []

        # Lazy import inside function — avoids circular import at module level.
        # edgelab_engine does not import edgelab_db so this is safe.
        try:
            import pandas as pd
            import numpy as np
            from edgelab_engine import EngineParams, predict_dataframe
        except Exception:
            return []

        # Build a single-row dataframe from fixture features.
        # Only columns that predict_dataframe actually reads are needed.
        # Missing values default to 0.0 — same as the engine's fallback behaviour.
        feature_row = {
            "home_form":      fixture_features.get("home_form", 0.0) or 0.0,
            "away_form":      fixture_features.get("away_form", 0.0) or 0.0,
            "home_gd":        fixture_features.get("home_gd", 0.0) or 0.0,
            "away_gd":        fixture_features.get("away_gd", 0.0) or 0.0,
            "dti":            fixture_features.get("dti", 0.5) or 0.5,
            "home_form_home": fixture_features.get("home_form_home", 0.0) or 0.0,
            "away_form_away": fixture_features.get("away_form_away", 0.0) or 0.0,
            "home_adv_team":  fixture_features.get("home_adv_team", 0.0) or 0.0,
            "away_adv_team":  fixture_features.get("away_adv_team", 0.0) or 0.0,
            "home_form_adj":  fixture_features.get("home_form_adj", 0.0) or 0.0,
            "away_form_adj":  fixture_features.get("away_form_adj", 0.0) or 0.0,
            "season_stage":   fixture_features.get("season_stage", 0.5) or 0.5,
            "rest_days_diff": fixture_features.get("rest_days_diff", 0.0) or 0.0,
            "odds_draw_prob": fixture_features.get("odds_draw_prob", 0.0) or 0.0,
            "draw_score":     0.0,
            "FTR":            "?",   # sentinel — engine skips eval on this
        }
        df_fix = pd.DataFrame([feature_row])

        results = []
        for scoreline, profile in profiles.items():
            if profile.get("merged_to_outcome"):
                continue  # skip merged populations — not specific enough

            outcome = profile["outcome"]
            lp = profile["params"]

            # Convert LeagueParams to EngineParams
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
                form_window=5,
            )

            try:
                df_result = predict_dataframe(df_fix.copy(), ep)
                pred = df_result["prediction"].iloc[0]
                conf = float(df_result["confidence"].iloc[0])
            except Exception:
                continue

            # Similarity = confidence score when this population's params are
            # applied to the fixture AND the prediction matches the population's
            # own outcome. If the params don't even agree on the outcome for this
            # fixture, similarity is still recorded but will rank lower (conf < 0.5).
            # We do not pre-filter by outcome — let the score determine the ranking.
            similarity = conf if pred == outcome else conf * 0.5

            # Weight by evolved density — higher density = more reliable population
            density = profile.get("evolved_density", 0.0) or 0.0
            weighted_similarity = similarity * max(density, 0.01)

            results.append({
                "scoreline":        scoreline,
                "outcome":          outcome,
                "similarity":       round(similarity, 4),
                "weighted_similarity": round(weighted_similarity, 4),
                "evolved_density":  density,
                "population_size":  profile.get("population_size", 0),
                "params":           lp,
            })

        results.sort(key=lambda x: x["weighted_similarity"], reverse=True)
        return results[:top_n] if top_n else results

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
    # Gary call logging
    # -----------------------------------------------------------------------

    def log_gary_call(
        self,
        tier: str,
        match_date: str,
        home_team: str,
        away_team: str,
        engine_prediction: Optional[str],
        engine_confidence: Optional[float],
        upset_flag: Optional[int],
        chaos_tier: Optional[str],
        dti: Optional[float],
        gary_prediction: Optional[str],
        gary_narrative: str,
        # Extended fields — populated when available
        engine_draw_score: Optional[float] = None,
        engine_btts_flag: Optional[int] = None,
        engine_upset_score: Optional[float] = None,
        engine_pred_scoreline: Optional[str] = None,
        gary_response: Optional[str] = None,
        gary_confidence_band: Optional[str] = None,
        gary_upset_called: Optional[int] = None,
        gary_draw_called: Optional[int] = None,
        pattern_n_similar: Optional[int] = None,
        pattern_h_pct: Optional[float] = None,
        pattern_d_pct: Optional[float] = None,
        pattern_a_pct: Optional[float] = None,
        pattern_agreement: Optional[str] = None,
        param_version_id: Optional[str] = None,
    ) -> str:
        """
        Log Gary's pre-match call to the database.
        Called silently after Gary's ask() returns.
        Returns call_id.
        """
        fixture_id = _make_fixture_id(tier, match_date, home_team, away_team)
        raw = f"gary_{fixture_id}"
        call_id = hashlib.md5(raw.encode()).hexdigest()[:16]

        with self._conn() as conn:
            existing = conn.execute(
                "SELECT call_id FROM gary_calls WHERE call_id = ?", (call_id,)
            ).fetchone()

            if not existing:
                # Build column list dynamically — only include columns that exist
                existing_cols = {
                    row[1] for row in
                    conn.execute("PRAGMA table_info(gary_calls)").fetchall()
                }

                base = {
                    "call_id": call_id,
                    "fixture_id": fixture_id,
                    "tier": tier,
                    "match_date": match_date,
                    "home_team": home_team,
                    "away_team": away_team,
                    "engine_prediction": engine_prediction,
                    "engine_confidence": round(engine_confidence, 4) if engine_confidence else None,
                    "upset_flag": upset_flag,
                    "chaos_tier": chaos_tier,
                    "dti": dti,
                    "gary_prediction": gary_prediction,
                    "gary_narrative": gary_narrative,
                    "logged_at": datetime.utcnow().isoformat(),
                }
                extended = {
                    "engine_draw_score": engine_draw_score,
                    "engine_btts_flag": engine_btts_flag,
                    "engine_upset_score": engine_upset_score,
                    "engine_pred_scoreline": engine_pred_scoreline,
                    "gary_response": gary_response,
                    "gary_confidence_band": gary_confidence_band,
                    "gary_upset_called": gary_upset_called,
                    "gary_draw_called": gary_draw_called,
                    "pattern_n_similar": pattern_n_similar,
                    "pattern_h_pct": pattern_h_pct,
                    "pattern_d_pct": pattern_d_pct,
                    "pattern_a_pct": pattern_a_pct,
                    "pattern_agreement": pattern_agreement,
                    "param_version_id": param_version_id,
                }

                # Merge — only include extended fields if column exists
                record = {**base}
                for col, val in extended.items():
                    if col in existing_cols:
                        record[col] = val

                cols = list(record.keys())
                vals = list(record.values())
                placeholders = ",".join("?" * len(cols))
                col_str = ",".join(cols)

                conn.execute(
                    f"INSERT INTO gary_calls ({col_str}) VALUES ({placeholders})",
                    vals,
                )
                conn.commit()
                logger.info(f"Gary call logged: {home_team} vs {away_team} ({match_date})")
            else:
                logger.info(f"Gary call already logged: {call_id} — skipping")

        return call_id

    def complete_gary_call(
        self,
        tier: str,
        match_date: str,
        home_team: str,
        away_team: str,
        actual_result: str,
        actual_score: Optional[str] = None,
    ) -> bool:
        """
        Complete a Gary call when the result comes in.
        Marks correct/wrong based on gary_prediction vs actual_result.
        Also computes engine_correct and gary_vs_engine if columns exist.
        Called from results_check.py alongside complete_fixture().
        Returns True if updated, False if not found.
        """
        fixture_id = _make_fixture_id(tier, match_date, home_team, away_team)

        with self._conn() as conn:
            row = conn.execute(
                "SELECT call_id, gary_prediction, engine_prediction FROM gary_calls WHERE fixture_id = ?",
                (fixture_id,)
            ).fetchone()

            if not row:
                return False

            gary_correct = 1 if (row["gary_prediction"] == actual_result) else 0
            engine_correct = 1 if (row["engine_prediction"] == actual_result) else 0 if row["engine_prediction"] else None

            # Compute gary_vs_engine label
            if engine_correct is not None:
                if gary_correct and engine_correct:
                    gary_vs_engine = "both_right"
                elif gary_correct and not engine_correct:
                    gary_vs_engine = "gary_only"
                elif not gary_correct and engine_correct:
                    gary_vs_engine = "engine_only"
                else:
                    gary_vs_engine = "both_wrong"
            else:
                gary_vs_engine = None

            # Check which columns exist
            existing_cols = {
                r[1] for r in
                conn.execute("PRAGMA table_info(gary_calls)").fetchall()
            }

            updates = {
                "actual_result": actual_result,
                "correct": gary_correct,
                "completed_at": datetime.utcnow().isoformat(),
            }
            if "actual_score" in existing_cols and actual_score:
                updates["actual_score"] = actual_score
            if "engine_correct" in existing_cols:
                updates["engine_correct"] = engine_correct
            if "gary_vs_engine" in existing_cols:
                updates["gary_vs_engine"] = gary_vs_engine

            set_clause = ", ".join(f"{k} = ?" for k in updates)
            vals = list(updates.values()) + [row["call_id"]]
            conn.execute(
                f"UPDATE gary_calls SET {set_clause} WHERE call_id = ?",
                vals,
            )
            conn.commit()

        logger.info(
            f"Gary call completed: {home_team} vs {away_team} — "
            f"gary={row['gary_prediction']} engine={row['engine_prediction']} "
            f"actual={actual_result} | {gary_vs_engine or ('correct' if gary_correct else 'wrong')}"
        )
        return True

    def get_gary_accuracy(self, tier: Optional[str] = None) -> dict:
        """
        Return Gary's call accuracy stats.
        Optional tier filter.
        """
        with self._conn() as conn:
            where = "WHERE completed_at IS NOT NULL"
            params = []
            if tier:
                where += " AND tier = ?"
                params.append(tier)

            row = conn.execute(f"""
                SELECT COUNT(*) as total,
                       SUM(correct) as correct_count
                FROM gary_calls {where}
            """, params).fetchone()

            total = row["total"] or 0
            correct = row["correct_count"] or 0
            accuracy = round(correct / total, 4) if total else None

        return {
            "tier": tier or "all",
            "total_calls": total,
            "correct": correct,
            "accuracy": accuracy,
        }

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
