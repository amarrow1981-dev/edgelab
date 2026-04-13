"""
EdgeLab Market Baseline Calculator
-----------------------------------
Uses B365 odds to establish the bookmaker market baseline per tier.
Method: convert B365H/D/A to implied probabilities, pick the favourite
(highest implied prob), measure how often that wins historically.

Also calculates H/A only accuracy — strips draws from both actual results
and market picks to show the true competitive gap excluding draw blindness.

Usage:
    python edgelab_market_baseline.py history/
"""

import sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, ".")

from edgelab_engine import load_all_csvs
import pandas as pd

DATA_DIR = sys.argv[1] if len(sys.argv) > 1 else "data/"

print("\n╔══════════════════════════════════════════╗")
print("║   EdgeLab Market Baseline Calculator     ║")
print("╚══════════════════════════════════════════╝\n")

print("  Loading CSVs...")
df_all = load_all_csvs(DATA_DIR)
print(f"  Loaded {len(df_all)} rows\n")

TIERS = ["E0","E1","E2","E3","EC","B1","D1","D2","I1","I2","N1","SC0","SC1","SC2","SC3","SP1","SP2"]

results = []

for tier in TIERS:
    df = df_all[df_all["tier"] == tier].copy()
    if df.empty:
        continue

    needed = ["B365H", "B365D", "B365A", "FTR"]
    if not all(c in df.columns for c in needed):
        print(f"  {tier}: missing B365 columns — skipping")
        continue

    df = df[needed].copy()
    for col in ["B365H", "B365D", "B365A"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["B365H", "B365D", "B365A", "FTR"])
    if df.empty:
        continue

    total = len(df)

    # Convert to implied probabilities (raw — includes overround)
    df["imp_h"] = 1.0 / df["B365H"]
    df["imp_d"] = 1.0 / df["B365D"]
    df["imp_a"] = 1.0 / df["B365A"]

    # Market favourite = outcome with highest implied prob
    df["market_pick"] = df[["imp_h","imp_d","imp_a"]].idxmax(axis=1).map({
        "imp_h": "H", "imp_d": "D", "imp_a": "A"
    })

    # Overall market baseline accuracy
    correct = (df["market_pick"] == df["FTR"]).sum()
    market_overall_acc = correct / total

    # H/A only — strip matches that actually ended in a draw
    # Both sides are blind to draws so compare on the ~75% where a result happened
    df_ha = df[df["FTR"].isin(["H", "A"])].copy()
    ha_total = len(df_ha)
    ha_correct = (df_ha["market_pick"] == df_ha["FTR"]).sum()
    market_ha_acc = ha_correct / ha_total if ha_total > 0 else 0.0

    # Actual result distribution
    actual_counts = df["FTR"].value_counts().to_dict()
    draw_rate = actual_counts.get("D", 0) / total

    # Coverage
    raw_count = len(df_all[df_all["tier"] == tier])
    coverage = total / raw_count if raw_count > 0 else 0

    results.append({
        "tier": tier,
        "matches": total,
        "ha_matches": ha_total,
        "coverage": coverage,
        "market_overall": market_overall_acc,
        "market_ha_acc": market_ha_acc,
        "actual_draw_rate": draw_rate,
    })

# Summary table
print("╔═══════════════════════════════════════════════════════════════════════════════════╗")
print("║                         MARKET BASELINE — FULL PICTURE                           ║")
print("╠════════╦══════════╦══════════╦═════════════════╦══════════════════╦══════════════╣")
print("║  Tier  ║ Matches  ║ Draw Rate║  Mkt Overall    ║  Mkt H/A Only   ║   Coverage   ║")
print("╠════════╬══════════╬══════════╬═════════════════╬══════════════════╬══════════════╣")
for r in results:
    print(f"║  {r['tier']:<4}  ║  {r['matches']:>6}  ║  {r['actual_draw_rate']:>5.1%}   ║     {r['market_overall']:>6.1%}      ║      {r['market_ha_acc']:>6.1%}      ║    {r['coverage']:>6.1%}    ║")
print("╚════════╩══════════╩══════════╩═════════════════╩══════════════════╩══════════════╝")

print("\n  Mkt Overall  = market accuracy on all matches (draws included)")
print("  Mkt H/A Only = market accuracy on matches that actually ended H or A")
print("  The gap between these two shows how much draw blindness costs both sides.")
print("  EdgeLab H/A accuracy should be compared against Mkt H/A Only for a fair fight.\n")
