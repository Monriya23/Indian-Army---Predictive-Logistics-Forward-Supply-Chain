"""
Demand Forecasting ML-Ready Feature Engineering Module.
Builds training datasets with historical demand lags, rolling statistical windows,
and node-specific environmental covariates, with zero future-data leakage.
"""

import os
import logging
import numpy as np
import pandas as pd
from data_pipeline.config import TRAINING_DATA_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def build_demand_training_dataset(
    demand_df: pd.DataFrame,
    weather_df: pd.DataFrame,
    nodes_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Construct demand forecasting training dataset.
    
    Targets:
      - demand_next_day: demand at t+1
      - demand_next_7_days: cumulative demand from t+1 to t+7
    
    Features:
      - lag_1, lag_7, lag_14, lag_30
      - rolling_mean_7, rolling_mean_14, rolling_mean_30
      - rolling_std_7, rolling_std_30
      - Node-specific observed and elevation-adjusted environmental covariates
    """
    logger.info("Engineering demand forecasting features with node-level weather...")
    
    # Merge weather data on date and node_id
    w_cols = ["date", "node_id", "temperature_c", "temperature_elevation_adjusted_c",
              "temperature_7d_avg", "precipitation_mm", "rainfall_3d", "rainfall_7d",
              "snowfall_cm", "snowfall_proxy_cm", "wind_speed_kmh",
              "weather_severity", "extreme_weather_indicator"]
              
    df_merged = pd.merge(demand_df, weather_df[w_cols], on=["date", "node_id"], how="left")
    
    # Merge node characteristics
    n_cols = ["node_id", "elevation_m", "terrain_difficulty", "criticality_level", "road_accessibility"]
    df_merged = pd.merge(df_merged, nodes_df[n_cols], on="node_id", how="left")
    
    # Ensure correct datetime sorting
    df_merged["date"] = pd.to_datetime(df_merged["date"])
    df_merged = df_merged.sort_values(["node_id", "supply_category", "date"]).reset_index(drop=True)
    
    # Feature engineering grouped by (node_id, supply_category)
    feature_dfs = []
    
    for (n_id, cat), group in df_merged.groupby(["node_id", "supply_category"]):
        grp = group.copy()
        
        # 1. Historical Lags (Strictly past values)
        grp["lag_1"] = grp["final_demand"].shift(1)
        grp["lag_7"] = grp["final_demand"].shift(7)
        grp["lag_14"] = grp["final_demand"].shift(14)
        grp["lag_30"] = grp["final_demand"].shift(30)
        
        # 2. Rolling Statistics (Shifted by 1 to prevent leakage of current day into rolling window)
        past_demand = grp["final_demand"].shift(1)
        grp["rolling_mean_7"] = past_demand.rolling(window=7, min_periods=3).mean().round(2)
        grp["rolling_mean_14"] = past_demand.rolling(window=14, min_periods=7).mean().round(2)
        grp["rolling_mean_30"] = past_demand.rolling(window=30, min_periods=14).mean().round(2)
        grp["rolling_std_7"] = past_demand.rolling(window=7, min_periods=3).std().fillna(0.0).round(2)
        grp["rolling_std_30"] = past_demand.rolling(window=30, min_periods=14).std().fillna(0.0).round(2)
        
        # 3. Targets (Strictly future)
        grp["demand_next_day"] = grp["final_demand"].shift(-1)
        
        # Rolling sum of next 7 days: shift(-7) rolling(7).sum()
        next_7d_series = grp["final_demand"].iloc[::-1].rolling(window=7, min_periods=7).sum().iloc[::-1].shift(-1)
        grp["demand_next_7_days"] = next_7d_series.round(1)
        
        # 4. Temporal Features
        grp["day_of_week"] = grp["date"].dt.dayofweek
        grp["month"] = grp["date"].dt.month
        grp["day_of_year"] = grp["date"].dt.dayofyear
        grp["is_weekend"] = grp["day_of_week"].isin([5, 6]).astype(int)
        
        feature_dfs.append(grp)
        
    full_df = pd.concat(feature_dfs, ignore_index=True)
    
    # Drop rows without complete lag_30 or future target (preserving strictly valid training rows)
    valid_df = full_df.dropna(subset=["lag_30", "demand_next_day", "demand_next_7_days"]).copy()
    valid_df["date"] = valid_df["date"].dt.strftime("%Y-%m-%d")
    
    out_csv = os.path.join(TRAINING_DATA_DIR, "demand_training.csv")
    valid_df.to_csv(out_csv, index=False)
    logger.info(f"Saved demand forecasting training dataset ({len(valid_df)} rows) to {out_csv}")
    return valid_df
