-- Module 1: Brand vs Generic Savings Opportunity
-- Uses BNF presentation codes to identify branded vs generic prescribing
-- Built using 5 years ICD-10/CPT/HCPCS coding expertise for drug classification

-- Step 1: Classify each prescription as branded or generic
-- Generic indicator: bnf_presentation_code ends in A0 (standard generic suffix in BNF)
WITH classified AS (
    SELECT
        practice_code,
        practice_name,
        icb_name,
        icb_code,
        bnf_chemical_substance_code,
        bnf_chemical_substance,
        bnf_presentation_code,
        bnf_presentation_name,
        actual_cost,
        items,
        -- Generic if presentation code ends in A0 (BNF generic convention)
        CASE
            WHEN RIGHT(bnf_presentation_code, 2) = 'A0' THEN 'Generic'
            ELSE 'Branded'
        END AS prescription_type
    FROM raw_prescriptions
    WHERE actual_cost IS NOT NULL
      AND bnf_presentation_code IS NOT NULL
),

-- Step 2: Aggregate by practice and type
practice_summary AS (
    SELECT
        practice_code,
        practice_name,
        icb_name,
        icb_code,
        SUM(CASE WHEN prescription_type = 'Branded' THEN actual_cost ELSE 0 END) AS branded_cost,
        SUM(CASE WHEN prescription_type = 'Generic'  THEN actual_cost ELSE 0 END) AS generic_cost,
        SUM(CASE WHEN prescription_type = 'Branded' THEN items ELSE 0 END)        AS branded_items,
        SUM(CASE WHEN prescription_type = 'Generic'  THEN items ELSE 0 END)       AS generic_items,
        SUM(actual_cost)  AS total_cost,
        SUM(items)        AS total_items
    FROM classified
    GROUP BY practice_code, practice_name, icb_name, icb_code
),

-- Step 3: Calculate brand rate and rank within ICB
ranked AS (
    SELECT
        practice_code,
        practice_name,
        icb_name,
        icb_code,
        ROUND(branded_cost::NUMERIC, 2)      AS branded_cost,
        ROUND(generic_cost::NUMERIC, 2)      AS generic_cost,
        ROUND(total_cost::NUMERIC, 2)        AS total_cost,
        branded_items,
        generic_items,
        total_items,
        ROUND((branded_cost / NULLIF(total_cost, 0) * 100)::NUMERIC, 1) AS brand_rate_pct,
        RANK() OVER (
            PARTITION BY icb_code
            ORDER BY branded_cost DESC
        ) AS rank_in_icb,
        RANK() OVER (
            ORDER BY branded_cost DESC
        ) AS national_rank
    FROM practice_summary
    WHERE total_items > 500
)

-- Step 4: Top 20 practices by branded spend nationally
SELECT
    national_rank,
    practice_name,
    practice_code,
    icb_name,
    branded_cost,
    generic_cost,
    total_cost,
    brand_rate_pct,
    rank_in_icb
FROM ranked
ORDER BY national_rank
LIMIT 20;
