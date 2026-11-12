# ADR-0003 · Política de decisión: 3 clases → NORMAL | PNEUMONIA

- **Estado**: aceptado · **Fecha**: 2026-11-05

## Contexto
El modelo emite `(bacteriana, normal, viral)`; el contrato exige `label ∈ {NORMAL, PNEUMONIA}` y `probability`.
El *argmax* puede decir "normal" con 0.40 cuando la neumonía suma 0.60.

## Decisión
`P(neumonía) = P(bacteriana) + P(viral)`; `label = PNEUMONIA` si `P(neumonía) ≥ umbral` (0.5 por defecto,
`NEUMONIA_THRESHOLD`). `probability` es la probabilidad de la etiqueta devuelta. `subtype` = clase de neumonía más
probable o `normal`. Grad-CAM se calcula sobre la clase de `subtype`.

## Consecuencias
- (+) Coherencia entre `label`, `probability` y el mapa de calor.
- (+) Umbral ajustable para priorizar sensibilidad (tamizaje) y comparable en MLflow.
- (−) `subtype` no está validado en RSNA (no hay etiquetas de causa): se presenta como sugerencia.
