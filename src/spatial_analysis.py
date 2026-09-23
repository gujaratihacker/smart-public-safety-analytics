"""
Geospatial Analysis module.
Generates interactive Folium maps, MarkerClusters, density HeatMaps,
and spatiotemporal slices for geographic exploration.
"""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
import folium
from folium.plugins import MarkerCluster, HeatMap

import config

CATEGORY_COLORS = {
    "Theft / Larceny": "#2563EB",       # Blue
    "Burglary": "#D97706",              # Amber
    "Assault": "#DC2626",               # Red
    "Motor Vehicle Theft": "#7C3AED",    # Purple
    "Vandalism": "#059669",             # Emerald
    "Public Disorder": "#DB2777",       # Pink
    "Robbery": "#B91C1C",               # Dark Red
    "Fraud": "#4B5563",                 # Slate Gray
    "Narcotics": "#0891B2"              # Cyan
}
DEFAULT_MARKER_COLOR = "#3B82F6"


def get_spatial_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes geographic centroid and bounding coordinates.
    """
    if df.empty or config.COL_LAT not in df.columns or config.COL_LON not in df.columns:
        return {
            "center_lat": 37.7749,
            "center_lon": -122.4194,
            "lat_min": None, "lat_max": None,
            "lon_min": None, "lon_max": None,
            "valid_points": 0
        }

    valid_coords = df[[config.COL_LAT, config.COL_LON]].dropna()
    if valid_coords.empty:
        return {
            "center_lat": 37.7749,
            "center_lon": -122.4194,
            "lat_min": None, "lat_max": None,
            "lon_min": None, "lon_max": None,
            "valid_points": 0
        }

    center_lat = float(valid_coords[config.COL_LAT].median())
    center_lon = float(valid_coords[config.COL_LON].median())

    return {
        "center_lat": center_lat,
        "center_lon": center_lon,
        "lat_min": float(valid_coords[config.COL_LAT].min()),
        "lat_max": float(valid_coords[config.COL_LAT].max()),
        "lon_min": float(valid_coords[config.COL_LON].min()),
        "lon_max": float(valid_coords[config.COL_LON].max()),
        "valid_points": len(valid_coords)
    }


def create_incident_map(
    df: pd.DataFrame, 
    max_points: int = 1500, 
    use_clustering: bool = True
) -> folium.Map:
    """
    Creates an interactive Folium map with clustered or direct incident markers.
    """
    summary = get_spatial_summary(df)
    m = folium.Map(
        location=[summary["center_lat"], summary["center_lon"]],
        zoom_start=13,
        tiles="CartoDB positron"
    )

    plot_df = df[[config.COL_LAT, config.COL_LON, config.COL_CATEGORY, 
                  config.COL_DATE, config.COL_TIME_PERIOD, config.COL_LOCATION_TYPE]].dropna()

    if len(plot_df) > max_points:
        plot_df = plot_df.sample(n=max_points, random_state=42)

    cluster_container = MarkerCluster().add_to(m) if use_clustering else m

    for _, row in plot_df.iterrows():
        cat = str(row.get(config.COL_CATEGORY, "Unknown"))
        color = CATEGORY_COLORS.get(cat, DEFAULT_MARKER_COLOR)
        
        popup_html = f"""
        <div style="font-family: sans-serif; font-size: 12px; width: 180px;">
            <b style="color: {color}; font-size: 13px;">{cat}</b><br/>
            <b>Date:</b> {row.get(config.COL_DATE, 'N/A')}<br/>
            <b>Period:</b> {row.get(config.COL_TIME_PERIOD, 'N/A')}<br/>
            <b>Location:</b> {row.get(config.COL_LOCATION_TYPE, 'N/A')}
        </div>
        """
        
        folium.CircleMarker(
            location=[row[config.COL_LAT], row[config.COL_LON]],
            radius=5,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=1,
            popup=folium.Popup(popup_html, max_width=220)
        ).add_to(cluster_container)

    return m


def create_heatmap(df: pd.DataFrame, radius: int = 18, blur: int = 22) -> folium.Map:
    """
    Creates a density HeatMap depicting aggregate geographic concentrations.
    """
    summary = get_spatial_summary(df)
    m = folium.Map(
        location=[summary["center_lat"], summary["center_lon"]],
        zoom_start=13,
        tiles="CartoDB dark_matter"
    )

    coords = df[[config.COL_LAT, config.COL_LON]].dropna()
    if not coords.empty:
        heat_data = coords.values.tolist()
        HeatMap(
            heat_data,
            radius=radius,
            blur=blur,
            max_zoom=14,
            gradient={0.2: "#3B82F6", 0.4: "#06B6D4", 0.6: "#10B981", 0.8: "#F59E0B", 1.0: "#EF4444"}
        ).add_to(m)

    return m


def get_area_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates incident volumes, area proportion, and top crime category per area.
    """
    if config.COL_AREA not in df.columns or df.empty:
        return pd.DataFrame(columns=[config.COL_AREA, "total_incidents", "percentage", "primary_crime"])

    grouped = df.groupby(config.COL_AREA)
    total_records = len(df)

    summary_rows = []
    for area, group in grouped:
        top_cat = group[config.COL_CATEGORY].mode().iloc[0] if not group.empty else "N/A"
        summary_rows.append({
            config.COL_AREA: area,
            "total_incidents": len(group),
            "percentage": round((len(group) / total_records) * 100, 2),
            "primary_crime": top_cat
        })

    result_df = pd.DataFrame(summary_rows).sort_values(by="total_incidents", ascending=False)
    return result_df
