---
name: gradcam-review
description: Revisa mapas Grad-CAM del modelo de apoyo al diagnóstico de neumonía para detectar aprendizaje por atajos (marcadores, bordes, texto) y documentar hallazgos de explicabilidad. Úsala al preparar la sustentación, la Model Card o al cambiar el modelo.
---

# Revisión de explicabilidad (Grad-CAM)

## Generar mapas
- UI: `make ui`, cargar una imagen, ver la columna Grad-CAM.
- Lote: `make evaluate` guarda `runtime/evaluation/gradcam_*.png` (y en MLflow).
- API: `gradcam_url` de cada respuesta.

## Lista de chequeo por imagen
| Señal | Interpretación |
|---|---|
| Calor sobre campos pulmonares / consolidación | Coherente con el hallazgo |
| Calor en letras, marcadores de lateralidad ("R/L"), electrodos, tubos | **Atajo** (shortcut learning) |
| Calor en bordes o en el marco negro de imágenes rotadas | El modelo usa el encuadre, no la anatomía |
| Mapa casi uniforme | Grad-CAM poco informativo (capa saturada o predicción muy segura) |

## Hallazgo ya documentado
En `viral (3).dcm` (RSNA, AP, 6 años) el calor se concentra en el marcador de lateralidad
y en los bordes de la placa rotada (`docs/img/gradcam_viral.png`). Es evidencia de posible
aprendizaje por atajos: está en la Model Card y en la matriz de riesgos (R-05).

## Notas técnicas
- Capa: `conv10_thisone` (31×31×128). Se ponderan los 128 filtros (el monolito usaba solo 64).
- Clase explicada: la de la decisión (`Decision.target_index`), no siempre el argmax.
- Superposición: JET con alfa 0.8 sobre la imagen 512×512 (igual que el monolito).
- Grad-CAM explica **qué miró** el modelo, no **por qué acierta**: no es validación clínica.
