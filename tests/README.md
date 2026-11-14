# Pruebas — Neumonía

**392 pruebas · cobertura 98 % · patrón AAA.** `make test` (todas) · `make test-fast` (sin modelo real ni lentas, ~15 s) · `make cov`.

## Smoke tests exigidos por el curso
| Requisito (`tests/README` original) | Prueba |
|---|---|
| `test_health`: `GET /health` → 200 | `test_api.py::test_health` |
| `test_predict_ok`: muestra de `artifacts/samples/` → 200 + contrato | `test_api.py::test_predict_ok_with_course_samples` (5 muestras) |
| `test_predict_invalid`: vacía o corrupta → 422 | `test_api.py::test_predict_invalid_returns_422` (5 casos) |
| `test_response_shape`: claves de `response_example.json` | `test_api.py::test_response_shape_matches_expected_example` |
| Contenedor responde `POST /predict` | `scripts/container_smoke.py` (CI) |

## Mapa de la suite
| Archivo | Qué cubre |
|---|---|
| `test_readers.py` | Estrategia de lectura, DICOM (MONOCHROME1, 16 bits), JPG/PNG/BMP, entradas inválidas, sin PHI |
| `test_metadata.py` | Edad DICOM, sexo, grupos etarios, lista blanca |
| `test_preprocessing.py` | 512×512, gris, CLAHE, rango [0,1], determinismo |
| `test_decision.py` | Política 3→2 clases y umbral |
| `test_service.py` | Controlador con dobles |
| `test_gradcam_and_classifier.py` | Grad-CAM y Keras con una red mínima real |
| `test_api.py` · `test_grpc.py` | Contrato REST y gRPC |
| `test_report_and_view.py` | PDF, historial, presentador, pasarelas local/HTTP |
| `test_hallazgos_3d.py` | Zonas pulmonares, lateralidad, alerta de atajo, informe, `findings` en API/PDF/pasarela, figuras 3D (spec 005) |
| `test_segmentacion_pulmonar.py` | Segmentación PSPNet con dobles, control de calidad y respaldo, proceso aislado, zonas por silueta, superposición en la vista (spec 006) |
| `test_localizacion_rsna.py` | Grad-CAM vs. cajas de RSNA: máscara, *pointing game*, enriquecimiento, IoU, IC de Wilson, extremo a extremo (spec 007) |
| `test_streamlit_view.py` | Render de la UI con `AppTest` |
| `test_evaluation_and_data.py` | Métricas/AUC, RSNA, muestreo estratificado, MLflow, descarga con SHA |
| `test_architecture.py` | Reglas MVC (*fitness functions*) |
| `test_documentacion.py` | 12 diagramas con SVG, 23 metodologías trazadas, memorias Engram válidas, grafo sin ciclos, hooks graphify con uv |
| `test_contract_and_config.py` | `openapi.yaml`, configuración, `.gitignore` |
| `test_real_model.py` | Modelo real (`-m model`): arquitectura, inferencia, determinismo |

Exactitud **no** se evalúa en pruebas: se mide en MLflow (`make evaluate`).
