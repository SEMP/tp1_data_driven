import os
import zipfile
import pandas as pd
import gdown

def descargar_zip(file_id, output_path):
    """Descarga el archivo desde Google Drive."""
    # fuzzy=True ayuda a gdown a encontrar el nombre correcto si es necesario
    gdown.download(id=file_id, output=output_path, quiet=False, fuzzy=True)

def descomprimir_y_limpiar(zip_path, extract_to):
    """Descomprime el zip en la carpeta destino y elimina el zip. (No cambia el nombre del archivo descomprimido)"""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"Descomprimido en: {extract_to}")
        
        # Eliminar el archivo zip tras la extracción
        os.remove(zip_path)
        print(f"Eliminado archivo temporal: {zip_path}")
    except zipfile.BadZipFile:
        print(f"Error: El archivo {zip_path} no es un zip válido.")

def descargar_y_descomprimir_datos(csv_enlaces, carpeta='data'):
    """Descarga y procesa los datos según el CSV de enlaces."""
    
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)

    df = pd.read_csv(csv_enlaces)

    for index, row in df.iterrows():
        año = row['año']
        drive_id = row['drive_id']
        
        # Nombre esperado del archivo final y del zip temporal
        nombre_csv_final = f"datatran{año}.csv"
        ruta_csv_final = os.path.join(carpeta, nombre_csv_final)
        ruta_zip_temp = os.path.join(carpeta, f"temp_{año}.zip")

        if os.path.exists(ruta_csv_final):
            print(f"El archivo {nombre_csv_final} ya existe. Saltando...")
        else:
            print(f"Descargando datos para el año {año}...")
            descargar_zip(drive_id, ruta_zip_temp)
            descomprimir_y_limpiar(ruta_zip_temp, carpeta)

if __name__ == "__main__":
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    enlaces_path = os.path.join(script_dir, 'enlaces.csv')

    descargar_y_descomprimir_datos(enlaces_path)