"""
Database management module.
Manages local SQLite database operations, schema creation, batch data ingestion,
and analytical SQL query executions.
"""

from typing import Dict, Any, List, Optional
import sqlite3
from datetime import datetime
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

import config

def get_db_connection() -> sqlite3.Connection:
    """Returns a native sqlite3 connection."""
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(config.DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def get_sqlalchemy_engine():
    """Returns a SQLAlchemy engine."""
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{config.DB_PATH}")


def initialize_database():
    """
    Creates the required schema tables if they do not exist:
    - incidents
    - data_quality
    - forecasts
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Table 1: incidents
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS incidents (
        id TEXT PRIMARY KEY,
        date TEXT NOT NULL,
        time TEXT,
        crime_category TEXT NOT NULL,
        area TEXT,
        latitude REAL,
        longitude REAL,
        location_type TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Table 2: data_quality
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS data_quality (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        metric TEXT NOT NULL,
        value REAL NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Table 3: forecasts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS forecasts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        area TEXT,
        crime_category TEXT,
        actual REAL,
        forecast REAL NOT NULL,
        lower_bound REAL,
        upper_bound REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Create indexes for fast analytical query performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_date ON incidents(date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_category ON incidents(crime_category);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_area ON incidents(area);")

    conn.commit()
    conn.close()


def ingest_incidents(df: pd.DataFrame) -> int:
    """
    Ingests cleaned incidents into the SQLite incidents table.
    Overwrites or appends depending on configuration.
    """
    initialize_database()
    
    # Prepare standard columns
    cols_to_keep = {
        config.COL_ID: "id",
        config.COL_DATE: "date",
        config.COL_TIME: "time",
        config.COL_CATEGORY: "crime_category",
        config.COL_AREA: "area",
        config.COL_LAT: "latitude",
        config.COL_LON: "longitude",
        config.COL_LOCATION_TYPE: "location_type"
    }

    db_df = pd.DataFrame()
    for col_key, db_col in cols_to_keep.items():
        if col_key in df.columns:
            db_df[db_col] = df[col_key]
        else:
            db_df[db_col] = None

    # Stringify dates and IDs
    db_df["id"] = db_df["id"].astype(str)
    db_df["date"] = db_df["date"].astype(str)
    if "time" in db_df.columns:
        db_df["time"] = db_df["time"].astype(str)

    engine = get_sqlalchemy_engine()
    # Replace table to refresh with current session data
    db_df.to_sql("incidents", con=engine, if_exists="replace", index=False)

    return len(db_df)


def log_data_quality_metrics(metrics: Dict[str, float]):
    """
    Stores data quality score cards into the data_quality table.
    """
    initialize_database()
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().isoformat()

    for metric_name, val in metrics.items():
        cursor.execute(
            "INSERT INTO data_quality (metric, value, timestamp) VALUES (?, ?, ?)",
            (metric_name, float(val), now_str)
        )
    conn.commit()
    conn.close()


def save_forecasts(forecast_records: List[Dict[str, Any]]):
    """
    Stores forecast evaluation results into the forecasts table.
    """
    if not forecast_records:
        return

    initialize_database()
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().isoformat()

    for r in forecast_records:
        cursor.execute("""
            INSERT INTO forecasts (date, area, crime_category, actual, forecast, lower_bound, upper_bound, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(r.get("date")),
            str(r.get("area", "All Areas")),
            str(r.get("crime_category", "All Categories")),
            float(r.get("actual", 0.0)) if r.get("actual") is not None else None,
            float(r.get("forecast", 0.0)),
            float(r.get("lower_bound", 0.0)) if r.get("lower_bound") is not None else None,
            float(r.get("upper_bound", 0.0)) if r.get("upper_bound") is not None else None,
            now_str
        ))

    conn.commit()
    conn.close()


# Analytical SQL Queries
def query_incidents_by_category() -> pd.DataFrame:
    """Executes SQL query aggregating incidents by category."""
    sql = """
    SELECT crime_category, COUNT(*) AS count,
           ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM incidents), 2) AS percentage
    FROM incidents
    GROUP BY crime_category
    ORDER BY count DESC;
    """
    engine = get_sqlalchemy_engine()
    return pd.read_sql(sql, con=engine)


def query_incidents_by_area() -> pd.DataFrame:
    """Executes SQL query aggregating incidents by area."""
    sql = """
    SELECT area, COUNT(*) AS count,
           ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM incidents), 2) AS percentage
    FROM incidents
    GROUP BY area
    ORDER BY count DESC;
    """
    engine = get_sqlalchemy_engine()
    return pd.read_sql(sql, con=engine)


def query_monthly_trend() -> pd.DataFrame:
    """Executes SQL query for monthly aggregation using substr(date, 1, 7)."""
    sql = """
    SELECT substr(date, 1, 7) AS year_month, COUNT(*) AS incident_count
    FROM incidents
    GROUP BY year_month
    ORDER BY year_month ASC;
    """
    engine = get_sqlalchemy_engine()
    return pd.read_sql(sql, con=engine)


def query_yearly_trend() -> pd.DataFrame:
    """Executes SQL query for yearly incident volume."""
    sql = """
    SELECT substr(date, 1, 4) AS year, COUNT(*) AS incident_count
    FROM incidents
    GROUP BY year
    ORDER BY year ASC;
    """
    engine = get_sqlalchemy_engine()
    return pd.read_sql(sql, con=engine)


def query_hourly_trend() -> pd.DataFrame:
    """Executes SQL query aggregating incidents by hour."""
    sql = """
    SELECT CAST(substr(time, 1, 2) AS INTEGER) AS hour, COUNT(*) AS incident_count
    FROM incidents
    WHERE time IS NOT NULL AND time != 'None' AND length(time) >= 2
    GROUP BY hour
    ORDER BY hour ASC;
    """
    engine = get_sqlalchemy_engine()
    return pd.read_sql(sql, con=engine)
