"""
Weather-Conditioned Demand Simulation Module.
Generates realistic, causal, daily demand and consumption figures for each
node x supply_category x date, conditioned on node-level observed & elevation-adjusted meteorological variables.
"""

import os
import logging
from datetime import datetime
import numpy as np
import pandas as pd
from data_pipeline.config import SYNTHETIC_DATA_DIR, SUPPLY_CATEGORIES, RANDOM_SEED

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def generate_weather_conditioned_demand(nodes_df: pd.DataFrame, weather_df: pd.DataFrame, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """
    Generate daily demand records for each node x supply_category x date.
    
    Causal Formula:
      final_demand = max(15.0, (baseline * seasonal_factor * temperature_effect * weather_effect * trend_factor * scenario_factor) + noise)
    """
    np.random.seed(seed)
    
    # Category baseline demands (in kg/day)
    CATEGORY_BASELINES = {
        "FOOD": {"MAIN_HUB": 3200, "REGIONAL_DEPOT": 2400, "TRANSIT_HUB": 1400, "FORWARD_DEPOT": 900, "TACTICAL_NODE": 500},
        "WATER": {"MAIN_HUB": 4000, "REGIONAL_DEPOT": 3000, "TRANSIT_HUB": 1800, "FORWARD_DEPOT": 1200, "TACTICAL_NODE": 700},
        "FUEL": {"MAIN_HUB": 3500, "REGIONAL_DEPOT": 2600, "TRANSIT_HUB": 1600, "FORWARD_DEPOT": 1100, "TACTICAL_NODE": 600},
        "MEDICAL": {"MAIN_HUB": 600, "REGIONAL_DEPOT": 450, "TRANSIT_HUB": 250, "FORWARD_DEPOT": 180, "TACTICAL_NODE": 100},
        "GENERAL_SUPPLIES": {"MAIN_HUB": 2000, "REGIONAL_DEPOT": 1500, "TRANSIT_HUB": 900, "FORWARD_DEPOT": 600, "TACTICAL_NODE": 350},
    }
    
    # Pre-index weather by (node_id) into records
    weather_by_node = {}
    for n_id, grp in weather_df.groupby("node_id"):
        weather_by_node[n_id] = grp.to_dict("records")
        
    records = []
    base_dt = datetime.strptime("2022-01-01", "%Y-%m-%d")
    
    for _, node in nodes_df.iterrows():
        node_id = node["node_id"]
        reg_id = node["region"]
        role = node["node_role"]
        
        node_weather_records = weather_by_node.get(node_id, [])
        
        for w_row in node_weather_records:
            d_str = w_row["date"]
            dt = datetime.strptime(d_str, "%Y-%m-%d")
            day_of_year = dt.timetuple().tm_yday
            
            # Use elevation-adjusted temperature for physiological & heating thermal demand
            temp_c = float(w_row.get("temperature_elevation_adjusted_c", w_row["temperature_c"]))
            precip_mm = float(w_row["precipitation_mm"])
            snow_cm = float(w_row["snowfall_cm"])
            severity = float(w_row["weather_severity"])
            
            # Seasonal factor (sinusoidal)
            season_rad = (day_of_year / 365.25) * 2 * np.pi
            days_from_start = (dt - base_dt).days
            trend_fac = 1.0 + (days_from_start / 1096.0) * 0.05
            scenario_fac = 1.25 if (day_of_year % 90 in [14, 15, 16]) else 1.00
            
            for cat in SUPPLY_CATEGORIES:
                base = float(CATEGORY_BASELINES[cat].get(role, 800))
                
                # Temperature Effect (Prototype Modelling Assumption)
                if cat == "WATER":
                    if temp_c > 35.0:
                        temp_eff = 1.0 + (temp_c - 35.0) * 0.035
                    elif temp_c < 0.0:
                        temp_eff = 1.0 + abs(temp_c) * 0.01
                    else:
                        temp_eff = 1.0
                    seasonal_fac = 1.0 + 0.20 * np.sin(season_rad - 1.2)
                    
                elif cat == "FUEL":
                    if temp_c < 5.0:
                        temp_eff = 1.0 + (5.0 - temp_c) * 0.045
                    elif temp_c > 42.0:
                        temp_eff = 1.0 + (temp_c - 42.0) * 0.02
                    else:
                        temp_eff = 1.0
                    seasonal_fac = 1.0 + 0.35 * np.cos(season_rad)
                    
                elif cat == "FOOD":
                    temp_eff = 1.0 + (min(30.0, max(0.0, -temp_c)) * 0.008)
                    seasonal_fac = 1.0 + 0.05 * np.cos(season_rad)
                    
                elif cat == "MEDICAL":
                    temp_eff = 1.0 + (min(30.0, max(0.0, -temp_c)) * 0.015) + (min(15.0, max(0.0, temp_c - 40.0)) * 0.02)
                    seasonal_fac = 1.0 + 0.15 * np.sin(season_rad)
                    
                else: # GENERAL_SUPPLIES
                    temp_eff = 1.0 + (severity * 0.15)
                    seasonal_fac = 1.0 + 0.08 * np.sin(season_rad)
                    
                # Weather Effect (Rain, Snow, Storms)
                if cat == "MEDICAL":
                    weather_eff = 1.0 + (precip_mm / 60.0) * 0.35 + (snow_cm / 20.0) * 0.25
                elif cat == "GENERAL_SUPPLIES":
                    weather_eff = 1.0 + (precip_mm / 50.0) * 0.20 + (snow_cm / 15.0) * 0.30
                elif cat == "FUEL":
                    weather_eff = 1.0 + (snow_cm / 15.0) * 0.40
                else:
                    weather_eff = 1.0 + (severity * 0.10)
                    
                # Controlled Noise
                noise = np.random.normal(0, base * 0.06)
                calculated_demand = (base * seasonal_fac * temp_eff * weather_eff * trend_fac * scenario_fac) + noise
                final_demand = round(max(15.0, float(calculated_demand)), 1)
                
                # Actual consumption with slight variance
                cons_ratio = np.clip(np.random.normal(0.98, 0.03), 0.88, 1.08)
                actual_consumption = round(max(10.0, final_demand * float(cons_ratio)), 1)
                
                records.append({
                    "date": d_str,
                    "node_id": node_id,
                    "region": reg_id,
                    "supply_category": cat,
                    "baseline_demand": base,
                    "temperature_effect": round(float(temp_eff), 3),
                    "weather_effect": round(float(weather_eff), 3),
                    "seasonal_factor": round(float(seasonal_fac), 3),
                    "trend_factor": round(float(trend_fac), 3),
                    "scenario_factor": round(float(scenario_fac), 2),
                    "demand_noise": round(float(noise), 1),
                    "final_demand": final_demand,
                    "actual_consumption": actual_consumption,
                    "data_type": "SYNTHETIC_LOGISTICS_DEMAND"
                })
                
    df_demand = pd.DataFrame(records)
    out_csv = os.path.join(SYNTHETIC_DATA_DIR, "demand.csv")
    df_demand.to_csv(out_csv, index=False)
    logger.info(f"Saved synthetic demand dataset ({len(df_demand)} records) to {out_csv}")
    return df_demand
