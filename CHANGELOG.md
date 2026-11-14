# Changelog
Formato [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) · [SemVer](https://semver.org/lang/es/).

## [0.9.0] — sin publicar · Aplicación única
### Cambiado
- `make ui` abre una sola aplicación (puerto 8501) con dos páginas en el menú lateral: «Radiografía» y
  «Tomografía 3D (prototipo)» (`view/app.py`, `st.navigation`) — ADR-0012, spec 010. Las vistas no cambian;
  `make ui-ct` queda como respaldo en el puerto 8502. Paciente e informe compartidos: nivel 2, pendiente.
### Agregado
- Frontend desacoplado HTML/JS (`frontend/`, `make frontend` en :5173) que consume la API por HTTP: estados
  idle/loading/success/error, Grad-CAM, confianza y datos del paciente. La API agrega CORS
  (`NEUMONIA_CORS_ORIGINS`) y carga el modelo al arrancar (lifespan). `make backend`. ADR-0013, SPEC-012.
- Panel «Datos del paciente» en la barra lateral de la radiografía: documento, código del paciente
  (seudónimo HMAC), código del dataset si el DICOM viene anonimizado, edad, sexo, proyección,
  modalidad, región, tamaño y archivo (`presenter.patient_rows`). Nunca muestra PatientName.
  Reemplaza el desplegable «Metadatos de la imagen».

## [0.7.0] — sin publicar · Prototipo de tomografía 3D (experimental)
### Agregado
- App separada `make ui-ct` (puerto 8502): reconstrucción 3D **real** de pulmones, vía aérea, arterias
  pulmonares, vidrio esmerilado y consolidación a partir de una tomografía; cortes axial/coronal; informe con
  % comprometido por pulmón y lóbulo y puntaje de severidad tomográfica (0–25) — ADR-0010, spec 008.
- MEDPSeg (MIT) en su propio entorno (`make ct-setup`, commit fijo, pesos con SHA-256), invocado como proceso
  externo sin GUI; remuestreo a 1.5 mm para CPU; caché por caso para demos instantáneas (`make ct-precompute`).
- Extra liviano `ct` (nibabel, scikit-image) incluido en `make install` y en CI. 32 pruebas nuevas (432).
- Verificado con una tomografía real: 29 min en CPU (2 núcleos), volúmenes iguales al informe de MEDPSeg.

## [0.6.0] — sin publicar · ¿Grad-CAM apunta a la lesión? (fase 2)
### Agregado
- `evaluation_localization.py` + `scripts/evaluate_localization.py` + `make evaluate-loc`: compara Grad-CAM con
  las cajas de radiólogos de RSNA (*pointing game* con IC de Wilson, enriquecimiento frente al azar, IoU),
  global y para los casos clasificados como neumonía; CSV por caso y registro en MLflow — ADR-0009, spec 007.
- Acepta el CSV de Kaggle (patientId) o la exportación adjudicada de RSNA (SOPInstanceUID) y busca los DICOM en subcarpetas.
- 15 pruebas nuevas con mapas y cajas sintéticos (392 en total). Falta la corrida con RSNA.

## [0.5.0] — sin publicar · Segmentación pulmonar real (fase 1)
### Agregado
- Estrategia `LungSegmenter`: zonas geométricas (por defecto) o **PSPNet de TorchXRayVision** (extra opcional
  `seg`, `make seg`, `NEUMONIA_LUNG_SEGMENTER=pspnet`, `make ui-seg`) — ADR-0008, spec 006.
- Control de calidad con respaldo geométrico y nota en el informe; pesos verificados con SHA-256.
- PSPNet corre en un proceso hijo (`neumonia.model.lung_worker`): TensorFlow y PyTorch no conviven en un proceso.
- Zonas en tercios de la altura de cada pulmón; `findings.lung_source`, `lung_note`, `lung_grid` (aditivos).
- La pestaña *Informe detallado* dibuja los pulmones, sus tercios y la zona dominante sobre la radiografía.
- Reglas de arquitectura: PyTorch solo perezoso y nunca en vista ni controlador. 37 pruebas nuevas (377).

## [0.4.0] — sin publicar · Informe de hallazgos y vistas 3D
### Agregado
- Informe de hallazgos asistido: atención del modelo por 6 zonas pulmonares aproximadas, lateralidad,
  extensión y **alerta de posible atajo** (razón de densidad fuera/dentro de los pulmones ≥ 1.0) — ADR-0007, spec 005.
- Campo aditivo `findings` en `POST /predict` (OpenAPI 0.4.0); la pasarela HTTP lo reconstruye.
- UI con pestañas *Resultado*, *Informe detallado* y *Vista 3D* (relieve 3D de Grad-CAM y esquema pulmonar, Plotly).
- Sección "Informe de hallazgos asistido" en el PDF.
- 28 pruebas nuevas (`tests/test_hallazgos_3d.py`): 340 en total, cobertura 99 %.
### Cambiado
- Streamlit ≥ 1.50: `use_container_width` → `width="stretch"` (parámetro obsoleto).

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
