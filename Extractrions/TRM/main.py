'''
    Web Scraping to TRM (Colombia)
    Step #1
    Release Date : 2025-06-09
'''

#=====================#
# ---- Libraries ---- #
#=====================#

import logging
import requests
from bs4 import BeautifulSoup
import pandas as pd 
from datetime import datetime
import sqlite3
from sqlalchemy import create_engine

#================================#
# ---- logger configuration ---- #
#================================#

logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)-15s - %(name)s - %(levelname)s - %(message)s'
        )
logger = logging.getLogger()

# ==============================================
# Paso: SQLite (Base de datos local simple)
# ==============================================

def setup_sqlite_database(db_path='trm_database.db'):
    """Crea la tabla si no existe"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trm_historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            valor_trm TEXT NOT NULL,
            fecha_extraccion DATETIME NOT NULL,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Base de datos SQLite configurada correctamente")

def obtener_y_guardar_trm_sqlite(db_path='trm_database.db'):
    """Extrae TRM y la guarda en SQLite"""
    
    df_trm = trm()
    
    if df_trm.empty:
        logger.warning("No se pudo obtener el valor de TRM")
        return
    
    # Conectar a SQLite y guardar
    conn = sqlite3.connect(db_path)
    
    # Renombrar columnas para que coincidan con la base de datos
    df_trm_renamed = df_trm.rename(columns={
        'TRM': 'valor_trm',
        'Fecha': 'fecha_extraccion'
    })
    
    # Insertar nuevo registro
    df_trm_renamed.to_sql('trm_historico', conn, if_exists='append', index=False)
    
    logger.info(f"TRM guardado: {df_trm['TRM'].iloc[0]} - {df_trm['Fecha'].iloc[0]}")
    
    conn.close()

def consultar_trm_sqlite(db_path='trm_database.db', limit=10):
    """Consulta los últimos registros de TRM"""
    conn = sqlite3.connect(db_path)
    
    query = f"""
    SELECT * FROM trm_historico 
    ORDER BY fecha_extraccion DESC 
    LIMIT {limit}
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    return df

#=============================#
# ---- Principal Function ----#
#=============================#

def trm():
    '''
    TRM web scraping process 
    Input: None,
    Output: DataFrame with TRM and Date
    '''

    url_dolar = 'https://dolar.wilkinsonpc.com.co/'
    try:
        logger.info(f'Inicializando web scraping con {url_dolar}')
        response = requests.get(url_dolar, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        valor_span = soup.find('span', class_=['sube-numero', 'baja-numero', 'dolar-valor'])
        
        if valor_span is None:
            logger.warning(f'No se encontró la TRM para {datetime.now()}')
            return pd.DataFrame()

        df_trm = pd.DataFrame({
            'TRM': [valor_span.get_text(strip=True)],
            'Fecha': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        })
        
        logger.info('Proceso completado exitosamente')
        return df_trm
        
    except requests.exceptions.RequestException as error:
        logger.error(f'Error de red: {error}')
        return pd.DataFrame()
    except Exception as error:
        logger.error(f"Error inesperado: {error}")
        return pd.DataFrame()

if __name__ == '__main__':
    logger.info("Iniciando aplicación TRM Scraper")
    
    # Configurar base de datos
    setup_sqlite_database()
    
    # Obtener y guardar TRM
    obtener_y_guardar_trm_sqlite()
    
    # Mostrar últimos registros
    print("\n📊 Último registro en la base de datos:")
    ultimos = consultar_trm_sqlite(limit=1)
    print(ultimos)
    
    logger.info("Aplicación finalizada")