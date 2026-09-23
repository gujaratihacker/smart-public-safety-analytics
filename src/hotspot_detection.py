"""
Hotspot Detection module.
Implements unsupervised spatial clustering using DBSCAN with haversine metric,
compares results with K-Means, and generates interactive cluster maps and summaries.
"""

from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from sklearn.metrics import silhouette_score
import folium

import config

EARTH_RADIUS_KM = 6371.0088

# Palette for clusters (distinct bright colors)
CLUSTER_PALETTE = [
    "#EF4444", "#3B82F6", "#10B981", "#F59E0B", "#8B5CF6",
    "#EC4899", "#06B6D4", "#F97316", "#84CC16", "#6366F1",
    "#14B8A6", "#E11D48", "#A855F7", "#D97706", "#059669"
]
NOISE_COLOR = "#64748B"  # Muted Slate for noise points


def run_dbscan_clustering(
    df: pd.DataFrame,
    eps_km: float = 0.5,
    min_samples: int = 15
) -> Tuple[pd.DataFrame, Dict[str, Any], pd.DataFrame]:
    """
    Executes DBSCAN clustering using geographic coordinates in radians and haversine metric.

    Parameters:
        df: Incident DataFrame containing latitude and longitude
        eps_km: Neighborhood radius in kilometers
        min_samples: Minimum incidents required to form a dense core

    Returns:
        clustered_df: DataFrame with added 'cluster_id' column (-1 for noise)
        metrics: Dictionary of summary statistics
        cluster_summary_df: Table of detected clusters, counts, centroids, and percentages
    """
    valid_mask = df[config.COL_LAT].notnull() & df[config.COL_LON].notnull()
    clustered_df = df[valid_mask].copy()

    if len(clustered_df) < min_samples:
        clustered_df["cluster_id"] = -1
        return clustered_df, {"total_clusters": 0, "noise_points": len(clustered_df), "noise_pct": 100.0}, pd.DataFrame()

    # Convert coordinates from degrees to radians for haversine distance
    coords_rad = np.radians(clustered_df[[config.COL_LAT, config.COL_LON]].values)
    eps_rad = eps_km / EARTH_RADIUS_KM

    db = DBSCAN(eps=eps_rad, min_samples=min_samples, metric="haversine", algorithm="ball_tree")
    labels = db.fit_predict(coords_rad)
    clustered_df["cluster_id"] = labels

    total_points = len(clustered_df)
    noise_count = int(np.sum(labels == -1))
    noise_pct = round((noise_count / total_points) * 100, 2) if total_points > 0 else 0.0

    unique_clusters = [lbl for lbl in np.unique(labels) if lbl != -1]
    num_clusters = len(unique_clusters)

    # Build cluster summary table
    summary_rows = []
    for c_id in unique_clusters:
        cluster_points = clustered_df[clustered_df["cluster_id"] == c_id]
        c_count = len(cluster_points)
        c_pct = round((c_count / total_points) * 100, 2)
        c_lat = round(float(cluster_points[config.COL_LAT].mean()), 6)
        c_lon = round(float(cluster_points[config.COL_LON].mean()), 6)
        top_cat = cluster_points[config.COL_CATEGORY].mode().iloc[0] if config.COL_CATEGORY in cluster_points.columns else "N/A"
        top_area = cluster_points[config.COL_AREA].mode().iloc[0] if config.COL_AREA in cluster_points.columns else "N/A"

        summary_rows.append({
            "Cluster Label": f"Hotspot {c_id + 1}",
            "Cluster ID": c_id,
            "Incidents": c_count,
            "% of Total": c_pct,
            "Centroid Latitude": c_lat,
            "Centroid Longitude": c_lon,
            "Primary Area": top_area,
            "Dominant Crime": top_cat
        })

    cluster_summary_df = pd.DataFrame(summary_rows)
    if not cluster_summary_df.empty:
        cluster_summary_df = cluster_summary_df.sort_values(by="Incidents", ascending=False).reset_index(drop=True)

    metrics = {
        "total_clusters": num_clusters,
        "noise_points": noise_count,
        "noise_pct": noise_pct,
        "total_clustered_points": total_points - noise_count,
        "clustered_pct": round(100.0 - noise_pct, 2),
        "eps_km": eps_km,
        "min_samples": min_samples
    }

    return clustered_df, metrics, cluster_summary_df


def run_kmeans_comparison(
    df: pd.DataFrame,
    n_clusters: int = 5
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Executes K-Means on coordinates for methodological comparison.
    Computes Inertia and Silhouette Score.
    """
    valid_mask = df[config.COL_LAT].notnull() & df[config.COL_LON].notnull()
    km_df = df[valid_mask].copy()

    if len(km_df) <= n_clusters:
        return km_df, {"inertia": 0.0, "silhouette_score": 0.0}

    coords = km_df[[config.COL_LAT, config.COL_LON]].values
    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = km.fit_predict(coords)
    km_df["kmeans_cluster"] = labels

    inertia = round(float(km.inertia_), 4)
    # Compute silhouette score on a sample if dataset is large to maintain fast UI responsiveness
    sample_size = min(len(coords), 1500)
    sil_score = round(float(silhouette_score(coords, labels, sample_size=sample_size, random_state=42)), 4)

    metrics = {
        "n_clusters": n_clusters,
        "inertia": inertia,
        "silhouette_score": sil_score,
        "centers": km.cluster_centers_.tolist()
    }

    return km_df, metrics


def create_hotspot_map(
    clustered_df: pd.DataFrame,
    cluster_summary_df: pd.DataFrame,
    show_noise: bool = True,
    max_noise_points: int = 400
) -> folium.Map:
    """
    Renders an interactive Folium map illustrating detected historical incident concentrations.
    """
    center_lat = float(clustered_df[config.COL_LAT].median())
    center_lon = float(clustered_df[config.COL_LON].median())

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13,
        tiles="CartoDB positron"
    )

    # 1. Render Noise Points if enabled
    if show_noise:
        noise_df = clustered_df[clustered_df["cluster_id"] == -1]
        if len(noise_df) > max_noise_points:
            noise_df = noise_df.sample(n=max_noise_points, random_state=42)

        for _, row in noise_df.iterrows():
            folium.CircleMarker(
                location=[row[config.COL_LAT], row[config.COL_LON]],
                radius=3,
                color=NOISE_COLOR,
                fill=True,
                fill_color=NOISE_COLOR,
                fill_opacity=0.3,
                weight=0,
                popup=folium.Popup("<i>Unclustered / Sparse Background Point</i>", max_width=200)
            ).add_to(m)

    # 2. Render Clustered Points
    non_noise = clustered_df[clustered_df["cluster_id"] != -1]
    for _, row in non_noise.iterrows():
        c_id = int(row["cluster_id"])
        color = CLUSTER_PALETTE[c_id % len(CLUSTER_PALETTE)]
        folium.CircleMarker(
            location=[row[config.COL_LAT], row[config.COL_LON]],
            radius=5,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=1,
            popup=folium.Popup(f"<b>Hotspot {c_id + 1}</b><br/>Crime: {row.get(config.COL_CATEGORY, 'N/A')}", max_width=200)
        ).add_to(m)

    # 3. Add Centroid Markers with summary badges
    if not cluster_summary_df.empty:
        for _, c_row in cluster_summary_df.iterrows():
            c_id = int(c_row["Cluster ID"])
            color = CLUSTER_PALETTE[c_id % len(CLUSTER_PALETTE)]
            popup_content = f"""
            <div style="font-family: sans-serif; font-size: 13px; width: 220px;">
                <b style="color: {color}; font-size: 14px;">{c_row['Cluster Label']}</b><br/>
                <b>Total Incidents:</b> {c_row['Incidents']} ({c_row['% of Total']}%)<br/>
                <b>Dominant Area:</b> {c_row['Primary Area']}<br/>
                <b>Top Crime:</b> {c_row['Dominant Crime']}<br/>
                <hr style="margin: 4px 0; border: 0; border-top: 1px solid #ccc;"/>
                <small style="color: #666;">Historical Concentration Centroid</small>
            </div>
            """
            folium.Marker(
                location=[c_row["Centroid Latitude"], c_row["Centroid Longitude"]],
                popup=folium.Popup(popup_content, max_width=250),
                icon=folium.Icon(color="red", icon="crosshairs", prefix="fa")
            ).add_to(m)

    return m
