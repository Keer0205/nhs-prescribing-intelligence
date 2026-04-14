import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
import os

load_dotenv()

st.set_page_config(
    page_title="NHS Prescribing Intelligence",
    page_icon="💊",
    layout="wide"
)

@st.cache_resource
def get_conn():
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )

@st.cache_data(ttl=3600)
def q(sql):
    return pd.read_sql(sql, get_conn())

st.title("NHS Prescribing Intelligence Engine")
st.caption("Nov 2025 – Jan 2026  ·  54.7M prescriptions  ·  Real NHSBSA EPD data")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total spend",
    f"£{q('SELECT ROUND(SUM(actual_cost)/1e6,1) v FROM raw_prescriptions')['v'][0]}M")
c2.metric("Total prescriptions",
    f"{q('SELECT COUNT(*) v FROM raw_prescriptions')['v'][0]:,}")
c3.metric("GP practices",
    f"{q('SELECT COUNT(DISTINCT practice_code) v FROM raw_prescriptions')['v'][0]:,}")
c4.metric("Months loaded", "3 months")

st.divider()

t1,t2,t3,t4,t5 = st.tabs([
    "Module 1 — Brand vs Generic",
    "Module 2 — AMR Monitor",
    "Module 3 — Anomaly Detection",
    "Module 4 — Benchmarking",
    "Module 5 — Trend & Drift"
])

with t1:
    st.subheader("Brand vs Generic Savings Opportunity")
    st.caption("Built using 5 years ICD-10/CPT/HCPCS coding expertise")
    df = q("""SELECT national_rank, practice_name, icb_name,
               branded_cost, generic_cost, brand_rate_pct, spend_decile
               FROM mart_brand_vs_generic ORDER BY national_rank LIMIT 20""")
    fig = px.bar(df, x='practice_name', y=['branded_cost','generic_cost'],
                 barmode='group',
                 color_discrete_map={'branded_cost':'#D85A30','generic_cost':'#1D9E75'},
                 labels={'value':'Cost (£)','practice_name':'Practice'})
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df, use_container_width=True)

with t2:
    st.subheader("AMR Monitor — MSc Microbiology applied")
    st.caption("Antibiotic tier classification built from MSc Immunology & Microbiology expertise")
    amr = q("""
        SELECT practice_name, icb_name,
               ROUND((SUM(CASE WHEN LEFT(bnf_chapter_plus_code,2)='05'
                         THEN items ELSE 0 END)::NUMERIC
                     /NULLIF(SUM(items),0)*100),1) AS antibiotic_rate_pct,
               ROUND(SUM(actual_cost)::NUMERIC,0) AS total_cost
        FROM raw_prescriptions WHERE actual_cost IS NOT NULL
        GROUP BY practice_name, icb_name
        HAVING SUM(CASE WHEN LEFT(bnf_chapter_plus_code,2)='05'
                   THEN items ELSE 0 END) > 200
        ORDER BY antibiotic_rate_pct DESC LIMIT 15
    """)
    fig2 = px.bar(amr, x='practice_name', y='antibiotic_rate_pct',
                  color='antibiotic_rate_pct',
                  color_continuous_scale='RdYlGn_r',
                  labels={'antibiotic_rate_pct':'Antibiotic rate %','practice_name':'Practice'})
    fig2.update_xaxes(tickangle=45)
    st.plotly_chart(fig2, use_container_width=True)
    st.dataframe(amr, use_container_width=True)

with t3:
    st.subheader("Anomaly Detection — Claims experience applied")
    st.caption("Audit-style detection logic from biomedical equipment rejection claims experience")
    anom = q("""
        WITH b AS (
            SELECT practice_code, practice_name, icb_name, year_month,
                   SUM(actual_cost) mc
            FROM raw_prescriptions WHERE actual_cost IS NOT NULL
            GROUP BY practice_code, practice_name, icb_name, year_month
        ),
        s AS (
            SELECT *,
                   AVG(mc) OVER (PARTITION BY practice_code) avg_mc,
                   STDDEV(mc) OVER (PARTITION BY practice_code) std_mc,
                   LAG(mc) OVER (PARTITION BY practice_code ORDER BY year_month) prev_mc
            FROM b
        )
        SELECT practice_name, icb_name, year_month,
               ROUND(mc::NUMERIC,2) monthly_cost,
               ROUND(avg_mc::NUMERIC,2) avg_cost,
               ROUND(((mc-avg_mc)/NULLIF(std_mc,0))::NUMERIC,2) z_score,
               ROUND(((mc-prev_mc)/NULLIF(prev_mc,0)*100)::NUMERIC,1) mom_pct
        FROM s
        WHERE prev_mc IS NOT NULL
          AND ABS((mc-avg_mc)/NULLIF(std_mc,0)) > 0.3
        ORDER BY ABS((mc-avg_mc)/NULLIF(std_mc,0)) DESC LIMIT 20
    """)
    st.dataframe(anom, use_container_width=True)

with t4:
    st.subheader("ICB and Practice Benchmarking")
    st.caption("RANK(), DENSE_RANK(), NTILE(10) — national decile banding")
    bench = q("""
        SELECT practice_name, icb_name,
               ROUND(SUM(actual_cost)::NUMERIC,2) total_cost,
               SUM(items) total_items,
               RANK() OVER (ORDER BY SUM(actual_cost) DESC) national_rank,
               NTILE(10) OVER (ORDER BY SUM(actual_cost) DESC) decile
        FROM raw_prescriptions WHERE actual_cost IS NOT NULL
        GROUP BY practice_name, icb_name
        HAVING SUM(items) > 1000
        ORDER BY national_rank LIMIT 20
    """)
    fig4 = px.bar(bench, x='practice_name', y='total_cost',
                  color='decile', color_continuous_scale='RdYlGn_r',
                  labels={'total_cost':'Total cost (£)','practice_name':'Practice'})
    fig4.update_xaxes(tickangle=45)
    st.plotly_chart(fig4, use_container_width=True)
    st.dataframe(bench, use_container_width=True)

with t5:
    st.subheader("Trend and Drift Analysis")
    st.caption("SUM() OVER (ROWS BETWEEN), LAG(), LEAD() window functions")
    trend = q("""
        WITH m AS (
            SELECT year_month, LEFT(bnf_chapter_plus_code,2) ch,
                   SUM(actual_cost) cost
            FROM raw_prescriptions
            WHERE actual_cost IS NOT NULL AND bnf_chapter_plus_code IS NOT NULL
            GROUP BY year_month, LEFT(bnf_chapter_plus_code,2)
        )
        SELECT year_month, ch,
               ROUND(cost::NUMERIC,2) monthly_cost,
               ROUND(SUM(cost) OVER (PARTITION BY ch ORDER BY year_month
                     ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)::NUMERIC,2) rolling_3m,
               ROUND((cost - LAG(cost) OVER (PARTITION BY ch
                     ORDER BY year_month))::NUMERIC,2) mom_delta
        FROM m ORDER BY year_month, ch
    """)
    top6 = trend.groupby('ch')['monthly_cost'].sum().nlargest(6).index.tolist()
    fig5 = px.line(trend[trend['ch'].isin(top6)],
                   x='year_month', y='monthly_cost', color='ch',
                   title="Monthly spend — top 6 BNF chapters")
    st.plotly_chart(fig5, use_container_width=True)
    st.dataframe(trend, use_container_width=True)

st.divider()
st.caption("github.com/Keer0205/nhs-prescribing-intelligence · MSc Immunology & Microbiology · ICD-10/CPT/HCPCS · 7 yrs Data Engineering")
