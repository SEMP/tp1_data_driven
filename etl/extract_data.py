"""
Data extraction orchestrator.
Calls various extraction functions to prepare data for analysis.
"""

from extract_timeseries import extract_timeseries


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

    # Future extractions can be added here:
    # print("\n2. Extracting spatial data...")
    # extract_spatial()

    print("\n" + "=" * 60)
    print("EXTRACTION COMPLETE")
    print("=" * 60)
    print("Output: extracted/analysis_data.db")


if __name__ == "__main__":
    main()
