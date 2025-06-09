# time_series_news
Pipeline automatizado para extraer datos de TRM y noticias de Colombia.

## 🚀 Instalación Rápida

```bash
# Instalar y configurar todo
make dev-setup

# Ejecutar pipeline completo
make run-all

# Verificar resultados
make check-data
```

## 📋 Comandos Disponibles

```bash
make help              # Ver todos los comandos
make setup             # Configurar entorno
make run-trm           # Solo TRM
make run-news          # Solo noticias  
make run-all           # Ambos pipelines
make mlflow-all        # Con MLflow tracking
make status            # Ver estado del proyecto
```

## 📁 Estructura del Proyecto

```
├── TRM/
│   ├── main.py        # Pipeline TRM
│   └── trm_database.db
├── News/
│   ├── main.py        # Pipeline noticias
├── databases/
│   ├── trm_database.db
│   └── cnn_noticias.db
├── MLproject          # Configuración MLflow
├── Makefile          # Comandos de automatización
└── pyproject.toml    # Dependencias uv
```

## 🔧 Tecnologías

- **uv**: Gestión de dependencias ultrarrápida
- **MLflow**: Tracking y reproducibilidad  
- **SQLite**: Almacenamiento de datos
- **BeautifulSoup**: Web scraping
- **Pandas**: Procesamiento de datos