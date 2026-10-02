"""
Travel-Time Prediction ML-Ready Feature Engineering Module.
Builds training datasets combining physical route geometry, vehicle payload specs,
observed meteorological covariates, and disruption indicators.
"""

import os
import logging
import pandas as pd
from data_pipeline.config import TRAINING_DATA_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def build_travel_time_training_dataset(
    shipments_df: pd.DataFrame,
    routes_df: pd.DataFrame,
    weather_df: pd.DataFrame,
    disruptions_df: pd.DataFrame,
    fleet_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Construct travel-time prediction dataset.
    
    Target:
      - actual_travel_time_hr
    
    Features:
      - Route geometry (distance, elevation change, terrain difficulty, lanes, surface, connectivity)
      - Vehicle attributes (vehicle class, payload utilization, operating range)
      - Weather conditions along route (temperature, precipitation, snow, wind, severity)
      - Disruption indicators (disruption active, severity, multiplier)
      - Planned departure schedule
    """
    logger.info("Engineering travel-time prediction features...")
    
    df = shipments_df.copy()
    
    # 1. Merge route characteristics
    r_cols = ["route_id", "distance_km", "elevation_change_m", "terrain_difficulty",
              "road_classification", "road_condition", "normal_travel_time_hr",
              "weather_exposure", "route_reliability", "alternative_route_count"]
    df = pd.merge(df, routes_df[r_cols], on="route_id", how="left")
    
    # 2. Merge fleet specs
    f_cols = ["vehicle_id", "speed_factor", "operating_range_km", "max_slope_degree", "weather_resilience"]
    df = pd.merge(df, fleet_df[f_cols], on="vehicle_id", how="left")
    
    # 3. Payload utilization ratio
    vehicle_caps = dict(zip(fleet_df["vehicle_id"], fleet_df["capacity_kg"]))
    df["vehicle_capacity_kg"] = df["vehicle_id"].map(vehicle_caps).fillna(7500.0)
    df["payload_utilization_ratio"] = (df["quantity_kg"] / df["vehicle_capacity_kg"]).round(3)
    
    # 4. Merge weather covariates from source node
    w_cols = ["date", "node_id", "temperature_c", "temperature_elevation_adjusted_c",
              "precipitation_mm", "snowfall_cm", "wind_speed_kmh", "rainfall_3d",
              "weather_severity", "extreme_weather_indicator"]
              
    src_weather = weather_df[w_cols].copy().rename(columns={
        "node_id": "source_node",
        "temperature_c": "source_temp_c",
        "temperature_elevation_adjusted_c": "temperature_c",
        "precipitation_mm": "precipitation_mm",
        "snowfall_cm": "snowfall_cm",
        "wind_speed_kmh": "wind_speed_kmh",
        "rainfall_3d": "rainfall_3d",
        "weather_severity": "source_weather_severity",
        "extreme_weather_indicator": "extreme_weather_indicator"
    })
    
    df = pd.merge(df, src_weather, on=["date", "source_node"], how="left")
    
    # 5. Merge disruption event details if any
    dis_map = {
        (r["date"], r["affected_route"]): {
            "disruption_severity": r["severity"],
            "disruption_type": r["event_type"],
            "travel_time_multiplier": r["travel_time_multiplier"]
        }
        for _, r in disruptions_df.iterrows()
    }
    
    dis_actives = []
    dis_sevs = []
    dis_types = []
    dis_mults = []
    
    for _, row in df.iterrows():
        key = (row["date"], row["route_id"])
        if key in dis_map:
            d_item = dis_map[key]
            dis_actives.append(1)
            dis_sevs.append(d_item["disruption_severity"])
            dis_types.append(d_item["disruption_type"])
            dis_mults.append(d_item["travel_time_multiplier"])
        else:
            dis_actives.append(0)
            dis_sevs.append(0.0)
            dis_types.append("NONE")
            dis_mults.append(1.0)
            
    df["disruption_active"] = dis_actives
    df["disruption_severity"] = dis_sevs
    df["disruption_type"] = dis_types
    df["travel_time_multiplier"] = dis_mults
    
    # 6. Temporal covariates
    plan_dep = pd.to_datetime(df["planned_departure"])
    df["planned_departure_hour"] = (plan_dep.dt.hour + plan_dep.dt.minute / 60.0).round(2)
    df["day_of_week"] = plan_dep.dt.dayofweek
    df["month"] = plan_dep.dt.month
    
    # Select feature columns in logical order
    feature_columns = [
        "shipment_id", "date", "region", "source_node", "destination_node", "route_id",
        "vehicle_id", "vehicle_class", "supply_category", "quantity_kg", "payload_utilization_ratio",
        "distance_km", "elevation_change_m", "terrain_difficulty", "road_classification", "road_condition",
        "weather_exposure", "route_reliability", "alternative_route_count",
        "speed_factor", "operating_range_km", "weather_resilience",
        "planned_departure_hour", "day_of_week", "month",
        "temperature_c", "precipitation_mm", "snowfall_cm", "wind_speed_kmh", "rainfall_3d",
        "weather_severity", "extreme_weather_indicator",
        "disruption_active", "disruption_severity", "disruption_type", "travel_time_multiplier",
        "planned_travel_time_hr",
        # Target
        "actual_travel_time_hr"
    ]
    
    clean_df = df[feature_columns].dropna().reset_index(drop=True)
    out_csv = os.path.join(TRAINING_DATA_DIR, "travel_time_training.csv")
    clean_df.to_csv(out_csv, index=False)
    logger.info(f"Saved travel-time training dataset ({len(clean_df)} records) to {out_csv}")
    return clean_df
