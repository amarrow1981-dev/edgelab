"""
EdgeLab DPOL (Dynamic Pattern Override Layer) Prototype

This module assumes you already have:
- A per-match dataframe with:
    - season_start_year
    - tier (league name)
    - parsed_date
    - FTR (full-time result: 'H','D','A')
- The ability to re-run your prediction engine with different parameter sets.

DPOL does NOT implement the prediction engine itself.
Instead, it manages:
    - pattern detection
    - candidate parameter adjustments
    - testing over a rolling window
    - selecting the best adjustment
    - applying or reverting changes per league
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple, Callable
import pandas as pd
import numpy as np
import copy
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass
class LeagueParams:
    """
    Parameter set for a single league (tier).
    These are the knobs DPOL can adjust.
    """
    # Core weights
    w_form: float = 1.0
    w_gd: float = 0.3
    home_adv: float = 0.25

    # DTI impact
    dti_edge_scale: float = 0.4   # how strongly DTI shrinks form/gd
    dti_ha_scale: float = 0.5     # how strongly DTI shrinks home advantage

    # Draw and coin-flip
    draw_margin: float = 0.15
    coin_dti_thresh: float = 0.7  # DTI threshold for coin-flip to kick in

    # Draw recovery params
    draw_pull: float = 0.08       # gravity toward draw when teams evenly matched
    dti_draw_lock: float = 0.85   # high DTI + parity = lock as draw

    # Draw intelligence layer (session 6) — all start at 0, DPOL activates them
    w_draw_odds: float = 0.0         # bookmaker implied draw probability weight
    w_draw_tendency: float = 0.0     # team rolling draw rate weight
    w_h2h_draw: float = 0.0          # H2H draw history weight
    draw_score_thresh: float = 0.55  # draw_score above this → call draw

    # Score prediction layer (session 6) — all start at 0, DPOL activates them
    w_score_margin: float = 0.0      # predicted goal margin reinforces H/A calls
    w_btts: float = 0.0              # BTTS probability contributes to draw score

    # Instinct / stability sensitivity (future hooks)
    instinct_dti_thresh: float = 0.6
    skew_correction_thresh: float = 0.55
    # --- External Signal Layer — Phase 1 (session 14) ---
    # All start at 0.0. DPOL will activate signals that correlate with outcomes.
    w_ref_signal:    float = 0.0   # referee home bias signal weight
    w_travel_load:   float = 0.0   # away travel distance disadvantage weight
    w_timing_signal: float = 0.0   # fixture timing disruption weight
    w_motivation_gap: float = 0.0  # home vs away motivation gap weight
    # --- External Signal Layer — Phase 2 (session 16) ---
    w_weather_signal: float = 0.0  # weather conditions burden weight (rain, wind, cold)
    # --- Composite draw signal layer (session 26) ---
    w_xg_draw: float = 0.0           # expected goals total as draw signal (1.088x lift)
    composite_draw_boost: float = 0.0 # additive boost when odds anchor + supporting signal align


@dataclass
class LeagueState:
    """
    Tracks current and previous parameter sets and performance for a given league.
    """
    current_params: LeagueParams
    best_params: LeagueParams
    best_accuracy: float = 0.0
    history: List[Tuple[int, float]] = field(default_factory=list)  # (round_index, accuracy)


class DPOLManager:
    """
    DPOL = Dynamic Pattern Override Layer.

    Responsibilities:
    - For each league (tier), maintain a parameter set.
    - On each evaluation window (e.g. last 4-8 rounds):
        * measure accuracy of current params
        * generate candidate tweaks
        * evaluate each candidate
        * if one is better than current, adopt it
        * otherwise, keep the current params
    """

    def __init__(
        self,
        initial_params_factory: Callable[[str], LeagueParams] = None,
        window_rounds: int = 6,
        boldness: str = "small",  # 'tiny', 'small', 'medium'
        db=None,  # Optional EdgeLabDB instance — enables candidate log navigation
    ):
        """
        :param initial_params_factory: function(tier) -> LeagueParams
        :param window_rounds: how many rounds of matches to use in evaluation window
        :param boldness: how aggressive adjustments are ('tiny','small','medium')
        :param db: Optional EdgeLabDB instance. When provided, DPOL reads
                   get_successful_param_directions() before each evolution round
                   to bias candidate generation toward historically proven moves.
                   Without this, DPOL runs blind (previous behaviour).
        """
        self.window_rounds = window_rounds
        self.boldness = boldness
        self.db = db  # fixture intelligence database — None = blind mode

        if initial_params_factory is None:
            initial_params_factory = lambda tier: LeagueParams()

        self.initial_params_factory = initial_params_factory
        self.leagues: Dict[str, LeagueState] = {}

    # ----------------------------
    # League param management
    # ----------------------------

    def get_league_state(self, tier: str) -> LeagueState:
        if tier not in self.leagues:
            params = self.initial_params_factory(tier)
            self.leagues[tier] = LeagueState(
                current_params=copy.deepcopy(params),
                best_params=copy.deepcopy(params),
                best_accuracy=0.0,
                history=[]
            )
        return self.leagues[tier]

    # ----------------------------
    # Evaluation & evolution entrypoint
    # ----------------------------

    def evolve_for_league(
        self,
        df_league: pd.DataFrame,
        round_col: str = "match_round",
        pred_fn: Callable[[pd.DataFrame, LeagueParams], pd.Series] = None,
        df_full: pd.DataFrame = None,
        min_improvement: float = 0.001,
        signals_only: bool = False,
        candidate_logger: Callable = None,
        season_label: str = "",
        param_version_id: str = None,
    ) -> None:
        """
        Run DPOL evolution for a single league.

        Args:
            df_league:        Season data with match_round and FTR columns.
            round_col:        Column containing round index.
            pred_fn:          pred_fn(df, params) -> Series of H/D/A predictions.
            df_full:          Optional. Full tier dataset for global accuracy guard.
            min_improvement:  Minimum gain to adopt a candidate (default 0.1%).
            candidate_logger: Optional callback fired for every candidate evaluated.
                              Signature: candidate_logger(tier, season, round_num,
                                          params, window_acc, global_acc,
                                          accepted, base_acc, param_version_id)
            season_label:     Current season string for logging (e.g. "2024-25").
            param_version_id: Active param version ID for cross-referencing in DB.
        """

        if pred_fn is None:
            raise ValueError("You must supply pred_fn(df_window, params) -> Series of predictions.")

        if df_league.empty:
            return

        tier_name = str(df_league["tier"].iloc[0])
        state = self.get_league_state(tier_name)

        max_round = int(df_league[round_col].max())
        if max_round < 1:
            return

        window_size = self.window_rounds
        start_round = max(1, max_round - window_size + 1)

        window_df = df_league[df_league[round_col].between(start_round, max_round)].copy()
        if window_df.empty:
            return

        # Evaluate current params on window
        base_acc = self._evaluate_params(window_df, state.current_params, pred_fn)
        state.history.append((max_round, base_acc))

        # Global baseline for guard
        if df_full is not None and not df_full.empty:
            global_base_acc = self._evaluate_params(df_full, state.current_params, pred_fn)
        else:
            global_base_acc = None

        logger.info(f"[DPOL] Tier={tier_name} Round={max_round} Base accuracy={base_acc:.3f}")

        # Query the fixture intelligence database for historically proven
        # param directions before generating candidates.
        # This is the core of the S30 fix: DPOL no longer starts blind.
        # If DB is not available (or has no data yet for this tier),
        # directions is empty and candidate generation falls back to the
        # original blind behaviour — safe and backward-compatible.
        proven_directions = []
        if self.db is not None:
            try:
                proven_directions = self.db.get_successful_param_directions(
                    tier=tier_name,
                    top_n=10,
                    min_delta=0.001,
                )
                if proven_directions:
                    logger.info(
                        f"[DPOL] Tier={tier_name} Round={max_round} "
                        f"Navigation: {len(proven_directions)} proven directions loaded from candidate log"
                    )
            except Exception as _db_err:
                logger.warning(f"[DPOL] Could not read candidate directions: {_db_err}")
                proven_directions = []

        candidates = (
            self._generate_candidates_signals_only(state.current_params)
            if signals_only
            else self._generate_candidates(state.current_params, proven_directions=proven_directions)
        )

        best_candidate = None
        best_candidate_acc = base_acc
        # Track all candidates for logging — (params, window_acc)
        all_evaluated = []

        # Phase 1: find best candidate by window accuracy only (fast — no global eval)
        for params in candidates:
            acc = self._evaluate_params(window_df, params, pred_fn)
            all_evaluated.append((params, acc))
            if acc <= base_acc + min_improvement:
                continue
            if acc > best_candidate_acc:
                best_candidate_acc = acc
                best_candidate = params

        # Phase 2: global guard on the single best window candidate only.
        # Previously ran global eval on every passing candidate — N evals per round.
        # Now it's 1 global eval per round max. Significant speedup, same guard strength.
        global_acc_for_best = None
        if best_candidate is not None and global_base_acc is not None:
            global_acc_for_best = self._evaluate_params(df_full, best_candidate, pred_fn)
            if global_acc_for_best < global_base_acc - min_improvement:
                logger.info(
                    f"[DPOL] Tier={tier_name} Candidate rejected: "
                    f"window={best_candidate_acc:.3f} but global {global_acc_for_best:.3f} < {global_base_acc:.3f}"
                )
                best_candidate = None

        accepted = best_candidate is not None

        if accepted:
            logger.info(
                f"[DPOL] Tier={tier_name} Round={max_round} "
                f"Improved {base_acc:.3f} -> {best_candidate_acc:.3f}"
            )
            state.current_params = best_candidate
            if best_candidate_acc > state.best_accuracy:
                state.best_accuracy = best_candidate_acc
                state.best_params = copy.deepcopy(best_candidate)
        else:
            logger.info(f"[DPOL] Tier={tier_name} Round={max_round} No better candidate found.")

        # Log all evaluated candidates to the fixture intelligence database.
        # The accepted candidate is logged with accepted=True and its global_acc.
        # All others are logged as rejected — this builds the navigation map.
        if candidate_logger is not None:
            for eval_params, eval_acc in all_evaluated:
                is_this_the_accepted = (
                    accepted and eval_params is best_candidate
                )
                try:
                    candidate_logger(
                        tier=tier_name,
                        season=season_label,
                        round_num=max_round,
                        params=eval_params,
                        window_acc=eval_acc,
                        global_acc=global_acc_for_best if is_this_the_accepted else None,
                        accepted=is_this_the_accepted,
                        base_acc=base_acc,
                        param_version_id=param_version_id,
                    )
                except Exception as _log_err:
                    logger.warning(f"[DPOL] Candidate log failed: {_log_err}")

    # ----------------------------
    # Core helpers
    # ----------------------------

    def _evaluate_params(
        self,
        df_window: pd.DataFrame,
        params: LeagueParams,
        pred_fn: Callable[[pd.DataFrame, LeagueParams], pd.Series],
        draw_weight: float = 1.5,
    ) -> float:
        """
        Weighted loss evaluation.

        Draw hits score draw_weight (default 1.5x).
        Draw misses (predicted D but wrong, or actual D but missed) score draw_weight penalty.
        All other hits/misses score 1.0.

        This incentivises DPOL to activate draw intelligence rather than ignoring draws.
        draw_weight=1.0 reverts to flat accuracy.
        """
        preds = pred_fn(df_window, params)
        ftr = df_window["FTR"].reindex(preds.index)

        if len(preds) == 0:
            return 0.0

        scores = []
        for pred, actual in zip(preds, ftr):
            is_draw_involved = (pred == "D") or (actual == "D")
            weight = draw_weight if is_draw_involved else 1.0
            scores.append(weight if pred == actual else -weight + 1.0)

        # Normalise to [0, 1] range comparable to flat accuracy
        max_possible = sum(
            draw_weight if ((p == "D") or (a == "D")) else 1.0
            for p, a in zip(preds, ftr)
        )
        return float(sum(scores) / max_possible) if max_possible > 0 else 0.0

    def _generate_candidates_signals_only(self, base: LeagueParams) -> List[LeagueParams]:
        """
        Signals-only variant — only varies signal weights.
        Core params (w_form, w_gd, home_adv, DTI, draw, etc.) are frozen.
        Used by --signals-only DPOL runs.
        """
        scale = {
            "tiny": 0.02,
            "small": 0.05,
            "medium": 0.10,
        }.get(self.boldness, 0.05)

        candidates: List[LeagueParams] = []

        def add_variant(**kwargs):
            p = copy.deepcopy(base)
            for k, v in kwargs.items():
                setattr(p, k, v)
            candidates.append(p)

        EXT_STEP = max(scale, 0.05)

        # Phase 1 signals
        for signal in ("w_ref_signal", "w_travel_load", "w_timing_signal", "w_motivation_gap"):
            current = getattr(base, signal)
            add_variant(**{signal: current + EXT_STEP})
            if current > 0:
                add_variant(**{signal: max(0.0, current - EXT_STEP)})

        # Phase 2 signals
        for signal in ("w_weather_signal",):
            current = getattr(base, signal)
            add_variant(**{signal: current + EXT_STEP})
            if current > 0:
                add_variant(**{signal: max(0.0, current - EXT_STEP)})

        return candidates

    def _generate_candidates(self, base: LeagueParams, proven_directions: list = None) -> List[LeagueParams]:
        """
        Generate candidate parameter variations around the current base parameters.
        Boldness controls how big the steps are.

        proven_directions: list of dicts from db.get_successful_param_directions().
            Each entry: {param, direction, avg_delta, avg_signed_move, count}
            When provided, candidates are generated with bias:
              - Proven direction: larger step (scale * PROVEN_BOOST)
              - Opposite direction: skipped if direction is clear ("up" or "down")
              - "mixed" direction: both directions tested at normal scale
              - Params with no history: normal blind generation (unchanged)
        """
        scale = {
            "tiny": 0.02,
            "small": 0.05,
            "medium": 0.10,
        }.get(self.boldness, 0.05)

        # Build a quick lookup: param -> direction entry
        # Only params with clear direction ("up" or "down") and enough evidence
        # get the bias treatment. "mixed" and unknown fall through to blind.
        direction_map = {}
        if proven_directions:
            for entry in proven_directions:
                direction_map[entry["param"]] = entry

        # Multiplier for the proven direction step — larger = bolder navigation
        PROVEN_BOOST = 2.0

        candidates: List[LeagueParams] = []

        def add_variant(**kwargs):
            p = copy.deepcopy(base)
            for k, v in kwargs.items():
                setattr(p, k, v)
            candidates.append(p)

        def biased_variants(param_name: str, current_val: float, step: float,
                            lower_bound: float = None):
            """
            Add up/down variants for a param, using direction bias if available.

            If direction is "up": add proven (up, bigger step) + exploratory (down, normal)
            If direction is "down": add proven (down, bigger step) + exploratory (up, normal)
            If direction is "mixed" or unknown: add both at normal step
            """
            entry = direction_map.get(param_name)

            if entry and entry["direction"] == "up":
                # Proven: larger step up
                add_variant(**{param_name: current_val * (1 + step * PROVEN_BOOST)})
                # Exploratory: normal step down (don't skip — we might be wrong)
                down_val = current_val * (1 - step)
                if lower_bound is not None:
                    down_val = max(lower_bound, down_val)
                if down_val != current_val:
                    add_variant(**{param_name: down_val})

            elif entry and entry["direction"] == "down":
                # Proven: larger step down
                down_val = current_val * (1 - step * PROVEN_BOOST)
                if lower_bound is not None:
                    down_val = max(lower_bound, down_val)
                add_variant(**{param_name: down_val})
                # Exploratory: normal step up
                add_variant(**{param_name: current_val * (1 + step)})

            else:
                # Blind (mixed, unknown, or no history) — normal both directions
                add_variant(**{param_name: current_val * (1 + step)})
                down_val = current_val * (1 - step)
                if lower_bound is not None:
                    down_val = max(lower_bound, down_val)
                if down_val != current_val:
                    add_variant(**{param_name: down_val})

        def biased_variants_zero_safe(param_name: str, current_val: float, step: float):
            """
            For params that start at 0.0 — use additive steps, not multiplicative.
            Direction bias still applies.
            """
            entry = direction_map.get(param_name)

            if entry and entry["direction"] == "up":
                add_variant(**{param_name: current_val + step * PROVEN_BOOST})
                if current_val > 0:
                    add_variant(**{param_name: max(0.0, current_val - step)})
            elif entry and entry["direction"] == "down":
                add_variant(**{param_name: max(0.0, current_val - step * PROVEN_BOOST)})
                add_variant(**{param_name: current_val + step})
            else:
                add_variant(**{param_name: current_val + step})
                if current_val > 0:
                    add_variant(**{param_name: max(0.0, current_val - step)})

        # ── Core params — multiplicative steps ──────────────────────────────
        biased_variants("w_form",         base.w_form,         scale)
        biased_variants("w_gd",           base.w_gd,           scale)
        biased_variants("home_adv",       base.home_adv,       scale)
        biased_variants("dti_edge_scale", base.dti_edge_scale, scale)
        biased_variants("dti_ha_scale",   base.dti_ha_scale,   scale)
        biased_variants("draw_margin",    base.draw_margin,    scale)
        biased_variants("coin_dti_thresh",base.coin_dti_thresh,scale)
        biased_variants("draw_pull",      base.draw_pull,      scale)
        biased_variants("dti_draw_lock",  base.dti_draw_lock,  scale)

        # ── Draw intelligence — additive from zero ───────────────────────────
        DRAW_STEP = max(scale, 0.05)

        biased_variants_zero_safe("w_draw_odds",      base.w_draw_odds,      DRAW_STEP)
        biased_variants_zero_safe("w_draw_tendency",  base.w_draw_tendency,  DRAW_STEP)
        biased_variants_zero_safe("w_h2h_draw",       base.w_h2h_draw,       DRAW_STEP)

        # draw_score_thresh — only tune if draw weights are active
        if (base.w_draw_odds + base.w_draw_tendency + base.w_h2h_draw) > 0:
            biased_variants_zero_safe("draw_score_thresh", base.draw_score_thresh, DRAW_STEP)

        # ── Score prediction params — additive from zero ─────────────────────
        SCORE_STEP = max(scale * 0.5, 0.02)
        biased_variants_zero_safe("w_score_margin", base.w_score_margin, SCORE_STEP)

        biased_variants_zero_safe("w_btts",         base.w_btts,         DRAW_STEP)

        # ── Composite draw signal layer ──────────────────────────────────────
        biased_variants_zero_safe("w_xg_draw",           base.w_xg_draw,           DRAW_STEP)
        biased_variants_zero_safe("composite_draw_boost", base.composite_draw_boost, DRAW_STEP)

        # ── External Signal Layer — Phase 1 ─────────────────────────────────
        EXT_STEP = max(scale, 0.05)
        biased_variants_zero_safe("w_ref_signal",     base.w_ref_signal,     EXT_STEP)
        biased_variants_zero_safe("w_travel_load",    base.w_travel_load,    EXT_STEP)
        biased_variants_zero_safe("w_timing_signal",  base.w_timing_signal,  EXT_STEP)
        biased_variants_zero_safe("w_motivation_gap", base.w_motivation_gap, EXT_STEP)

        return candidates
    