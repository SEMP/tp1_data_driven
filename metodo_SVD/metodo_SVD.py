import sqlite3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ============================================================
# 0. Carga de datos desde la base de datos
# ============================================================

DB_PATH = "extracted/analysis_data.db"  # ajusta la ruta si hace falta

def load_accident_series(db_path=DB_PATH, table="accidents_daily"):
    """
    Carga la serie temporal de accidentes desde la base de datos SQLite.

    Devuelve
    --------
    t : ndarray
        Vector de fechas (como objetos datetime64).
    x : ndarray
        Serie de accidentes (float).
    df : DataFrame
        DataFrame completo por si quieres inspeccionarlo.
    """
    con = sqlite3.connect(db_path)
    df = pd.read_sql_query(
        f"SELECT date, accidents_count FROM {table} ORDER BY date ASC",
        con,
        parse_dates=["date"],
    )
    con.close()

    t = df["date"].values
    x = df["accidents_count"].astype(float).values
    return t, x, df


# ============================================================
# 1. Construcción de matriz de snapshots (time-delay embedding)
# ============================================================

def build_snapshot_matrix(x, window_size):
    """
    Construye una matriz de snapshots a partir de una serie 1D.

    Cada columna es un 'snapshot' que contiene una ventana deslizante:
        snapshot k = [x_k, x_{k+1}, ..., x_{k+window_size-1}]^T

    Parámetros
    ----------
    x : ndarray de forma (N,)
        Serie temporal (por ejemplo, accidentes diarios).
    window_size : int
        Tamaño de la ventana (nº de días por snapshot).

    Devuelve
    --------
    X : ndarray de forma (window_size, n_snapshots)
        Matriz de snapshots.
    """
    N = len(x)
    if window_size > N:
        raise ValueError("window_size no puede ser mayor que la longitud de la serie")

    n_snapshots = N - window_size + 1
    X = np.zeros((window_size, n_snapshots))

    for k in range(n_snapshots):
        X[:, k] = x[k : k + window_size]

    return X


# ============================================================
# 2. SVD (Singular Value Decomposition)
# ============================================================

def compute_svd(X):
    """
    La función compute_svd recibe una matriz X (la matriz de snapshots) y
    calcula la descomposición en valores singulares (SVD) de la matriz X.
                            X≈UΣ(V^T)
    En código, eso se escribe como:
    X ≈ U @ np.diag(S) @ Vt

    Devuelve
    --------
    U : ndarray (m, r), modos de la base en el “espacio de estados” (filas de X)
    S : ndarray (r,), valores singulares (importancia/energía de cada modo)
    Vt: ndarray (r, n), patrones temporales (columnas de X) pero transpuestos
    """
    U, S, Vt = np.linalg.svd(X, full_matrices=False)
    return U, S, Vt

# ============================================================
# 3. POD (Proper Orthogonal Decomposition)
#    (esencialmente SVD + interpretación física)
# ============================================================

def compute_pod(X, center=True):
    """
    Calcula los modos POD a partir de una matriz de snapshots.

    Convención: cada columna de X es un snapshot.

    Parámetros
    ----------
    X : ndarray (m, n)
        Matriz de snapshots.
    center : bool
        Si True, resta la media de cada fila (campo medio).

    Devuelve
    --------
    modes : ndarray (m, r)
        Modos POD (ortogonales en el espacio de estados).
    temporal_coeffs : ndarray (r, n)
        Coeficientes temporales de cada modo.
    singular_values : ndarray (r,)
        Valores singulares (relacionados con la energía de cada modo).
    mean_field : ndarray (m, 1)
        Campo medio (0 si center=False).
    """
    if center:
        mean_field = X.mean(axis=1, keepdims=True)
        Xc = X - mean_field
    else:
        mean_field = np.zeros((X.shape[0], 1))
        Xc = X

    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)

    modes = U                           # modos espaciales (aquí: patrones en la ventana)
    temporal_coeffs = np.diag(S) @ Vt   # evolución temporal de cada modo

    return modes, temporal_coeffs, S, mean_field

# ============================================================
# 5. Ejemplo de uso con la base de datos
# ============================================================

if __name__ == "__main__":
    # 1) Cargar la serie de accidentes
    t, x, df = load_accident_series()
    print(f"Nº de días cargados: {len(x)}")
    print("t (fechas):", t[:5])            # primeras 5 fechas
    print("x (accidentes):", x[:5])         # primeros 5 valores
    print("df (dataframe):")
    print(df.head())                        # primeras 5 filas del DataFrame

    # Graficar serie original
    plt.figure()
    plt.plot(df["date"], x)
    plt.xlabel("Fecha")
    plt.ylabel("Número de accidentes")
    plt.title("Serie temporal diaria de accidentes")
    plt.tight_layout()
    plt.savefig("fig1_timeseries.png", dpi=300, bbox_inches="tight")  # <<< guardar la imagen

    # 2) Construir matriz de snapshots con una ventana de, por ejemplo, 30 días
    window_size = 30  # puedes jugar con este parámetro
    X = build_snapshot_matrix(x, window_size)
    print(f"Matriz de snapshots X tiene forma: {X.shape}") # filas y columnas
    #Para window_size=30 por ejemplo se tiene (30, 6850), esto indica que se está embebiendo la serie en ventanas de 30 días y se obtuvo 6850 ventanas.
    print("Primer snapshot (columna 0):")
    print(X[:, 0])  # días 0 a 29
    print("Segundo snapshot (columna 1):")
    print(X[:, 1])  # días 1 a 30
    print("Primeras 3 columnas de X:")
    print(X[:, :3])

    # --------------------------------------------------------
    # SVD
    # --------------------------------------------------------
    U, S, Vt = compute_svd(X)
    print("\n=== SVD ===")
    print("U shape:", U.shape)
    print("S (valores singulares):", S)
    print("Valores singulares (primeros 5):", S[:5])
    print("Vt shape:", Vt.shape)

    # --------------------------------------------------------
    # POD
    # --------------------------------------------------------
    modes_pod, coeffs_pod, S_pod, mean_field = compute_pod(X, center=True)
    print("\n=== POD ===")
    print("Valores singulares POD (primeros 5):", S_pod[:5])
    # modes_pod[:, 0] = modo dominante
    # coeffs_pod[0, :] = evolución temporal del modo dominante

    # Energía acumulada de los valores singulares
    energy = S**2 / np.sum(S**2)
    cum_energy = np.cumsum(energy)

    plt.figure()
    plt.stem(range(1, len(S) + 1), S)
    plt.xlabel("Índice del modo")
    plt.ylabel("Valor singular")
    plt.title("Espectro de valores singulares (SVD/POD)")
    plt.tight_layout()
    plt.savefig("fig2_svd_spectrum.png", dpi=300, bbox_inches="tight")

    plt.figure()
    plt.plot(range(1, len(cum_energy) + 1), cum_energy, marker="o")
    plt.xlabel("Número de modos")
    plt.ylabel("Energía acumulada")
    plt.title("Energía acumulada de los modos POD")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("fig3_pod_energy.png", dpi=300, bbox_inches="tight")

    # Modo POD dominante (patrón medio en una ventana de 30 días)
    plt.figure()
    plt.plot(range(window_size), modes_pod[:, 0])
    plt.xlabel("Día dentro de la ventana")
    plt.ylabel("Amplitud del modo")
    plt.title("Modo POD dominante (patrón típico de 30 días)")
    plt.tight_layout()
    plt.savefig("fig4_pod_mode1.png", dpi=300, bbox_inches="tight")

    # Coeficientes temporales del modo dominante
    plt.figure()
    plt.plot(coeffs_pod[0, :])
    plt.xlabel("Índice de snapshot")
    plt.ylabel("Coeficiente temporal")
    plt.title("Evolución temporal del modo POD dominante")
    plt.tight_layout()
    plt.savefig("fig5_pod_coeff1.png", dpi=300, bbox_inches="tight")

    plt.show()