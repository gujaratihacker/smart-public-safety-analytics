"""
Page 7: Statistical Analysis & Socioeconomic Context.
Chi-square, ANOVA, correlation, and contextual overlays with enterprise presentation.
Uses statistics module: perform_chi_square_test, perform_anova_district_test,
compute_descriptive_stats, get_socioeconomic_indicators.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit_antd_components as sac

import config
from src.statistics import (
    perform_chi_square_test, perform_anova_district_test,
    compute_descriptive_stats, get_socioeconomic_indicators,
)
from components import (
    inject_enterprise_styles, apply_plotly_theme, render_kpi_metric,
    render_section_header, render_page_header, render_methodology_disclaimer, render_aggrid_table,
    render_enterprise_sidebar,
)

st.set_page_config(page_title="Statistics – Public Safety Analytics", page_icon="🛡️", layout="wide")
inject_enterprise_styles()
st.markdown('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">', unsafe_allow_html=True)

# ── Sidebar & Active Filtered Data ────────────────────────
df = render_enterprise_sidebar("Statistical Analysis")

# ── Page Header ────────────────────────────────────────────
render_page_header("Statistical Analysis", "Inferential statistics, correlation analysis, and hypothesis testing on aggregate incident data.", icon="⚖️")

render_methodology_disclaimer(
    "Statistical Interpretation Notice",
    "All statistical tests operate on aggregate reported incident data. Correlation does NOT imply causation. "
    "Results should be interpreted within the limitations of the source dataset.",
    banner_type="warning"
)

if df.empty:
    sac.result(label="No Data Available", description="Load a dataset or adjust filters.", status="empty")
    st.stop()

# ── Sub-navigation ─────────────────────────────────────────
view_idx = sac.segmented(
    items=[
        sac.SegmentedItem(label="Descriptive Statistics", icon="bar-chart-line-fill"),
        sac.SegmentedItem(label="Hypothesis Testing", icon="clipboard2-data-fill"),
        sac.SegmentedItem(label="Socioeconomic Context", icon="buildings"),
    ],
    align="center", size="sm", return_index=True,
)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ── View 0: Descriptive Statistics ────────────────────────
if view_idx == 0:
    render_section_header("Descriptive Summary Statistics", "Central tendency, dispersion, and distributional characteristics")

    desc_stats = compute_descriptive_stats(df)

    if desc_stats is not None and not desc_stats.empty:
        ds1, ds2 = st.columns([2, 3])
        with ds1:
            render_aggrid_table(desc_stats, height=350, key="desc_stats_tbl")
        with ds2:
            if config.COL_DATE in df.columns:
                daily = df.groupby(config.COL_DATE).size().reset_index(name="Daily Incidents")
                fig_dist = px.histogram(daily, x="Daily Incidents", nbins=30,
                                        title="Distribution of Daily Incident Counts",
                                        marginal="box")
                fig_dist = apply_plotly_theme(fig_dist)
                fig_dist.update_traces(marker_color="#6366F1")
                st.plotly_chart(fig_dist, use_container_width=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Category frequency table
    render_section_header("Category Frequency Analysis", color_name="amber-70")
    cat_freq = df[config.COL_CATEGORY].value_counts().reset_index()
    cat_freq.columns = ["Crime Category", "Frequency"]
    cat_freq["Relative %"] = (cat_freq["Frequency"] / cat_freq["Frequency"].sum() * 100).round(2)
    cat_freq["Cumulative %"] = cat_freq["Relative %"].cumsum().round(2)

    cf1, cf2 = st.columns([3, 2])
    with cf1:
        render_aggrid_table(cat_freq, height=300, key="cat_freq_tbl")
    with cf2:
        fig_pareto = go.Figure()
        fig_pareto.add_trace(go.Bar(x=cat_freq["Crime Category"], y=cat_freq["Frequency"],
                                     name="Frequency", marker_color="#3B82F6"))
        fig_pareto.add_trace(go.Scatter(x=cat_freq["Crime Category"], y=cat_freq["Cumulative %"],
                                         name="Cumulative %", yaxis="y2",
                                         line=dict(color="#EF4444", width=2.5), mode="lines+markers"))
        fig_pareto.update_layout(
            title="Pareto Analysis", yaxis_title="Frequency",
            yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 110]),
        )
        fig_pareto = apply_plotly_theme(fig_pareto)
        st.plotly_chart(fig_pareto, use_container_width=True)

    # Correlation matrix of numeric features
    render_section_header("Numeric Feature Correlation", color_name="blue-70")
    numeric_df = df.select_dtypes(include=[np.number])
    exclude_cols = [config.COL_LAT, config.COL_LON]
    corr_cols = [c for c in numeric_df.columns if c not in exclude_cols]

    if len(corr_cols) >= 2:
        corr_matrix = numeric_df[corr_cols].corr()
        fig_corr = px.imshow(
            corr_matrix,
            labels=dict(color="Pearson r"),
            color_continuous_scale="RdBu_r",
            zmin=-1, zmax=1,
            aspect="auto",
            title="Feature Correlation Heatmap"
        )
        fig_corr = apply_plotly_theme(fig_corr)
        st.plotly_chart(fig_corr, use_container_width=True)

        corr_pairs = []
        cols = corr_matrix.columns.tolist()
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                corr_pairs.append({
                    "Feature A": cols[i],
                    "Feature B": cols[j],
                    "Pearson r": round(corr_matrix.iloc[i, j], 4),
                    "|r|": round(abs(corr_matrix.iloc[i, j]), 4),
                })
        pairs_df = pd.DataFrame(corr_pairs).sort_values("|r|", ascending=False).head(10)
        render_aggrid_table(pairs_df, height=250, key="corr_pairs_tbl")

# ── View 1: Hypothesis Testing ────────────────────────────
elif view_idx == 1:
    render_section_header("Chi-Square Test of Independence",
                          "Test whether crime category and time period are statistically independent")

    if config.COL_TIME_PERIOD in df.columns and config.COL_CATEGORY in df.columns:
        chi_result = perform_chi_square_test(df, config.COL_CATEGORY, config.COL_TIME_PERIOD)

        if chi_result.get("status") == "success":
            hk1, hk2, hk3, hk4 = st.columns(4)
            with hk1:
                render_kpi_metric("Chi² Statistic", f"{chi_result['chi2_stat']:.2f}", icon_name="calculator")
            with hk2:
                render_kpi_metric("p-Value", chi_result['p_value_formatted'], icon_name="bullseye")
            with hk3:
                render_kpi_metric("Degrees of Freedom", f"{chi_result['dof']}", icon_name="sliders")
            with hk4:
                sig = "Significant ✓" if chi_result['is_significant'] else "Not Significant"
                render_kpi_metric("Result (α=0.05)", sig, icon_name="patch-check-fill",
                                  subtext="H₀: Variables are independent")

            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

            ct = chi_result["contingency_table"]
            fig_ct = px.imshow(ct, labels=dict(x="Time Period", y="Category", color="Count"),
                               color_continuous_scale="YlOrRd", aspect="auto",
                               title="Contingency Table: Category × Time Period")
            fig_ct = apply_plotly_theme(fig_ct)
            st.plotly_chart(fig_ct, use_container_width=True)

            render_methodology_disclaimer("Interpretation", chi_result['interpretation'], banner_type="info")
        else:
            sac.result(label="Test Failed", description=chi_result.get("message", ""), status="warning")
    else:
        sac.result(label="Required Columns Missing", description="Need 'time_period' feature.", status="warning")

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    render_section_header("One-Way ANOVA: District Comparison",
                          "Test whether mean daily incident rates differ significantly across geographic areas")

    if config.COL_AREA in df.columns and config.COL_DATE in df.columns:
        anova_result = perform_anova_district_test(df)

        if anova_result.get("status") == "success":
            ak1, ak2, ak3 = st.columns(3)
            with ak1:
                render_kpi_metric("F-Statistic", f"{anova_result['f_stat']:.2f}", icon_name="calculator")
            with ak2:
                render_kpi_metric("p-Value", anova_result['p_value_formatted'], icon_name="bullseye")
            with ak3:
                sig = "Significant ✓" if anova_result['is_significant'] else "Not Significant"
                render_kpi_metric("Result (α=0.05)", sig, icon_name="patch-check-fill")

            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

            means = anova_result.get("area_means", {})
            stds = anova_result.get("area_stds", {})
            if means:
                means_df = pd.DataFrame([
                    {"District": k, "Mean Daily Incidents": v, "Std Dev": stds.get(k, 0)}
                    for k, v in means.items()
                ]).sort_values("Mean Daily Incidents", ascending=False)

                fig_means = px.bar(means_df, x="District", y="Mean Daily Incidents",
                                   error_y="Std Dev", title="Mean Daily Incident Rate by District")
                fig_means = apply_plotly_theme(fig_means)
                st.plotly_chart(fig_means, use_container_width=True)

            render_methodology_disclaimer("Interpretation", anova_result['interpretation'], banner_type="info")
        else:
            sac.result(label="Test Failed", description=anova_result.get("message", ""), status="warning")
    else:
        sac.result(label="Required Columns Missing", description="Need 'area' and 'date' columns.", status="warning")

# ── View 2: Socioeconomic Context ─────────────────────────
elif view_idx == 2:
    render_section_header("Socioeconomic Contextual Overlay",
                          "Area-level incident rates alongside census benchmark indicators")

    render_methodology_disclaimer(
        "CRITICAL: Ecological Fallacy Warning",
        "Area-level statistical associations DO NOT establish individual-level causation. "
        "Reported crime numbers are influenced by commercial activity, foot traffic density, "
        "police patrol allocation, and differing reporting rates — not the socioeconomic status of residents.",
        banner_type="warning"
    )

    socio_df, socio_meta = get_socioeconomic_indicators(df)

    if not socio_df.empty:
        render_aggrid_table(socio_df, height=280, key="socio_tbl")

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        sc1, sc2 = st.columns(2)
        with sc1:
            render_kpi_metric("Correlation: Incident Rate ↔ Unemployment",
                              f"{socio_meta.get('corr_unemployment', 0):.3f}",
                              icon_name="graph-down-arrow",
                              subtext="Pearson r (area-level)")
        with sc2:
            render_kpi_metric("Correlation: Incident Rate ↔ Median Income",
                              f"{socio_meta.get('corr_income', 0):.3f}",
                              icon_name="currency-dollar",
                              subtext="Pearson r (area-level)")

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        s1, s2 = st.columns(2)
        with s1:
            fig_s1 = px.scatter(socio_df, x="Unemployment Rate (%)", y="Incident Rate per 1k",
                                text="Area", title="Incident Rate vs Unemployment Rate",
                                trendline="ols")
            fig_s1 = apply_plotly_theme(fig_s1)
            fig_s1.update_traces(textposition="top center", marker_size=12)
            st.plotly_chart(fig_s1, use_container_width=True)

        with s2:
            fig_s2 = px.scatter(socio_df, x="Median Income ($)", y="Incident Rate per 1k",
                                text="Area", title="Incident Rate vs Median Income",
                                trendline="ols")
            fig_s2 = apply_plotly_theme(fig_s2)
            fig_s2.update_traces(textposition="top center", marker_size=12)
            st.plotly_chart(fig_s2, use_container_width=True)

        render_methodology_disclaimer(
            "Mandatory Caveat",
            socio_meta.get("methodological_caveat", ""),
            banner_type="warning"
        )
    else:
        sac.result(label="No Area Data Available", description="Socioeconomic overlay requires area-level data.", status="info")
