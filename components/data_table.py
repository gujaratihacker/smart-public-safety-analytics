"""
Standardized Data Table Component using streamlit-aggrid.
Replaces raw st.dataframe with enterprise ag-Grid tables featuring
sorting, multi-column filtering, pagination, and dark slate styling.
"""

from typing import Optional
import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode

def render_aggrid_table(
    df: pd.DataFrame,
    height: int = 360,
    page_size: int = 10,
    enable_pagination: bool = True,
    key: Optional[str] = None
):
    """
    Renders an interactive enterprise AgGrid data table.
    
    Parameters:
        df: Input DataFrame to display
        height: Pixel height of the table container
        page_size: Number of records per pagination page
        enable_pagination: Whether pagination is active
        key: Unique Streamlit component key
    """
    if df.empty:
        st.info("No records available to display in table.")
        return

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(
        resizable=True,
        filterable=True,
        sortable=True,
        editable=False,
        groupable=False
    )

    if enable_pagination:
        gb.configure_pagination(
            paginationAutoPageSize=False,
            paginationPageSize=page_size
        )

    grid_options = gb.build()

    return AgGrid(
        df,
        gridOptions=grid_options,
        height=height,
        theme="alpine", # Styled via assets/styles.css dark override
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        key=key,
        reload_data=False
    )
