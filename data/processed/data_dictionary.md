# NHS EPD SNOMED Data Dictionary
## Source: NHSBSA English Prescribing Dataset with SNOMED CT
## Schema version: Post-September 2025 (SNOMED-enhanced)
## Months loaded: Nov 2025, Dec 2025, Jan 2026

| Column | Type | Description | Used in |
|--------|------|-------------|---------|
| YEAR_MONTH | string | Prescribing month (YYYY-MM) | All modules |
| REGIONAL_OFFICE_NAME | string | NHS England regional office name | Module 4 |
| REGIONAL_OFFICE_CODE | string | Regional office code | Module 4 |
| ICB_NAME | string | Integrated Care Board name | All modules |
| ICB_CODE | string | ICB code | All modules |
| PCO_NAME | string | Primary Care Organisation name | Module 4 |
| PCO_CODE | string | PCO code | Module 4 |
| PRACTICE_NAME | string | GP practice name | All modules |
| PRACTICE_CODE | string | GP practice code (join key) | All modules |
| ADDRESS_1 to 4 | string | Practice address | Reference |
| POSTCODE | string | Practice postcode | Reference |
| BNF_CHEMICAL_SUBSTANCE_CODE | string | BNF chemical substance code | Modules 1,2,3 |
| BNF_CHEMICAL_SUBSTANCE | string | Drug chemical name | Modules 1,2,3 |
| BNF_PRESENTATION_CODE | string | BNF presentation code (join key) | All modules |
| BNF_PRESENTATION_NAME | string | Drug brand/generic name | Module 1 |
| BNF_CHAPTER_PLUS_CODE | string | BNF chapter code (first 2 digits = chapter) | Modules 2,4 |
| QUANTITY | float | Quantity of drug in each item | Module 3 |
| ITEMS | integer | Number of prescription items | All modules |
| TOTAL_QUANTITY | float | Total quantity dispensed | Module 3 |
| ADQ_USAGE | float | Defined daily doses | Module 2 |
| NIC | float | Net ingredient cost (£) | Reference |
| ACTUAL_COST | float | Actual cost to NHS (£) | All modules |
| UNIDENTIFIED | string | Unidentified prescriber flag | Module 3 |
| SNOMED_CODE | string | SNOMED CT clinical code | Future v2 |
