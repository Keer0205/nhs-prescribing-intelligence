-- Module 2: Antimicrobial Resistance Prescribing Monitor
-- Built using MSc Immunology & Microbiology expertise
-- Antibiotic tier classification manually constructed from microbiology knowledge
-- BNF Chapter 05 = Infections

-- Step 1: Extract all antibiotic prescriptions (BNF chapter 05)
WITH antibiotic_prescriptions AS (
    SELECT
        r.practice_code,
        r.practice_name,
        r.icb_name,
        r.icb_code,
        r.year_month,
        r.bnf_chemical_substance,
        r.bnf_presentation_code,
        r.actual_cost,
        r.items,
        -- Classify using our MSc-informed tier table
        COALESCE(t.resistance_tier, 'Broad') AS resistance_tier,
        COALESCE(t.spectrum, 'Broad-spectrum') AS spectrum
    FROM raw_prescriptions r
    LEFT JOIN amr_tier_classification t
        ON LEFT(r.bnf_presentation_code, 6) = t.bnf_section_code
    WHERE LEFT(r.bnf_chapter_plus_code, 2) = '05'
      AND r.actual_cost IS NOT NULL
),

-- Step 2: Summarise by practice and month
practice_amr AS (
    SELECT
        practice_code,
        practice_name,
        icb_name,
        icb_code,
        year_month,
        SUM(items) AS total_antibiotic_items,
        SUM(CASE WHEN resistance_tier IN ('Broad','Restricted') THEN items ELSE 0 END) AS broad_spectrum_items,
        SUM(CASE WHEN resistance_tier = 'Narrow' THEN items ELSE 0 END) AS narrow_spectrum_items,
        SUM(CASE WHEN resistance_tier = 'Restricted' THEN items ELSE 0 END) AS restricted_items,
        SUM(actual_cost) AS total_antibiotic_cost
    FROM antibiotic_prescriptions
    GROUP BY practice_code, practice_name, icb_name, icb_code, year_month
),

-- Step 3: Calculate broad-spectrum rate per practice
practice_rates AS (
    SELECT
        practice_code,
        practice_name,
        icb_name,
        icb_code,
        SUM(total_antibiotic_items)   AS total_items,
        SUM(broad_spectrum_items)     AS broad_spectrum_items,
        SUM(narrow_spectrum_items)    AS narrow_spectrum_items,
        SUM(restricted_items)         AS restricted_items,
        SUM(total_antibiotic_cost)    AS total_cost,
        ROUND(
            (SUM(broad_spectrum_items)::NUMERIC /
             NULLIF(SUM(total_antibiotic_items), 0) * 100)::NUMERIC, 1
        ) AS broad_spectrum_rate_pct
    FROM practice_amr
    WHERE total_antibiotic_items > 100
    GROUP BY practice_code, practice_name, icb_name, icb_code
),

-- Step 4: Z-score detection — flag outlier practices
icb_stats AS (
    SELECT
        icb_code,
        AVG(broad_spectrum_rate_pct)    AS icb_avg_rate,
        STDDEV(broad_spectrum_rate_pct) AS icb_stddev_rate
    FROM practice_rates
    GROUP BY icb_code
)

-- Step 5: Final output with z-score and stewardship flag
SELECT
    pr.practice_name,
    pr.practice_code,
    pr.icb_name,
    pr.broad_spectrum_rate_pct,
    ROUND(is2.icb_avg_rate::NUMERIC, 1)     AS icb_avg_rate,
    ROUND(
        ((pr.broad_spectrum_rate_pct - is2.icb_avg_rate) /
         NULLIF(is2.icb_stddev_rate, 0))::NUMERIC, 2
    ) AS z_score,
    pr.total_items,
    pr.restricted_items,
    CASE
        WHEN ((pr.broad_spectrum_rate_pct - is2.icb_avg_rate) /
               NULLIF(is2.icb_stddev_rate, 0)) > 2.0 THEN 'HIGH FLAG'
        WHEN ((pr.broad_spectrum_rate_pct - is2.icb_avg_rate) /
               NULLIF(is2.icb_stddev_rate, 0)) > 1.0 THEN 'MONITOR'
        ELSE 'NORMAL'
    END AS stewardship_flag
FROM practice_rates pr
JOIN icb_stats is2 USING (icb_code)
ORDER BY z_score DESC NULLS LAST
LIMIT 20;
