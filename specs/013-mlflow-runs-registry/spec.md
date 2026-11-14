# SPEC-013 · MLflow: 3 corridas comparables y Model Registry

**Historia**: Como equipo, quiero comparar en MLflow tres configuraciones de inferencia del mismo modelo
y registrar la versión que sirve el backend, para justificar el umbral y el preprocesamiento con datos.

## Problema
El modelo es preentrenado (MaaS): no hay hiperparámetros de entrenamiento. El M3 exige un servidor MLflow
vivo (puerto 5050), al menos 3 runs comparables en el mismo experimento con parámetros, métricas de calidad
y de latencia, artefactos, tags y el modelo en el Model Registry, consistente con el que usa la API.

## Requisitos
- RF1. `make mlflow`: servidor con UI y Model Registry en http://127.0.0.1:5050 (SQLite + `./mlruns`).
- RF2. `make mlflow-runs`: 3 corridas en el experimento `neumonia-m3`, mismo modelo y mismas imágenes,
  cambiando un solo factor: (1) línea base, umbral 0.5 con CLAHE; (2) umbral 0.3; (3) sin CLAHE.
- RF3. Parámetros: modelo@versión, SHA-256, umbral, preprocesamiento, dataset, n, semilla, backend.
- RF4. Métricas: exactitud, precisión, sensibilidad, especificidad, F1, AUC, latencia media/p50/p95, throughput.
- RF5. Artefactos: predicciones.csv, matriz_confusion.png y reporte.md por corrida.
- RF6. Tags: licencia, equipo, ambiente, commit, spec.
- RF7. Registro `neumonia-conv-mlp-84` (pyfunc que usa el mismo lector, preprocesamiento y política que la
  API) con alias `produccion` y tag `stage=Production`.
- RNF. Sin PatientID ni PatientName en artefactos. Sin RSNA, funciona con las muestras del aula.

## Criterios de aceptación (Given-When-Then)
| # | Criterio | Prueba |
|---|---|---|
| 1 | Dadas las 3 configuraciones, entonces cada una cambia un solo factor frente a la línea base | `test_mlflow_m3.py::test_the_three_runs_change_one_thing_each` |
| 2 | Dado CLAHE activo, entonces el tensor es idéntico al del backend | `::test_clahe_variant_is_identical_to_the_serving_preprocessing` |
| 3 | Dadas latencias, entonces se reportan media, p50, p95 y throughput | `::test_latency_summary_reports_mean_p95_and_throughput` |
| 4 | Dada una muestra con semilla, entonces es reproducible y conserva la proporción de clases | `::test_sample_is_reproducible_and_keeps_both_classes` |
| 5 | Dada una corrida, entonces mide calidad y latencia, omite ilegibles y no guarda identificadores | `::test_run_config_measures_quality_latency_and_skips_unreadable` |
| 6 | Dado el servidor en :5050, cuando corre `make mlflow-runs`, entonces la UI muestra 3 runs y el modelo con alias `produccion` | Demo en vivo (plan.md) |

## Fuera de alcance
Fine-tuning; despliegue del registro en el Droplet (M4).
