"""
Page 5: Aggregate Forecasting.
SARIMA forecasting with enterprise presentation, backtesting, and model comparison.
Uses forecasting module: prepare_aggregate_series, forecast_sarima,
forecast_naive_baseline, forecast_ml_regressor, run_chronological_evaluation.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit_antd_components as sac

import config
from src.forecasting import (
    prepare_aggregate_series, forecast_sarima, forecast_naive_baseline,
    forecast_ml_regressor, run_chronological_evaluation, calculate_metrics,
)
from components import (
    inject_enterprise_styles, apply_plotly_theme, render_kpi_metric,
    render_section_header, render_page_header, render_methodology_disclaimer, render_aggrid_table,
    render_enterprise_sidebar,
)

st.set_page_config(page_title="Forecasting – Public Safety Analytics", page_icon="🛡️", layout="wide")
inject_enterprise_styles()
st.markdown('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">', unsafe_allow_html=True)

# ── Sidebar & Active Filtered Data ────────────────────────
df = render_enterprise_sidebar("Aggregate Forecasting")

# ── Page Header ────────────────────────────────────
render_page_header("Aggregate Incident Forecasting", "Time-series modelling of historical incident volume for short-term aggregate projections.", icon="🔮")

render_methodology_disclaimer(
    "Forecasting Ethical Boundary",
    "This module predicts aggregate statistical volumes (total incidents per day/month), NOT where or when specific incidents will occur. "
    "Forecasts are intended for resource-planning purposes only.",
    banner_type="warning"
)

if df.empty:
    sac.result(label="No Data Available", description="Load a dataset or adjust filters.", status="empty")
    st.stop()

# ── Sub-navigation ─────────────────────────────────────────
view_idx = sac.segmented(
    items=[
        sac.SegmentedItem(label="SARIMA Forecast", icon="graph-up-arrow"),
        sac.SegmentedItem(label="Model Evaluation", icon="clipboard2-data-fill"),
    ],
    align="center", size="sm", return_index=True,
)

# ── Prepare time series ────────────────────────────────────
with st.sidebar:
    with st.expander("⚙️ Forecast Settings", expanded=False):
        all_areas = sorted(df[config.COL_AREA].dropna().unique().tolist()) if config.COL_AREA in df.columns else []
        fc_area = st.selectbox("Area Filter", ["All Areas"] + all_areas, key="fc_area")
        all_cats = sorted(df[config.COL_CATEGORY].dropna().unique().tolist())
        fc_cat = st.selectbox("Category Filter", ["All Categories"] + all_cats, key="fc_cat")
        fc_freq = st.selectbox("Temporal Resolution", ["D", "W", "ME"], index=0,
                               format_func=lambda x: {"D": "Daily", "W": "Weekly", "ME": "Monthly"}[x])

ts_series = prepare_aggregate_series(df, freq=fc_freq, area=fc_area, category=fc_cat)

if ts_series.empty or len(ts_series) < 14:
    sac.result(
        label="Insufficient Time-Series Data",
        description=f"Need >= 14 observations at selected frequency. Got {len(ts_series)}.",
        status="warning",
    )
    st.stop()

# ── View 0: SARIMA Forecast ───────────────────────────────
if view_idx == 0:
    render_section_header("Forecast Configuration", "Adjust SARIMA parameters and forecast horizon")

    p1, p2, p3, p4 = st.columns(4)
    with p1:
        horizon = st.slider("Forecast Horizon", 7, 60, 14)
    with p2:
        order_p = st.selectbox("AR(p)", [0, 1, 2], index=1)
    with p3:
        order_d = st.selectbox("I(d)", [0, 1, 2], index=1)
    with p4:
        order_q = st.selectbox("MA(q)", [0, 1, 2], index=1)

    sp1, sp2 = st.columns(2)
    with sp1:
        seasonal_m = st.selectbox("Seasonal Period (m)", [7, 12, 30], index=0,
                                   format_func=lambda x: {7: "Weekly (7)", 12: "Monthly (12)", 30: "30-day"}[x])
    with sp2:
        seasonal_P = st.selectbox("Seasonal AR(P)", [0, 1], index=1)

    # KPI row - Series info
    fk1, fk2, fk3 = st.columns(3)
    with fk1:
        render_kpi_metric("Training Observations", f"{len(ts_series)}", icon_name="clock-history",
                          subtext=f"Resolution: {fc_freq}")
    with fk2:
        render_kpi_metric("Forecast Horizon", f"{horizon} periods", icon_name="calendar-plus")
    with fk3:
        order_label = f"({order_p},{order_d},{order_q})×({seasonal_P},0,1,{seasonal_m})"
        render_kpi_metric("Model Order", order_label, icon_name="sliders")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Run SARIMA
    with st.spinner("Fitting SARIMA model..."):
        order = (order_p, order_d, order_q)
        seasonal_order = (seasonal_P, 0, 1, seasonal_m)
        mean_fc, lower_ci, upper_ci = forecast_sarima(ts_series, horizon=horizon,
                                                       order=order, seasonal_order=seasonal_order)

    # Forecast chart
    render_section_header("Aggregate Incident Forecast", "Historical volume with forward projection and confidence interval")

    fig = go.Figure()

    # Historical
    fig.add_trace(go.Scatter(x=ts_series.index, y=ts_series.values,
                              mode="lines+markers", name="Observed",
                              line=dict(color="#3B82F6", width=2),
                              marker=dict(size=3)))

    # Create forecast index
    freq_map = {"D": "D", "W": "W", "ME": "ME", "M": "ME"}
    fc_index = pd.date_range(start=ts_series.index[-1], periods=horizon + 1,
                              freq=freq_map.get(fc_freq, fc_freq))[1:]
    mean_fc.index = fc_index
    lower_ci.index = fc_index
    upper_ci.index = fc_index

    # Forecast line
    fig.add_trace(go.Scatter(x=fc_index, y=mean_fc.values,
                              mode="lines+markers", name="SARIMA Forecast",
                              line=dict(color="#22C55E", width=3, dash="dot"),
                              marker=dict(size=4)))

    # Confidence band
    fig.add_trace(go.Scatter(
        x=list(fc_index) + list(fc_index[::-1]),
        y=list(upper_ci.values) + list(lower_ci.values[::-1]),
        fill="toself", fillcolor="rgba(34,197,94,0.12)", line=dict(color="rgba(0,0,0,0)"),
        name="95% CI"))

    fig.update_layout(title=f"SARIMA Aggregate Forecast ({horizon}-Period Horizon)",
                      xaxis_title="Date", yaxis_title="Incident Count")
    fig = apply_plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

    # Forecast table
    render_section_header("Forecast Data", color_name="green-70")
    fc_df = pd.DataFrame({
        "Date": fc_index.strftime("%Y-%m-%d"),
        "Forecast": mean_fc.values.round(1),
        "Lower CI": lower_ci.values.round(1),
        "Upper CI": upper_ci.values.round(1),
    })
    render_aggrid_table(fc_df, height=250, key="fc_table")

# ── View 1: Model Evaluation ─────────────────────────────
elif view_idx == 1:
    render_section_header("Chronological Model Evaluation",
                          "Walk-forward train/test split comparing Naive, Seasonal Naive, SARIMA, and Random Forest")

    ev1, ev2 = st.columns(2)
    with ev1:
        eval_horizon = st.slider("Test Horizon (periods)", 7, min(30, max(8, len(ts_series) // 3)), 14)
    with ev2:
        st.caption(f"Training: {len(ts_series) - eval_horizon} obs → Testing: {eval_horizon} obs")

    with st.spinner("Running chronological evaluation..."):
        eval_results = run_chronological_evaluation(ts_series, test_horizon=eval_horizon)

    if eval_results.get("status") == "error":
        sac.result(label="Evaluation Failed", description=eval_results.get("message", ""), status="warning")
        st.stop()

    st.session_state["forecast_eval_results"] = eval_results

    # Metrics comparison table
    render_section_header("Model Performance Comparison", color_name="blue-70")
    metrics = eval_results["metrics"]
    metrics_rows = []
    for model_name, m in metrics.items():
        metrics_rows.append({
            "Model": model_name,
            "MAE": m["MAE"],
            "RMSE": m["RMSE"],
            "MAPE (%)": m["MAPE"],
        })
    metrics_df = pd.DataFrame(metrics_rows)
    render_aggrid_table(metrics_df, height=200, key="metrics_tbl")

    # Find best model
    best_model = metrics_df.loc[metrics_df["MAE"].idxmin(), "Model"]
    render_methodology_disclaimer(
        f"Best Performing Model: {best_model}",
        f"Based on lowest MAE ({metrics_df['MAE'].min():.2f}). Note: model selection should consider "
        "domain context, interpretability, and deployment constraints beyond raw accuracy.",
        banner_type="info"
    )

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # KPI row for best model
    best_metrics = metrics[best_model]
    ek1, ek2, ek3 = st.columns(3)
    with ek1:
        render_kpi_metric("Best MAE", f"{best_metrics['MAE']:.2f}",
                          icon_name="rulers", subtext=f"{best_model}")
    with ek2:
        render_kpi_metric("Best RMSE", f"{best_metrics['RMSE']:.2f}",
                          icon_name="speedometer", subtext=f"{best_model}")
    with ek3:
        render_kpi_metric("Best MAPE", f"{best_metrics['MAPE']:.1f}%",
                          icon_name="percent", subtext=f"{best_model}")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Actual vs Predicted chart
    render_section_header("Test Set: Actual vs Predicted", color_name="blue-70")

    train_s = eval_results["train"]
    test_s = eval_results["test"]
    preds = eval_results["predictions"]
    bounds = eval_results.get("bounds", {})

    fig_eval = go.Figure()

    # Training tail (last 30 for context)
    tail_n = min(30, len(train_s))
    fig_eval.add_trace(go.Scatter(x=train_s.index[-tail_n:], y=train_s.values[-tail_n:],
                                   mode="lines", name="Training (tail)",
                                   line=dict(color="#64748B", width=1.5)))

    # Actual test
    fig_eval.add_trace(go.Scatter(x=test_s.index, y=test_s.values,
                                   mode="lines+markers", name="Actual",
                                   line=dict(color="#3B82F6", width=2.5)))

    # All model predictions
    colors = {"Naive": "#94A3B8", "Seasonal Naive": "#F59E0B", "SARIMA": "#22C55E", "Random Forest": "#EF4444"}
    for model_name, pred_series in preds.items():
        fig_eval.add_trace(go.Scatter(
            x=pred_series.index, y=pred_series.values,
            mode="lines", name=model_name,
            line=dict(color=colors.get(model_name, "#8B5CF6"), width=2,
                      dash="dot" if model_name != "SARIMA" else "solid")))

    # SARIMA confidence band
    if "sarima_lower" in bounds and "sarima_upper" in bounds:
        sl = bounds["sarima_lower"]
        su = bounds["sarima_upper"]
        fig_eval.add_trace(go.Scatter(
            x=list(sl.index) + list(su.index[::-1]),
            y=list(su.values) + list(sl.values[::-1]),
            fill="toself", fillcolor="rgba(34,197,94,0.08)", line=dict(color="rgba(0,0,0,0)"),
            name="SARIMA 95% CI"))

    fig_eval.update_layout(title="Chronological Evaluation: All Models",
                           xaxis_title="Date", yaxis_title="Incident Count")
    fig_eval = apply_plotly_theme(fig_eval)
    st.plotly_chart(fig_eval, use_container_width=True)
