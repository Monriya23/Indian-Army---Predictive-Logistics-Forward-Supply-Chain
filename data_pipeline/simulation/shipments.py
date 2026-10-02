"""
Synthetic Logistics Shipments Simulation Module.
Generates scheduled and executed shipment records influenced by vehicle payloads,
terrain slope, real route-level weather severity, road conditions, and disruption events.
"""

import os
import logging
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from data_pipeline.config import SYNTHETIC_DATA_DIR, RANDOM_SEED, SUPPLY_CATEGORIES

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def generate_weather_conditioned_shipments(
    nodes_df: pd.DataFrame,
    routes_df: pd.DataFrame,
    fleet_df: pd.DataFrame,
    weather_df: pd.DataFrame,
    disruptions_df: pd.DataFrame,
    seed: int = RANDOM_SEED
) -> pd.DataFrame:
    """
    Simulate daily shipments across the transportation network.
    """
    np.random.seed(seed)
    
    routes_list = routes_df.to_dict("records")
    
    # Pre-index disruptions by (date, affected_route)
    disruption_map = {}
    for _, d in disruptions_df.iterrows():
        disruption_map[(d["date"], d["affected_route"])] = d
        
    # Weather lookup by (date, node_id)
    weather_map = {}
    for _, w in weather_df.iterrows():
        weather_map[(w["date"], w["node_id"])] = w
        
    # Vehicle classification dictionaries
    vehicles_by_class = {
        "LIGHT": fleet_df[fleet_df["vehicle_class"] == "LIGHT"].to_dict("records"),
        "MEDIUM": fleet_df[fleet_df["vehicle_class"] == "MEDIUM"].to_dict("records"),
        "HEAVY": fleet_df[fleet_df["vehicle_class"] == "HEAVY"].to_dict("records"),
    }
    
    shipments = []
    shipment_counter = 1
    
    all_dates = sorted(weather_df["date"].unique())
    
    for d_str in all_dates:
        curr_date = datetime.strptime(d_str, "%Y-%m-%d")
        
        for r in routes_list:
            route_id = r["route_id"]
            reg_id = r["region"]
            src = r["source_node"]
            dst = r["destination_node"]
            base_travel_time = r["normal_travel_time_hr"]
            terrain_diff = r["terrain_difficulty"]
            elev_change = r["elevation_change_m"]
            
            # Weather along route (mean of source and destination nodes)
            w_src = weather_map.get((d_str, src), {})
            w_dst = weather_map.get((d_str, dst), {})
            
            w_sev = (float(w_src.get("weather_severity", 0.1)) + float(w_dst.get("weather_severity", 0.1))) / 2.0
            precip = (float(w_src.get("precipitation_mm", 0.0)) + float(w_dst.get("precipitation_mm", 0.0))) / 2.0
            snow = (float(w_src.get("snowfall_cm", 0.0)) + float(w_dst.get("snowfall_cm", 0.0))) / 2.0
            
            # Convoy probability
            is_hub = "A01" in src or "B01" in src or "C01" in src or "A05" in src or "B05" in src or "C05" in src
            prob = 0.60 if is_hub else 0.35
            
            if np.random.rand() > prob:
                continue
                
            cat = np.random.choice(SUPPLY_CATEGORIES, p=[0.25, 0.25, 0.25, 0.10, 0.15])
            
            # Select compatible vehicle class
            if terrain_diff > 0.75:
                v_class = np.random.choice(["LIGHT", "MEDIUM"], p=[0.55, 0.45])
            elif terrain_diff > 0.50:
                v_class = np.random.choice(["LIGHT", "MEDIUM", "HEAVY"], p=[0.30, 0.50, 0.20])
            else:
                v_class = np.random.choice(["LIGHT", "MEDIUM", "HEAVY"], p=[0.20, 0.35, 0.45])
                
            avail_vehicles = vehicles_by_class[v_class]
            vehicle = avail_vehicles[np.random.randint(0, len(avail_vehicles))]
            v_id = vehicle["vehicle_id"]
            max_cap = vehicle["capacity_kg"]
            v_speed_factor = vehicle["speed_factor"]
            resilience = vehicle.get("weather_resilience", 0.85)
            
            # Payload quantity (60% to 98% of vehicle payload capacity)
            qty = round(float(np.random.uniform(0.60 * max_cap, 0.98 * max_cap)), 1)
            
            # Planned departure
            dep_hour = int(np.random.randint(5, 9))
            dep_min = int(np.random.choice([0, 15, 30, 45]))
            planned_dep_dt = curr_date + timedelta(hours=dep_hour, minutes=dep_min)
            
            # Planned travel time
            planned_travel_time = round(base_travel_time / v_speed_factor, 2)
            planned_arr_dt = planned_dep_dt + timedelta(hours=planned_travel_time)
            
            # Dispatch delay
            dispatch_delay_min = int(np.random.exponential(15)) if w_sev < 0.45 else int(np.random.exponential(45))
            actual_dep_dt = planned_dep_dt + timedelta(minutes=dispatch_delay_min)
            
            # Environmental multipliers
            weather_mult = 1.0 + (w_sev * 0.45) + (snow / 15.0) * 0.35 + (precip / 50.0) * 0.25
            terrain_mult = 1.0 + (terrain_diff * 0.25) + (elev_change / 2500.0) * 0.15
            
            # Disruption Effect
            dis_event = disruption_map.get((d_str, route_id))
            dis_mult = float(dis_event["travel_time_multiplier"]) if dis_event is not None else 1.0
            
            env_impact = (weather_mult - 1.0) * (1.1 - resilience)
            total_time_mult = max(1.0, (1.0 + env_impact) * terrain_mult * dis_mult)
            
            # Actual Travel Time
            actual_travel_time = round(planned_travel_time * total_time_mult + float(np.random.normal(0, 0.15)), 2)
            actual_travel_time = max(0.5, actual_travel_time)
            
            actual_arr_dt = actual_dep_dt + timedelta(hours=actual_travel_time)
            
            # Delay Hours
            delay_hr = round(max(0.0, (actual_arr_dt - planned_arr_dt).total_seconds() / 3600.0), 2)
            
            # Status
            if dis_event is not None and dis_event.get("route_status") == "BLOCKED":
                status = "DELAYED_CRITICAL"
            elif delay_hr > 3.0:
                status = "SIGNIFICANTLY_DELAYED"
            elif delay_hr > 0.5:
                status = "MINOR_DELAY"
            else:
                status = "ON_TIME"
                
            shipments.append({
                "shipment_id": f"SHP-{shipment_counter:06d}",
                "date": d_str,
                "region": reg_id,
                "source_node": src,
                "destination_node": dst,
                "supply_category": cat,
                "quantity_kg": qty,
                "vehicle_id": v_id,
                "vehicle_class": v_class,
                "route_id": route_id,
                "planned_departure": planned_dep_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "actual_departure": actual_dep_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "planned_arrival": planned_arr_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "actual_arrival": actual_arr_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "planned_travel_time_hr": planned_travel_time,
                "actual_travel_time_hr": actual_travel_time,
                "delay_hours": delay_hr,
                "shipment_status": status,
                "disruption_active": 1 if dis_event is not None else 0,
                "weather_severity": round(w_sev, 3)
            })
            shipment_counter += 1
            
    df_shipments = pd.DataFrame(shipments)
    out_csv = os.path.join(SYNTHETIC_DATA_DIR, "shipments.csv")
    df_shipments.to_csv(out_csv, index=False)
    logger.info(f"Saved synthetic shipments dataset ({len(df_shipments)} shipments) to {out_csv}")
    return df_shipments
