.PHONY: help install setup clean run-trm run-news run-all test format lint

# Variables
PYTHON := python
UV := uv

help: 
	@echo "Comandos disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: 
	@if ! command -v uv >/dev/null 2>&1; then \
		echo "Installing uv..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		export PATH="$$HOME/.cargo/bin:$$PATH"; \
	fi

setup: install 
	@echo "🔧 Configurando entorno con uv..."
	$(UV) venv .venv --python 3.11
	$(UV) pip install -e .
	@echo "✅ Entorno configurado correctamente"

setup-dev: setup 
	@echo "🛠️ Instalando dependencias de desarrollo..."
	$(UV) pip install pytest black isort
	@echo "✅ Entorno de desarrollo listo"

databases: 
	@echo "📁 Creando directorio databases..."
	@mkdir -p databases
	@echo "✅ Directorio databases creado"

run-trm: databases 
	@echo "💰 Ejecutando pipeline TRM..."
	@source .venv/bin/activate && $(PYTHON) TRM/main.py
	@echo "✅ Pipeline TRM completado"

run-news: databases ## Ejecuta el pipeline de noticias
	@echo "📰 Ejecutando pipeline de noticias..."
	@source .venv/bin/activate && $(PYTHON) News/main.py
	@echo "✅ Pipeline de noticias completado"

run-all: databases ## Ejecuta ambos pipelines
	@echo "🚀 Ejecutando pipeline completo..."
	@$(MAKE) run-trm
	@$(MAKE) run-news
	@echo "✅ Pipeline completo finalizado"

mlflow-trm: ## Ejecuta TRM con MLflow
	@echo "🔬 Ejecutando TRM pipeline con MLflow..."
	@source .venv/bin/activate && mlflow run . -e trm_pipeline
	@echo "✅ MLflow TRM completado"

mlflow-news: ## Ejecuta News con MLflow  
	@echo "🔬 Ejecutando News pipeline con MLflow..."
	@source .venv/bin/activate && mlflow run . -e news_pipeline
	@echo "✅ MLflow News completado"

mlflow-all: ## Ejecuta pipeline completo con MLflow
	@echo "🔬 Ejecutando pipeline completo con MLflow..."
	@source .venv/bin/activate && mlflow run . -e full_pipeline
	@echo "✅ MLflow pipeline completo finalizado"

check-data: ## Revisa el estado de las bases de datos
	@echo "📊 Verificando bases de datos..."
	@if [ -f "databases/trm_database.db" ]; then \
		echo "✅ TRM database existe"; \
		echo "Tamaño: $$(du -h databases/trm_database.db | cut -f1)"; \
	else \
		echo "❌ TRM database no existe"; \
	fi
	@if [ -f "databases/cnn_noticias.db" ]; then \
		echo "✅ CNN database existe"; \
		echo "Tamaño: $$(du -h databases/cnn_noticias.db | cut -f1)"; \
	else \
		echo "❌ CNN database no existe"; \
	fi

clean: ## Limpia archivos temporales y cache
	@echo "🧹 Limpiando archivos temporales..."
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name ".DS_Store" -delete
	@echo "✅ Limpieza completada"

clean-all: clean ## Limpia todo incluyendo entorno virtual y bases de datos
	@echo "🗑️ Limpieza completa..."
	@rm -rf .venv
	@rm -rf databases/*.db
	@echo "✅ Limpieza completa finalizada"

format: ## Formatea el código con black e isort
	@echo "🎨 Formateando código..."
	@source .venv/bin/activate && black TRM/ News/
	@source .venv/bin/activate && isort TRM/ News/
	@echo "✅ Código formateado"

lint: ## Verifica el formato del código
	@echo "🔍 Verificando formato del código..."
	@source .venv/bin/activate && black --check TRM/ News/
	@source .venv/bin/activate && isort --check-only TRM/ News/
	@echo "✅ Verificación completada"

test: ## Ejecuta tests (si los hay)
	@echo "🧪 Ejecutando tests..."
	@source .venv/bin/activate && pytest -v
	@echo "✅ Tests completados"

status: ## Muestra el estado del proyecto
	@echo "📋 Estado del proyecto:"
	@echo "Python: $$(python --version 2>&1)"
	@echo "UV disponible: $$(if command -v uv >/dev/null 2>&1; then echo "✅"; else echo "❌"; fi)"
	@echo "Entorno virtual: $$(if [ -d ".venv" ]; then echo "✅"; else echo "❌"; fi)"
	@echo "Directorio databases: $$(if [ -d "databases" ]; then echo "✅"; else echo "❌"; fi)"
	@$(MAKE) check-data

install-mlflow: setup 
	@echo "📊 Instalando MLflow..."
	@source .venv/bin/activate && $(UV) pip install mlflow
	@echo "✅ MLflow instalado"

mlflow-ui: 
	@echo "🌐 Iniciando MLflow UI en http://localhost:5000"
	@source .venv/bin/activate && mlflow ui


dev-setup: setup-dev databases 
	@echo "🚀 Entorno de desarrollo listo!"
	@$(MAKE) status

quick-run: run-all check-data 
	@echo "⚡ Ejecución rápida completada!"