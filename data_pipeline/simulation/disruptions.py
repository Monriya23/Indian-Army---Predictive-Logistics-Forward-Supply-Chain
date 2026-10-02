"""
Weather-Conditioned Logistics Disruptions Simulation Module.
Generates realistic disruption events conditioned on node and corridor meteorological thresholds,
terrain slope, and infrastructure characteristics.
"""

import os
import logging
import numpy as np
import pandas as pd
from data_pipeline.config import SYNTHETIC_DATA_DIR, RANDOM_SEED

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def generate_weather_conditioned_disruptions(
    weather_df: pd.DataFrame,
    routes_df: pd.DataFrame,
    seed: int = RANDOM_SEED
) -> pd.DataFrame:
    """
    Generate synthetic disruption events conditioned on route-level observed environmental conditions.
    """
    np.random.seed(seed)
    
    # Pre-index weather by (date, node_id)
    weather_map = {}
    for _, w in weather_df.iterrows():
        weather_map[(w["date"], w["node_id"])] = w
        
    routes_list = routes_df.to_dict("records")
    all_dates = sorted(weather_df["date"].unique())
    
    events = []
    event_counter = 1
    
    for d_str in all_dates:
        for r in routes_list:
            route_id = r["route_id"]
            reg_id = r["region"]
            src = r["source_node"]
            dst = r["destination_node"]
            
            # Route weather is evaluated using worst-case between source and destination endpoints
            w_src = weather_map.get((d_str, src))
            w_dst = weather_map.get((d_str, dst))
            
            if w_src is None or w_dst is None:
                continue
                
            temp_c = min(float(w_src["temperature_elevation_adjusted_c"]), float(w_dst["temperature_elevation_adjusted_c"]))
            max_temp = max(float(w_src["temperature_elevation_adjusted_c"]), float(w_dst["temperature_elevation_adjusted_c"]))
            precip_mm = max(float(w_src["precipitation_mm"]), float(w_dst["precipitation_mm"]))
            snow_cm = max(float(w_src["snowfall_cm"]), float(w_dst["snowfall_cm"]))
            rain_3d = max(float(w_src["rainfall_3d"]), float(w_dst["rainfall_3d"]))
            wind_kmh = max(float(w_src["wind_speed_kmh"]), float(w_dst["wind_speed_kmh"]))
            severity = max(float(w_src["weather_severity"]), float(w_dst["weather_severity"]))
            
            # 1. Heavy Snow / Avalanche risk in High Altitude
            if snow_cm >= 6.0 or (temp_c <= -8.0 and precip_mm >= 4.0):
                sev = min(1.0, 0.4 + (snow_cm / 25.0) + (abs(temp_c) / 40.0) * 0.3)
                is_closure = sev > 0.75
                events.append({
                    "event_id": f"DIS-{event_counter:05d}",
                    "date": d_str,
                    "region": reg_id,
                    "affected_route": route_id,
                    "event_type": "SNOW" if not is_closure else "ROAD_CLOSURE",
                    "severity": round(sev, 2),
                    "duration_hours": round(float(np.random.uniform(6.0, 36.0)), 1),
                    "capacity_reduction_percent": round(float(np.random.uniform(40.0, 90.0) if not is_closure else 100.0), 1),
                    "travel_time_multiplier": round(float(np.random.uniform(1.8, 3.5) if not is_closure else 5.0), 2),
                    "route_status": "RESTRICTED" if not is_closure else "BLOCKED",
                    "environmental_trigger": f"Snowfall={snow_cm}cm, MinTemp={temp_c}C"
                })
                event_counter += 1
                
            # 2. Monsoon Rain & Landslide in Steep Mountain Terrain
            elif (rain_3d >= 40.0 or precip_mm >= 30.0) and reg_id in ["SIKKIM", "LADAKH"]:
                sev = min(1.0, 0.5 + (rain_3d / 120.0))
                is_closure = sev > 0.70
                events.append({
                    "event_id": f"DIS-{event_counter:05d}",
                    "date": d_str,
                    "region": reg_id,
                    "affected_route": route_id,
                    "event_type": "LANDSLIDE" if sev > 0.65 else "HEAVY_RAIN",
                    "severity": round(sev, 2),
                    "duration_hours": round(float(np.random.uniform(8.0, 48.0)), 1),
                    "capacity_reduction_percent": round(float(np.random.uniform(50.0, 100.0)), 1),
                    "travel_time_multiplier": round(float(np.random.uniform(2.0, 4.0) if not is_closure else 6.0), 2),
                    "route_status": "RESTRICTED" if not is_closure else "BLOCKED",
                    "environmental_trigger": f"3-Day Rain={rain_3d}mm, Daily Precip={precip_mm}mm"
                })
                event_counter += 1
                
            # 3. Extreme Heat & Sandstorm in Arid Desert
            elif max_temp >= 43.0 and reg_id == "RAJASTHAN":
                sev = min(1.0, 0.4 + (max_temp - 43.0) * 0.08)
                events.append({
                    "event_id": f"DIS-{event_counter:05d}",
                    "date": d_str,
                    "region": reg_id,
                    "affected_route": route_id,
                    "event_type": "EXTREME_HEAT",
                    "severity": round(sev, 2),
                    "duration_hours": round(float(np.random.uniform(4.0, 12.0)), 1),
                    "capacity_reduction_percent": round(float(np.random.uniform(20.0, 50.0)), 1),
                    "travel_time_multiplier": round(float(np.random.uniform(1.3, 1.8)), 2),
                    "route_status": "RESTRICTED",
                    "environmental_trigger": f"Max Temp={max_temp}C"
                })
                event_counter += 1
                
            # 4. Gale Winds / Fog
            elif wind_kmh >= 48.0:
                events.append({
                    "event_id": f"DIS-{event_counter:05d}",
                    "date": d_str,
                    "region": reg_id,
                    "affected_route": route_id,
                    "event_type": "WEATHER_DELAY",
                    "severity": round(min(1.0, wind_kmh / 75.0), 2),
                    "duration_hours": round(float(np.random.uniform(3.0, 10.0)), 1),
                    "capacity_reduction_percent": round(float(np.random.uniform(15.0, 40.0)), 1),
                    "travel_time_multiplier": round(float(np.random.uniform(1.25, 1.7)), 2),
                    "route_status": "RESTRICTED",
                    "environmental_trigger": f"Wind Speed={wind_kmh}km/h"
                })
                event_counter += 1
                
            # 5. Generic Non-Weather Baseline Disruptions (Low background probability ~0.5% per route-day)
            elif np.random.rand() < 0.005:
                dis_type = np.random.choice([
                    "VEHICLE_BREAKDOWN",
                    "TRANSPORT_CAPACITY_REDUCTION",
                    "SECURITY_RELATED_ROUTE_RESTRICTION"
                ])
                events.append({
                    "event_id": f"DIS-{event_counter:05d}",
                    "date": d_str,
                    "region": reg_id,
                    "affected_route": route_id,
                    "event_type": dis_type,
                    "severity": round(float(np.random.uniform(0.2, 0.6)), 2),
                    "duration_hours": round(float(np.random.uniform(2.0, 14.0)), 1),
                    "capacity_reduction_percent": round(float(np.random.uniform(15.0, 50.0)), 1),
                    "travel_time_multiplier": round(float(np.random.uniform(1.2, 1.9)), 2),
                    "route_status": "RESTRICTED",
                    "environmental_trigger": "Operational / Baseline Maintenance / Administrative Window"
                })
                event_counter += 1
                
    df_disruptions = pd.DataFrame(events)
    out_csv = os.path.join(SYNTHETIC_DATA_DIR, "disruptions.csv")
    df_disruptions.to_csv(out_csv, index=False)
    logger.info(f"Saved synthetic disruptions dataset ({len(df_disruptions)} events) to {out_csv}")
    return df_disruptions
