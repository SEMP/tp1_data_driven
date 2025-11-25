import re
import pandas as pd
import os
import numpy as np

def leer_y_preparar_dataframe(ruta_archivo):
    """
    Lee un archivo CSV, extrae el año del nombre del archivo y 
    agrega columnas faltantes para normalización.
    """
    nombre_archivo = os.path.basename(ruta_archivo)
    df = pd.read_csv(ruta_archivo, sep=';', encoding='latin1', dtype=str, low_memory=False)

    match_año = re.search(r'(\d{4})', nombre_archivo)
    año = int(match_año.group(1)) if match_año else 0

    # a partir del 2017 se tienen estas columnas
    cols_nuevas = ['latitude', 'longitude', 'regional', 'delegacia', 'uop']
    for col in cols_nuevas:
        if col not in df.columns:
            df[col] = np.nan
    
    return df, año

def normalizar_columnas_numericas(df):
    """
    Normaliza las columnas de tipo numérico (km, latitud, longitud, br) 
    convirtiéndolas a float o int.
    """
    cols_float = ['km', 'latitude', 'longitude']
    for col in cols_float:
        if col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce')

    if 'br' in df.columns:
        df['br'] = pd.to_numeric(df['br'], errors='coerce')
    
    return df

def normalizar_fechas_y_horas(df, año):
    """
    Normaliza las columnas de fecha y hora, y crea la columna 'data_hora'.
    """
    if 'data_inversa' in df.columns:
        if año == 2016:
            fmt = '%d/%m/%y'
        elif 2001 <= año <= 2011:
            fmt = '%d/%m/%Y'
        else:
            fmt = '%Y-%m-%d'
        df['data_inversa'] = pd.to_datetime(df['data_inversa'], format=fmt, errors='coerce')

    if 'horario' in df.columns:
        tiempo_delta = pd.to_timedelta(df['horario'].astype(str), errors='coerce')
        if 'data_inversa' in df.columns and pd.api.types.is_datetime64_any_dtype(df['data_inversa']):
            df['data_hora'] = df['data_inversa'] + tiempo_delta
        else:
            df['data_hora'] = tiempo_delta
            
    return df

def eliminar_columnas_redundantes(df):
    """
    Elimina columnas que ya no son necesarias después de la normalización.
    """
    cols_a_eliminar = ['ano', 'data_inversa', 'horario', 'dia_semana', 'fase_dia']
    for col in cols_a_eliminar:
        if col in df.columns:
            df.drop(columns=[col], inplace=True)
    return df

def corregir_uf_y_municipios(df):
    """
    Corrige y estandariza los nombres de municipios y UF, llenando valores
    faltantes de UF basados en un diccionario de correcciones.
    """
    correcciones_uf = {
        'TERRA NOVA DO NORTE': 'MT',
        'GUARANTA DO NORTE'  : 'MT',
        'MATUPA'             : 'MT',
        'PEIXOTO DE AZEVEDO' : 'MT', 
        'VALPARAISO DE GOIAS': 'GO',
        'SAO JOAO DE MERITI' : 'RJ',
        'TABOAO DA SERRA'    : 'SP',
    }

    if 'municipio' in df.columns:
        df['municipio'] = df['municipio'].str.strip().str.upper()
    if 'uf' in df.columns:
        df['uf'] = df['uf'].str.strip().str.upper()

        filtro_nulos = df['uf'].isna() | (df['uf'] == '(NULL)')
        if 'municipio' in df.columns:
            df.loc[filtro_nulos, 'uf'] = df.loc[filtro_nulos, 'municipio'].map(correcciones_uf)
            
    return df

def procesar_archivo(ruta_archivo):
    """
    Orquesta el procesamiento completo de un archivo, aplicando todas las
    transformaciones en secuencia.
    """
    nombre_archivo = os.path.basename(ruta_archivo)
    try:
        df, año = leer_y_preparar_dataframe(ruta_archivo)
        df = normalizar_columnas_numericas(df)
        df = normalizar_fechas_y_horas(df, año)
        df = eliminar_columnas_redundantes(df)
        df = corregir_uf_y_municipios(df)
        print(f"✅ Archivo {nombre_archivo} procesado exitosamente.")
        return df
    except Exception as e:
        import traceback
        print(f"❌ Error al procesar {nombre_archivo}: {e}")
        traceback.print_exc()
        return None
    
if __name__ == "__main__":
    # Ejemplo de uso, solo para probar el funcionamiento correcto con todos los archivos
    import glob
    data_path = 'data'
    csv_files = glob.glob(os.path.join(data_path, 'datatran*.csv'))

    for file in csv_files:
        procesar_archivo(file)
