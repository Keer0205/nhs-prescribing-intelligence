# NHS Prescribing Cost, Variation & Antimicrobial Intelligence Engine

> A population-level prescribing analytics platform built on real NHS England data

🔗 **[Live Demo](https://nhs-prescribing-intelligence-xqmppaqteys4rwsy6bqpk5.streamlit.app)** | **[GitHub](https://github.com/Keer0205/nhs-prescribing-intelligence)**

---

## What This Project Is

A population-level prescribing analytics platform built on real NHS England prescribing data. It surfaces prescribing cost variation, generic savings opportunities, antimicrobial prescribing patterns, and unusual cost and quantity anomalies across GP practices and Integrated Care Boards in England.

**54,691,186 real NHS prescription rows · Nov 2025 – Jan 2026 · All ICBs in England**

---

## Why I Built This

Built by Keerthana Murugesan, combining:
- **7 years Data Engineering** — pipeline design, PostgreSQL, dbt, Python
- **MSc Immunology & Microbiology** — AMR tier classification built from domain knowledge, not a generic BNF lookup
- **5 years ICD-10/CPT/HCPCS coding** — drug reference system structure and therapeutic area groupings
- **2 years biomedical equipment claims** — anomaly detection logic from real rejection claim experience

> OpenPrescribing is an excellent tool built on the same NHSBSA dataset. My project does three things it does not: (1) demonstrates the full engineering pipeline — 50M row ingestion, star schema, dbt testing, dashboard deployment; (2) applies a custom AMR resistance tier classification built from MSc Microbiology knowledge; (3) uses audit-style anomaly detection logic from biomedical claims experience.

---

## Five Modules

| Module | What It Does | Key Technique |
|--------|-------------|---------------|
| Brand vs Generic | Savings opportunity across practices | CTEs, RANK(), dm+d join |
| AMR Monitor | Antibiotic resistance patterns by ICB | Custom MSc tier table, z-score |
| Anomaly Detection | Cost and quantity outliers | IQR, LAG(), audit flags |
| Benchmarking | Practice efficiency leaderboard | NTILE(10), DENSE_RANK() |
| Trend & Drift | Monthly spend with rolling averages | SUM() OVER, ROWS BETWEEN |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Database | PostgreSQL 16 |
| Transformation | dbt (with tests) |
| Dashboard | Streamlit + Plotly |
| Cloud DB | Supabase |
| Deployment | Streamlit Cloud |
| Language | Python, SQL |

---

## Data Source

- **NHSBSA English Prescribing Dataset (EPD)** — Nov 2025, Dec 2025, Jan 2026
- Downloaded via NHSBSA CKAN API (fully automatable, no browser needed)
- 54,691,186 rows · ~23GB raw · aggregated to 5 summary tables for cloud deployment

---

## Running Locally

```bash
git clone https://github.com/Keer0205/nhs-prescribing-intelligence
cd nhs-prescribing-intelligence
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
streamlit run dashboard/app.py
```

Add `.streamlit/secrets.toml` with your PostgreSQL credentials.

---

*MSc Immunology & Microbiology · ICD-10/CPT/HCPCS · 7 yrs Data Engineering · NHS England EPD*
