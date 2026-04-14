-- Module 3: Cost and Quantity Anomaly Detection
-- Built using biomedical equipment rejection claims experience
-- Applies audit-style detection logic to prescribing data

-- Step 1: Calculate practice-level baselines
WITH practice_baseline AS (
    SELECT
        practice_code,
        practice_name,
        icb_name,
        icb_code,
        year_month,
        SUM(actual_cost)     AS monthly_cost,
        SUM(items)           AS monthly_items,
        SUM(total_quantity)  AS monthly_quantity
    FROM raw_prescriptions
    WHERE actual_cost IS NOT NULL
    GROUP BY practice_code, practice_name, icb_name, icb_code, year_month
),

-- Step 2: Calculate rolling stats per practice
practice_stats AS (
    SELECT
        practice_code,
        practice_name,
        icb_name,
        icb_code,
        year_month,
        monthly_cost,
        monthly_items,
        monthly_quantity,
        AVG(monthly_cost) OVER (
            PARTITION BY practice_code
        ) AS avg_monthly_cost,
        STDDEV(monthly_cost) OVER (
            PARTITION BY practice_code
        ) AS stddev_monthly_cost,
        LAG(monthly_cost) OVER (
            PARTITION BY practice_code
            ORDER BY year_month
        ) AS prev_month_cost,
        LAG(monthly_items) OVER (
            PARTITION BY practice_code
            ORDER BY year_month
        ) AS prev_month_items
    FROM practice_baseline
),

-- Step 3: Calculate z-scores and month-on-month changes
anomaly_flags AS (
    SELECT
        practice_code,
        practice_name,
        icb_name,
        icb_code,
        year_month,
        ROUND(monthly_cost::NUMERIC, 2)      AS monthly_cost,
        ROUND(avg_monthly_cost::NUMERIC, 2)  AS avg_monthly_cost,
        ROUND(
            ((monthly_cost - avg_monthly_cost) /
             NULLIF(stddev_monthly_cost, 0))::NUMERIC, 2
        ) AS cost_z_score,
        ROUND(
            ((monthly_cost - prev_month_cost) /
             NULLIF(prev_month_cost, 0) * 100)::NUMERIC, 1
        ) AS mom_cost_change_pct,
        ROUND(
            ((monthly_items - prev_month_items) /
             NULLIF(prev_month_items, 0) * 100)::NUMERIC, 1
        ) AS mom_items_change_pct,
        -- Anomaly classification (claims-informed logic)
        CASE
            WHEN ((monthly_cost - avg_monthly_cost) /
                   NULLIF(stddev_monthly_cost, 0)) > 2.0
            THEN 'COST SPIKE'
            WHEN ((monthly_cost - prev_month_cost) /
                   NULLIF(prev_month_cost, 0) * 100) > 50
            THEN 'MOM SPIKE'
            WHEN ((monthly_cost - prev_month_cost) /
                   NULLIF(prev_month_cost, 0) * 100) < -50
            THEN 'MOM DROP'
            ELSE 'NORMAL'
        END AS anomaly_type
    FROM practice_stats
    WHERE prev_month_cost IS NOT NULL
)

-- Step 4: Return flagged anomalies only
SELECT
    year_month,
    practice_name,
    practice_code,
    icb_name,
    monthly_cost,
    avg_monthly_cost,
    cost_z_score,
    mom_cost_change_pct,
    anomaly_type
FROM anomaly_flags
WHERE anomaly_type != 'NORMAL'
ORDER BY ABS(cost_z_score) DESC NULLS LAST
LIMIT 20;
