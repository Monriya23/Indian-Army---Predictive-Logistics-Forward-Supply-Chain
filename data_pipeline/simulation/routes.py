"""
Synthetic Transportation Routes Module.
Exports the regional transportation network with physical routing parameters,
weather exposure, baseline travel times, and reliability metrics.
"""

import os
import logging
import pandas as pd
from data_pipeline.config import SYNTHETIC_DATA_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def generate_synthetic_routes(road_features_df: pd.DataFrame) -> pd.DataFrame:
    """
    Format and export synthetic transportation routes for the simulation.
    """
    df = road_features_df.copy()
    
    # Standardize column naming and status
    routes = []
    for _, r in df.iterrows():
        # Condition initial assessment
        if "ASPHALT" in r["surface_type"]:
            cond = "GOOD_SURFACED"
        elif "PAVED" in r["surface_type"]:
            cond = "FAIR_MOUNTAIN_PAVED"
        else:
            cond = "UNPAVED_SANDY_TRACK"
            
        routes.append({
            "route_id": r["route_id"],
            "region": r["region"],
            "source_node": r["source_node"],
            "destination_node": r["destination_node"],
            "distance_km": r["distance_km"],
            "elevation_change_m": r["elevation_change_m"],
            "terrain_difficulty": r["terrain_difficulty"],
            "road_classification": r["road_classification"],
            "road_condition": cond,
            "normal_travel_time_hr": r["normal_travel_time_hr"],
            "weather_exposure": r["weather_exposure"],
            "route_reliability": r["route_reliability"],
            "alternative_route_count": r["alternative_path_count"],
            "route_status": "OPEN",
            "is_bidirectional": True
        })
        
    df_routes = pd.DataFrame(routes)
    out_csv = os.path.join(SYNTHETIC_DATA_DIR, "routes.csv")
    df_routes.to_csv(out_csv, index=False)
    logger.info(f"Saved synthetic routes dataset ({len(df_routes)} routes) to {out_csv}")
    return df_routes

if __name__ == "__main__":
    from data_pipeline.acquisition.elevation import acquire_regional_elevation
    from data_pipeline.acquisition.roads import acquire_regional_road_segments
    from data_pipeline.processing.terrain_processing import process_terrain_features
    from data_pipeline.processing.road_processing import process_road_network_features
    elev_raw = acquire_regional_elevation()
    terrain_df = process_terrain_features(elev_raw)
    roads_raw = acquire_regional_road_segments(elev_raw)
    roads_df = process_road_network_features(roads_raw, terrain_df)
    generate_synthetic_routes(roads_df)
