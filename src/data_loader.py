"""
Data Loader module.
Handles dataset ingestion from CSV, automated column schema mapping,
user-override mappings, and privacy/PII keyword auditing.
"""

from typing import Dict, List, Optional, Tuple, Union, BinaryIO
import re
import pandas as pd
from pathlib import Path

import config

def detect_column_mappings(df_columns: List[str]) -> Tuple[Dict[str, str], List[str]]:
    """
    Automatically maps uploaded dataframe columns to canonical schema fields
    based on case-insensitive alias dictionaries.

    Returns:
        mapping: Dict[canonical_field, dataset_column]
        unmapped_canonical: List of canonical fields that could not be automatically mapped
    """
    mapping = {}
    normalized_cols = {col: re.sub(r'[^a-zA-Z0-9]', '', str(col).lower()) for col in df_columns}
    
    for canonical_field, aliases in config.COLUMN_ALIASES.items():
        matched = False
        # Exact alias match
        for alias in aliases:
            clean_alias = re.sub(r'[^a-zA-Z0-9]', '', alias.lower())
            for orig_col, norm_col in normalized_cols.items():
                if norm_col == clean_alias:
                    mapping[canonical_field] = orig_col
                    matched = True
                    break
            if matched:
                break
        
        # Substring / partial match if not matched
        if not matched:
            for alias in aliases:
                clean_alias = re.sub(r'[^a-zA-Z0-9]', '', alias.lower())
                for orig_col, norm_col in normalized_cols.items():
                    if clean_alias in norm_col or norm_col in clean_alias:
                        # Avoid ambiguous collisions
                        if orig_col not in mapping.values():
                            mapping[canonical_field] = orig_col
                            matched = True
                            break
                if matched:
                    break

    unmapped = [f for f in [config.COL_DATE, config.COL_CATEGORY, config.COL_LAT, config.COL_LON] if f not in mapping]
    return mapping, unmapped


def scan_pii_columns(df_columns: List[str]) -> List[str]:
    """
    Scans column names against known PII / privacy-sensitive keyword list.
    """
    flagged = []
    for col in df_columns:
        norm = re.sub(r'[^a-zA-Z0-9]', '_', str(col).lower())
        for keyword in config.SENSITIVE_PII_KEYWORDS:
            if re.search(r'\b' + re.escape(keyword) + r'\b', norm) or keyword == norm:
                flagged.append(col)
                break
    return flagged


def load_csv_data(
    file_source: Union[str, Path, BinaryIO],
    encoding: Optional[str] = None
) -> Tuple[pd.DataFrame, Dict[str, str], List[str], List[str]]:
    """
    Reads CSV file safely with multiple encoding fallbacks.
    Returns:
        df: Raw DataFrame
        suggested_mapping: Dict[canonical_field, dataset_col]
        missing_critical: Critical canonical fields that could not be mapped
        pii_flags: List of sensitive column names detected
    """
    encodings_to_try = [encoding] if encoding else ["utf-8", "latin1", "cp1252", "iso-8859-1"]
    df = None
    last_err = None

    for enc in encodings_to_try:
        if not enc:
            continue
        try:
            if hasattr(file_source, "seek"):
                file_source.seek(0)
            df = pd.read_csv(file_source, encoding=enc, low_memory=False)
            break
        except (UnicodeDecodeError, Exception) as e:
            last_err = e
            continue

    if df is None:
        raise ValueError(f"Failed to read CSV with supported encodings. Error: {last_err}")

    suggested_mapping, missing_critical = detect_column_mappings(df.columns.tolist())
    pii_flags = scan_pii_columns(df.columns.tolist())

    return df, suggested_mapping, missing_critical, pii_flags


def load_sample_dataset() -> Tuple[pd.DataFrame, Dict[str, str], List[str], List[str]]:
    """
    Loads the benchmark synthetic sample dataset.
    """
    if not config.SAMPLE_DATA_PATH.exists():
        raise FileNotFoundError(f"Sample data file not found at {config.SAMPLE_DATA_PATH}")
    return load_csv_data(config.SAMPLE_DATA_PATH)
