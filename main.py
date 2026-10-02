"""
Master Entry Point for Indian Army Predictive Logistics Data Pipeline (Phase 1).
SIH 2026 Problem Statement ID: 26251.
"""

import sys
import argparse
from data_pipeline.output.generate_pipeline import run_full_pipeline

def main():
    parser = argparse.ArgumentParser(description="Indian Army Predictive Logistics Data Foundation Pipeline")
    parser.add_argument("--refresh-raw", action="store_true", help="Force re-download of raw external datasets from APIs")
    args = parser.parse_args()

    print("\n================================================================================")
    print(" INDIAN ARMY - PREDICTIVE LOGISTICS & FORWARD SUPPLY CHAIN DECISION-SUPPORT SYSTEM")
    print(" PHASE 1: Real-World Data Acquisition + Conditioned Synthetic Simulation")
    print("================================================================================\n")
    
    result = run_full_pipeline(force_refresh_raw=args.refresh_raw)
    
    if result["status"] == "SUCCESS":
        print("\nPipeline execution finished with 100% data integrity validation.")
        sys.exit(0)
    else:
        print("\nPipeline execution encountered errors.")
        sys.exit(1)

if __name__ == "__main__":
    main()
