import sqlite3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ============================================================
# 0. Carga de datos y construcción de la matriz de snapshots
# ============================================================

DB_PATH = "../extracted/analysis_data.db" # ajustar ruta si es necesario

conn = sqlite3.connect(DB_PATH)
daily = pd.read_sql_query("SELECT * FROM accidents_daily;", conn)
conn.close()

daily["date"] = pd.to_datetime(daily["date"])
daily = daily.sort_values("date")

# Serie diaria de accidentes
y = daily["accidents_count"].values
len_series = len(y)

plt.figure(figsize=(10, 4))
plt.plot(daily["date"], y, linewidth=1)
plt.xlabel("Fecha")
plt.ylabel("Número de accidentes")
plt.title("Serie temporal diaria de accidentes")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("fig1_original_daily_series.png")
plt.close()

# Parámetro de ventana deslizante
window_size = 30
n_windows = len_series - window_size + 1

# Matriz de snapshots X de tamaño (30, n_windows)
X = np.zeros((window_size, n_windows))
for j in range(n_windows):
    X[:, j] = y[j:j+window_size]

print(f"Matriz de snapshots X tiene forma: {X.shape}")

# ============================================================
# 1. SVD de X
# ============================================================

U, S, Vt = np.linalg.svd(X, full_matrices=False)
energy = S**2
cum_energy = np.cumsum(energy) / np.sum(energy)

# ============================================================
# 2. Espectro de valores singulares
# ============================================================

plt.figure()
plt.plot(np.arange(1, len(S)+1), S, marker="o")
plt.yscale("log")
plt.xlabel("Índice del modo")
plt.ylabel("Valor singular σ")
plt.title("Espectro de valores singulares (SVD)")
plt.tight_layout()
plt.savefig("fig2_svd_spectrum.png")
plt.close()

# ============================================================
# 3. Energía acumulada
# ============================================================

plt.figure()
plt.plot(np.arange(1, len(S)+1), cum_energy, marker="o")
plt.xlabel("Número de modos k")
plt.ylabel("Energía acumulada")
plt.title("Energía acumulada de los modos SVD")
plt.grid(True)
plt.tight_layout()
plt.savefig("fig3_cumulative_energy.png")
plt.close()

# Imprimir tabla de las primeras energías
max_modes = min(10, len(S))
explained = (energy[:max_modes] / np.sum(energy)) * 100.0
cum_explained = cum_energy[:max_modes] * 100.0

print("\\nPrimeros modos y su energía explicada:")
print("k\tenergia_%\tenergia_acum_%")
for k in range(1, max_modes+1):
    print(f"{k}\t{explained[k-1]:.3f}\t\t{cum_explained[k-1]:.3f}")

# ============================================================
# 4. Modos espaciales (U) – primeros 3
# ============================================================

days = np.arange(1, window_size+1)
plt.figure()
for i in range(min(3, U.shape[1])):
    plt.plot(days, U[:, i], label=f"Modo {i+1}")
plt.xlabel("Día dentro de la ventana (1–30)")
plt.ylabel("Amplitud del modo")
plt.title("Primeros 3 modos espaciales (POD)")
plt.legend()
plt.tight_layout()
plt.savefig("fig4_spatial_modes.png")
plt.close()

# ============================================================
# 5. Coeficientes temporales (Vt) – primeros 3
# ============================================================

windows_idx = np.arange(1, n_windows+1)
plt.figure()
for i in range(min(3, Vt.shape[0])):
    plt.plot(windows_idx, Vt[i, :], label=f"Coeficiente modo {i+1}")
plt.xlabel("Índice de ventana (snapshot)")
plt.ylabel("Coeficiente temporal")
plt.title("Primeros 3 coeficientes temporales")
plt.legend()
plt.tight_layout()
plt.savefig("fig5_temporal_coeffs.png")
plt.close()


# ============================================================
# 6. Error de reconstrucción vs k
# ============================================================

errors = []
ks = np.arange(1, len(S)+1)
for k in ks:
    Sk = np.diag(S[:k])
    Xk = U[:, :k] @ Sk @ Vt[:k, :]
    err = np.linalg.norm(X - Xk, "fro")
    errors.append(err)

plt.figure()
plt.plot(ks, errors, marker="o")
plt.xlabel("Número de modos k")
plt.ylabel("Error de reconstrucción ||X - X_k||_F")
plt.title("Error de reconstrucción en función de k")
plt.grid(True)
plt.tight_layout()
plt.savefig("fig6_reconstruction_error.png")
plt.close()

# ============================================================
# 7. Error por ventana para k que captura ~95% de la energía
# ============================================================

k95 = int(np.searchsorted(cum_energy, 0.95) + 1)
Sk95 = np.diag(S[:k95])
Xk95 = U[:, :k95] @ Sk95 @ Vt[:k95, :]
window_errors = np.linalg.norm(X - Xk95, axis=0)

plt.figure()
plt.plot(windows_idx, window_errors)
plt.xlabel("Índice de ventana")
plt.ylabel("Error de reconstrucción (k ≈ 95% energía)")
plt.title(f"Error por ventana usando k={k95} modos (~95% energía)")
plt.tight_layout()
plt.savefig("fig7_window_errors_95.png")
plt.close()

print(f"\\nNúmero de modos para ~95% energía: k95 = {k95}")

# ============================================================
# 9. Ejemplo de reconstrucción de una ventana
# ============================================================

def plot_reconstruction_for_window(j, name_prefix):
    original = X[:, j]
    ks = [1, 3, 5]
    ks = [k for k in ks if k <= len(S)]
    
    plt.figure()
    days = np.arange(1, window_size+1)
    plt.plot(days, original, label="Original")
    for k in ks:
        Sk = np.diag(S[:k])
        Xk = U[:, :k] @ Sk @ Vt[:k, :]
        recon = Xk[:, j]
        plt.plot(days, recon, label=f"Recon k={k}")
    plt.xlabel("Día dentro de la ventana (1–30)")
    plt.ylabel("accidents_count")
    plt.title(f"Reconstrucción ventana {j+1} (original vs modos)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{name_prefix}_window_{j+1}.png")
    plt.close()

# Ventana "central"
idx_central = n_windows // 2
plot_reconstruction_for_window(idx_central, "central")

# Ventana con mayor error usando k95
idx_anom = int(np.argmax(window_errors))
plot_reconstruction_for_window(idx_anom, "anomalous")
print(f"Ventana central: {idx_central+1}, ventana más anómala (k95): {idx_anom+1}")

# ============================================================
# 8. Heatmap de X (opcionalmente submuestreado)
# ============================================================

step = max(n_windows // 500, 1)  # a lo sumo 500 columnas
X_sub = X[:, ::step]

plt.figure()
plt.imshow(X_sub, aspect="auto", origin="lower")
plt.colorbar(label="accidents_count")
plt.xlabel("Ventanas (submuestreadas)")
plt.ylabel("Días dentro de la ventana")
plt.title("Heatmap de la matriz de snapshots X")
plt.tight_layout()
plt.savefig("fig10_X_heatmap.png")
plt.close()