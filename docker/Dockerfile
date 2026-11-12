# syntax=docker/dockerfile:1.7
# Imagen CPU del caso Neumonía (sin CUDA). Multi-etapa: el builder resuelve dependencias con uv
# y descarga el modelo verificando su SHA-256; el runtime solo lleva el entorno y el código.
#   docker build -f docker/Dockerfile -t neumonia:latest .
ARG PYTHON_IMAGE=python:3.13-slim-bookworm

FROM ${PYTHON_IMAGE} AS builder
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0
WORKDIR /app

# 1) Dependencias (capa cacheable: solo cambia si cambia uv.lock)
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# 2) Código del proyecto
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# 3) Modelo: se descarga del Release y se verifica (no viaja en el contexto de build)
COPY scripts/fetch_model.py ./scripts/
RUN uv run --no-sync python scripts/fetch_model.py

FROM ${PYTHON_IMAGE} AS runtime
LABEL org.opencontainers.image.title="neumonia" \
      org.opencontainers.image.description="Detección de neumonía (Keras/TF CPU + Grad-CAM)" \
      org.opencontainers.image.licenses="Uso académico"
RUN useradd --create-home --uid 1000 app
WORKDIR /app
COPY --from=builder --chown=app:app /app /app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    TF_CPP_MIN_LOG_LEVEL=2 \
    CUDA_VISIBLE_DEVICES="" \
    NEUMONIA_STATIC_DIR=/app/runtime/static \
    NEUMONIA_HISTORY_PATH=/app/runtime/historial.csv
RUN mkdir -p /app/runtime/static && chown -R app:app /app/runtime
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=4)"
CMD ["uvicorn", "neumonia.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
