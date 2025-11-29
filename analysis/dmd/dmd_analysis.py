"""
DMD (Dynamic Mode Decomposition) Analysis

Análisis dinámico con predicción futura basado en DMD.
DMD modela el sistema como: x_{k+1} = A x_k

Permite:
- Identificar modos dinámicos del sistema
- Analizar estabilidad (eigenvalues)
- Predecir estados futuros
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
OUTPUT_DIR = "analysis/dmd/results"

# Caso de estudio: BR-101 en Santa Catarina
ESTADO = 'SC'
CARRETERA = 101
BIN_SIZE_KM = 10
N_MODOS = 15  # Número de modos DMD a usar
MESES_PREDICCION = 24  # Meses a predecir (2 años)

# ============================================================
# Funciones de Carga de Datos (reutilizadas de POD)
# ============================================================

def load_spatial_data(estado, carretera):
	"""Carga datos espaciales desde la base de datos."""
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
	"""Construye la matriz snapshot espacial-temporal."""
	max_km = df['km'].max()
	bins_espacio = np.arange(0, max_km + bin_size, bin_size)
	df['tramo_km'] = pd.cut(df['km'], bins=bins_espacio, labels=bins_espacio[:-1])

	matriz_X = pd.crosstab(df['tramo_km'], df['mes_anio'])
	X = matriz_X.values
	tramos = matriz_X.index.astype(float).values
	meses = matriz_X.columns.values

	return X, tramos, meses


# ============================================================
# Algoritmo DMD
# ============================================================

def dmd_exact(X, r=10):
	"""
	Implementación del algoritmo Exact DMD.

	Args:
		X: Matriz de datos (espacio × tiempo)
		r: Rango de reducción (número de modos)

	Returns:
		Phi: Modos DMD (espacio × r)
		eigenvalues: Autovalores (crecimiento/oscilación)
		b: Amplitudes iniciales
	"""
	# Matrices desplazadas en el tiempo
	X1 = X[:, :-1]  # Estados actuales
	X2 = X[:, 1:]   # Estados futuros (un paso adelante)

	# SVD reducida de X1
	U, S, Vh = np.linalg.svd(X1, full_matrices=False)
	Ur = U[:, :r]
	Sr = np.diag(S[:r])
	Vr = Vh[:r, :].T

	# Matriz Atilde (dinámica proyectada en espacio reducido)
	Atilde = Ur.T @ X2 @ Vr @ np.linalg.inv(Sr)

	# Eigendecomposición de Atilde
	eigenvalues, W = np.linalg.eig(Atilde)

	# Reconstrucción de modos DMD en espacio completo
	Phi = X2 @ Vr @ np.linalg.inv(Sr) @ W

	# Calcular amplitudes iniciales (proyección del estado inicial)
	x0 = X[:, 0]
	b = np.linalg.pinv(Phi) @ x0

	return Phi, eigenvalues, b


def predict_future(Phi, eigenvalues, b, n_timesteps):
	"""
	Predice estados futuros usando DMD.

	Args:
		Phi: Modos DMD
		eigenvalues: Autovalores
		b: Amplitudes iniciales
		n_timesteps: Número total de pasos (presente + futuro)

	Returns:
		X_dmd: Matriz predicha (espacio × tiempo)
	"""
	r = len(eigenvalues)
	time_dynamics = np.zeros((r, n_timesteps), dtype='complex')

	# Evolución temporal: coef_t = (lambda^t) * b
	for t in range(n_timesteps):
		time_dynamics[:, t] = (eigenvalues ** t) * b

	# Reconstrucción: X ≈ Phi @ time_dynamics
	X_dmd = (Phi @ time_dynamics).real

	return X_dmd


def analyze_stability(eigenvalues):
	"""
	Analiza la estabilidad del sistema basándose en los eigenvalues.

	Returns:
		Dict con información de estabilidad
	"""
	magnitudes = np.abs(eigenvalues)
	angles = np.angle(eigenvalues)
	frequencies = angles / (2 * np.pi)

	stability_info = {
		'stable': np.sum(magnitudes < 1),
		'neutral': np.sum(np.abs(magnitudes - 1) < 0.05),
		'unstable': np.sum(magnitudes > 1),
		'max_magnitude': magnitudes.max(),
		'min_magnitude': magnitudes.min()
	}

	return stability_info


# ============================================================
# Visualización
# ============================================================

def plot_dmd_results(X, X_dmd, eigenvalues, tiempo_actual, meses_futuros):
	"""Genera visualizaciones del análisis DMD."""
	os.makedirs(OUTPUT_DIR, exist_ok=True)

	fig, axs = plt.subplots(1, 2, figsize=(16, 6))

	# A. Mapa de predicción (Presente + Futuro)
	im = axs[0].imshow(X_dmd, aspect='auto', cmap='hot', interpolation='nearest')
	axs[0].set_title(f'Predicción DMD: Presente + {meses_futuros} meses futuros',
	                 fontsize=12, fontweight='bold')
	axs[0].axvline(tiempo_actual, color='cyan', linestyle='--', linewidth=2, label='Límite Presente/Futuro')
	axs[0].set_ylabel('Tramo (KM)')
	axs[0].set_xlabel('Tiempo (Meses)')
	axs[0].legend(loc='upper right')
	plt.colorbar(im, ax=axs[0], label='Accidentes (predicho)')

	# Añadir región sombreada para futuro
	axs[0].axvspan(tiempo_actual, X_dmd.shape[1], alpha=0.2, color='yellow', label='Predicción')

	# B. Análisis de estabilidad (Plano complejo)
	theta = np.linspace(0, 2*np.pi, 100)
	axs[1].plot(np.cos(theta), np.sin(theta), 'k--', linewidth=1.5, label='Círculo unitario')
	axs[1].scatter(eigenvalues.real, eigenvalues.imag, c='red', s=100, marker='x', linewidths=2,
	               label='Eigenvalues DMD')
	axs[1].set_title('Estabilidad del Sistema\n(Eigenvalues en Plano Complejo)',
	                 fontsize=12, fontweight='bold')
	axs[1].set_xlabel('Parte Real')
	axs[1].set_ylabel('Parte Imaginaria')
	axs[1].grid(True, alpha=0.3)
	axs[1].axis('equal')
	axs[1].legend()

	# Añadir anotaciones sobre estabilidad
	inside = np.sum(np.abs(eigenvalues) < 1)
	on_circle = np.sum(np.abs(np.abs(eigenvalues) - 1) < 0.05)
	outside = np.sum(np.abs(eigenvalues) > 1)

	stability_text = f"Dentro círculo (decae): {inside}\n"
	stability_text += f"Sobre círculo (estable): {on_circle}\n"
	stability_text += f"Fuera círculo (crece): {outside}"

	axs[1].text(0.05, 0.95, stability_text, transform=axs[1].transAxes,
	            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
	            fontsize=9)

	plt.tight_layout()
	plt.savefig(f"{OUTPUT_DIR}/dmd_prediction_br{CARRETERA}_{ESTADO}.png", dpi=300, bbox_inches='tight')
	print(f"   ✓ Gráfico guardado: {OUTPUT_DIR}/dmd_prediction_br{CARRETERA}_{ESTADO}.png")

	# Gráfico adicional: Comparación Original vs DMD
	fig2, axs2 = plt.subplots(1, 2, figsize=(16, 6))

	im1 = axs2[0].imshow(X, aspect='auto', cmap='hot', interpolation='nearest')
	axs2[0].set_title('Datos Originales (Observados)', fontsize=12, fontweight='bold')
	axs2[0].set_ylabel('Tramo (KM)')
	axs2[0].set_xlabel('Tiempo (Meses)')
	plt.colorbar(im1, ax=axs2[0], label='Accidentes')

	im2 = axs2[1].imshow(X_dmd[:, :X.shape[1]], aspect='auto', cmap='hot', interpolation='nearest')
	axs2[1].set_title('Reconstrucción DMD (Ajuste)', fontsize=12, fontweight='bold')
	axs2[1].set_ylabel('Tramo (KM)')
	axs2[1].set_xlabel('Tiempo (Meses)')
	plt.colorbar(im2, ax=axs2[1], label='Accidentes')

	plt.tight_layout()
	plt.savefig(f"{OUTPUT_DIR}/dmd_comparison_br{CARRETERA}_{ESTADO}.png", dpi=300, bbox_inches='tight')
	print(f"   ✓ Gráfico guardado: {OUTPUT_DIR}/dmd_comparison_br{CARRETERA}_{ESTADO}.png")

	plt.show()


def print_statistics(X, eigenvalues, stability_info):
	"""Imprime estadísticas del análisis DMD."""
	print("\n" + "="*60)
	print("ESTADÍSTICAS DMD")
	print("="*60)
	print(f"Modos DMD utilizados: {len(eigenvalues)}")
	print(f"\nEstabilidad del sistema:")
	print(f"  Modos decrecientes (|λ| < 1): {stability_info['stable']}")
	print(f"  Modos estables (|λ| ≈ 1):     {stability_info['neutral']}")
	print(f"  Modos crecientes (|λ| > 1):   {stability_info['unstable']}")
	print(f"  Magnitud máxima: {stability_info['max_magnitude']:.3f}")
	print(f"  Magnitud mínima: {stability_info['min_magnitude']:.3f}")

	print(f"\nEigenvalues con mayor magnitud (top 5):")
	sorted_idx = np.argsort(np.abs(eigenvalues))[::-1]
	for i in range(min(5, len(eigenvalues))):
		idx = sorted_idx[i]
		eig = eigenvalues[idx]
		mag = np.abs(eig)
		freq = np.angle(eig) / (2 * np.pi)
		period = 1/freq if freq != 0 else np.inf
		print(f"  Modo {i+1}: |λ|={mag:.3f}, frecuencia={freq:.4f}, período≈{period:.1f} meses")

	print("="*60)


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
	print("="*60)
	print(f"DMD ANALYSIS: BR-{CARRETERA} en {ESTADO}")
	print("="*60)

	# 1. Cargar datos y construir matriz
	print(f"\n1. Cargando datos...")
	df = load_spatial_data(ESTADO, CARRETERA)
	X, tramos, meses = build_snapshot_matrix(df, bin_size=BIN_SIZE_KM)
	print(f"   ✓ Matriz generada: {X.shape[0]} tramos × {X.shape[1]} meses")

	# Centrar datos (restar media temporal)
	X_mean = X.mean(axis=1, keepdims=True)
	X_centered = X - X_mean

	# 2. Aplicar DMD
	print(f"\n2. Aplicando DMD (r={N_MODOS} modos)...")
	Phi, eigenvalues, b = dmd_exact(X_centered, r=N_MODOS)
	print(f"   ✓ DMD completado: {len(eigenvalues)} modos extraídos")

	# 3. Analizar estabilidad
	print("\n3. Analizando estabilidad...")
	stability_info = analyze_stability(eigenvalues)

	# 4. Predicción futura
	print(f"\n4. Generando predicción ({MESES_PREDICCION} meses futuros)...")
	tiempo_actual = X.shape[1]
	tiempo_total = tiempo_actual + MESES_PREDICCION
	X_dmd = predict_future(Phi, eigenvalues, b, tiempo_total) + X_mean
	print(f"   ✓ Predicción generada: {X_dmd.shape[0]} × {X_dmd.shape[1]}")

	# 5. Estadísticas
	print_statistics(X, eigenvalues, stability_info)

	# 6. Visualizar
	print("\n5. Generando visualizaciones...")
	plot_dmd_results(X, X_dmd, eigenvalues, tiempo_actual, MESES_PREDICCION)

	print("\n✅ Análisis DMD completado!")
	print("="*60)
