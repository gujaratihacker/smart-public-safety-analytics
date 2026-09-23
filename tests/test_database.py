"""Unit tests for src/database.py"""
import pandas as pd
from src.database import (
    initialize_database,
    ingest_incidents,
    log_data_quality_metrics,
    query_incidents_by_category,
    query_incidents_by_area,
    query_monthly_trend,
    get_db_connection
)
import config

def test_database_lifecycle():
    initialize_database()
    
    test_df = pd.DataFrame({
        config.COL_ID: ["INC-001", "INC-002", "INC-003"],
        config.COL_DATE: ["2024-05-01", "2024-05-02", "2024-05-03"],
        config.COL_TIME: ["10:00:00", "14:30:00", "22:15:00"],
        config.COL_CATEGORY: ["Theft", "Burglary", "Theft"],
        config.COL_AREA: ["Downtown", "Mission", "Downtown"],
        config.COL_LAT: [37.77, 37.76, 37.78],
        config.COL_LON: [-122.41, -122.42, -122.41],
        config.COL_LOCATION_TYPE: ["Street", "Retail", "Street"]
    })

    rows_inserted = ingest_incidents(test_df)
    assert rows_inserted == 3

    # Test queries
    cat_df = query_incidents_by_category()
    assert not cat_df.empty
    assert "crime_category" in cat_df.columns
    assert "count" in cat_df.columns

    area_df = query_incidents_by_area()
    assert not area_df.empty
    assert "area" in area_df.columns

    monthly_df = query_monthly_trend()
    assert not monthly_df.empty

    # Test data quality logging
    log_data_quality_metrics({"completeness": 99.2, "validity": 98.5})
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM data_quality")
    dq_count = c.fetchone()[0]
    conn.close()
    assert dq_count >= 2
