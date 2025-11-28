import sqlite3
import pandas as pd
import os

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
		latitude,
		longitude
	FROM normalized
	WHERE date IS NOT NULL
	ORDER BY date_normalized
	;
	"""

	# Connect to the full raw database
	with sqlite3.connect(SOURCE_DB) as source_db_connection:
		# Load spatial data into DataFrame
		spatial_dataframe = pd.read_sql_query(query, source_db_connection)

	# Close source DB
	source_db_connection.close()

	# Data cleaning and normalization
	print("   Cleaning and normalizing data...")

	# 1. Normalize lat/long: convert comma to period, then to float
	spatial_dataframe['latitude'] = (
		spatial_dataframe['latitude']
		.astype(str)
		.str.replace(',', '.', regex=False)
		.replace('None', pd.NA)
		.astype(float)
	)
	spatial_dataframe['longitude'] = (
		spatial_dataframe['longitude']
		.astype(str)
		.str.replace(',', '.', regex=False)
		.replace('None', pd.NA)
		.astype(float)
	)

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

	# Query to create the target table
	create_table_query = f"""
	CREATE TABLE {TARGET_TABLE_NAME}
	(
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		date TEXT NOT NULL,
		uf TEXT,
		municipio TEXT,
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

	print(f"   ✓ Spatial data extracted successfully!")
	print(f"   Source: {SOURCE_DB}")
	print(f"   Output: {TARGET_DB} (table: {TARGET_TABLE_NAME})")
	print(f"   Records: {len(spatial_dataframe)} accidents with valid coordinates")
	if dropped_count > 0:
		print(f"   Dropped: {dropped_count} records with invalid coordinates after normalization")

		# Show sample of dropped records
		if len(dropped_records) > 0:
			print(f"\n   Sample of dropped records (first {min(5, len(dropped_records))}):")
			print(dropped_records.head().to_string(index=False))

			# Save all dropped records to CSV for inspection
			dropped_csv_path = os.path.join(EXTRACTED_DIR, "dropped_spatial_records.csv")
			dropped_records.to_csv(dropped_csv_path, index=False, encoding='utf-8')
			print(f"\n   Full list saved to: {dropped_csv_path}")

	if uf_filled_count > 0:
		print(f"   Filled: {uf_filled_count} missing UF values based on municipality")

if __name__ == "__main__":
	extract_spatial()
