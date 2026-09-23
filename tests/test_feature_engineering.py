"""Unit tests for src/feature_engineering.py"""
import pandas as pd
from src.feature_engineering import assign_time_period, engineer_features, create_lag_features
import config

def test_assign_time_period():
    assert assign_time_period(23) == "Night"
    assert assign_time_period(2) == "Night"
    assert assign_time_period(6) == "Morning"
    assert assign_time_period(11) == "Afternoon"
    assert assign_time_period(18) == "Evening"

def test_engineer_features():
    df = pd.DataFrame({
        config.COL_DATETIME: ["2024-03-15 14:30:00", "2024-03-16 23:45:00"], # 15 is Friday, 16 is Saturday
        config.COL_CATEGORY: ["Theft", "Assault"]
    })
    feat_df = engineer_features(df)
    
    assert config.COL_YEAR in feat_df.columns
    assert feat_df[config.COL_YEAR].iloc[0] == 2024
    assert feat_df[config.COL_MONTH].iloc[0] == 3
    assert feat_df[config.COL_MONTH_NAME].iloc[0] == "March"
    assert feat_df[config.COL_DAY_OF_WEEK].iloc[0] == "Friday"
    assert feat_df[config.COL_DAY_OF_WEEK].iloc[1] == "Saturday"
    assert feat_df[config.COL_IS_WEEKEND].iloc[0] == False
    assert feat_df[config.COL_IS_WEEKEND].iloc[1] == True
    assert feat_df[config.COL_TIME_PERIOD].iloc[0] == "Afternoon"
    assert feat_df[config.COL_TIME_PERIOD].iloc[1] == "Night"

def test_create_lag_features():
    dates = pd.date_range("2024-01-01", periods=40, freq="D")
    ts_df = pd.DataFrame({"incident_count": range(40)}, index=dates)
    lag_df = create_lag_features(ts_df, target_col="incident_count", lags=[1, 7], rolling_windows=[7])
    
    assert "lag_1" in lag_df.columns
    assert "lag_7" in lag_df.columns
    assert "rolling_mean_7" in lag_df.columns
    # Check value of lag_1 at row 10
    assert lag_df["lag_1"].iloc[10] == 9
