# Changelog
Formato [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) · [SemVer](https://semver.org/lang/es/).

## [0.3.0] — 2026-11-12 · M3 Construcción local
### Agregado
- Arquitectura documentada: `docs/arquitectura/DESIGN.md` con 12 diagramas Mermaid/SVG (C4 + 4+1) y
  trazabilidad de las 23 metodologías con cada componente (`METODOLOGIAS_ARQUITECTURA.md`).
- graphify: grafo de conocimiento en `graphify-out/`, skill y hooks (`make grafo`).
- Engram: memoria del proyecto `neumonia` (18 decisiones y hallazgos) en `.engram/` (`make memoria`).
- API FastAPI (`/health`, `/predict`, `/static/gradcam`) y servidor gRPC (`neumonia.proto`).
- Pasarelas de la UI (Local/HTTP) para el despliegue cliente-servidor con Docker Compose.
- Catálogo de datasets con metadatos (RSNA, Kermany, aula) y evaluación por subgrupos con MLflow (SQLite).
- GitLab CI/CD con compuertas (ruff, pytest ≥ 80 %, smoke del contenedor, Trivy, despliegue manual).
- Kit agéntico: `CLAUDE.md`, `AGENTS.md`, 9 skills, 2 subagentes, hooks y permisos.
- Documentación: metodologías, dataset, M2, Model Card, M4, ADR 0001–0006, especificaciones.

## [0.1.0] — 2026-10-31 · M1 Taller de código heredado
### Cambiado
- Monolito `detector_neumonia.py` → paquete MVC `src/neumonia` con Estrategia y DIP.
- TensorFlow 1 (`K.gradients`) → `tf.GradientTape`; Grad-CAM con los 128 filtros.
- Tkinter + `tkcap` → Streamlit clínico + PDF con `fpdf2`.
### Agregado
- uv + Python 3.13, pytest (patrón AAA), Docker CPU, GitHub Actions, pre-commit, descarga del modelo con SHA-256.
