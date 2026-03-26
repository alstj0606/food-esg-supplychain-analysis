import duckdb
from pathlib import Path

db_path = "data/processed/food_analysis.duckdb"
sql_path = "sql/03_volatility_summary.sql"

con = duckdb.connect(db_path)

query = Path(sql_path).read_text(encoding="utf-8")
results = con.execute(query).fetchdf()

print(results)

con.close()