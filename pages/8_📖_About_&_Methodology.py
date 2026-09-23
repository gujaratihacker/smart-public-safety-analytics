"""
Page 8: About & Methodology.
Project documentation, tech stack, ethical framework, data dictionary, and academic references.
"""

import streamlit as st
import textwrap

import config
from components import (
    inject_enterprise_styles, render_section_header, render_page_header, render_methodology_disclaimer,
    render_enterprise_sidebar,
)

st.set_page_config(page_title="About – Public Safety Analytics", page_icon="🛡️", layout="wide")
inject_enterprise_styles()
st.markdown('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">', unsafe_allow_html=True)

# ── Sidebar & Active Filtered Data ────────────────────────
df = render_enterprise_sidebar("About & Methodology")

# ── Page Header ────────────────────────────────────────────
render_page_header("About & Methodology", "Project documentation, analytical methodology, technology stack, and ethical framework.", icon="📖")

# ── Project Overview ───────────────────────────────────────
render_section_header("Project Overview", "Mission, scope, and design philosophy")

st.markdown(textwrap.dedent("""
**Smart Public Safety Analytics** is an end-to-end spatiotemporal crime analysis platform designed
for aggregate historical pattern recognition in publicly available incident data.

**Core Objective**: Enable data-driven insights for urban safety resource planning through transparent,
reproducible, and ethically-bounded analytics.

**Key Capabilities**:
- Automated data ingestion, cleaning, and validation pipeline
- Multi-scale temporal trend analysis (annual, monthly, diurnal, seasonal)
- Interactive geospatial mapping with density heatmaps
- DBSCAN density-based hotspot detection with K-Means comparison
- SARIMA aggregate incident volume forecasting
- Inferential statistical testing (Chi-square, ANOVA, correlation)
- Full audit trail for data quality and pipeline transparency
"""))

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ── Ethical Framework ──────────────────────────────────────
render_section_header("Ethical Framework & Analytical Boundaries", "Responsible data science principles")

render_methodology_disclaimer(
    "Fundamental Ethical Principle",
    "This platform analyses AGGREGATE historical patterns in publicly available data. "
    "It does NOT predict individual criminal behaviour, identify individuals, or enable surveillance. "
    "All methodologies operate at the population/geographic level only.",
    banner_type="warning"
)

col_e1, col_e2 = st.columns(2)

with col_e1:
    st.markdown(textwrap.dedent("""
    ### What This Platform DOES
    - ✅ Analyses **aggregate** historical incident volumes
    - ✅ Identifies **geographic concentration** patterns
    - ✅ Forecasts **total monthly incident counts**
    - ✅ Tests **statistical associations** between variables
    - ✅ Provides **transparent audit trails** for all processing
    - ✅ Uses only **publicly available** open data
    """))

with col_e2:
    st.markdown(textwrap.dedent("""
    ### What This Platform Does NOT Do
    - ❌ Predict **individual** criminal behaviour
    - ❌ **Identify** or profile individuals
    - ❌ Enable **predictive policing** or surveillance
    - ❌ Use **demographic** or protected characteristic data
    - ❌ Claim **causal relationships** from correlations
    - ❌ Access **private** or restricted datasets
    """))

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ── Methodology ────────────────────────────────────────────
render_section_header("Analytical Methodology", "Technical approaches and model specifications")

with st.expander("Data Pipeline", expanded=False):
    st.markdown(textwrap.dedent("""
    | Stage | Method | Details |
    |-------|--------|---------|
    | **Ingestion** | `pandas.read_csv` | Auto-detection of encoding, delimiters, date formats |
    | **Column Mapping** | Fuzzy matching | Maps user columns to canonical schema via string similarity |
    | **PII Detection** | Regex scanning | Flags potential PII columns (names, SSNs, emails, phones) |
    | **Cleaning** | Multi-step pipeline | Deduplication, null handling, coordinate validation, type casting |
    | **Feature Engineering** | Temporal decomposition | Year, month, quarter, day-of-week, hour, time-period extraction |
    | **Storage** | SQLite | Lightweight local database for query performance |
    """))

with st.expander("Hotspot Detection (DBSCAN)", expanded=False):
    st.markdown(textwrap.dedent("""
    **Algorithm**: Density-Based Spatial Clustering of Applications with Noise (DBSCAN)

    | Parameter | Description | Default |
    |-----------|-------------|---------|
    | `eps` | Neighbourhood radius in kilometres | 0.45 km |
    | `min_samples` | Minimum core-point density | 15 |
    | `metric` | Distance function | Haversine (spherical) |

    **Why DBSCAN over K-Means?**
    - Discovers arbitrary-shape clusters (not just spherical)
    - Automatically determines number of clusters
    - Isolates sparse noise points rather than forcing them into clusters
    - Better suited for geographic incident data with natural density variation
    """))

with st.expander("Aggregate Forecasting (SARIMA)", expanded=False):
    st.markdown(textwrap.dedent("""
    **Model**: Seasonal Autoregressive Integrated Moving Average (SARIMA)

    | Component | Description |
    |-----------|-------------|
    | **AR(p)** | Autoregressive terms capturing linear dependency on past values |
    | **I(d)** | Differencing order for stationarity |
    | **MA(q)** | Moving average terms for residual error modelling |
    | **Seasonal (P,D,Q,m)** | Seasonal counterparts with period m (default: 12 months) |

    **Evaluation**: Walk-forward cross-validation with MAE, RMSE, MAPE, and R² metrics.

    **Scope**: Forecasts predict **total aggregate monthly incident volume** only — not
    where or when individual incidents will occur.
    """))

with st.expander("Statistical Testing", expanded=False):
    st.markdown(textwrap.dedent("""
    | Test | Purpose | Variables |
    |------|---------|-----------|
    | **Chi-Square (χ²)** | Independence test | Category × Time Period |
    | **One-Way ANOVA** | Mean comparison | Daily counts across days of week |
    | **Pearson Correlation** | Linear association | Numeric feature pairs |

    All tests use significance level α = 0.05 with appropriate null hypotheses stated.
    """))

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ── Technology Stack ───────────────────────────────────────
render_section_header("Technology Stack", "Libraries, frameworks, and infrastructure")

st.markdown(textwrap.dedent("""
| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Streamlit 1.x | Interactive web application framework |
| **Design System** | streamlit-shadcn-ui, streamlit-antd-components | Enterprise UI components |
| **Navigation** | streamlit-option-menu | Professional sidebar navigation |
| **Data Tables** | streamlit-aggrid | Enterprise sortable/filterable data grids |
| **Visualisation** | Plotly Express + Graph Objects | Interactive statistical charts |
| **Mapping** | Folium + streamlit-folium | Interactive geographic visualisation |
| **Data Processing** | Pandas, NumPy | Data manipulation and computation |
| **ML / Clustering** | scikit-learn (DBSCAN, KMeans) | Unsupervised spatial clustering |
| **Forecasting** | statsmodels (SARIMAX) | Time-series aggregate forecasting |
| **Statistics** | SciPy | Hypothesis testing (χ², ANOVA, Pearson) |
| **Database** | SQLite3 | Lightweight local persistence |
| **Styling** | Custom CSS + Bootstrap Icons | Enterprise dark-slate design tokens |
"""))

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ── Data Dictionary ────────────────────────────────────────
render_section_header("Canonical Data Dictionary", "Standard schema for incident datasets")

st.markdown(textwrap.dedent("""
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `incident_date` | date | ✅ | Date of reported incident |
| `incident_time` | time | ⬜ | Time of reported incident |
| `crime_category` | string | ✅ | Offense classification label |
| `area` | string | ⬜ | Geographic district / precinct |
| `latitude` | float | ✅ | WGS-84 latitude coordinate |
| `longitude` | float | ✅ | WGS-84 longitude coordinate |
| `location_type` | string | ⬜ | Premises type (street, residential, etc.) |
| `district` | string | ⬜ | Administrative boundary |

**Engineered Features** (auto-generated):
`year`, `month`, `month_name`, `quarter`, `day_of_week`, `hour`, `time_period`, `is_weekend`
"""))

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ── Academic References ────────────────────────────────────
render_section_header("Academic References", "Key literature and methodological sources")

st.markdown(textwrap.dedent("""
1. Ester, M., Kriegel, H.-P., Sander, J., & Xu, X. (1996). *A density-based algorithm for discovering clusters in large spatial databases with noise*. KDD-96 Proceedings.
2. Box, G. E. P., Jenkins, G. M., Reinsel, G. C., & Ljung, G. M. (2015). *Time Series Analysis: Forecasting and Control* (5th ed.). Wiley.
3. Chainey, S. & Ratcliffe, J. (2005). *GIS and Crime Mapping*. Wiley.
4. Sherman, L. W. (1995). *Hot spots of crime and criminal careers of places*. Crime and Place, 4, 35–52.
5. Hyndman, R. J. & Athanasopoulos, G. (2021). *Forecasting: Principles and Practice* (3rd ed.). OTexts.
6. Richardson, R., Schultz, J. M., & Crawford, K. (2019). *Dirty Data, Bad Predictions*. NYU Law Review, 94(1).
"""))

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────
st.markdown(
    f'<div style="text-align:center;padding:20px;color:#64748B;font-size:12px;">'
    f'Smart Public Safety Analytics v{config.VERSION}<br/>'
    f'Built with Streamlit · Aggregate Historical Analysis Only<br/>'
    f'© 2024 – Academic Research Project'
    f'</div>',
    unsafe_allow_html=True,
)
