# Atajos reproducibles. Todo pasa por uv (prohibido pip/requirements.txt — regla del curso).
# Multiplataforma: cada receta solo invoca uv/docker, sin rm/cp/grep, así corre igual en
# PowerShell, cmd, Git Bash, macOS y Linux.  Windows: winget install ezwinports.make

# Engram corre en WSL (el MCP de Claude Code usa ese binario y esa base de memoria).
# Cambiar aquí si se usa otra distro o ruta:  make memoria ENGRAM_DISTRO=Ubuntu-24.04
ENGRAM_DISTRO ?= Ubuntu
ENGRAM_BIN    ?= /home/linuxbrew/.linuxbrew/bin/engram
WSL_PROJECT   ?= /mnt/c/Neumonia
.PHONY: help install model data-course dataset-rsna dataset-kermany run api ui grpc proto \
        smoke test test-fast cov lint format check evaluate mlflow docker-build docker-up \
        docker-down docker-smoke hooks grafo memoria memoria-exportar memoria-buscar diagramas clean \
        seg ui-seg evaluate-loc ct-setup ct-precompute ui-ct

help:  ## Lista los comandos
	@uv run python -c "import re,sys; [print(f'  make {m[0]:<16} {m[1]}') for m in re.findall(r'^([a-z-]+):.*?## (.*)$$', open('Makefile', encoding='utf-8').read(), re.M)]"

install:  ## Crea .venv con las versiones exactas de uv.lock (dev, mlops y el extra liviano ct)
	uv sync --frozen --all-groups --extra ct

model:  ## Descarga conv_MLP_84.h5 y verifica su SHA-256
	uv run python scripts/fetch_model.py

data-course:  ## Descomprime JPG.zip/DICOM.zip del aula y genera el catálogo de metadatos
	uv run python scripts/fetch_dataset.py --source course

dataset-rsna:  ## Descarga RSNA Pneumonia (Kaggle, ~3.9 GB) y genera metadatos (subconjunto 2000)
	uv run python scripts/fetch_dataset.py --source rsna --subset 2000

dataset-kermany:  ## Descarga Chest X-Ray (Kermany, Kaggle, ~1.2 GB) y genera metadatos
	uv run python scripts/fetch_dataset.py --source kermany

run: ui  ## Alias de ui

api: model  ## API REST en http://localhost:8000/docs
	uv run neumonia-api

ui: model  ## Interfaz clínica Streamlit en http://localhost:8501
	uv run streamlit run src/neumonia/view/streamlit_app.py

seg:  ## Instala la segmentación pulmonar real (PyTorch + TorchXRayVision) y verifica PSPNet
	uv sync --all-groups --extra ct --extra seg
	uv run python scripts/fetch_lung_model.py

ui-seg: export NEUMONIA_LUNG_SEGMENTER = pspnet
ui-seg: model  ## UI con segmentación pulmonar real (requiere make seg una vez)
	uv run streamlit run src/neumonia/view/streamlit_app.py

ct-setup:  ## (Prototipo) Instala MEDPSeg en su propio entorno para tomografías (ADR-0010)
	uv run --extra ct python scripts/setup_medpseg.py

ct-precompute:  ## (Prototipo) Segmenta una tomografía: make ct-precompute CT=ruta.nii.gz
	uv run --extra ct python scripts/ct_precompute.py --ct "$(CT)"

ui-ct:  ## (Prototipo) Tomografía en 3D: pulmones, vía aérea, arterias y lesión (puerto 8502)
	uv run --extra ct streamlit run src/neumonia/view/ct_app.py --server.port 8502

grpc: model  ## Servidor gRPC en el puerto 50051
	uv run neumonia-grpc

proto:  ## Regenera los stubs gRPC desde neumonia.proto
	uv run python -m grpc_tools.protoc -I src --python_out=src --grpc_python_out=src src/neumonia/grpc_api/neumonia.proto

smoke: model  ## Smoke test del curso: carga, infiere y valida el contrato
	uv run python smoke_infer.py

test:  ## Todas las pruebas (pytest -v, patrón AAA)
	uv run pytest -v

test-fast:  ## Pruebas sin el modelo real ni las lentas
	uv run pytest -q -m "not model and not slow"

cov:  ## Pruebas con cobertura (compuerta: 80 %)
	uv run pytest -q --cov --cov-report=term-missing --cov-report=xml --cov-fail-under=80

lint:  ## Ruff (estilo y errores)
	uv run ruff check .

format:  ## Formatea con Ruff
	uv run ruff format .

check:  ## Compuerta local = la de CI: lint + formato + pruebas con cobertura
	uv run ruff check .
	uv run ruff format --check .
	uv run pytest -q --cov --cov-fail-under=80

evaluate: data-course  ## Evalúa el modelo y registra el experimento en MLflow
	uv run --group mlops python scripts/evaluate.py --metadata data/processed/course_metadata.csv

evaluate-loc: model  ## ¿Grad-CAM apunta a la lesión? Compara con las cajas de RSNA (300 casos)
	uv run --group mlops python scripts/evaluate_localization.py --limit 300

mlflow:  ## Interfaz de MLflow en http://127.0.0.1:5000
	uv run --group mlops mlflow ui --backend-store-uri sqlite:///mlflow.db

docker-build:  ## Construye las imágenes CPU (api y ui)
	docker compose build

docker-up:  ## Levanta api + ui + mlflow con Docker Compose
	docker compose up -d

docker-down:  ## Detiene los contenedores
	docker compose down

docker-smoke:  ## Verifica que el contenedor responde en /health y /predict
	uv run python scripts/container_smoke.py http://localhost:8000

grafo:  ## Reconstruye el grafo de conocimiento con graphify (AST, sin LLM)
	uv run graphify update .

memoria:  ## Importa la memoria del proyecto al Engram de WSL (.engram/chunks)
	wsl -d $(ENGRAM_DISTRO) --cd $(WSL_PROJECT) -e $(ENGRAM_BIN) sync --import

memoria-exportar:  ## Guarda/actualiza scripts/engram_memoria.py en Engram (WSL) y exporta a .engram/
	wsl -d $(ENGRAM_DISTRO) --cd $(WSL_PROJECT) -e env ENGRAM_BIN=$(ENGRAM_BIN) python3 scripts/engram_memoria.py

memoria-buscar:  ## Busca en la memoria del proyecto: make memoria-buscar Q="umbral"
	wsl -d $(ENGRAM_DISTRO) -e $(ENGRAM_BIN) search "$(Q)" --project neumonia

diagramas:  ## Exporta los diagramas Mermaid de docs/arquitectura a SVG (requiere Node.js)
	uv run python scripts/render_diagramas.py

hooks:  ## Instala los ganchos pre-commit
	uv run pre-commit install

clean:  ## Borra cachés y salidas de ejecución
	uv run python -c "import pathlib, shutil; h = pathlib.Path('.'); [shutil.rmtree(d, ignore_errors=True) for d in [*h.rglob('__pycache__'), h/'.pytest_cache', h/'.ruff_cache', h/'runtime', h/'htmlcov'] if '.venv' not in d.parts]"
