"""
Standardized Enterprise KPI Card Component.
Renders consistent metric cards with label, value, delta badge, and icon.
"""

from typing import Optional
import streamlit as st

def render_kpi_metric(
    label: str,
    value: str,
    icon_name: str = "activity",
    delta: Optional[str] = None,
    delta_type: str = "neutral",
    subtext: str = ""
):
    """
    Renders an enterprise KPI card following the design system.
    
    Parameters:
        label: Metric title (e.g. 'TOTAL REPORTED INCIDENTS')
        value: Main numeric value (e.g. '4,492')
        icon_name: Bootstrap/Lucide icon identifier (e.g. 'shield-check', 'graph-up')
        delta: Optional delta string (e.g. '+3.4% YoY')
        delta_type: 'positive' (severity), 'negative' (reduction), or 'neutral'
        subtext: Explanatory microcopy
    """
    delta_class = f"delta-{delta_type}"
    delta_html = f'<span class="ent-kpi-delta {delta_class}">{delta}</span>' if delta else ""
    subtext_html = f'<div class="ent-kpi-subtext">{subtext}</div>' if subtext else ""

    # Bootstrap icon CDN integration
    icon_html = f'<i class="bi bi-{icon_name} ent-kpi-icon"></i>' if icon_name else ""

    card_html = (
        f'<div class="ent-kpi-card">'
        f'<div class="ent-kpi-header">'
        f'<span class="ent-kpi-label">{label}</span>'
        f'{icon_html}'
        f'</div>'
        f'<div class="ent-kpi-value">{value}</div>'
        f'<div class="ent-kpi-footer">'
        f'{delta_html}'
        f'{subtext_html}'
        f'</div>'
        f'</div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)
