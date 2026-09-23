"""Unit tests for src/data_loader.py"""
import pandas as pd
from src.data_loader import detect_column_mappings, scan_pii_columns, load_sample_dataset
import config

def test_detect_column_mappings():
    raw_columns = ["Date_Occurred", "Time_Occurred", "Offense_Type", "Area_Name", "LAT", "LON"]
    mapping, missing = detect_column_mappings(raw_columns)
    
    assert config.COL_DATE in mapping
    assert mapping[config.COL_DATE] == "Date_Occurred"
    assert config.COL_CATEGORY in mapping
    assert mapping[config.COL_CATEGORY] == "Offense_Type"
    assert config.COL_LAT in mapping
    assert mapping[config.COL_LAT] == "LAT"
    assert config.COL_LON in mapping
    assert mapping[config.COL_LON] == "LON"

def test_scan_pii_columns():
    safe_columns = ["date", "crime_type", "latitude", "longitude", "area"]
    flagged_safe = scan_pii_columns(safe_columns)
    assert len(flagged_safe) == 0

    sensitive_columns = ["victim_name", "phone_number", "ssn", "date", "crime_type"]
    flagged = scan_pii_columns(sensitive_columns)
    assert "victim_name" in flagged
    assert "phone_number" in flagged
    assert "ssn" in flagged
    assert "crime_type" not in flagged

def test_load_sample_dataset():
    df, mapping, missing, pii = load_sample_dataset()
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 1000
    assert config.COL_DATE in mapping
    assert config.COL_LAT in mapping
    assert config.COL_LON in mapping
