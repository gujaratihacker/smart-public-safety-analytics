"""
Statistical Analysis and Hypothesis Testing module.
Provides Chi-Square tests of independence, One-Way ANOVA tests across spatial districts,
correlation matrices, and area-level socioeconomic analysis with ecological fallacies disclaimers.
"""

from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np
from scipy import stats

import config

def perform_chi_square_test(
    df: pd.DataFrame, 
    col1: str = config.COL_CATEGORY, 
    col2: str = config.COL_TIME_PERIOD
) -> Dict[str, Any]:
    """
    Executes Pearson's Chi-Square Test of Independence between two categorical variables.
    Example: Is the distribution of crime categories independent of the time of day?
    """
    if col1 not in df.columns or col2 not in df.columns or df.empty:
        return {"status": "error", "message": f"Columns {col1} or {col2} not found in dataset."}

    contingency = pd.crosstab(df[col1], df[col2])
    chi2, p, dof, expected = stats.chi2_contingency(contingency)

    is_significant = p < 0.05
    interpretation = (
        f"Statistically significant association detected (p = {p:.4e} < 0.05). "
        f"The distribution of '{col1}' depends significantly on '{col2}'."
        if is_significant else
        f"No statistically significant association detected (p = {p:.4e} >= 0.05). "
        f"'{col1}' and '{col2}' appear statistically independent."
    )

    return {
        "status": "success",
        "contingency_table": contingency,
        "chi2_stat": round(float(chi2), 3),
        "p_value": float(p),
        "p_value_formatted": f"{p:.4e}" if p < 0.0001 else f"{p:.4f}",
        "dof": int(dof),
        "is_significant": is_significant,
        "interpretation": interpretation
    }


def perform_anova_district_test(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Executes One-Way ANOVA testing whether daily incident rates differ significantly across areas.
    """
    if config.COL_DATE not in df.columns or config.COL_AREA not in df.columns or df.empty:
        return {"status": "error", "message": "Required columns 'date' or 'area' missing."}

    daily_area_counts = df.groupby([config.COL_DATE, config.COL_AREA]).size().unstack(fill_value=0)

    # Need at least 2 areas with multiple samples
    valid_cols = [col for col in daily_area_counts.columns if len(daily_area_counts[col]) > 10]
    if len(valid_cols) < 2:
        return {"status": "error", "message": "Insufficient areas with data for ANOVA."}

    samples = [daily_area_counts[col].values for col in valid_cols]
    f_stat, p_val = stats.f_oneway(*samples)

    is_significant = p_val < 0.05
    interpretation = (
        f"Statistically significant variation across areas (F = {f_stat:.2f}, p = {p_val:.4e} < 0.05). "
        "Average daily incident counts differ significantly between geographic areas."
        if is_significant else
        f"No statistically significant variation across areas (F = {f_stat:.2f}, p = {p_val:.4f} >= 0.05)."
    )

    means = {area: round(float(daily_area_counts[area].mean()), 2) for area in valid_cols}
    stds = {area: round(float(daily_area_counts[area].std()), 2) for area in valid_cols}

    return {
        "status": "success",
        "f_stat": round(float(f_stat), 3),
        "p_value": float(p_val),
        "p_value_formatted": f"{p_val:.4e}" if p_val < 0.0001 else f"{p_val:.4f}",
        "is_significant": is_significant,
        "interpretation": interpretation,
        "area_means": means,
        "area_stds": stds
    }


def compute_descriptive_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates detailed descriptive statistics for daily aggregate incident volumes.
    """
    if config.COL_DATE not in df.columns or df.empty:
        return pd.DataFrame()

    daily = df.groupby(config.COL_DATE).size()
    
    stats_dict = {
        "Total Days Observed": len(daily),
        "Mean Daily Incidents": round(float(daily.mean()), 2),
        "Std Deviation": round(float(daily.std()), 2),
        "Median Daily Incidents": round(float(daily.median()), 2),
        "Min Daily Incidents": int(daily.min()),
        "Max Daily Incidents": int(daily.max()),
        "25th Percentile (Q1)": round(float(daily.quantile(0.25)), 2),
        "75th Percentile (Q3)": round(float(daily.quantile(0.75)), 2),
        "Interquartile Range (IQR)": round(float(daily.quantile(0.75) - daily.quantile(0.25)), 2),
        "Skewness": round(float(daily.skew()), 3),
        "Kurtosis": round(float(daily.kurtosis()), 3)
    }

    return pd.DataFrame(list(stats_dict.items()), columns=["Metric", "Value"])


def get_socioeconomic_indicators(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Constructs an area-level analytical dataset merging incident rates with municipal census variables.
    Note: Prominently warns about the ecological fallacy.
    """
    if config.COL_AREA not in df.columns or df.empty:
        return pd.DataFrame(), {}

    area_counts = df[config.COL_AREA].value_counts().to_dict()

    # Representative benchmark census profiles for the standard metropolitan areas
    socio_benchmarks = {
        "Downtown Central": {"population": 68000, "median_income": 82000, "unemployment_rate": 6.8, "poverty_rate": 14.2},
        "Mission Commercial": {"population": 54000, "median_income": 71000, "unemployment_rate": 6.2, "poverty_rate": 15.8},
        "Westside Arts": {"population": 42000, "median_income": 105000, "unemployment_rate": 3.9, "poverty_rate": 7.4},
        "Waterfront Marina": {"population": 36000, "median_income": 128000, "unemployment_rate": 3.1, "poverty_rate": 5.2},
        "South Rail Corridor": {"population": 29000, "median_income": 59000, "unemployment_rate": 8.1, "poverty_rate": 19.5}
    }

    rows = []
    for area, total_inc in area_counts.items():
        base = socio_benchmarks.get(area, {
            "population": 45000, "median_income": 75000, "unemployment_rate": 5.5, "poverty_rate": 12.0
        })
        pop = base["population"]
        rate_per_1k = round((total_inc / pop) * 1000, 2)
        rows.append({
            "Area": area,
            "Total Incidents": total_inc,
            "Population": pop,
            "Incident Rate per 1k": rate_per_1k,
            "Median Income ($)": base["median_income"],
            "Unemployment Rate (%)": base["unemployment_rate"],
            "Poverty Rate (%)": base["poverty_rate"]
        })

    socio_df = pd.DataFrame(rows).sort_values(by="Incident Rate per 1k", ascending=False).reset_index(drop=True)

    # Compute correlation between incident rate and poverty / unemployment
    if len(socio_df) >= 3:
        corr_unemployment = round(float(socio_df["Incident Rate per 1k"].corr(socio_df["Unemployment Rate (%)"])), 3)
        corr_income = round(float(socio_df["Incident Rate per 1k"].corr(socio_df["Median Income ($)"])), 3)
    else:
        corr_unemployment, corr_income = 0.0, 0.0

    meta = {
        "corr_unemployment": corr_unemployment,
        "corr_income": corr_income,
        "methodological_caveat": (
            "CRITICAL METHODOLOGICAL NOTE: Area-level statistical associations DO NOT establish "
            "individual-level causation (Ecological Fallacy). Reported crime numbers are heavily influenced "
            "by commercial activity, foot traffic density, police patrol allocation, and differing reporting "
            "rates across neighborhoods rather than the socio-economic status of residents."
        )
    }

    return socio_df, meta
