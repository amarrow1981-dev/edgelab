#!/usr/bin/env python3
"""
Check actual draw rates per tier against engine estimates.
Run from the edgelab folder.

Usage:
    python check_draw_rates.py --data history/
"""

import argparse
import glob
import os
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("--data", default="history/", help="Path to history folder")
args = parser.parse_args()

print("\n  Loading CSVs...")
files = glob.glob(os.path.join(args.data, "**", "*.csv"), recursive=True)

dfs = []
for f in files:
    try:
        df = pd.read_csv(f, encoding="utf-8", on_bad_lines="skip")
        if "FTR" in df.columns and "Div" in df.columns:
            dfs.append(df[["Div", "FTR"]])
    except Exception:
        try:
            df = pd.read_csv(f, encoding="latin-1", on_bad_lines="skip")
            if "FTR" in df.columns and "Div" in df.columns:
                dfs.append(df[["Div", "FTR"]])
        except Exception:
            pass

if not dfs:
    print("  No CSVs found. Check --data path.")
    raise SystemExit

df_all = pd.concat(dfs, ignore_index=True)
df_all = df_all[df_all["FTR"].isin(["H", "D", "A"])]

# Engine estimates from TIER_DRAW_RATE lookup
ENGINE_ESTIMATES = {
    "E0":  0.26,
    "E1":  0.27,
    "E2":  0.26,
    "E3":  0.25,
    "EC":  0.25,
    "B1":  0.27,
    "D1":  0.29,
    "D2":  0.27,
    "I1":  0.28,
    "I2":  0.27,
    "N1":  0.26,
    "SC0": 0.25,
    "SC1": 0.26,
    "SC2": 0.25,
    "SC3": 0.24,
    "SP1": 0.27,
    "SP2": 0.26,
}

TIER_MAP = {
    "E0": "E0", "E1": "E1", "E2": "E2", "E3": "E3", "EC": "EC",
    "B1": "B1", "D1": "D1", "D2": "D2",
    "I1": "I1", "I2": "I2", "N1": "N1",
    "SC0": "SC0", "SC1": "SC1", "SC2": "SC2", "SC3": "SC3",
    "SP1": "SP1", "SP2": "SP2",
}

print(f"\n  {'Tier':<6} {'Matches':>8} {'Actual':>8} {'Engine':>8} {'Diff':>8}  {'Status'}")
print(f"  {'-'*55}")

needs_update = []

for div_code, tier in sorted(TIER_MAP.items()):
    subset = df_all[df_all["Div"] == div_code]
    if len(subset) < 100:
        continue
    actual = (subset["FTR"] == "D").sum() / len(subset)
    estimate = ENGINE_ESTIMATES.get(tier, 0.26)
    diff = actual - estimate
    flag = ""
    if abs(diff) >= 0.01:
        flag = "UPDATE NEEDED"
        needs_update.append((tier, actual, estimate, diff))
    elif abs(diff) >= 0.005:
        flag = "minor"
    print(f"  {tier:<6} {len(subset):>8,} {actual:>8.3f} {estimate:>8.3f} {diff:>+8.3f}  {flag}")

print(f"\n  {'='*55}")
if needs_update:
    print(f"\n  Tiers needing update (diff >= 1pp):")
    for tier, actual, estimate, diff in needs_update:
        print(f"    {tier}: engine={estimate:.3f} -> actual={actual:.3f}  ({diff:+.3f})")
    print(f"\n  Update TIER_DRAW_RATE in edgelab_engine.py for these tiers.")
else:
    print(f"\n  All tiers within 1pp. Engine estimates are good.")

print()
