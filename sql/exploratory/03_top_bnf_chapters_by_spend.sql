-- Query 3: Top 10 BNF chapters by total spend
-- Shows which drug categories cost the NHS most
SELECT
    LEFT(bnf_chapter_plus_code, 2) AS bnf_chapter,
    ROUND(SUM(actual_cost::NUMERIC)::NUMERIC, 2) AS total_cost_gbp,
    SUM(items::NUMERIC)::BIGINT AS total_items,
    ROUND((SUM(actual_cost::NUMERIC) / NULLIF(SUM(items::NUMERIC), 0))::NUMERIC, 2) AS avg_cost_per_item
FROM raw_prescriptions
WHERE bnf_chapter_plus_code IS NOT NULL
GROUP BY LEFT(bnf_chapter_plus_code, 2)
ORDER BY total_cost_gbp DESC
LIMIT 10;
