-- Module 5: Trend and Drift Analysis
-- SUM() OVER (ROWS BETWEEN), LAG(), LEAD()
-- Identifies rising cost categories and drifting practices

WITH monthly_totals AS (
    SELECT
        year_month,
        LEFT(bnf_chapter_plus_code, 2)      AS bnf_chapter,
        SUM(actual_cost)                    AS monthly_cost,
        SUM(items)                          AS monthly_items
    FROM raw_prescriptions
    WHERE actual_cost IS NOT NULL
      AND bnf_chapter_plus_code IS NOT NULL
    GROUP BY year_month, LEFT(bnf_chapter_plus_code, 2)
),

trend_analysis AS (
    SELECT
        year_month,
        bnf_chapter,
        ROUND(monthly_cost::NUMERIC, 2)     AS monthly_cost,
        monthly_items,
        -- Rolling 3-month total using SUM OVER
        ROUND(SUM(monthly_cost) OVER (
            PARTITION BY bnf_chapter
            ORDER BY year_month
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        )::NUMERIC, 2)                      AS rolling_3m_cost,
        -- Month-on-month delta using LAG
        ROUND((monthly_cost - LAG(monthly_cost) OVER (
            PARTITION BY bnf_chapter
            ORDER BY year_month
        ))::NUMERIC, 2)                     AS mom_cost_delta,
        -- Prior month cost
        ROUND(LAG(monthly_cost) OVER (
            PARTITION BY bnf_chapter
            ORDER BY year_month
        )::NUMERIC, 2)                      AS prev_month_cost,
        -- Next month projection flag using LEAD
        LEAD(monthly_cost) OVER (
            PARTITION BY bnf_chapter
            ORDER BY year_month
        )                                   AS next_month_cost
    FROM monthly_totals
),

final AS (
    SELECT
        year_month,
        bnf_chapter,
        monthly_cost,
        monthly_items,
        rolling_3m_cost,
        mom_cost_delta,
        prev_month_cost,
        ROUND(
            (mom_cost_delta / NULLIF(prev_month_cost, 0) * 100)::NUMERIC, 1
        )                                   AS mom_change_pct,
        CASE
            WHEN mom_cost_delta > 0 THEN 'RISING'
            WHEN mom_cost_delta < 0 THEN 'FALLING'
            ELSE 'STABLE'
        END                                 AS trend_direction,
        CASE
            WHEN (mom_cost_delta / NULLIF(prev_month_cost,0) * 100) > 10
            THEN 'DRIFT ALERT'
            ELSE 'NORMAL'
        END                                 AS drift_flag
    FROM trend_analysis
    WHERE mom_cost_delta IS NOT NULL
)

SELECT
    year_month,
    bnf_chapter,
    monthly_cost,
    rolling_3m_cost,
    mom_cost_delta,
    mom_change_pct,
    trend_direction,
    drift_flag
FROM final
ORDER BY ABS(mom_change_pct) DESC NULLS LAST
LIMIT 20;
