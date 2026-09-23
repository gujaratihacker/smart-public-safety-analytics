"""
Configuration module for Smart Public Safety Analytics Platform.
Centralizes paths, standardized column schemas, time periods, and UI styling.
"""

from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SAMPLE_DATA_DIR = DATA_DIR / "sample"
SAMPLE_DATA_PATH = SAMPLE_DATA_DIR / "sample_crime_data.csv"
DB_PATH = DATA_DIR / "public_safety.db"
MODELS_DIR = BASE_DIR / "models"

# Ensure runtime directories exist
for folder in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, SAMPLE_DATA_DIR, MODELS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# Application Metadata
APP_TITLE = "Smart Public Safety Analytics"
APP_SUBTITLE = "Spatiotemporal Crime Analysis, Hotspot Detection and Aggregate Crime Forecasting"
APP_TAGLINE = "Aggregate historical patterns and public data analytics"
VERSION = "1.0.0"

# Standard Canonical Schema
COL_ID = "incident_id"
COL_DATE = "date"
COL_TIME = "time"
COL_CATEGORY = "crime_category"
COL_AREA = "area"
COL_DISTRICT = "district"
COL_LAT = "latitude"
COL_LON = "longitude"
COL_LOCATION_TYPE = "location_type"
COL_DESCRIPTION = "description"

# Derived Feature Names
COL_DATETIME = "datetime"
COL_YEAR = "year"
COL_MONTH = "month"
COL_MONTH_NAME = "month_name"
COL_DAY = "day"
COL_DAY_OF_WEEK = "day_of_week"
COL_HOUR = "hour"
COL_QUARTER = "quarter"
COL_IS_WEEKEND = "is_weekend"
COL_TIME_PERIOD = "time_period"

# Time Period Definitions (24-hour hour ranges)
# Night: 22:00 - 03:59 | Morning: 04:00 - 09:59 | Afternoon: 10:00 - 15:59 | Evening: 16:00 - 21:59
TIME_PERIOD_CONFIG = {
    "Night": (22, 4),
    "Morning": (4, 10),
    "Afternoon": (10, 16),
    "Evening": (16, 22),
}

# Coordinate Bounding Validation (Global bounds)
LAT_MIN, LAT_MAX = -90.0, 90.0
LON_MIN, LON_MAX = -180.0, 180.0

# Known / Sensitive PII Column Keywords
SENSITIVE_PII_KEYWORDS = [
    "name", "victim_name", "first_name", "last_name", "phone", "phone_number",
    "ssn", "social_security", "sin", "aadhaar", "driver_license", "dl_num",
    "email", "address", "street_address", "home_address", "dob", "birth_date",
    "officer_name", "suspect_name", "witness_name"
]

# Common Column Aliases for Auto-Mapping
COLUMN_ALIASES = {
    COL_ID: ["incident_id", "id", "case_number", "dr_no", "report_num", "incident_num", "record_id"],
    COL_DATE: ["date", "incident_date", "date_occ", "occurred_date", "reported_date", "date_reported", "event_date"],
    COL_TIME: ["time", "incident_time", "time_occ", "occurred_time", "reported_time", "event_time"],
    COL_CATEGORY: ["crime_category", "crime_type", "primary_type", "offense_type", "offense_description", "type", "crime", "charge_description"],
    COL_AREA: ["area", "area_name", "neighborhood", "zone", "ward", "community", "precinct", "borough"],
    COL_DISTRICT: ["district", "district_id", "police_district", "sector", "division", "beat"],
    COL_LAT: ["latitude", "lat", "y_coordinate", "y", "location_latitude", "lat_deg"],
    COL_LON: ["longitude", "lon", "long", "x_coordinate", "x", "location_longitude", "lon_deg"],
    COL_LOCATION_TYPE: ["location_type", "premise_desc", "location_description", "premise", "place_type", "venue"],
    COL_DESCRIPTION: ["description", "narrative", "offense_details", "summary", "notes"]
}

# Responsible Analytics Disclaimers
CORE_DISCLAIMERS = [
    "Reported Incidents ≠ Actual Crime Prevalence: Many incidents go unreported or unrecorded, reflecting reporting propensities and law enforcement deployment rather than true crime rates.",
    "Historical Patterns ≠ Future Certainty: Historical concentrations highlight where incidents were reported in the past. They do not predetermine future events.",
    "No Individual Prediction: This system analyzes aggregate spatial and temporal volumes only. It cannot and should not be used to profile, predict, or evaluate individual behavior.",
    "Data Quality Limitations: Public datasets contain missing values, geocoding inaccuracies, reporting delays, and categorization changes over time.",
    "Ecological Fallacy: Neighborhood or area-level statistical associations cannot be applied to deduce characteristics of individuals living in those areas."
]

# Color Palette for Plotly Charts
COLOR_PALETTE = [
    "#2563EB", "#7C3AED", "#DB2777", "#EA580C", "#059669",
    "#0891B2", "#4F46E5", "#D97706", "#DC2626", "#475569"
]
