"""
Theme and Design Tokens Module.
Defines centralized colors, fonts, CSS injection, and the global Plotly template.
"""

from pathlib import Path
import streamlit as st
import plotly.graph_objects as go
import plotly.io as pio

# Path to centralized stylesheet
CSS_PATH = Path(__file__).resolve().parent.parent / "assets" / "styles.css"

# Enterprise Dark Slate Palette
PALETTE = {
    "canvas": "#0B0F17",
    "surface": "#111827",
    "card": "#1E293B",
    "border": "#334155",
    "border_subtle": "rgba(255, 255, 255, 0.08)",
    "primary": "#3B82F6",
    "primary_hover": "#2563EB",
    "secondary": "#6366F1",
    "text_primary": "#F8FAFC",
    "text_muted": "#94A3B8"
}

# Semantic Severity / Risk Scale
SEMANTIC_COLORS = {
    "high": "#EF4444",      # High incident density / risk
    "medium": "#F59E0B",    # Moderate concentration
    "low": "#10B981",       # Low concentration / stable
    "info": "#06B6D4",      # Analytical baseline
    "neutral": "#64748B"    # Noise / background
}

# Plotly Categorical Sequence
PLOTLY_COLOR_SEQUENCE = [
    "#3B82F6", "#6366F1", "#06B6D4", "#10B981", 
    "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899", "#14B8A6"
]

def inject_enterprise_styles():
    """
    Reads assets/styles.css and injects it centrally into the Streamlit session.
    Never scatters ad-hoc CSS across components.
    """
    st.markdown(
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />'
        '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" />',
        unsafe_allow_html=True
    )
    if CSS_PATH.exists():
        with open(CSS_PATH, "r", encoding="utf-8") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)


def apply_plotly_theme(fig: go.Figure) -> go.Figure:
    """
    Applies the standardized enterprise dark slate theme to any Plotly figure.
    Ensures uniform typography, subtle gridlines, transparent canvas, and clean margins.
    """
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif",
            size=12,
            color=PALETTE["text_muted"]
        ),
        title_font=dict(
            family="Inter, sans-serif",
            size=15,
            color=PALETTE["text_primary"]
        ),
        colorway=PLOTLY_COLOR_SEQUENCE,
        xaxis=dict(
            gridcolor=PALETTE["card"],
            zerolinecolor=PALETTE["border"],
            showgrid=True,
            linecolor=PALETTE["border"],
            tickfont=dict(color=PALETTE["text_muted"], size=11)
        ),
        yaxis=dict(
            gridcolor=PALETTE["card"],
            zerolinecolor=PALETTE["border"],
            showgrid=True,
            linecolor=PALETTE["border"],
            tickfont=dict(color=PALETTE["text_muted"], size=11)
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color=PALETTE["text_muted"], size=11)
        ),
        margin=dict(l=16, r=16, t=44, b=24),
        hoverlabel=dict(
            bgcolor=PALETTE["card"],
            font_size=12,
            font_family="Inter, sans-serif",
            bordercolor=PALETTE["border"]
        )
    )
    return fig
