'''
    Web Scraping CNN Español Colombia
    Step #1
    Release Date : 2025-06-09
'''

#=====================#
# ---- Libraries ---- #
#=====================#

import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd
from datetime import datetime
import time
import sqlite3
import os
from pathlib import Path

#================================#
# ---- logger configuration ---- #
#================================#

logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)-15s - %(name)s - %(levelname)s - %(message)s'
        )
logger = logging.getLogger()

#================================#
# ---- Database Configuration ---#
#================================#

def get_database_path():
    """Obtiene la ruta de la base de datos en el folder databases"""
    current_dir = Path(__file__).parent  # Directorio del script actual
    project_root = current_dir.parent.parent  # Dos niveles arriba
    database_dir = project_root / 'databases'
    
    database_dir.mkdir(exist_ok=True)
    
    return database_dir / 'cnn_noticias.db'

def setup_sqlite_database():
    """Crea la tabla si no existe"""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS noticias_cnn (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            enlace TEXT NOT NULL UNIQUE,
            contenido_completo TEXT,
            fecha_extraccion DATETIME NOT NULL,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info(f"Base de datos configurada en: {db_path}")

def guardar_noticias_sqlite(df_noticias):
    """Guarda las noticias en SQLite, evitando duplicados"""
    if df_noticias.empty:
        logger.warning("No hay noticias para guardar")
        return
    
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    
    nuevas_noticias = 0
    duplicadas = 0
    
    for _, row in df_noticias.iterrows():
        try:
            # Intentar insertar, si ya existe el enlace se ignora
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO noticias_cnn 
                (titulo, enlace, contenido_completo, fecha_extraccion)
                VALUES (?, ?, ?, ?)
            ''', (row['titulo'], row['enlace'], row['contenido_completo'], row['fecha_extraccion']))
            
            if cursor.rowcount > 0:
                nuevas_noticias += 1
            else:
                duplicadas += 1
                
        except Exception as e:
            logger.error(f"Error al insertar noticia: {e}")
    
    conn.commit()
    conn.close()
    
    logger.info(f"Guardado completado: {nuevas_noticias} nuevas noticias, {duplicadas} duplicadas")

def consultar_noticias_sqlite(limit=10):
    """Consulta las últimas noticias"""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    
    query = f"""
    SELECT id, titulo, enlace, fecha_extraccion 
    FROM noticias_cnn 
    ORDER BY fecha_extraccion DESC 
    LIMIT {limit}
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    return df

def obtener_estadisticas_noticias():
    """Obtiene estadísticas de la base de datos"""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT 
        COUNT(*) as total_noticias,
        COUNT(DISTINCT DATE(fecha_extraccion)) as dias_con_extraccion,
        MIN(fecha_extraccion) as primera_extraccion,
        MAX(fecha_extraccion) as ultima_extraccion
    FROM noticias_cnn
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    return df

#=============================#
# ---- Principal Functions ---#
#=============================#

def scrape_cnn_noticias():
    """
    Extrae noticias de CNN Español Colombia y retorna listas
    """
    url = 'https://cnnespanol.cnn.com/colombia'
    
    try:
        logger.info(f'Iniciando extracción de noticias desde {url}')
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        
        contenedores = soup.find_all(attrs={'data-component-name': 'card'})
        logger.info(f'Encontrados {len(contenedores)} contenedores de noticias')
        
        titulos = []
        enlaces = []
        
        for contenedor in contenedores:
            enlace_tag = contenedor.find('a')
            titulo_tag = contenedor.find('span', class_='container__headline-text')
            
            if enlace_tag and titulo_tag:
                link_parcial = enlace_tag.get('href', '')
                link_completo = urljoin(url, link_parcial)
                titulo = titulo_tag.get_text(strip=True)
                
                if titulo and link_completo:
                    titulos.append(titulo)
                    enlaces.append(link_completo)
        
        logger.info(f'Extraídos {len(titulos)} títulos y enlaces válidos')
        return titulos, enlaces
        
    except Exception as e:
        logger.error(f"Error al extraer noticias: {e}")
        return [], []

def extraer_contenido_articulo(url_articulo):
    """
    Extrae el contenido completo de un artículo específico
    """
    try:
        response = requests.get(url_articulo, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Buscar el contenedor del artículo
        articulos = soup.find_all(class_='article__content-container')
        
        if articulos:
            contenedor_principal = articulos[0]
            contenido_limpio = contenedor_principal.get_text(separator='\n', strip=True)
            return contenido_limpio
        else:
            return "No se encontró el contenedor del artículo"
            
    except Exception as e:
        logger.warning(f"Error al extraer contenido de {url_articulo}: {e}")
        return f"Error al extraer contenido: {e}"

def procesar_y_guardar_noticias():
    """
    Función principal que extrae, procesa y guarda todas las noticias
    """
    logger.info("=== INICIANDO PROCESO DE EXTRACCIÓN CNN ===")
    
    # Extraer títulos y enlaces
    titulos, enlaces = scrape_cnn_noticias()
    
    if not titulos or not enlaces:
        logger.warning("No se pudieron extraer noticias")
        return
    
    logger.info(f"Procesando contenido completo de {len(titulos)} artículos...")
    
    # Listas para el DataFrame final
    todos_titulos = []
    todos_enlaces = []
    todos_contenidos = []
    fecha_extraccion = []
    
    # Extraer contenido de cada artículo
    for i, (titulo, enlace) in enumerate(zip(titulos, enlaces), 1):
        logger.info(f"Procesando artículo {i}/{len(titulos)}: {titulo[:50]}...")
        
        contenido = extraer_contenido_articulo(enlace)
        
        todos_titulos.append(titulo)
        todos_enlaces.append(enlace)
        todos_contenidos.append(contenido)
        fecha_extraccion.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # Pausa para no sobrecargar el servidor
        time.sleep(1)
    
    # Crear DataFrame
    df_completo = pd.DataFrame({
        'titulo': todos_titulos,
        'enlace': todos_enlaces,
        'contenido_completo': todos_contenidos,
        'fecha_extraccion': fecha_extraccion
    })
    
    # Guardar en base de datos
    guardar_noticias_sqlite(df_completo)
    
    logger.info(f"✅ Proceso completado! Total de artículos procesados: {len(df_completo)}")
    
    return df_completo

if __name__ == '__main__':
    logger.info("=== INICIANDO APLICACIÓN CNN SCRAPER ===")
    
    # Configurar base de datos
    setup_sqlite_database()
    
    # Procesar y guardar noticias
    df_noticias = procesar_y_guardar_noticias()
    
    if df_noticias is not None and not df_noticias.empty:
        # Mostrar estadísticas
        print("\n📊 ESTADÍSTICAS DE LA BASE DE DATOS:")
        stats = obtener_estadisticas_noticias()
        print(stats)
        
        # Mostrar últimas noticias
        print("\n📰 ÚLTIMAS 5 NOTICIAS EN LA BASE DE DATOS:")
        ultimas = consultar_noticias_sqlite(limit=5)
        print(ultimas[['id', 'titulo', 'fecha_extraccion']])
        
        # Mostrar ejemplo del primer artículo
        if len(df_noticias) > 0:
            print("\n" + "="*80)
            print("📰 EJEMPLO - PRIMER ARTÍCULO PROCESADO:")
            print("="*80)
            print(f"TÍTULO: {df_noticias['titulo'].iloc[0]}")
            print(f"ENLACE: {df_noticias['enlace'].iloc[0]}")
            print("-"*80)
            print(df_noticias['contenido_completo'].iloc[0][:500] + "...")
    
    logger.info("=== APLICACIÓN FINALIZADA ===")
