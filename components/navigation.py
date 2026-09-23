"""
Enterprise Sidebar Navigation & Control Component.
Provides unified brand header, option_menu navigation, dataset loading/uploading,
global filter pipeline orchestration, and system metadata.
"""

from typing import Optional
import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
import streamlit_antd_components as sac

import config
from src.data_loader import load_csv_data, load_sample_dataset
from src.data_cleaning import inspect_raw_data, clean_and_validate_data
from src.feature_engineering import engineer_features
from src.database import ingest_incidents
from src.eda import apply_filters

NAV_OPTIONS = [
    "Overview",
    "Spatiotemporal Trends",
    "Geospatial Analysis",
    "Hotspot Detection",
    "Aggregate Forecasting",
    "Data Explorer & Quality",
    "Statistical Analysis",
    "About & Methodology"
]

NAV_ICONS = [
    "grid-1x2-fill",
    "graph-up",
    "geo-alt-fill",
    "fire",
    "cpu-fill",
    "shield-check",
    "bar-chart-line-fill",
    "info-circle-fill"
]

PAGE_MAP = {
    "Overview": "pages/1_📊_Overview.py",
    "Spatiotemporal Trends": "pages/2_📈_Crime_Trends.py",
    "Geospatial Analysis": "pages/3_🗺️_Spatial_Analysis.py",
    "Hotspot Detection": "pages/4_🔥_Hotspots.py",
    "Aggregate Forecasting": "pages/5_🔮_Forecasting.py",
    "Data Explorer & Quality": "pages/6_🛡️_Data_Quality.py",
    "Statistical Analysis": "pages/7_⚖️_Statistics_&_Socioeconomic.py",
    "About & Methodology": "pages/8_📖_About_&_Methodology.py",
}

NAV_STYLES = {
    "container": {
        "padding": "0!important",
        "background-color": "#0F172A",
        "border": "none"
    },
    "icon": {
        "color": "#3B82F6",
        "font-size": "15px"
    },
    "nav-link": {
        "font-size": "13px",
        "font-weight": "500",
        "text-align": "left",
        "margin": "3px 0",
        "--hover-color": "#1E293B",
        "color": "#94A3B8",
        "font-family": "Inter, sans-serif",
        "border-radius": "6px",
        "padding": "8px 12px"
    },
    "nav-link-selected": {
        "background-color": "#1E293B",
        "color": "#F8FAFC",
        "font-weight": "600",
        "border-left": "3px solid #3B82F6"
    }
}


def _ensure_session_state():
    """Initializes global session state keys if not already present."""
    defaults = {
        "raw_df": None,
        "cleaned_df": None,
        "featured_df": None,
        "filtered_df": None,
        "raw_audit": None,
        "cleaning_log": None,
        "col_mapping": {},
        "pii_flags": [],
        "dataset_source": "Synthetic Benchmark",
        "quality_scores": {},
        "forecast_eval_results": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _run_pipeline(raw_df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """Executes inspection, cleaning, feature engineering, and DB ingestion."""
    audit = inspect_raw_data(raw_df)
    cleaned, clean_log = clean_and_validate_data(raw_df, mapping)
    featured = engineer_features(cleaned)
    st.session_state.update({
        "raw_df": raw_df,
        "raw_audit": audit,
        "cleaned_df": cleaned,
        "cleaning_log": clean_log,
        "featured_df": featured,
        "filtered_df": featured,
    })
    try:
        ingest_incidents(cleaned)
    except Exception:
        pass
    return featured


def render_sidebar_menu(default_index: int = 0) -> str:
    """Renders the standalone option_menu navigation widget."""
    with st.sidebar:
        selected = option_menu(
            menu_title=None,
            options=NAV_OPTIONS,
            icons=NAV_ICONS,
            menu_icon="cast",
            default_index=default_index,
            styles=NAV_STYLES
        )
    return selected


def render_enterprise_sidebar(current_page: str = "Overview") -> pd.DataFrame:
    """
    Renders the unified enterprise sidebar including:
    - Brand Header
    - Option Menu Navigation
    - Auto-Routing (st.switch_page)
    - Dataset Source Selector & CSV Uploader
    - Global Filters (Date, Category, District, Time Period)
    - System Metadata & Record Counts

    Returns the active filtered DataFrame.
    """
    _ensure_session_state()

    # Auto-load benchmark dataset on first boot
    if st.session_state["featured_df"] is None:
        try:
            raw_df, mapping, _, pii = load_sample_dataset()
            st.session_state["col_mapping"] = mapping
            st.session_state["pii_flags"] = pii
            st.session_state["dataset_source"] = "Synthetic Benchmark"
            _run_pipeline(raw_df, mapping)
        except Exception as e:
            st.sidebar.error(f"Failed to bootstrap demo data: {e}")

    with st.sidebar:
        # 1. Brand Header
        st.markdown(
            '<div style="padding:4px 0 12px 0;text-align:center;">'
            '<span style="font-size:20px;font-weight:700;color:#F8FAFC;letter-spacing:-0.02em;">'
            '🛡️ Public Safety Analytics</span><br/>'
            '<span style="font-size:11px;color:#94A3B8;letter-spacing:0.02em;">Spatiotemporal Incident Intelligence</span>'
            '</div>',
            unsafe_allow_html=True,
        )

        # 2. Navigation Menu
        page_idx = NAV_OPTIONS.index(current_page) if current_page in NAV_OPTIONS else 0
        selected = option_menu(
            menu_title=None,
            options=NAV_OPTIONS,
            icons=NAV_ICONS,
            menu_icon="cast",
            default_index=page_idx,
            styles=NAV_STYLES,
            key=f"nav_{current_page}"
        )

    # Route if user clicked another page
    if selected != current_page and selected in PAGE_MAP:
        st.switch_page(PAGE_MAP[selected])

    with st.sidebar:
        st.markdown("<hr style='margin:10px 0;border-color:rgba(255,255,255,0.08);'/>", unsafe_allow_html=True)

        # 3. Dataset Source & Upload
        with st.expander("📁 Dataset & Ingestion", expanded=False):
            source_idx = sac.segmented(
                items=[
                    sac.SegmentedItem(label="Demo", icon="database-fill"),
                    sac.SegmentedItem(label="Upload CSV", icon="upload"),
                ],
                align="center",
                size="xs",
                return_index=True,
                key="ds_seg_ctrl"
            )

            # Re-load synthetic benchmark if toggled to demo
            if source_idx == 0 and st.session_state.get("dataset_source") != "Synthetic Benchmark":
                try:
                    raw_df, mapping, _, pii = load_sample_dataset()
                    st.session_state["col_mapping"] = mapping
                    st.session_state["pii_flags"] = pii
                    st.session_state["dataset_source"] = "Synthetic Benchmark"
                    _run_pipeline(raw_df, mapping)
                    st.success("Loaded Synthetic Benchmark.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error loading demo: {e}")

            # CSV upload interface
            if source_idx == 1:
                uploaded_file = st.file_uploader(
                    "Upload Public Incident CSV",
                    type=["csv"],
                    label_visibility="collapsed",
                    key="sidebar_csv_uploader"
                )
                if uploaded_file is not None:
                    try:
                        raw_df, auto_mapping, missing, pii = load_csv_data(uploaded_file)
                        st.session_state["raw_df"] = raw_df
                        st.session_state["pii_flags"] = pii

                        if pii:
                            st.warning(f"PII detected: {', '.join(pii)}")

                        st.markdown("<div style='font-size:12px;font-weight:600;margin-top:6px;'>Column Mapping:</div>", unsafe_allow_html=True)
                        user_mapping = {}
                        col_options = ["-- Not Mapped --"] + list(raw_df.columns)
                        for canon_col, label in [
                            (config.COL_DATE, "Incident Date *"),
                            (config.COL_TIME, "Incident Time"),
                            (config.COL_CATEGORY, "Crime Category *"),
                            (config.COL_AREA, "Area"),
                            (config.COL_LAT, "Latitude *"),
                            (config.COL_LON, "Longitude *"),
                            (config.COL_LOCATION_TYPE, "Location Type"),
                            (config.COL_DISTRICT, "District"),
                        ]:
                            default = auto_mapping.get(canon_col, "-- Not Mapped --")
                            idx = col_options.index(default) if default in col_options else 0
                            choice = st.selectbox(label, col_options, index=idx, key=f"map_{canon_col}")
                            if choice != "-- Not Mapped --":
                                user_mapping[canon_col] = choice

                        if st.button("Run Pipeline", type="primary", use_container_width=True):
                            with st.spinner("Processing..."):
                                st.session_state["col_mapping"] = user_mapping
                                st.session_state["dataset_source"] = uploaded_file.name
                                _run_pipeline(raw_df, user_mapping)
                                st.success(f"{len(st.session_state['featured_df']):,} records ready.")
                                st.rerun()
                    except Exception as err:
                        st.error(f"CSV error: {err}")

            st.caption(f"Active: **{st.session_state.get('dataset_source', 'Demo')}**")

        # 4. Global Filters
        featured_df = st.session_state.get("featured_df")
        if featured_df is not None and not featured_df.empty:
            with st.expander("🔍 Global Filters", expanded=False):
                min_d = featured_df[config.COL_DATE].min()
                max_d = featured_df[config.COL_DATE].max()
                date_val = st.date_input("Date Range", value=(min_d, max_d), min_value=min_d, max_value=max_d, key="filter_date")
                selected_date_range = date_val if isinstance(date_val, (list, tuple)) and len(date_val) == 2 else (min_d, max_d)

                all_categories = sorted(featured_df[config.COL_CATEGORY].dropna().unique().tolist())
                selected_categories = st.multiselect("Crime Category", all_categories, key="filter_cat")

                all_areas = sorted(featured_df[config.COL_AREA].dropna().unique().tolist()) if config.COL_AREA in featured_df.columns else []
                selected_areas = st.multiselect("Area / District", all_areas, key="filter_area")

                selected_periods = st.multiselect("Time Period", ["Night", "Morning", "Afternoon", "Evening"], key="filter_period")
                selected_dows = st.multiselect("Day of Week", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], key="filter_dow")

                if st.button("Reset Filters", use_container_width=True):
                    st.session_state["filtered_df"] = featured_df
                    st.rerun()

            # Apply filters
            filtered_df = apply_filters(
                featured_df,
                date_range=selected_date_range,
                categories=selected_categories or None,
                areas=selected_areas or None,
                time_periods=selected_periods or None,
                days_of_week=selected_dows or None,
            )
            st.session_state["filtered_df"] = filtered_df
        else:
            filtered_df = pd.DataFrame()
            st.session_state["filtered_df"] = filtered_df

        # 5. System Status Footer
        tot_count = len(featured_df) if featured_df is not None else 0
        filt_count = len(filtered_df)
        st.markdown(
            f'<div style="padding-top:10px;font-size:11px;color:#64748B;line-height:1.4;">'
            f'<span>v{config.VERSION} · SQLite Engine</span><br/>'
            f'<span>Records: <strong style="color:#94A3B8;">{filt_count:,}</strong> / {tot_count:,}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    return filtered_df
