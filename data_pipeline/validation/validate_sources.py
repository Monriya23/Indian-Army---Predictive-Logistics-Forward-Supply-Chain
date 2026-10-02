"""
Data Sources Validation Module.
Validates raw public meteorological (node-level), elevation, and road data integrity.
"""

import os
import logging
import pandas as pd
from data_pipeline.config import RAW_WEATHER_DIR, RAW_ELEVATION_DIR, RAW_ROADS_DIR, REGIONS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def validate_raw_sources() -> dict:
    """
    Validate all raw acquired files across all 15 nodes and regional infrastructures.
    """
    results = {}
    
    # 1. Node-Level Weather Validation
    weather_ok = True
    weather_issues = []
    node_count = 0
    
    for reg_key, reg_info in REGIONS.items():
        for pt in reg_info["reference_points"]:
            node_id = pt["id"]
            node_count += 1
            csv_file = os.path.join(RAW_WEATHER_DIR, f"weather_raw_{node_id.lower().replace('-', '_')}.csv")
            
            if not os.path.exists(csv_file):
                weather_ok = False
                weather_issues.append(f"Missing raw weather CSV for node {node_id}")
                continue
                
            df_w = pd.read_csv(csv_file)
            if len(df_w) < 1000:
                weather_ok = False
                weather_issues.append(f"Weather rows for node {node_id} is {len(df_w)} (expected 1096)")
                
            if df_w["temperature_mean_c"].isnull().sum() > 0:
                weather_issues.append(f"Nulls in temperature_mean_c for {node_id}: {df_w['temperature_mean_c'].isnull().sum()}")
                
    results["node_weather_sources"] = {
        "status": "PASS" if weather_ok and not weather_issues else "WARNING" if weather_ok else "FAIL",
        "nodes_validated": node_count,
        "issues": weather_issues
    }
    
    # 2. Elevation Validation
    elev_ok = True
    elev_issues = []
    elev_csv = os.path.join(RAW_ELEVATION_DIR, "copernicus_dem_raw.csv")
    if not os.path.exists(elev_csv):
        elev_ok = False
        elev_issues.append("Missing copernicus_dem_raw.csv")
    else:
        df_e = pd.read_csv(elev_csv)
        if len(df_e) != 15:
            elev_ok = False
            elev_issues.append(f"Expected 15 elevation points, found {len(df_e)}")
        if df_e["elevation_m"].isnull().sum() > 0:
            elev_ok = False
            elev_issues.append("Null values found in elevation_m")
            
    results["elevation_sources"] = {
        "status": "PASS" if elev_ok else "FAIL",
        "issues": elev_issues
    }
    
    # 3. Roads Validation
    roads_ok = True
    roads_issues = []
    roads_csv = os.path.join(RAW_ROADS_DIR, "osm_public_roads_raw.csv")
    if not os.path.exists(roads_csv):
        roads_ok = False
        roads_issues.append("Missing osm_public_roads_raw.csv")
    else:
        df_r = pd.read_csv(roads_csv)
        if len(df_r) == 0:
            roads_ok = False
            roads_issues.append("Road segments table is empty")
        if (df_r["road_distance_km"] <= 0).any():
            roads_ok = False
            roads_issues.append("Found non-positive road distance values")
            
    results["road_sources"] = {
        "status": "PASS" if roads_ok else "FAIL",
        "issues": roads_issues
    }
    
    return results

if __name__ == "__main__":
    res = validate_raw_sources()
    print("Source Validation Results:", res)
