"""
Aggregate Crime Forecasting module.
Provides time-series preparation, baseline naive forecasting, ARIMA/SARIMA statistical modeling,
lag-engineered machine learning forecasting, chronological evaluation (MAE, RMSE, MAPE),
and prediction intervals.
"""

from typing import Dict, Any, Tuple, Optional
import warnings
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
import statsmodels.api as sm
from statsmodels.tsa.statespace.sarimax import SARIMAX

import config
from src.feature_engineering import create_lag_features

# Suppress statsmodels convergence warnings for cleaner UI logs
warnings.filterwarnings("ignore")

def prepare_aggregate_series(
    df: pd.DataFrame,
    freq: str = "D",
    area: Optional[str] = None,
    category: Optional[str] = None
) -> pd.Series:
    """
    Subsets dataset by area/category and resamples incident volume to a regular temporal grid.
    Fills missing intervals with 0 (since no recorded incidents = 0 incidents).
    """
    filtered = df.copy()

    if area and area != "All Areas" and config.COL_AREA in filtered.columns:
        filtered = filtered[filtered[config.COL_AREA] == area]

    if category and category != "All Categories" and config.COL_CATEGORY in filtered.columns:
        filtered = filtered[filtered[config.COL_CATEGORY] == category]

    if filtered.empty or config.COL_DATE not in filtered.columns:
        return pd.Series(dtype=float)

    filtered["dt_index"] = pd.to_datetime(filtered[config.COL_DATE])
    norm_freq = "ME" if freq == "M" else ("YE" if freq in ("Y", "A") else ("QE" if freq == "Q" else freq))
    ts = filtered.set_index("dt_index").resample(norm_freq).size()
    ts.name = "incident_count"
    return ts


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Calculates MAE, RMSE, and MAPE with zero-division protection.
    """
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)

    if len(y_true) == 0:
        return {"MAE": 0.0, "RMSE": 0.0, "MAPE": 0.0}

    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

    # Prevent division by zero in MAPE by replacing zero actuals with 1.0 or using epsilon
    non_zero_mask = y_true > 0
    if np.sum(non_zero_mask) > 0:
        mape = float(np.mean(np.abs((y_true[non_zero_mask] - y_pred[non_zero_mask]) / y_true[non_zero_mask])) * 100)
    else:
        mape = 0.0

    return {
        "MAE": round(mae, 2),
        "RMSE": round(rmse, 2),
        "MAPE": round(mape, 2)
    }


def forecast_naive_baseline(
    ts_series: pd.Series, 
    horizon: int = 14,
    season_length: int = 7
) -> Tuple[pd.Series, pd.Series]:
    """
    Generates Naive (last value) and Seasonal Naive forecasts.
    """
    last_val = float(ts_series.iloc[-1])
    naive_forecast = pd.Series([last_val] * horizon)

    if len(ts_series) >= season_length:
        season_vals = ts_series.iloc[-season_length:].values
        seasonal_naive_forecast = pd.Series([season_vals[i % season_length] for i in range(horizon)])
    else:
        seasonal_naive_forecast = naive_forecast.copy()

    return naive_forecast, seasonal_naive_forecast


def forecast_sarima(
    train_series: pd.Series,
    horizon: int = 14,
    order: Tuple[int, int, int] = (1, 1, 1),
    seasonal_order: Tuple[int, int, int, int] = (1, 0, 1, 7)
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Fits SARIMAX statistical model and forecasts future horizon with 95% confidence intervals.
    """
    try:
        model = SARIMAX(
            train_series,
            order=order,
            seasonal_order=seasonal_order,
            enforce_stationarity=False,
            enforce_invertibility=False
        )
        fitted = model.fit(disp=False, maxiter=50)
        fc_obj = fitted.get_forecast(steps=horizon)
        mean_fc = fc_obj.predicted_mean
        conf_int = fc_obj.conf_int(alpha=0.05)

        lower_bound = conf_int.iloc[:, 0].clip(lower=0.0) # Incidents cannot be negative
        upper_bound = conf_int.iloc[:, 1].clip(lower=0.0)
        mean_fc = mean_fc.clip(lower=0.0)

        return mean_fc, lower_bound, upper_bound
    except Exception:
        # Fallback to simple ARIMA(1, 1, 0) if convergence issues arise
        try:
            model = SARIMAX(train_series, order=(1, 1, 0), enforce_stationarity=False)
            fitted = model.fit(disp=False, maxiter=30)
            fc_obj = fitted.get_forecast(steps=horizon)
            mean_fc = fc_obj.predicted_mean.clip(lower=0.0)
            conf_int = fc_obj.conf_int(alpha=0.05)
            lower_b = conf_int.iloc[:, 0].clip(lower=0.0)
            upper_b = conf_int.iloc[:, 1].clip(lower=0.0)
            return mean_fc, lower_b, upper_b
        except Exception:
            # Absolute fallback to moving average
            last_mean = float(train_series.tail(7).mean())
            fc = pd.Series([last_mean] * horizon)
            return fc, fc * 0.7, fc * 1.3


def forecast_ml_regressor(
    ts_series: pd.Series,
    horizon: int = 14,
    model_type: str = "rf"
) -> pd.Series:
    """
    Fits a Lag-Engineered Machine Learning regressor (Random Forest or Ridge)
    and predicts multi-step recursively.
    """
    df_feat = pd.DataFrame({"incident_count": ts_series})
    lags = [1, 2, 7, 14]
    windows = [7, 14]

    feat_df = create_lag_features(df_feat, target_col="incident_count", lags=lags, rolling_windows=windows)
    feat_df = feat_df.dropna()

    if len(feat_df) < 15:
        # Insufficient training samples for ML lags, return mean
        return pd.Series([float(ts_series.mean())] * horizon)

    feature_cols = [c for c in feat_df.columns if c != "incident_count"]
    X = feat_df[feature_cols]
    y = feat_df["incident_count"]

    if model_type == "rf":
        model = RandomForestRegressor(n_estimators=60, max_depth=6, random_state=42)
    else:
        model = Ridge(alpha=1.0)

    model.fit(X, y)

    # Recursive multi-step forecasting
    history = list(ts_series.values)
    predictions = []

    last_date = ts_series.index[-1]
    freq = pd.infer_freq(ts_series.index) or "D"
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=horizon, freq=freq)

    for step_date in future_dates:
        row_feats = {}
        for lag in lags:
            row_feats[f"lag_{lag}"] = history[-lag] if len(history) >= lag else history[0]
        for w in windows:
            row_feats[f"rolling_mean_{w}"] = np.mean(history[-w:]) if len(history) >= w else np.mean(history)

        row_feats["month"] = step_date.month
        row_feats["day_of_week"] = step_date.dayofweek
        row_feats["day_of_year"] = step_date.dayofyear
        row_feats["quarter"] = step_date.quarter

        feat_vector = pd.DataFrame([row_feats])[feature_cols]
        pred_val = max(0.0, float(model.predict(feat_vector)[0]))
        predictions.append(round(pred_val, 2))
        history.append(pred_val)

    return pd.Series(predictions, index=future_dates)


def run_chronological_evaluation(
    ts_series: pd.Series,
    test_horizon: int = 14
) -> Dict[str, Any]:
    """
    Performs chronological train/test split evaluation comparing:
    - Baseline Naive
    - Baseline Seasonal Naive
    - SARIMA
    - ML Regressor (Random Forest)
    """
    if len(ts_series) <= test_horizon + 14:
        return {"status": "error", "message": "Insufficient data points for meaningful time series validation."}

    train_series = ts_series.iloc[:-test_horizon]
    test_series = ts_series.iloc[-test_horizon:]

    # 1. Baseline Naive
    naive_pred, s_naive_pred = forecast_naive_baseline(train_series, horizon=test_horizon)
    naive_pred.index = test_series.index
    s_naive_pred.index = test_series.index

    # 2. SARIMA
    sarima_pred, sarima_lower, sarima_upper = forecast_sarima(train_series, horizon=test_horizon)
    sarima_pred.index = test_series.index
    sarima_lower.index = test_series.index
    sarima_upper.index = test_series.index

    # 3. ML Regressor
    ml_pred = forecast_ml_regressor(train_series, horizon=test_horizon, model_type="rf")
    ml_pred.index = test_series.index

    y_true = test_series.values

    metrics_naive = calculate_metrics(y_true, naive_pred.values)
    metrics_s_naive = calculate_metrics(y_true, s_naive_pred.values)
    metrics_sarima = calculate_metrics(y_true, sarima_pred.values)
    metrics_ml = calculate_metrics(y_true, ml_pred.values)

    return {
        "status": "success",
        "train": train_series,
        "test": test_series,
        "predictions": {
            "Naive": naive_pred,
            "Seasonal Naive": s_naive_pred,
            "SARIMA": sarima_pred,
            "Random Forest": ml_pred
        },
        "bounds": {
            "sarima_lower": sarima_lower,
            "sarima_upper": sarima_upper
        },
        "metrics": {
            "Naive": metrics_naive,
            "Seasonal Naive": metrics_s_naive,
            "SARIMA": metrics_sarima,
            "Random Forest": metrics_ml
        }
    }
