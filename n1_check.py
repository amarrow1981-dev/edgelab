import json, glob, os
import pandas as pd

# Check params.json N1 entry
with open('edgelab_params.json') as f:
    p = json.load(f)
n1 = p.get('N1', {})
print(f"params.json N1 matches: {n1.get('matches')}")
print(f"params.json N1 source:  {n1.get('source')}")
print(f"params.json N1 saved:   {str(n1.get('saved_at', ''))[:10]}")

# Check what N1 CSVs are actually in history/
n1_files = sorted(glob.glob('history/N1*.csv'))
print(f"\nN1 CSV files found: {len(n1_files)}")
for f in n1_files:
    print(f"  {os.path.basename(f)}")

# Count actual rows
from edgelab_engine import load_all_csvs
df = load_all_csvs('history/', tiers=['N1'])
print(f"\nActual N1 rows loaded: {len(df)}")
print(f"Seasons: {sorted(df['season'].unique())}")
