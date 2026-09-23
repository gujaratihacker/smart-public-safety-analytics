# Smart Public Safety Analytics: Spatiotemporal Crime Analysis, Hotspot Detection and Aggregate Crime Forecasting

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B.svg)](https://streamlit.io/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.3+-F7931E.svg)](https://scikit-learn.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An end-to-end, production-grade Data Science web application designed for municipal public-data analysts, academic researchers, and public safety planning. The platform processes historical open-data incident datasets to uncover spatial clusters, diurnal rhythms, and multi-scale temporal trajectories, while providing aggregate volume forecasting.

---

> ### ⚠️ Critical Methodological & Ethical Disclaimer
> **Reported Incidents ≠ Actual Underlying Crime Prevalence**
> - Open crime datasets capture **only reported and recorded events**. They reflect community reporting habits, patrol deployments, and institutional recording practices rather than the true distribution of crime.
> - **Zero Individual Prediction:** This platform is strictly architected for macro aggregate spatial and temporal analytics. It **never** predicts individual criminal behavior, perpetrator recidivism, or profiles citizens.
> - **Hotspots as Historical Concentrations:** Unsupervised density clusters indicate where events were historically documented in public data; they do not dictate where future crime is destined to occur.

---

## 🏛️ System Architecture

```text
smart-public-safety-analytics/
│
├── app.py                      # Main application entry point & shared navigation
├── config.py                   # Central configuration, schemas, paths, diurnal bounds
├── requirements.txt            # Python dependencies
├── README.md                   # System documentation & setup guide
│
├── data/
│   ├── raw/                    # Uploaded open-data CSV records
│   ├── processed/              # Cleaned & validated analytical datasets
│   ├── sample/
│   │   └── sample_crime_data.csv # 4,500+ record calibrated synthetic benchmark
│   └── public_safety.db        # SQLite database (incidents, data_quality, forecasts)
│
├── src/
│   ├── data_loader.py          # CSV ingestion, auto-column mapping, PII auditor
│   ├── data_cleaning.py        # Deduplication, coordinate bounds check, safe imputation
│   ├── feature_engineering.py  # Diurnal periods (Night/Morning/Afternoon/Evening), lag features
│   ├── eda.py                  # High-performance aggregations & dynamic multi-criteria filter
│   ├── spatial_analysis.py     # Folium MarkerCluster, HeatMap, spatiotemporal slices
│   ├── hotspot_detection.py    # DBSCAN (haversine metric), K-Means comparison
│   ├── forecasting.py          # SARIMA, ML Lag Regressor, Naive baselines, MAE/RMSE/MAPE
│   ├── statistics.py           # Chi-Square test, One-Way ANOVA, socioeconomic associations
│   ├── database.py             # SQLite ORM, ingestion, and analytical SQL queries
│   └── utils.py                # Executive report generator, custom CSS, download helpers
│
├── pages/                      # Multi-Page Streamlit Dashboards
│   ├── 1_📊_Overview.py        # KPI scorecard, category distribution, diurnal curves
│   ├── 2_📈_Crime_Trends.py    # Longitudinal yearly, monthly, day-of-week, and hourly trends
│   ├── 3_🗺️_Spatial_Analysis.py # Interactive Folium maps, heatmaps, and spatiotemporal slices
│   ├── 4_🔥_Hotspots.py        # Unsupervised DBSCAN hotspot detection & K-Means comparison
│   ├── 5_🔮_Forecasting.py     # Aggregate volume forecasting (SARIMA vs. ML Regressors)
│   ├── 6_🛡️_Data_Quality.py    # 5-pillar data reliability audit & transformation log
│   ├── 7_⚖️_Statistics_&_Socioeconomic.py # Chi-Square, ANOVA tests & demographic correlations
│   └── 8_📖_About_&_Methodology.py # Ethical guidelines, architecture, and report export
│
├── notebooks/                  # Interactive Jupyter Notebooks
│   ├── 01_data_exploration.ipynb # Exploratory data analysis & data cleaning pipeline
│   ├── 02_spatial_analysis.ipynb # Spatial clustering, DBSCAN tuning & density heatmaps
│   └── 03_forecasting.ipynb      # Time-series decomposition, SARIMA & lag modeling
│
└── tests/                      # Pytest suite (15 unit tests passing)
    ├── test_data_loader.py
    ├── test_data_cleaning.py
    ├── test_feature_engineering.py
    ├── test_hotspot_detection.py
    ├── test_forecasting.py
    └── test_database.py
```

---

## ✨ Key Features

1. **Automated Column Mapping & PII Shield:**
   - Ingests public incident CSVs from any city (NYPD, LAPD, Chicago Data Portal, UK Police Data).
   - Fuzzy regex auto-maps diverse column aliases (`date_occ`, `primary_type`, `lat`, `long`).
   - Built-in PII scanner flags and suppresses personal identifiers (names, phone numbers, SSNs, victim addresses).

2. **5-Pillar Data Quality & Reliability Audit:**
   - Evaluates **Completeness, Uniqueness, Validity, Consistency, and Coverage**.
   - Generates a transparent, weighted Data Quality Score (0–100%).
   - Displays column-by-column missing rates and an automated cleaning transformation log.

3. **Geospatial Hotspot Detection (DBSCAN):**
   - Applies density-based clustering with spherical `haversine` metric on coordinate radians:
     $$\epsilon_{\text{rad}} = \frac{\epsilon_{\text{km}}}{6371.0088}$$
   - Identifies non-spherical clusters of arbitrary geometry and isolates sparse background noise.
   - Includes interactive K-Means comparison ($k$-means inertia and silhouette scores).

4. **Aggregate Time-Series Volume Forecasting:**
   - Forecasts macro incident counts by district and crime category over Daily, Weekly, or Monthly resolutions.
   - Models evaluated:
     - **Baseline:** Naive and Seasonal Naive ($s=7$ for daily).
     - **Statistical:** SARIMA $(p, d, q) \times (P, D, Q)_s$ with 95% confidence intervals.
     - **Machine Learning:** Random Forest regressor with lag (`lag_1`, `lag_7`, `lag_14`, `lag_30`) and rolling window features (`rolling_mean_7`, `rolling_mean_30`).
   - Chronological train/test split validation reporting **MAE, RMSE, and MAPE**.

5. **Hypothesis Testing & Socioeconomic Associations:**
   - **Chi-Square Test of Independence ($\chi^2$):** Tests whether crime category distribution is dependent on time of day or district.
   - **One-Way ANOVA:** Evaluates whether mean daily incident rates differ significantly across geographic zones.
   - **Socioeconomic Indicators:** Integrates municipal census profiles with prominent ecological fallacy warnings.

6. **SQLite Persistence & Analytical SQL Engine:**
   - Automatically stores cleaned incidents, data quality audit logs, and forecast evaluation runs into `data/public_safety.db`.
   - Includes built-in optimized SQL queries and an interactive SQL Query Inspector.

7. **Executive Report Generation:**
   - One-click compilation of an executive Markdown / HTML analytical summary report for academic or municipal submission.

---

## 🛠️ Technology Stack

| Domain | Technology | Purpose |
| :--- | :--- | :--- |
| **Language** | Python 3.11+ / 3.14 | Core computational backend |
| **Web Dashboard** | Streamlit | Interactive multi-page UI |
| **Data Manipulation** | Pandas, NumPy | High-performance vector processing |
| **Machine Learning** | Scikit-Learn | DBSCAN clustering, K-Means, Random Forest Regressor |
| **Time-Series** | Statsmodels | SARIMA statistical forecasting & confidence intervals |
| **Inferential Stats** | SciPy | Chi-Square test of independence, One-Way ANOVA |
| **Spatial Visualization** | Folium, Streamlit-Folium | Marker clustering, kernel density heatmaps |
| **Interactive Charts** | Plotly | Dynamic bar, pie, line, and forecast confidence band charts |
| **Database** | SQLite, SQLAlchemy | Relational persistence, schema indexing, SQL analytics |
| **Testing** | Pytest | Automated test suite |

---

## 🚀 Installation & Local Execution

### 1. Clone the Repository
```bash
git clone https://github.com/gujaratihacker/smart-public-safety-analytics.git
cd smart-public-safety-analytics
```

### 2. Create and Activate a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Unit Tests
```bash
python -m pytest tests/ -v
```
*(All 15 tests should pass cleanly in under 3 seconds)*

### 5. Launch the Dashboard
```bash
streamlit run app.py
```
Open your browser and navigate to `http://localhost:8501`.

---

## 📸 Screenshots & Workflow

| Module | Description |
| :--- | :--- |
| **Executive Overview** | Metric KPI cards, category breakdown, diurnal 24-hour cycle, and temporal trends. |
| **Longitudinal Trends** | Continuous monthly volume, YoY growth rate, day-of-week vs. hour heatmaps. |
| **Geospatial Analysis** | Interactive Folium map with marker clusters and density heatmaps. |
| **Hotspot Detection** | DBSCAN spatial clustering with haversine distance and noise isolation. |
| **Aggregate Forecasting** | SARIMA vs. Random Forest actual vs. predicted curves with 95% confidence intervals. |
| **Data Reliability Audit** | 5-pillar completeness, uniqueness, and coordinate validity scorecard. |

*(Placeholders: Add application screenshots here when compiling final university portfolio documents)*

---

## 📊 Dataset Schema Requirements

The application automatically maps diverse column names. For custom CSV uploads, the following core fields are supported:

| Canonical Field | Type | Example Aliases | Description |
| :--- | :--- | :--- | :--- |
| `date` *(Required)* | Date / String | `DATE`, `Date_Occurred`, `incident_date` | Date of incident occurrence |
| `time` | Time / String | `TIME`, `Time_Occurred`, `incident_time` | Time of occurrence (24-hr or 12-hr) |
| `crime_category` *(Required)* | String | `OFFENSE_TYPE`, `Crime_Type`, `Primary_Type` | Standardized crime classification |
| `latitude` *(Required)* | Float | `LATITUDE`, `Lat`, `Y_Coordinate` | Decimal latitude (-90.0 to 90.0) |
| `longitude` *(Required)* | Float | `LONGITUDE`, `Lon`, `X_Coordinate` | Decimal longitude (-180.0 to 180.0) |
| `area` | String | `DISTRICT`, `Area_Name`, `Neighborhood` | Geographic zone / precinct name |
| `location_type` | String | `LOCATION_DESCRIPTION`, `Premise` | Physical venue (Street, Retail, Residence) |

---

## 🧪 Scientific Methodology

### 1. Spatial Hotspot Formulation (DBSCAN)
Given geographic coordinate pairs $(\phi_i, \lambda_i)$ in radians, distance is calculated via spherical Haversine geometry:
$$d_H(p_1, p_2) = 2R \arcsin \sqrt{\sin^2\left(\frac{\Delta \phi}{2}\right) + \cos \phi_1 \cos \phi_2 \sin^2\left(\frac{\Delta \lambda}{2}\right)}$$
Where $R \approx 6371.0088\text{ km}$. $\epsilon_{\text{rad}} = \frac{\epsilon_{\text{km}}}{R}$. Core samples require at least `min_samples` within distance $\epsilon$. Outliers with insufficient neighborhood density are classified as noise ($-1$).

### 2. Time-Series Holdout Validation
To respect temporal causality and prevent data leakage, time series are evaluated strictly chronologically:
- Training: $[t_1, t_{N - H}]$
- Holdout Evaluation: $[t_{N - H + 1}, t_N]$ (where $H$ is the forecast horizon)
- Metrics computed:
  $$\text{MAE} = \frac{1}{H} \sum_{t=1}^H |y_t - \hat{y}_t|, \quad \text{RMSE} = \sqrt{\frac{1}{H} \sum_{t=1}^H (y_t - \hat{y}_t)^2}, \quad \text{MAPE} = \frac{100\%}{H} \sum_{t=1}^H \left|\frac{y_t - \hat{y}_t}{y_t + \epsilon}\right|$$

---

## 🤝 Responsible Use & Limitations

- **No Predictive Policing:** This software must not be deployed to direct punitive law enforcement interventions or assess individual citizens.
- **Reporting Disparities:** Differences in reported incident counts between neighborhoods often reflect differences in commercial density, foot traffic, and willingness to contact police rather than resident criminality.
- **Ecological Fallacy:** Aggregate statistics for an entire district do not characterize individuals residing within that district.

---

## 🔮 Future Enhancements

- Integration with real-time municipal GTFS transit feeds to correlate incident volume with commuter flow.
- Support for PostgreSQL / PostGIS backend for enterprise spatial indexing.
- Automated exogenous weather variables (temperature, precipitation) in the SARIMAX pipeline.

---

## 📄 License
This project is released under the **MIT License**.
