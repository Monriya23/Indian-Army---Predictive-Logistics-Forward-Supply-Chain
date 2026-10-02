"""
Synthetic Logistics Nodes Module.
Generates fictional logistics node representations grounded in real Copernicus DEM elevation,
terrain classification, and road network accessibility.
"""

import os
import logging
import pandas as pd
from data_pipeline.config import SYNTHETIC_DATA_DIR, REGIONS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def generate_synthetic_nodes(terrain_df: pd.DataFrame, road_df: pd.DataFrame) -> pd.DataFrame:
    """
    Construct synthetic logistics nodes dataset.
    Storage capacity and criticality are aligned with node role and terrain accessibility.
    """
    # Calculate average route accessibility per node from road_df
    src_acc = road_df.groupby("source_node")["route_accessibility"].mean()
    dst_acc = road_df.groupby("destination_node")["route_accessibility"].mean()
    node_acc = (src_acc.add(dst_acc, fill_value=0.7) / 2.0).to_dict()
    
    nodes = []
    
    for _, r in terrain_df.iterrows():
        n_id = r["node_id"]
        reg_id = r["region"]
        role = r["role"]
        elev = r["elevation_m"]
        terrain_type = r["terrain_type"]
        terrain_diff = r["terrain_difficulty"]
        
        # Storage capacities (kg) based on node hierarchy
        if role == "MAIN_HUB":
            storage_cap = 250000.0  # 250 tons
            crit_level = 5  # Highest strategic importance
        elif role == "REGIONAL_DEPOT":
            storage_cap = 180000.0  # 180 tons
            crit_level = 4
        elif role == "TRANSIT_HUB":
            storage_cap = 100000.0  # 100 tons
            crit_level = 3
        elif role == "FORWARD_DEPOT":
            storage_cap = 60000.0   # 60 tons
            crit_level = 4
        else: # TACTICAL_NODE
            storage_cap = 35000.0   # 35 tons
            crit_level = 3
            
        acc_score = round(node_acc.get(n_id, 0.75), 3)
        
        nodes.append({
            "node_id": n_id,
            "region": reg_id,
            "name": r["name"],
            "latitude": r["latitude"],
            "longitude": r["longitude"],
            "elevation_m": elev,
            "terrain_type": terrain_type,
            "terrain_difficulty": terrain_diff,
            "road_accessibility": acc_score,
            "storage_capacity_kg": storage_cap,
            "criticality_level": crit_level,
            "node_role": role,
            "is_fictional": True,
            "elevation_source": "Copernicus DEM (90m)"
        })
        
    df_nodes = pd.DataFrame(nodes)
    out_csv = os.path.join(SYNTHETIC_DATA_DIR, "nodes.csv")
    df_nodes.to_csv(out_csv, index=False)
    logger.info(f"Saved synthetic nodes dataset ({len(df_nodes)} nodes) to {out_csv}")
    return df_nodes

if __name__ == "__main__":
    from data_pipeline.acquisition.elevation import acquire_regional_elevation
    from data_pipeline.acquisition.roads import acquire_regional_road_segments
    from data_pipeline.processing.terrain_processing import process_terrain_features
    from data_pipeline.processing.road_processing import process_road_network_features
    elev_raw = acquire_regional_elevation()
    terrain_df = process_terrain_features(elev_raw)
    roads_raw = acquire_regional_road_segments(elev_raw)
    roads_df = process_road_network_features(roads_raw, terrain_df)
    generate_synthetic_nodes(terrain_df, roads_df)
