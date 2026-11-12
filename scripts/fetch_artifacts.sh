#!/usr/bin/env bash
# Descarga los artifacts que no se versionan (modelo) y prepara las muestras del aula.
# Equivalente multiplataforma: `make model data-course`.
set -euo pipefail
cd "$(dirname "$0")/.."
uv run python scripts/fetch_model.py
uv run python scripts/fetch_dataset.py --source course
