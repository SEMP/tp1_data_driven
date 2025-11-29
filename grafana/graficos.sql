-- Gráfico de accidentes diarios
SELECT
  unixepoch(accidents_t.date) AS time,
  accidents_t.accidents_count
FROM accidents_daily AS accidents_t
WHERE time BETWEEN $__from/1000 AND $__to/1000
ORDER BY time
;

-- Mapa de accidentes
SELECT
  unixepoch(accident_t.date) AS time,
  accident_t.uf,
  accident_t.municipio,
  accident_t.br,
  accident_t.km,
  accident_t.latitude,
  accident_t.longitude
FROM accidents_spatial AS accident_t
WHERE time BETWEEN $__from/1000 AND $__to/1000
;

-- Mapa de accidentes, muestras aleatorias de 1000 registros (para no sobrecargar el grafico)
SELECT
	unixepoch(accident_t.date) AS time,
	accident_t.uf,
	accident_t.municipio,
	accident_t.br,
	accident_t.km,
	accident_t.latitude,
	accident_t.longitude
FROM accidents_spatial AS accident_t
WHERE time BETWEEN $__from/1000 AND $__to/1000
ORDER BY RANDOM()
LIMIT 1000;
