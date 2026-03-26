import duckdb
import pandas as pd

db_path = "data/processed/food_analysis.duckdb"

volatility_query = """
WITH monthly_price AS (
    SELECT
        item,
        year,
        month,
        date,
        price
    FROM kamis_monthly_clean
    WHERE price IS NOT NULL
),
price_change AS (
    SELECT
        item,
        year,
        month,
        date,
        price,
        LAG(price) OVER (
            PARTITION BY item
            ORDER BY year, month
        ) AS prev_price
    FROM monthly_price
),
volatility_base AS (
    SELECT
        item,
        year,
        month,
        date,
        price,
        prev_price,
        ROUND((price - prev_price) / prev_price * 100, 2) AS mom_change_pct
    FROM price_change
)
SELECT
    item,
    COUNT(*) AS total_months,
    ROUND(AVG(price), 2) AS avg_price,
    ROUND(STDDEV_SAMP(price), 2) AS price_stddev,
    ROUND(AVG(ABS(mom_change_pct)), 2) AS avg_abs_mom_change_pct,
    ROUND(MAX(mom_change_pct), 2) AS max_mom_increase_pct,
    ROUND(MIN(mom_change_pct), 2) AS max_mom_decrease_pct
FROM volatility_base
WHERE mom_change_pct IS NOT NULL
GROUP BY item
"""

con = duckdb.connect(db_path)
volatility_df = con.execute(volatility_query).fetchdf()

print("\n=== Volatility summary ===")
print(volatility_df)

score_cols = [
    "price_stddev",
    "avg_abs_mom_change_pct",
    "max_mom_increase_pct"
]

for col in score_cols:
    col_min = volatility_df[col].min()
    col_max = volatility_df[col].max()

    if col_max == col_min:
        volatility_df[col + "_score"] = 50.0
    else:
        volatility_df[col + "_score"] = (
            (volatility_df[col] - col_min) / (col_max - col_min) * 100
        )

volatility_df["price_volatility_score"] = (
    volatility_df["price_stddev_score"] * 0.4
    + volatility_df["avg_abs_mom_change_pct_score"] * 0.4
    + volatility_df["max_mom_increase_pct_score"] * 0.2
).round(2)

faostat_query = """
SELECT
    area,
    item,
    year,
    unit,
    emissions_value
FROM faostat_clean
WHERE area = 'Republic of Korea'
ORDER BY year
"""

faostat_score_df = con.execute(faostat_query).fetchdf()
con.close()

latest_esg = faostat_score_df.sort_values("year").iloc[-1:].copy()
latest_esg = latest_esg[["year", "emissions_value"]]

em_min = faostat_score_df["emissions_value"].min()
em_max = faostat_score_df["emissions_value"].max()

if em_max == em_min:
    latest_esg["esg_risk_score"] = 50.0
else:
    latest_esg["esg_risk_score"] = (
        (latest_esg["emissions_value"] - em_min) / (em_max - em_min) * 100
    ).round(2)

volatility_df["key"] = 1
latest_esg["key"] = 1

priority_df = volatility_df.merge(latest_esg, on="key", how="left").drop(columns=["key"])

priority_df["priority_score"] = (
    priority_df["price_volatility_score"] * 0.6
    + priority_df["esg_risk_score"] * 0.4
).round(2)

priority_df = priority_df.sort_values("priority_score", ascending=False)

print("\n=== Priority score table ===")
print(priority_df[[
    "item",
    "price_volatility_score",
    "esg_risk_score",
    "priority_score"
]])

output_path = "data/processed/priority_score_prototype.csv"
priority_df.to_csv(output_path, index=False, encoding="utf-8-sig")
print("\nSaved file:", output_path)