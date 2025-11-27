-- Grafico de accidentes diarios
SELECT
  unixepoch(accidents_t.date) AS time,
  accidents_t.accidents_count
FROM accidents_daily AS accidents_t
WHERE unixepoch(accidents_t.date) BETWEEN $__from/1000 AND $__to/1000
ORDER BY time
;
