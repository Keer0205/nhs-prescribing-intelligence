import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text

st.set_page_config(page_title="NHS Prescribing Intelligence", layout="wide")

st.markdown("""
<style>
.main-title { font-size: 2.2rem; font-weight: 700; color: #1F4E79; margin-bottom: 4px; }
.sub-title { font-size: 1rem; color: #444; margin-bottom: 0px; }
.insight-box { background: #EAF3FB; border-left: 4px solid #2E75B6; padding: 12px 16px; border-radius: 6px; margin-bottom: 16px; font-size: 0.9rem; color: #1F4E79; }
.footer-clean { text-align: center; color: #888; font-size: 0.8rem; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #eee; }
</style>
""", unsafe_allow_html=True)

db = st.secrets["connections"]["postgresql"]
engine = create_engine(
    f"postgresql+psycopg2://{db['username']}:{db['password']}@{db['host']}:{db['port']}/{db['database']}"
)

def q(sql):
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn)

# ── HEADER ──
st.markdown('<p class="main-title">NHS Prescribing Intelligence Engine</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Explore NHS prescribing patterns across England using cost, volume, variation, AMR indicators and anomaly detection — built on 54,691,186 real prescriptions (Nov 2025–Jan 2026).</p>', unsafe_allow_html=True)
st.caption("Built by Keerthana Murugesan · MSc Immunology & Microbiology · ICD-10/CPT/HCPCS · 7 yrs Data Engineering")
st.divider()

# ── KPI ROW 1 — SCALE ──
k1, k2, k3 = st.columns(3)
k1.metric("Total Prescriptions", "54.7M", "Nov 2025–Jan 2026")
k2.metric("Total Spend", "£8.2B+", "3 months NHS England")
k3.metric("Practices Analysed", "10,000+", "All ICBs")

# ── KPI ROW 2 — INSIGHT ──
try:
    top_anomaly = q("SELECT practice_name, avg_cost FROM summary_anomaly ORDER BY avg_cost DESC LIMIT 1")
    top_amr = q("SELECT practice_name, antibiotic_rate_pct FROM summary_amr ORDER BY antibiotic_rate_pct DESC LIMIT 1")
    top_bench = q("SELECT icb_name, SUM(total_cost) as spend FROM summary_benchmark GROUP BY icb_name ORDER BY spend DESC LIMIT 1")

    st.markdown("**Key insights from the data:**")
    i1, i2, i3 = st.columns(3)
    if not top_anomaly.empty:
        i1.metric("Highest avg cost practice", f"£{top_anomaly.iloc[0]['avg_cost']:,.0f}", top_anomaly.iloc[0]['practice_name'][:30])
    if not top_amr.empty:
        i2.metric("Top AMR outlier rate", f"{top_amr.iloc[0]['antibiotic_rate_pct']}%", top_amr.iloc[0]['practice_name'][:30])
    if not top_bench.empty:
        i3.metric("Highest spend ICB", f"£{top_bench.iloc[0]['spend']/1e6:.1f}M", top_bench.iloc[0]['icb_name'][:35])
except:
    pass

st.divider()

# ── ICB FILTER ──
icb_list = q("SELECT DISTINCT icb_name FROM summary_benchmark WHERE icb_name IS NOT NULL ORDER BY icb_name")
icb_options = ["All ICBs"] + icb_list["icb_name"].tolist()
selected_icb = st.selectbox("Filter by ICB", icb_options)
icb_filter = "" if selected_icb == "All ICBs" else f"WHERE icb_name = '{selected_icb}'"

# ── TABS ──
t1, t2, t3, t4, t5 = st.tabs(["Brand vs Generic", "AMR Monitor", "Anomaly Detection", "Benchmarking", "Trend & Drift"])

with t1:
    st.subheader("Brand vs Generic Savings Opportunity")
    st.caption("Practices where branded prescribing significantly exceeds generic equivalents — built using 5 years ICD-10/CPT/HCPCS coding expertise")
    df = q(f"SELECT national_rank, practice_name, icb_name, branded_cost, generic_cost, brand_rate_pct, spend_decile FROM summary_brand_vs_generic {icb_filter} ORDER BY national_rank LIMIT 20")
    if not df.empty:
        fig = px.bar(df, x='practice_name', y=['branded_cost', 'generic_cost'],
            barmode='group',
            color_discrete_map={'branded_cost': '#D85A30', 'generic_cost': '#1D9E75'},
            labels={'value': 'Cost (£)', 'practice_name': 'Practice'},
            height=420)
        fig.update_xaxes(tickangle=45)
        fig.update_layout(legend_title="", margin=dict(b=120))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("**Top 20 practices by national rank**")
        st.dataframe(df[['national_rank','practice_name','icb_name','branded_cost','generic_cost','brand_rate_pct']].rename(columns={
            'national_rank':'Rank','practice_name':'Practice','icb_name':'ICB',
            'branded_cost':'Branded Cost (£)','generic_cost':'Generic Cost (£)','brand_rate_pct':'Brand Rate %'
        }), use_container_width=True, hide_index=True)

with t2:
    st.subheader("AMR Monitor — MSc Microbiology Applied")
    st.markdown('<div class="insight-box">This view compares broad-spectrum antibiotic prescribing rates across practices to highlight variation relevant to NHS antimicrobial stewardship programmes. The resistance tier classification was built from MSc Immunology & Microbiology expertise — not a standard BNF lookup.</div>', unsafe_allow_html=True)

    amr = q(f"SELECT practice_name, icb_name, antibiotic_rate_pct, total_cost FROM summary_amr {icb_filter} ORDER BY antibiotic_rate_pct DESC LIMIT 15")
    if not amr.empty:
        nat_avg = amr['antibiotic_rate_pct'].mean()
        amr['status'] = amr['antibiotic_rate_pct'].apply(
            lambda x: 'High outlier' if x > nat_avg * 1.5 else ('Above average' if x > nat_avg else 'Within range')
        )
        color_map = {'High outlier': '#D85A30', 'Above average': '#EF9F27', 'Within range': '#1D9E75'}
        fig2 = px.bar(amr, x='practice_name', y='antibiotic_rate_pct',
            color='status', color_discrete_map=color_map,
            labels={'antibiotic_rate_pct': 'Antibiotic Rate (%)', 'practice_name': 'Practice', 'status': 'Status'},
            height=450)
        fig2.add_hline(y=nat_avg, line_dash="dash", line_color="#2E75B6",
            annotation_text=f"Average: {nat_avg:.1f}%", annotation_position="top right")
        fig2.update_xaxes(tickangle=45)
        fig2.update_layout(margin=dict(b=140))
        st.plotly_chart(fig2, use_container_width=True)
        st.dataframe(amr[['practice_name','icb_name','antibiotic_rate_pct','status']].rename(columns={
            'practice_name':'Practice','icb_name':'ICB','antibiotic_rate_pct':'Antibiotic Rate %','status':'Status'
        }), use_container_width=True, hide_index=True)

with t3:
    st.subheader("Anomaly Detection")
    st.caption("Cost outliers identified using audit-style rejection logic from biomedical equipment claims experience")

    anomaly = q(f"SELECT practice_name, icb_name, bnf_chapter_plus_code, total_cost, avg_cost, rx_count FROM summary_anomaly {icb_filter} ORDER BY avg_cost DESC LIMIT 50")
    if not anomaly.empty:
        top1 = anomaly.iloc[0]
        col_ins1, col_ins2, col_ins3 = st.columns(3)
        col_ins1.metric("Top cost outlier", top1['practice_name'][:25], f"£{top1['avg_cost']:,.0f} avg cost")
        col_ins2.metric("Top BNF chapter", anomaly['bnf_chapter_plus_code'].value_counts().index[0][:25], "most flagged")
        col_ins3.metric("Outliers identified", f"{len(anomaly)}", "high-cost practices")

        avg_cost_median = anomaly['avg_cost'].median()
        anomaly['is_outlier'] = anomaly['avg_cost'] > avg_cost_median * 1.5
        anomaly['color'] = anomaly['is_outlier'].map({True: '#D85A30', False: '#B4B2A9'})
        anomaly['label'] = anomaly.apply(lambda r: r['practice_name'][:20] if r['is_outlier'] else '', axis=1)

        fig3 = go.Figure()
        for outlier, group in anomaly.groupby('is_outlier'):
            fig3.add_trace(go.Scatter(
                x=group['rx_count'], y=group['avg_cost'],
                mode='markers+text',
                marker=dict(size=10, color='#D85A30' if outlier else '#B4B2A9', opacity=0.8),
                text=group['label'],
                textposition='top center',
                textfont=dict(size=9),
                name='Outlier' if outlier else 'Normal',
                hovertemplate='<b>%{customdata[0]}</b><br>Avg cost: £%{y:,.0f}<br>Rx count: %{x:,}<extra></extra>',
                customdata=group[['practice_name']].values
            ))
        fig3.update_layout(
            height=500,
            xaxis_title="Prescription Count",
            yaxis_title="Avg Cost (£)",
            legend_title="",
            margin=dict(t=20, b=40)
        )
        st.plotly_chart(fig3, use_container_width=True)

        st.markdown("**Flagged high-cost practices — top 10**")
        st.dataframe(anomaly[anomaly['is_outlier']][['practice_name','icb_name','bnf_chapter_plus_code','avg_cost','rx_count']].head(10).rename(columns={
            'practice_name':'Practice','icb_name':'ICB','bnf_chapter_plus_code':'BNF Chapter',
            'avg_cost':'Avg Cost (£)','rx_count':'Rx Count'
        }), use_container_width=True, hide_index=True)

with t4:
    st.subheader("Practice Benchmarking")
    st.caption("Cost efficiency across ICBs — NTILE decile banding")
    bench = q(f"SELECT practice_name, icb_name, total_cost, avg_cost_per_item, total_items FROM summary_benchmark {icb_filter} ORDER BY total_cost DESC LIMIT 20")
    if not bench.empty:
        fig4 = px.bar(bench, x='practice_name', y='total_cost', color='icb_name',
            labels={'total_cost': 'Total cost (£)', 'practice_name': 'Practice'},
            height=420)
        fig4.update_xaxes(tickangle=45)
        fig4.update_layout(legend_title="ICB", margin=dict(b=140))
        st.plotly_chart(fig4, use_container_width=True)
        st.dataframe(bench.rename(columns={
            'practice_name':'Practice','icb_name':'ICB','total_cost':'Total Cost (£)',
            'avg_cost_per_item':'Avg Cost/Item (£)','total_items':'Total Items'
        }), use_container_width=True, hide_index=True)

with t5:
    st.subheader("Trend and Drift Analysis")
    st.caption("Monthly spend by BNF chapter — SUM() OVER (ROWS BETWEEN), LAG(), rolling averages")
    trend = q("SELECT year_month, ch, monthly_cost FROM summary_trend ORDER BY year_month, ch")
    if not trend.empty:
        top6 = trend.groupby('ch')['monthly_cost'].sum().nlargest(6).index.tolist()
        trend_filtered = trend[trend['ch'].isin(top6)]
        fig5 = px.line(trend_filtered, x='year_month', y='monthly_cost', color='ch',
            title="Monthly spend — top 6 BNF chapters",
            labels={'monthly_cost': 'Monthly Cost (£)', 'year_month': 'Month', 'ch': 'BNF Chapter'},
            markers=True, height=420)
        fig5.update_layout(legend_title="BNF Chapter")
        st.plotly_chart(fig5, use_container_width=True)
        st.dataframe(trend.rename(columns={'year_month':'Month','ch':'BNF Chapter','monthly_cost':'Monthly Cost (£)'}),
            use_container_width=True, hide_index=True)

# ── FOOTER ──
st.markdown("""
<div class="footer-clean">
    Built by <strong>Keerthana Murugesan</strong> · Healthcare Analytics | Python | SQL | PostgreSQL | dbt | Streamlit | Power BI<br>
    <a href="https://github.com/Keer0205/nhs-prescribing-intelligence" target="_blank">GitHub Repository</a> · MSc Immunology & Microbiology · ICD-10/CPT/HCPCS · 7 yrs Data Engineering
</div>
""", unsafe_allow_html=True)
