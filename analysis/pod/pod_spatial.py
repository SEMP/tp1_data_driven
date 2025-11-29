"""
POD Spatial-Temporal Analysis: Caso Micro BR-101 Santa Catarina

Análisis espacial-temporal usando POD (Proper Orthogonal Decomposition)
sobre un tramo específico de carretera federal.

Matriz Snapshot X:
- Filas (Espacio): Tramos de carretera discretizados cada 10 km
- Columnas (Tiempo): Agrupación mensual
- Valores: Cantidad de accidentes por tramo/mes
"""

import sqlite3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

# ============================================================
# Configuración
# ============================================================

DB_PATH = "extracted/analysis_data.db"
OUTPUT_DIR = "analysis/pod/results"

# Caso de estudio: BR-101 en Santa Catarina
ESTADO = 'SC'
CARRETERA = 101
BIN_SIZE_KM = 10  # Discretización espacial cada 10 km

# ============================================================
# Funciones
# ============================================================

def load_spatial_data(estado, carretera):
	"""
	Carga datos espaciales desde la base de datos para un estado y carretera específicos.

	Returns:
		DataFrame con: date, uf, br, km, mes_anio
	"""
	conn = sqlite3.connect(DB_PATH)

	query = f"""
	SELECT
		date,
		uf,
		br,
		km,
		strftime('%Y-%m', date) as mes_anio
	FROM accidents_spatial
	WHERE uf = '{estado}'
	  AND br = {carretera}
	  AND km IS NOT NULL
	ORDER BY date
	"""

	df = pd.read_sql_query(query, conn)
	conn.close()

	return df


def build_snapshot_matrix(df, bin_size=10):
	"""
	Construye la matriz snapshot espacial-temporal.

	Args:
		df: DataFrame con columnas 'km' y 'mes_anio'
		bin_size: Tamaño de los bins espaciales en km

	Returns:
		X: Matriz numpy (n_tramos, n_meses)
		tramos: Array con los valores de km de cada tramo
		meses: Array con los períodos mensuales
	"""
	# Crear bins espaciales
	max_km = df['km'].max()
	bins_espacio = np.arange(0, max_km + bin_size, bin_size)
	df['tramo_km'] = pd.cut(df['km'], bins=bins_espacio, labels=bins_espacio[:-1])

	# Crear matriz de conteo (crosstab)
	matriz_X = pd.crosstab(df['tramo_km'], df['mes_anio'])

	# Convertir a numpy
	X = matriz_X.values
	tramos = matriz_X.index.astype(float).values
	meses = matriz_X.columns.values

	return X, tramos, meses


def compute_pod(X, center=True):
	"""
	Calcula POD usando SVD.

	Args:
		X: Matriz snapshot (espacio × tiempo)
		center: Si True, resta la media temporal

	Returns:
		U: Modos espaciales
		S: Valores singulares
		Vt: Modos temporales (transpuestos)
		X_mean: Campo medio
	"""
	if center:
		X_mean = X.mean(axis=1, keepdims=True)
		X_centered = X - X_mean
	else:
		X_mean = np.zeros((X.shape[0], 1))
		X_centered = X

	# SVD
	U, S, Vt = np.linalg.svd(X_centered, full_matrices=False)

	return U, S, Vt, X_mean


def plot_results(X, U, S, Vt, tramos, meses, X_mean):
	"""
	Genera visualizaciones del análisis POD.
	"""
	os.makedirs(OUTPUT_DIR, exist_ok=True)

	# Configuración visual
	plt.rcParams['figure.figsize'] = [15, 10]

	fig, axs = plt.subplots(2, 2, figsize=(15, 10))

	# A. Energía de los modos (Valores singulares)
	n_modes_plot = min(20, len(S))
	axs[0, 0].plot(range(1, n_modes_plot + 1), S[:n_modes_plot], 'ro-', linewidth=2)
	axs[0, 0].set_title('Energía de los Modos (Valores Singulares)', fontsize=12, fontweight='bold')
	axs[0, 0].set_ylabel('Importancia (Valor Singular)')
	axs[0, 0].set_xlabel('Modo #')
	axs[0, 0].grid(True, alpha=0.3)

	# B. Modo Espacial 1 (Estructura dominante)
	axs[1, 0].plot(tramos, U[:, 0], 'b-', linewidth=2)
	axs[1, 0].fill_between(tramos, U[:, 0], color='blue', alpha=0.3)
	axs[1, 0].set_title('Modo 1 Espacial (Estructura Dominante)', fontsize=12, fontweight='bold')
	axs[1, 0].set_ylabel('Intensidad del Patrón')
	axs[1, 0].set_xlabel('Kilómetro de la Ruta')
	axs[1, 0].grid(True, alpha=0.3)
	axs[1, 0].set_xlim(0, tramos.max())

	# Anotar zona crítica (máximo absoluto)
	max_idx = np.argmax(np.abs(U[:, 0]))
	max_km = tramos[max_idx]
	max_val = U[max_idx, 0]
	axs[1, 0].annotate(
		f'Zona Crítica: KM {max_km:.0f}',
		xy=(max_km, max_val),
		xytext=(max_km + 50, max_val),
		arrowprops=dict(facecolor='black', shrink=0.05),
		fontsize=10,
		bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7)
	)

	# C. Modo Temporal 1 (Dinámica)
	axs[1, 1].plot(range(len(Vt[0, :])), Vt[0, :], 'g-', linewidth=2)
	axs[1, 1].set_title('Modo 1 Temporal (Evolución)', fontsize=12, fontweight='bold')
	axs[1, 1].set_xlabel('Meses (desde inicio)')
	axs[1, 1].set_ylabel('Coeficiente Temporal')
	axs[1, 1].grid(True, alpha=0.3)

	# D. Reconstrucción usando solo Modo 1
	X_rank1 = S[0] * np.outer(U[:, 0], Vt[0, :]) + X_mean
	im = axs[0, 1].imshow(X_rank1, aspect='auto', cmap='hot', interpolation='nearest')
	axs[0, 1].set_title('Reconstrucción usando SOLO Modo 1', fontsize=12, fontweight='bold')
	axs[0, 1].set_ylabel('Tramo (KM)')
	axs[0, 1].set_xlabel('Meses')
	plt.colorbar(im, ax=axs[0, 1], label='Accidentes')

	plt.tight_layout()
	plt.savefig(f"{OUTPUT_DIR}/pod_spatial_br{CARRETERA}_{ESTADO}.png", dpi=300, bbox_inches='tight')
	print(f"   ✓ Gráfico guardado: {OUTPUT_DIR}/pod_spatial_br{CARRETERA}_{ESTADO}.png")

	# Gráfico adicional: Matriz original
	fig2, ax = plt.subplots(figsize=(10, 6))
	im = ax.imshow(X, aspect='auto', cmap='hot', interpolation='nearest')
	ax.set_title(f'Matriz Snapshot Original: BR-{CARRETERA} {ESTADO}\n(Accidentes por Tramo × Mes)',
	             fontsize=12, fontweight='bold')
	ax.set_ylabel('Espacio (Tramos de 10 KM)')
	ax.set_xlabel('Tiempo (Meses)')
	plt.colorbar(im, ax=ax, label='Cantidad de Accidentes')
	plt.tight_layout()
	plt.savefig(f"{OUTPUT_DIR}/matriz_original_br{CARRETERA}_{ESTADO}.png", dpi=300, bbox_inches='tight')
	print(f"   ✓ Gráfico guardado: {OUTPUT_DIR}/matriz_original_br{CARRETERA}_{ESTADO}.png")

	plt.show()


def print_statistics(X, S):
	"""
	Imprime estadísticas del análisis.
	"""
	# Energía acumulada
	energy = S**2 / np.sum(S**2) * 100
	cum_energy = np.cumsum(energy)

	print("\n" + "="*60)
	print("ESTADÍSTICAS POD")
	print("="*60)
	print(f"Dimensiones de la matriz: {X.shape[0]} tramos × {X.shape[1]} meses")
	print(f"Total de accidentes: {int(X.sum())}")
	print(f"\nEnergía de los primeros 5 modos:")
	for i in range(min(5, len(S))):
		print(f"  Modo {i+1}: {energy[i]:.2f}% (acumulado: {cum_energy[i]:.2f}%)")

	# Modos necesarios para 90% de energía
	n_modes_90 = np.argmax(cum_energy >= 90) + 1
	print(f"\nModos necesarios para 90% de energía: {n_modes_90}")
	print("="*60)


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
	print("="*60)
	print(f"POD SPATIAL-TEMPORAL: BR-{CARRETERA} en {ESTADO}")
	print("="*60)

	# 1. Cargar datos
	print(f"\n1. Cargando datos de BR-{CARRETERA} en {ESTADO}...")
	df = load_spatial_data(ESTADO, CARRETERA)
	print(f"   ✓ Registros cargados: {len(df):,}")
	print(f"   ✓ Rango temporal: {df['mes_anio'].min()} a {df['mes_anio'].max()}")
	print(f"   ✓ Rango espacial: KM {df['km'].min():.1f} a {df['km'].max():.1f}")

	# 2. Construir matriz snapshot
	print(f"\n2. Construyendo matriz snapshot (bins de {BIN_SIZE_KM} km)...")
	X, tramos, meses = build_snapshot_matrix(df, bin_size=BIN_SIZE_KM)
	print(f"   ✓ Matriz generada: {X.shape[0]} tramos × {X.shape[1]} meses")

	# 3. Aplicar POD
	print("\n3. Aplicando POD (SVD)...")
	U, S, Vt, X_mean = compute_pod(X, center=True)
	print(f"   ✓ SVD completado: {len(S)} modos extraídos")

	# 4. Estadísticas
	print_statistics(X, S)

	# 5. Visualizar
	print("\n4. Generando visualizaciones...")
	plot_results(X, U, S, Vt, tramos, meses, X_mean)

	print("\n✅ Análisis POD espacial completado!")
	print("="*60)
