"""
Script to generate production Jupyter notebooks for the project.
Produces:
- notebooks/01_data_exploration.ipynb
- notebooks/02_spatial_analysis.ipynb
- notebooks/03_forecasting.ipynb
"""

import json
from pathlib import Path

NOTEBOOKS_DIR = Path(__file__).resolve().parent.parent / "notebooks"
NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)

def make_notebook(cells):
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.11.0"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }

def make_markdown_cell(source):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in source.strip().split("\n")]
    }

def make_code_cell(source):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in source.strip().split("\n")]
    }

# 1. 01_data_exploration.ipynb
nb1_cells = [
    make_markdown_cell("""# 01. Exploratory Data Analysis & Data Cleaning Pipeline
### Project: Smart Public Safety Analytics
**Focus:** Aggregate historical incident patterns, data quality inspection, and feature engineering.

> **CRITICAL METHODOLOGICAL NOTICE:**
> Reported Incidents ≠ Actual Underlying Crime. This notebook analyzes historical public open-data records. It does NOT predict individual behavior."""),
    make_code_cell("""import sys
from pathlib import Path
sys.path.append(str(Path.cwd().parent))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

import config
from src.data_loader import load_sample_dataset
from src.data_cleaning import inspect_raw_data, clean_and_validate_data
from src.feature_engineering import engineer_features
from src.eda import calculate_kpis, get_category_counts, get_trend_by_year, get_trend_by_month"""),
    make_markdown_cell("""## 1. Load Sample Incident Dataset & Inspect Health"""),
    make_code_cell("""raw_df, mapping, missing_critical, pii_flags = load_sample_dataset()
print(f"Loaded Raw Dataset: {raw_df.shape[0]} rows, {raw_df.shape[1]} columns")
print(f"PII Scan Result: {pii_flags if pii_flags else 'Safe - No PII detected'}")

raw_audit = inspect_raw_data(raw_df)
print(f"Duplicate records: {raw_audit['duplicate_count']}")
print(f"Overall missing rate: {raw_audit['overall_missing_pct']}%")
raw_df.head()"""),
    make_markdown_cell("""## 2. Execute Data Cleaning & Validation Pipeline
Steps:
1. Deduplication
2. Safe categorical missing imputation
3. Geographic coordinate boundary validation (-90..90, -180..180, excluding (0,0) null-island)
4. Datetime parsing and normalization"""),
    make_code_cell("""cleaned_df, clean_log = clean_and_validate_data(raw_df, mapping)
print("Pipeline Cleaning Audit:")
for step, val in clean_log.items():
    print(f" - {step}: {val}")"""),
    make_markdown_cell("""## 3. Analytical Feature Engineering
Deriving diurnal time periods (Night, Morning, Afternoon, Evening), calendar features, and weekend flags."""),
    make_code_cell("""featured_df = engineer_features(cleaned_df)
print("Engineered Columns:", [c for c in featured_df.columns if c not in cleaned_df.columns])
featured_df[["incident_id", "date", "time", "crime_category", "time_period", "is_weekend"]].head()"""),
    make_markdown_cell("""## 4. Exploratory Data Distributions"""),
    make_code_cell("""kpis = calculate_kpis(featured_df, raw_audit)
print("Summary KPIs:", kpis)

top_crimes = get_category_counts(featured_df, top_n=8)
print("\\nTop Reported Crime Categories:\\n", top_crimes)""")
]

# 2. 02_spatial_analysis.ipynb
nb2_cells = [
    make_markdown_cell("""# 02. Geospatial Analysis & Unsupervised Hotspot Detection
### Project: Smart Public Safety Analytics
**Focus:** Geographic coordinate validation, density mapping, DBSCAN clustering (haversine metric), and K-Means comparison.

> **CRITICAL METHODOLOGICAL NOTICE:**
> Detected clusters represent **historical incident concentrations in reported public data**. They must never be interpreted as predictive indicators of future crime."""),
    make_code_cell("""import sys
from pathlib import Path
sys.path.append(str(Path.cwd().parent))

import pandas as pd
import numpy as np
import folium

import config
from src.data_loader import load_sample_dataset
from src.data_cleaning import clean_and_validate_data
from src.feature_engineering import engineer_features
from src.spatial_analysis import get_spatial_summary, get_area_summary
from src.hotspot_detection import run_dbscan_clustering, run_kmeans_comparison"""),
    make_markdown_cell("""## 1. Load and Clean Spatial Incident Data"""),
    make_code_cell("""raw_df, mapping, _, _ = load_sample_dataset()
cleaned_df, _ = clean_and_validate_data(raw_df, mapping)
featured_df = engineer_features(cleaned_df)

spatial_summary = get_spatial_summary(featured_df)
print("Spatial Bounding Box Summary:")
for k, v in spatial_summary.items():
    print(f" - {k}: {v}")"""),
    make_markdown_cell("""## 2. Unsupervised Hotspot Detection with DBSCAN
Using haversine spherical distance metric on geographic coordinates in radians:
$$\\epsilon_{\\text{rad}} = \\frac{\\epsilon_{\\text{km}}}{6371.0088}$$"""),
    make_code_cell("""clustered_df, metrics, summary_df = run_dbscan_clustering(
    featured_df,
    eps_km=0.45,
    min_samples=15
)
print("DBSCAN Clustering Scorecard:")
for k, v in metrics.items():
    print(f" - {k}: {v}")

print("\\nDetected Hotspots Summary Table:")
summary_df"""),
    make_markdown_cell("""## 3. Methodological Comparison: K-Means vs. DBSCAN"""),
    make_code_cell("""km_df, km_metrics = run_kmeans_comparison(featured_df, n_clusters=5)
print(f"K-Means Inertia: {km_metrics['inertia']}")
print(f"K-Means Silhouette Score: {km_metrics['silhouette_score']}")
print("\\nDiscussion: Why DBSCAN is superior for spatial incident analysis:")
print("1. DBSCAN detects non-spherical clusters of arbitrary geometry.")
print("2. DBSCAN isolates sparse noise instead of forcing outliers into clusters.")""")
]

# 3. 03_forecasting.ipynb
nb3_cells = [
    make_markdown_cell("""# 03. Aggregate Incident Volume Forecasting & Evaluation
### Project: Smart Public Safety Analytics
**Focus:** Chronological time-series preparation, baseline naive forecasting, SARIMA modeling, lag-engineered Random Forest regression, and performance evaluation (MAE, RMSE, MAPE).

> **CRITICAL METHODOLOGICAL NOTICE:**
> Forecasts describe **aggregate historical statistical patterns** with uncertainty intervals. They do NOT predict individual behavior."""),
    make_code_cell("""import sys
from pathlib import Path
sys.path.append(str(Path.cwd().parent))

import pandas as pd
import numpy as np

import config
from src.data_loader import load_sample_dataset
from src.data_cleaning import clean_and_validate_data
from src.feature_engineering import engineer_features
from src.forecasting import (
    prepare_aggregate_series,
    run_chronological_evaluation,
    calculate_metrics
)"""),
    make_markdown_cell("""## 1. Prepare Aggregate Time Series"""),
    make_code_cell("""raw_df, mapping, _, _ = load_sample_dataset()
cleaned_df, _ = clean_and_validate_data(raw_df, mapping)
featured_df = engineer_features(cleaned_df)

ts_daily = prepare_aggregate_series(featured_df, freq='D', area='All Areas', category='All Categories')
print(f"Daily Time Series: {len(ts_daily)} days ({ts_daily.index.min()} to {ts_daily.index.max()})")
print(f"Average Daily Incidents: {ts_daily.mean():.2f}")
ts_daily.head()"""),
    make_markdown_cell("""## 2. Chronological Train/Test Holdout Evaluation
Split into training history and subsequent test holdout periods (no random shuffling!)."""),
    make_code_cell("""eval_results = run_chronological_evaluation(ts_daily, test_horizon=14)
print("Status:", eval_results['status'])

metrics_df = pd.DataFrame(eval_results['metrics']).T
print("\\nChronological Model Evaluation Scorecard:")
metrics_df"""),
    make_markdown_cell("""## 3. Comparison of Actual vs Forecast"""),
    make_code_cell("""test_s = eval_results['test']
preds = eval_results['predictions']

comparison_df = pd.DataFrame({
    'Actual': test_s,
    'SARIMA': preds['SARIMA'],
    'Random Forest (ML)': preds['Random Forest'],
    'Seasonal Naive': preds['Seasonal Naive']
})
comparison_df""")
]

with open(NOTEBOOKS_DIR / "01_data_exploration.ipynb", "w", encoding="utf-8") as f:
    json.dump(make_notebook(nb1_cells), f, indent=2)

with open(NOTEBOOKS_DIR / "02_spatial_analysis.ipynb", "w", encoding="utf-8") as f:
    json.dump(make_notebook(nb2_cells), f, indent=2)

with open(NOTEBOOKS_DIR / "03_forecasting.ipynb", "w", encoding="utf-8") as f:
    json.dump(make_notebook(nb3_cells), f, indent=2)

print("Created 3 Jupyter notebooks in", NOTEBOOKS_DIR)
