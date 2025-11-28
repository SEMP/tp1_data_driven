# Database Usage Examples

**Project:** Trabajo Práctico 1 - Análisis de Datos con Métodos Data-Driven
**Related:** See `database-structure.md` for schema details

---

## Table of Contents

1. [Python Examples](#python-examples)
2. [R Examples](#r-examples)
3. [SQL CLI Examples](#sql-cli-examples)
4. [Common Queries](#common-queries)
5. [Data Export Examples](#data-export-examples)
6. [Performance Tips](#performance-tips)

---

## Python Examples

### Using pandas (Recommended)

```python
import pandas as pd
import sqlite3

# Connect to analysis database
conn = sqlite3.connect('extracted/analysis_data.db')

# Read spatial data
df_spatial = pd.read_sql_query("""
    SELECT date, uf, municipio, latitude, longitude
    FROM accidents_spatial
    WHERE date >= '2023-01-01'
""", conn)

# Read time series data
df_timeseries = pd.read_sql_query("""
    SELECT date, accidents_count
    FROM accidents_daily
    ORDER BY date
""", conn)

conn.close()

print(df_spatial.head())
print(f"Total records: {len(df_spatial)}")
```

### Using sqlite3 only

```python
import sqlite3

conn = sqlite3.connect('extracted/analysis_data.db')
cursor = conn.cursor()

# Query data
cursor.execute("""
    SELECT uf, COUNT(*) as count
    FROM accidents_spatial
    GROUP BY uf
    ORDER BY count DESC
""")

results = cursor.fetchall()
for uf, count in results:
    print(f"{uf}: {count} accidents")

conn.close()
```

### Best Practice: Using Context Manager

```python
import sqlite3
import pandas as pd

# Automatically closes connection
with sqlite3.connect('extracted/analysis_data.db') as conn:
    df = pd.read_sql_query("""
        SELECT * FROM accidents_spatial
        WHERE uf = 'SP'
        LIMIT 1000
    """, conn)

print(df.head())
```

---

## R Examples

### Using DBI and RSQLite

```r
library(DBI)
library(RSQLite)

# Connect to database
con <- dbConnect(SQLite(), "extracted/analysis_data.db")

# Read data
df_spatial <- dbGetQuery(con, "
  SELECT date, uf, municipio, latitude, longitude
  FROM accidents_spatial
  WHERE uf = 'SP'
")

# Read with parameters
df_filtered <- dbGetQuery(con, "
  SELECT *
  FROM accidents_spatial
  WHERE date BETWEEN ? AND ?
", params = c('2023-01-01', '2023-12-31'))

# Disconnect
dbDisconnect(con)

head(df_spatial)
```

### Using dplyr with Database Backend

```r
library(dplyr)
library(dbplyr)
library(RSQLite)

# Create connection
con <- dbConnect(SQLite(), "extracted/analysis_data.db")

# Create table reference (lazy evaluation)
accidents_tbl <- tbl(con, "accidents_spatial")

# Use dplyr verbs (translated to SQL)
result <- accidents_tbl %>%
  filter(uf == "SP") %>%
  group_by(municipio) %>%
  summarise(
    count = n(),
    avg_lat = mean(latitude, na.rm = TRUE),
    avg_lon = mean(longitude, na.rm = TRUE)
  ) %>%
  arrange(desc(count)) %>%
  collect()  # Fetch results

print(result)

dbDisconnect(con)
```

---

## SQL CLI Examples

### Opening Database

```bash
# Open database
sqlite3 extracted/analysis_data.db

# Or execute single query
sqlite3 extracted/analysis_data.db "SELECT COUNT(*) FROM accidents_spatial;"
```

### Useful Commands

```sql
-- List tables
.tables

-- Show schema
.schema accidents_spatial

-- Show schema for all tables
.schema

-- Change output mode
.mode column
.headers on

-- Export query to CSV
.mode csv
.output accidents_sp.csv
SELECT * FROM accidents_spatial WHERE uf = 'SP';
.output stdout

-- Execute SQL file
.read queries.sql

-- Show database info
.databases

-- Exit
.quit
```

### Interactive Query Examples

```sql
-- Set display mode
.mode column
.headers on
.width 12 8 20 10 10

-- Query data
SELECT date, uf, municipio, latitude, longitude
FROM accidents_spatial
LIMIT 10;

-- Count by state
SELECT uf, COUNT(*) as accident_count
FROM accidents_spatial
GROUP BY uf
ORDER BY accident_count DESC;
```

---

## Common Queries

### Time Series Analysis

**Daily accidents over time:**
```sql
SELECT date, accidents_count
FROM accidents_daily
ORDER BY date;
```

**Weekly aggregation:**
```sql
SELECT
  strftime('%Y-%W', date) AS week,
  SUM(accidents_count) AS weekly_accidents
FROM accidents_daily
GROUP BY week
ORDER BY week;
```

**Monthly aggregation:**
```sql
SELECT
  strftime('%Y-%m', date) AS month,
  SUM(accidents_count) AS monthly_accidents
FROM accidents_daily
GROUP BY month
ORDER BY month;
```

**Year-over-year comparison:**
```sql
SELECT
  strftime('%Y', date) AS year,
  strftime('%m', date) AS month,
  SUM(accidents_count) AS monthly_accidents
FROM accidents_daily
GROUP BY year, month
ORDER BY year, month;
```

### Spatial Analysis

**Accidents by state:**
```sql
SELECT
  uf,
  COUNT(*) AS accident_count
FROM accidents_spatial
GROUP BY uf
ORDER BY accident_count DESC;
```

**Accidents by municipality (top 20):**
```sql
SELECT
  uf,
  municipio,
  COUNT(*) AS accident_count,
  AVG(latitude) AS avg_lat,
  AVG(longitude) AS avg_lon
FROM accidents_spatial
GROUP BY uf, municipio
ORDER BY accident_count DESC
LIMIT 20;
```

**Accidents in bounding box (geographic filter):**
```sql
SELECT *
FROM accidents_spatial
WHERE latitude BETWEEN -25 AND -20
  AND longitude BETWEEN -50 AND -45
LIMIT 1000;
```

**Find municipalities with most accidents in a specific state:**
```sql
SELECT
  municipio,
  COUNT(*) AS accident_count,
  AVG(latitude) AS avg_lat,
  AVG(longitude) AS avg_lon
FROM accidents_spatial
WHERE uf = 'SP'
GROUP BY municipio
ORDER BY accident_count DESC
LIMIT 10;
```

### Spatio-Temporal Analysis (POD/DMD)

**Monthly municipality matrix (for POD/DMD):**
```sql
SELECT
  strftime('%Y-%m', date) AS month,
  uf,
  municipio,
  COUNT(*) AS accident_count,
  AVG(latitude) AS avg_lat,
  AVG(longitude) AS avg_lon
FROM accidents_spatial
GROUP BY month, uf, municipio
ORDER BY month, uf, municipio;
```

**Monthly state aggregation:**
```sql
SELECT
  strftime('%Y-%m', date) AS month,
  uf,
  COUNT(*) AS accident_count
FROM accidents_spatial
GROUP BY month, uf
ORDER BY month, uf;
```

**Find maximum accidents per month:**
```sql
SELECT
  strftime('%Y-%m', date) AS month,
  COUNT(*) AS accident_count
FROM accidents_spatial
GROUP BY month
ORDER BY accident_count DESC
LIMIT 1;
```

**Random sample for map visualization (avoid freezing):**
```sql
SELECT
  date,
  uf,
  municipio,
  latitude,
  longitude
FROM accidents_spatial
WHERE date BETWEEN '2023-01-01' AND '2023-12-31'
ORDER BY RANDOM()
LIMIT 1000;
```

### Advanced Queries

**Accidents by year and state:**
```sql
SELECT
  strftime('%Y', date) AS year,
  uf,
  COUNT(*) AS accident_count
FROM accidents_spatial
GROUP BY year, uf
ORDER BY year, uf;
```

**Time series for specific municipality:**
```sql
SELECT
  strftime('%Y-%m', date) AS month,
  COUNT(*) AS accident_count
FROM accidents_spatial
WHERE uf = 'SP' AND municipio = 'SAO PAULO'
GROUP BY month
ORDER BY month;
```

**Get distinct municipalities per state:**
```sql
SELECT
  uf,
  COUNT(DISTINCT municipio) AS municipality_count
FROM accidents_spatial
GROUP BY uf
ORDER BY municipality_count DESC;
```

---

## Data Export Examples

### Export to CSV (Python)

```python
import pandas as pd
import sqlite3

conn = sqlite3.connect('extracted/analysis_data.db')

# Export spatial data
df = pd.read_sql_query("SELECT * FROM accidents_spatial", conn)
df.to_csv('data/spatial_export.csv', index=False)

# Export monthly aggregation
df_monthly = pd.read_sql_query("""
    SELECT
      strftime('%Y-%m', date) AS month,
      uf,
      municipio,
      COUNT(*) AS accident_count
    FROM accidents_spatial
    GROUP BY month, uf, municipio
""", conn)
df_monthly.to_csv('data/monthly_export.csv', index=False)

conn.close()
```

### Export to JSON (Python)

```python
import json
import sqlite3

conn = sqlite3.connect('extracted/analysis_data.db')
cursor = conn.cursor()

cursor.execute("SELECT * FROM accidents_spatial LIMIT 100")
columns = [desc[0] for desc in cursor.description]
results = cursor.fetchall()

data = [dict(zip(columns, row)) for row in results]

with open('data/spatial_export.json', 'w') as f:
    json.dump(data, f, indent=2)

conn.close()
```

### Export to CSV (SQL CLI)

```bash
# Direct export
sqlite3 -header -csv extracted/analysis_data.db \
  "SELECT * FROM accidents_spatial LIMIT 1000" \
  > data/spatial_export.csv

# Monthly aggregation export
sqlite3 -header -csv extracted/analysis_data.db \
  "SELECT strftime('%Y-%m', date) AS month, uf, municipio, COUNT(*) as count
   FROM accidents_spatial
   GROUP BY month, uf, municipio" \
  > data/monthly_accidents.csv
```

### Export to Excel (Python)

```python
import pandas as pd
import sqlite3

conn = sqlite3.connect('extracted/analysis_data.db')

# Create Excel file with multiple sheets
with pd.ExcelWriter('data/accidents_export.xlsx') as writer:
    # Sheet 1: Daily time series
    df_daily = pd.read_sql_query(
        "SELECT * FROM accidents_daily",
        conn
    )
    df_daily.to_excel(writer, sheet_name='Daily', index=False)

    # Sheet 2: Accidents by state
    df_states = pd.read_sql_query("""
        SELECT uf, COUNT(*) as count
        FROM accidents_spatial
        GROUP BY uf
        ORDER BY count DESC
    """, conn)
    df_states.to_excel(writer, sheet_name='By State', index=False)

    # Sheet 3: Top municipalities
    df_cities = pd.read_sql_query("""
        SELECT uf, municipio, COUNT(*) as count
        FROM accidents_spatial
        GROUP BY uf, municipio
        ORDER BY count DESC
        LIMIT 100
    """, conn)
    df_cities.to_excel(writer, sheet_name='Top Cities', index=False)

conn.close()
```

---

## Performance Tips

### Adding Indexes

For faster queries, create indexes on frequently queried columns:

```sql
-- Index on date for time range queries
CREATE INDEX IF NOT EXISTS idx_spatial_date
ON accidents_spatial(date);

-- Index on location for spatial queries
CREATE INDEX IF NOT EXISTS idx_spatial_location
ON accidents_spatial(uf, municipio);

-- Composite index for spatio-temporal queries
CREATE INDEX IF NOT EXISTS idx_spatial_date_location
ON accidents_spatial(date, uf, municipio);

-- Index on daily date
CREATE INDEX IF NOT EXISTS idx_daily_date
ON accidents_daily(date);
```

**Check existing indexes:**
```sql
-- List all indexes
.indexes

-- Or query sqlite_master
SELECT name, tbl_name, sql
FROM sqlite_master
WHERE type = 'index';
```

### Query Optimization Tips

**1. Use LIMIT for testing:**
```sql
-- Instead of loading all data
SELECT * FROM accidents_spatial;

-- Use LIMIT for testing
SELECT * FROM accidents_spatial LIMIT 100;
```

**2. Aggregate before loading into memory:**
```python
# Bad: Load all data then aggregate in pandas
df = pd.read_sql_query("SELECT * FROM accidents_spatial", conn)
df.groupby('uf')['date'].count()

# Good: Aggregate in SQL
df = pd.read_sql_query("""
    SELECT uf, COUNT(*) as count
    FROM accidents_spatial
    GROUP BY uf
""", conn)
```

**3. Use date range filters:**
```sql
-- Filter early
SELECT *
FROM accidents_spatial
WHERE date BETWEEN '2023-01-01' AND '2023-12-31'
  AND uf = 'SP';
```

**4. Use column selection:**
```sql
-- Don't select all columns if you don't need them
SELECT latitude, longitude  -- Only what you need
FROM accidents_spatial
WHERE date > '2023-01-01';
```

### Database Maintenance

**Optimize database:**
```bash
# Vacuum to reclaim space and optimize
sqlite3 extracted/analysis_data.db "VACUUM;"

# Analyze to update query optimizer statistics
sqlite3 extracted/analysis_data.db "ANALYZE;"
```

**Check database integrity:**
```bash
sqlite3 extracted/analysis_data.db "PRAGMA integrity_check;"
```

**Get database statistics:**
```sql
-- Table sizes
SELECT
  name,
  (SELECT COUNT(*) FROM accidents_daily) as daily_rows,
  (SELECT COUNT(*) FROM accidents_spatial) as spatial_rows;

-- Date ranges
SELECT
  'accidents_daily' as table_name,
  MIN(date) as earliest,
  MAX(date) as latest
FROM accidents_daily
UNION ALL
SELECT
  'accidents_spatial',
  MIN(date),
  MAX(date)
FROM accidents_spatial;
```

---

## Troubleshooting

### "Database is locked" error

**Cause:** Another process is using the database

**Solutions:**
```python
# Use timeout parameter
conn = sqlite3.connect('extracted/analysis_data.db', timeout=10)

# Use context manager to ensure connections close
with sqlite3.connect('extracted/analysis_data.db') as conn:
    df = pd.read_sql_query("SELECT * FROM accidents_spatial", conn)

# Check for open connections
import gc
gc.collect()  # Force garbage collection to close connections
```

### "No such table" error

**Cause:** Table doesn't exist or wrong database file

**Solutions:**
```bash
# Check tables exist
sqlite3 extracted/analysis_data.db ".tables"

# Rebuild if needed
make extract-data

# Verify you're using correct database path
ls -l extracted/analysis_data.db
```

### Slow queries

**Solutions:**
1. Add indexes (see Performance Tips)
2. Use EXPLAIN QUERY PLAN to analyze:
```sql
EXPLAIN QUERY PLAN
SELECT * FROM accidents_spatial WHERE uf = 'SP';
```
3. Use LIMIT for large results
4. Filter data in SQL, not after loading
5. Use date range filters

### Memory errors with large results

**Solutions:**
```python
# Use chunksize to read in batches
for chunk in pd.read_sql_query(
    "SELECT * FROM accidents_spatial",
    conn,
    chunksize=10000
):
    process(chunk)

# Or aggregate in SQL first
df = pd.read_sql_query("""
    SELECT month, uf, COUNT(*) as count
    FROM (SELECT strftime('%Y-%m', date) as month, uf
          FROM accidents_spatial)
    GROUP BY month, uf
""", conn)
```

---

## Best Practices

### Connection Management

```python
# Good: Use context manager
with sqlite3.connect('extracted/analysis_data.db') as conn:
    df = pd.read_sql_query("SELECT ...", conn)
# Connection automatically closed

# Good: Explicit close
conn = sqlite3.connect('extracted/analysis_data.db')
try:
    df = pd.read_sql_query("SELECT ...", conn)
finally:
    conn.close()

# Bad: Connection left open
conn = sqlite3.connect('extracted/analysis_data.db')
df = pd.read_sql_query("SELECT ...", conn)
# conn never closed!
```

### SQL Injection Prevention

```python
# Bad: String formatting (SQL injection risk!)
uf = "SP"
query = f"SELECT * FROM accidents_spatial WHERE uf = '{uf}'"

# Good: Use parameters
uf = "SP"
query = "SELECT * FROM accidents_spatial WHERE uf = ?"
df = pd.read_sql_query(query, conn, params=(uf,))
```

### Data Validation

```python
# Check for NULL values
df = pd.read_sql_query("SELECT * FROM accidents_spatial", conn)
print(df.isnull().sum())

# Verify data types
print(df.dtypes)

# Check coordinate ranges
print(f"Lat range: {df['latitude'].min()} to {df['latitude'].max()}")
print(f"Lon range: {df['longitude'].min()} to {df['longitude'].max()}")
```

---

## Additional Resources

- SQLite Documentation: https://www.sqlite.org/docs.html
- pandas SQL documentation: https://pandas.pydata.org/docs/reference/api/pandas.read_sql_query.html
- dbplyr (R): https://dbplyr.tidyverse.org/
