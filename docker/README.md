# Docker CPU — Neumonía

| Requisito del curso | Implementación |
|---|---|
| Base `python:3.13-slim` | `python:3.13-slim-bookworm` (multi-etapa) |
| `uv sync --frozen` / `uv run` | `uv sync --frozen --no-dev` en el *builder*; el *runtime* lleva solo `.venv` |
| Copiar solo modelo y artifacts necesarios | El modelo se **descarga y verifica (SHA-256)** en el build; `.dockerignore` excluye datos, pruebas y `.h5` locales |
| Exponer 8000 y healthcheck `/health` | `EXPOSE 8000` + `HEALTHCHECK` |
| Sin CUDA ni GPU | TensorFlow CPU, `CUDA_VISIBLE_DEVICES=""` |
| Seguridad | Usuario no root `app` (uid 1000) |

```bash
docker build -f docker/Dockerfile -t neumonia:latest .
docker run --rm -p 8000:8000 neumonia:latest
uv run python scripts/container_smoke.py http://localhost:8000     # paso 4 del smoke test del curso

docker compose up -d --build           # api :8000 + ui :8501 (la UI llama a la API)
docker compose --profile mlops up -d   # + MLflow :5000
```
Tamaño aproximado de la imagen: 1,6–1,9 GB (TensorFlow ≈ 1,2 GB). Memoria recomendada: 2–3 GB.
