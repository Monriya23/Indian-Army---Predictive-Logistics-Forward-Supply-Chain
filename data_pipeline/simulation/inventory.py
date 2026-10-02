"""
Dynamic Inventory Simulation Module.
Enforces chronological inventory conservation:
Closing Inventory(t) = Opening Inventory(t) + Received Quantity(t) - Consumed Quantity(t)
Opening Inventory(t+1) = Closing Inventory(t)
"""

import os
import logging
import pandas as pd
from data_pipeline.config import SYNTHETIC_DATA_DIR, SUPPLY_CATEGORIES

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def simulate_chronological_inventory(
    nodes_df: pd.DataFrame,
    demand_df: pd.DataFrame,
    shipments_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Simulate daily inventory dynamics for every node and supply category chronologically.
    """
    # Group shipments by (arrival_date, destination_node, supply_category)
    shipments_copy = shipments_df.copy()
    shipments_copy["arrival_date"] = pd.to_datetime(shipments_copy["actual_arrival"]).dt.strftime("%Y-%m-%d")
    received_map = (
        shipments_copy.groupby(["arrival_date", "destination_node", "supply_category"])["quantity_kg"]
        .sum()
        .to_dict()
    )
    
    # Pre-index demand/consumption dictionary
    demand_map = {
        (r["date"], r["node_id"], r["supply_category"]): r["actual_consumption"]
        for _, r in demand_df.iterrows()
    }
    
    node_storage = dict(zip(nodes_df["node_id"], nodes_df["storage_capacity_kg"]))
    all_dates = sorted(demand_df["date"].unique())
    all_nodes = nodes_df["node_id"].tolist()
    
    category_cap_share = {"FOOD": 0.25, "WATER": 0.25, "FUEL": 0.30, "MEDICAL": 0.05, "GENERAL_SUPPLIES": 0.15}
    
    current_inventory = {}
    for n_id in all_nodes:
        total_cap = node_storage.get(n_id, 100000.0)
        for cat in SUPPLY_CATEGORIES:
            cat_cap = total_cap * category_cap_share[cat]
            current_inventory[(n_id, cat)] = round(cat_cap * 0.65, 1)
            
    inventory_records = []
    
    for d_str in all_dates:
        for n_id in all_nodes:
            total_cap = node_storage.get(n_id, 100000.0)
            
            for cat in SUPPLY_CATEGORIES:
                cat_cap = total_cap * category_cap_share[cat]
                crit_threshold = round(cat_cap * 0.20, 1)
                
                opening = current_inventory[(n_id, cat)]
                received = round(float(received_map.get((d_str, n_id, cat), 0.0)), 1)
                target_consumed = float(demand_map.get((d_str, n_id, cat), 50.0))
                
                # Physical constraint: consumption cannot exceed available stock
                available_stock = opening + received
                actual_consumed = min(available_stock, target_consumed)
                
                closing = round(available_stock - actual_consumed, 1)
                closing = min(closing, cat_cap)
                
                current_inventory[(n_id, cat)] = closing
                
                days_of_supply = round(closing / (target_consumed + 1e-3), 2)
                shortage_flag = 1 if (closing <= crit_threshold or days_of_supply < 3.0) else 0
                
                inventory_records.append({
                    "date": d_str,
                    "node_id": n_id,
                    "supply_category": cat,
                    "opening_inventory": opening,
                    "received_quantity": received,
                    "consumed_quantity": round(actual_consumed, 1),
                    "closing_inventory": closing,
                    "storage_capacity": round(cat_cap, 1),
                    "days_of_supply": days_of_supply,
                    "critical_threshold": crit_threshold,
                    "shortage_flag": shortage_flag
                })
                
    df_inv = pd.DataFrame(inventory_records)
    out_csv = os.path.join(SYNTHETIC_DATA_DIR, "inventory.csv")
    df_inv.to_csv(out_csv, index=False)
    logger.info(f"Saved synthetic inventory dataset ({len(df_inv)} records) to {out_csv}")
    return df_inv
