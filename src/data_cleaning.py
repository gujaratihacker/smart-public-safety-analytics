"""
Data Cleaning and Validation Pipeline.
Performs data inspection, deduplication, field-specific missing value imputation,
geographic coordinate bounding validation, date-time parsing, and string normalization.
"""

from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np

import config


def inspect_raw_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes summary health metrics for raw uploaded data.
    """
    total_rows = len(df)
    total_cols = len(df.columns)
    duplicate_count = int(df.duplicated().sum())
    missing_by_col = df.isnull().sum().to_dict()
    missing_pct_by_col = {col: round((count / total_rows) * 100, 2) if total_rows > 0 else 0.0 
                          for col, count in missing_by_col.items()}
    total_missing_cells = int(df.isnull().sum().sum())
    total_cells = total_rows * total_cols if total_rows > 0 else 1
    overall_missing_pct = round((total_missing_cells / total_cells) * 100, 2)

    dtypes_summary = {col: str(dtype) for col, dtype in df.dtypes.items()}

    return {
        "total_rows": total_rows,
        "total_cols": total_cols,
        "duplicate_count": duplicate_count,
        "missing_by_col": missing_by_col,
        "missing_pct_by_col": missing_pct_by_col,
        "overall_missing_pct": overall_missing_pct,
        "dtypes": dtypes_summary
    }


def clean_and_validate_data(
    df: pd.DataFrame, 
    col_mapping: Dict[str, str]
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Applies the full cleaning and validation pipeline:
    1. Rename columns according to canonical mapping.
    2. Deduplication.
    3. Categorical missing imputation ('Unknown').
    4. Coordinate validation (-90 <= lat <= 90, -180 <= lon <= 180, lat/lon != 0.0).
    5. Datetime parsing and validation.
    6. Text normalization (whitespace, title case).

    Returns:
        cleaned_df: Validated DataFrame with canonical column names
        audit_log: Execution summary dictionary
    """
    initial_rows = len(df)
    audit_log = {
        "initial_rows": initial_rows,
        "duplicates_removed": 0,
        "invalid_coords_removed": 0,
        "invalid_dates_removed": 0,
        "imputed_categorical_cells": 0,
        "final_rows": 0,
        "retention_rate_pct": 100.0
    }

    # Invert mapping to rename dataset_col -> canonical_field
    rename_map = {src_col: canon_field for canon_field, src_col in col_mapping.items() if src_col in df.columns}
    working_df = df.rename(columns=rename_map).copy()

    # Step 1: Remove exact duplicates
    dup_mask = working_df.duplicated()
    dup_count = int(dup_mask.sum())
    if dup_count > 0:
        working_df = working_df[~dup_mask].copy()
    audit_log["duplicates_removed"] = dup_count

    # Step 2: Handle Categoricals (safe imputation, do NOT blindly drop)
    categorical_cols = [config.COL_CATEGORY, config.COL_AREA, config.COL_DISTRICT, 
                        config.COL_LOCATION_TYPE, config.COL_DESCRIPTION]
    for col in categorical_cols:
        if col in working_df.columns:
            null_count = int(working_df[col].isnull().sum())
            audit_log["imputed_categorical_cells"] += null_count
            working_df[col] = working_df[col].fillna("Unknown").astype(str).str.strip().str.title()
            # Collapse empty strings to 'Unknown'
            working_df.loc[working_df[col] == "", col] = "Unknown"

    # Step 3: Parse and Validate Dates
    if config.COL_DATE in working_df.columns:
        parsed_dates = pd.to_datetime(working_df[config.COL_DATE], errors="coerce")
        invalid_dates_mask = parsed_dates.isnull()
        invalid_date_count = int(invalid_dates_mask.sum())
        audit_log["invalid_dates_removed"] = invalid_date_count
        
        # Drop rows where date is completely unparseable
        if invalid_date_count > 0:
            working_df = working_df[~invalid_dates_mask].copy()
            parsed_dates = parsed_dates[~invalid_dates_mask]
        
        working_df[config.COL_DATE] = parsed_dates.dt.date

        # If time is available, combine into a unified datetime
        if config.COL_TIME in working_df.columns:
            # Parse time string safely
            time_series = working_df[config.COL_TIME].astype(str).str.strip()
            # Try to build full datetime
            combined_dt_str = working_df[config.COL_DATE].astype(str) + " " + time_series
            parsed_dts = pd.to_datetime(combined_dt_str, errors="coerce")
            # If combined parsing failed on some rows, fallback to midnight for those
            fallback_dts = pd.to_datetime(working_df[config.COL_DATE])
            working_df[config.COL_DATETIME] = parsed_dts.fillna(fallback_dts)
        else:
            working_df[config.COL_DATETIME] = pd.to_datetime(working_df[config.COL_DATE])

    # Step 4: Validate Coordinates
    if config.COL_LAT in working_df.columns and config.COL_LON in working_df.columns:
        working_df[config.COL_LAT] = pd.to_numeric(working_df[config.COL_LAT], errors="coerce")
        working_df[config.COL_LON] = pd.to_numeric(working_df[config.COL_LON], errors="coerce")

        valid_lat = (working_df[config.COL_LAT] >= config.LAT_MIN) & (working_df[config.COL_LAT] <= config.LAT_MAX)
        valid_lon = (working_df[config.COL_LON] >= config.LON_MIN) & (working_df[config.COL_LON] <= config.LON_MAX)
        not_null_island = ~((working_df[config.COL_LAT] == 0.0) & (working_df[config.COL_LON] == 0.0))
        not_null = working_df[config.COL_LAT].notnull() & working_df[config.COL_LON].notnull()

        valid_coord_mask = valid_lat & valid_lon & not_null_island & not_null
        invalid_coord_count = int((~valid_coord_mask).sum())
        audit_log["invalid_coords_removed"] = invalid_coord_count

        if invalid_coord_count > 0:
            working_df = working_df[valid_coord_mask].copy()

    # Step 5: Assign synthetic/row-based ID if missing
    if config.COL_ID not in working_df.columns:
        working_df[config.COL_ID] = [f"INC-{i:06d}" for i in range(1, len(working_df) + 1)]
    else:
        working_df[config.COL_ID] = working_df[config.COL_ID].astype(str)

    # Compute final metrics
    audit_log["final_rows"] = len(working_df)
    if initial_rows > 0:
        audit_log["retention_rate_pct"] = round((len(working_df) / initial_rows) * 100, 2)

    audit_log["steps"] = [
        {"Step": "1. Ingestion & Schema Alignment", "Action": "Column Renaming & Canonical Casting", "Impacted": f"{initial_rows:,} records", "Status": "Passed"},
        {"Step": "2. Exact Deduplication", "Action": "Identical Row Deduplication", "Impacted": f"{dup_count:,} duplicates", "Status": "Removed" if dup_count > 0 else "Clean"},
        {"Step": "3. Categorical Imputation", "Action": "Impute 'Unknown' on missing fields", "Impacted": f"{audit_log['imputed_categorical_cells']:,} cells", "Status": "Imputed"},
        {"Step": "4. Date Validation", "Action": "Parse Dates & Drop Unparseable", "Impacted": f"{audit_log['invalid_dates_removed']:,} rows", "Status": "Validated"},
        {"Step": "5. Coordinate Validation", "Action": "Global Bounds & (0,0) Filter", "Impacted": f"{audit_log['invalid_coords_removed']:,} rows", "Status": "Validated"},
        {"Step": "6. Canonical ID Verification", "Action": "Ensure Unique Incident Identifier", "Impacted": f"{len(working_df):,} rows", "Status": "Active"},
    ]
    audit_log["imputed_cols"] = {col: "Fillna('Unknown') + Title Case" for col in categorical_cols if col in working_df.columns}

    working_df = working_df.reset_index(drop=True)
    return working_df, audit_log
