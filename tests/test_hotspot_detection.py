"""Unit tests for src/hotspot_detection.py"""
import pandas as pd
import numpy as np
from src.hotspot_detection import run_dbscan_clustering, run_kmeans_comparison
import config

def test_dbscan_clustering():
    # Generate 50 points clustered tightly around (37.77, -122.41) and 5 scattered noise points
    np.random.seed(42)
    cluster_lats = np.random.normal(37.77, 0.002, 50)
    cluster_lons = np.random.normal(-122.41, 0.002, 50)
    noise_lats = [37.85, 37.70, 37.65, 37.90, 37.60]
    noise_lons = [-122.30, -122.50, -122.35, -122.45, -122.40]

    all_lats = list(cluster_lats) + noise_lats
    all_lons = list(cluster_lons) + noise_lons

    df = pd.DataFrame({
        config.COL_LAT: all_lats,
        config.COL_LON: all_lons,
        config.COL_CATEGORY: ["Theft"] * len(all_lats),
        config.COL_AREA: ["Downtown"] * len(all_lats)
    })

    clustered_df, metrics, summary_df = run_dbscan_clustering(df, eps_km=0.5, min_samples=10)

    assert "cluster_id" in clustered_df.columns
    assert metrics["total_clusters"] >= 1
    assert metrics["noise_points"] > 0
    assert not summary_df.empty
    assert "Cluster Label" in summary_df.columns

def test_kmeans_comparison():
    df = pd.DataFrame({
        config.COL_LAT: [37.77, 37.78, 37.79, 37.80, 37.81, 37.82, 37.83, 37.84],
        config.COL_LON: [-122.41, -122.42, -122.43, -122.44, -122.45, -122.46, -122.47, -122.48]
    })
    km_df, metrics = run_kmeans_comparison(df, n_clusters=2)
    assert "kmeans_cluster" in km_df.columns
    assert "inertia" in metrics
    assert "silhouette_score" in metrics
