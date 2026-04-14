import sqlite3
import pandas as pd

conn = sqlite3.connect('edgelab.db')

# Check total rows and date range
print("=== FIXTURES TABLE ===")
df = pd.read_sql("SELECT COUNT(*) as total, MIN(match_date) as earliest, MAX(match_date) as latest FROM fixtures", conn)
print(df.to_string())

# Sample recent rows to see date format and whether actual_result is populated
print("\n=== MOST RECENT 20 ROWS ===")
df2 = pd.read_sql("""
    SELECT tier, match_date, home_team, away_team, prediction, actual_result, correct 
    FROM fixtures 
    ORDER BY match_date DESC 
    LIMIT 20
""", conn)
print(df2.to_string())

# Check how many rows have actual_result filled
print("\n=== COMPLETION STATUS ===")
df3 = pd.read_sql("SELECT COUNT(*) as total, SUM(CASE WHEN actual_result IS NOT NULL THEN 1 ELSE 0 END) as completed FROM fixtures", conn)
print(df3.to_string())

conn.close()
