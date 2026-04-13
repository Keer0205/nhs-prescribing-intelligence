-- Staging model: clean and type-cast raw prescriptions
-- Source: raw_prescriptions (54.7M rows, Nov 2025 - Jan 2026)

SELECT
    year_month,
    regional_office_name,
    regional_office_code,
    icb_name,
    icb_code,
    practice_name,
    practice_code,
    postcode,
    bnf_chemical_substance_code,
    bnf_chemical_substance,
    bnf_presentation_code,
    bnf_presentation_name,
    bnf_chapter_plus_code,
    LEFT(bnf_chapter_plus_code, 2)          AS bnf_chapter,
    CAST(quantity AS NUMERIC)               AS quantity,
    CAST(items AS NUMERIC)                  AS items,
    CAST(total_quantity AS NUMERIC)         AS total_quantity,
    CAST(actual_cost AS NUMERIC)            AS actual_cost,
    CAST(nic AS NUMERIC)                    AS nic,
    snomed_code
FROM {{ source('public', 'raw_prescriptions') }}
WHERE actual_cost IS NOT NULL
  AND practice_code IS NOT NULL
  AND bnf_chapter_plus_code IS NOT NULL
