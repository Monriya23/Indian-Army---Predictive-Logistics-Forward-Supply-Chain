"""
Road Network Processing Module.
Applies graph topological analysis using NetworkX to derive road connectivity,
alternative paths, route accessibility, normal travel time, and baseline reliability.
"""

import os
import logging
import networkx as nx
import numpy as np
import pandas as pd
from data_pipeline.config import PROCESSED_DATA_DIR, REGIONS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def process_road_network_features(raw_roads_df: pd.DataFrame, terrain_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute graph topological properties and route characteristics.
    """
    df = raw_roads_df.copy()
    
    # Merge terrain difficulties
    terrain_map = dict(zip(terrain_df["node_id"], terrain_df["terrain_difficulty"]))
    
    df["source_terrain_diff"] = df["source_node"].map(terrain_map).fillna(0.5)
    df["dest_terrain_diff"] = df["destination_node"].map(terrain_map).fillna(0.5)
    df["terrain_difficulty"] = ((df["source_terrain_diff"] + df["dest_terrain_diff"]) / 2.0).round(3)
    
    # Build NetworkX graphs per region to compute topology metrics
    processed_rows = []
    
    for reg_key, reg_info in REGIONS.items():
        reg_id = reg_info["region_id"]
        reg_df = df[df["region"] == reg_id].copy()
        
        G = nx.Graph()
        for _, r in reg_df.iterrows():
            G.add_edge(r["source_node"], r["destination_node"], weight=r["road_distance_km"])
            
        density = nx.density(G)
        
        for _, r in reg_df.iterrows():
            src = r["source_node"]
            dst = r["destination_node"]
            
            # 1. Road connectivity (degree of source + destination in regional graph)
            src_deg = G.degree(src) if src in G else 1
            dst_deg = G.degree(dst) if dst in G else 1
            connectivity = round((src_deg + dst_deg) / 2.0, 1)
            
            # 2. Alternative paths count (simple paths between src and dst)
            try:
                paths = list(nx.all_simple_paths(G, source=src, target=dst, cutoff=4))
                alt_count = len(paths)
            except Exception:
                alt_count = 1
                
            # 3. Base speed estimate based on region terrain and road class (km/h)
            if reg_id == "LADAKH":
                base_speed = 32.0 if r["road_classification"] == "NATIONAL_HIGHWAY_PRIMARY" else 22.0
                weather_exp = 0.85
            elif reg_id == "SIKKIM":
                base_speed = 38.0 if r["road_classification"] == "NATIONAL_HIGHWAY_PRIMARY" else 26.0
                weather_exp = 0.75
            else: # RAJASTHAN
                base_speed = 68.0 if r["road_classification"] == "NATIONAL_HIGHWAY_PRIMARY" else 48.0
                weather_exp = 0.35
                
            # Elevation gradient penalty on speed
            grad_penalty = 1.0 + (r["elevation_change_m"] / 2000.0) * 0.35
            effective_speed = base_speed / grad_penalty
            normal_travel_time_hr = round(r["road_distance_km"] / effective_speed, 2)
            
            # 4. Route accessibility score (0.0 to 1.0)
            # Higher with more lanes, asphalt surface, lower terrain difficulty
            surface_score = 0.90 if "ASPHALT" in r["surface_type"] else 0.65
            lane_score = 0.95 if r["lanes"] >= 2 else 0.70
            diff_score = 1.0 - (r["terrain_difficulty"] * 0.5)
            accessibility = round(0.4 * surface_score + 0.3 * lane_score + 0.3 * diff_score, 3)
            
            # 5. Route reliability (0.0 to 1.0)
            # Higher if multiple alternative paths, lower terrain difficulty, better surface
            redundancy_bonus = min(0.15, (alt_count - 1) * 0.05)
            reliability = round(np.clip(accessibility * 0.85 + redundancy_bonus, 0.20, 0.98), 3)
            
            processed_rows.append({
                "route_id": r["route_id"],
                "region": reg_id,
                "source_node": src,
                "destination_node": dst,
                "distance_km": r["road_distance_km"],
                "elevation_change_m": r["elevation_change_m"],
                "terrain_difficulty": r["terrain_difficulty"],
                "road_classification": r["road_classification"],
                "lanes": r["lanes"],
                "surface_type": r["surface_type"],
                "road_connectivity": connectivity,
                "alternative_path_count": alt_count,
                "network_density": round(density, 3),
                "normal_travel_time_hr": normal_travel_time_hr,
                "weather_exposure": weather_exp,
                "route_accessibility": accessibility,
                "route_reliability": reliability,
                "route_status": "OPEN",
                "data_source": r["data_source"]
            })
            
    out_df = pd.DataFrame(processed_rows)
    out_csv = os.path.join(PROCESSED_DATA_DIR, "road_network_features.csv")
    out_df.to_csv(out_csv, index=False)
    logger.info(f"Saved processed road network features ({len(out_df)} routes) to {out_csv}")
    return out_df

if __name__ == "__main__":
    from data_pipeline.acquisition.elevation import acquire_regional_elevation
    from data_pipeline.acquisition.roads import acquire_regional_road_segments
    from data_pipeline.processing.terrain_processing import process_terrain_features
    elev_raw = acquire_regional_elevation()
    terrain_df = process_terrain_features(elev_raw)
    roads_raw = acquire_regional_road_segments(elev_raw)
    process_road_network_features(roads_raw, terrain_df)
