"""
Standardized Section and Page Header Components.
Clean native Streamlit headers with enterprise accent bars.
"""

from typing import Optional
import streamlit as st

COLOR_MAP = {
    "blue-70": "#3B82F6",
    "blue": "#3B82F6",
    "red-70": "#EF4444",
    "red": "#EF4444",
    "green-70": "#10B981",
    "green": "#10B981",
    "amber-70": "#F59E0B",
    "amber": "#F59E0B",
    "orange-70": "#F97316",
    "orange": "#F97316",
    "violet-70": "#8B5CF6",
    "violet": "#8B5CF6",
    "gray-70": "#64748B",
    "gray": "#64748B",
}


def render_page_header(
    title: str,
    subtitle: Optional[str] = None,
    icon: Optional[str] = None
):
    """
    Renders a unified enterprise page header with title and subtitle.
    """
    icon_prefix = f"{icon} " if icon else ""
    st.title(f"{icon_prefix}{title}")
    if subtitle:
        st.caption(subtitle)
    st.markdown("<hr style='margin: 4px 0 16px 0; border: none; border-top: 1px solid rgba(255,255,255,0.08);'/>", unsafe_allow_html=True)


def render_section_header(
    title: str,
    subtitle: Optional[str] = None,
    color_name: str = "blue-70"
):
    """
    Renders a unified section header with colored accent bar and subtitle.
    """
    hex_color = COLOR_MAP.get(color_name.lower(), "#3B82F6")
    st.subheader(title)
    if subtitle:
        st.caption(subtitle)
    st.markdown(
        f"<hr style='margin: 4px 0 14px 0; border: none; height: 2.5px; background: {hex_color}; border-radius: 2px;'/>",
        unsafe_allow_html=True
    )
