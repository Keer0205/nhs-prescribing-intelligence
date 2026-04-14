-- Module 4: ICB and Practice Benchmarking
-- RANK(), DENSE_RANK(), NTILE(10), CASE WHEN pivot
-- Produces national practice leaderboard with decile banding

WITH practice_totals AS (
    SELECT
        practice_code,
        practice_name,
        icb_name,
        icb_code,
        regional_office_name,
        SUM(actual_cost)        AS total_cost,
        SUM(items)              AS total_items,
        COUNT(DISTINCT year_month) AS months_active,
        -- BNF chapter cost breakdown using CASE WHEN pivot
        SUM(CASE WHEN LEFT(bnf_chapter_plus_code,2) = '01' THEN actual_cost ELSE 0 END) AS gastro_cost,
        SUM(CASE WHEN LEFT(bnf_chapter_plus_code,2) = '02' THEN actual_cost ELSE 0 END) AS cardio_cost,
        SUM(CASE WHEN LEFT(bnf_chapter_plus_code,2) = '03' THEN actual_cost ELSE 0 END) AS respiratory_cost,
        SUM(CASE WHEN LEFT(bnf_chapter_plus_code,2) = '04' THEN actual_cost ELSE 0 END) AS cns_cost,
        SUM(CASE WHEN LEFT(bnf_chapter_plus_code,2) = '05' THEN actual_cost ELSE 0 END) AS infection_cost,
        SUM(CASE WHEN LEFT(bnf_chapter_plus_code,2) = '06' THEN actual_cost ELSE 0 END) AS endocrine_cost
    FROM raw_prescriptions
    WHERE actual_cost IS NOT NULL
      AND bnf_chapter_plus_code IS NOT NULL
    GROUP BY practice_code, practice_name, icb_name, icb_code, regional_office_name
),

ranked AS (
    SELECT
        practice_code,
        practice_name,
        icb_name,
        icb_code,
        regional_office_name,
        ROUND(total_cost::NUMERIC, 2)           AS total_cost,
        total_items,
        ROUND(gastro_cost::NUMERIC, 2)          AS gastro_cost,
        ROUND(cardio_cost::NUMERIC, 2)          AS cardio_cost,
        ROUND(respiratory_cost::NUMERIC, 2)     AS respiratory_cost,
        ROUND(cns_cost::NUMERIC, 2)             AS cns_cost,
        ROUND(endocrine_cost::NUMERIC, 2)       AS endocrine_cost,
        -- National rankings
        RANK() OVER (ORDER BY total_cost DESC)                          AS national_rank,
        DENSE_RANK() OVER (ORDER BY total_cost DESC)                    AS national_dense_rank,
        NTILE(10) OVER (ORDER BY total_cost DESC)                       AS cost_decile,
        -- ICB-level ranking
        RANK() OVER (PARTITION BY icb_code ORDER BY total_cost DESC)    AS rank_in_icb,
        -- Regional ranking
        RANK() OVER (PARTITION BY regional_office_name ORDER BY total_cost DESC) AS rank_in_region
    FROM practice_totals
    WHERE total_items > 1000
)

SELECT
    national_rank,
    cost_decile,
    practice_name,
    practice_code,
    icb_name,
    total_cost,
    total_items,
    rank_in_icb,
    cardio_cost,
    endocrine_cost,
    cns_cost,
    CASE
        WHEN cost_decile = 1  THEN 'Top 10% nationally'
        WHEN cost_decile <= 3 THEN 'High spend'
        WHEN cost_decile <= 7 THEN 'Mid range'
        ELSE 'Low spend'
    END AS spend_band
FROM ranked
ORDER BY national_rank
LIMIT 20;
