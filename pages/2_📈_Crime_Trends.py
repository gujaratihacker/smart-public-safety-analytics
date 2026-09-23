"""
Page 2: Spatiotemporal Crime Trends.
Multi-scale temporal analytics with sac.segmented sub-navigation and themed Plotly charts.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit_antd_components as sac

import config
from src.eda import (
    get_trend_by_year, get_trend_by_month, get_trend_by_day_of_week,
    get_trend_by_hour, get_seasonal_distribution, get_category_trend_over_time,
)
from components import (
    inject_enterprise_styles, apply_plotly_theme, render_section_header,
    render_page_header, render_aggrid_table, render_enterprise_sidebar,
)

st.set_page_config(page_title="Crime Trends – Public Safety Analytics", page_icon="🛡️", layout="wide")
inject_enterprise_styles()
st.markdown('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">', unsafe_allow_html=True)

# ── Sidebar & Active Filtered Data ────────────────────────
df = render_enterprise_sidebar("Spatiotemporal Trends")

# ── Page Header ────────────────────────────────────────────
render_page_header("Spatiotemporal Crime Trends", "Longitudinal, seasonal, and cyclical evaluation of aggregate incident patterns.", icon="📈")

if df.empty:
    sac.result(label="No Data Available", description="Adjust filters or load a dataset.", status="empty")
    st.stop()

# ── Sub-navigation ─────────────────────────────────────────
view_idx = sac.segmented(
    items=[
        sac.SegmentedItem(label="Annual Trajectories", icon="calendar3"),
        sac.SegmentedItem(label="Diurnal & Weekly Cycles", icon="clock-fill"),
        sac.SegmentedItem(label="Seasonal Patterns", icon="snow"),
        sac.SegmentedItem(label="Category Drilldown", icon="search"),
    ],
    align="center",
    size="sm",
    return_index=True,
)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ── View 0: Annual Trajectories ───────────────────────────
if view_idx == 0:
    render_section_header("Longitudinal Historical Progression", "Year-over-year incident volume with growth rates")
    m_c1, m_c2 = st.columns([1, 2])

    with m_c1:
        yearly_df = get_trend_by_year(df)
        if not yearly_df.empty:
            fig_yr = px.bar(yearly_df, x=config.COL_YEAR, y="count", title="Annual Incident Volume",
                            text="count")
            fig_yr = apply_plotly_theme(fig_yr)
            st.plotly_chart(fig_yr, use_container_width=True)
            render_aggrid_table(yearly_df.rename(columns={
                config.COL_YEAR: "Year", "count": "Incidents", "yoy_pct": "YoY Change %"
            }), height=220, key="yearly_tbl")

    with m_c2:
        monthly_df = get_trend_by_month(df)
        if not monthly_df.empty:
            fig_mo = px.line(monthly_df, x="year_month", y="count", title="Continuous Monthly Volume",
                             markers=True, labels={"year_month": "Month", "count": "Incidents"})
            fig_mo.update_traces(line_color="#3B82F6", line_width=3)
            monthly_df["rolling_3m"] = monthly_df["count"].rolling(window=3, min_periods=1).mean()
            fig_mo.add_scatter(x=monthly_df["year_month"], y=monthly_df["rolling_3m"],
                               name="3-Month Trend", line=dict(color="#EF4444", width=2, dash="dot"))
            fig_mo = apply_plotly_theme(fig_mo)
            st.plotly_chart(fig_mo, use_container_width=True)

# ── View 1: Diurnal & Weekly Cycles ───────────────────────
elif view_idx == 1:
    render_section_header("Diurnal & Weekly Cycles", "Incident concentrations across 24-hour and 7-day cycles")
    c1, c2 = st.columns(2)

    with c1:
        dow_df = get_trend_by_day_of_week(df)
        if not dow_df.empty:
            fig_dow = px.bar(dow_df, x="day_of_week", y="count", title="Day of Week Distribution")
            fig_dow = apply_plotly_theme(fig_dow)
            st.plotly_chart(fig_dow, use_container_width=True)

    with c2:
        hour_df = get_trend_by_hour(df)
        if not hour_df.empty:
            fig_hr = px.bar(hour_df, x="hour_label", y="count", title="Hourly 24-Hour Cycle")
            fig_hr = apply_plotly_theme(fig_hr)
            st.plotly_chart(fig_hr, use_container_width=True)

    # 2D Heatmap
    render_section_header("Diurnal Heatmap", "Day of Week × Hour of Day incident density")
    if config.COL_DAY_OF_WEEK in df.columns and config.COL_HOUR in df.columns:
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        ct = pd.crosstab(df[config.COL_DAY_OF_WEEK], df[config.COL_HOUR]).reindex(day_order).fillna(0)
        fig_heat = px.imshow(ct, labels=dict(x="Hour (0–23)", y="Day", color="Incidents"),
                             x=ct.columns, y=ct.index, color_continuous_scale="Plasma", aspect="auto")
        fig_heat = apply_plotly_theme(fig_heat)
        st.plotly_chart(fig_heat, use_container_width=True)

# ── View 2: Seasonal Patterns ─────────────────────────────
elif view_idx == 2:
    render_section_header("Calendar Seasonality", "Aggregate monthly and quarterly incident cycles")
    s1, s2 = st.columns(2)

    with s1:
        seasonal_df = get_seasonal_distribution(df)
        if not seasonal_df.empty:
            fig_seas = px.bar(seasonal_df, x="month_name", y="count", title="Monthly Aggregate Volume")
            fig_seas = apply_plotly_theme(fig_seas)
            st.plotly_chart(fig_seas, use_container_width=True)

    with s2:
        if config.COL_QUARTER in df.columns:
            q_df = df.groupby(config.COL_QUARTER).size().reset_index(name="count")
            q_df["quarter_label"] = q_df[config.COL_QUARTER].apply(lambda q: f"Q{q}")
            fig_q = px.pie(q_df, values="count", names="quarter_label", title="Quarterly Distribution", hole=0.45)
            fig_q.update_traces(textposition="inside", textinfo="percent")
            fig_q = apply_plotly_theme(fig_q)
            st.plotly_chart(fig_q, use_container_width=True)

# ── View 3: Category Drilldown ────────────────────────────
elif view_idx == 3:
    render_section_header("Category-Specific Trajectory", "Select a crime category to inspect its longitudinal pattern")
    all_cats = sorted(df[config.COL_CATEGORY].dropna().unique().tolist())
    sel_cat = st.selectbox("Crime Category", all_cats, index=0, label_visibility="collapsed")

    if sel_cat:
        cat_ts = get_category_trend_over_time(df, sel_cat, freq="ME")
        if not cat_ts.empty and len(cat_ts) > 1:
            fig_ct = px.line(cat_ts, x="date", y="count", title=f"Monthly Trajectory: {sel_cat}",
                             markers=True, labels={"date": "Date", "count": "Incidents"})
            fig_ct.update_traces(line_color="#6366F1", line_width=3)
            cat_ts["ma_3"] = cat_ts["count"].rolling(window=3, min_periods=1).mean()
            fig_ct.add_scatter(x=cat_ts["date"], y=cat_ts["ma_3"], name="3-Month Smoothed",
                               line=dict(color="#F59E0B", width=2, dash="dash"))
            fig_ct = apply_plotly_theme(fig_ct)
            st.plotly_chart(fig_ct, use_container_width=True)

            sub_df = df[df[config.COL_CATEGORY] == sel_cat]
            if config.COL_TIME_PERIOD in sub_df.columns:
                tp = sub_df[config.COL_TIME_PERIOD].value_counts().reset_index()
                tp.columns = ["Time Period", "Incidents"]
                fig_tp = px.bar(tp, x="Time Period", y="Incidents", title=f"Diurnal Breakdown: {sel_cat}")
                fig_tp = apply_plotly_theme(fig_tp)
                st.plotly_chart(fig_tp, use_container_width=True)
        else:
            sac.result(label="Insufficient Data", description=f"Not enough longitudinal points for '{sel_cat}'.", status="info")
