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
)
SELECT
    item,
    year,
    month,
    date,
    price,
    prev_price,
    ROUND((price - prev_price) / prev_price * 100, 2) AS mom_change_pct
FROM price_change
ORDER BY year, month;