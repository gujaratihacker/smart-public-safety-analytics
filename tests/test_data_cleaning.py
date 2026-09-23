"""Unit tests for src/data_cleaning.py"""
import pandas as pd
import numpy as np
from src.data_cleaning import clean_and_validate_data, inspect_raw_data
import config

def test_clean_and_validate_data_duplicates_and_coords():
    # Setup test dataframe with 1 duplicate, 1 out of bounds lat, 1 null-island coord, 1 missing category
    data = {
        "event_date": ["2024-01-01", "2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
        "event_time": ["12:00:00", "12:00:00", "15:30:00", "02:00:00", "23:00:00"],
        "offense": ["Theft", "Theft", None, "Assault", "Burglary"],
        "lat": [37.77, 37.77, 37.78, 150.0, 0.0], # 150 is invalid lat, 0.0 is null island
        "lon": [-122.41, -122.41, -122.42, -122.40, 0.0]
    }
    raw_df = pd.DataFrame(data)
    mapping = {
        config.COL_DATE: "event_date",
        config.COL_TIME: "event_time",
        config.COL_CATEGORY: "offense",
        config.COL_LAT: "lat",
        config.COL_LON: "lon"
    }

    cleaned_df, audit_log = clean_and_validate_data(raw_df, mapping)

    # 1 duplicate should be dropped
    assert audit_log["duplicates_removed"] == 1
    # 2 invalid coords (150.0 and 0.0,0.0) dropped
    assert audit_log["invalid_coords_removed"] == 2
    # Categorical null imputed to Unknown
    assert audit_log["imputed_categorical_cells"] >= 1
    assert "Unknown" in cleaned_df[config.COL_CATEGORY].values
    # Check remaining row count
    assert len(cleaned_df) == 2
    assert audit_log["final_rows"] == 2

def test_inspect_raw_data():
    df = pd.DataFrame({
        "a": [1, 2, 2, None],
        "b": ["x", "y", "y", "z"]
    })
    audit = inspect_raw_data(df)
    assert audit["total_rows"] == 4
    assert audit["total_cols"] == 2
    assert audit["duplicate_count"] == 1
    assert audit["missing_by_col"]["a"] == 1
