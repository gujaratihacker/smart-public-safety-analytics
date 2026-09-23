"""Unit tests for src/forecasting.py"""
import pandas as pd
import numpy as np
from src.forecasting import (
    prepare_aggregate_series,
    calculate_metrics,
    forecast_naive_baseline,
    forecast_sarima,
    forecast_ml_regressor,
    run_chronological_evaluation
)
import config

def test_calculate_metrics():
    y_true = np.array([10.0, 20.0, 30.0])
    y_pred = np.array([12.0, 18.0, 33.0])
    metrics = calculate_metrics(y_true, y_pred)
    
    assert "MAE" in metrics
    assert "RMSE" in metrics
    assert "MAPE" in metrics
    assert metrics["MAE"] == round((2.0 + 2.0 + 3.0) / 3, 2)

def test_prepare_aggregate_series():
    df = pd.DataFrame({
        config.COL_DATE: ["2024-01-01", "2024-01-01", "2024-01-02", "2024-01-04"],
        config.COL_AREA: ["Downtown", "Downtown", "Downtown", "Downtown"],
        config.COL_CATEGORY: ["Theft", "Theft", "Theft", "Theft"]
    })
    ts = prepare_aggregate_series(df, freq="D", area="Downtown", category="Theft")
    assert len(ts) == 4 # 2024-01-01 to 2024-01-04 (with 0 filled for 2024-01-03)
    assert ts.loc["2024-01-01"] == 2
    assert ts.loc["2024-01-03"] == 0

def test_forecast_naive_baseline():
    ts = pd.Series([5, 8, 12, 10, 15], index=pd.date_range("2024-01-01", periods=5, freq="D"))
    naive, s_naive = forecast_naive_baseline(ts, horizon=3, season_length=2)
    assert len(naive) == 3
    assert naive.iloc[0] == 15
    assert naive.iloc[1] == 15

def test_run_chronological_evaluation():
    dates = pd.date_range("2024-01-01", periods=60, freq="D")
    counts = [10 + int(5 * np.sin(i * np.pi / 7) + (i % 3)) for i in range(60)]
    ts = pd.Series(counts, index=dates)

    results = run_chronological_evaluation(ts, test_horizon=7)
    assert results["status"] == "success"
    assert "metrics" in results
    assert "SARIMA" in results["metrics"]
    assert "Random Forest" in results["metrics"]
    assert "Naive" in results["metrics"]
