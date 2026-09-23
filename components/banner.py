"""
Standardized Notification & Methodology Banner Component.
Uses streamlit-antd-components sac.alert to enforce consistent disclaimers without inline styles.
"""

import streamlit as st
import streamlit_antd_components as sac

def render_methodology_disclaimer(
    title: str,
    text: str,
    banner_type: str = "warning"
):
    """
    Renders an enterprise notice or methodological disclaimer banner.
    
    Parameters:
        title: Short bold headline (e.g. 'METHODOLOGICAL PRINCIPLE')
        text: Explanatory paragraph (e.g. 'Reported Incidents != Actual Crime')
        banner_type: 'warning' (red/error), 'info' (blue), or 'neutral'
    """
    color_map = {
        "warning": "error",
        "disclaimer": "error",
        "info": "info",
        "success": "success"
    }
    alert_color = color_map.get(banner_type, "info")

    sac.alert(
        label=title,
        description=text,
        color=alert_color,
        banner=True,
        icon=True,
        closable=False
    )
