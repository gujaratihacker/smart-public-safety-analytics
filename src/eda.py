"""
Exploratory Data Analysis (EDA) module.
Provides aggregation engines, KPI calculations, dynamic filtering routines,
and cross-tabulations for dashboard visualizations.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import date
import pandas as pd
import numpy as np

import config

def calculate_kpis(df: pd.DataFrame, raw_audit: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Computes primary high-level summary KPIs.
    """
    total_incidents = len(df)
    unique_categories = int(df[config.COL_CATEGORY].nunique()) if config.COL_CATEGORY in df.columns else 0
    areas_covered = int(df[config.COL_AREA].nunique()) if config.COL_AREA in df.columns else 0

    if config.COL_DATE in df.columns and not df.empty:
        min_date = df[config.COL_DATE].min()
        max_date = df[config.COL_DATE].max()
    else:
        min_date, max_date = None, None

    missing_data_pct = raw_audit.get("overall_missing_pct", 0.0) if raw_audit else 0.0
    duplicates_removed = raw_audit.get("duplicates_removed", 0) if raw_audit else 0

    return {
        "total_incidents": total_incidents,
        "unique_categories": unique_categories,
        "areas_covered": areas_covered,
        "min_date": min_date,
        "max_date": max_date,
        "date_range_str": f"{min_date} to {max_date}" if min_date and max_date else "N/A",
        "missing_data_pct": missing_data_pct,
        "duplicates_removed": duplicates_removed
    }


def apply_filters(
    df: pd.DataFrame,
    date_range: Optional[Tuple[date, date]] = None,
    categories: Optional[List[str]] = None,
    areas: Optional[List[str]] = None,
    districts: Optional[List[str]] = None,
    time_periods: Optional[List[str]] = None,
    days_of_week: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Applies multi-criteria dynamic filtering across the analytical dataset.
    """
    filtered = df.copy()

    if date_range and len(date_range) == 2 and date_range[0] and date_range[1]:
        start_d, end_d = date_range[0], date_range[1]
        if config.COL_DATE in filtered.columns:
            filtered = filtered[(filtered[config.COL_DATE] >= start_d) & (filtered[config.COL_DATE] <= end_d)]

    if categories and config.COL_CATEGORY in filtered.columns:
        filtered = filtered[filtered[config.COL_CATEGORY].isin(categories)]

    if areas and config.COL_AREA in filtered.columns:
        filtered = filtered[filtered[config.COL_AREA].isin(areas)]

    if districts and config.COL_DISTRICT in filtered.columns:
        filtered = filtered[filtered[config.COL_DISTRICT].isin(districts)]

    if time_periods and config.COL_TIME_PERIOD in filtered.columns:
        filtered = filtered[filtered[config.COL_TIME_PERIOD].isin(time_periods)]

    if days_of_week and config.COL_DAY_OF_WEEK in filtered.columns:
        filtered = filtered[filtered[config.COL_DAY_OF_WEEK].isin(days_of_week)]

    return filtered.reset_index(drop=True)


def get_category_counts(df: pd.DataFrame, top_n: int = 12) -> pd.DataFrame:
    """
    Returns incident frequency and percentage by crime category.
    """
    if config.COL_CATEGORY not in df.columns or df.empty:
        return pd.DataFrame(columns=[config.COL_CATEGORY, "count", "percentage"])

    counts = df[config.COL_CATEGORY].value_counts().reset_index()
    counts.columns = [config.COL_CATEGORY, "count"]
    counts["percentage"] = round((counts["count"] / len(df)) * 100, 2)
    return counts.head(top_n)


def get_trend_by_year(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates incident count by year with YoY percentage change.
    """
    if config.COL_YEAR not in df.columns or df.empty:
        return pd.DataFrame(columns=[config.COL_YEAR, "count", "yoy_pct"])

    yearly = df.groupby(config.COL_YEAR).size().reset_index(name="count")
    yearly = yearly.sort_values(by=config.COL_YEAR)
    yearly["yoy_pct"] = yearly["count"].pct_change() * 100
    yearly["yoy_pct"] = yearly["yoy_pct"].round(2)
    return yearly


def get_trend_by_month(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates incident count by continuous Year-Month (e.g. '2024-01').
    """
    if config.COL_DATETIME not in df.columns or df.empty:
        return pd.DataFrame(columns=["year_month", "count"])

    df_temp = df.copy()
    df_temp["year_month"] = pd.to_datetime(df_temp[config.COL_DATETIME]).dt.to_period("M").astype(str)
    monthly = df_temp.groupby("year_month").size().reset_index(name="count")
    return monthly.sort_values(by="year_month")


def get_trend_by_day_of_week(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates incident counts ordered Monday through Sunday.
    """
    if config.COL_DAY_OF_WEEK not in df.columns or df.empty:
        return pd.DataFrame(columns=["day_of_week", "count"])

    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    counts = df[config.COL_DAY_OF_WEEK].value_counts().reindex(order).fillna(0).reset_index()
    counts.columns = ["day_of_week", "count"]
    counts["count"] = counts["count"].astype(int)
    counts["percentage"] = round((counts["count"] / len(df)) * 100, 2) if len(df) > 0 else 0
    return counts


def get_trend_by_hour(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates incident counts across all 24 diurnal hours.
    """
    if config.COL_HOUR not in df.columns or df.empty:
        return pd.DataFrame(columns=["hour", "count"])

    hours_full = pd.DataFrame({"hour": list(range(24))})
    counts = df.groupby(config.COL_HOUR).size().reset_index(name="count")
    merged = pd.merge(hours_full, counts, on="hour", how="left").fillna(0)
    merged["count"] = merged["count"].astype(int)
    merged["hour_label"] = merged["hour"].apply(lambda h: f"{h:02d}:00")
    return merged


def get_seasonal_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates incidents across calendar months (1-12) to reveal seasonal cycles.
    """
    if config.COL_MONTH not in df.columns or df.empty:
        return pd.DataFrame(columns=["month", "month_name", "count"])

    months_full = pd.DataFrame({
        "month": list(range(1, 13)),
        "month_name": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    })
    counts = df.groupby(config.COL_MONTH).size().reset_index(name="count")
    merged = pd.merge(months_full, counts, on="month", how="left").fillna(0)
    merged["count"] = merged["count"].astype(int)
    return merged


def get_category_trend_over_time(df: pd.DataFrame, category: str, freq: str = "ME") -> pd.DataFrame:
    """
    Extracts time series counts for a specific crime category.
    """
    if df.empty or config.COL_CATEGORY not in df.columns or config.COL_DATETIME not in df.columns:
        return pd.DataFrame(columns=["date", "count"])

    norm_freq = "ME" if freq == "M" else ("YE" if freq in ("Y", "A") else ("QE" if freq == "Q" else freq))
    cat_df = df[df[config.COL_CATEGORY] == category].copy()
    cat_df["date_idx"] = pd.to_datetime(cat_df[config.COL_DATETIME])
    ts = cat_df.set_index("date_idx").resample(norm_freq).size().reset_index(name="count")
    ts.columns = ["date", "count"]
    return ts


def get_crosstab_category_period(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates a 2D contingency matrix between crime categories and time periods.
    """
    if df.empty or config.COL_CATEGORY not in df.columns or config.COL_TIME_PERIOD not in df.columns:
        return pd.DataFrame()

    ct = pd.crosstab(df[config.COL_CATEGORY], df[config.COL_TIME_PERIOD])
    period_order = ["Night", "Morning", "Afternoon", "Evening"]
    present_periods = [p for p in period_order if p in ct.columns]
    return ct[present_periods]
