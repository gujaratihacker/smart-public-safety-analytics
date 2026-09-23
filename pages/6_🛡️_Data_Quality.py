"""
Page 6: Data Explorer & Quality Audit.
Schema inspection, completeness profiling, cleaning audit trail, and interactive AgGrid explorer.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit_antd_components as sac

import config
from components import (
    inject_enterprise_styles, apply_plotly_theme, render_kpi_metric,
    render_section_header, render_page_header, render_methodology_disclaimer, render_aggrid_table,
    render_enterprise_sidebar,
)
from src.utils import convert_df_to_csv

st.set_page_config(page_title="Data Quality – Public Safety Analytics", page_icon="🛡️", layout="wide")
inject_enterprise_styles()
st.markdown('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">', unsafe_allow_html=True)

# ── Sidebar & Active Filtered Data ────────────────────────
df = render_enterprise_sidebar("Data Explorer & Quality")

raw_df = st.session_state.get("raw_df") if st.session_state.get("raw_df") is not None else pd.DataFrame()
raw_audit = st.session_state.get("raw_audit") or {}
clean_log = st.session_state.get("cleaning_log") or {}

# ── Page Header ────────────────────────────────────────────
render_page_header("Data Explorer & Quality Audit", "Schema inspection, completeness profiling, and full-pipeline cleaning audit trail.", icon="🛡️")

# ── Sub-navigation ─────────────────────────────────────────
view_idx = sac.segmented(
    items=[
        sac.SegmentedItem(label="Schema & Profiling", icon="table"),
        sac.SegmentedItem(label="Cleaning Audit Trail", icon="funnel-fill"),
        sac.SegmentedItem(label="Interactive Explorer", icon="search"),
    ],
    align="center", size="sm", return_index=True,
)

# ── View 0: Schema & Profiling ────────────────────────────
if view_idx == 0:
    render_section_header("Dataset Schema & Quality Profile", "Per-column data type, null rate, and cardinality")

    # KPI row
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        render_kpi_metric("Raw Records", f"{raw_audit.get('total_rows', len(raw_df)):,}", icon_name="database")
    with q2:
        render_kpi_metric("Columns", f"{raw_audit.get('total_columns', len(raw_df.columns))}", icon_name="layout-text-sidebar")
    with q3:
        render_kpi_metric("Total Missing Cells", f"{raw_audit.get('total_missing', 0):,}", icon_name="exclamation-triangle")
    with q4:
        completeness = 100.0 - raw_audit.get("overall_missing_pct", 0)
        render_kpi_metric("Overall Completeness", f"{completeness:.1f}%", icon_name="check-circle-fill")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Column profiling table
    if not raw_df.empty:
        profile_data = []
        for col in raw_df.columns:
            null_ct = int(raw_df[col].isnull().sum())
            null_pct = round(null_ct / len(raw_df) * 100, 1) if len(raw_df) > 0 else 0
            profile_data.append({
                "Column": col,
                "Data Type": str(raw_df[col].dtype),
                "Non-Null": f"{len(raw_df) - null_ct:,}",
                "Null": f"{null_ct:,}",
                "Null %": null_pct,
                "Unique Values": raw_df[col].nunique(),
            })
        profile_df = pd.DataFrame(profile_data)
        render_aggrid_table(profile_df, height=350, key="profile_tbl")

        # Null rate bar chart
        null_rows = profile_df[profile_df["Null %"] > 0].sort_values("Null %", ascending=True)
        if not null_rows.empty:
            fig_null = px.bar(null_rows, x="Null %", y="Column", orientation="h", title="Column Null Rates (%)")
            fig_null = apply_plotly_theme(fig_null)
            fig_null.update_traces(marker_color="#EF4444")
            st.plotly_chart(fig_null, use_container_width=True)

# ── View 1: Cleaning Audit Trail ──────────────────────────
elif view_idx == 1:
    render_section_header("Data Pipeline Cleaning Audit", "Deduplication, validation, and retention metrics")

    if clean_log:
        cl1, cl2, cl3, cl4, cl5 = st.columns(5)
        with cl1:
            render_kpi_metric("Input Rows", f"{clean_log.get('initial_rows', 0):,}", icon_name="inbox-fill")
        with cl2:
            render_kpi_metric("Output Rows", f"{clean_log.get('final_rows', 0):,}", icon_name="check2-all")
        with cl3:
            render_kpi_metric("Duplicates Removed", f"{clean_log.get('duplicates_removed', 0):,}", icon_name="trash")
        with cl4:
            render_kpi_metric("Invalid Dropped", f"{clean_log.get('invalid_coords_removed', 0) + clean_log.get('invalid_dates_removed', 0):,}", icon_name="x-circle")
        with cl5:
            render_kpi_metric("Retention Rate", f"{clean_log.get('retention_rate_pct', 100)}%",
                              icon_name="funnel-fill")

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # Cleaning pipeline steps
        render_section_header("Pipeline Step Execution Log", color_name="green-70")
        steps = clean_log.get("steps", [])
        if steps:
            steps_df = pd.DataFrame(steps)
            render_aggrid_table(steps_df, height=250, key="steps_tbl")

        # Imputed columns
        imputed = clean_log.get("imputed_cols", {})
        if imputed:
            render_section_header("Categorical Transformations", color_name="blue-70")
            imp_df = pd.DataFrame([{"Field": k, "Transformation Strategy": v} for k, v in imputed.items()])
            render_aggrid_table(imp_df, height=180, key="imp_tbl")
    else:
        sac.result(label="No Cleaning Audit", description="Load or upload dataset to generate audit.", status="info")

# ── View 2: Interactive Explorer ──────────────────────────
elif view_idx == 2:
    render_section_header("Full Dataset Interactive Explorer", "Sort, filter, and search across all features")

    if not df.empty:
        st.caption(f"Displaying {len(df):,} records × {len(df.columns)} columns (active filtered subset)")

        render_aggrid_table(df, height=500, key="explorer_tbl", enable_pagination=True, page_size=50)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.download_button("Download Active Subset CSV", convert_df_to_csv(df),
                           file_name="public_safety_data_export.csv", mime="text/csv")
    else:
        sac.result(label="No Data Available", description="Adjust filters or select a dataset.", status="empty")
