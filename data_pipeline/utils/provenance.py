"""
Data Provenance and Metadata Generation Module.
Generates comprehensive data_dictionary.csv and data_source_register.csv documenting
all field schemas, origins, units, and licenses.
"""

import os
import logging
from datetime import datetime
import pandas as pd
from data_pipeline.config import METADATA_DATA_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def generate_data_source_register() -> pd.DataFrame:
    """
    Generate data_source_register.csv tracking all primary public data providers,
    variables retrieved, licenses, and access status.
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    sources = [
        {
            "source_name": "NASA POWER (Prediction Of Worldwide Energy Resources)",
            "provider": "NASA Langley Research Center",
            "source_url": "https://power.larc.nasa.gov/",
            "variables_used": "T2M, T2M_MAX, T2M_MIN, PRECTOTCORR, WS10M, RH2M",
            "geographical_coverage": "Ladakh (34.15N, 77.58E), Sikkim (27.34N, 88.61E), Rajasthan (26.92N, 70.91E)",
            "temporal_coverage": "2022-01-01 to 2024-12-31 (1096 daily records per region)",
            "spatial_resolution": "0.5 x 0.5 degree (~50km)",
            "retrieval_date": today_str,
            "license_or_usage_notes": "NASA Open Data Policy (Public Domain / Free unrestricted research & commercial use)",
            "retrieval_status": "ONLINE_AUTOMATED_API"
        },
        {
            "source_name": "Copernicus DEM (GLO-90)",
            "provider": "European Space Agency (ESA) / Open-Meteo Elevation API",
            "source_url": "https://dataspace.copernicus.eu/",
            "variables_used": "elevation_m, local gradient, elevation_std_local_m, slope_degree",
            "geographical_coverage": "Ladakh, Sikkim, Rajasthan corridor node coordinates",
            "temporal_coverage": "Static Topographical Baseline (2020 Release)",
            "spatial_resolution": "90m global digital elevation model",
            "retrieval_date": today_str,
            "license_or_usage_notes": "Open Access under Copernicus Sentinel Data Policy (Free / CC-BY-4.0 equivalent)",
            "retrieval_status": "ONLINE_AUTOMATED_API"
        },
        {
            "source_name": "OpenStreetMap (OSM) / OSRM",
            "provider": "OpenStreetMap Contributors / Project OSRM",
            "source_url": "https://www.openstreetmap.org/",
            "variables_used": "road_distance_km, road_classification, lanes, surface_type, network topology",
            "geographical_coverage": "National Highway Corridors (NH-1, NH-10, NH-11, NH-68)",
            "temporal_coverage": "Current Public Network Topology (2024/2026)",
            "spatial_resolution": "Vector road geometry (sub-meter)",
            "retrieval_date": today_str,
            "license_or_usage_notes": "Open Database License (ODbL) / Open Data Commons",
            "retrieval_status": "ONLINE_AUTOMATED_API"
        },
        {
            "source_name": "ERA5-Land Reanalysis",
            "provider": "European Centre for Medium-Range Weather Forecasts (ECMWF) / Copernicus CDS",
            "source_url": "https://cds.climate.copernicus.eu/",
            "variables_used": "2m temperature, Total precipitation, 10m wind speed, Snowfall water equivalent",
            "geographical_coverage": "Western Himalayas, Eastern Himalayas, Western Arid Zone",
            "temporal_coverage": "Historical Reanalysis (1950-Present)",
            "spatial_resolution": "9km (0.1 degree)",
            "retrieval_date": today_str,
            "license_or_usage_notes": "Copernicus Terms of Use (Requires CDS API token registration ~/.cdsapirc)",
            "retrieval_status": "MANUAL_WORKFLOW_OR_STANDBY_REGISTERED_API"
        },
        {
            "source_name": "India Meteorological Department (IMD) Gridded Data",
            "provider": "Ministry of Earth Sciences, Government of India",
            "source_url": "https://mausam.imd.gov.in/",
            "variables_used": "Daily Gridded Rainfall (0.25x0.25 deg) & Temperature (1.0x1.0 deg)",
            "geographical_coverage": "Indian Landmass",
            "temporal_coverage": "1901-Present",
            "spatial_resolution": "0.25 x 0.25 degree (Rainfall)",
            "retrieval_date": today_str,
            "license_or_usage_notes": "Government Open Data / IMD Data Policy (Requires academic/institutional registration)",
            "retrieval_status": "MANUAL_WORKFLOW_SUPPORTED"
        }
    ]
    
    df = pd.DataFrame(sources)
    out_csv = os.path.join(METADATA_DATA_DIR, "data_source_register.csv")
    df.to_csv(out_csv, index=False)
    logger.info(f"Saved data source register ({len(df)} sources) to {out_csv}")
    return df

def generate_data_dictionary() -> pd.DataFrame:
    """
    Generate comprehensive data_dictionary.csv for all datasets across the pipeline.
    """
    entries = [
        # Processed Weather
        {"table_name": "weather_processed.csv", "column_name": "date", "description": "Observation date in ISO format", "data_type": "string (YYYY-MM-DD)", "unit": "date", "source_name": "NASA POWER", "source_url": "https://power.larc.nasa.gov/", "source_type": "PUBLIC_REAL", "generation_method": "API Acquisition & Standardization", "used_by_model": "All Models"},
        {"table_name": "weather_processed.csv", "column_name": "node_id", "description": "Unique study node identifier", "data_type": "string", "unit": "identifier", "source_name": "Configuration", "source_url": "N/A", "source_type": "SYNTHETIC", "generation_method": "Study Node Mapping", "used_by_model": "All Models"},
        {"table_name": "weather_processed.csv", "column_name": "region", "description": "Geographical study region identifier", "data_type": "string", "unit": "category", "source_name": "Civilian Geography", "source_url": "N/A", "source_type": "PUBLIC_REAL", "generation_method": "Config Definition", "used_by_model": "All Models"},
        {"table_name": "weather_processed.csv", "column_name": "latitude", "description": "Civilian study node latitude", "data_type": "float", "unit": "degrees_north", "source_name": "Civilian Geography", "source_url": "N/A", "source_type": "PUBLIC_REAL", "generation_method": "WGS84 Reference Point", "used_by_model": "Spatial Validation"},
        {"table_name": "weather_processed.csv", "column_name": "longitude", "description": "Civilian study node longitude", "data_type": "float", "unit": "degrees_east", "source_name": "Civilian Geography", "source_url": "N/A", "source_type": "PUBLIC_REAL", "generation_method": "WGS84 Reference Point", "used_by_model": "Spatial Validation"},
        {"table_name": "weather_processed.csv", "column_name": "temperature_c", "description": "Daily mean 2m ambient air temperature", "data_type": "float", "unit": "deg C", "source_name": "NASA POWER", "source_url": "https://power.larc.nasa.gov/", "source_type": "PUBLIC_REAL", "generation_method": "Direct Measurement / Reanalysis", "used_by_model": "Demand, Travel Time, Shortage"},
        {"table_name": "weather_processed.csv", "column_name": "temperature_max_c", "description": "Daily maximum 2m air temperature", "data_type": "float", "unit": "deg C", "source_name": "NASA POWER", "source_url": "https://power.larc.nasa.gov/", "source_type": "PUBLIC_REAL", "generation_method": "Direct Measurement", "used_by_model": "Demand, Disruptions"},
        {"table_name": "weather_processed.csv", "column_name": "temperature_min_c", "description": "Daily minimum 2m air temperature", "data_type": "float", "unit": "deg C", "source_name": "NASA POWER", "source_url": "https://power.larc.nasa.gov/", "source_type": "PUBLIC_REAL", "generation_method": "Direct Measurement", "used_by_model": "Demand, Disruptions"},
        {"table_name": "weather_processed.csv", "column_name": "temperature_elevation_adjusted_c", "description": "Derived temperature adjusted for node altitude via standard lapse rate (-6.5C/km)", "data_type": "float", "unit": "deg C", "source_name": "NASA POWER + Copernicus DEM", "source_url": "https://power.larc.nasa.gov/", "source_type": "DERIVED", "generation_method": "temperature_c - 0.0065 * (elevation_node - elevation_ref)", "used_by_model": "All Models"},
        {"table_name": "weather_processed.csv", "column_name": "precipitation_mm", "description": "Daily total corrected precipitation", "data_type": "float", "unit": "mm/day", "source_name": "NASA POWER", "source_url": "https://power.larc.nasa.gov/", "source_type": "PUBLIC_REAL", "generation_method": "Direct Measurement / Reanalysis", "used_by_model": "Demand, Travel Time, Shortage"},
        {"table_name": "weather_processed.csv", "column_name": "wind_speed_kmh", "description": "10-meter wind speed converted to km/h", "data_type": "float", "unit": "km/h", "source_name": "NASA POWER", "source_url": "https://power.larc.nasa.gov/", "source_type": "DERIVED", "generation_method": "Unit conversion: WS10M * 3.6", "used_by_model": "Travel Time, Disruptions"},
        {"table_name": "weather_processed.csv", "column_name": "relative_humidity_pct", "description": "Daily relative humidity at 2m", "data_type": "float", "unit": "%", "source_name": "NASA POWER", "source_url": "https://power.larc.nasa.gov/", "source_type": "PUBLIC_REAL", "generation_method": "Direct Measurement", "used_by_model": "Weather Conditioning"},
        {"table_name": "weather_processed.csv", "column_name": "snowfall_era5_cm", "description": "Daily snowfall reanalysis from ECMWF ERA5-Land (9km grid)", "data_type": "float", "unit": "cm/day", "source_name": "ECMWF ERA5-Land", "source_url": "https://cds.climate.copernicus.eu/", "source_type": "PUBLIC_REAL", "generation_method": "ERA5-Land Snowfall Reanalysis Extraction", "used_by_model": "Demand, Travel Time, Shortage"},
        {"table_name": "weather_processed.csv", "column_name": "snowfall_proxy_cm", "description": "Fallback synthetic snowfall proxy from precipitation & freezing temperature", "data_type": "float", "unit": "cm/day", "source_name": "Synthetic Fallback", "source_url": "N/A", "source_type": "SYNTHETIC", "generation_method": "precip * 1.0 when temp_adj <= 0.5 C", "used_by_model": "Fallback Comparison"},
        {"table_name": "weather_processed.csv", "column_name": "snowfall_cm", "description": "Operational daily snowfall accumulation", "data_type": "float", "unit": "cm/day", "source_name": "ECMWF ERA5-Land (with proxy fallback)", "source_url": "https://cds.climate.copernicus.eu/", "source_type": "PUBLIC_REAL", "generation_method": "ERA5-Land primary", "used_by_model": "Demand, Travel Time, Shortage"},
        {"table_name": "weather_processed.csv", "column_name": "rainfall_3d", "description": "3-day rolling precipitation accumulation", "data_type": "float", "unit": "mm", "source_name": "NASA POWER", "source_url": "https://power.larc.nasa.gov/", "source_type": "DERIVED", "generation_method": "Rolling sum window=3", "used_by_model": "Shortage, Travel Time, Disruptions"},
        {"table_name": "weather_processed.csv", "column_name": "rainfall_7d", "description": "7-day rolling precipitation accumulation", "data_type": "float", "unit": "mm", "source_name": "NASA POWER", "source_url": "https://power.larc.nasa.gov/", "source_type": "DERIVED", "generation_method": "Rolling sum window=7", "used_by_model": "Shortage, Demand"},
        {"table_name": "weather_processed.csv", "column_name": "temperature_7d_avg", "description": "7-day rolling average temperature", "data_type": "float", "unit": "deg C", "source_name": "NASA POWER", "source_url": "https://power.larc.nasa.gov/", "source_type": "DERIVED", "generation_method": "Rolling mean window=7", "used_by_model": "Demand Forecasting"},
        {"table_name": "weather_processed.csv", "column_name": "weather_severity", "description": "Composite normalized weather severity index (weights sum to 1.00)", "data_type": "float [0.0 - 1.0]", "unit": "index", "source_name": "NASA POWER + ERA5 + DEM", "source_url": "N/A", "source_type": "DERIVED", "generation_method": "0.25*Cold + 0.20*Heat + 0.25*Rain + 0.20*Snow + 0.10*Wind", "used_by_model": "All Models"},
        {"table_name": "weather_processed.csv", "column_name": "extreme_weather_indicator", "description": "Binary flag for multi-hazard severe weather conditions", "data_type": "integer [0, 1]", "unit": "binary flag", "source_name": "Composite Environmental", "source_url": "N/A", "source_type": "DERIVED", "generation_method": "Multi-hazard threshold rule on severity and extreme metrics", "used_by_model": "All Models"},

        # Terrain Features
        {"table_name": "terrain_features.csv", "column_name": "node_id", "description": "Unique identifier of fictional logistics node", "data_type": "string", "unit": "identifier", "source_name": "Simulation", "source_url": "N/A", "source_type": "SYNTHETIC", "generation_method": "Config Hierarchy", "used_by_model": "All Models"},
        {"table_name": "terrain_features.csv", "column_name": "elevation_m", "description": "Elevation above mean sea level", "data_type": "float", "unit": "metres", "source_name": "Copernicus DEM (GLO-90)", "source_url": "https://dataspace.copernicus.eu/", "source_type": "PUBLIC_REAL", "generation_method": "DEM 90m Sampling", "used_by_model": "Travel Time, Demand, Shortage"},
        {"table_name": "terrain_features.csv", "column_name": "slope_degree", "description": "Approximate terrain gradient slope", "data_type": "float", "unit": "degrees", "source_name": "Copernicus DEM (GLO-90)", "source_url": "https://dataspace.copernicus.eu/", "source_type": "DERIVED", "generation_method": "Finite difference spatial elevation derivative", "used_by_model": "Travel Time"},
        {"table_name": "terrain_features.csv", "column_name": "terrain_difficulty", "description": "Composite terrain difficulty score", "data_type": "float [0.0 - 1.0]", "unit": "index", "source_name": "Copernicus DEM (GLO-90)", "source_url": "https://dataspace.copernicus.eu/", "source_type": "DERIVED", "generation_method": "Normalized altitude, slope, and variance combination", "used_by_model": "All Models"},
        {"table_name": "terrain_features.csv", "column_name": "terrain_type", "description": "Biogeographical terrain classification", "data_type": "string", "unit": "category", "source_name": "Geographical Reference", "source_url": "N/A", "source_type": "PUBLIC_REAL", "generation_method": "Regional Classification", "used_by_model": "All Models"},

        # Road Network Features
        {"table_name": "road_network_features.csv", "column_name": "route_id", "description": "Unique identifier of public transportation link", "data_type": "string", "unit": "identifier", "source_name": "OSM / Simulation", "source_url": "https://www.openstreetmap.org/", "source_type": "DERIVED", "generation_method": "Graph Topology Node Pair", "used_by_model": "Travel Time, Shipments"},
        {"table_name": "road_network_features.csv", "column_name": "distance_km", "description": "Public driving distance along highway", "data_type": "float", "unit": "km", "source_name": "OpenStreetMap / OSRM", "source_url": "https://www.openstreetmap.org/", "source_type": "PUBLIC_REAL", "generation_method": "OSRM Routing & Road Network Extraction", "used_by_model": "Travel Time Prediction"},
        {"table_name": "road_network_features.csv", "column_name": "elevation_change_m", "description": "Absolute elevation delta between endpoints", "data_type": "float", "unit": "metres", "source_name": "Copernicus DEM (GLO-90)", "source_url": "https://dataspace.copernicus.eu/", "source_type": "DERIVED", "generation_method": "|dest_elevation - source_elevation|", "used_by_model": "Travel Time Prediction"},
        {"table_name": "road_network_features.csv", "column_name": "road_connectivity", "description": "Average topological degree of route endpoints", "data_type": "float", "unit": "count", "source_name": "NetworkX Analysis", "source_url": "N/A", "source_type": "DERIVED", "generation_method": "Graph Degree Centrality", "used_by_model": "Travel Time, Shortage"},
        {"table_name": "road_network_features.csv", "column_name": "alternative_path_count", "description": "Redundant paths available between nodes", "data_type": "integer", "unit": "count", "source_name": "NetworkX Analysis", "source_url": "N/A", "source_type": "DERIVED", "generation_method": "Graph Simple Paths Cutoff=4", "used_by_model": "Travel Time, Route Reliability"},
        {"table_name": "road_network_features.csv", "column_name": "route_accessibility", "description": "Composite accessibility score based on road class & lanes", "data_type": "float [0.0 - 1.0]", "unit": "index", "source_name": "OSM / DEM", "source_url": "N/A", "source_type": "DERIVED", "generation_method": "Weighted lanes, surface, terrain difficulty formula", "used_by_model": "Shortage, Travel Time"},
        {"table_name": "road_network_features.csv", "column_name": "route_reliability", "description": "Baseline route reliability score", "data_type": "float [0.0 - 1.0]", "unit": "index", "source_name": "OSM / DEM / NetworkX", "source_url": "N/A", "source_type": "DERIVED", "generation_method": "Accessibility + Redundancy factor", "used_by_model": "Travel Time, Shortage Risk"},

        # Synthetic Nodes
        {"table_name": "nodes.csv", "column_name": "node_id", "description": "Fictional node identifier (e.g. LAD-A01)", "data_type": "string", "unit": "identifier", "source_name": "Simulation", "source_url": "N/A", "source_type": "SYNTHETIC", "generation_method": "Synthetic Fictional Designation", "used_by_model": "All Models"},
        {"table_name": "nodes.csv", "column_name": "storage_capacity_kg", "description": "Total warehouse payload storage capacity", "data_type": "float", "unit": "kg", "source_name": "Simulation", "source_url": "N/A", "source_type": "SYNTHETIC", "generation_method": "Assigned by node strategic role hierarchy", "used_by_model": "Inventory, Shortage"},
        {"table_name": "nodes.csv", "column_name": "criticality_level", "description": "Strategic priority level (1=lowest, 5=highest)", "data_type": "integer [1-5]", "unit": "score", "source_name": "Simulation", "source_url": "N/A", "source_type": "SYNTHETIC", "generation_method": "Role Hierarchy", "used_by_model": "Shortage Risk"},

        # Synthetic Demand
        {"table_name": "demand.csv", "column_name": "final_demand", "description": "Simulated daily demand quantity", "data_type": "float", "unit": "kg/day", "source_name": "Simulation", "source_url": "N/A", "source_type": "SYNTHETIC", "generation_method": "Causal formula: Base * Season * Temp * Weather * Scenario + Noise", "used_by_model": "Demand Forecasting"},
        {"table_name": "demand.csv", "column_name": "actual_consumption", "description": "Actual daily supply consumed", "data_type": "float", "unit": "kg/day", "source_name": "Simulation", "source_url": "N/A", "source_type": "SYNTHETIC", "generation_method": "final_demand * consumption_ratio", "used_by_model": "Inventory, Shortage"},

        # Synthetic Inventory
        {"table_name": "inventory.csv", "column_name": "opening_inventory", "description": "Stock on hand at start of day", "data_type": "float", "unit": "kg", "source_name": "Simulation", "source_url": "N/A", "source_type": "SYNTHETIC", "generation_method": "Closing inventory of day t-1", "used_by_model": "Shortage Risk"},
        {"table_name": "inventory.csv", "column_name": "received_quantity", "description": "Supplies received via arrived shipments", "data_type": "float", "unit": "kg", "source_name": "Simulation", "source_url": "N/A", "source_type": "SYNTHETIC", "generation_method": "Sum of arrived shipments on date", "used_by_model": "Inventory, Shortage"},
        {"table_name": "inventory.csv", "column_name": "closing_inventory", "description": "Stock on hand at close of day", "data_type": "float", "unit": "kg", "source_name": "Simulation", "source_url": "N/A", "source_type": "SYNTHETIC", "generation_method": "opening + received - consumed", "used_by_model": "Inventory, Shortage"},
        {"table_name": "inventory.csv", "column_name": "days_of_supply", "description": "Estimated remaining days of supply", "data_type": "float", "unit": "days", "source_name": "Simulation", "source_url": "N/A", "source_type": "SYNTHETIC", "generation_method": "closing_inventory / consumption", "used_by_model": "Shortage Risk"},
        {"table_name": "inventory.csv", "column_name": "shortage_flag", "description": "Indicator of stock depletion or critical threshold breach", "data_type": "integer [0, 1]", "unit": "binary flag", "source_name": "Simulation", "source_url": "N/A", "source_type": "SYNTHETIC", "generation_method": "1 if closing <= critical_threshold else 0", "used_by_model": "Shortage Risk Target"},

        # Synthetic Fleet
        {"table_name": "fleet.csv", "column_name": "vehicle_id", "description": "Abstract vehicle identifier", "data_type": "string", "unit": "identifier", "source_name": "Simulation", "source_url": "N/A", "source_type": "SYNTHETIC", "generation_method": "Synthetic Class Identifier", "used_by_model": "Shipments, Travel Time"},
        {"table_name": "fleet.csv", "column_name": "capacity_kg", "description": "Maximum physical cargo payload capacity", "data_type": "float", "unit": "kg", "source_name": "Simulation", "source_url": "N/A", "source_type": "SYNTHETIC", "generation_method": "Abstract class specification (2500, 7500, 16000)", "used_by_model": "Shipments, Travel Time"},

        # Synthetic Shipments
        {"table_name": "shipments.csv", "column_name": "shipment_id", "description": "Unique shipment identifier", "data_type": "string", "unit": "identifier", "source_name": "Simulation", "source_url": "N/A", "source_type": "SYNTHETIC", "generation_method": "Sequential ID", "used_by_model": "Travel Time Prediction"},
        {"table_name": "shipments.csv", "column_name": "planned_travel_time_hr", "description": "Scheduled travel time based on road & vehicle speed", "data_type": "float", "unit": "hours", "source_name": "Simulation", "source_url": "N/A", "source_type": "SYNTHETIC", "generation_method": "normal_travel_time / vehicle_speed_factor", "used_by_model": "Travel Time Feature"},
        {"table_name": "shipments.csv", "column_name": "actual_travel_time_hr", "description": "Realized travel time including weather, terrain, and disruption delays", "data_type": "float", "unit": "hours", "source_name": "Simulation", "source_url": "N/A", "source_type": "SYNTHETIC", "generation_method": "planned_travel_time * env_mult * terrain_mult * dis_mult", "used_by_model": "Travel Time Target"},
        {"table_name": "shipments.csv", "column_name": "delay_hours", "description": "Total shipment delay beyond schedule", "data_type": "float", "unit": "hours", "source_name": "Simulation", "source_url": "N/A", "source_type": "SYNTHETIC", "generation_method": "max(0, actual_arrival - planned_arrival)", "used_by_model": "Evaluation"},

        # Synthetic Disruptions
        {"table_name": "disruptions.csv", "column_name": "event_id", "description": "Unique disruption event identifier", "data_type": "string", "unit": "identifier", "source_name": "Simulation", "source_url": "N/A", "source_type": "SYNTHETIC", "generation_method": "Sequential ID", "used_by_model": "Travel Time, Shipments"},
        {"table_name": "disruptions.csv", "column_name": "event_type", "description": "High-level non-sensitive disruption type", "data_type": "string", "unit": "category", "source_name": "Simulation", "source_url": "N/A", "source_type": "SYNTHETIC", "generation_method": "Conditioned on weather thresholds and background probability", "used_by_model": "Travel Time, Shipments"},
        {"table_name": "disruptions.csv", "column_name": "travel_time_multiplier", "description": "Factor by which route travel time increases during event", "data_type": "float [1.0 - 6.0]", "unit": "multiplier", "source_name": "Simulation", "source_url": "N/A", "source_type": "SYNTHETIC", "generation_method": "Conditioned on event severity", "used_by_model": "Travel Time Feature"},

        # Training Demand
        {"table_name": "demand_training.csv", "column_name": "demand_next_day", "description": "Target: Next-day demand (t+1)", "data_type": "float", "unit": "kg/day", "source_name": "Simulation", "source_url": "N/A", "source_type": "SYNTHETIC", "generation_method": "shift(-1) on final_demand", "used_by_model": "Demand Model Target 1"},
        {"table_name": "demand_training.csv", "column_name": "demand_next_7_days", "description": "Target: Cumulative next 7 days demand (t+1 to t+7)", "data_type": "float", "unit": "kg/7-days", "source_name": "Simulation", "source_url": "N/A", "source_type": "SYNTHETIC", "generation_method": "rolling sum window=7 on shift(-1)", "used_by_model": "Demand Model Target 2"},
        {"table_name": "demand_training.csv", "column_name": "lag_1", "description": "Demand from previous day (t-1)", "data_type": "float", "unit": "kg/day", "source_name": "Simulation", "source_url": "N/A", "source_type": "SYNTHETIC", "generation_method": "shift(1) on final_demand", "used_by_model": "Demand Feature"},

        # Training Shortage
        {"table_name": "shortage_risk_training.csv", "column_name": "shortage_in_next_7_days", "description": "Target: Binary flag if shortage occurs within next 7 days", "data_type": "integer [0, 1]", "unit": "binary label", "source_name": "Simulation", "source_url": "N/A", "source_type": "SYNTHETIC", "generation_method": "max(shortage_flag[t+1 : t+7])", "used_by_model": "Shortage Risk Model Target"}
    ]
    
def generate_provenance_audit() -> pd.DataFrame:
    """
    Generate comprehensive provenance_audit.csv tracking all columns, sources,
    causal real-input dependencies, and explicit synthetic assumptions.
    """
    audit_records = [
        # weather_processed.csv
        {"table": "weather_processed.csv", "column": "date", "type": "PUBLIC_REAL", "source": "NASA POWER", "source_url": "https://power.larc.nasa.gov/", "generation_rule": "Direct daily date index", "real_input_dependency": "Observation date", "assumption": "None", "notes": "Temporal anchor for all 15 node simulations (2022-2024)"},
        {"table": "weather_processed.csv", "column": "node_id", "type": "SYNTHETIC", "source": "Configuration", "source_url": "N/A", "generation_rule": "Fictional node identifier mapping to study coordinate", "real_input_dependency": "Study node coordinate", "assumption": "Fictional node designation mapped to civilian point", "notes": "No real military installation used"},
        {"table": "weather_processed.csv", "column": "region", "type": "PUBLIC_REAL", "source": "Civilian Geography", "source_url": "N/A", "generation_rule": "Geographical biome category (Ladakh, Sikkim, Rajasthan)", "real_input_dependency": "Geographical domain", "assumption": "None", "notes": "3 distinct biomes with contrasting topoclimates"},
        {"table": "weather_processed.csv", "column": "latitude", "type": "PUBLIC_REAL", "source": "Civilian Reference Coordinate", "source_url": "N/A", "generation_rule": "Public civilian study node latitude", "real_input_dependency": "WGS84 Coordinate", "assumption": "None", "notes": "Civilian public corridor point"},
        {"table": "weather_processed.csv", "column": "longitude", "type": "PUBLIC_REAL", "source": "Civilian Reference Coordinate", "source_url": "N/A", "generation_rule": "Public civilian study node longitude", "real_input_dependency": "WGS84 Coordinate", "assumption": "None", "notes": "Civilian public corridor point"},
        {"table": "weather_processed.csv", "column": "temperature_c", "type": "PUBLIC_REAL", "source": "NASA POWER (CERES/MERRA-2)", "source_url": "https://power.larc.nasa.gov/", "generation_rule": "Direct daily mean 2-meter air temperature (T2M)", "real_input_dependency": "NASA POWER T2M", "assumption": "None", "notes": "Raw observed public temperature, untouched"},
        {"table": "weather_processed.csv", "column": "temperature_max_c", "type": "PUBLIC_REAL", "source": "NASA POWER (CERES/MERRA-2)", "source_url": "https://power.larc.nasa.gov/", "generation_rule": "Direct daily max 2-meter air temperature (T2M_MAX)", "real_input_dependency": "NASA POWER T2M_MAX", "assumption": "None", "notes": "Raw observed public maximum temperature"},
        {"table": "weather_processed.csv", "column": "temperature_min_c", "type": "PUBLIC_REAL", "source": "NASA POWER (CERES/MERRA-2)", "source_url": "https://power.larc.nasa.gov/", "generation_rule": "Direct daily min 2-meter air temperature (T2M_MIN)", "real_input_dependency": "NASA POWER T2M_MIN", "assumption": "None", "notes": "Raw observed public minimum temperature"},
        {"table": "weather_processed.csv", "column": "precipitation_mm", "type": "PUBLIC_REAL", "source": "NASA POWER (CERES/MERRA-2)", "source_url": "https://power.larc.nasa.gov/", "generation_rule": "Direct daily corrected precipitation (PRECTOTCORR)", "real_input_dependency": "NASA POWER PRECTOTCORR", "assumption": "None", "notes": "Raw observed public precipitation"},
        {"table": "weather_processed.csv", "column": "wind_speed_kmh", "type": "DERIVED", "source": "NASA POWER (CERES/MERRA-2)", "source_url": "https://power.larc.nasa.gov/", "generation_rule": "WS10M * 3.6 (m/s to km/h conversion)", "real_input_dependency": "NASA POWER WS10M", "assumption": "Linear standard unit conversion", "notes": "Derived physical variable"},
        {"table": "weather_processed.csv", "column": "relative_humidity_pct", "type": "PUBLIC_REAL", "source": "NASA POWER (CERES/MERRA-2)", "source_url": "https://power.larc.nasa.gov/", "generation_rule": "Direct daily relative humidity at 2m (RH2M)", "real_input_dependency": "NASA POWER RH2M", "assumption": "None", "notes": "Raw observed public humidity"},
        {"table": "weather_processed.csv", "column": "snowfall_era5_cm", "type": "PUBLIC_REAL", "source": "ECMWF ERA5-Land Reanalysis", "source_url": "https://cds.climate.copernicus.eu/", "generation_rule": "Daily snowfall water equivalent / accumulation from 9km ERA5-Land reanalysis", "real_input_dependency": "ERA5-Land snowfall_sum", "assumption": "Reanalysis model physical assimilation", "notes": "Public reanalysis snowfall"},
        {"table": "weather_processed.csv", "column": "snowfall_proxy_cm", "type": "SYNTHETIC", "source": "Physical Fallback Rule", "source_url": "N/A", "generation_rule": "np.where(temp_adj <= 0.5, precip_mm * 1.0, 0.0)", "real_input_dependency": "temperature_elevation_adjusted_c, precipitation_mm", "assumption": "SYNTHETIC ASSUMPTION: 1mm liquid precipitation yields 1cm fresh snow below 0.5 deg C", "notes": "Derived synthetic proxy; explicitly documented as fallback"},
        {"table": "weather_processed.csv", "column": "snowfall_cm", "type": "PUBLIC_REAL", "source": "ECMWF ERA5-Land Reanalysis (with synthetic fallback)", "source_url": "https://cds.climate.copernicus.eu/", "generation_rule": "Prefers ERA5-Land snowfall reanalysis; falls back to proxy if ERA5 unavailable", "real_input_dependency": "snowfall_era5_cm / snowfall_proxy_cm", "assumption": "Reanalysis primary", "notes": "Operational snowfall variable"},
        {"table": "weather_processed.csv", "column": "temperature_elevation_adjusted_c", "type": "DERIVED", "source": "NASA POWER + Copernicus DEM", "source_url": "https://power.larc.nasa.gov/", "generation_rule": "temperature_c - 0.0065 * (elevation_node - elevation_ref)", "real_input_dependency": "temperature_c, elevation_m", "assumption": "Standard atmospheric lapse rate of 6.5 deg C / 1000m altitude delta", "notes": "Derived topoclimatic adjustment; raw temperature preserved separately"},
        {"table": "weather_processed.csv", "column": "weather_severity", "type": "DERIVED", "source": "NASA POWER + ERA5-Land + Copernicus DEM", "source_url": "N/A", "generation_rule": "0.25*ColdPenalty + 0.20*HeatPenalty + 0.25*RainPenalty + 0.20*SnowPenalty + 0.10*WindPenalty", "real_input_dependency": "temperature_elevation_adjusted_c, precipitation_mm, snowfall_cm, wind_speed_kmh", "assumption": "Multi-hazard domain penalty weights summing strictly to 1.00", "notes": "Normalized index in [0.0, 1.0]; recomputed and verified by automated consistency test"},
        {"table": "weather_processed.csv", "column": "extreme_weather_indicator", "type": "DERIVED", "source": "Composite Environmental", "source_url": "N/A", "generation_rule": "(weather_severity >= 0.65) | (temp <= -18) | (temp >= 44) | (precip >= 35) | (snow >= 10) | (wind >= 50)", "real_input_dependency": "weather_severity, temperature, precipitation, snowfall, wind", "assumption": "Domain multi-hazard threshold rules", "notes": "Binary extreme event flag"},

        # terrain_features.csv
        {"table": "terrain_features.csv", "column": "node_id", "type": "SYNTHETIC", "source": "Configuration", "source_url": "N/A", "generation_rule": "Study node identifier", "real_input_dependency": "Node coordinate", "assumption": "Fictional designation", "notes": "Fictional identifier"},
        {"table": "terrain_features.csv", "column": "elevation_m", "type": "PUBLIC_REAL", "source": "Copernicus DEM (GLO-90)", "source_url": "https://dataspace.copernicus.eu/", "generation_rule": "Direct 90m DEM sampling at node coordinate", "real_input_dependency": "Copernicus DEM", "assumption": "None", "notes": "Real public topographic elevation"},
        {"table": "terrain_features.csv", "column": "slope_degree", "type": "DERIVED", "source": "Copernicus DEM (GLO-90)", "source_url": "https://dataspace.copernicus.eu/", "generation_rule": "Finite difference spatial elevation derivative over surrounding grid", "real_input_dependency": "Copernicus DEM 90m grid", "assumption": "Local terrain gradient approximation", "notes": "Real terrain derivative"},
        {"table": "terrain_features.csv", "column": "terrain_difficulty", "type": "DERIVED", "source": "Copernicus DEM (GLO-90)", "source_url": "https://dataspace.copernicus.eu/", "generation_rule": "0.45*(elev/5500) + 0.35*(slope/40) + 0.20*(elev_std/150)", "real_input_dependency": "elevation_m, slope_degree, elevation_std_local_m", "assumption": "Composite ruggedness weighting formula", "notes": "Normalized terrain score [0.0, 1.0]"},
        {"table": "terrain_features.csv", "column": "terrain_type", "type": "PUBLIC_REAL", "source": "Biogeographical Survey", "source_url": "N/A", "generation_rule": "Regional biome classification (High-Altitude Mountain, Mountainous Foothill, Arid Desert)", "real_input_dependency": "Geographical region", "assumption": "None", "notes": "Real biome classification"},

        # road_network_features.csv
        {"table": "road_network_features.csv", "column": "route_id", "type": "SYNTHETIC", "source": "Simulation", "source_url": "N/A", "generation_rule": "Synthetic corridor route pair", "real_input_dependency": "Node topology", "assumption": "Fictional route identifier", "notes": "Connects study nodes"},
        {"table": "road_network_features.csv", "column": "distance_km", "type": "PUBLIC_REAL", "source": "OpenStreetMap / OSRM", "source_url": "https://www.openstreetmap.org/", "generation_rule": "Real road network driving distance along public highways", "real_input_dependency": "OSM Highway Geometry", "assumption": "Public highway routing", "notes": "Real public road distance"},
        {"table": "road_network_features.csv", "column": "elevation_change_m", "type": "DERIVED", "source": "Copernicus DEM (GLO-90)", "source_url": "https://dataspace.copernicus.eu/", "generation_rule": "abs(dest_elevation - source_elevation)", "real_input_dependency": "elevation_m", "assumption": "Endpoint vertical delta", "notes": "Topographic gradient"},
        {"table": "road_network_features.csv", "column": "road_classification", "type": "PUBLIC_REAL", "source": "OpenStreetMap", "source_url": "https://www.openstreetmap.org/", "generation_rule": "OSM highway classification tag (Primary National Highway, Secondary Link, Mountain Pass)", "real_input_dependency": "OSM highway tags", "assumption": "None", "notes": "Real public road class"},
        {"table": "road_network_features.csv", "column": "normal_travel_time_hr", "type": "DERIVED", "source": "OSM + Copernicus DEM", "source_url": "https://www.openstreetmap.org/", "generation_rule": "distance_km / effective_speed_kmh (speed penalized by slope)", "real_input_dependency": "distance_km, slope_degree, road_classification", "assumption": "PROTOTYPE MODELLING ASSUMPTION: baseline transit speed by road class and slope penalty", "notes": "Ideal baseline transit duration"},
        {"table": "road_network_features.csv", "column": "route_accessibility", "type": "DERIVED", "source": "OSM + Copernicus DEM", "source_url": "N/A", "generation_rule": "0.40*surface_weight + 0.30*lane_weight + 0.30*(1 - 0.5*terrain_diff)", "real_input_dependency": "surface_type, lanes, terrain_difficulty", "assumption": "PROTOTYPE MODELLING ASSUMPTION: accessibility index combining infrastructure & terrain", "notes": "Normalized accessibility [0.0, 1.0]"},
        {"table": "road_network_features.csv", "column": "route_reliability", "type": "DERIVED", "source": "OSM + NetworkX Graph Analysis", "source_url": "N/A", "generation_rule": "route_accessibility * 0.85 + min(0.15, (alternative_path_count - 1) * 0.05)", "real_input_dependency": "route_accessibility, alternative_path_count", "assumption": "PROTOTYPE MODELLING ASSUMPTION: reliability enhanced by topological redundancy", "notes": "Normalized reliability [0.0, 1.0]"},

        # nodes.csv
        {"table": "nodes.csv", "column": "storage_capacity_kg", "type": "SYNTHETIC", "source": "Simulation", "source_url": "N/A", "generation_rule": "Assigned based on node strategic role (Main Hub=250t, Depot=180t, Forward Base=90t, Post=35t)", "real_input_dependency": "Node role hierarchy", "assumption": "SYNTHETIC ASSUMPTION: fictional warehouse payload storage capacity hierarchy", "notes": "Prototype warehouse capacity"},
        {"table": "nodes.csv", "column": "criticality_level", "type": "SYNTHETIC", "source": "Simulation", "source_url": "N/A", "generation_rule": "Assigned based on node strategic tier (1 to 5)", "real_input_dependency": "Node role hierarchy", "assumption": "SYNTHETIC ASSUMPTION: strategic priority scoring", "notes": "Priority classification"},

        # demand.csv
        {"table": "demand.csv", "column": "final_demand", "type": "SYNTHETIC", "source": "Conditioned Simulation", "source_url": "N/A", "generation_rule": "Base * Season * Temp_Factor * Weather_Factor * Trend * Scenario + Noise", "real_input_dependency": "temperature_elevation_adjusted_c, precipitation_mm, snowfall_cm, weather_severity", "assumption": "SYNTHETIC ASSUMPTION: fuel consumption surges in sub-zero cold (+3.5%/deg below 0C); water demand surges in heat (+3.0%/deg above 30C)", "notes": "Daily simulated demand causally grounded in real weather"},
        {"table": "demand.csv", "column": "actual_consumption", "type": "SYNTHETIC", "source": "Conditioned Simulation", "source_url": "N/A", "generation_rule": "final_demand * consumption_ratio (ratio sampled from Beta(15, 2))", "real_input_dependency": "final_demand", "assumption": "SYNTHETIC ASSUMPTION: stochastic consumption variance centered at 88% of demand", "notes": "Realized daily supply depletion"},

        # fleet.csv
        {"table": "fleet.csv", "column": "capacity_kg", "type": "SYNTHETIC", "source": "Simulation", "source_url": "N/A", "generation_rule": "Abstract vehicle class payload (Light=2500kg, Medium=7500kg, Heavy=16000kg)", "real_input_dependency": "Vehicle class", "assumption": "SYNTHETIC ASSUMPTION: abstract civilian logistics vehicle payload specifications", "notes": "No real military unit or vehicle roster used"},
        {"table": "fleet.csv", "column": "weather_resilience", "type": "SYNTHETIC", "source": "Simulation", "source_url": "N/A", "generation_rule": "Vehicle class weather attenuation factor (0.70 to 0.90)", "real_input_dependency": "Vehicle class", "assumption": "SYNTHETIC ASSUMPTION: 4x4 and heavy platforms have higher adverse weather resilience", "notes": "Environmental friction tolerance"},

        # disruptions.csv
        {"table": "disruptions.csv", "column": "event_type", "type": "SYNTHETIC", "source": "Conditioned Simulation", "source_url": "N/A", "generation_rule": "Triggered by physical environmental thresholds (landslide if rain>=25mm & slope>=12; blizzard if snow>=6cm & temp<=-5C; heatwave if temp>=42C; flash flood if rain>=35mm)", "real_input_dependency": "temperature_elevation_adjusted_c, precipitation_mm, snowfall_cm, wind_speed_kmh, slope_degree", "assumption": "SYNTHETIC ASSUMPTION: empirical threshold rules triggering non-sensitive hazard events", "notes": "Conditioned natural & mechanical disruption events"},
        {"table": "disruptions.csv", "column": "travel_time_multiplier", "type": "SYNTHETIC", "source": "Conditioned Simulation", "source_url": "N/A", "generation_rule": "Conditioned on event severity and type (Uniform 1.3 to 5.0)", "real_input_dependency": "event_type, severity", "assumption": "SYNTHETIC ASSUMPTION: severe landslides and blizzards impose 2.5x - 5.0x transit duration inflation", "notes": "Delay multiplier on route transit"},

        # shipments.csv
        {"table": "shipments.csv", "column": "actual_travel_time_hr", "type": "SYNTHETIC", "source": "Conditioned Simulation", "source_url": "N/A", "generation_rule": "planned_travel_time * env_multiplier * terrain_multiplier * disruption_multiplier + dispatch_delay + noise", "real_input_dependency": "distance_km, terrain_difficulty, weather_severity, route disruptions", "assumption": "SYNTHETIC ASSUMPTION: multiplicative travel-time friction compounding terrain, weather, vehicle resilience, and active disruptions", "notes": "Realized transit duration for convoy movements"},
        {"table": "shipments.csv", "column": "delay_hours", "type": "SYNTHETIC", "source": "Conditioned Simulation", "source_url": "N/A", "generation_rule": "max(0.0, actual_travel_time_hr - planned_travel_time_hr)", "real_input_dependency": "actual_travel_time_hr, planned_travel_time_hr", "assumption": "Accounting definition", "notes": "Shipment delay beyond baseline schedule"},

        # inventory.csv
        {"table": "inventory.csv", "column": "opening_inventory", "type": "SYNTHETIC", "source": "Conditioned Simulation", "source_url": "N/A", "generation_rule": "Closing inventory of day t-1 for node and supply category", "real_input_dependency": "Prior day stock state", "assumption": "Strict physical mass conservation", "notes": "No supply creation or disappearance"},
        {"table": "inventory.csv", "column": "received_quantity", "type": "SYNTHETIC", "source": "Conditioned Simulation", "source_url": "N/A", "generation_rule": "Sum of quantity delivered by shipments arriving on date t at node", "real_input_dependency": "Shipment arrival timestamps", "assumption": "Replenishment added to stock upon verified arrival", "notes": "Material inflow"},
        {"table": "inventory.csv", "column": "closing_inventory", "type": "SYNTHETIC", "source": "Conditioned Simulation", "source_url": "N/A", "generation_rule": "max(0.0, opening_inventory + received_quantity - actual_consumption)", "real_input_dependency": "opening_inventory, received_quantity, actual_consumption", "assumption": "Strict mass balance conservation law", "notes": "Stock on hand at end of day"},
        {"table": "inventory.csv", "column": "shortage_flag", "type": "SYNTHETIC", "source": "Conditioned Simulation", "source_url": "N/A", "generation_rule": "1 if closing_inventory <= critical_threshold else 0", "real_input_dependency": "closing_inventory, storage_capacity_kg", "assumption": "SYNTHETIC ASSUMPTION: critical threshold defined at 15% of warehouse capacity", "notes": "Binary stock-out indicator"},

        # demand_training.csv
        {"table": "demand_training.csv", "column": "demand_next_day", "type": "SYNTHETIC", "source": "Feature Pipeline", "source_url": "N/A", "generation_rule": "shift(-1) on final_demand within node and category group", "real_input_dependency": "final_demand", "assumption": "Forecasting horizon t+1", "notes": "Supervised learning target 1"},
        {"table": "demand_training.csv", "column": "demand_next_7_days", "type": "SYNTHETIC", "source": "Feature Pipeline", "source_url": "N/A", "generation_rule": "rolling sum window=7 on shift(-1) of final_demand", "real_input_dependency": "final_demand", "assumption": "Forecasting horizon cumulative t+1 to t+7", "notes": "Supervised learning target 2"},

        # travel_time_training.csv
        {"table": "travel_time_training.csv", "column": "actual_travel_time_hr", "type": "SYNTHETIC", "source": "Feature Pipeline", "source_url": "N/A", "generation_rule": "Realized transit time from shipments simulation", "real_input_dependency": "shipments.actual_travel_time_hr", "assumption": "Supervised regression target", "notes": "Travel time target"},

        # shortage_risk_training.csv
        {"table": "shortage_risk_training.csv", "column": "shortage_in_next_7_days", "type": "SYNTHETIC", "source": "Feature Pipeline", "source_url": "N/A", "generation_rule": "max(shortage_flag from t+1 to t+7) within node and category group", "real_input_dependency": "inventory.shortage_flag", "assumption": "Supervised binary classification target (7-day lookahead)", "notes": "Shortage risk target"}
    ]
    
    df = pd.DataFrame(audit_records)
    out_csv = os.path.join(METADATA_DATA_DIR, "provenance_audit.csv")
    df.to_csv(out_csv, index=False)
    logger.info(f"Saved complete provenance audit ({len(df)} records) to {out_csv}")
    return df

if __name__ == "__main__":
    generate_data_source_register()
    generate_data_dictionary()
    generate_provenance_audit()
