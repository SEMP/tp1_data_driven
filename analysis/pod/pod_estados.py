"""
POD Macro Analysis: Comparación entre Estados

Análisis espacial-temporal a nivel macro usando POD.

Matriz Snapshot X:
- Filas (Espacio): Estados (UF)
- Columnas (Tiempo): Agrupación mensual
- Valores: Cantidad de accidentes por estado/mes

Permite identificar:
- Tendencias nacionales (Modo 1)
- Contrastes regionales (Modo 2+)
- Dinámicas opuestas entre estados
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

# ============================================================
# Funciones
# ============================================================

def load_estados_data():
	"""
	Carga datos agregados por estado y mes desde la base de datos.

	Returns:
		DataFrame con: uf, mes_anio, count
	"""
	conn = sqlite3.connect(DB_PATH)

	query = """
	SELECT
		uf,
		strftime('%Y-%m', date) as mes_anio,
		COUNT(*) as count
	FROM accidents_spatial
	WHERE uf IS NOT NULL
	GROUP BY uf, mes_anio
	ORDER BY uf, mes_anio
	"""

	df = pd.read_sql_query(query, conn)
	conn.close()

	return df


def build_estados_matrix(df):
	"""
	Construye la matriz snapshot de estados × tiempo.

	Args:
		df: DataFrame con columnas 'uf', 'mes_anio', 'count'

	Returns:
		X: Matriz numpy (n_estados, n_meses)
		estados: Array con los códigos de los estados
		meses: Array con los períodos mensuales
	"""
	# Crear matriz de conteo (pivot table)
	matriz_X = df.pivot_table(index='uf', columns='mes_anio', values='count', fill_value=0)

	X = matriz_X.values
	estados = matriz_X.index.values
	meses = matriz_X.columns.values

	return X, estados, meses


def compute_pod(X, center=True):
	"""Calcula POD usando SVD."""
	if center:
		X_mean = X.mean(axis=1, keepdims=True)
		X_centered = X - X_mean
	else:
		X_mean = np.zeros((X.shape[0], 1))
		X_centered = X

	U, S, Vt = np.linalg.svd(X_centered, full_matrices=False)
	return U, S, Vt, X_mean


def plot_results(X, U, S, Vt, estados, meses):
	"""Genera visualizaciones del análisis POD macro."""
	os.makedirs(OUTPUT_DIR, exist_ok=True)

	fig, axs = plt.subplots(2, 1, figsize=(14, 12))

	# A. Modo 1 Temporal: Tendencia Nacional
	axs[0].plot(range(len(Vt[0, :])), Vt[0, :], 'k-', linewidth=2)
	axs[0].set_title('Modo 1 Temporal: Tendencia Nacional de Accidentes en Brasil',
	                 fontsize=13, fontweight='bold')
	axs[0].set_ylabel('Fluctuación (coeficiente temporal)')
	axs[0].set_xlabel('Tiempo (Meses desde inicio)')
	axs[0].grid(True, alpha=0.3)
	axs[0].axhline(y=0, color='gray', linestyle='--', alpha=0.5)

	# Añadir anotaciones temporales
	n_years = len(meses) // 12
	for year in range(0, n_years, 2):
		month_idx = year * 12
		if month_idx < len(meses):
			year_label = meses[month_idx][:4]
			axs[0].axvline(x=month_idx, color='gray', linestyle=':', alpha=0.3)
			axs[0].text(month_idx, axs[0].get_ylim()[1]*0.95, year_label,
			            ha='center', fontsize=8, alpha=0.7)

	# B. Modo 2 Espacial: Contraste Regional
	colores = ['red' if x < 0 else 'blue' for x in U[:, 1]]
	bars = axs[1].bar(estados, U[:, 1], color=colores, edgecolor='black', linewidth=0.5)
	axs[1].set_title('Modo 2 Espacial: Contraste Regional\n(Rojo: Comportamiento opuesto | Azul: Comportamiento normal)',
	                 fontsize=13, fontweight='bold')
	axs[1].set_ylabel('Coeficiente del Modo')
	axs[1].set_xlabel('Estado (UF)')
	axs[1].grid(True, axis='y', alpha=0.3)
	axs[1].axhline(y=0, color='black', linestyle='-', linewidth=1.5)

	# Rotar labels para mejor legibilidad
	axs[1].tick_params(axis='x', rotation=45)

	# Añadir leyenda explicativa
	from matplotlib.patches import Patch
	legend_elements = [
		Patch(facecolor='blue', edgecolor='black', label='Dinámica dominante'),
		Patch(facecolor='red', edgecolor='black', label='Dinámica opuesta')
	]
	axs[1].legend(handles=legend_elements, loc='upper right')

	plt.tight_layout()
	plt.savefig(f"{OUTPUT_DIR}/pod_estados_macro.png", dpi=300, bbox_inches='tight')
	print(f"   ✓ Gráfico guardado: {OUTPUT_DIR}/pod_estados_macro.png")

	# Gráfico adicional: Energía de los modos
	fig2, ax = plt.subplots(figsize=(10, 6))
	energy = S**2 / np.sum(S**2) * 100
	n_modes_plot = min(10, len(S))

	bars = ax.bar(range(1, n_modes_plot + 1), energy[:n_modes_plot], color='steelblue', edgecolor='black')
	ax.set_title('Energía de los Modos POD (Estados)', fontsize=13, fontweight='bold')
	ax.set_ylabel('Energía (%)')
	ax.set_xlabel('Modo #')
	ax.grid(True, axis='y', alpha=0.3)

	# Añadir valores sobre las barras
	for i, bar in enumerate(bars):
		height = bar.get_height()
		ax.text(bar.get_x() + bar.get_width()/2., height,
		        f'{height:.1f}%', ha='center', va='bottom', fontsize=9)

	plt.tight_layout()
	plt.savefig(f"{OUTPUT_DIR}/pod_estados_energia.png", dpi=300, bbox_inches='tight')
	print(f"   ✓ Gráfico guardado: {OUTPUT_DIR}/pod_estados_energia.png")

	plt.show()


def print_statistics(X, S, U, estados):
	"""Imprime estadísticas del análisis."""
	energy = S**2 / np.sum(S**2) * 100
	cum_energy = np.cumsum(energy)

	print("\n" + "="*60)
	print("ESTADÍSTICAS POD MACRO (ESTADOS)")
	print("="*60)
	print(f"Dimensiones de la matriz: {X.shape[0]} estados × {X.shape[1]} meses")
	print(f"Total de accidentes: {int(X.sum()):,}")

	print(f"\nEnergía de los primeros 5 modos:")
	for i in range(min(5, len(S))):
		print(f"  Modo {i+1}: {energy[i]:.2f}% (acumulado: {cum_energy[i]:.2f}%)")

	# Modos necesarios para 90% de energía
	n_modes_90 = np.argmax(cum_energy >= 90) + 1
	print(f"\nModos necesarios para 90% de energía: {n_modes_90}")

	# Análisis del Modo 2 (contraste regional)
	print(f"\nAnálisis del Modo 2 (Contraste Regional):")
	modo2 = U[:, 1]
	positivos_idx = modo2 > 0
	negativos_idx = modo2 < 0

	print(f"  Estados con coeficiente POSITIVO ({np.sum(positivos_idx)}):")
	estados_pos = [(estados[i], modo2[i]) for i in range(len(estados)) if positivos_idx[i]]
	estados_pos.sort(key=lambda x: x[1], reverse=True)
	for uf, coef in estados_pos[:5]:
		print(f"    {uf}: {coef:+.4f}")

	print(f"\n  Estados con coeficiente NEGATIVO ({np.sum(negativos_idx)}):")
	estados_neg = [(estados[i], modo2[i]) for i in range(len(estados)) if negativos_idx[i]]
	estados_neg.sort(key=lambda x: x[1])
	for uf, coef in estados_neg[:5]:
		print(f"    {uf}: {coef:+.4f}")

	print("="*60)


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
	print("="*60)
	print("POD MACRO: ANÁLISIS DE ESTADOS")
	print("="*60)

	# 1. Cargar datos
	print("\n1. Cargando datos agregados por estado...")
	df = load_estados_data()
	print(f"   ✓ Registros cargados: {len(df):,}")

	# 2. Construir matriz
	print("\n2. Construyendo matriz Estados × Tiempo...")
	X, estados, meses = build_estados_matrix(df)
	print(f"   ✓ Matriz generada: {X.shape[0]} estados × {X.shape[1]} meses")
	print(f"   ✓ Estados: {', '.join(estados)}")
	print(f"   ✓ Rango temporal: {meses[0]} a {meses[-1]}")

	# 3. Aplicar POD
	print("\n3. Aplicando POD (SVD)...")
	U, S, Vt, X_mean = compute_pod(X, center=True)
	print(f"   ✓ SVD completado: {len(S)} modos extraídos")

	# 4. Estadísticas
	print_statistics(X, S, U, estados)

	# 5. Visualizar
	print("\n4. Generando visualizaciones...")
	plot_results(X, U, S, Vt, estados, meses)

	print("\n✅ Análisis POD macro completado!")
	print("="*60)
