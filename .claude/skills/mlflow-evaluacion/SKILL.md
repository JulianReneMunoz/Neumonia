---
name: mlflow-evaluacion
description: Ejecuta la evaluación del modelo de neumonía con métricas globales y por subgrupo (sexo, edad, proyección) y la registra en MLflow. Úsala para el entregable M3, para comparar umbrales o para actualizar la Model Card.
---

# Evaluación con MLflow

## Ejecutar
```bash
make evaluate                       # aula (16 imágenes) → smoke de la evaluación
uv run --group mlops python scripts/evaluate.py --metadata data/processed/rsna_metadata.csv --limit 500
NEUMONIA_THRESHOLD=0.35 uv run --group mlops python scripts/evaluate.py --metadata ...   # otro umbral
make mlflow                         # http://127.0.0.1:5000 (backend sqlite:///mlflow.db)
```
Con Docker: `docker compose --profile mlops up -d` y `MLFLOW_TRACKING_URI=http://localhost:5000`.

## Qué se registra
- Parámetros: `threshold`, `n_samples`, `model_version`, `dataset`.
- Métricas: `accuracy, precision, recall, specificity, f1, roc_auc, seconds_per_image, skipped`
  y `recall__<sexo|age_group|view_position>__<grupo>`.
- Artefactos: `predictions.csv`, `metrics.json`, 4 ejemplos Grad-CAM.

## Cómo leer los resultados
1. **Sensibilidad (recall) primero**: en tamizaje un falso negativo cuesta más que un falso positivo.
2. Compara `recall` entre subgrupos: una brecha > 10 puntos es un riesgo de equidad → anotarlo
   en `docs/riesgos` (matriz del M2) y en `docs/model_card.md`.
3. `AP` vs `PA`: las placas AP suelen ser de pacientes hospitalizados (más neumonía): cuidado con
   el atajo "proyección = enfermedad".
4. Con el aula o Kermany la métrica está inflada (posible fuga de entrenamiento). Repórtalo.

## Después
Actualiza la tabla de métricas de `docs/model_card.md` con el `run_id` de MLflow.
