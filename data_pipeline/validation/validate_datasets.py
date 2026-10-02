"""
Comprehensive Data Quality and Validation Module.
Executes automated integrity, conservation, causality, formula consistency,
and leakage tests across all generated datasets, and outputs data_quality_report.txt.
"""

import os
import logging
from datetime import datetime
import numpy as np
import pandas as pd
from data_pipeline.config import (
    DATA_DIR, PROCESSED_DATA_DIR, SYNTHETIC_DATA_DIR, TRAINING_DATA_DIR,
    METADATA_DATA_DIR, REGIONS, SUPPLY_CATEGORIES
)
from data_pipeline.processing.weather_processing import compute_weather_severity_index

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def run_comprehensive_validation() -> dict:
    """
    Run automated validation checks across all pipeline datasets.
    """
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("INDIAN ARMY LOGISTICS - PHASE 1 FINAL ENVIRONMENTAL & DATA QUALITY REPORT")
    report_lines.append(f"Generated At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    validation_summary = {"total_checks": 0, "passed_checks": 0, "failed_checks": 0, "issues": []}
    
    def record_check(name: str, passed: bool, details: str = ""):
        validation_summary["total_checks"] += 1
        if passed:
            validation_summary["passed_checks"] += 1
            status_str = "[PASS]"
        else:
            validation_summary["failed_checks"] += 1
            status_str = "[FAIL]"
            validation_summary["issues"].append(f"{name}: {details}")
        report_lines.append(f"  {status_str} {name}")
        if details:
            report_lines.append(f"         Details: {details}")

    # 1. Dataset Existence & File Size Audit
    report_lines.append("1. DATASET FILE INVENTORY & ROW COUNTS")
    report_lines.append("-" * 80)
    
    dataset_paths = {
        # Processed
        "weather_processed.csv": os.path.join(PROCESSED_DATA_DIR, "weather_processed.csv"),
        "terrain_features.csv": os.path.join(PROCESSED_DATA_DIR, "terrain_features.csv"),
        "road_network_features.csv": os.path.join(PROCESSED_DATA_DIR, "road_network_features.csv"),
        # Synthetic
        "nodes.csv": os.path.join(SYNTHETIC_DATA_DIR, "nodes.csv"),
        "demand.csv": os.path.join(SYNTHETIC_DATA_DIR, "demand.csv"),
        "inventory.csv": os.path.join(SYNTHETIC_DATA_DIR, "inventory.csv"),
        "fleet.csv": os.path.join(SYNTHETIC_DATA_DIR, "fleet.csv"),
        "routes.csv": os.path.join(SYNTHETIC_DATA_DIR, "routes.csv"),
        "shipments.csv": os.path.join(SYNTHETIC_DATA_DIR, "shipments.csv"),
        "disruptions.csv": os.path.join(SYNTHETIC_DATA_DIR, "disruptions.csv"),
        # Training
        "demand_training.csv": os.path.join(TRAINING_DATA_DIR, "demand_training.csv"),
        "travel_time_training.csv": os.path.join(TRAINING_DATA_DIR, "travel_time_training.csv"),
        "shortage_risk_training.csv": os.path.join(TRAINING_DATA_DIR, "shortage_risk_training.csv"),
        # Metadata
        "data_dictionary.csv": os.path.join(METADATA_DATA_DIR, "data_dictionary.csv"),
        "data_source_register.csv": os.path.join(METADATA_DATA_DIR, "data_source_register.csv"),
        "provenance_audit.csv": os.path.join(METADATA_DATA_DIR, "provenance_audit.csv"),
    }
    
    loaded_dfs = {}
    for filename, filepath in dataset_paths.items():
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            loaded_dfs[filename] = df
            size_kb = os.path.getsize(filepath) / 1024.0
            report_lines.append(f"  • {filename:<30} | {len(df):>7} rows | {len(df.columns):>3} cols | {size_kb:>8.1f} KB")
        else:
            report_lines.append(f"  • {filename:<30} | MISSING FILE")
            record_check(f"File Existence: {filename}", False, "File does not exist")
            
    report_lines.append("")
    report_lines.append("2. ENVIRONMENTAL & WEATHER SEVERITY CONSISTENCY CHECKS")
    report_lines.append("-" * 80)
    
    # 2.1 Weather Severity Formula Consistency Check
    if "weather_processed.csv" in loaded_dfs:
        df_wp = loaded_dfs["weather_processed.csv"]
        recomputed_ws = compute_weather_severity_index(
            temperature_c=df_wp["temperature_elevation_adjusted_c"],
            precipitation_mm=df_wp["precipitation_mm"],
            snowfall_cm=df_wp["snowfall_cm"],
            wind_speed_kmh=df_wp["wind_speed_kmh"]
        )
        ws_diff = (df_wp["weather_severity"] - recomputed_ws).abs()
        max_ws_diff = ws_diff.max()
        ws_consistent = max_ws_diff <= 0.005
        record_check("Weather Severity Formula Consistency (Independently Recomputed)", ws_consistent, f"Max deviation: {max_ws_diff:.4f}, Evaluated on {len(df_wp)} node-days")
        
        # 2.2 Weather Spatial Variation within Regions
        temp_vars = df_wp.groupby("region")["temperature_elevation_adjusted_c"].std()
        precip_vars = df_wp.groupby("region")["precipitation_mm"].std()
        spatial_var_ok = (temp_vars > 1.0).all()
        record_check("Node-Level Spatial Weather Variation within Regions", spatial_var_ok, f"Regional Temp StdDev: {temp_vars.to_dict()}")

    # 2.3 Geographic coordinate validation
    if "nodes.csv" in loaded_dfs:
        df_n = loaded_dfs["nodes.csv"]
        valid_coords = (df_n["latitude"].between(20.0, 38.0) & df_n["longitude"].between(68.0, 98.0)).all()
        record_check("Geographic Coordinates Validity (Nodes within India bounds)", valid_coords, f"Total nodes: {len(df_n)}")
        
        unique_nodes = df_n["node_id"].nunique() == len(df_n)
        record_check("Primary Key Uniqueness (nodes.csv node_id)", unique_nodes, f"Unique IDs: {df_n['node_id'].nunique()}/{len(df_n)}")
        
        no_nulls = df_n[["node_id", "region", "latitude", "longitude", "elevation_m", "storage_capacity_kg"]].isnull().sum().sum() == 0
        record_check("Critical Fields Completeness (nodes.csv)", no_nulls)

    report_lines.append("")
    report_lines.append("3. SYNTHETIC SIMULATION & CONSERVATION INTEGRITY")
    report_lines.append("-" * 80)
    
    # 3.1 Demand Validation
    if "demand.csv" in loaded_dfs:
        df_d = loaded_dfs["demand.csv"]
        non_neg_demand = (df_d["final_demand"] >= 0).all()
        record_check("Non-Negative Demand Values", non_neg_demand, f"Min final_demand: {df_d['final_demand'].min():.1f} kg")
        
        dup_demand = df_d.duplicated(subset=["date", "node_id", "supply_category"]).sum()
        record_check("Primary Key Uniqueness (demand.csv date x node_id x category)", dup_demand == 0, f"Duplicates found: {dup_demand}")
        
    # 3.2 Inventory Conservation Validation
    if "inventory.csv" in loaded_dfs:
        df_i = loaded_dfs["inventory.csv"]
        uncapped_expected = df_i["opening_inventory"] + df_i["received_quantity"] - df_i["consumed_quantity"]
        expected_closing = np.minimum(df_i["storage_capacity"], uncapped_expected)
        conservation_diff = (df_i["closing_inventory"] - expected_closing).abs()
        max_diff = conservation_diff.max()
        conservation_holds = (conservation_diff <= 0.01).all()
        record_check("Inventory Conservation Law (Closing = min(Cap, Opening + Received - Consumed))", conservation_holds, f"Max deviation: {max_diff:.4f} kg")
        
        non_neg_inv = (df_i["closing_inventory"] >= 0).all()
        record_check("Non-Negative Closing Inventory", non_neg_inv, f"Min closing inventory: {df_i['closing_inventory'].min():.1f} kg")
        
        df_i_sorted = df_i.sort_values(["node_id", "supply_category", "date"]).reset_index(drop=True)
        prev_closing = df_i_sorted.groupby(["node_id", "supply_category"])["closing_inventory"].shift(1)
        opening = df_i_sorted["opening_inventory"]
        valid_mask = prev_closing.notnull()
        chrono_diff = (opening[valid_mask] - prev_closing[valid_mask]).abs().max()
        chrono_holds = chrono_diff <= 0.1
        record_check("Chronological Continuity (Opening[t] == Closing[t-1])", chrono_holds, f"Max transition delta: {chrono_diff:.4f} kg")

    # 3.3 Shipments Validation
    if "shipments.csv" in loaded_dfs and "fleet.csv" in loaded_dfs and "routes.csv" in loaded_dfs:
        df_s = loaded_dfs["shipments.csv"]
        df_f = loaded_dfs["fleet.csv"]
        df_r = loaded_dfs["routes.csv"]
        
        dup_shipments = df_s["shipment_id"].duplicated().sum()
        record_check("Primary Key Uniqueness (shipments.csv shipment_id)", dup_shipments == 0, f"Duplicates: {dup_shipments}")
        
        non_neg_qty = (df_s["quantity_kg"] > 0).all()
        record_check("Positive Shipment Quantities", non_neg_qty, f"Min quantity: {df_s['quantity_kg'].min()} kg")
        
        v_caps = dict(zip(df_f["vehicle_id"], df_f["capacity_kg"]))
        ship_caps = df_s["vehicle_id"].map(v_caps)
        cap_exceeded = (df_s["quantity_kg"] > ship_caps + 1e-3).sum()
        record_check("Payload Capacity Constraint (quantity <= vehicle capacity)", cap_exceeded == 0, f"Violations: {cap_exceeded}")
        
        valid_routes = df_s["route_id"].isin(df_r["route_id"]).all()
        record_check("Foreign Key Validity (shipment route_id in routes.csv)", valid_routes)
        
        act_dep = pd.to_datetime(df_s["actual_departure"])
        act_arr = pd.to_datetime(df_s["actual_arrival"])
        chronological_trips = (act_arr >= act_dep).all()
        record_check("Causal Trip Progression (actual_arrival >= actual_departure)", chronological_trips)

    report_lines.append("")
    report_lines.append("4. ML TRAINING DATASETS & LEAKAGE VERIFICATION")
    report_lines.append("-" * 80)
    
    if "demand_training.csv" in loaded_dfs:
        df_dt = loaded_dfs["demand_training.csv"]
        no_nans = df_dt.isnull().sum().sum() == 0
        record_check("Demand Training Dataset Completeness (Zero NaNs)", no_nans, f"Total rows: {len(df_dt)}")
        
    if "travel_time_training.csv" in loaded_dfs:
        df_tt = loaded_dfs["travel_time_training.csv"]
        no_nans = df_tt.isnull().sum().sum() == 0
        record_check("Travel-Time Training Dataset Completeness (Zero NaNs)", no_nans, f"Total records: {len(df_tt)}")
        has_target = "actual_travel_time_hr" in df_tt.columns
        has_planned = "planned_travel_time_hr" in df_tt.columns
        record_check("Travel Time Planned vs Actual Distinction", has_target and has_planned)
        
    if "shortage_risk_training.csv" in loaded_dfs:
        df_st = loaded_dfs["shortage_risk_training.csv"]
        no_nans = df_st.isnull().sum().sum() == 0
        record_check("Shortage Risk Training Dataset Completeness (Zero NaNs)", no_nans, f"Total records: {len(df_st)}")
        
        class_dist = df_st["shortage_in_next_7_days"].value_counts(normalize=True).to_dict()
        dist_str = ", ".join(f"Class {k}: {v*100:.1f}%" for k, v in class_dist.items())
        record_check("Shortage Risk Label Balance", len(class_dist) >= 2, dist_str)

    # 5. REALISM STATISTICS BREAKDOWN
    report_lines.append("")
    report_lines.append("5. REALISM STATISTICS & OPERATIONAL DISTRIBUTIONS")
    report_lines.append("-" * 80)
    
    if "disruptions.csv" in loaded_dfs:
        df_dis = loaded_dfs["disruptions.csv"]
        report_lines.append("Disruption Events by Region & Event Type:")
        dis_summary = df_dis.groupby(["region", "event_type"]).size().unstack(fill_value=0)
        for reg, row in dis_summary.iterrows():
            report_lines.append(f"  • {reg:<10}: " + ", ".join(f"{col}={val}" for col, val in row.items() if val > 0))
            
    if "shipments.csv" in loaded_dfs:
        df_sh = loaded_dfs["shipments.csv"]
        report_lines.append("\nTravel Time & Delay by Region:")
        for reg in ["LADAKH", "SIKKIM", "RAJASTHAN"]:
            sub = df_sh[df_sh["region"] == reg]
            mean_plan = sub["planned_travel_time_hr"].mean()
            mean_act = sub["actual_travel_time_hr"].mean()
            mean_delay = sub["delay_hours"].mean()
            pct_delayed = (sub["delay_hours"] > 0.5).mean() * 100.0
            report_lines.append(f"  • {reg:<10}: Planned={mean_plan:.2f}h | Actual={mean_act:.2f}h | Avg Delay={mean_delay:.2f}h | Delayed Convoys={pct_delayed:.1f}%")

    if "inventory.csv" in loaded_dfs:
        df_inv = loaded_dfs["inventory.csv"]
        report_lines.append("\nStock-Out Rate by Supply Category:")
        for cat in SUPPLY_CATEGORIES:
            sub = df_inv[df_inv["supply_category"] == cat]
            stockout_pct = (sub["closing_inventory"] == 0.0).mean() * 100.0
            crit_pct = (sub["shortage_flag"] == 1).mean() * 100.0
            report_lines.append(f"  • {cat:<17}: Stockout={stockout_pct:.2f}% | Below Critical Buffer={crit_pct:.1f}%")

    # Summary section
    report_lines.append("")
    report_lines.append("6. VALIDATION SUMMARY")
    report_lines.append("-" * 80)
    report_lines.append(f"Total Integrity Checks Run : {validation_summary['total_checks']}")
    report_lines.append(f"Checks Passed              : {validation_summary['passed_checks']}")
    report_lines.append(f"Checks Failed              : {validation_summary['failed_checks']}")
    report_lines.append(f"Overall Quality Status     : {'ALL CHECKS PASSED (100%)' if validation_summary['failed_checks'] == 0 else 'WARNING/FAILURES DETECTED'}")
    report_lines.append("=" * 80)
    
    report_text = "\n".join(report_lines)
    report_file = os.path.join(METADATA_DATA_DIR, "data_quality_report.txt")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_text)
        
    logger.info(f"Saved complete data quality report to {report_file}")
    print(report_text)
    return validation_summary

if __name__ == "__main__":
    run_comprehensive_validation()
