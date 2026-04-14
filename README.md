# NHS Prescribing Intelligence Engine

> Live dashboard analysing 54.7M NHS prescriptions (Nov 2025 – Jan 2026)

🔗 **[Live Demo](https://nhs-prescribing-intelligence-xqmppaqteys4rwsy6bqpk5.streamlit.app)**

## Overview
Built by Keerthana Murugesan — combining 7 years of Data Engineering with an MSc in Immunology & Microbiology and ICD-10/CPT/HCPCS coding expertise to build a clinically meaningful NHS prescribing analytics platform.

## Modules
| Module | Description |
|--------|-------------|
| Brand vs Generic | Identifies savings opportunities across practices |
| AMR Monitor | Antibiotic resistance patterns using MSc Microbiology classification |
| Anomaly Detection | Cost outliers by practice and BNF chapter |
| Benchmarking | Practice efficiency across ICBs |
| Trend & Drift | Monthly spend trends with rolling averages |

## Tech Stack
- **Database:** PostgreSQL (local 54M rows) + Supabase (cloud)
- **Transformation:** dbt
- **Dashboard:** Streamlit + Plotly
- **Language:** Python, SQL
- **Deployment:** Streamlit Cloud

## Data
- Source: NHS England EPD SNOMED (Nov 2025, Dec 2025, Jan 2026)
- 54,691,186 prescription rows
- 5 aggregated summary tables for cloud deployment
