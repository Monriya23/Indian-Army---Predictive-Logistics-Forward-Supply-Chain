"""
Elevation and Terrain Data Acquisition Module.
Retrieves real elevation from Copernicus DEM (90m) and SRTM datasets via Copernicus/Open-Meteo elevation endpoints,
calculates local terrain gradients, variance, and approximate slope.
"""

import os
import json
import logging
import math
import requests
import pandas as pd
from data_pipeline.config import RAW_ELEVATION_DIR, REGIONS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

OPEN_METEO_ELEVATION_URL = "https://api.open-meteo.com/v1/elevation"

def fetch_point_elevation(lat: float, lon: float) -> float:
    """Fetch accurate elevation for a single point from Copernicus DEM (90m)."""
    try:
        params = {"latitude": lat, "longitude": lon}
        r = requests.get(OPEN_METEO_ELEVATION_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        elevations = data.get("elevation", [])
        if elevations and len(elevations) > 0:
            return float(elevations[0])
    except Exception as e:
        logger.warning(f"Error querying Copernicus DEM for ({lat}, {lon}): {e}")
    return None

def fetch_batch_elevation_with_terrain_metrics(points: list) -> pd.DataFrame:
    """
    Fetch elevations for multiple points along with local terrain gradients
    (sampling 4 cardinal offsets ~1km away to derive real slope & elevation variation).
    """
    lats = []
    lons = []
    point_metadata = []
    
    # 1 degree lat is approx 111 km -> 0.01 deg is approx 1.1 km
    OFFSET = 0.01
    
    for pt in points:
        p_id = pt["id"]
        c_lat, c_lon = pt["lat"], pt["lon"]
        region = pt["region"]
        name = pt.get("name", p_id)
        role = pt.get("role", "STANDARD_NODE")
        
        # Add center point and 4 cardinal offsets for local slope/variance calculation
        lats.extend([c_lat, c_lat + OFFSET, c_lat - OFFSET, c_lat, c_lat])
        lons.extend([c_lon, c_lon, c_lon, c_lon + OFFSET, c_lon - OFFSET])
        
        point_metadata.append({
            "id": p_id,
            "name": name,
            "region": region,
            "role": role,
            "center_lat": c_lat,
            "center_lon": c_lon,
        })
        
    try:
        params = {
            "latitude": ",".join(f"{x:.4f}" for x in lats),
            "longitude": ",".join(f"{y:.4f}" for y in lons)
        }
        r = requests.get(OPEN_METEO_ELEVATION_URL, params=params, timeout=20)
        r.raise_for_status()
        elev_list = r.json().get("elevation", [])
    except Exception as e:
        logger.error(f"Failed to fetch batch elevation: {e}")
        elev_list = [None] * len(lats)
        
    results = []
    for i, meta in enumerate(point_metadata):
        idx = i * 5
        center_elev = elev_list[idx] if idx < len(elev_list) else None
        north_elev = elev_list[idx+1] if idx+1 < len(elev_list) else center_elev
        south_elev = elev_list[idx+2] if idx+2 < len(elev_list) else center_elev
        east_elev = elev_list[idx+3] if idx+3 < len(elev_list) else center_elev
        west_elev = elev_list[idx+4] if idx+4 < len(elev_list) else center_elev
        
        # Calculate local elevation variance and slope in degrees
        elev_samples = [e for e in [center_elev, north_elev, south_elev, east_elev, west_elev] if e is not None]
        if elev_samples:
            avg_elev = sum(elev_samples) / len(elev_samples)
            elev_var = (sum((e - avg_elev) ** 2 for e in elev_samples) / len(elev_samples)) ** 0.5
            
            # dz/dx and dz/dy over approx 2.2km (2 * 1110m)
            dist_m = 2220.0
            dz_dy = abs((north_elev or center_elev) - (south_elev or center_elev))
            dz_dx = abs((east_elev or center_elev) - (west_elev or center_elev))
            max_gradient = max(dz_dy, dz_dx) / dist_m
            slope_deg = math.degrees(math.atan(max_gradient))
        else:
            avg_elev = center_elev or 0.0
            elev_var = 0.0
            slope_deg = 0.0

        results.append({
            "node_id": meta["id"],
            "name": meta["name"],
            "region": meta["region"],
            "role": meta["role"],
            "latitude": meta["center_lat"],
            "longitude": meta["center_lon"],
            "elevation_m": round(center_elev, 1) if center_elev is not None else None,
            "elevation_std_local_m": round(elev_var, 2),
            "slope_degree": round(slope_deg, 2),
            "elevation_source": "Copernicus DEM (GLO-90) via Open-Meteo Elevation API",
        })
        
    return pd.DataFrame(results)

def acquire_regional_elevation(force_refresh: bool = False) -> pd.DataFrame:
    """Acquire elevation for all predefined regional reference points."""
    raw_csv = os.path.join(RAW_ELEVATION_DIR, "copernicus_dem_raw.csv")
    
    if os.path.exists(raw_csv) and not force_refresh:
        logger.info(f"Loading cached elevation data from {raw_csv}")
        return pd.read_csv(raw_csv)
        
    all_points = []
    for reg_key, reg_info in REGIONS.items():
        for pt in reg_info["reference_points"]:
            pt_copy = pt.copy()
            pt_copy["region"] = reg_info["region_id"]
            all_points.append(pt_copy)
            
    df_elev = fetch_batch_elevation_with_terrain_metrics(all_points)
    df_elev.to_csv(raw_csv, index=False)
    logger.info(f"Saved raw elevation & terrain slope data ({len(df_elev)} nodes) to {raw_csv}")
    return df_elev

if __name__ == "__main__":
    acquire_regional_elevation(force_refresh=True)
