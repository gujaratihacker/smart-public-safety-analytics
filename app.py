"""
Smart Public Safety Analytics - Main Application Entry Point.
Initializes session state, applies design system styles, and routes to Overview dashboard.
"""

import streamlit as st
from components import inject_enterprise_styles
from components.navigation import _ensure_session_state, _run_pipeline, load_sample_dataset

# ── Page Config ─────────────────────────────────────────────
st.set_page_config(
    page_title="Smart Public Safety Analytics",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Inject Enterprise Styles ───────────────────────────────
inject_enterprise_styles()

# Bootstrap Icons CDN
st.markdown(
    '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">',
    unsafe_allow_html=True
)

# ── Bootstrap Data and Route ────────────────────────────────
_ensure_session_state()

if st.session_state["featured_df"] is None:
    try:
        raw_df, mapping, _, pii = load_sample_dataset()
        st.session_state["col_mapping"] = mapping
        st.session_state["pii_flags"] = pii
        st.session_state["dataset_source"] = "Synthetic Benchmark"
        _run_pipeline(raw_df, mapping)
    except Exception as e:
        st.error(f"Failed to load initial dataset: {e}")

st.switch_page("pages/1_📊_Overview.py")
