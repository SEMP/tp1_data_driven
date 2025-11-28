"""
Data extraction orchestrator.
Calls various extraction functions to prepare data for analysis.
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extract_timeseries import extract_timeseries
from extract_spatial import extract_spatial


def main():
    """
    Execute all data extraction processes.
    """
    print("=" * 60)
    print("DATA EXTRACTION")
    print("=" * 60)

    # Extract time series data
    print("\n1. Extracting time series data...")
    extract_timeseries()

    # Extract spatial data
    print("\n2. Extracting spatial data...")
    extract_spatial()

    print("\n" + "=" * 60)
    print("EXTRACTION COMPLETE")
    print("=" * 60)
    print("Output: extracted/analysis_data.db")
    print("Tables: accidents_daily, accidents_spatial")


if __name__ == "__main__":
    main()
