# Datatran Analysis Project

Data analysis project for transportation accident data (datatran) spanning 2007-2025. Part of the course "Análisis de Datos con Métodos de Data Driven" - Maestría en Inteligencia Artificial.

## Project Overview

This project provides an ETL (Extract, Transform, Load) pipeline for downloading, processing, and analyzing Brazilian transportation accident data from Google Drive. The data covers accidents from 2007 to 2025 with varying schema structures across different years.

## Setup

### Prerequisites

- Python 3.7+
- Make (cross-platform compatible with Windows PowerShell and Linux/Mac)

### Installation

1. Clone the repository
2. Create virtual environment and install dependencies:

```bash
make install
```

This will:
- Create a virtual environment in `.venv/`
- Upgrade pip
- Install required packages from `requirements.txt`

## Usage

### Available Commands

```bash
make install        # Create virtual environment and install dependencies
make download       # Download CSV files from Google Drive
make create-sqlite  # Create SQLite database from downloaded CSVs
make run            # Run the main script (main.py)
make run-file FILE=<path>  # Run a specific Python file
make freeze         # Update requirements.txt with current packages
make clean          # Remove virtual environment
```

### Data Pipeline Workflow

1. **Download data:**
   ```bash
   make download
   ```
   Downloads zip files from Google Drive and extracts CSVs to `data/` directory.

2. **Create database:**
   ```bash
   make create-sqlite
   ```
   Creates `data/datatran_raw.db` SQLite database from all CSV files.

## Project Structure

```
.
├── etl/
│   ├── descarga.py           # Extract: Download data from Google Drive
│   ├── create_sqlite_db.py   # Transform & Load: Create SQLite database
│   └── enlaces.csv           # Configuration: Google Drive file IDs
├── data/                     # Downloaded CSVs and database (gitignored)
├── main.py                   # Main entry point
├── Makefile                  # Cross-platform build commands
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Data Schema

The dataset schema evolved over the years:

- **2007-2015:** 26 columns (includes "ano" field)
- **2016:** 25 columns (no "ano", no geolocation)
- **2017-2025:** 30 columns (no "ano", includes latitude/longitude/regional data)

The unified database schema contains **31 columns** total, with missing fields filled as NULL:

- Basic info: id, data_inversa, dia_semana, horario, uf, br, km, municipio
- Accident details: causa_acidente, tipo_acidente, classificacao_acidente
- Context: fase_dia, sentido_via, condicao_metereologica, tipo_pista, tracado_via, uso_solo
- Statistics: ano, pessoas, mortos, feridos_leves, feridos_graves, ilesos, ignorados, feridos, veiculos
- Geolocation: latitude, longitude, regional, delegacia, uop

## Dependencies

- `gdown==5.2.0` - Download files from Google Drive
- `pandas==2.3.3` - Data processing and CSV manipulation

## Configuration

To customize the pipeline, edit variables at the top of the Makefile:

```makefile
MAIN_FILE = main.py              # Main script entry point
DOWNLOAD_SCRIPT = etl/descarga.py
CREATE_DB_SCRIPT = etl/create_sqlite_db.py
```

Or edit configuration constants in the ETL scripts:
- `etl/create_sqlite_db.py`: `DB_FILENAME`, `TABLE_NAME`, `DATA_PATH`

## Notes

- Downloaded data is stored in `data/` (excluded from git)
- Database encoding automatically handles ISO-8859-1 to UTF-8 conversion
- Files are processed in chronological order (2007 → 2025)
- The database uses `row_id` as primary key (original `id` field has duplicates across years)
