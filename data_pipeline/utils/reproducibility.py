"""
Reproducibility and Run Configuration Module.
Records all hyperparameters, random seeds, software environment details,
and dataset integrity checksums.
"""

import os
import sys
import json
import hashlib
import logging
from datetime import datetime
from data_pipeline.config import (
    METADATA_DATA_DIR, RANDOM_SEED, START_DATE, END_DATE,
    SUPPLY_CATEGORIES, VEHICLE_CLASSES, REGIONS, DATA_DIR
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def compute_file_sha256(filepath: str) -> str:
    """Compute SHA-256 hash of a file for integrity verification."""
    if not os.path.exists(filepath):
        return "FILE_NOT_FOUND"
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def record_reproducibility_metadata(dataset_files: dict = None) -> dict:
    """
    Save complete execution environment and dataset checksums.
    """
    metadata = {
        "project": "Indian Army - Predictive Logistics & Forward Supply Chain (SIH 2026)",
        "phase": "Phase 1 - Real-World Data Acquisition & Conditioned Synthetic Logistics Data Generation",
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "random_seed": RANDOM_SEED,
        "temporal_bounds": {
            "start_date": START_DATE,
            "end_date": END_DATE,
            "total_days_per_region": 1096
        },
        "python_environment": {
            "python_version": sys.version,
            "platform": sys.platform
        },
        "supply_categories": SUPPLY_CATEGORIES,
        "vehicle_classes": list(VEHICLE_CLASSES.keys()),
        "study_regions": [
            {"region_id": r["region_id"], "name": r["name"], "corridor": r["corridor"]}
            for r in REGIONS.values()
        ],
        "dataset_checksums": {}
    }
    
    if dataset_files:
        for name, path in dataset_files.items():
            if os.path.exists(path):
                metadata["dataset_checksums"][name] = {
                    "path": os.path.relpath(path, DATA_DIR),
                    "size_bytes": os.path.getsize(path),
                    "sha256": compute_file_sha256(path)
                }
                
    out_json = os.path.join(METADATA_DATA_DIR, "reproducibility_config.json")
    with open(out_json, "w") as f:
        json.dump(metadata, f, indent=2)
        
    logger.info(f"Saved pipeline reproducibility metadata to {out_json}")
    return metadata
