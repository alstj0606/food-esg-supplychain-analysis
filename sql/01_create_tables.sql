SELECT
    item,
    COUNT(*) AS row_count,
    MIN(date) AS min_date,
    MAX(date) AS max_date
FROM kamis_monthly_clean
GROUP BY item
ORDER BY item;