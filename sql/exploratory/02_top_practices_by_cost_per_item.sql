-- Query 2: Top 10 practices by average cost per item
-- Identifies high-cost prescribing practices
SELECT
    practice_name,
    practice_code,
    icb_name,
    SUM(items::NUMERIC)::BIGINT AS total_items,
    ROUND(SUM(actual_cost::NUMERIC)::NUMERIC, 2) AS total_cost,
    ROUND((SUM(actual_cost::NUMERIC) / NULLIF(SUM(items::NUMERIC), 0))::NUMERIC, 2) AS avg_cost_per_item
FROM raw_prescriptions
GROUP BY practice_name, practice_code, icb_name
HAVING SUM(items::NUMERIC) > 1000
ORDER BY avg_cost_per_item DESC
LIMIT 10;
