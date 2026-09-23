"""
Synthetic sample data generator for Smart Public Safety Analytics.
Generates realistic multi-year spatio-temporal incident data with clear synthetic labeling.
Uses only standard library modules (random, math, csv, datetime) for maximum portability.
"""

import csv
import random
import math
from datetime import datetime, timedelta
from pathlib import Path

# Fix seed for reproducibility
random.seed(42)

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "sample"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "sample_crime_data.csv"

# Areas and their cluster centers (Metro Bay Area coordinates)
AREAS = {
    "Downtown Central": {
        "lat": 37.7790, "lon": -122.4170, "radius": 0.012, "weight": 0.35, "district": "District 1",
        "top_crimes": ["Theft / Larceny", "Public Disorder", "Assault", "Vandalism", "Robbery"]
    },
    "Mission Commercial": {
        "lat": 37.7600, "lon": -122.4190, "radius": 0.010, "weight": 0.25, "district": "District 3",
        "top_crimes": ["Theft / Larceny", "Motor Vehicle Theft", "Vandalism", "Burglary", "Assault"]
    },
    "Westside Arts": {
        "lat": 37.7750, "lon": -122.4350, "radius": 0.009, "weight": 0.16, "district": "District 5",
        "top_crimes": ["Burglary", "Theft / Larceny", "Motor Vehicle Theft", "Fraud"]
    },
    "Waterfront Marina": {
        "lat": 37.8020, "lon": -122.4370, "radius": 0.011, "weight": 0.14, "district": "District 2",
        "top_crimes": ["Theft / Larceny", "Vandalism", "Public Disorder", "Burglary"]
    },
    "South Rail Corridor": {
        "lat": 37.7490, "lon": -122.3920, "radius": 0.014, "weight": 0.10, "district": "District 4",
        "top_crimes": ["Motor Vehicle Theft", "Burglary", "Vandalism", "Narcotics"]
    }
}

LOCATION_TYPES = [
    "Street / Sidewalk", "Commercial Retail", "Parking Facility", 
    "Residential Apartment", "Transit Station", "Park / Public Space", 
    "Bar / Restaurant", "Alleyway"
]

ALL_CRIMES = [
    "Theft / Larceny", "Burglary", "Assault", "Motor Vehicle Theft",
    "Vandalism", "Public Disorder", "Robbery", "Fraud", "Narcotics"
]

# Diurnal probabilities by hour (0 to 23)
HOURLY_WEIGHTS = [
    0.025, 0.020, 0.015, 0.010, 0.008, 0.007,  # 00:00 - 05:00 (trough)
    0.015, 0.025, 0.040, 0.050, 0.055, 0.060,  # 06:00 - 11:00 (morning rise)
    0.065, 0.065, 0.060, 0.065, 0.075, 0.085,  # 12:00 - 17:00 (afternoon / rush)
    0.090, 0.085, 0.070, 0.055, 0.045, 0.035   # 18:00 - 23:00 (evening peak)
]

def generate_sample_dataset(num_records=4500):
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 12, 31)
    date_range_days = (end_date - start_date).days

    area_names = list(AREAS.keys())
    area_weights = [AREAS[a]["weight"] for a in area_names]

    records = []
    
    for i in range(1, num_records + 1):
        # Pick date with seasonal modifier (higher in summer: June-August)
        random_day_offset = random.randint(0, date_range_days)
        rec_date = start_date + timedelta(days=random_day_offset)
        
        # Seasonality probability acceptance
        month = rec_date.month
        seasonal_factor = 1.0 + 0.25 * math.sin((month - 3) * math.pi / 6.0) # peak in summer (~July)
        if random.random() > (seasonal_factor / 1.3):
            # slightly resample
            random_day_offset = random.randint(0, date_range_days)
            rec_date = start_date + timedelta(days=random_day_offset)

        # Pick hour according to diurnal profile
        hour = random.choices(range(24), weights=HOURLY_WEIGHTS)[0]
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        rec_time = f"{hour:02d}:{minute:02d}:{second:02d}"

        # Weekend modifier: weekend evenings have more public disorder & assault
        is_weekend = rec_date.weekday() >= 4  # Fri, Sat, Sun

        # Pick area
        chosen_area = random.choices(area_names, weights=area_weights)[0]
        area_info = AREAS[chosen_area]

        # Pick crime category
        if is_weekend and hour >= 18 and random.random() < 0.4:
            crime_category = random.choice(["Assault", "Public Disorder", "Theft / Larceny"])
        else:
            crime_category = random.choices(
                area_info["top_crimes"] + ALL_CRIMES,
                weights=[3]*len(area_info["top_crimes"]) + [1]*len(ALL_CRIMES)
            )[0]

        # Location Type
        if crime_category == "Motor Vehicle Theft":
            location_type = random.choice(["Street / Sidewalk", "Parking Facility"])
        elif crime_category == "Burglary":
            location_type = random.choice(["Residential Apartment", "Commercial Retail"])
        elif crime_category in ["Assault", "Public Disorder"]:
            location_type = random.choice(["Bar / Restaurant", "Street / Sidewalk", "Park / Public Space"])
        else:
            location_type = random.choice(LOCATION_TYPES)

        # Coordinates: 92% tightly clustered in area, 8% random spatial noise (crucial for DBSCAN testing)
        is_noise = random.random() < 0.08
        if is_noise:
            # Spread across general metropolitan bounding box
            lat = round(37.73 + random.random() * (37.82 - 37.73), 6)
            lon = round(-122.46 + random.random() * (-122.38 - -122.46), 6)
        else:
            # Normal distribution around area center
            radius = area_info["radius"]
            lat = round(random.gauss(area_info["lat"], radius / 2.5), 6)
            lon = round(random.gauss(area_info["lon"], radius / 2.5), 6)

        incident_id = f"SYN-{rec_date.year}-{i:05d}"
        date_str = rec_date.strftime("%Y-%m-%d")

        records.append({
            "incident_id": incident_id,
            "date": date_str,
            "time": rec_time,
            "crime_category": crime_category,
            "area": chosen_area,
            "district": area_info["district"],
            "latitude": lat,
            "longitude": lon,
            "location_type": location_type,
            "description": f"Reported {crime_category} at {location_type}"
        })

    # Add controlled data quality quirks (realistic anomalies for the cleaning & validation pipeline)
    # 1. Add 12 exact duplicates
    for dup_idx in range(12):
        dup_record = dict(records[dup_idx])
        records.append(dup_record)

    # 2. Add 8 missing or invalid coordinates (e.g. 0,0 or null)
    for err_coord_idx in range(15, 23):
        if err_coord_idx % 2 == 0:
            records[err_coord_idx]["latitude"] = ""
            records[err_coord_idx]["longitude"] = ""
        else:
            records[err_coord_idx]["latitude"] = 0.0
            records[err_coord_idx]["longitude"] = 0.0

    # 3. Add 10 missing categorical values (e.g. location_type or crime_category missing)
    for err_cat_idx in range(30, 40):
        records[err_cat_idx]["location_type"] = ""

    # Sort primarily by date and time
    records.sort(key=lambda r: (r["date"], r["time"]))

    fieldnames = [
        "incident_id", "date", "time", "crime_category", "area", 
        "district", "latitude", "longitude", "location_type", "description"
    ]

    with open(OUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"Generated {len(records)} records into {OUT_FILE}")

if __name__ == "__main__":
    generate_sample_dataset()
