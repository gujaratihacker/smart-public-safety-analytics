"""
Page 4: Hotspot Detection.
DBSCAN spatial clustering, K-Means comparison, AgGrid cluster profiles, enterprise Folium map.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit_antd_components as sac
from streamlit_folium import folium_static

import config
from src.hotspot_detection import run_dbscan_clustering, run_kmeans_comparison, create_hotspot_map
from components import (
    inject_enterprise_styles, apply_plotly_theme, render_kpi_metric,
    render_section_header, render_page_header, render_methodology_disclaimer, render_aggrid_table,
    render_enterprise_sidebar,
)
from src.utils import convert_df_to_csv

st.set_page_config(page_title="Hotspot Detection – Public Safety Analytics", page_icon="🛡️", layout="wide")
inject_enterprise_styles()
st.markdown('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">', unsafe_allow_html=True)

# ── Sidebar & Active Filtered Data ────────────────────────
df = render_enterprise_sidebar("Hotspot Detection")

# ── Page Header ────────────────────────────────────────────
render_page_header("Geospatial Hotspot Detection", "Unsupervised density-based clustering for identifying historical incident concentrations.", icon="🔥")

render_methodology_disclaimer(
    "Critical Analytical Boundary",
    "Detected clusters reflect historical reported incident concentrations in available open data. "
    "They must NEVER be interpreted as predictive indicators of future crime or individual wrongdoing.",
    banner_type="warning"
)

if df.empty or config.COL_LAT not in df.columns or config.COL_LON not in df.columns:
    sac.result(label="No Geographic Data", description="Coordinates required for clustering.", status="warning")
    st.stop()

valid_df = df[df[config.COL_LAT].notnull() & df[config.COL_LON].notnull()].copy()
if len(valid_df) < 20:
    sac.result(label="Insufficient Data", description="Need >= 20 geocoded records for clustering.", status="warning")
    st.stop()

# ── Sub-navigation ─────────────────────────────────────────
view_idx = sac.segmented(
    items=[
        sac.SegmentedItem(label="DBSCAN Clustering", icon="bullseye"),
        sac.SegmentedItem(label="K-Means Comparison", icon="diagram-3-fill"),
    ],
    align="center", size="sm", return_index=True,
)

# ── View 0: DBSCAN ────────────────────────────────────────
if view_idx == 0:
    render_section_header("DBSCAN Density-Based Hotspot Detection",
                          "Haversine spherical distance, configurable neighbourhood radius and minimum density")

    p1, p2, p3 = st.columns(3)
    with p1:
        eps_km = st.slider("Epsilon (km)", 0.1, 2.0, 0.45, 0.05)
    with p2:
        min_samples = st.slider("Min Core Samples", 5, 50, 15)
    with p3:
        show_noise = st.checkbox("Show Noise Points", True)

    with st.spinner("Running DBSCAN spherical clustering..."):
        clustered_df, metrics, cluster_summary = run_dbscan_clustering(valid_df, eps_km=eps_km, min_samples=min_samples)

    # KPI row
    mk1, mk2, mk3, mk4 = st.columns(4)
    with mk1:
        render_kpi_metric("Detected Hotspots", f"{metrics['total_clusters']}",
                          icon_name="bullseye", subtext="Dense clusters")
    with mk2:
        render_kpi_metric("Clustered Volume", f"{metrics['total_clustered_points']:,}",
                          icon_name="diagram-3-fill",
                          delta=f"{metrics['clustered_pct']}%", delta_type="neutral")
    with mk3:
        render_kpi_metric("Noise Points", f"{metrics['noise_points']:,}",
                          icon_name="broadcast-pin",
                          delta=f"{metrics['noise_pct']}%", delta_type="neutral",
                          subtext="Unclustered / sparse")
    with mk4:
        render_kpi_metric("Search Radius", f"{eps_km} km",
                          icon_name="search", subtext=f"Min {min_samples} pts")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Map + Table
    map_col, tbl_col = st.columns([3, 2])

    with map_col:
        render_section_header("Historical Concentration Map", color_name="red-70")
        m_hot = create_hotspot_map(clustered_df, cluster_summary, show_noise=show_noise)
        folium_static(m_hot, width=750, height=520)

    with tbl_col:
        render_section_header("Hotspot Cluster Profiles", color_name="red-70")
        if not cluster_summary.empty:
            render_aggrid_table(
                cluster_summary[["Cluster Label", "Incidents", "% of Total", "Primary Area", "Dominant Crime"]],
                height=280, key="hs_tbl"
            )

            fig_cb = px.bar(cluster_summary, x="Incidents", y="Cluster Label", orientation="h",
                            title="Incidents per Hotspot", text="Incidents")
            fig_cb.update_layout(yaxis={"categoryorder": "total ascending"})
            fig_cb = apply_plotly_theme(fig_cb)
            fig_cb.update_traces(marker_color="#EF4444")
            st.plotly_chart(fig_cb, use_container_width=True)

            st.download_button("Export Hotspot CSV", convert_df_to_csv(cluster_summary),
                               file_name="hotspot_clusters.csv", mime="text/csv")
        else:
            sac.result(label="No Clusters", description="Adjust Epsilon or Min Samples.", status="info")

# ── View 1: K-Means Comparison ────────────────────────────
elif view_idx == 1:
    render_section_header("Methodological Comparison: DBSCAN vs K-Means",
                          "K-Means forces ALL points into clusters; DBSCAN isolates sparse noise")

    render_methodology_disclaimer(
        "Why DBSCAN is preferred for spatial incident analysis",
        "K-Means assumes spherical clusters of equal variance and has no noise concept — "
        "every outlier is forced into a cluster. DBSCAN discovers arbitrary-shape concentrations "
        "and naturally isolates sparse background points.",
        banner_type="info"
    )

    kc1, kc2 = st.columns([1, 2])
    with kc1:
        k_val = st.slider("Select k clusters", 2, 10, 5)
        km_df, km_metrics = run_kmeans_comparison(valid_df, n_clusters=k_val)
        render_kpi_metric("Inertia (SSE)", f"{km_metrics['inertia']:,.1f}", icon_name="speedometer")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        render_kpi_metric("Silhouette Score", f"{km_metrics['silhouette_score']:.3f}",
                          icon_name="bar-chart-fill", subtext="Scale: -1 to +1")

    with kc2:
        fig_km = px.scatter(km_df, x=config.COL_LON, y=config.COL_LAT,
                            color=km_df["kmeans_cluster"].astype(str),
                            title=f"K-Means Spatial Partitioning (k={k_val})",
                            labels={config.COL_LON: "Longitude", config.COL_LAT: "Latitude"})
        fig_km = apply_plotly_theme(fig_km)
        st.plotly_chart(fig_km, use_container_width=True)
