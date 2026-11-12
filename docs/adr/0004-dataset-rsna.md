# ADR-0004 · RSNA Pneumonia 2018 como dataset con metadatos

- **Estado**: aceptado · **Fecha**: 2026-11-07

## Contexto
Se necesita un dataset de calidad con metadatos por imagen. Candidatos: RSNA, Kermany, NIH ChestX-ray14,
CheXpert, MIMIC-CXR y PneumoniaMNIST (`docs/dataset.md` §2).

## Decisión
RSNA como dataset principal de evaluación (DICOM con edad, sexo y proyección; etiquetas de radiólogos; cajas)
y Kermany como complemento para el subtipo. Se catalogan en CSV con lista blanca de metadatos y submuestras
estratificadas reproducibles (`seed=42`).

## Consecuencias
- (+) Evaluación por subgrupos y de generalización (adultos vs. entrenamiento pediátrico).
- (+) Coherente con los DICOM del aula, que provienen del RSNA.
- (−) Requiere cuenta de Kaggle y aceptar reglas; no se redistribuye en el repo.
