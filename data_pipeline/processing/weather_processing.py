"""
Node-Level Weather Processing & Feature Engineering Module.
Harmonizes real meteorological inputs, calculates elevation-adjusted temperature,
processes ERA5 snowfall & synthetic proxy, and computes strictly normalized weather severity.
"""

import os
import logging
import numpy as np
import pandas as pd
from data_pipeline.config import PROCESSED_DATA_DIR, REGIONS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Standard tropospheric lapse rate (deg C per meter)
STANDARD_LAPSE_RATE = 0.0065

def compute_weather_severity_index(
    temperature_c: pd.Series,
    precipitation_mm: pd.Series,
    snowfall_cm: pd.Series,
    wind_speed_kmh: pd.Series
) -> pd.Series:
    """
    Compute domain-grounded Weather Severity Index with strictly normalized weights (sum = 1.00).
    
    Weights:
      - Cold Penalty (weight = 0.25): Sub-zero freeze hazard (0°C to -25°C)
      - Heat Penalty (weight = 0.20): Extreme heat stress (38°C to 50°C)
      - Rain Penalty (weight = 0.25): Flash flood/landslide moisture (0mm to 50mm)
      - Snow Penalty (weight = 0.20): Fresh snow accumulation (0cm to 20cm)
      - Wind Penalty (weight = 0.10): Gale force winds (25 km/h to 65 km/h)
      Total Sum of Weights = 0.25 + 0.20 + 0.25 + 0.20 + 0.10 = 1.00
    """
    cold_penalty = np.clip((-temperature_c) / 25.0, 0.0, 1.0)
    heat_penalty = np.clip((temperature_c - 38.0) / 12.0, 0.0, 1.0)
    rain_penalty = np.clip(precipitation_mm / 50.0, 0.0, 1.0)
    snow_penalty = np.clip(snowfall_cm / 20.0, 0.0, 1.0)
    wind_penalty = np.clip((wind_speed_kmh - 25.0) / 40.0, 0.0, 1.0)
    
    ws = (0.25 * cold_penalty +
          0.20 * heat_penalty +
          0.25 * rain_penalty +
          0.20 * snow_penalty +
          0.10 * wind_penalty)
          
    return np.clip(np.round(ws, 3), 0.0, 1.0)

def process_node_weather_data(raw_weather_dict: dict, terrain_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Process raw node-level weather data into a unified, feature-engineered dataset.
    """
    if terrain_df is None:
        terrain_file = os.path.join(PROCESSED_DATA_DIR, "terrain_features.csv")
        if os.path.exists(terrain_file):
            terrain_df = pd.read_csv(terrain_file)
        else:
            terrain_df = pd.DataFrame(columns=["node_id", "elevation_m"])
            
    # Map node elevation from Copernicus DEM
    node_elev_map = dict(zip(terrain_df["node_id"], terrain_df["elevation_m"])) if "node_id" in terrain_df.columns and "elevation_m" in terrain_df.columns else {}

    
    # Regional baseline reference elevations for lapse-rate adjustment
    ref_elevations = {
        "LADAKH": 3200.0,
        "SIKKIM": 1000.0,
        "RAJASTHAN": 250.0
    }
    
    processed_dfs = []
    
    for node_id, df_raw in raw_weather_dict.items():
        df = df_raw.copy()
        
        # Ensure proper sorting by date
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        
        # Missing value handling (forward-fill then backward-fill)
        for col in ["temperature_mean_c", "temperature_max_c", "temperature_min_c", "precipitation_mm", "wind_speed_ms", "relative_humidity_pct"]:
            if col in df.columns:
                df[col] = df[col].ffill().bfill()
                
        # 1. Observed Temperature
        df["temperature_c"] = df["temperature_mean_c"].round(2)
        
        # 2. Elevation Lapse-Rate Adjusted Temperature (Derived Variable)
        reg_id = df["region"].iloc[0]
        node_elev = node_elev_map.get(node_id, 1000.0)
        ref_elev = ref_elevations.get(reg_id, 1000.0)
        elev_delta = node_elev - ref_elev
        lapse_correction = STANDARD_LAPSE_RATE * elev_delta
        df["temperature_elevation_adjusted_c"] = (df["temperature_c"] - lapse_correction).round(2)
        
        # 3. Wind speed in km/h
        df["wind_speed_kmh"] = (df["wind_speed_ms"] * 3.6).round(2)
        
        # 4. Snowfall: ERA5-Land observed reanalysis vs Synthetic Proxy
        if "snowfall_era5_cm" in df.columns and df["snowfall_era5_cm"].notnull().any():
            df["snowfall_era5_cm"] = df["snowfall_era5_cm"].fillna(0.0).round(2)
        else:
            df["snowfall_era5_cm"] = 0.0
            
        # Synthetic snowfall proxy for comparison/fallback
        df["snowfall_proxy_cm"] = np.where(
            df["temperature_elevation_adjusted_c"] <= 0.5,
            np.round(df["precipitation_mm"] * 1.0, 2),
            0.0
        )
        
        # Primary operational snowfall field (prefers ERA5-Land reanalysis when available)
        df["snowfall_cm"] = np.where(
            df["snowfall_era5_cm"] > 0,
            df["snowfall_era5_cm"],
            df["snowfall_proxy_cm"]
        )
        
        # 5. Rolling accumulations per node (past observations only)
        df["rainfall_3d"] = df["precipitation_mm"].rolling(window=3, min_periods=1).sum().round(2)
        df["rainfall_7d"] = df["precipitation_mm"].rolling(window=7, min_periods=1).sum().round(2)
        df["temperature_7d_avg"] = df["temperature_elevation_adjusted_c"].rolling(window=7, min_periods=1).mean().round(2)
        
        # 6. Strictly Normalized Weather Severity Index
        df["weather_severity"] = compute_weather_severity_index(
            temperature_c=df["temperature_elevation_adjusted_c"],
            precipitation_mm=df["precipitation_mm"],
            snowfall_cm=df["snowfall_cm"],
            wind_speed_kmh=df["wind_speed_kmh"]
        )
        
        # 7. Extreme Weather Indicator (Binary 0/1)
        df["extreme_weather_indicator"] = (
            (df["weather_severity"] >= 0.45) |
            (df["precipitation_mm"] >= 40.0) |
            (df["temperature_elevation_adjusted_c"] <= -15.0) |
            (df["temperature_elevation_adjusted_c"] >= 45.0) |
            (df["snowfall_cm"] >= 15.0) |
            (df["wind_speed_kmh"] >= 55.0)
        ).astype(int)
        
        # Convert date back to string ISO
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")
        processed_dfs.append(df)
        
    final_df = pd.concat(processed_dfs, ignore_index=True)
    out_csv = os.path.join(PROCESSED_DATA_DIR, "weather_processed.csv")
    final_df.to_csv(out_csv, index=False)
    logger.info(f"Saved node-level processed weather ({len(final_df)} rows across {len(processed_dfs)} nodes) to {out_csv}")
    return final_df

# Compatibility alias
process_weather_data = process_node_weather_data


if __name__ == "__main__":
    from data_pipeline.config import REGIONS
    from data_pipeline.acquisition.weather import acquire_node_level_weather
    from data_pipeline.acquisition.elevation import acquire_regional_elevation
    from data_pipeline.processing.terrain_processing import process_terrain_features
    
    all_points = []
    for reg_key, reg_info in REGIONS.items():
        for pt in reg_info["reference_points"]:
            pt_copy = pt.copy()
            pt_copy["region"] = reg_info["region_id"]
            all_points.append(pt_copy)
            
    elev_raw = acquire_regional_elevation()
    terrain_df = process_terrain_features(elev_raw)
    raw_dict = acquire_node_level_weather(all_points)
    process_node_weather_data(raw_dict, terrain_df)
