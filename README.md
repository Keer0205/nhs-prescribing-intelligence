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

## Performance Engineering

One of the key challenges of this project was making 54,691,186 rows queryable at speed.

### Indexing Strategy

After bulk loading, 5 indexes were created on raw_prescriptions. The query planner switched from a full sequential scan to a Bitmap Index Scan.

| Query type | Before indexing | After indexing | Improvement |
|-----------|----------------|---------------|-------------|
| Filtered practice lookup | ~39,000 ms | 7.8 ms | 99.98% faster |

### Materialised Views

Summary tables pre-aggregate the 54M row fact table into 5 lean reporting tables (~26MB total), powering sub-second dashboard load times on Streamlit Cloud.

## Known Limitations

- Population-level only — The NHSBSA EPD does not contain patient-level records or linked ICD-10 diagnosis codes. All analysis is at practice, ICB, or drug category level.
- v1.0 uses Nov 2025-Jan 2026 EPD SNOMED CT-enhanced schema. v2.0 will incorporate additional SNOMED dimensions.
- Brand vs generic savings are opportunity estimates. Some branded prescribing is clinically justified.
- The live dashboard queries pre-aggregated summary tables, not the full 54M row dataset, to enable cloud deployment within Supabase free tier limits.

## Key Findings

Three genuine insights from 54,691,186 NHS prescriptions (Nov 2025–Jan 2026):

### Finding 1 — Antimicrobial Resistance Risk
Accrington Minor Injuries Unit prescribes broad-spectrum antibiotics at **78.5%** of all antibiotic items — nearly 3x the NHS stewardship recommended threshold. Out-of-hours and urgent care services consistently dominate the AMR outlier list. Under time pressure, broad-spectrum becomes the default. This is the pattern NHS stewardship programmes exist to address.

### Finding 2 — Brand vs Generic Savings Opportunity
Three appliance prescribing services show **100% branded prescribing** with zero generic usage:
- NHS Surrey ICB Appliance Service: £2.9M branded, £0 generic
- Notts Appliance Management Service: £2.5M branded, £0 generic
- BLMK Appliance Prescribing Service: £2.5M branded, £0 generic

These represent the highest savings opportunity practices in England for commissioner review.

### Finding 3 — Highest Spend BNF Chapter
BNF Chapter 06 (Endocrine System — includes diabetes medications) is consistently the highest spending chapter across all 3 months:
- Dec 2025: £206M
- Jan 2026: £197M
- Nov 2025: £190M

This reflects the growing diabetes medication burden on NHS prescribing budgets, driven by GLP-1 receptor agonists and insulin.
