# ADR-0007 · Informe de hallazgos por zonas y vistas 3D de la atención

- **Estado**: propuesto (rama `feature/hallazgos-3d`) · **Fecha**: 2026-11-12

## Contexto
Se pidió que el sistema "dé un diagnóstico detallado y muestre en 3D los lugares afectados". Hay tres
restricciones técnicas que condicionan lo que se puede prometer:

1. **El modelo es un clasificador** (`conv_MLP_84`: bacteriana / normal / viral). No fue entrenado para
   segmentar ni localizar lesiones; no existe una salida "lugar afectado".
2. **Grad-CAM indica dónde miró la red**, no dónde está la enfermedad. En `viral (3).dcm` la atención cae en
   el marcador de lateralidad y en los bordes (Model Card, R-05).
3. **Una radiografía de tórax es una proyección 2D.** Sin tomografía no hay información de profundidad: un
   "pulmón 3D" real no puede reconstruirse a partir de una sola placa.

## Decisión
1. **Análisis por zonas** (`model/localization.py`): el mapa Grad-CAM (31×31) se lleva a 512×512 y se resume
   en seis zonas geométricas aproximadas (derecho/izquierdo × superior/medio/inferior), con la convención
   radiológica *pulmón derecho del paciente = izquierda de la imagen*. Se calculan:
   - atención media por zona y zona dominante;
   - lateralidad a partir de la zona más intensa de cada lado (umbral de foco 0.15, razón 1.5);
   - extensión: % del campo pulmonar con atención ≥ 0.5;
   - **alerta de atajo**: razón de densidad de atención fuera/dentro de los campos pulmonares ≥ 1.0
     (con atención uniforme la razón es 1.0). Se limita a 99 para no emitir infinitos en JSON.
2. **Informe en lenguaje prudente** (`controller/findings.py`): frases del tipo "el modelo sugiere…",
   "la región que más influyó…", siempre con la nota "no es una segmentación de lesiones".
3. **Dos vistas 3D honestas** (`view/visual3d.py`, Plotly):
   - *Relieve de atención*: la radiografía como plano base y el Grad-CAM como superficie de altura.
   - *Esquema pulmonar*: dos elipsoides **no anatómicos** coloreados por la atención de cada zona.
   Ambas llevan el rótulo "no reconstruye el pulmón en 3D".
4. **Cambio aditivo del contrato**: `findings` se agrega a `/predict` (nullable). `label`, `probability` y
   `gradcam_url` no cambian. El PDF incorpora la sección "Informe de hallazgos asistido".

## Alternativas descartadas
| Alternativa | Motivo |
|---|---|
| Segmentación pulmonar con U-Net (p. ej. TorchXRayVision `PSPNet`) | Mejor precisión de zonas, pero otro modelo, ~200 MB y validación propia; queda como Estrategia futura detrás de un `LungSegmenter` |
| Detector de opacidades entrenado en RSNA (cajas) | Sí localizaría lesiones, pero exige reentrenar y validar; fuera del alcance del M3 |
| Reconstrucción 3D desde la radiografía (NeRF/GAN 2D→3D) | Investigación; inventa profundidad y no es verificable: riesgo clínico inaceptable |
| Llamar "diagnóstico" al informe | Contradice el uso previsto (apoyo, no dispositivo médico) |

## Consecuencias
- (+) El médico recibe un resumen legible y localizado de **en qué se basó** el modelo, con lateralidad y extensión.
- (+) La alerta de atajo hace visible el riesgo R-05 en cada predicción: con las muestras del curso marca
  `viral (3).dcm` (razón 1.04), `normal (3).dcm` (1.49) y `NORMAL2-IM-1148` (2.63).
- (+) Es aditivo: los clientes previos del API y las 312 pruebas anteriores siguen funcionando.
- (−) Zonas geométricas: placas rotadas, recortadas o pediátricas muy pequeñas reducen la exactitud.
- (−) Resolución limitada por Grad-CAM (31×31 ≈ 16 px por celda).
- (−) Una vista 3D atractiva puede sugerir más certeza de la que existe; por eso los rótulos y la nota son obligatorios.

## Verificación
`tests/test_hallazgos_3d.py` (spec 005) y revisión visual de la UI con `viral (3).dcm`.
