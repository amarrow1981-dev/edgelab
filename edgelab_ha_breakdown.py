"""
EdgeLab H/A Breakdown
----------------------
Evaluates current saved params against full dataset.
Shows H, D, A accuracy per tier so we can compare
our H/A accuracy against the market H/A only baseline.

Read-only — no params changed.

Usage:
    python edgelab_ha_breakdown.py history/
"""

import sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, ".")

from edgelab_engine import load_all_csvs, prepare_dataframe, predict_dataframe, evaluate, assign_match_round, EngineParams
from edgelab_config import load_params
from edgelab_dpol import LeagueParams
import pandas as pd

DATA_DIR = sys.argv[1] if len(sys.argv) > 1 else "data/"

print("\n╔══════════════════════════════════════════╗")
print("║   EdgeLab H/A Breakdown vs Market        ║")
print("╚══════════════════════════════════════════╝\n")

print("  Loading CSVs...")
df_all = load_all_csvs(DATA_DIR)
print(f"  Loaded {len(df_all)} rows\n")

TIERS = ["E0","E1","E2","E3","EC","B1","D1","D2","I1","I2","N1","SC0","SC1","SC2","SC3","SP1","SP2"]

# Market H/A only baselines from last run
MARKET_HA = {
    "E0": 0.722, "E1": 0.640, "E2": 0.647, "E3": 0.620, "EC": 0.651,
    "B1": 0.702, "D1": 0.689, "D2": 0.648, "I1": 0.735, "I2": 0.662,
    "N1": 0.734, "SC0": 0.700, "SC1": 0.654, "SC2": 0.650, "SC3": 0.635,
    "SP1": 0.715, "SP2": 0.659,
}

results = []

for tier in TIERS:
    df = df_all[df_all["tier"] == tier].copy()
    if df.empty:
        continue

    lp = load_params(tier)
    if lp is None:
        print(f"  {tier}: no saved params — skipping")
        continue

    ep = EngineParams(
        w_form=lp.w_form, w_gd=lp.w_gd, home_adv=lp.home_adv,
        dti_edge_scale=lp.dti_edge_scale, dti_ha_scale=lp.dti_ha_scale,
        draw_margin=lp.draw_margin, coin_dti_thresh=lp.coin_dti_thresh,
        draw_pull=lp.draw_pull, dti_draw_lock=lp.dti_draw_lock,
        w_draw_odds=lp.w_draw_odds, w_draw_tendency=lp.w_draw_tendency,
        w_h2h_draw=lp.w_h2h_draw, draw_score_thresh=lp.draw_score_thresh,
        w_score_margin=lp.w_score_margin, w_btts=lp.w_btts,
        w_ref_signal=lp.w_ref_signal, w_travel_load=lp.w_travel_load,
        w_timing_signal=lp.w_timing_signal, w_motivation_gap=lp.w_motivation_gap,
        form_window=5,
    )

    df = assign_match_round(df)
    df_feat = prepare_dataframe(df.copy(), ep)
    df_pred = predict_dataframe(df_feat, ep)
    stats = evaluate(df_pred)

    overall = stats["accuracy"]
    h_acc = stats["breakdown"].get("H", 0.0)
    d_acc = stats["breakdown"].get("D", 0.0)
    a_acc = stats["breakdown"].get("A", 0.0)

    # Our H/A only — accuracy on matches that actually ended H or A
    df_ha = df_pred[df_pred["FTR"].isin(["H", "A"])].copy()
    ha_total = len(df_ha)
    ha_correct = (df_ha["prediction"] == df_ha["FTR"]).sum()
    our_ha_acc = ha_correct / ha_total if ha_total > 0 else 0.0

    market_ha = MARKET_HA.get(tier, 0.0)
    ha_gap = our_ha_acc - market_ha

    results.append({
        "tier": tier,
        "overall": overall,
        "h_acc": h_acc,
        "d_acc": d_acc,
        "a_acc": a_acc,
        "our_ha_acc": our_ha_acc,
        "market_ha": market_ha,
        "ha_gap": ha_gap,
    })

print("╔══════════════════════════════════════════════════════════════════════════════════════════╗")
print("║                        EDGELAB vs MARKET — H/A BREAKDOWN                                ║")
print("╠════════╦══════════╦═══════════╦═══════════╦═══════════╦═══════════╦═══════════╦═════════╣")
print("║  Tier  ║ Overall  ║  H acc    ║  D acc    ║  A acc    ║ Our H/A   ║ Mkt H/A   ║  Gap    ║")
print("╠════════╬══════════╬═══════════╬═══════════╬═══════════╬═══════════╬═══════════╬═════════╣")
for r in results:
    gap_sign = "+" if r["ha_gap"] >= 0 else ""
    gap_flag = "✓" if r["ha_gap"] >= 0 else "✗"
    print(f"║  {r['tier']:<4}  ║  {r['overall']:>5.1%}   ║   {r['h_acc']:>5.1%}   ║   {r['d_acc']:>5.1%}   ║   {r['a_acc']:>5.1%}   ║   {r['our_ha_acc']:>5.1%}   ║   {r['market_ha']:>5.1%}   ║ {gap_flag}{gap_sign}{r['ha_gap']:>5.1%} ║")
print("╚════════╩══════════╩═══════════╩═══════════╩═══════════╩═══════════╩═══════════╩═════════╝")

print("\n  Our H/A  = EdgeLab accuracy on matches that actually ended H or A")
print("  Mkt H/A  = Market accuracy on same subset")
print("  Gap      = positive means we beat the market on H/A calls\n")
