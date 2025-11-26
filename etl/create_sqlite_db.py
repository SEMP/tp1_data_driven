import os
import sqlite3
import pandas as pd
from glob import glob

def create_sqlite_db():
    # Configuration
    DATA_PATH = 'data'
    DB_FILENAME = 'datatran_raw.db'
    TABLE_NAME = 'accidents'
    DELETE_CSV_AFTER_IMPORT = True  # Delete CSV files after successful database creation

    # Path to CSV files (sorted by year)
    csv_files = sorted(glob(os.path.join(DATA_PATH, 'datatran*.csv')))

    # Safety check: Ensure CSV files exist before proceeding
    if not csv_files:
        print("   Error: No CSV files found to import!")
        print(f"   Please run 'make download' first to download the data.")
        print(f"   Looking for files in: {DATA_PATH}/datatran*.csv")
        return

    print(f"Found {len(csv_files)} CSV files to import.")

    # SQLite DB name (save inside data folder)
    db_name = os.path.join(DATA_PATH, DB_FILENAME)

    # Connect to SQLite database (or create it)
    db_connection = sqlite3.connect(db_name)

    # Drop existing table to avoid duplicates (safe because we verified CSV files exist)
    db_connection.execute(f"DROP TABLE IF EXISTS {TABLE_NAME};")
    db_connection.commit()

    # Column names - unified schema from all years (2007-2025)
    columns = [
        "id", "data_inversa", "dia_semana", "horario", "uf", "br", "km", "municipio",
        "causa_acidente", "tipo_acidente", "classificacao_acidente", "fase_dia", "sentido_via",
        "condicao_metereologica", "tipo_pista", "tracado_via", "uso_solo", "ano", "pessoas", "mortos",
        "feridos_leves", "feridos_graves", "ilesos", "ignorados", "feridos", "veiculos",
        "latitude", "longitude", "regional", "delegacia", "uop"
    ]

    # Create table with a new field as primary key (since the dataset has repeated ids between files)
    create_table_sql = f"""
    CREATE TABLE {TABLE_NAME}
    (
        row_id INTEGER PRIMARY KEY AUTOINCREMENT,
        {columns[0]} INTEGER,
        {columns[1]} TEXT,
        {columns[2]} TEXT,
        {columns[3]} TEXT,
        {columns[4]} TEXT,
        {columns[5]} INTEGER,
        {columns[6]} TEXT,
        {columns[7]} TEXT,
        {columns[8]} TEXT,
        {columns[9]} TEXT,
        {columns[10]} TEXT,
        {columns[11]} TEXT,
        {columns[12]} TEXT,
        {columns[13]} TEXT,
        {columns[14]} TEXT,
        {columns[15]} TEXT,
        {columns[16]} TEXT,
        {columns[17]} INTEGER,
        {columns[18]} INTEGER,
        {columns[19]} INTEGER,
        {columns[20]} INTEGER,
        {columns[21]} INTEGER,
        {columns[22]} INTEGER,
        {columns[23]} INTEGER,
        {columns[24]} INTEGER,
        {columns[25]} INTEGER,
        {columns[26]} TEXT,
        {columns[27]} TEXT,
        {columns[28]} TEXT,
        {columns[29]} TEXT,
        {columns[30]} TEXT
    );
    """

    db_connection.execute(create_table_sql)
    db_connection.commit()

    # Import each CSV into the database
    expected_columns = columns  # full set of 30 columns

    for file in csv_files:
        print(f"Importing {file}...")
        csv_dataframe = pd.read_csv(file, sep=';', encoding='ISO-8859-1', low_memory=False)

        # Add missing columns with None
        missing_cols = set(expected_columns) - set(csv_dataframe.columns)
        for col in missing_cols:
            csv_dataframe[col] = None

        # Reorder and truncate columns to match expected
        csv_dataframe = csv_dataframe.reindex(columns=expected_columns)

        # Insert into SQLite
        csv_dataframe.to_sql(TABLE_NAME, db_connection, if_exists='append', index=False)

    print("All files imported successfully into SQLite.")
    db_connection.close()

    # Cleanup: Delete CSV files after successful import
    if DELETE_CSV_AFTER_IMPORT:
        print("\nCleaning up CSV files...")
        for csv_file in csv_files:
            try:
                os.remove(csv_file)
                print(f"  ✓ Deleted: {os.path.basename(csv_file)}")
            except Exception as e:
                print(f"  ✗ Could not delete {os.path.basename(csv_file)}: {e}")
        print("Cleanup complete. CSV files removed, database retained.")

if __name__ == "__main__":
    create_sqlite_db()