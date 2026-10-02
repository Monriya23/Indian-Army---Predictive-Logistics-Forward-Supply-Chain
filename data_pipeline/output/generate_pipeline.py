"""
Master Data Pipeline Execution Module.
Executes end-to-end data acquisition, environmental processing,
weather-conditioned logistics simulation, ML training dataset creation, and validation.
"""

import os
import sys
import logging
from datetime import datetime
import pandas as pd

from data_pipeline.config import (
    DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, SYNTHETIC_DATA_DIR,
    TRAINING_DATA_DIR, METADATA_DATA_DIR
)
from data_pipeline.acquisition.weather import acquire_node_level_weather, acquire_regional_weather
from data_pipeline.acquisition.elevation import acquire_regional_elevation
from data_pipeline.acquisition.roads import acquire_regional_road_segments
from data_pipeline.processing.weather_processing import process_weather_data
from data_pipeline.processing.terrain_processing import process_terrain_features
from data_pipeline.processing.road_processing import process_road_network_features
from data_pipeline.simulation.nodes import generate_synthetic_nodes
from data_pipeline.simulation.fleet import generate_synthetic_fleet
from data_pipeline.simulation.routes import generate_synthetic_routes
from data_pipeline.simulation.demand import generate_weather_conditioned_demand
from data_pipeline.simulation.disruptions import generate_weather_conditioned_disruptions
from data_pipeline.simulation.shipments import generate_weather_conditioned_shipments
from data_pipeline.simulation.inventory import simulate_chronological_inventory
from data_pipeline.features.demand_features import build_demand_training_dataset
from data_pipeline.features.travel_time_features import build_travel_time_training_dataset
from data_pipeline.features.shortage_features import build_shortage_risk_training_dataset
from data_pipeline.utils.provenance import (
    generate_data_source_register,
    generate_data_dictionary,
    generate_provenance_audit
)
from data_pipeline.utils.reproducibility import record_reproducibility_metadata
from data_pipeline.validation.validate_sources import validate_raw_sources
from data_pipeline.validation.validate_datasets import run_comprehensive_validation

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def run_full_pipeline(force_refresh_raw: bool = False) -> dict:
    """
    Execute complete Phase 1 Data Pipeline.
    """
    start_time = datetime.now()
    logger.info("=" * 80)
    logger.info("STARTING PHASE 1: DATA ACQUISITION & CONDITIONED SYNTHETIC LOGISTICS PIPELINE")
    logger.info("=" * 80)
    
    # -------------------------------------------------------------
    # Step 1: Real Public Data Acquisition
    # -------------------------------------------------------------
    logger.info(">>> STEP 1: Acquiring Real Public Environmental & Geographical Data...")
    raw_weather_dict = acquire_regional_weather(force_refresh=force_refresh_raw)
    raw_elevation_df = acquire_regional_elevation(force_refresh=force_refresh_raw)
    raw_roads_df = acquire_regional_road_segments(raw_elevation_df, force_refresh=force_refresh_raw)
    
    # Validate raw sources
    raw_val = validate_raw_sources()
    logger.info(f"Raw sources validation: {raw_val}")
    
    # -------------------------------------------------------------
    # Step 2: Environmental Processing & Feature Engineering
    # -------------------------------------------------------------
    logger.info(">>> STEP 2: Processing Environmental & Geographic Features...")
    terrain_features_df = process_terrain_features(raw_elevation_df)
    weather_processed_df = process_weather_data(raw_weather_dict, terrain_features_df)
    road_features_df = process_road_network_features(raw_roads_df, terrain_features_df)
    
    # -------------------------------------------------------------
    # Step 3: Conditioned Synthetic Logistics Simulation
    # -------------------------------------------------------------
    logger.info(">>> STEP 3: Running Weather-Conditioned Synthetic Logistics Simulation...")
    nodes_df = generate_synthetic_nodes(terrain_features_df, road_features_df)
    fleet_df = generate_synthetic_fleet(nodes_df)
    routes_df = generate_synthetic_routes(road_features_df)
    
    demand_df = generate_weather_conditioned_demand(nodes_df, weather_processed_df)
    disruptions_df = generate_weather_conditioned_disruptions(weather_processed_df, routes_df)
    shipments_df = generate_weather_conditioned_shipments(nodes_df, routes_df, fleet_df, weather_processed_df, disruptions_df)
    inventory_df = simulate_chronological_inventory(nodes_df, demand_df, shipments_df)
    
    # -------------------------------------------------------------
    # Step 4: ML-Ready Training Datasets
    # -------------------------------------------------------------
    logger.info(">>> STEP 4: Constructing ML-Ready Training Datasets...")
    demand_training_df = build_demand_training_dataset(demand_df, weather_processed_df, nodes_df)
    travel_time_training_df = build_travel_time_training_dataset(shipments_df, routes_df, weather_processed_df, disruptions_df, fleet_df)
    shortage_risk_training_df = build_shortage_risk_training_dataset(inventory_df, weather_processed_df, nodes_df, shipments_df)
    
    # -------------------------------------------------------------
    # Step 5: Data Provenance & Metadata Generation
    # -------------------------------------------------------------
    logger.info(">>> STEP 5: Generating Metadata, Provenance, & Reproducibility Specs...")
    generate_data_source_register()
    generate_data_dictionary()
    generate_provenance_audit()
    
    # Register dataset file paths for checksums
    all_dataset_files = {
        "weather_processed": os.path.join(PROCESSED_DATA_DIR, "weather_processed.csv"),
        "terrain_features": os.path.join(PROCESSED_DATA_DIR, "terrain_features.csv"),
        "road_network_features": os.path.join(PROCESSED_DATA_DIR, "road_network_features.csv"),
        "nodes": os.path.join(SYNTHETIC_DATA_DIR, "nodes.csv"),
        "demand": os.path.join(SYNTHETIC_DATA_DIR, "demand.csv"),
        "inventory": os.path.join(SYNTHETIC_DATA_DIR, "inventory.csv"),
        "fleet": os.path.join(SYNTHETIC_DATA_DIR, "fleet.csv"),
        "routes": os.path.join(SYNTHETIC_DATA_DIR, "routes.csv"),
        "shipments": os.path.join(SYNTHETIC_DATA_DIR, "shipments.csv"),
        "disruptions": os.path.join(SYNTHETIC_DATA_DIR, "disruptions.csv"),
        "demand_training": os.path.join(TRAINING_DATA_DIR, "demand_training.csv"),
        "travel_time_training": os.path.join(TRAINING_DATA_DIR, "travel_time_training.csv"),
        "shortage_risk_training": os.path.join(TRAINING_DATA_DIR, "shortage_risk_training.csv"),
    }
    record_reproducibility_metadata(all_dataset_files)
    
    # -------------------------------------------------------------
    # Step 6: Comprehensive Quality Validation & Report
    # -------------------------------------------------------------
    logger.info(">>> STEP 6: Executing Full Data Integrity & Quality Validation Suite...")
    validation_results = run_comprehensive_validation()
    
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info("=" * 80)
    logger.info(f"PIPELINE COMPLETED SUCCESSFULLY IN {elapsed:.2f} SECONDS!")
    logger.info("=" * 80)
    
    return {
        "status": "SUCCESS",
        "elapsed_seconds": elapsed,
        "validation_summary": validation_results
    }

if __name__ == "__main__":
    run_full_pipeline(force_refresh_raw=False)
