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
ORDER BY avg_abs_mom_change_pct DESC;