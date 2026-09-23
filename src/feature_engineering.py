"""
Feature Engineering module.
Extracts analytical temporal features, diurnal time periods, weekend indicators,
and creates lag and rolling window features for time-series forecasting.
"""

from typing import List
import pandas as pd
import numpy as np

import config

def assign_time_period(hour: int) -> str:
    """
    Categorizes hour (0-23) into standard diurnal periods:
    - Night: 22:00 - 03:59
    - Morning: 04:00 - 09:59
    - Afternoon: 10:00 - 15:59
    - Evening: 16:00 - 21:59
    """
    if hour >= 22 or hour < 4:
        return "Night"
    elif 4 <= hour < 10:
        return "Morning"
    elif 10 <= hour < 16:
        return "Afternoon"
    else:
        return "Evening"


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derives standard analytical features from the cleaned dataset.
    Adds:
        - year, month, month_name, day, day_of_week, day_of_week_num
        - hour, quarter, is_weekend, time_period
    """
    df = df.copy()

    if config.COL_DATETIME not in df.columns:
        if config.COL_DATE in df.columns:
            df[config.COL_DATETIME] = pd.to_datetime(df[config.COL_DATE])
        else:
            raise KeyError("Neither 'datetime' nor 'date' found in DataFrame for feature engineering.")

    dt_series = pd.to_datetime(df[config.COL_DATETIME])

    df[config.COL_YEAR] = dt_series.dt.year
    df[config.COL_MONTH] = dt_series.dt.month
    df[config.COL_MONTH_NAME] = dt_series.dt.month_name()
    df[config.COL_DAY] = dt_series.dt.day
    df[config.COL_DAY_OF_WEEK] = dt_series.dt.day_name()
    df["day_of_week_num"] = dt_series.dt.dayofweek # 0=Monday, 6=Sunday
    df[config.COL_HOUR] = dt_series.dt.hour
    df[config.COL_QUARTER] = dt_series.dt.quarter
    df[config.COL_IS_WEEKEND] = df["day_of_week_num"].isin([5, 6]) # Saturday or Sunday
    
    # Assign time period
    df[config.COL_TIME_PERIOD] = df[config.COL_HOUR].apply(assign_time_period)

    return df


def create_lag_features(
    ts_df: pd.DataFrame,
    target_col: str = "incident_count",
    lags: List[int] = [1, 7, 14, 30],
    rolling_windows: List[int] = [7, 30]
) -> pd.DataFrame:
    """
    Constructs lag and rolling-statistic features for chronological time-series forecasting.
    Includes calendar features (month, day of week, day of year).
    """
    df_feat = ts_df.copy()
    
    # Create lag features
    for lag in lags:
        df_feat[f"lag_{lag}"] = df_feat[target_col].shift(lag)

    # Create rolling mean features (lagged by 1 to prevent data leakage)
    for window in rolling_windows:
        df_feat[f"rolling_mean_{window}"] = df_feat[target_col].shift(1).rolling(window=window).mean()

    # Calendar features from index if datetime index
    if isinstance(df_feat.index, pd.DatetimeIndex):
        df_feat["month"] = df_feat.index.month
        df_feat["day_of_week"] = df_feat.index.dayofweek
        df_feat["day_of_year"] = df_feat.index.dayofyear
        df_feat["quarter"] = df_feat.index.quarter

    return df_feat
