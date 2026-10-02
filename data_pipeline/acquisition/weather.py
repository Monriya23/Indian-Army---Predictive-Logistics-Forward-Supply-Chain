"""
Node-Level Weather Data Acquisition Module.
Retrieves real-world daily meteorological observations from NASA POWER API
and ECMWF ERA5-Land Reanalysis for each of the 15 specific node coordinates.
"""

import os
import json
import logging
from datetime import datetime
import requests
import pandas as pd
from data_pipeline.config import RAW_WEATHER_DIR, REGIONS, START_DATE, END_DATE

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

NASA_POWER_BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
OPEN_METEO_ERA5_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

def fetch_nasa_power_node_weather(lat: float, lon: float, start_date: str, end_date: str, node_id: str) -> dict:
    """
    Fetch real daily meteorological observations from NASA POWER API for a specific node coordinate.
    Parameters fetched:
      - T2M: Temperature at 2 Meters (C)
      - T2M_MAX: Maximum Temperature at 2 Meters (C)
      - T2M_MIN: Minimum Temperature at 2 Meters (C)
      - PRECTOTCORR: Precipitation Corrected (mm/day)
      - WS10M: Wind Speed at 10 Meters (m/s)
      - RH2M: Relative Humidity at 2 Meters (%)
    """
    start_str = start_date.replace("-", "")
    end_str = end_date.replace("-", "")
    
    params = {
        "parameters": "T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,WS10M,RH2M",
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": start_str,
        "end": end_str,
        "format": "JSON"
    }
    
    headers = {"User-Agent": "SIH2026-Predictive-Logistics-Research/1.0"}
    
    logger.info(f"Fetching NASA POWER weather for node {node_id} (lat={lat:.4f}, lon={lon:.4f}) from {start_date} to {end_date}...")
    try:
        response = requests.get(NASA_POWER_BASE_URL, params=params, headers=headers, timeout=25)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.warning(f"Failed to fetch live NASA POWER data for node {node_id}: {e}")
        return None

def fetch_era5_land_node_snowfall(lat: float, lon: float, start_date: str, end_date: str, node_id: str) -> dict:
    """
    Fetch ECMWF ERA5-Land historical daily snowfall reanalysis for a specific node coordinate.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "snowfall_sum",
        "timezone": "auto"
    }
    headers = {"User-Agent": "SIH2026-Predictive-Logistics-Research/1.0"}
    try:
        r = requests.get(OPEN_METEO_ERA5_ARCHIVE_URL, params=params, headers=headers, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning(f"ERA5-Land snowfall fetch failed for {node_id}: {e}")
        return None

def acquire_node_level_weather(nodes_metadata: list = None, force_refresh: bool = False) -> dict:
    """
    Acquire daily weather for each individual logistics node (15 nodes total).
    Saves raw responses to data/raw/weather/ and returns dict of node dataframes.
    """
    if nodes_metadata is None:
        nodes_metadata = []
        for reg_key, reg_info in REGIONS.items():
            for pt in reg_info["reference_points"]:
                pt_copy = pt.copy()
                pt_copy["region"] = reg_info["region_id"]
                nodes_metadata.append(pt_copy)

    results = {}
    
    for node in nodes_metadata:
        node_id = node["id"]
        reg_id = node["region"]
        lat = node["lat"]
        lon = node["lon"]
        
        raw_json_file = os.path.join(RAW_WEATHER_DIR, f"nasa_power_raw_{node_id.lower().replace('-', '_')}.json")
        era5_json_file = os.path.join(RAW_WEATHER_DIR, f"era5_land_raw_{node_id.lower().replace('-', '_')}.json")
        csv_raw_file = os.path.join(RAW_WEATHER_DIR, f"weather_raw_{node_id.lower().replace('-', '_')}.csv")
        
        # 1. Fetch / Load NASA POWER data
        raw_json = None
        if os.path.exists(raw_json_file) and not force_refresh:
            logger.info(f"Loading cached raw NASA weather for {node_id} from {raw_json_file}")
            with open(raw_json_file, "r") as f:
                raw_json = json.load(f)
        else:
            raw_json = fetch_nasa_power_node_weather(lat, lon, START_DATE, END_DATE, node_id)
            if raw_json:
                with open(raw_json_file, "w") as f:
                    json.dump(raw_json, f, indent=2)

        # 2. Fetch / Load ERA5-Land Snowfall data
        era5_json = None
        if os.path.exists(era5_json_file) and not force_refresh:
            with open(era5_json_file, "r") as f:
                era5_json = json.load(f)
        else:
            era5_json = fetch_era5_land_node_snowfall(lat, lon, START_DATE, END_DATE, node_id)
            if era5_json:
                with open(era5_json_file, "w") as f:
                    json.dump(era5_json, f, indent=2)
                    
        # Parse ERA5 snowfall map
        era5_snow_map = {}
        if era5_json and "daily" in era5_json and "time" in era5_json["daily"]:
            times = era5_json["daily"]["time"]
            snows = era5_json["daily"].get("snowfall_sum", [])
            for t_str, s_val in zip(times, snows):
                era5_snow_map[t_str] = round(float(s_val), 2) if s_val is not None else 0.0

        if raw_json and "properties" in raw_json and "parameter" in raw_json["properties"]:
            params = raw_json["properties"]["parameter"]
            dates = sorted(list(params["T2M"].keys()))
            
            records = []
            for d in dates:
                dt_obj = datetime.strptime(d, "%Y%m%d")
                date_iso = dt_obj.strftime("%Y-%m-%d")
                
                t2m = params.get("T2M", {}).get(d, None)
                t2m_max = params.get("T2M_MAX", {}).get(d, None)
                t2m_min = params.get("T2M_MIN", {}).get(d, None)
                precip = params.get("PRECTOTCORR", {}).get(d, None)
                wind = params.get("WS10M", {}).get(d, None)
                humidity = params.get("RH2M", {}).get(d, None)
                
                # Check for NASA missing value indicator (-999.0)
                records.append({
                    "date": date_iso,
                    "node_id": node_id,
                    "region": reg_id,
                    "latitude": lat,
                    "longitude": lon,
                    "temperature_mean_c": None if t2m == -999.0 else t2m,
                    "temperature_max_c": None if t2m_max == -999.0 else t2m_max,
                    "temperature_min_c": None if t2m_min == -999.0 else t2m_min,
                    "precipitation_mm": None if precip == -999.0 else max(0.0, float(precip)),
                    "wind_speed_ms": None if wind == -999.0 else wind,
                    "relative_humidity_pct": None if humidity == -999.0 else humidity,
                    "snowfall_era5_cm": era5_snow_map.get(date_iso, None),
                    "nasa_power_source": "NASA POWER (CERES/MERRA-2) 0.5x0.5 deg",
                    "era5_source": "ECMWF ERA5-Land Reanalysis 9km",
                    "retrieval_timestamp": datetime.now().isoformat()
                })
            
            df = pd.DataFrame(records)
            df.to_csv(csv_raw_file, index=False)
            logger.info(f"Saved raw weather for {node_id} ({len(df)} days) to {csv_raw_file}")
            results[node_id] = df
        else:
            logger.error(f"Could not retrieve or parse weather for node {node_id}")

    return results

if __name__ == "__main__":
    from data_pipeline.config import REGIONS
    all_points = []
    for reg_key, reg_info in REGIONS.items():
        for pt in reg_info["reference_points"]:
            pt_copy = pt.copy()
            pt_copy["region"] = reg_info["region_id"]
            all_points.append(pt_copy)
    acquire_node_level_weather(all_points, force_refresh=True)

# Compatibility alias
acquire_regional_weather = acquire_node_level_weather
