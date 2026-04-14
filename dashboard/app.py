import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text

st.set_page_config(page_title="NHS Prescribing Intelligence", layout="wide")
st.title("NHS Prescribing Intelligence Engine")
st.caption("54M+ rows · Nov 2025–Jan 2026 · Built by Keer0205")

db = st.secrets["connections"]["postgresql"]
engine = create_engine(
    f"postgresql+psycopg2://{db['username']}:{db['password']}@{db['host']}:{db['port']}/{db['database']}"
)

def q(sql): 
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn)

k1,k2,k3 = st.columns(3)
k1.metric("Total Prescriptions", "54.7M", "Nov 2025-Jan 2026")
k2.metric("Total Spend", "£8.2B+", "3 months NHS England")
k3.metric("Practices Analysed", "10,000+", "All ICBs")

t1,t2,t3,t4,t5 = st.tabs(["Brand vs Generic","AMR Monitor","Anomaly Detection","Benchmarking","Trend & Drift"])

with t1:
    st.subheader("Brand vs Generic Savings Opportunity")
    st.caption("Built using 5 years ICD-10/CPT/HCPCS coding expertise")
    df = q("SELECT national_rank, practice_name, icb_name, branded_cost, generic_cost, brand_rate_pct, spend_decile FROM summary_brand_vs_generic ORDER BY national_rank LIMIT 20")
    fig = px.bar(df, x='practice_name', y=['branded_cost','generic_cost'], barmode='group', color_discrete_map={'branded_cost':'#D85A30','generic_cost':'#1D9E75'}, labels={'value':'Cost (£)','practice_name':'Practice'})
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df, use_container_width=True)

with t2:
    st.subheader("AMR Monitor — MSc Microbiology applied")
    st.caption("Antibiotic tier classification built from MSc Immunology & Microbiology expertise")
    amr = q("SELECT practice_name, icb_name, antibiotic_rate_pct, total_cost FROM summary_amr ORDER BY antibiotic_rate_pct DESC")
    fig2 = px.bar(amr, x='practice_name', y='antibiotic_rate_pct', color='icb_name', labels={'antibiotic_rate_pct':'Antibiotic Rate (%)','practice_name':'Practice'})
    fig2.update_xaxes(tickangle=45)
    st.plotly_chart(fig2, use_container_width=True)
    st.dataframe(amr, use_container_width=True)

with t3:
    st.subheader("Anomaly Detection")
    st.caption("Cost outliers by practice and BNF chapter")
    anomaly = q("SELECT practice_name, icb_name, bnf_chapter_plus_code, total_cost, avg_cost, rx_count FROM summary_anomaly ORDER BY total_cost DESC LIMIT 50")
    fig3 = px.scatter(anomaly, x='rx_count', y='avg_cost', color='icb_name', hover_data=['practice_name','bnf_chapter_plus_code'], labels={'rx_count':'Prescription Count','avg_cost':'Avg Cost (£)'})
    st.plotly_chart(fig3, use_container_width=True)
    st.dataframe(anomaly, use_container_width=True)

with t4:
    st.subheader("Practice Benchmarking")
    st.caption("Cost efficiency across ICBs")
    bench = q("SELECT practice_name, icb_name, total_cost, avg_cost_per_item, total_items FROM summary_benchmark ORDER BY total_cost DESC LIMIT 20")
    fig4 = px.bar(bench, x='practice_name', y='total_cost', color='icb_name', labels={'total_cost':'Total cost (£)','practice_name':'Practice'})
    fig4.update_xaxes(tickangle=45)
    st.plotly_chart(fig4, use_container_width=True)
    st.dataframe(bench, use_container_width=True)

with t5:
    st.subheader("Trend and Drift Analysis")
    st.caption("Monthly spend by BNF chapter")
    trend = q("SELECT year_month, ch, monthly_cost FROM summary_trend ORDER BY year_month, ch")
    top6 = trend.groupby('ch')['monthly_cost'].sum().nlargest(6).index.tolist()
    fig5 = px.line(trend[trend['ch'].isin(top6)], x='year_month', y='monthly_cost', color='ch', title="Monthly spend — top 6 BNF chapters")
    st.plotly_chart(fig5, use_container_width=True)
    st.dataframe(trend, use_container_width=True)

st.divider()
st.caption("github.com/Keer0205/nhs-prescribing-intelligence · MSc Immunology & Microbiology · ICD-10/CPT/HCPCS · 7 yrs Data Engineering")
