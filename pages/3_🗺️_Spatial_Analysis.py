"""
Page 3: Geospatial Incident Analysis.
Interactive Folium maps (dark basemap), density heatmaps, spatiotemporal slices, and district comparison.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit_antd_components as sac
from streamlit_folium import folium_static

import config
from src.spatial_analysis import create_incident_map, create_heatmap, get_area_summary, get_spatial_summary
from components import (
    inject_enterprise_styles, apply_plotly_theme, render_kpi_metric,
    render_section_header, render_page_header, render_methodology_disclaimer, render_aggrid_table,
    render_enterprise_sidebar,
)

st.set_page_config(page_title="Geospatial – Public Safety Analytics", page_icon="🛡️", layout="wide")
inject_enterprise_styles()
st.markdown('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">', unsafe_allow_html=True)

# ── Sidebar & Active Filtered Data ────────────────────────
df = render_enterprise_sidebar("Geospatial Analysis")

# ── Page Header ────────────────────────────────────
render_page_header("Geospatial Incident Analysis", "Interactive mapping, density heatmaps, and spatiotemporal geographic slicing.", icon="🗺️")

render_methodology_disclaimer(
    "Privacy & Methodological Disclaimer",
    "Coordinates represent reported public event locations. Individual addresses and personal identities are excluded. "
    "Spatial density indicates reporting concentration, not individual propensity.",
    banner_type="warning"
)

if df.empty or config.COL_LAT not in df.columns or config.COL_LON not in df.columns:
    sac.result(label="No Geographic Data", description="Latitude / Longitude not found or dataset is empty.", status="warning")
    st.stop()

valid_geo = df[df[config.COL_LAT].notnull() & df[config.COL_LON].notnull()]
if valid_geo.empty:
    sac.result(label="No Valid Coordinates", description="All geographic records are invalid or filtered out.", status="warning")
    st.stop()

# ── KPI row ────────────────────────────────────────────────
spatial = get_spatial_summary(valid_geo)
sk1, sk2, sk3, sk4 = st.columns(4)
with sk1:
    render_kpi_metric("Geocoded Records", f"{spatial['valid_points']:,}", icon_name="pin-map-fill")
with sk2:
    render_kpi_metric("Center Latitude", f"{spatial['center_lat']:.4f}°", icon_name="compass")
with sk3:
    render_kpi_metric("Center Longitude", f"{spatial['center_lon']:.4f}°", icon_name="compass-fill")
with sk4:
    n_areas = valid_geo[config.COL_AREA].nunique() if config.COL_AREA in valid_geo.columns else 0
    render_kpi_metric("Active Districts", f"{n_areas}", icon_name="buildings")

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# ── Sub-navigation ─────────────────────────────────────────
view_idx = sac.segmented(
    items=[
        sac.SegmentedItem(label="Cluster Map", icon="pin-map-fill"),
        sac.SegmentedItem(label="Density HeatMap", icon="fire"),
        sac.SegmentedItem(label="Spatiotemporal Slice", icon="clock-history"),
        sac.SegmentedItem(label="District Comparison", icon="buildings"),
    ],
    align="center", size="sm", return_index=True,
)

# ── View 0: Cluster Map ───────────────────────────────────
if view_idx == 0:
    render_section_header("Interactive Marker Clustering", "Incidents clustered to optimise render performance")
    fl1, fl2 = st.columns([1, 3])
    with fl1:
        cat_filter = st.selectbox("Category", ["All"] + sorted(valid_geo[config.COL_CATEGORY].dropna().unique().tolist()), key="map_cat")
        max_pts = st.slider("Max Markers", 200, 3000, 1200, 100)
        use_clust = st.checkbox("Cluster Grouping", True)
    subset = valid_geo if cat_filter == "All" else valid_geo[valid_geo[config.COL_CATEGORY] == cat_filter]
    with fl2:
        if not subset.empty:
            with st.spinner("Rendering map..."):
                folium_static(create_incident_map(subset, max_points=max_pts, use_clustering=use_clust), width=850, height=520)
        else:
            sac.result(label="No Records", description="No records match filter.", status="info")

# ── View 1: Heatmap ───────────────────────────────────────
elif view_idx == 1:
    render_section_header("Kernel Density HeatMap", "Continuous density surface of historical incident concentrations")
    hf1, hf2 = st.columns([1, 3])
    with hf1:
        h_radius = st.slider("Heat Radius", 10, 35, 18)
        h_blur = st.slider("Blur", 12, 40, 22)
        h_cat = st.selectbox("Category", ["All"] + sorted(valid_geo[config.COL_CATEGORY].dropna().unique().tolist()), key="heat_cat")
    h_sub = valid_geo if h_cat == "All" else valid_geo[valid_geo[config.COL_CATEGORY] == h_cat]
    with hf2:
        if not h_sub.empty:
            with st.spinner("Calculating density..."):
                folium_static(create_heatmap(h_sub, radius=h_radius, blur=h_blur), width=850, height=520)

# ── View 2: Spatiotemporal Slice ──────────────────────────
elif view_idx == 2:
    render_section_header("Spatiotemporal Slice", "Inspect how concentration shifts across periods and months")
    sf1, sf2 = st.columns([1, 3])
    with sf1:
        period_opts = ["All Periods", "Night", "Morning", "Afternoon", "Evening"]
        sl_period = st.selectbox("Time Period", period_opts)
        month_opts = ["All Months"] + ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        sl_month = st.selectbox("Month", month_opts)
    sl_df = valid_geo.copy()
    if sl_period != "All Periods":
        sl_df = sl_df[sl_df[config.COL_TIME_PERIOD] == sl_period]
    if sl_month != "All Months":
        sl_df = sl_df[sl_df[config.COL_MONTH_NAME].str.startswith(sl_month)]
    with sf2:
        st.caption(f"Showing {len(sl_df):,} incidents for {sl_period} / {sl_month}")
        if not sl_df.empty:
            folium_static(create_incident_map(sl_df, max_points=1000, use_clustering=True), width=850, height=500)
        else:
            sac.result(label="No Records", description="No records match slice.", status="info")

# ── View 3: District Comparison ───────────────────────────
elif view_idx == 3:
    render_section_header("District-Level Volume Comparison", "Reported incidents aggregated by geographic zone")
    area_df = get_area_summary(valid_geo)
    dc1, dc2 = st.columns([3, 2])
    with dc1:
        if not area_df.empty:
            fig_a = px.bar(area_df, x="total_incidents", y=config.COL_AREA, orientation="h",
                           title="Incidents by District", text="total_incidents")
            fig_a.update_layout(yaxis={"categoryorder": "total ascending"})
            fig_a = apply_plotly_theme(fig_a)
            st.plotly_chart(fig_a, use_container_width=True)
    with dc2:
        render_aggrid_table(area_df.rename(columns={
            config.COL_AREA: "District", "total_incidents": "Total",
            "percentage": "% of Dataset", "primary_crime": "Dominant Crime"
        }), height=320, key="dist_tbl")
