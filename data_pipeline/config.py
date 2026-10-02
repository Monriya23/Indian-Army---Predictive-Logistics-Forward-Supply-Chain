"""
Pipeline Configuration for SIH 2026 Problem Statement ID 26251:
Indian Army - Predictive Logistics & Forward Supply Chain (Phase 1).
"""

import os
from datetime import datetime

# Base Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
SYNTHETIC_DATA_DIR = os.path.join(DATA_DIR, "synthetic")
TRAINING_DATA_DIR = os.path.join(DATA_DIR, "training")
METADATA_DATA_DIR = os.path.join(DATA_DIR, "metadata")

RAW_WEATHER_DIR = os.path.join(RAW_DATA_DIR, "weather")
RAW_ELEVATION_DIR = os.path.join(RAW_DATA_DIR, "elevation")
RAW_ROADS_DIR = os.path.join(RAW_DATA_DIR, "roads")

# Reproducibility & Simulation Settings
RANDOM_SEED = 42
START_DATE = "2022-01-01"
END_DATE = "2024-12-31"  # 3 complete calendar years (1096 days)
NUM_NODES_PER_REGION = 5

# Broad, Non-sensitive Supply Categories
SUPPLY_CATEGORIES = [
    "FOOD",
    "WATER",
    "FUEL",
    "MEDICAL",
    "GENERAL_SUPPLIES",
]

# Vehicle Classes and Capacities (Abstract / Non-sensitive)
VEHICLE_CLASSES = {
    "LIGHT": {
        "capacity_kg": 2500,
        "speed_factor": 1.15,
        "max_slope_degree": 25.0,
        "operating_range_km": 450,
        "weather_resilience": 0.70,
    },
    "MEDIUM": {
        "capacity_kg": 7500,
        "speed_factor": 1.00,
        "max_slope_degree": 18.0,
        "operating_range_km": 600,
        "weather_resilience": 0.85,
    },
    "HEAVY": {
        "capacity_kg": 16000,
        "speed_factor": 0.80,
        "max_slope_degree": 12.0,
        "operating_range_km": 800,
        "weather_resilience": 0.90,
    },
}

# Study Regions - Public Geographical Corridors (Non-sensitive / Public Roads only)
REGIONS = {
    "REGION_A": {
        "region_id": "LADAKH",
        "name": "Ladakh / Western Himalayas",
        "corridor": "Srinagar - Kargil - Leh Public Highway (NH-1)",
        "center_lat": 34.1526,
        "center_lon": 77.5771,
        "bbox": [33.8, 74.8, 34.6, 77.8],  # min_lat, min_lon, max_lat, max_lon
        "terrain_type": "HIGH_ALTITUDE_MOUNTAINOUS",
        "base_terrain_difficulty": 0.85,
        "default_elevation_m": 3500.0,
        "node_prefix": "LAD",
        "reference_points": [
            {"id": "LAD-A01", "name": "Western Valley Staging Point", "lat": 34.20, "lon": 75.00, "role": "REGIONAL_DEPOT"},
            {"id": "LAD-A02", "name": "Pass Approach Transit Hub", "lat": 34.28, "lon": 75.60, "role": "TRANSIT_HUB"},
            {"id": "LAD-A03", "name": "Central Mountain Forward Base", "lat": 34.55, "lon": 76.13, "role": "FORWARD_DEPOT"},
            {"id": "LAD-A04", "name": "High Ridge Relay Station", "lat": 34.35, "lon": 76.85, "role": "TACTICAL_NODE"},
            {"id": "LAD-A05", "name": "Eastern Plateau Terminal", "lat": 34.15, "lon": 77.58, "role": "MAIN_HUB"},
        ]
    },
    "REGION_B": {
        "region_id": "SIKKIM",
        "name": "Sikkim / Eastern Himalayas",
        "corridor": "Siliguri - Sevoke - Singtam - Gangtok Public Corridor (NH-10)",
        "center_lat": 27.3389,
        "center_lon": 88.6065,
        "bbox": [26.7, 88.3, 27.5, 88.8],
        "terrain_type": "STEEP_FORESTED_MOUNTAIN",
        "base_terrain_difficulty": 0.75,
        "default_elevation_m": 1650.0,
        "node_prefix": "SIK",
        "reference_points": [
            {"id": "SIK-B01", "name": "Foothill Logistics Junction", "lat": 26.72, "lon": 88.42, "role": "REGIONAL_DEPOT"},
            {"id": "SIK-B02", "name": "Gorge Entry Transit Center", "lat": 26.88, "lon": 88.48, "role": "TRANSIT_HUB"},
            {"id": "SIK-B03", "name": "Mid-Elevation River Relay", "lat": 27.15, "lon": 88.50, "role": "FORWARD_DEPOT"},
            {"id": "SIK-B04", "name": "Eastern Valley Sector Node", "lat": 27.28, "lon": 88.58, "role": "TACTICAL_NODE"},
            {"id": "SIK-B05", "name": "High Ridge Terminal", "lat": 27.35, "lon": 88.62, "role": "MAIN_HUB"},
        ]
    },
    "REGION_C": {
        "region_id": "RAJASTHAN",
        "name": "Rajasthan / Western Desert",
        "corridor": "Jodhpur - Pokhran - Jaisalmer - Barmer Public Corridor",
        "center_lat": 26.9157,
        "center_lon": 70.9083,
        "bbox": [25.7, 70.8, 27.2, 73.1],
        "terrain_type": "ARID_DESERT_PLAINS",
        "base_terrain_difficulty": 0.35,
        "default_elevation_m": 240.0,
        "node_prefix": "RAJ",
        "reference_points": [
            {"id": "RAJ-C01", "name": "Eastern Sector Supply Terminal", "lat": 26.28, "lon": 73.02, "role": "REGIONAL_DEPOT"},
            {"id": "RAJ-C02", "name": "Central Arid Junction Hub", "lat": 26.92, "lon": 71.91, "role": "TRANSIT_HUB"},
            {"id": "RAJ-C03", "name": "Western Dunes Forward Post", "lat": 26.91, "lon": 70.91, "role": "FORWARD_DEPOT"},
            {"id": "RAJ-C04", "name": "Southern Desert Corridor Relay", "lat": 25.75, "lon": 71.40, "role": "TACTICAL_NODE"},
            {"id": "RAJ-C05", "name": "Southwestern Logistics Point", "lat": 26.30, "lon": 71.10, "role": "MAIN_HUB"},
        ]
    }
}

# Ensure all directories exist
for directory in [
    DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, SYNTHETIC_DATA_DIR,
    TRAINING_DATA_DIR, METADATA_DATA_DIR, RAW_WEATHER_DIR,
    RAW_ELEVATION_DIR, RAW_ROADS_DIR
]:
    os.makedirs(directory, exist_ok=True)
