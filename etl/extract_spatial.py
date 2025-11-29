import sqlite3
import pandas as pd
import os

def normalize_to_float(series):
	"""
	Normalize a pandas Series to float, handling comma decimal separators.

	Converts both '3.14' and '3,14' formats to proper float values.
	Handles 'None', 'nan', and NULL values by converting to pd.NA.

	Args:
		series: pandas Series with numeric data (potentially as string)

	Returns:
		pandas Series with float values
	"""
	return (
		series
		.astype(str)
		.str.replace(',', '.', regex=False)  # 3,14 → 3.14
		.replace('None', pd.NA)
		.replace('nan', pd.NA)
		.astype(float)
	)

def extract_spatial():
	# Configuration
	SOURCE_DB = "data/datatran_raw.db"
	SOURCE_TABLE_NAME = "accidents"

	EXTRACTED_DIR = "extracted"
	TARGET_DB = os.path.join(EXTRACTED_DIR, "analysis_data.db")
	TARGET_TABLE_NAME = "accidents_spatial"

	# Create extracted directory if it doesn't exist
	os.makedirs(EXTRACTED_DIR, exist_ok=True)

	# SQL to extract spatial data with normalized dates
	# Only includes records with valid lat/long (2017-2025 data)
	query = f"""
	WITH normalized AS
	(
		SELECT
			CASE
			WHEN data_inversa LIKE '__/__/__' THEN
				'20' ||
				SUBSTR(data_inversa, 7, 2) ||
				'-' ||
				SUBSTR(data_inversa, 4, 2) ||
				'-' ||
				SUBSTR(data_inversa, 1, 2)
			WHEN data_inversa LIKE '__/__/____' THEN
				SUBSTR(data_inversa, 7, 4) ||
				'-' ||
				SUBSTR(data_inversa, 4, 2) ||
				'-' ||
				SUBSTR(data_inversa, 1, 2)
			WHEN data_inversa LIKE '____-__-__' THEN
				data_inversa
			ELSE
				NULL
			END AS date_normalized,
			uf,
			municipio,
			br,
			km,
			latitude,
			longitude
		FROM {SOURCE_TABLE_NAME}
		WHERE
			data_inversa IS NOT NULL
			AND latitude IS NOT NULL
			AND longitude IS NOT NULL
	)

	SELECT
		date_normalized AS date,
		uf,
		municipio,
		br,
		km,
		latitude,
		longitude
	FROM normalized
	WHERE date IS NOT NULL
	ORDER BY date_normalized
	;
	"""

	# Connect to the full raw database
	print("   Loading data from raw database...")

	with sqlite3.connect(SOURCE_DB) as source_db_connection:
		# First, get statistics about invalid records
		stats_query = f"""
		SELECT
			COUNT(*) as total_records,
			SUM(CASE WHEN data_inversa IS NULL THEN 1 ELSE 0 END) as null_dates,
			SUM(CASE WHEN latitude IS NULL THEN 1 ELSE 0 END) as null_latitude,
			SUM(CASE WHEN longitude IS NULL THEN 1 ELSE 0 END) as null_longitude,
			SUM(CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL THEN 1 ELSE 0 END) as with_coords
		FROM {SOURCE_TABLE_NAME}
		"""
		stats = pd.read_sql_query(stats_query, source_db_connection).iloc[0]

		print(f"\n   Database statistics:")
		print(f"   - Total records in raw DB: {stats['total_records']:,}")
		print(f"   - Records with coordinates: {stats['with_coords']:,}")
		print(f"   - Records without dates: {stats['null_dates']:,}")
		print(f"   - Records without latitude: {stats['null_latitude']:,}")
		print(f"   - Records without longitude: {stats['null_longitude']:,}")

		# Get sample of records without coordinates
		sample_no_coords_query = f"""
		SELECT data_inversa, uf, municipio, br, km, latitude, longitude
		FROM {SOURCE_TABLE_NAME}
		WHERE latitude IS NULL OR longitude IS NULL
		LIMIT 5
		"""
		sample_no_coords = pd.read_sql_query(sample_no_coords_query, source_db_connection)

		if len(sample_no_coords) > 0:
			print(f"\n   Sample of records WITHOUT coordinates (first 5):")
			print(sample_no_coords.to_string(index=False))

		# Load spatial data into DataFrame
		print(f"\n   Extracting records with valid coordinates...")
		spatial_dataframe = pd.read_sql_query(query, source_db_connection)
		print(f"   ✓ Extracted {len(spatial_dataframe):,} records")

	# Close source DB
	source_db_connection.close()

	# Data cleaning and normalization
	print("\n   Cleaning and normalizing numeric fields...")

	# 1. Normalize lat/long/km: convert comma to period, then to float
	# Handles both formats: 3.14 and 3,14
	spatial_dataframe['latitude'] = normalize_to_float(spatial_dataframe['latitude'])
	spatial_dataframe['longitude'] = normalize_to_float(spatial_dataframe['longitude'])
	spatial_dataframe['km'] = normalize_to_float(spatial_dataframe['km'])

	# 2. Fill missing UF values based on municipality
	municipio_to_uf = {
		'TERRA NOVA DO NORTE': 'MT',
		'GUARANTA DO NORTE': 'MT',
		'MATUPA': 'MT',
		'PEIXOTO DE AZEVEDO': 'MT',
		'VALPARAISO DE GOIAS': 'GO',
		'SAO JOAO DE MERITI': 'RJ',
		'TABOAO DA SERRA': 'SP'
	}

	# Fill UF where it's null
	def fill_uf(row):
		if pd.isna(row['uf']) or row['uf'] == '':
			return municipio_to_uf.get(row['municipio'], row['uf'])
		return row['uf']

	# Count how many UFs were filled
	uf_filled_count = spatial_dataframe['uf'].apply(lambda x: municipio_to_uf.get(x, None) is not None).sum()

	spatial_dataframe['uf'] = spatial_dataframe.apply(fill_uf, axis=1)

	# Remove records with invalid coordinates after normalization
	initial_count = len(spatial_dataframe)

	# Identify records to be dropped (for logging)
	invalid_coords_mask = spatial_dataframe[['latitude', 'longitude']].isna().any(axis=1)
	dropped_records = spatial_dataframe[invalid_coords_mask].copy()

	# Drop invalid records
	spatial_dataframe = spatial_dataframe.dropna(subset=['latitude', 'longitude'])
	dropped_count = initial_count - len(spatial_dataframe)

	# Check for coordinates outside valid ranges (after conversion to float)
	# Brazil's approximate bounding box:
	#   Latitude:  -33.75° (south, Uruguay border) to 5.27° (north, Venezuela border)
	#   Longitude: -73.98° (west, Acre) to -28.84° (east, Paraíba/RN)
	# Using slightly wider bounds (-34 to 6, -75 to -30) to include border areas
	valid_brazil_mask = (
		(spatial_dataframe['latitude'].between(-34, 6)) &
		(spatial_dataframe['longitude'].between(-75, -30))
	)
	invalid_range_count = (~valid_brazil_mask).sum()
	invalid_range_records = spatial_dataframe[~valid_brazil_mask].copy()

	print(f"   ✓ Coordinate normalization complete")
	print(f"   - Valid coordinates after conversion: {len(spatial_dataframe):,}")
	print(f"   - Invalid/NULL coordinates dropped: {dropped_count:,}")
	print(f"   - Coordinates outside Brazil bounds: {invalid_range_count:,}")

	# Query to create the target table
	create_table_query = f"""
	CREATE TABLE {TARGET_TABLE_NAME}
	(
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		date TEXT NOT NULL,
		uf TEXT,
		municipio TEXT,
		br INTEGER,
		km REAL,
		latitude REAL,
		longitude REAL
	)
	"""

	# Create/update table in analysis database
	with sqlite3.connect(TARGET_DB) as analysis_db:
		analysis_db.execute(f"DROP TABLE IF EXISTS {TARGET_TABLE_NAME};")
		analysis_db.execute(create_table_query)
		spatial_dataframe.to_sql(TARGET_TABLE_NAME, analysis_db, index=False, if_exists="append")

	analysis_db.close()

	print(f"\n{'='*60}")
	print(f"   ✓ SPATIAL DATA EXTRACTION COMPLETE")
	print(f"{'='*60}")
	print(f"   Source: {SOURCE_DB}")
	print(f"   Output: {TARGET_DB} (table: {TARGET_TABLE_NAME})")
	print(f"   Final records in table: {len(spatial_dataframe):,}")

	# Summary of data cleaning
	print(f"\n   Data quality summary:")
	if uf_filled_count > 0:
		print(f"   - UF values filled: {uf_filled_count:,}")
	if dropped_count > 0:
		print(f"   - Invalid/NULL coordinates dropped: {dropped_count:,}")
	if invalid_range_count > 0:
		print(f"   - Coordinates outside Brazil (included but flagged): {invalid_range_count:,}")

	# Show sample of dropped records (NULL/invalid after conversion)
	if dropped_count > 0 and len(dropped_records) > 0:
		print(f"\n   Sample of DROPPED records with NULL/invalid coordinates (first {min(5, len(dropped_records))}):")
		print(dropped_records.head().to_string(index=False))

		# Save all dropped records to CSV for inspection
		dropped_csv_path = os.path.join(EXTRACTED_DIR, "dropped_spatial_records.csv")
		dropped_records.to_csv(dropped_csv_path, index=False, encoding='utf-8')
		print(f"   Full list saved to: {dropped_csv_path}")

	# Show sample of records with coordinates outside Brazil bounds
	if invalid_range_count > 0 and len(invalid_range_records) > 0:
		print(f"\n   Sample of records with coordinates OUTSIDE Brazil bounds (first {min(5, len(invalid_range_records))}):")
		print(invalid_range_records[['date', 'uf', 'municipio', 'br', 'km', 'latitude', 'longitude']].head().to_string(index=False))

		# Save invalid range records to CSV
		invalid_range_csv_path = os.path.join(EXTRACTED_DIR, "invalid_range_spatial_records.csv")
		invalid_range_records.to_csv(invalid_range_csv_path, index=False, encoding='utf-8')
		print(f"   Full list saved to: {invalid_range_csv_path}")
		print(f"\n   Note: These records are INCLUDED in the database for manual review.")
		print(f"         Filter them out for analysis: WHERE latitude BETWEEN -34 AND 6 AND longitude BETWEEN -75 AND -30")

	print(f"\n{'='*60}")

if __name__ == "__main__":
	extract_spatial()
