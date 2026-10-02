"""
Synthetic Fleet Generation Module.
Generates abstract, non-sensitive vehicle fleet records with physical payload capacities,
terrain compatibility, operating ranges, and weather resilience factors.
"""

import os
import logging
import pandas as pd
from data_pipeline.config import SYNTHETIC_DATA_DIR, VEHICLE_CLASSES, RANDOM_SEED

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def generate_synthetic_fleet(nodes_df: pd.DataFrame, num_vehicles_per_class: dict = None, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """
    Generate fleet records across LIGHT, MEDIUM, and HEAVY vehicle classes.
    """
    if num_vehicles_per_class is None:
        num_vehicles_per_class = {"LIGHT": 30, "MEDIUM": 30, "HEAVY": 20}
        
    all_nodes = nodes_df["node_id"].tolist()
    fleet = []
    
    for v_class, count in num_vehicles_per_class.items():
        specs = VEHICLE_CLASSES[v_class]
        
        for i in range(1, count + 1):
            v_id = f"VEH-{v_class[0]}-{i:03d}"
            assigned_node = all_nodes[(i - 1) % len(all_nodes)]
            
            # Terrain compatibility rule
            if v_class == "LIGHT":
                terrain_comp = "ALL_TERRAIN_4X4"
                maint_status = "OPERATIONAL" if i % 7 != 0 else "DUE_INSPECTION"
            elif v_class == "MEDIUM":
                terrain_comp = "MOUNTAIN_PAVED_AND_DESERT"
                maint_status = "OPERATIONAL" if i % 8 != 0 else "UNDER_REPAIR" if i % 15 == 0 else "DUE_INSPECTION"
            else: # HEAVY
                terrain_comp = "HIGHWAY_AND_PLAINS_ONLY"
                maint_status = "OPERATIONAL" if i % 6 != 0 else "DUE_INSPECTION"
                
            fleet.append({
                "vehicle_id": v_id,
                "vehicle_class": v_class,
                "capacity_kg": specs["capacity_kg"],
                "speed_factor": specs["speed_factor"],
                "max_slope_degree": specs["max_slope_degree"],
                "operating_range_km": specs["operating_range_km"],
                "weather_resilience": specs["weather_resilience"],
                "terrain_compatibility": terrain_comp,
                "maintenance_status": maint_status,
                "current_node": assigned_node,
                "availability": "AVAILABLE" if maint_status == "OPERATIONAL" else "MAINTENANCE"
            })
            
    df_fleet = pd.DataFrame(fleet)
    out_csv = os.path.join(SYNTHETIC_DATA_DIR, "fleet.csv")
    df_fleet.to_csv(out_csv, index=False)
    logger.info(f"Saved synthetic fleet dataset ({len(df_fleet)} vehicles) to {out_csv}")
    return df_fleet

if __name__ == "__main__":
    from data_pipeline.acquisition.elevation import acquire_regional_elevation
    from data_pipeline.acquisition.roads import acquire_regional_road_segments
    from data_pipeline.processing.terrain_processing import process_terrain_features
    from data_pipeline.processing.road_processing import process_road_network_features
    from data_pipeline.simulation.nodes import generate_synthetic_nodes
    
    elev_raw = acquire_regional_elevation()
    terrain_df = process_terrain_features(elev_raw)
    roads_raw = acquire_regional_road_segments(elev_raw)
    roads_df = process_road_network_features(roads_raw, terrain_df)
    nodes_df = generate_synthetic_nodes(terrain_df, roads_df)
    generate_synthetic_fleet(nodes_df)
