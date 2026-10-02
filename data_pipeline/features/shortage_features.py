"""
Shortage-Risk Prediction ML-Ready Feature Engineering Module.
Constructs binary shortage classification datasets with strict time-series leakage prevention
and node-specific environmental covariates.
"""

import os
import logging
import numpy as np
import pandas as pd
from data_pipeline.config import TRAINING_DATA_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def build_shortage_risk_training_dataset(
    inventory_df: pd.DataFrame,
    weather_df: pd.DataFrame,
    nodes_df: pd.DataFrame,
    shipments_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Construct shortage-risk prediction dataset.
    
    Target:
      - shortage_in_next_7_days (Binary 0/1: is shortage_flag == 1 at any point between t+1 and t+7)
    
    Features:
      - Current inventory level, capacity utilization, days of supply
      - Historical consumption lags and rolling statistics
      - Node-specific weather severity, rainfall, snowfall, and temperature
      - Node criticality and terrain difficulty
    """
    logger.info("Engineering shortage-risk prediction features with node-level weather...")
    
    df = inventory_df.copy()
    
    # 1. Capacity utilization percentage
    df["capacity_utilization_pct"] = ((df["closing_inventory"] / df["storage_capacity"]) * 100.0).round(2)
    
    # 2. Merge node metadata
    n_cols = ["node_id", "region", "elevation_m", "terrain_difficulty", "criticality_level", "road_accessibility"]
    df = pd.merge(df, nodes_df[n_cols], on="node_id", how="left")
    
    # 3. Merge weather covariates on (date, node_id)
    w_cols = ["date", "node_id", "temperature_c", "temperature_elevation_adjusted_c",
              "precipitation_mm", "rainfall_7d", "snowfall_cm",
              "weather_severity", "extreme_weather_indicator"]
    df = pd.merge(df, weather_df[w_cols], on=["date", "node_id"], how="left")
    
    # Ensure correct datetime sorting
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["node_id", "supply_category", "date"]).reset_index(drop=True)
    
    feature_dfs = []
    
    for (n_id, cat), group in df.groupby(["node_id", "supply_category"]):
        grp = group.copy()
        
        # 4. Historical Consumption Features (Past only)
        grp["consumed_lag_1"] = grp["consumed_quantity"].shift(1)
        grp["consumed_lag_7"] = grp["consumed_quantity"].shift(7)
        
        past_consumed = grp["consumed_quantity"].shift(1)
        grp["consumed_rolling_mean_7"] = past_consumed.rolling(window=7, min_periods=3).mean().round(2)
        grp["consumed_rolling_mean_14"] = past_consumed.rolling(window=14, min_periods=7).mean().round(2)
        grp["consumed_rolling_std_7"] = past_consumed.rolling(window=7, min_periods=3).std().fillna(0.0).round(2)
        
        # 5. Target Definition: Shortage occurring in next 7 days [t+1 to t+7]
        shortage_flags = grp["shortage_flag"]
        next_7d_shortages = shortage_flags.iloc[::-1].rolling(window=7, min_periods=7).max().iloc[::-1].shift(-1)
        grp["shortage_in_next_7_days"] = next_7d_shortages.fillna(0).astype(int)
        
        # 6. Temporal covariates
        grp["day_of_week"] = grp["date"].dt.dayofweek
        grp["month"] = grp["date"].dt.month
        grp["day_of_year"] = grp["date"].dt.dayofyear
        
        feature_dfs.append(grp)
        
    full_df = pd.concat(feature_dfs, ignore_index=True)
    
    # Drop rows without complete history or future targets
    valid_df = full_df.dropna(subset=["consumed_lag_7", "shortage_in_next_7_days"]).copy()
    valid_df["date"] = valid_df["date"].dt.strftime("%Y-%m-%d")
    
    feature_columns = [
        "date", "node_id", "region", "supply_category", "criticality_level",
        "opening_inventory", "received_quantity", "consumed_quantity", "closing_inventory",
        "storage_capacity", "capacity_utilization_pct", "days_of_supply", "critical_threshold", "shortage_flag",
        "consumed_lag_1", "consumed_lag_7", "consumed_rolling_mean_7", "consumed_rolling_mean_14", "consumed_rolling_std_7",
        "elevation_m", "terrain_difficulty", "road_accessibility",
        "temperature_c", "temperature_elevation_adjusted_c", "precipitation_mm", "rainfall_7d", "snowfall_cm",
        "weather_severity", "extreme_weather_indicator",
        "day_of_week", "month", "day_of_year",
        # Target
        "shortage_in_next_7_days"
    ]
    
    clean_df = valid_df[feature_columns].reset_index(drop=True)
    out_csv = os.path.join(TRAINING_DATA_DIR, "shortage_risk_training.csv")
    clean_df.to_csv(out_csv, index=False)
    logger.info(f"Saved shortage-risk training dataset ({len(clean_df)} records) to {out_csv}")
    return clean_df
