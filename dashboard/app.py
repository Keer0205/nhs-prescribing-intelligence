import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text

st.set_page_config(page_title="NHS Prescribing Intelligence", layout="wide")

st.markdown("""
<style>
.main-title { font-size: 2.8rem; font-weight: 800; color: #1F4E79; margin-bottom: 8px; line-height: 1.2; }
.sub-title { font-size: 1.15rem; color: #333; margin-bottom: 6px; line-height: 1.6; }
.byline { font-size: 0.95rem; color: #555; margin-bottom: 0; }
.insight-box { background: #EAF3FB; border-left: 4px solid #2E75B6; padding: 12px 16px; border-radius: 6px; margin-bottom: 16px; font-size: 0.92rem; color: #1F4E79; }
.footer-line1 { text-align: center; color: #555; font-size: 0.85rem; margin-bottom: 4px; }
.footer-line2 { text-align: center; color: #888; font-size: 0.82rem; }
.footer-wrap { margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #eee; }
div[data-baseweb="select"] > div { border-color: #ccc !important; box-shadow: none !important; }
div[data-baseweb="select"] > div:focus-within { border-color: #2E75B6 !important; }
</style>
""", unsafe_allow_html=True)

db = st.secrets["connections"]["postgresql"]
engine = create_engine(
    f"postgresql+psycopg2://{db['username']}:{db['password']}@{db['host']}:{db['port']}/{db['database']}"
)

def q(sql):
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn)

st.markdown('<p class="main-title">NHS Prescribing Intelligence Engine</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Explore NHS prescribing patterns across England using cost, volume, variation, AMR indicators and anomaly detection — built on 54,691,186 real prescriptions (Nov 2025–Jan 2026).</p>', unsafe_allow_html=True)
st.markdown('<p class="byline">Built by <strong>Keerthana Murugesan</strong> · MSc Immunology & Microbiology · ICD-10/CPT/HCPCS · 7 yrs Data Engineering</p>', unsafe_allow_html=True)
st.divider()

k1, k2, k3 = st.columns(3)
k1.metric("Total Prescriptions", "54.7M", "Nov 2025–Jan 2026")
k2.metric("Total Spend", "£8.2B+", "3 months NHS England")
k3.metric("Practices Analysed", "10,000+", "All ICBs")

try:
    top_anomaly = q("SELECT practice_name, avg_cost FROM summary_anomaly ORDER BY avg_cost DESC LIMIT 1")
    top_amr = q("SELECT practice_name, antibiotic_rate_pct FROM summary_amr ORDER BY antibiotic_rate_pct DESC LIMIT 1")
    top_bench = q("SELECT icb_name, SUM(total_cost) as spend FROM summary_benchmark GROUP BY icb_name ORDER BY spend DESC LIMIT 1")
    st.markdown("**Key insights from the data:**")
    i1, i2, i3 = st.columns(3)
    if not top_anomaly.empty:
        i1.metric("Highest avg cost practice", f"£{top_anomaly.iloc[0]['avg_cost']:,.0f}", top_anomaly.iloc[0]['practice_name'][:30])
    if not top_amr.empty:
        i2.metric("Highest antibiotic outlier rate", f"{top_amr.iloc[0]['antibiotic_rate_pct']}%", top_amr.iloc[0]['practice_name'][:30])
    if not top_bench.empty:
        i3.metric("Highest spend ICB", f"£{top_bench.iloc[0]['spend']/1e6:.1f}M", top_bench.iloc[0]['icb_name'][:35])
except:
    pass

st.divider()

icb_list = q("SELECT DISTINCT icb_name FROM summary_benchmark WHERE icb_name IS NOT NULL ORDER BY icb_name")
icb_options = ["All ICBs"] + icb_list["icb_name"].tolist()
selected_icb = st.selectbox("Filter by ICB", icb_options)
icb_filter = "" if selected_icb == "All ICBs" else f"WHERE icb_name = '{selected_icb}'"

t1, t2, t3, t4, t5 = st.tabs(["Brand vs Generic", "AMR Monitor", "Anomaly Detection", "Benchmarking", "Trend & Drift"])

with t1:
    st.subheader("Brand vs Generic Savings Opportunity")
    st.caption("Highlights practices where branded prescribing materially exceeds generic alternatives, indicating possible cost-saving opportunities.")

    df = q(f"SELECT national_rank, practice_name, icb_name, branded_cost, generic_cost, brand_rate_pct, spend_decile FROM summary_brand_vs_generic {icb_filter} ORDER BY national_rank LIMIT 10")

    if not df.empty:
        df["savings_gap"] = df["branded_cost"] - df["generic_cost"]
        df = df.sort_values("savings_gap", ascending=False).reset_index(drop=True)
        df["display_rank"] = range(1, len(df) + 1)
        df["short_name"] = df["practice_name"].str[:32]

        s1, s2, s3 = st.columns(3)
        top = df.iloc[0]
        s1.metric("Top savings opportunity", top["practice_name"][:28], f"£{top['savings_gap']:,.0f} gap")
        s2.metric("Avg brand prescribing share", f"{df['brand_rate_pct'].mean():.1f}%", "across top 10 practices")
        s3.metric("Total branded spend", f"£{df['branded_cost'].sum()/1e6:.1f}M", "top 10 practices")

        fig = go.Figure(go.Bar(
            x=df["savings_gap"],
            y=df["short_name"],
            orientation="h",
            marker_color="#D85A30",
            text=[f"£{v/1e6:.2f}M" for v in df["savings_gap"]],
            textposition="outside",
            hovertemplate="<b>%{customdata}</b><br>Savings gap: £%{x:,.0f}<extra></extra>",
            customdata=df["practice_name"]
        ))
        fig.update_layout(
            height=420,
            xaxis_title="Potential savings gap (£)",
            yaxis_title="",
            yaxis=dict(autorange="reversed"),
            margin=dict(l=20, r=110, t=20, b=40),
            plot_bgcolor="white",
            xaxis=dict(gridcolor="#f0f0f0")
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("**Top flagged practices by potential savings gap**")
        display_df = df[["display_rank","practice_name","icb_name","branded_cost","generic_cost","savings_gap","brand_rate_pct"]].copy()
        display_df["branded_cost"] = display_df["branded_cost"].apply(lambda x: f"£{x:,.0f}")
        display_df["generic_cost"] = display_df["generic_cost"].apply(lambda x: f"£{x:,.0f}")
        display_df["savings_gap"] = display_df["savings_gap"].apply(lambda x: f"£{x:,.0f}")
        display_df["brand_rate_pct"] = display_df["brand_rate_pct"].apply(lambda x: f"{x:.1f}%")
        display_df.columns = ["Rank","Practice","ICB","Branded Cost","Generic Cost","Savings Gap","Brand Rate %"]
        st.caption("Brand Rate % = proportion of prescribing that is branded vs generic alternatives. Higher values indicate greater savings opportunity.")
        st.dataframe(display_df, use_container_width=True, hide_index=True)

with t2:
    st.subheader("AMR Monitor — MSc Microbiology Applied")
    st.markdown('<div class="insight-box">This view compares broad-spectrum antibiotic prescribing rates across practices to highlight variation relevant to NHS antimicrobial stewardship programmes. The resistance tier classification was built from MSc Immunology & Microbiology expertise — not a standard BNF lookup.</div>', unsafe_allow_html=True)
    amr = q(f"SELECT practice_name, icb_name, antibiotic_rate_pct, total_cost FROM summary_amr {icb_filter} ORDER BY antibiotic_rate_pct DESC LIMIT 15")
    if not amr.empty:
        nat_avg = amr['antibiotic_rate_pct'].mean()
        amr['status'] = amr['antibiotic_rate_pct'].apply(
            lambda x: 'High outlier' if x > nat_avg * 1.5 else ('Above average' if x > nat_avg else 'Within range'))
        color_map = {'High outlier': '#D85A30', 'Above average': '#EF9F27', 'Within range': '#1D9E75'}
        amr['short_name'] = amr['practice_name'].str[:35]
        fig2 = px.bar(amr, x='antibiotic_rate_pct', y='short_name',
            orientation='h', color='status', color_discrete_map=color_map,
            labels={'antibiotic_rate_pct': 'Antibiotic Rate (%)', 'short_name': ''},
            height=480)
        fig2.add_vline(x=nat_avg, line_dash="dash", line_color="#2E75B6",
            annotation_text=f"Group avg: {nat_avg:.1f}%", annotation_position="top right")
        fig2.update_layout(yaxis=dict(autorange="reversed"),
            margin=dict(l=20, r=120, t=20, b=40), legend_title="")
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
        col_ins2.metric("Most flagged BNF chapter", anomaly['bnf_chapter_plus_code'].value_counts().index[0][:25], "by frequency")
        avg_cost_median = anomaly['avg_cost'].median()
        outlier_count = len(anomaly[anomaly['avg_cost'] > avg_cost_median * 1.5])
        col_ins3.metric("Outliers identified", f"{outlier_count}", "high-cost practices")
        anomaly['is_outlier'] = anomaly['avg_cost'] > avg_cost_median * 1.5
        top_outliers = anomaly[anomaly['is_outlier']].head(5)['practice_name'].tolist()
        anomaly['label'] = anomaly.apply(
            lambda r: r['practice_name'][:22] if r['practice_name'] in top_outliers else '', axis=1)
        fig3 = go.Figure()
        normal = anomaly[~anomaly['is_outlier']]
        outliers = anomaly[anomaly['is_outlier']]
        fig3.add_trace(go.Scatter(
            x=normal['rx_count'], y=normal['avg_cost'], mode='markers',
            marker=dict(size=8, color='#B4B2A9', opacity=0.6), name='Normal',
            hovertemplate='<b>%{customdata[0]}</b><br>Avg cost: £%{y:,.0f}<br>Rx count: %{x:,}<extra></extra>',
            customdata=normal[['practice_name']].values))
        fig3.add_trace(go.Scatter(
            x=outliers['rx_count'], y=outliers['avg_cost'], mode='markers+text',
            marker=dict(size=12, color='#D85A30', opacity=0.9),
            text=outliers['label'], textposition='top center',
            textfont=dict(size=10, color='#1F4E79'), name='Outlier',
            hovertemplate='<b>%{customdata[0]}</b><br>Avg cost: £%{y:,.0f}<br>Rx count: %{x:,}<extra></extra>',
            customdata=outliers[['practice_name']].values))
        fig3.update_layout(height=520, xaxis_title="Prescription Count",
            yaxis_title="Avg Cost per Item (£)", legend_title="",
            margin=dict(t=30, b=50, l=60, r=30))
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown("**Flagged high-cost practices — top 10**")
        st.dataframe(anomaly[anomaly['is_outlier']][['practice_name','icb_name','bnf_chapter_plus_code','avg_cost','rx_count']].head(10).rename(columns={
            'practice_name':'Practice','icb_name':'ICB','bnf_chapter_plus_code':'BNF Chapter',
            'avg_cost':'Avg Cost (£)','rx_count':'Rx Count'
        }), use_container_width=True, hide_index=True)

with t4:
    st.subheader("Practice Benchmarking")
    st.caption("Cost efficiency across ICBs — ordered by total prescribing spend")
    bench = q(f"SELECT practice_name, icb_name, total_cost, avg_cost_per_item, total_items FROM summary_benchmark {icb_filter} ORDER BY total_cost DESC LIMIT 20")
    if not bench.empty:
        bench['short_name'] = bench['practice_name'].str[:35]
        fig4 = px.bar(bench, x='total_cost', y='short_name',
            orientation='h', color='icb_name',
            labels={'total_cost': 'Total cost (£)', 'short_name': ''},
            height=520)
        fig4.update_layout(yaxis=dict(autorange="reversed"),
            legend_title="ICB", margin=dict(l=20, r=20, t=20, b=40))
        st.plotly_chart(fig4, use_container_width=True)
        st.dataframe(bench[['practice_name','icb_name','total_cost','avg_cost_per_item','total_items']].rename(columns={
            'practice_name':'Practice','icb_name':'ICB','total_cost':'Total Cost (£)',
            'avg_cost_per_item':'Avg Cost/Item (£)','total_items':'Total Items'
        }), use_container_width=True, hide_index=True)

with t5:
    st.subheader("Trend and Drift Analysis")
    st.caption("Monthly spend by BNF chapter — rolling averages and month-on-month drift")
    trend = q("SELECT year_month, ch, monthly_cost FROM summary_trend ORDER BY year_month, ch")
    if not trend.empty:
        top6 = trend.groupby('ch')['monthly_cost'].sum().nlargest(6).index.tolist()
        fig5 = px.line(trend[trend['ch'].isin(top6)], x='year_month', y='monthly_cost', color='ch',
            title="Monthly spend — top 6 BNF chapters",
            labels={'monthly_cost': 'Monthly Cost (£)', 'year_month': 'Month', 'ch': 'BNF Chapter'},
            markers=True, height=450)
        fig5.update_layout(legend_title="BNF Chapter", margin=dict(t=40, b=40))
        st.plotly_chart(fig5, use_container_width=True)
        st.dataframe(trend.rename(columns={
            'year_month':'Month','ch':'BNF Chapter','monthly_cost':'Monthly Cost (£)'
        }), use_container_width=True, hide_index=True)

st.markdown("""
<div class="footer-wrap">
  <p class="footer-line1">Built by <strong>Keerthana Murugesan</strong> &nbsp;|&nbsp; Healthcare Analytics &nbsp;|&nbsp; Python &nbsp;|&nbsp; SQL &nbsp;|&nbsp; PostgreSQL &nbsp;|&nbsp; dbt &nbsp;|&nbsp; Streamlit &nbsp;|&nbsp; Power BI</p>
  <p class="footer-line2"><a href="https://github.com/Keer0205/nhs-prescribing-intelligence" target="_blank">GitHub Repository</a> &nbsp;|&nbsp; MSc Immunology & Microbiology &nbsp;|&nbsp; ICD-10/CPT/HCPCS &nbsp;|&nbsp; 7 yrs Data Engineering</p>
</div>
""", unsafe_allow_html=True)
