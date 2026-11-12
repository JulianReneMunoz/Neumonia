---
name: entregables-curso
description: Mapea los entregables M1–M4 del curso Gestión de Proyectos en IA (UAO 2026-2S) a los archivos del proyecto Neumonía y verifica su estado antes de una sustentación. Úsala al preparar una entrega o la demo.
---

# Entregables del curso → archivos del proyecto

| Módulo | Peso | Exige | Evidencia en el repo | Verificar con |
|---|---|---|---|---|
| **M1** Taller de código heredado | 25 % | MVC, uv + Python 3.13, pytest AAA, Docker CPU, UI Streamlit, CI + Gitflow + ruff + reporte PDF | `src/neumonia/`, `pyproject.toml`, `uv.lock`, `tests/`, `docker/Dockerfile`, `view/streamlit_app.py`, `.github/workflows/ci.yml`, `controller/report.py` | `make check && make smoke && make docker-build` |
| **M2** Propuesta | 35 % | Data Thinking, BMC, OKR/KPI, problema, alternativas, historias con AC, cronograma, riesgos, Kanban | `docs/M2_propuesta.md`, `docs/metodologias.md`, `docs/dataset.md`, `specs/` | Lectura + revisión del equipo |
| **M3** Construcción local | 25 % | Backend/API (FastAPI/gRPC), UI, pytest, MLflow, calidad, Gitflow, en local | `api/`, `grpc_api/`, `scripts/evaluate.py`, `tracking/`, `docker-compose.yml` | `make api`, `make ui`, `make evaluate`, `make mlflow` |
| **M4** Producción | 15 % | CI/CD con compuertas, credenciales, despliegue en Droplet, monitoreo, demo en vivo, post-mortem | `.gitlab-ci.yml`, `docs/M4_despliegue.md`, `docs/postmortem.md` | Pipeline verde + URL pública |

## Checklist previo a la sustentación
1. `git status` limpio, rama `main` con tag de la versión.
2. `make check` verde y número de pruebas/cobertura anotados para la diapositiva.
3. `make smoke` y demo con las 5 muestras de `artifacts/samples/` (incluye un DICOM con metadatos).
4. Mostrar un 422 (archivo .txt) y el PDF del reporte.
5. Mostrar Grad-CAM y el hallazgo de atajo (`gradcam-review`).
6. MLflow con al menos 2 runs comparables (p. ej. umbral 0.5 vs 0.35).
7. Declaración de uso de IA actualizada (`docs/declaracion_uso_ia.md`).

## Pitch de 3 minutos (estructura)
Problema → solución → estado de madurez (M1→M4) → datos (RSNA + metadatos) → demo → riesgos y próximos pasos.
