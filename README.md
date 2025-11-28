# Datatran Analysis Project

Transportation accident data analysis using data-driven methods (2007-2025).

**Course:** MIA10 - Análisis de Datos con Métodos de Data Driven
**Institution:** Maestría en Inteligencia Artificial y Ciencias de Datos - Facultad Politécnica (FP-UNA)
**Professor:** Dr. Carlos Méndez

## Assignment Context

This repository corresponds to **Trabajo Práctico 1** (40% of final grade, due Week 3):

**Requirements:**
- Apply **at least two data-driven methods** (POD, DMD, HODMD, SVD, etc.) to discover patterns, extract dominant modes, or perform predictions
- Analyze real-world data to reveal hidden structures and patterns

**Deliverables:**
1. Technical Report: introduction, methodology, results, discussion, and conclusions
2. Oral presentation (15 minutes) with visualizations and group discussion

**Methodological Purpose:**
- Understand how decomposition methods reveal hidden structures in real data
- Evaluate predictive power and interpretability without knowing the underlying physics
- Develop interdisciplinary analysis capability

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
make extract-data   # Extract and prepare data for analysis
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

2. **Create raw database:**
   ```bash
   make create-sqlite
   ```
   Creates `data/datatran_raw.db` SQLite database from all CSV files.

3. **Extract data for analysis:**
   ```bash
   make extract-data
   ```
   Extracts and prepares data from raw database to `extracted/analysis_data.db`:
   - **accidents_daily** - Daily time series of accident counts
   - **accidents_spatial** - Spatial data with coordinates (2017-2025, includes: date, uf, municipio, lat, lon)

## Project Structure

```
.
├── etl/
│   ├── descarga.py           # Extract: Download data from Google Drive
│   ├── create_sqlite_db.py   # Transform & Load: Create raw SQLite database
│   ├── extract_data.py       # Orchestrator: Extract data for analysis
│   ├── extract_timeseries.py # Extract: Daily time series
│   ├── extract_spatial.py    # Extract: Spatial data with coordinates
│   └── enlaces.csv           # Configuration: Google Drive file IDs
├── data/                     # Downloaded CSVs and raw database (gitignored)
├── extracted/                # Processed data for analysis (committed)
│   └── analysis_data.db      # Contains: accidents_daily, accidents_spatial
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
MAIN_FILE = main.py                # Main script entry point
DOWNLOAD_SCRIPT = etl/descarga.py
CREATE_DB_SCRIPT = etl/create_sqlite_db.py
EXTRACT_DATA_SCRIPT = etl/extract_data.py
```

Or edit configuration constants in the ETL scripts:
- `etl/create_sqlite_db.py`: `DB_FILENAME`, `TABLE_NAME`, `DATA_PATH`

## Notes

- Downloaded data is stored in `data/` (excluded from git)
- **CSV files are automatically deleted** after successful database creation to save disk space
  - To keep CSV files, set `DELETE_CSV_AFTER_IMPORT = False` in `etl/create_sqlite_db.py`
- Extracted/processed data is stored in `extracted/` (committed to repository)
- Database encoding automatically handles ISO-8859-1 to UTF-8 conversion
- Files are processed in chronological order (2007 → 2025)
- The database uses `row_id` as primary key (original `id` field has duplicates across years)
