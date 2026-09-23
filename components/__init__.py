"""
Enterprise UI Component Library.
Provides standardized, reusable widgets, KPI cards, tables, and theme wrappers.
"""

from .theme import inject_enterprise_styles, apply_plotly_theme, PALETTE, SEMANTIC_COLORS
from .kpi_card import render_kpi_metric
from .section_header import render_section_header, render_page_header
from .data_table import render_aggrid_table
from .banner import render_methodology_disclaimer
from .navigation import render_sidebar_menu, render_enterprise_sidebar, NAV_OPTIONS

__all__ = [
    "inject_enterprise_styles",
    "apply_plotly_theme",
    "PALETTE",
    "SEMANTIC_COLORS",
    "render_kpi_metric",
    "render_section_header",
    "render_page_header",
    "render_aggrid_table",
    "render_methodology_disclaimer",
    "render_sidebar_menu",
    "render_enterprise_sidebar",
    "NAV_OPTIONS"
]
