"""
Page 1: Executive Overview Dashboard.
Enterprise KPI scorecard, category analytics, and temporal snapshot.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit_antd_components as sac

import config
from src.eda import (
    calculate_kpis, get_category_counts, get_trend_by_month,
    get_trend_by_hour,
)
from components import (
    inject_enterprise_styles, apply_plotly_theme, render_kpi_metric,
    render_section_header, render_page_header, render_aggrid_table, render_methodology_disclaimer,
    render_enterprise_sidebar,
)
from src.utils import convert_df_to_csv

st.set_page_config(page_title="Overview – Public Safety Analytics", page_icon="🛡️", layout="wide")
inject_enterprise_styles()
st.markdown('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">', unsafe_allow_html=True)

# ── Sidebar & Active Filtered Data ────────────────────────
df = render_enterprise_sidebar("Overview")

# ── Page Header ────────────────────────────────────────────
render_page_header("Executive Overview", "High-level synthesis of reported public safety incidents across active districts and time periods.", icon="📊")

# ── Methodology Banner ─────────────────────────────────────
render_methodology_disclaimer(
    "Critical Methodological Principle",
    "Reported Incidents ≠ Actual Crime Prevalence. This dashboard analyses historical aggregate open-data records. "
    "It does NOT predict individual behaviour or identify individuals.",
    banner_type="warning"
)

if st.session_state.get("dataset_source") == "Synthetic Benchmark":
    render_methodology_disclaimer(
        "Synthetic Demo Dataset Active",
        "4,500+ calibrated synthetic records are loaded for demonstration. Upload a real public CSV via the sidebar to analyse your own data.",
        banner_type="info"
    )

if df.empty:
    sac.result(label="No Data Available", description="Adjust filters or select a dataset in the sidebar.", status="empty")
    st.stop()

# ── KPI Row ────────────────────────────────────────────────
raw_audit = st.session_state.get("raw_audit") or {}
kpis = calculate_kpis(df, raw_audit)

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    render_kpi_metric("Total Reported Incidents", f"{kpis['total_incidents']:,}",
                      icon_name="file-earmark-bar-graph", subtext="Active filter subset")
with k2:
    render_kpi_metric("Crime Categories", f"{kpis['unique_categories']}",
                      icon_name="tags-fill", subtext="Distinct classifications")
with k3:
    render_kpi_metric("Districts Covered", f"{kpis['areas_covered']}",
                      icon_name="geo-alt-fill", subtext="Geographic zones")
with k4:
    render_kpi_metric("Dataset Completeness", f"{round(100 - kpis['missing_data_pct'], 1)}%",
                      icon_name="check-circle-fill",
                      delta=f"{kpis['missing_data_pct']}% missing" if kpis['missing_data_pct'] > 0 else None,
                      delta_type="neutral", subtext="Non-null cell rate")
with k5:
    clean_log = st.session_state.get("cleaning_log") or {}
    retention = clean_log.get("retention_rate_pct", 100)
    render_kpi_metric("Pipeline Retention", f"{retention}%",
                      icon_name="funnel-fill",
                      delta=f"{clean_log.get('duplicates_removed', 0)} duplicates removed",
                      delta_type="neutral", subtext="Post-cleaning yield")

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ── Category Breakdown ─────────────────────────────────────
render_section_header("Incident Category Analysis", "Top offense categories by reported volume", color_name="blue-70")

cat_df = get_category_counts(df, top_n=10)
c_left, c_right = st.columns([3, 2])

with c_left:
    if not cat_df.empty:
        fig_bar = px.bar(cat_df, x="count", y=config.COL_CATEGORY, orientation="h",
                         title="Top Reported Offense Categories",
                         labels={"count": "Incidents", config.COL_CATEGORY: ""}, text="count")
        fig_bar.update_layout(yaxis={"categoryorder": "total ascending"})
        fig_bar = apply_plotly_theme(fig_bar)
        st.plotly_chart(fig_bar, use_container_width=True)

with c_right:
    if not cat_df.empty:
        fig_donut = px.pie(cat_df, values="count", names=config.COL_CATEGORY,
                           title="Category Proportion", hole=0.5)
        fig_donut.update_traces(textposition="inside", textinfo="percent")
        fig_donut = apply_plotly_theme(fig_donut)
        st.plotly_chart(fig_donut, use_container_width=True)

# ── Temporal Snapshot ──────────────────────────────────────
render_section_header("Temporal Snapshot", "Diurnal and longitudinal incident patterns", color_name="blue-70")

t1, t2 = st.columns(2)

with t1:
    monthly = get_trend_by_month(df)
    if not monthly.empty:
        fig_m = px.line(monthly, x="year_month", y="count", title="Monthly Incident Volume",
                        markers=True, labels={"year_month": "Month", "count": "Incidents"})
        fig_m.update_traces(line_color="#3B82F6", line_width=3)
        fig_m = apply_plotly_theme(fig_m)
        st.plotly_chart(fig_m, use_container_width=True)

with t2:
    hourly = get_trend_by_hour(df)
    if not hourly.empty:
        fig_h = px.bar(hourly, x="hour_label", y="count", title="Diurnal 24-Hour Distribution",
                       labels={"hour_label": "Hour", "count": "Incidents"})
        fig_h = apply_plotly_theme(fig_h)
        st.plotly_chart(fig_h, use_container_width=True)

# ── Export ─────────────────────────────────────────────────
render_section_header("Data Export", "Download filtered incident records", color_name="gray-70")
st.download_button("Download Filtered CSV", convert_df_to_csv(df),
                   file_name="public_safety_filtered.csv", mime="text/csv")
