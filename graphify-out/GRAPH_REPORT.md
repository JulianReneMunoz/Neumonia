# Graph Report - Neumonia  (2026-11-12)

## Corpus Check
- 105 files · ~63,536 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 22 file(s) not represented in the graph (top: .mmd 12, (none) 7, .example 1)

## Summary
- 1025 nodes · 1926 edges · 81 communities (66 shown, 15 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 261 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- numpy
- service.py
- test_evaluation_and_data.py
- pytest
- with
- Neumonía — caso base (Keras/TF + Grad-CAM)
- ui
- app.py
- metadata.py
- tracker.py
- FakeClassifier
- evaluation.py
- server.py
- test_service.py
- conftest.py
- test_report_and_view.py
- CLAUDE.md — memoria del proyecto Neumonía
- Settings
- PneumoniaService
- 3. Vistas de arquitectura
- pull_request_template.md
- reports
- hooks
- test_evaluate_logs_metrics_and_artifacts
- test_architecture.py
- README.md
- M2 · Propuesta del proyecto — Detector de neumonía con explicabilidad
- Post-mortem del proyecto (formato sin culpables)
- trivy
- permissions
- ModelNotFoundError
- pytest
- Dataset: selección, justificación y datasheet
- M4 · Producción: CI/CD, despliegue, monitoreo y demo
- B. Ingeniería de software para IA
- .gitlab-ci.yml
- deploy-droplet
- config.py
- Contrato de API — Neumonía
- [0.1.0] — 2026-10-31 · M1 Taller de código heredado
- Dataset con metadatos
- Gitflow + Conventional Commits
- download.py
- test_gradcam_and_classifier.py
- specs/README.md
- test_streamlit_view.py
- Cambios de API sin romper el contrato
- Revisión de explicabilidad (Grad-CAM)
- Evaluación con MLflow
- Implementar una funcionalidad respetando MVC
- Pruebas con pytest (patrón AAA)
- README.md
- if
- docker-build
- ADR-0002 · Reutilizar conv_MLP_84 y descargarlo verificado
- ADR-0003 · Política de decisión: 3 clases → NORMAL | PNEUMONIA
- ADR-0004 · RSNA Pneumonia 2018 como dataset con metadatos
- make_dicom_bytes
- evaluate.py
- overlay_heatmap
- Entregables del curso → archivos del proyecto
- ADR-0001 · Arquitectura MVC con Estrategia e inversión de dependencias
- ADR-0005 · Streamlit clínico + FastAPI + gRPC con pasarela intercambiable
- variables
- docker/README.md
- fetch_artifacts.sh
- neumonia
- roc_auc
- test_api.py
- Spec 001 · Inferencia por API
- .model
- PneumoniaDetectorServicer
- Default.md
- Memoria persistente del proyecto (Engram)
- Grafo de conocimiento del proyecto (graphify)

## God Nodes (most connected - your core abstractions)
1. `PneumoniaService` - 43 edges
2. `InvalidImageError` - 26 edges
3. `evaluate()` - 26 edges
4. `FakeClassifier` - 22 edges
5. `Settings` - 21 edges
6. `Prediction` - 20 edges
7. `FakeExplainer` - 20 edges
8. `create_app()` - 20 edges
9. `ThresholdPolicy` - 19 edges
10. `C. Datos, modelo y MLOps` - 18 edges

## Surprising Connections (you probably didn't know these)
- `3.2 Contenedores (C4-2)` --references--> `HttpGateway`  [INFERRED]
  docs/arquitectura/DESIGN.md → src/neumonia/controller/gateways.py
- `3.5 Dinámica: `POST /predict`` --references--> `ThresholdPolicy`  [INFERRED]
  docs/arquitectura/DESIGN.md → src/neumonia/controller/decision.py
- `3.11 Verificación: dependencias reales medidas con graphify` --references--> `PneumoniaService`  [INFERRED]
  docs/arquitectura/DESIGN.md → src/neumonia/controller/service.py
- `7. Riesgos técnicos y deuda conocida` --references--> `Classifier`  [INFERRED]
  docs/arquitectura/DESIGN.md → src/neumonia/model/classifier.py
- `7. Modelo-Vista-Controlador (MVC)` --references--> `PneumoniaService`  [INFERRED]
  docs/metodologias.md → src/neumonia/controller/service.py

## Import Cycles
- None detected.

## Communities (81 total, 15 thin omitted)

### Community 0 - "numpy"
Cohesion: 0.19
Nodes (12): apply_clahe(), preprocess(), resize_for_display(), to_gray(), test_clahe_increases_local_contrast(), test_preprocess_custom_size(), test_preprocess_is_deterministic(), test_preprocess_output_shape_and_range() (+4 more)

### Community 1 - "service.py"
Cohesion: 0.06
Nodes (22): main(), main(), main(), main(), kaggle_download(), main(), main(), test_expected_example_has_contract_keys() (+14 more)

### Community 2 - "test_evaluation_and_data.py"
Cohesion: 0.14
Nodes (8): course_dir(), rsna_dir(), _samples(), test_download_model_from_file_url(), test_load_rsna_limit_and_missing(), test_stratified_subset_is_reproducible(), test_stratified_subset_keeps_proportion(), test_stratified_subset_larger_than_data()

### Community 3 - "pytest"
Cohesion: 0.07
Nodes (29): 2.2 Atributos de calidad (escenarios medibles), RadiographImage, DicomReader, InvalidImageError, RasterReader, read_path(), select_reader(), to_three_channels() (+21 more)

### Community 4 - "with"
Cohesion: 0.06
Nodes (40): concurrency, cancel-in-progress, group, needs, runs-on, steps, jobs, docker (+32 more)

### Community 5 - "Neumonía — caso base (Keras/TF + Grad-CAM)"
Cohesion: 0.13
Nodes (15): 10. Smoke test mínimo (sección 5 del README del curso), 11. Resultados de referencia, 1. Fuente y licencia, 2. Estado de artifacts, 3. Inicio rápido en Windows (`C:\Neumonia`), 4. Comandos, 5. Contrato de inferencia, 6. Arquitectura (MVC + Estrategia + DIP) (+7 more)

### Community 6 - "ui"
Cohesion: 0.05
Nodes (36): build, condition, deploy, environment, image, ports, restart, context (+28 more)

### Community 7 - "app.py"
Cohesion: 0.13
Nodes (9): create_app(), health(), predict(), service(), _prune(), ErrorResponse, HealthResponse, PredictionResponse (+1 more)

### Community 8 - "metadata.py"
Cohesion: 0.08
Nodes (25): 1. Matriz de trazabilidad, 2. Explicación por metodología, 3. Cómo verificar esta trazabilidad, A. Gestión y ciclo de vida, D. Agentes, Metodologías ↔ Arquitectura: trazabilidad y explicación, Análisis cualitativo (Grad-CAM), Consideraciones éticas y limitaciones (+17 more)

### Community 9 - "tracker.py"
Cohesion: 0.09
Nodes (13): ADR-0006 · MLflow con backend SQLite, Consecuencias, Contexto, Decisión, C. Datos, modelo y MLOps, 20. MLOps con MLflow, build_tracker(), MlflowTracker (+5 more)

### Community 10 - "FakeClassifier"
Cohesion: 0.19
Nodes (8): Convenciones, FakeClassifier, FakeExplainer, client(), test_evaluate_skips_missing_files(), test_explainer_factory_is_lazy(), factory(), test_without_explainer_heatmap_is_none()

### Community 11 - "evaluation.py"
Cohesion: 0.17
Nodes (8): binary_metrics(), evaluate(), EvaluationResult, subgroup_metrics(), test_binary_metrics_confusion_counts(), test_binary_metrics_length_mismatch(), test_binary_metrics_perfect(), test_metrics_handle_no_positive_predictions()

### Community 12 - "server.py"
Cohesion: 0.14
Nodes (5): run(), get_service(), create_server(), serve(), stub()

### Community 13 - "test_service.py"
Cohesion: 0.30
Nodes (9): Spec 002 · Explicabilidad Grad-CAM, test_class_probabilities_are_named(), test_dicom_metadata_flows_to_prediction(), test_explain_false_skips_gradcam(), test_gradcam_targets_decided_subtype(), test_heatmap_is_rgb_512(), test_invalid_bytes_raise(), test_predict_bytes_happy_path() (+1 more)

### Community 14 - "conftest.py"
Cohesion: 0.17
Nodes (13): Dobles y fixtures disponibles (`tests/conftest.py`), 11. Pirámide de pruebas, patrón AAA y *fitness functions*, gateway(), dicom_bytes_sample(), encode(), fake_classifier(), fake_explainer(), fake_service() (+5 more)

### Community 15 - "test_report_and_view.py"
Cohesion: 0.05
Nodes (36): Decision, ThresholdPolicy, GatewayError, GatewayResult, _original_rgb(), append_history(), build_pdf_report(), _latin1() (+28 more)

### Community 16 - "CLAUDE.md — memoria del proyecto Neumonía"
Cohesion: 0.13
Nodes (12): Antes de editar, Bucle de trabajo (spec → prueba → código → compuerta), Límites, Arquitectura documentada, CLAUDE.md — memoria del proyecto Neumonía, Comandos (todo pasa por `uv`; prohibido `pip` y `requirements.txt`), Contrato (no romper), Engram — memoria de decisiones (proyecto `neumonia`) (+4 more)

### Community 17 - "Settings"
Cohesion: 0.16
Nodes (9): Resultados (12/11/2026), _env_float(), _env_path(), Settings, build_gateway(), HttpGateway, test_settings_from_env(), real_service() (+1 more)

### Community 18 - "PneumoniaService"
Cohesion: 0.14
Nodes (13): Decisión, Decisión, 3.4 Código: dominio y abstracciones, B. Ingeniería de software, 8. SOLID: patrón Estrategia e Inversión de Dependencias (DIP), DecisionPolicy, LocalGateway, PredictionGateway (+5 more)

### Community 19 - "3. Vistas de arquitectura"
Cohesion: 0.10
Nodes (20): 1. Propósito, alcance y no objetivos, 2.3 Restricciones, 2. Impulsores de la arquitectura (*drivers*), 3.10 Desarrollo agéntico (Claude Code + graphify + Engram), 3.11 Verificación: dependencias reales medidas con graphify, 3.1 Contexto (C4-1), 3.2 Contenedores (C4-2), 3.3 Componentes (C4-3): MVC + Estrategia + DIP (+12 more)

### Community 20 - "pull_request_template.md"
Cohesion: 0.33
Nodes (5): Checklist de arquitectura (Definition of Done), Cómo se probó, Por qué, Qué cambia, Revisión (la completa el revisor)

### Community 21 - "reports"
Cohesion: 0.18
Nodes (12): reports, when, coverage_format, path, artifacts, codequality, coverage_report, junit (+4 more)

### Community 22 - "hooks"
Cohesion: 0.17
Nodes (11): args, entry, id, language, name, pass_filenames, stages, repos (+3 more)

### Community 23 - "test_evaluate_logs_metrics_and_artifacts"
Cohesion: 0.25
Nodes (4): Spec 003 · Evaluación con metadatos, RecordingTracker, test_evaluate_logs_metrics_and_artifacts(), test_load_rsna_merges_labels_classes_and_headers()

### Community 24 - "test_architecture.py"
Cohesion: 0.31
Nodes (4): imports_of(), test_every_package_has_docstring(), test_layer_does_not_import_forbidden_modules(), test_tensorflow_is_imported_lazily()

### Community 25 - "README.md"
Cohesion: 0.33
Nodes (5): Controles que limitan al agente, Declaración de uso de IA, Qué hizo el agente, Qué verificó el equipo (humanos), Responsabilidad

### Community 26 - "M2 · Propuesta del proyecto — Detector de neumonía con explicabilidad"
Cohesion: 0.18
Nodes (10): 10. Tablero Kanban, 1. Data Thinking, 2. Business Model Canvas, 3. OKR y KPI, 4. Alcance, 5. Estado del arte (resumen), 6. Alternativas de solución, 7. Matriz de riesgos (probabilidad × impacto, 1–3) (+2 more)

### Community 27 - "Post-mortem del proyecto (formato sin culpables)"
Cohesion: 0.20
Nodes (10): Acciones, Causas raíz (5 porqués) del incidente principal, Dónde tuvimos suerte, Lecciones sobre la deuda técnica (Sculley et al., 2015), Línea de tiempo de hitos e incidentes, Post-mortem del proyecto (formato sin culpables), Qué salió bien, Qué salió mal (+2 more)

### Community 28 - "trivy"
Cohesion: 0.20
Nodes (10): entrypoint, name, trivy, image, rules, script, stage, variables (+2 more)

### Community 29 - "permissions"
Cohesion: 0.20
Nodes (9): hooks, PostToolUse, PreToolUse, SessionStart, permissions, allow, ask, deny (+1 more)

### Community 30 - "ModelNotFoundError"
Cohesion: 0.22
Nodes (6): Diagnóstico, Docker y despliegue, Imagen (`docker/Dockerfile`), Local, Producción (M4) — Droplet DigitalOcean, ModelNotFoundError

### Community 31 - "pytest"
Cohesion: 0.25
Nodes (9): key, paths, cache, files, pytest, cache, coverage, script (+1 more)

### Community 32 - "Dataset: selección, justificación y datasheet"
Cohesion: 0.25
Nodes (7): 1. Requisito, 2. Candidatos evaluados, 3. Decisión: RSNA Pneumonia Detection Challenge como dataset principal, 4. Cómo obtenerlo, 5. Datasheet (Gebru et al., 2021) — RSNA Pneumonia 2018, 6. Datos locales del aula (smoke test), Dataset: selección, justificación y datasheet

### Community 33 - "M4 · Producción: CI/CD, despliegue, monitoreo y demo"
Cohesion: 0.25
Nodes (7): 1. Pipeline (`.gitlab-ci.yml`), 2. Credenciales (nunca en el repositorio), 3. Preparar el Droplet (una vez), 4. Monitoreo, 5. Guion de la demo en vivo (5 min), 6. Reversión, M4 · Producción: CI/CD, despliegue, monitoreo y demo

### Community 34 - "B. Ingeniería de software para IA"
Cohesion: 0.07
Nodes (27): 10. Contract-first API (OpenAPI), REST y gRPC, 12. Reproducibilidad: uv, configuración 12-factor y Docker, 13. Gitflow, Conventional Commits y versionado semántico, 14. CI/CD con compuertas de calidad y DevSecOps, 15. Reutilizar el modelo preentrenado `conv_MLP_84` (no reentrenar), 16. Paridad entrenamiento-servicio (preprocesamiento con CLAHE), 17. Análisis de decisión: de 3 clases a un contrato binario, 18. Grad-CAM como técnica de explicabilidad (+19 more)

### Community 35 - ".gitlab-ci.yml"
Cohesion: 0.25
Nodes (7): default, image, smoke-production, needs, script, stage, stages

### Community 36 - "deploy-droplet"
Cohesion: 0.25
Nodes (8): deploy-droplet, before_script, environment, image, script, stage, name, url

### Community 37 - "config.py"
Cohesion: 0.13
Nodes (7): 2.1 Requisitos funcionales clave, main(), get_settings(), build_service(), explainer_factory(), KerasClassifier, GradCamExplainer

### Community 38 - "Contrato de API — Neumonía"
Cohesion: 0.29
Nodes (6): Contrato de API — Neumonía, Ejemplos, Endpoints, Entrada, Reglas, Salida

### Community 39 - "[0.1.0] — 2026-10-31 · M1 Taller de código heredado"
Cohesion: 0.29
Nodes (6): [0.1.0] — 2026-10-31 · M1 Taller de código heredado, [0.3.0] — 2026-11-12 · M3 Construcción local, Agregado, Agregado, Cambiado, Changelog

### Community 40 - "Dataset con metadatos"
Cohesion: 0.29
Nodes (6): Dataset con metadatos, Fuentes, Reglas, Requisitos de Kaggle (RSNA y Kermany), Salidas, Siguiente paso

### Community 41 - "Gitflow + Conventional Commits"
Cohesion: 0.29
Nodes (6): Antes del PR, Commits, Gitflow + Conventional Commits, Iniciar una tarea, Liberar, Ramas

### Community 42 - "download.py"
Cohesion: 0.26
Nodes (7): main(), ChecksumError, download_model(), sha256_of(), test_download_model_checksum_mismatch(), test_download_model_rejects_http(), test_download_model_skips_valid_existing()

### Community 43 - "test_gradcam_and_classifier.py"
Cohesion: 0.31
Nodes (6): test_gradcam_explainer_with_tiny_model(), test_gradcam_unknown_layer(), test_keras_classifier_rejects_wrong_number_of_classes(), test_keras_classifier_with_tiny_model(), test_missing_model_raises_clear_error(), test_model_is_cached()

### Community 46 - "Cambios de API sin romper el contrato"
Cohesion: 0.33
Nodes (5): Cambios de API sin romper el contrato, Contrato estable, Pasos (en este orden), Tipos de cambio, Verificación manual

### Community 47 - "Revisión de explicabilidad (Grad-CAM)"
Cohesion: 0.33
Nodes (5): Generar mapas, Hallazgo ya documentado, Lista de chequeo por imagen, Notas técnicas, Revisión de explicabilidad (Grad-CAM)

### Community 48 - "Evaluación con MLflow"
Cohesion: 0.33
Nodes (5): Cómo leer los resultados, Después, Ejecutar, Evaluación con MLflow, Qué se registra

### Community 49 - "Implementar una funcionalidad respetando MVC"
Cohesion: 0.33
Nodes (5): 1. Ubica la capa correcta, 2. Reglas que no se negocian, 3. Flujo, Ejemplo: nuevo lector, Implementar una funcionalidad respetando MVC

### Community 50 - "Pruebas con pytest (patrón AAA)"
Cohesion: 0.33
Nodes (5): Cerrar, Estructura de cada prueba, Marcas, Pruebas con pytest (patrón AAA), Qué probar según la capa

### Community 52 - "if"
Cohesion: 0.40
Nodes (6): rules, if, when, rules, workflow, rules

### Community 53 - "docker-build"
Cohesion: 0.33
Nodes (6): docker-build, image, rules, script, services, stage

### Community 54 - "ADR-0002 · Reutilizar conv_MLP_84 y descargarlo verificado"
Cohesion: 0.40
Nodes (4): ADR-0002 · Reutilizar conv_MLP_84 y descargarlo verificado, Consecuencias, Contexto, Decisión

### Community 55 - "ADR-0003 · Política de decisión: 3 clases → NORMAL | PNEUMONIA"
Cohesion: 0.40
Nodes (4): ADR-0003 · Política de decisión: 3 clases → NORMAL | PNEUMONIA, Consecuencias, Contexto, Decisión

### Community 56 - "ADR-0004 · RSNA Pneumonia 2018 como dataset con metadatos"
Cohesion: 0.40
Nodes (4): ADR-0004 · RSNA Pneumonia 2018 como dataset con metadatos, Consecuencias, Contexto, Decisión

### Community 57 - "make_dicom_bytes"
Cohesion: 0.25
Nodes (4): gradient_image(), make_dicom_bytes(), test_dicom_16_bits_is_scaled_to_uint8(), test_dicom_monochrome1_is_inverted()

### Community 59 - "overlay_heatmap"
Cohesion: 0.23
Nodes (6): normalize_heatmap(), overlay_heatmap(), test_normalize_heatmap(), test_normalize_heatmap_degenerate_returns_zeros(), test_overlay_heatmap_shape(), test_overlay_highlights_hot_region()

### Community 60 - "Entregables del curso → archivos del proyecto"
Cohesion: 0.50
Nodes (3): Checklist previo a la sustentación, Entregables del curso → archivos del proyecto, Pitch de 3 minutos (estructura)

### Community 61 - "ADR-0001 · Arquitectura MVC con Estrategia e inversión de dependencias"
Cohesion: 0.50
Nodes (3): ADR-0001 · Arquitectura MVC con Estrategia e inversión de dependencias, Consecuencias, Contexto

### Community 62 - "ADR-0005 · Streamlit clínico + FastAPI + gRPC con pasarela intercambiable"
Cohesion: 0.50
Nodes (3): ADR-0005 · Streamlit clínico + FastAPI + gRPC con pasarela intercambiable, Consecuencias, Contexto

### Community 63 - "variables"
Cohesion: 0.50
Nodes (4): variables, IMAGE, UV_CACHE_DIR, UV_LINK_MODE

### Community 73 - "roc_auc"
Cohesion: 0.29
Nodes (4): roc_auc(), test_roc_auc_known_values(), test_roc_auc_single_class_is_none(), test_subtype_from_name()

### Community 74 - "test_api.py"
Cohesion: 0.20
Nodes (5): 8. Historias de usuario y criterios de aceptación (Gherkin), ExplodingClassifier, test_gradcam_url_is_served(), test_model_failure_returns_500_with_error(), test_response_has_no_local_paths()

### Community 75 - "Spec 001 · Inferencia por API"
Cohesion: 0.24
Nodes (9): Spec 001 · Inferencia por API, Mapa de la suite, Pruebas — Neumonía, Smoke tests exigidos por el curso, test_health(), test_predict_invalid_returns_422(), test_predict_ok_with_course_samples(), test_predict_too_large_returns_422() (+1 more)

### Community 79 - "Default.md"
Cohesion: 0.33
Nodes (5): Checklist de arquitectura (Definition of Done), Cómo se probó, Por qué, Qué cambia, Revisión (la completa el revisor)

### Community 81 - "Memoria persistente del proyecto (Engram)"
Cohesion: 0.40
Nodes (5): Las 18 memorias, Memoria persistente del proyecto (Engram), Protocolo de memoria para el agente, Qué hay en el repositorio, Uso en Windows (`C:\Neumonia`)

### Community 82 - "Grafo de conocimiento del proyecto (graphify)"
Cohesion: 0.50
Nodes (4): Comandos, Grafo de conocimiento del proyecto (graphify), Integración con Claude Code, Salidas (`graphify-out/`)

## Knowledge Gaps
- **1 isolated node(s):** `neumonia`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 464 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Resultados (12/11/2026)` connect `Settings` to `pytest`, `app.py`, `FakeClassifier`, `evaluation.py`, `test_report_and_view.py`, `Grafo de conocimiento del proyecto (graphify)`, `PneumoniaService`?**
  _High betweenness centrality (0.074) - this node is a cross-community bridge._
- **Are the 29 inferred relationships involving `PneumoniaService` (e.g. with `2.1 Requisitos funcionales clave` and `3.11 Verificación: dependencias reales medidas con graphify`) actually correct?**
  _`PneumoniaService` has 29 INFERRED edges - model-reasoned connections that need verification._
- **What connects `neumonia` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `service.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06289308176100629 - nodes in this community are weakly interconnected._
- **Why does `Grafo de conocimiento del proyecto (graphify)` connect `Grafo de conocimiento del proyecto (graphify)` to `Settings`, `README.md`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `InvalidImageError` (e.g. with `Qué probar según la capa` and `2.1 Requisitos funcionales clave`) actually correct?**
  _`InvalidImageError` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_evaluation_and_data.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1437908496732026 - nodes in this community are weakly interconnected._