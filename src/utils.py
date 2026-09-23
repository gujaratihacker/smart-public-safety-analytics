"""
Utilities module.
Provides modern CSS styling, summary report generators (Markdown & HTML),
CSV export helpers, and Plotly theme formatters.
"""

from typing import Dict, Any, Optional
import pandas as pd
import streamlit as st
from datetime import datetime

import config

def apply_custom_css():
    """
    Injects custom CSS to style the Streamlit interface with a polished,
    modern Data Science dashboard look.
    """
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Metric KPI Card Styling */
        .kpi-container {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 12px;
            padding: 16px 20px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(8px);
            margin-bottom: 12px;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .kpi-container:hover {
            transform: translateY(-2px);
            border-color: #3B82F6;
        }
        .kpi-title {
            font-size: 13px;
            font-weight: 500;
            color: #94A3B8;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 6px;
        }
        .kpi-value {
            font-size: 26px;
            font-weight: 700;
            color: #F8FAFC;
            letter-spacing: -0.02em;
        }
        .kpi-subtext {
            font-size: 11px;
            color: #64748B;
            margin-top: 4px;
        }

        /* Notice & Warning Box */
        .disclaimer-box {
            background-color: rgba(239, 68, 68, 0.08);
            border-left: 4px solid #EF4444;
            padding: 12px 16px;
            border-radius: 0 8px 8px 0;
            margin: 12px 0 20px 0;
            font-size: 13px;
            color: #FCA5A5;
            line-height: 1.5;
        }
        .info-box {
            background-color: rgba(59, 130, 246, 0.08);
            border-left: 4px solid #3B82F6;
            padding: 12px 16px;
            border-radius: 0 8px 8px 0;
            margin: 12px 0 20px 0;
            font-size: 13px;
            color: #93C5FD;
            line-height: 1.5;
        }

        /* Badge Pill */
        .badge {
            display: inline-block;
            padding: 3px 10px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 9999px;
            background-color: rgba(59, 130, 246, 0.2);
            color: #60A5FA;
            border: 1px solid rgba(59, 130, 246, 0.3);
        }
        .badge-warning {
            background-color: rgba(245, 158, 11, 0.2);
            color: #FBBF24;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }
        .badge-success {
            background-color: rgba(16, 185, 129, 0.2);
            color: #34D399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        /* Section Headings */
        .section-header {
            font-size: 18px;
            font-weight: 600;
            color: #F1F5F9;
            margin-top: 24px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Streamlit Element Fine-Tuning */
        div[data-testid="stSidebarNav"] {
            padding-top: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)


def render_kpi_card(title: str, value: Any, subtext: str = "", badge: Optional[str] = None):
    """Renders a sleek HTML KPI card."""
    badge_html = f'<span class="badge" style="float: right;">{badge}</span>' if badge else ""
    html = f"""
    <div class="kpi-container">
        <div class="kpi-title">{title} {badge_html}</div>
        <div class="kpi-value">{value}</div>
        {f'<div class="kpi-subtext">{subtext}</div>' if subtext else ''}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def convert_df_to_csv(df: pd.DataFrame) -> bytes:
    """Encodes a DataFrame into UTF-8 CSV bytes for download."""
    return df.to_csv(index=False).encode("utf-8")


def generate_executive_report(
    kpis: Dict[str, Any],
    quality_scores: Dict[str, float],
    top_crimes: pd.DataFrame,
    hotspot_summary: pd.DataFrame,
    forecast_metrics: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generates an executive analytical summary report in Markdown format.
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    top_crime_md = ""
    if not top_crimes.empty:
        for _, r in top_crimes.head(5).iterrows():
            top_crime_md += f"- **{r.iloc[0]}**: {r['count']:,} incidents ({r.get('percentage', 0)}%)\n"
    else:
        top_crime_md = "No crime category breakdown available.\n"

    hotspots_md = ""
    if not hotspot_summary.empty:
        for _, r in hotspot_summary.head(4).iterrows():
            hotspots_md += f"- **{r['Cluster Label']}**: {r['Incidents']:,} incidents ({r['% of Total']}%) | Primary Area: {r['Primary Area']} | Dominant Crime: {r['Dominant Crime']}\n"
    else:
        hotspots_md = "No active spatial hotspots detected.\n"

    forecast_md = ""
    if forecast_metrics and "metrics" in forecast_metrics:
        for model_name, m in forecast_metrics["metrics"].items():
            forecast_md += f"- **{model_name}**: MAE = {m['MAE']}, RMSE = {m['RMSE']}, MAPE = {m['MAPE']}%\n"
    else:
        forecast_md = "Forecast evaluation not executed in current session.\n"

    report = f"""# Smart Public Safety Analytics: Executive Analytical Summary
**Generated:** {now_str}  
**Platform Version:** {config.VERSION}  
**Scope:** Aggregate Historical Incident Analytics (Public Open Data)

---

## 1. Executive Summary & KPIs
- **Total Reported Incidents Analyzed:** {kpis.get('total_incidents', 0):,}
- **Distinct Crime Categories:** {kpis.get('unique_categories', 0)}
- **Geographic Areas Covered:** {kpis.get('areas_covered', 0)}
- **Temporal Range:** {kpis.get('date_range_str', 'N/A')}
- **Raw Missing Data Rate:** {kpis.get('missing_data_pct', 0.0)}%
- **Duplicate Records Removed:** {kpis.get('duplicates_removed', 0)}

---

## 2. Data Reliability & Quality Audit
- **Completeness Score:** {quality_scores.get('completeness', 100.0)}%
- **Uniqueness Score:** {quality_scores.get('uniqueness', 100.0)}%
- **Coordinate Validity Score:** {quality_scores.get('validity', 100.0)}%
- **Consistency Score:** {quality_scores.get('consistency', 100.0)}%
- **Overall Data Reliability Index:** {quality_scores.get('overall', 100.0)}%

---

## 3. Dominant Historical Crime Categories
{top_crime_md}

---

## 4. Unsupervised Hotspot Clusters (DBSCAN)
{hotspots_md}

---

## 5. Aggregate Volume Forecasting Evaluation
{forecast_md}

---

## 6. Critical Methodological Disclaimers
1. **Reported Incidents ≠ Actual Crime Prevalence**: Many crimes go unreported. Reported crime volumes reflect reporting propensities, community trust, and police patrol presence rather than true criminal behavior.
2. **Historical Concentrations ≠ Future Prediction**: Spatial clusters denote historical reported incidents. They do not predict future events or deterministic criminal activity.
3. **No Individual Prediction**: This system operates strictly at the macro, aggregate spatio-temporal level. It cannot and must never be applied to individual profiling or recidivism prediction.
4. **Ecological Fallacy**: Geographic statistical correlations cannot be attributed to the characteristics of individual residents.

---
*Report generated automatically by Smart Public Safety Analytics Engine.*
"""
    return report
