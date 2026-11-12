---
name: dataset-rsna
description: Descarga y cataloga el dataset de radiografías con metadatos (RSNA Pneumonia Detection Challenge; alternativos Kermany y muestras del aula), respetando licencia y privacidad. Úsala para preparar datos de evaluación o para preguntas sobre el dataset.
---

# Dataset con metadatos

## Fuentes
| Fuente | Comando | Contenido | Licencia |
|---|---|---|---|
| Aula | `make data-course` | 12 JPG + 4 DICOM (los DICOM son del RSNA) | Uso académico |
| **RSNA 2018 (principal)** | `make dataset-rsna` | 26 684 DICOM, edad/sexo/proyección en cabecera, etiquetas y cajas de radiólogos | Investigación y educación, con atribución a RSNA |
| Kermany 2018 | `make dataset-kermany` | 5 856 JPG, subtipo bacteriana/viral en el nombre | CC BY 4.0 |

## Requisitos de Kaggle (RSNA y Kermany)
1. kaggle.com → Settings → API → *Create New Token* → `kaggle.json`.
2. Windows: `%USERPROFILE%\.kaggle\kaggle.json` · Linux/macOS: `~/.kaggle/kaggle.json` (chmod 600).
3. Solo RSNA: aceptar las reglas de la competencia `rsna-pneumonia-detection-challenge`.
`kaggle.json` está en `.gitignore` y el hook `guard_bash.py` impide versionarlo.

## Salidas
- `data/raw/<fuente>/` — imágenes (no se versionan).
- `data/processed/<fuente>_metadata.csv` — catálogo: `image_path, source, target, subtype, rsna_class, n_boxes, age, age_group, sex, view_position, modality, rows, columns`.
- `data/processed/<fuente>_summary.json` — balance de clases y cobertura demográfica (datasheet).

## Reglas
- Nunca extraer PatientID/PatientName: `model/metadata.py::SAFE_FIELDS` es la lista blanca.
- Submuestras siempre con `stratified_subset(..., seed=42)` para que sean reproducibles.
- La etiqueta RSNA `No Lung Opacity / Not Normal` es **negativa para neumonía** pero no "sana":
  reportar sus métricas aparte (`rsna_class`).
- Las imágenes del aula y de Kermany pueden estar en el set de entrenamiento de conv_MLP_84:
  sus métricas **no** miden generalización. Para eso, usar RSNA.

## Siguiente paso
`uv run --group mlops python scripts/evaluate.py --metadata data/processed/rsna_metadata.csv --limit 500`
(ver skill `mlflow-evaluacion`).
