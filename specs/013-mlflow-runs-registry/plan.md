# Plan · SPEC-013

## Diseño
- `src/neumonia/tracking/m3_runs.py` (sin MLflow, probado con pytest): configuraciones, preprocesamiento
  con o sin CLAHE, corrida (lectura → preprocesamiento → `predict_proba` cronometrado → métricas), muestreo
  estratificado y matriz de confusión.
- `src/neumonia/tracking/pyfunc_model.py`: `NeumoniaPyfunc`, envoltura `mlflow.pyfunc` del `.h5`.
- `scripts/mlflow_m3.py`: elige datos (RSNA si están; si no, muestras del aula), registra las 3 corridas y el
  modelo. `make mlflow` (servidor) y `make mlflow-runs` (corridas).

## Decisiones
| Decisión | Por qué | Alternativa descartada |
|---|---|---|
| Cambiar un solo factor por corrida | Comparación interpretable en la UI | Barrido de muchos umbrales (ruido en la demo) |
| Latencia solo de preprocesamiento + inferencia | Es lo que depende del modelo; la red y el disco se miden en la API (`X-Process-Time-ms`) | Medir lectura del disco |
| Alias `produccion` + tag `stage` | MLflow 3 depreca las *stages*; el alias es el mecanismo vigente | `transition_model_version_stage` |
| Registro solo en la línea base | El `.h5` pesa ~118 MB: se copia una vez | Registrar en las 3 corridas |
| 200 imágenes RSNA, semilla 42, estratificado | ~1–2 min por corrida en CPU, mismas imágenes en las 3 | Las 500 (más lento para el ensayo) |

## Riesgos
El servidor debe correr desde la raíz del repo (rutas `./mlruns`); `--no-register` evita copiar el `.h5`.

## Pruebas
pytest con imágenes sintéticas y un modelo falso (sin red ni GPU); corrida real con el servidor local.
