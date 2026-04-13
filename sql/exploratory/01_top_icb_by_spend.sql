-- Query 1: Top 10 ICBs by total actual cost
-- Nov 2025 - Jan 2026 | NHS England prescribing data
SELECT
    icb_name,
    icb_code,
    ROUND(SUM(actual_cost::NUMERIC)::NUMERIC, 2) AS total_cost_gbp,
    SUM(items::NUMERIC)::BIGINT AS total_items,
    COUNT(DISTINCT practice_code) AS practice_count
FROM raw_prescriptions
GROUP BY icb_name, icb_code
ORDER BY total_cost_gbp DESC
LIMIT 10;
