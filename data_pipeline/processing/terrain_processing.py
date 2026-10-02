"""
Terrain Processing Module.
Calculates standardized terrain difficulty scores, classification, and elevation characteristics
from Copernicus DEM 90m observations.
"""

import os
import logging
import numpy as np
import pandas as pd
from data_pipeline.config import PROCESSED_DATA_DIR, REGIONS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def process_terrain_features(raw_elevation_df: pd.DataFrame) -> pd.DataFrame:
    """
    Derive terrain difficulty and environmental features from raw DEM points.
    Terrain difficulty calculation:
      - Elevation component: normalized altitude above 1000m (up to 5000m)
      - Slope component: normalized gradient slope degrees (0 to 35 deg)
      - Local ruggedness: standard deviation of local elevations
    """
    df = raw_elevation_df.copy()
    
    # 1. Elevation normalization (0 to 1 scale)
    elev_norm = np.clip((df["elevation_m"] - 200.0) / 4500.0, 0.0, 1.0)
    
    # 2. Slope normalization (0 to 1 scale, 30 degrees considered severe mountain incline)
    slope_norm = np.clip(df["slope_degree"] / 30.0, 0.0, 1.0)
    
    # 3. Ruggedness normalization (local variance)
    rugged_norm = np.clip(df["elevation_std_local_m"] / 150.0, 0.0, 1.0)
    
    # Composite Terrain Difficulty Index (0.10 to 0.99)
    difficulty = 0.40 * elev_norm + 0.40 * slope_norm + 0.20 * rugged_norm
    
    # Regional baseline adjustment
    for reg_key, reg_info in REGIONS.items():
        reg_id = reg_info["region_id"]
        mask = df["region"] == reg_id
        if reg_id == "LADAKH":
            df.loc[mask, "terrain_type"] = "HIGH_ALTITUDE_MOUNTAINOUS"
            # High altitude thin air & rugged passes
            df.loc[mask, "terrain_difficulty"] = np.clip(difficulty[mask] * 0.8 + 0.25, 0.60, 0.98)
        elif reg_id == "SIKKIM":
            df.loc[mask, "terrain_type"] = "STEEP_FORESTED_MOUNTAIN"
            # Steep slopes and landslide prone gorges
            df.loc[mask, "terrain_difficulty"] = np.clip(difficulty[mask] * 0.8 + 0.20, 0.50, 0.95)
        else: # RAJASTHAN
            df.loc[mask, "terrain_type"] = "ARID_DESERT_PLAINS"
            df.loc[mask, "terrain_difficulty"] = np.clip(difficulty[mask] * 0.5 + 0.15, 0.15, 0.45)
            
    df["terrain_difficulty"] = df["terrain_difficulty"].round(3)
    
    out_csv = os.path.join(PROCESSED_DATA_DIR, "terrain_features.csv")
    df.to_csv(out_csv, index=False)
    logger.info(f"Saved processed terrain features ({len(df)} nodes) to {out_csv}")
    return df

if __name__ == "__main__":
    from data_pipeline.acquisition.elevation import acquire_regional_elevation
    raw_elev = acquire_regional_elevation()
    process_terrain_features(raw_elev)
