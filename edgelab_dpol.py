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
    ):
        """
        :param initial_params_factory: function(tier) -> LeagueParams
        :param window_rounds: how many rounds of matches to use in evaluation window
        :param boldness: how aggressive adjustments are ('tiny','small','medium')
        """
        self.window_rounds = window_rounds
        self.boldness = boldness

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

        candidates = (
            self._generate_candidates_signals_only(state.current_params)
            if signals_only
            else self._generate_candidates(state.current_params)
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

    def _generate_candidates(self, base: LeagueParams) -> List[LeagueParams]:
        """
        Generate candidate parameter variations around the current base parameters.
        Boldness controls how big the steps are.
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

        # Adjust form weight
        add_variant(w_form=base.w_form * (1 + scale))
        add_variant(w_form=base.w_form * (1 - scale))

        # Adjust goal difference weight
        add_variant(w_gd=base.w_gd * (1 + scale))
        add_variant(w_gd=base.w_gd * (1 - scale))

        # Adjust home advantage
        add_variant(home_adv=base.home_adv * (1 + scale))
        add_variant(home_adv=base.home_adv * (1 - scale))

        # Adjust DTI impact
        add_variant(dti_edge_scale=base.dti_edge_scale * (1 + scale))
        add_variant(dti_edge_scale=base.dti_edge_scale * (1 - scale))
        add_variant(dti_ha_scale=base.dti_ha_scale * (1 + scale))
        add_variant(dti_ha_scale=base.dti_ha_scale * (1 - scale))

        # Adjust draw margin slightly
        add_variant(draw_margin=base.draw_margin * (1 + scale))
        add_variant(draw_margin=base.draw_margin * (1 - scale))

        # Adjust coin-flip DTI threshold
        add_variant(coin_dti_thresh=base.coin_dti_thresh * (1 + scale))
        add_variant(coin_dti_thresh=base.coin_dti_thresh * (1 - scale))

        # Adjust draw_pull — how strongly parity pulls toward draw
        add_variant(draw_pull=base.draw_pull * (1 + scale))
        add_variant(draw_pull=base.draw_pull * (1 - scale))

        # Adjust dti_draw_lock — when to lock parity matches as draw
        add_variant(dti_draw_lock=base.dti_draw_lock * (1 + scale))
        add_variant(dti_draw_lock=base.dti_draw_lock * (1 - scale))

        # --- Draw intelligence params ---
        # These start at 0.0. DPOL tries activating them from scratch
        # by nudging up from zero. Once active, it also nudges down/up.
        DRAW_STEP = max(scale, 0.05)  # minimum step so 0.0 * anything != 0

        # Odds weight — try switching on
        add_variant(w_draw_odds=base.w_draw_odds + DRAW_STEP)
        if base.w_draw_odds > 0:
            add_variant(w_draw_odds=max(0.0, base.w_draw_odds - DRAW_STEP))

        # Draw tendency weight — try switching on
        add_variant(w_draw_tendency=base.w_draw_tendency + DRAW_STEP)
        if base.w_draw_tendency > 0:
            add_variant(w_draw_tendency=max(0.0, base.w_draw_tendency - DRAW_STEP))

        # H2H draw weight — try switching on
        add_variant(w_h2h_draw=base.w_h2h_draw + DRAW_STEP)
        if base.w_h2h_draw > 0:
            add_variant(w_h2h_draw=max(0.0, base.w_h2h_draw - DRAW_STEP))

        # Draw score threshold — only tune if any draw weights are active
        if (base.w_draw_odds + base.w_draw_tendency + base.w_h2h_draw) > 0:
            add_variant(draw_score_thresh=base.draw_score_thresh + DRAW_STEP)
            add_variant(draw_score_thresh=max(0.30, base.draw_score_thresh - DRAW_STEP))

        # --- Score prediction params ---
        # w_score_margin: predicted goal margin reinforces H/A calls.
        # Try switching on from zero with a small nudge.
        SCORE_STEP = max(scale * 0.5, 0.02)  # smaller step — this signal is continuous
        add_variant(w_score_margin=base.w_score_margin + SCORE_STEP)
        if base.w_score_margin > 0:
            add_variant(w_score_margin=max(0.0, base.w_score_margin - SCORE_STEP))

        # w_btts: BTTS probability feeds into draw_score.
        # Only meaningful if draw intelligence is also active.
        add_variant(w_btts=base.w_btts + DRAW_STEP)
        if base.w_btts > 0:
            add_variant(w_btts=max(0.0, base.w_btts - DRAW_STEP))

        # --- Composite draw signal layer (session 26) ---
        # w_xg_draw: expected goals total as draw signal (low xG = tight match = draw-positive).
        # composite_draw_boost: additive boost when odds anchor + supporting signal fire together.
        # Both start at 0.0 — nudge up from zero to try activating. Tune down once active.
        add_variant(w_xg_draw=base.w_xg_draw + DRAW_STEP)
        if base.w_xg_draw > 0:
            add_variant(w_xg_draw=max(0.0, base.w_xg_draw - DRAW_STEP))

        add_variant(composite_draw_boost=base.composite_draw_boost + DRAW_STEP)
        if base.composite_draw_boost > 0:
            add_variant(composite_draw_boost=max(0.0, base.composite_draw_boost - DRAW_STEP))

        # --- External Signal Layer — Phase 1 ---
        # All start at 0.0. Nudge up from zero to try activating each signal.
        EXT_STEP = max(scale, 0.05)

        # Referee home bias signal
        add_variant(w_ref_signal=base.w_ref_signal + EXT_STEP)
        if base.w_ref_signal > 0:
            add_variant(w_ref_signal=max(0.0, base.w_ref_signal - EXT_STEP))

        # Away travel load signal
        add_variant(w_travel_load=base.w_travel_load + EXT_STEP)
        if base.w_travel_load > 0:
            add_variant(w_travel_load=max(0.0, base.w_travel_load - EXT_STEP))

        # Fixture timing disruption signal
        add_variant(w_timing_signal=base.w_timing_signal + EXT_STEP)
        if base.w_timing_signal > 0:
            add_variant(w_timing_signal=max(0.0, base.w_timing_signal - EXT_STEP))

        # Motivation gap signal
        add_variant(w_motivation_gap=base.w_motivation_gap + EXT_STEP)
        if base.w_motivation_gap > 0:
            add_variant(w_motivation_gap=max(0.0, base.w_motivation_gap - EXT_STEP))

        return candidates
    