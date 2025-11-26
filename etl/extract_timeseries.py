import sqlite3
import pandas as pd
import os

def extract_timeseries():
	# Configuration
	SOURCE_DB = "data/datatran_raw.db"
	SOURCE_TABLE_NAME = "accidents"

	EXTRACTED_DIR = "extracted"
	TARGET_DB = os.path.join(EXTRACTED_DIR, "analysis_data.db")
	TARGET_TABLE_NAME = "accidents_daily"

	# Create extracted directory if it doesn't exist
	os.makedirs(EXTRACTED_DIR, exist_ok=True)

	# SQL to extract normalized time series
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
			END AS date_normalized
		FROM {SOURCE_TABLE_NAME}
		WHERE
			data_inversa IS NOT NULL
	)

	SELECT
		date_normalized AS date,
		COUNT(*) AS accidents_count
	FROM normalized
	GROUP BY date_normalized
	ORDER BY date_normalized
	;
	"""

	# Connect to the full raw database
	with sqlite3.connect(SOURCE_DB) as source_db_connection:
		# Load time series data into DataFrame
		time_series_dataframe = pd.read_sql_query(query, source_db_connection)

	# Close source DB
	source_db_connection.close()

	# Query to creat the target table
	create_table_query = f"""
	CREATE TABLE {TARGET_TABLE_NAME}
	(
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		date TEXT NOT NULL,
		accidents_count INTEGER NOT NULL
	)
	"""

	# Create new database for time series
	with sqlite3.connect(TARGET_DB) as time_series_db:
		time_series_db.execute(f"DROP TABLE IF EXISTS {TARGET_TABLE_NAME};")
		time_series_db.execute(create_table_query)
		time_series_dataframe.to_sql(TARGET_TABLE_NAME, time_series_db, index=False, if_exists="append")

		# Create index on the date field (optional)
		# time_series_db.execute(f"CREATE INDEX IF NOT EXISTS idx_accidents_date ON {TARGET_TABLE_NAME}(date);")

	time_series_db.close()

	print(f"   Daily time series extracted successfully!")
	print(f"   Source: {SOURCE_DB}")
	print(f"   Output: {TARGET_DB}")
	print(f"   Records: {len(time_series_dataframe)} days")

if __name__ == "__main__":
    extract_timeseries()